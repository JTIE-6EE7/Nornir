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
    # filter The Norn to nxos
    #nr = nr.filter(platform="cisco_ios")
    # run The Norn
    #nr.run(task=grab_info)

    # find friends
    output = nr.run(task=find_friends, num_workers=1)
    
    print("\nOriginal inventory:\n" + "~"*20)
    for name, host in nr.inventory.hosts.items():
        print(f"{name} hostname: {host.hostname}")
        #print(f"{name} platform: {host.platform}")

    for host in output:
        for friend in output[host][1].result:
            platform = nr.inventory.hosts[host].platform
            if platform == "nxos":
                dev_name = re.split("\.|\(", friend['dest_host'])[0]
                mgmt_ip = friend['mgmt_ip']

            elif platform == "cisco_ios":
                dev_name = re.split("\.|\(", friend['destination_host'])[0]
                mgmt_ip = friend['management_ip']
            
            nr.inventory.add_host(dev_name)
            nr.inventory.hosts[dev_name].hostname = mgmt_ip

    print("\nUpdated inventory:\n" + "~"*20)
    #print(nr.inventory.hosts)
    #nr.inventory.add_host("Test")
    #nr.inventory.hosts["Test"].hostname = "Testing"
    for name, host in nr.inventory.hosts.items():
        print(f"{name} hostname: {host.hostname}")

    print()
        
if __name__ == "__main__":
    main()