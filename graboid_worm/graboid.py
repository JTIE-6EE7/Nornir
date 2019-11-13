#!/usr/local/bin/python3

'''
This script is used to collect discovery information from devices and their CDP neighbors.
'''

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

    # init list of friends
    friends = []

    # run show CDP neighbors command
    task.run(
        task=netmiko_send_command,
        command_string="show cdp neighbors detail",
        use_textfsm=True,
    )

    # parse results
    for host in task.results:
        for friend in host.result:

            if friend['mgmt_ip'] not in friends:
                friends.append(friend['mgmt_ip'])

    return friends

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn to nxos
    nr = nr.filter(platform="nxos")
    # run The Norn
    #nr.run(task=grab_info)

    # find friends
    result = nr.run(task=find_friends, num_workers=1)

    #print_result(result)

if __name__ == "__main__":
    main()