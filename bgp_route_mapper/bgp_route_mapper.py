#!/usr/local/bin/python3

'''
This script is used to update BGP route maps to add a community
'''

import ipaddress, textwrap, json
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks import text, files
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command
from ttp import ttp


def get_bgp_config(task):
        
    # send command to device
    output = task.run(
        task=netmiko_send_command, 
        command_string="show run | section bgp",
        )
    
    # TTP template for BGP config output
    bgp_ttp_template = textwrap.dedent("""
        <group name="networks">
         network {{ network }} mask {{ mask }}
         aggregate-address {{ network }} {{ mask }} summary-only
        </group>
        <group name="aggregates">
         aggregate-address {{ network }} {{ mask }} summary-only
        </group>
        <group name="neighbors">
         neighbor {{ peer_ip }} remote-as {{ remote_as }}
         neighbor {{ peer_ip }} description {{ description }}
         neighbor {{ peer_ip }} route-map {{ route_map_out }} out
         neighbor {{ peer_ip }} route-map {{ route_map_in }} in
        </group>
    """)

    # magic TTP parsing
    parser = ttp(data=output.result, template=bgp_ttp_template)
    parser.parse()
    bgp_config = json.loads(parser.result(format='json')[0])

    # convert any rogue dicts to lists
    for key, value in bgp_config[0].items():
        if type(value) == dict:
            bgp_config[0][key] = [{key: value}]
    
    # add bgp output to the Nornir task.host
    task.host['bgp_config'] = bgp_config[0]


def get_route_maps(task):
    
    # send command to device
    output = task.run(
        task=netmiko_send_command, 
        command_string="show route-map",
        use_textfsm=True
        )
    
    task.host['route_maps'] = output.result


def get_as_path(task):
    # send command to device
    output = task.run(
        task=netmiko_send_command, 
        command_string="show run | section ip as-path",
        )

    # TTP template for BGP config output
    as_path_ttp_template = textwrap.dedent("""
        ip as-path access-list {{ as_path_acl }} permit {{ as_path_match }}
        """)

    # magic TTP parsing
    parser = ttp(data=output.result, template=as_path_ttp_template)
    parser.parse()
    as_path = json.loads(parser.result(format='json')[0])



    print(as_path)


def validate_peer(task):

    # init validated peer list
    task.host['validated_peers'] = []

    # check if BGP peer ip is in a list of excluded ranges
    for neighbor in task.host['bgp_config']['neighbors']:
        # convert peer ip address string to ip address object
        peer_ip = ipaddress.ip_address(neighbor['peer_ip'])
        # list of excluded networks
        networks = [
            '11.0.0.0/8',
            '22.0.0.0/8',
            '101.0.0.0/8',
        ]

        # init flag for excluded peers
        exclude_peer = False

        # check each peer against excluded peers list
        for network in networks:
            if peer_ip in ipaddress.ip_network(network):
                # add peer to list of excluded peerts
                exclude_peer = True
                break

        # add validated peers to list
        if exclude_peer == False:
            task.host['validated_peers'].append(str(peer_ip))
    

def build_route_map(task):

    # TODO check if route map exists
    # TODO create or update route-map
    # TODO set communities
    # TODO apply new route maps
    # TODO verify route maps applied
    print()

        
def print_results(task):
    print(f"{task.host} complete.")
    #print(task.host)
    #print(task.host['bgp_config'])
    #print(task.host['route_maps'])


def main():
    # initialize The Norn
    nr = InitNornir(config_file="config.yaml")
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn to get bgp config
    nr.run(task=get_bgp_config)
    # run The Norn to get route maps
    nr.run(task=get_route_maps)
    # run The Norn to get as-psth
    nr.run(task=get_as_path)
    # run The Norn to validate BGP peers
    nr.run(task=validate_peer)
    # run The Norn to build route maps
    nr.run(task=build_route_map)
    # run The Norn to print results
    nr.run(task=print_results)
    





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
    
if __name__ == "__main__":
    main()