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

def find_friends(task):
    # run show CDP neighbors command
    task.run(
        task=netmiko_send_command,
        command_string="show cdp neighbors detail",
        use_textfsm=True,
    )

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn to something
    #nr = nr.filter(platform="cisco_ios")
    # run The Norn to grab info
    #nr.run(task=grab_info)

    # run The Norn to find friends
    output = nr.run(task=find_friends, num_workers=1)

    # print initial Nornir inventory    
    print("\nOriginal inventory:\n" + "~"*20)
    for name, host in nr.inventory.hosts.items():
        print(f"{name} hostname: {host.hostname}")
        #print(f"{name} platform: {host.platform}")

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
            nr.inventory.add_host(dev_name)
            nr.inventory.hosts[dev_name].hostname = mgmt_ip

    # print updated Nornir inventory
    print("\nUpdated inventory:\n" + "~"*20)
    for name, host in nr.inventory.hosts.items():
        print(f"{name} hostname: {host.hostname}")

    print()
        
if __name__ == "__main__":
    main()