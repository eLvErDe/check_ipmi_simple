# Usage

Usage: check_ipmi_simple_sensors.py [-h] -H HOST -U USER -P PASSWORD -S SENSOR [-D]

Simple IPMI sensor checking script

Optional arguments:
*  -h, --help            show this help message and exit
*  -H HOST, --host HOST  Hostname or address to query (mandatory)
*  -U USER, --user USER  IPMI username to log in
*  -P PASSWORD, --password PASSWORD  
                         IPMI password to log in
*  -S SENSOR, --sensor SENSOR  
                         IPMI sensor to query (Run ipmi-sensors by hand to list then (column "Name"))
*  -T IPMI_TIMEOUT, --ipmi-timeout IPMI_TIMEOUT  
                         IPMI timeout
*  -D, --debug           Debug mode: re raise Exception (do not use in production)


# Examples (on a SuperMicro board)

```
./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'Fan1'
CRITCAL: Fan "Fan1"=0.00RPM (At or Below (<=) Lower Non-Recoverable Threshold) | Fan1=0.00RPM

./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'Fan6/CPU'
OK: Fan "Fan6/CPU"=2100.00RPM (OK) | Fan6/CPU=2100.00RPM

./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'Power Supply'
OK: Power Supply "Power Supply"=OK

./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'Power Supply'
CRITCAL: Power Supply "Power Supply"=State Asserted

./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'Power Supply'
OK: Power Supply "Power Supply"=OK

./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'Power Supply'

UNKNOWN: Got exception while running which: Unable to find ipmi-sensors binary in '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/sbin:/sbin:/docker/centreon/volumes/data/git/ipmi'

./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN2 -S 'Power Supply' 
UNKNOWN: Got exception while running get_output: Command '['/usr/sbin/ipmi-sensors', '-h', '10.20.49.101', '-u', 'ADMIN', '-p', 'ADMIN2', '--session-timeout', '5000']' returned non-zero exit status 1

./check_ipmi_simple_sensors.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'Power Supply 2' 
UNKNOWN: Sensor Power Supply 2 is not present
```

# Screenshots

Graphing power consumption on DELL R720 with Centreon
![Alt screenshot](/screenshots/ipmi_power_consumption.png?raw=true)

Power supply redundancy, consumption and chassis state on ESX servers (as it's using the iDrac/ILO cards directly, it's OS-independent so it can work with appliances too)
![Alt screenshot](/screenshots/ipmi_basic_checks.png?raw=true)


# Chassis status script

An additional script is available to check epected chassis state

```
./check_ipmi_simple_chassis.py -H 10.20.49.101 -U ADMIN -P ADMIN -S 'System Power' -E 'on'
OK: System Power is on
```
