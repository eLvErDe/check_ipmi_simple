#!/usr/bin/python

import sys
import os
import subprocess
from argparse import ArgumentParser, ArgumentError
from functools import wraps

debug = False

# Argument parser
# My own ArgumentParser with single-line stdout output and unknown state Nagios retcode
class NagiosArgumentParser(ArgumentParser):
    def error(self, message):
        sys.stdout.write('UNKNOWN: Bad arguments (see --help): %s\n' % message)
        sys.exit(3)

# Nagios unknown exit decorator in case of TB
def tb2unknown(method):
    @wraps(method)
    def wrapped(*args, **kw):
        try:
            f_result = method(*args, **kw)
            return f_result
        except Exception, e:
            print 'UNKNOWN: Got exception while running %s: %s' % (method.__name__, str(e))
            if debug:
                raise
            sys.exit(3)
    return wrapped

# Can a string be casted to float ?
def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

# Check if we have -x permission
@tb2unknown
def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

# Find a program in path smartely
@tb2unknown
def which(program):
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        # Add some defaults
        os.environ["PATH"] += os.pathsep + '/usr/sbin'
        os.environ["PATH"] += os.pathsep + '/sbin'
        os.environ["PATH"] += os.pathsep + os.path.dirname(os.path.realpath(sys.argv[0]))
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    raise Exception('Unable to find ipmi-sensors binary in %r' % os.environ["PATH"])

# Get shell command stdout
@tb2unknown
def get_output(cmd_r):
    proc = subprocess.Popen(cmd_r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    assert proc.returncode == 0, "Command return exit code != 0: output: %s" % stdout+stderr
    return stdout

# Parse ipmi-sensors stdout
@tb2unknown
def parse_output(output):
    headers = output.splitlines()[0].split('|')[2:]
    headers = [ x.strip() for x in headers ]
    status = {}
    for line in output.splitlines()[1:]:
        data = line.split('|')[1:]
        data = [ x.strip() for x in data ]
        name = data.pop(0)
        status[name] = dict(zip(headers, data))
    return status

# Arguments handler
@tb2unknown
def parse_args():
    argparser = NagiosArgumentParser(description='Simple IPMI sensor checking script')
    argparser.add_argument('-H', '--host',       type=str,     required=True,
                           help='Hostname or address to query (mandatory)')
    argparser.add_argument('-U', '--user',       type=str,     required=True,
                           help='IPMI username to log in')
    argparser.add_argument('-P', '--password',   type=str,     required=True,
                           help='IPMI password to log in')
    argparser.add_argument('-S', '--sensor',     type=str ,    required=True,
                           help='IPMI sensor to query (Run ipmi-sensors by hand to list then (column "Name"))')
    argparser.add_argument('-T','--ipmi-timeout',type=int ,    default=5000,
                           help='IPMI timeout')
    argparser.add_argument('-D', '--debug', action='store_true',
                           help='Debug mode: re raise Exception (do not use in production)')
    args = argparser.parse_args()

    return args

if __name__ == '__main__':

    config = parse_args()
    debug = config.debug
    binary = which('ipmi-sensors')
    # Give config.timeout ms to ipmi command but also limit subprocess to config.timeout + 2000ms
    output = get_output([binary, '-h', config.host, '-u', config.user, '-p', config.password, '--sdr-cache-recreate', '-D', 'LAN_2_0', '--session-timeout', str(config.ipmi_timeout)])
    status = parse_output(output)

    if not config.sensor in status:
        message = 'UNKNOWN: Sensor %s is not present' % config.sensor
        code = 3
    else:
        state = status[config.sensor]['Event'].strip("'")
        value = status[config.sensor]['Reading'].strip("'")
        unit = status[config.sensor]['Units'].strip("'")
        stype = status[config.sensor]['Type'].strip("'")
        if state in [ 'OK', 'Device Inserted/Device Present', 'Fully Redundant', 'Device Enabled', 'Presence detected', 'Drive Presence' ]:
            message = 'OK: '
            code = 0
        else:
            message = 'CRITICAL: '
            code = 2
        if unit != 'N/A' and isfloat(value):
            message += '%s "%s"=%s%s (%s)' % (stype, config.sensor, value, unit, state)
            message += ' | %s=%s%s' % (config.sensor.replace(' ', '_'), value, unit)
        else:
            message += '%s "%s"=%s' % (stype, config.sensor, state)

    print(message)
    sys.exit(code)
