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
        sys.stdout.write("UNKNOWN: Bad arguments (see --help): %s\n" % message)
        sys.exit(3)


# Nagios unknown exit decorator in case of TB
def tb2unknown(method):
    @wraps(method)
    def wrapped(*args, **kw):
        try:
            f_result = method(*args, **kw)
            return f_result
        except Exception as e:
            print("UNKNOWN: Got exception while running %s: %s" % (method.__name__, str(e)))
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
        os.environ["PATH"] += os.pathsep + "/usr/sbin"
        os.environ["PATH"] += os.pathsep + "/sbin"
        os.environ["PATH"] += os.pathsep + os.path.dirname(os.path.realpath(sys.argv[0]))
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    raise Exception("Unable to find ipmi-sensors binary in %r" % os.environ["PATH"])


# Get shell command stdout
@tb2unknown
def get_output(cmd_r):
    proc = subprocess.Popen(cmd_r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    assert proc.returncode == 0, "Command return exit code != 0: output: %s" % stdout + stderr
    return stdout


# Parse ipmi-chassis stdout
@tb2unknown
def parse_output(output):
    status = []
    for line in output.splitlines():
        data = line.split(":")
        data = [x.strip() for x in data]
        if len(data) == 2:
            status.append(data)

    return dict(status)


# Arguments handler
@tb2unknown
def parse_args():
    argparser = NagiosArgumentParser(description="Simple IPMI chassis checking script")
    argparser.add_argument("-H", "--host", type=str, required=True, help="Hostname or address to query (mandatory)")
    argparser.add_argument("-U", "--user", type=str, required=True, help="IPMI username to log in")
    argparser.add_argument("-P", "--password", type=str, required=True, help="IPMI password to log in")
    argparser.add_argument("-S", "--sensor", type=str, required=True, help="IPMI chassis to query (Run ipmi-chassis by hand to list then (first column)")
    argparser.add_argument(
        "-E", "--expected", type=str, required=True, help="IPMI chassis to expected state (Run ipmi-chassis by hand to list then (second column)"
    )
    argparser.add_argument("-T", "--ipmi-timeout", type=int, default=5000, help="IPMI timeout")
    argparser.add_argument("-D", "--debug", action="store_true", help="Debug mode: re raise Exception (do not use in production)")
    args = argparser.parse_args()

    return args


if __name__ == "__main__":

    config = parse_args()
    debug = config.debug
    binary = which("ipmi-chassis")
    # Give config.timeout ms to ipmi command but also limit subprocess to config.timeout + 2000ms
    output = get_output(
        [
            binary,
            "-h",
            config.host,
            "-u",
            config.user,
            "-p",
            config.password,
            "--session-timeout",
            str(config.ipmi_timeout),
            "-D",
            "LAN_2_0",
            "--get-chassis-status",
        ]
    )
    status = parse_output(output)

    if not config.sensor in status:
        message = "UNKNOWN: Chassis attribute %s is not present" % config.sensor
        code = 3
    else:
        state = status[config.sensor]
        if state == config.expected:
            message = "OK: %s is %s" % (config.sensor, status[config.sensor])
            code = 0
        else:
            message = "CRITICAL: %s is %s (%s expected)" % (config.sensor, status[config.sensor], config.expected)
            code = 2

    print(message)
    sys.exit(code)
