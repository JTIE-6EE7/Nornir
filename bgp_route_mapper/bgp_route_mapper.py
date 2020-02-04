#!/usr/local/bin/python3

'''
This script is used to update BGP route maps
'''

from datetime import datetime
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
        "show vlan",
        "show interface status",
        "show interface trunk",
        "show power inline",
        "show ip interface brief",
        "show ip route",
        "show ip arp",
        "show mac address-table",
        "show cdp neighbors",
        "show cdp neighbors detail",
        ]

    print(f"Collecting data from {task.host}")

    # loop over commands
    for cmd in commands:
        # send command to device
        output = task.run(task=netmiko_send_command, command_string=cmd)
        # save results with timestamp to aggregate result
        time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        task.host["info"]="\n"*2+"#"*40+"\n"+cmd+" : "+time_stamp+"\n"+"#"*40+"\n"*2+output.result
        # write output files
        task.run(
            task=files.write_file,
            filename=f"output/{task.host}_info.txt",
            content=task.host["info"],
            append=True
        )

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn
    nr.run(task=grab_info)

if __name__ == "__main__":
    main()