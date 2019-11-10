#!/usr/local/bin/python3

'''
This script is used to collect discovery information from devices. 

'''

from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks import text, files
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command

def grab_info(task):
    # show commands to be run
    commands = [
        "show version",
        "show run",
        "show vlan brief",
        "show interface trunk",
        "show ip interface brief",
        "show ip route",
        "show cdp neighbors",
        "show cdp neighbors detail",
        ]

    # loop over commands
    for cmd in commands:
        # send command to device
        output = task.run(task=netmiko_send_command, command_string=cmd)
        # save results to aggregate
        task.host["info"] =  "#"*30 + "\n" + cmd + "\n" + "#"*30 + "\n"*2 + output.result
        # write output files
        task.run(
            task=files.write_file,
            filename=f"{task.host}_info.txt",
            content=task.host["info"],
            append=True
        )

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn to nxos
    nr = nr.filter(platform="nxos")
    # run The Norn
    nr.run(task=grab_info)

if __name__ == "__main__":
    main()