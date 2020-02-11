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
import textwrap
import json

# TODO how to deal with multiple peers

# TODO build new route maps

# TODO set communities

# TODO apply new route maps

# TODO verify route maps applied


def get_route_maps(task):
        
    # send command to device
    output = task.run(
        task=netmiko_send_command, 
        command_string="show route-map",
        use_textfsm=True
        )
    
    task.host['route_maps'] = output.result

def get_bgp_config(task):
        
    # send command to device
    output = task.run(
        task=netmiko_send_command, 
        command_string="show run | section bgp",
        )
    
    bgp_ttp_template = textwrap.dedent("""
        <group name="networks">
         network {{ network }} mask {{ mask }}
         aggregate-address {{ network }} {{ mask }} summary-only
        </group>
        <group name="aggregates">
         aggregate-address {{ network }} {{ mask }} summary-only
        </group>
        <group name="neighbors">
         neighbor {{ neighbor }} remote-as {{ remote_as }}
         neighbor {{ neighbor }} description {{ description }}
         neighbor {{ neighbor }} route-map {{ route_map_out }} out
         neighbor {{ neighbor }} route-map {{ route_map_in }} in
        </group>
    """)

    parser = ttp(data=output.result, template=bgp_ttp_template)
    parser.parse()
    
    task.host['bgp_config'] = json.loads(parser.result(format='json')[0])

def print_results(task):
    print(task.host)
    pp(task.host['bgp_config'])

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn to get route maps
    nr.run(task=get_route_maps)
    # run The Norn to get bgp config
    nr.run(task=get_bgp_config)
    # run The Norn to print results
    nr.run(task=print_results)


    """
    fake_route_map = [
        {'action': 'deny',
         'match_clauses': [],
         'name': 'DENY_ANY',
         'seq': '10',
         'set_clauses': []},
        {'action': 'permit',
         'match_clauses': ['as-path (as-path filter): 1'],
         'name': 'VERIZON_OUT',
         'seq': '10',
         'set_clauses': []},
        {'action': 'deny',
         'match_clauses': [],
         'name': 'VERIZON_OUT',
         'seq': '20',
         'set_clauses': []}
    ]
    """
    
    fake_bgp = """
    router bgp 65000
     network 10.10.192.0 mask 255.255.255.0
     network 10.10.193.0 mask 255.255.255.0
     network 10.10.194.0 mask 255.255.255.0
     aggregate-address 10.10.192.0 255.255.240.0 summary-only
     neighbor 11.11.11.11 remote-as 65111
     neighbor 11.11.11.11 next-hop-self
     neighbor 11.11.11.11 route-map VERIZON_OUT out
     neighbor 11.11.11.11 route-map VERIZON_IN in
     neighbor 11.11.11.11 description MPLS1
     neighbor 22.22.22.22 remote-as 65222
     neighbor 22.22.22.22 route-map ATT_OUT out
     neighbor 22.22.22.22 route-map ATT_IN in
     neighbor 22.22.22.22 description MPLS2
     neighbor 33.33.33.33 remote-as 65333
     neighbor 33.33.33.33 route-map CenturyLink_OUT out
     neighbor 33.33.33.33 route-map CenturyLink_IN in
     neighbor 33.33.33.33 description MPLS3
    """

    bgp_ttp_template = """
    <group name="networks">
     network {{ network }} mask {{ mask }}
     aggregate-address {{ network }} {{ mask }} summary-only
    </group>
    <group name="aggregates">
     aggregate-address {{ network }} {{ mask }} summary-only
    </group>
    <group name="neighbors">
     neighbor {{ neighbor }} remote-as {{ remote_as }}
     neighbor {{ neighbor }} description {{ description }}
     neighbor {{ neighbor }} route-map {{ route_map_out }} out
     neighbor {{ neighbor }} route-map {{ route_map_in }} in
    </group>
    """
    
    parser = ttp(data=fake_bgp, template=bgp_ttp_template)
    parser.parse()
    
    """
    bgp_config = json.loads(parser.result(format='json')[0])
    
    if type(bgp_config[0]['neighbors']) == list:
        for neighbor in bgp_config[0]['neighbors']:
            print(neighbor)
    else:
        print(bgp_config[0]['neighbors'])
    print()

    if type(bgp_config[0]['networks']) == list:
        for network in bgp_config[0]['networks']:
            print(network)
    else:
        print(bgp_config[0]['networks'])
    print()

    if type(bgp_config[0]['aggregates']) == list:
        for aggregate in bgp_config[0]['aggregates']:
            print(aggregate)
    else:
        print(bgp_config[0]['aggregates'])
    print()

    for map in fake_route_map:
        pp(map)
    """
    print()

if __name__ == "__main__":
    main()