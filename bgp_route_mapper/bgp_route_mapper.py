#!/usr/local/bin/python3

'''
This script is used to update BGP route mapper
'''

from datetime import datetime
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks import text, files
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command
from pprint import pprint as pp

# TODO get BGP config

# TODO get BGP summary

# TODO how to deal with multiple peers

# TODO get existing route maps

# TODO build new route maps

# TODO set communities

# TODO apply new route maps

# TODO verify route maps applied


def grab_info(task):
    # show commands to be run
    cmd = "show run | section bgp"

    bgp_config = task.run(
        task=netmiko_send_command, 
        command_string=cmd,
        )

    print(bgp_config.result)
#    for line in bgp_config.result:
#        print(line)
        
    commands = [
#        "show route-map",
        "show ip bgp summary",
#        "show ip bgp neighbor",

        ]

    # loop over commands
    for cmd in commands:
        # send command to device
        output = task.run(
            task=netmiko_send_command, 
            command_string=cmd,
            use_textfsm=True
            )

#        print(output.result)
        for thing in output.result:
            pp(thing)
            print()
        #pp(output.result)
        # save results with timestamp to aggregate result
        time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#        task.host["info"]=output.result
#        # write output files
#        task.run(
#            task=files.write_file,
#            filename=f"output/{task.host}_info.txt",
#            content=task.host["info"],
#        )


def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn
    nr.run(task=grab_info)

if __name__ == "__main__":
    main()