#!/usr/local/bin/python3

'''
This script is used to collect discovery information from devices and their CDP neighbors.
'''

import re
from nornir import InitNornir
from nornir.core.filter import F
from nornir.core.inventory import Inventory
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
        "show interface status",
        "show ip interface brief",
        "show ip route",
        "show ip arp",
        "show mac address-table",
        "show cdp neighbors",
        "show cdp neighbors detail",
        ]

    # loop over commands
    for cmd in commands:
        # send command to device
        output = task.run(task=netmiko_send_command, command_string=cmd)
        # save results to aggregate result
        task.host["info"] =  "#"*30 + "\n" + cmd + "\n" + "#"*30 + "\n"*2 + output.result
        # write output files
        task.run(
            task=files.write_file,
            filename=f"{task.host}_info.txt",
            content=task.host["info"],
            append=True
        )

    print(f"Writing {task.host}_info.txt")

def find_friends(task):
    # run show CDP neighbors command
    task.run(
        task=netmiko_send_command,
        command_string="show cdp neighbors detail",
        use_textfsm=True,
    )

def add_friends(output, nr):
    # loop over hosts
    for host in output:
        # loop over each host's CDP neighbors
        for friend in output[host][1].result:
            # check platform to deal with ntc-template differences
            platform = nr.inventory.hosts[host].platform
            # parse Nexus CDP output
            if platform == "nxos":
                # get device name
                dev_name = re.split(r"\.|\(", friend['dest_host'])[0]
                # get device IP
                mgmt_ip = friend['mgmt_ip']
            # parse IOS CDP output
            elif platform == "cisco_ios":
                # get device name
                dev_name = re.split(r"\.|\(", friend['destination_host'])[0]
                # get device IP
                mgmt_ip = friend['management_ip']
            # add new host to The Norn iventory 
            if dev_name not in nr.inventory.hosts.keys():
                # set group based on device type
                if friend['platform'] == 'N9K-9000v':
                    groups = ['nxos']
                else:
                    groups = ['iosxe']
                # add friend to inventory
                nr.inventory.add_host(
                    name=dev_name,
                    hostname = mgmt_ip,
                    groups = groups
                )

def main():
    # initialize The Norn
    nr = InitNornir()

    # print initial Nornir inventory    
    print("\nOriginal inventory:\n" + "~"*30)
    for name, host in nr.inventory.hosts.items():
        print(f"{name} hostname: {host.hostname}")

    # run The Norn to find friends
    output = nr.run(task=find_friends)

    # add new CDP neighbors to Nornir inventory
    add_friends(output, nr)

    # print updated Nornir inventory
    print("\nFirst CDP pass inventory:\n" + "~"*30)
    for name, host in nr.inventory.hosts.items():
        print(f"{name} hostname: {host.hostname}")

    # run The Norn to find friends
    output = nr.run(task=find_friends)

    # add new CDP neighbors to Nornir inventory
    add_friends(output, nr)
    
    # print third Nornir inventory    
    print("\nSecond CDP pass inventory:\n" + "~"*30)
    for name, host in nr.inventory.hosts.items():
        print(f"{name} hostname: {host.hostname}")

    # run The Norn to grab info
    print("\nGrabbing info from all hosts:")
    print("~"*30)
    nr.run(task=grab_info)
        
if __name__ == "__main__":
    main()