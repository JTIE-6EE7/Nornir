#!/usr/local/bin/python3

'''
This script is used to collect discovery information from IOS devices. 

Nornir Simple Inventory yaml files are used.
'''

from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command

def main():
    # initialize blank dict for command output
    report = {}

    # show commands to be run
    commands = ["show version", "show run", "show ip interface brief", "sh ip route", "show cdp neighbors", "show cdp neighbors detail"]

    # initialize The Norn
    nr = InitNornir()

    # filter The Norn to cisco ios
    nr = nr.filter(platform="ios")

    # loop over commands
    for cmd in commands:
        # send command to device
        response = nr.run(task=netmiko_send_command, command_string=cmd)

        # parse responses
        for k, v in response.items():
            # create new sub-dict if device does not exist
            if k not in report.keys():
                report[k] = {}   
            # add device output to report dict
            report[k][cmd] = v[0].result

    # write all collected information to file
    for device, output in report.items():

        # name the file with the device name
        with open(device + '.txt', 'w') as f: 

            # fancy formatting to begin device section
            f.write("\n\n" + "#"*20 + "\n")
            f.write('BEGIN: ' + device)
            f.write("\n" + "#"*20 + "\n\n")

            # write command output + formatting
            for cmd in output.values():
                f.write(cmd)
                f.write("\n\n\n")
                f.write("~"*50)
                f.write("\n\n")
            
            # fancy formatting to end device section
            f.write("\n\n" + "#"*20 + "\n")
            f.write('END: ' + device)
            f.write("\n" + "#"*20 + "\n\n")

    # open each new file and print to screen  
    for device in report.keys():
        with open(device + '.txt', 'r') as f:
            for line in f:
                print(line, end="")

if __name__ == "__main__":
    main()