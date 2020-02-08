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
from ttp import ttp

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
    
    #print(bgp_config.result)
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

        for thing in output.result:
            #pp(thing)
            print()

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn
    nr.run(task=grab_info)

    fake_bgp = """
    router bgp 64661
     neighbor 68.136.205.69 remote-as 65000
     neighbor 68.136.205.69 route-map VERIZON_OUT out
    """

    ttp_template = """
    router bgp {{ local_as }}
     neighbor {{ neighbor_1 }} remote-as {{ remote_as_1 }}
     neighbor {{ neighbor_1 }} route-map {{ route_map_1 }}
    """
    
    parser = ttp(data=fake_bgp, template=ttp_template)
    parser.parse()
    print(parser.result(format='json')[0])


if __name__ == "__main__":
    main()