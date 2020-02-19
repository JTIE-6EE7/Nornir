#!/usr/local/bin/python3

'''
This script is used to update BGP route maps to add a community
'''

import ipaddress, textwrap, json
from pprint import pprint as pp
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
        <group name="router_bgp">
        router bgp {{ asn }}
        </group>
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
            bgp_config[0][key] = [value]

    # if no neighbors found, add empty list
    if 'neighbors' not in bgp_config[0]:
        bgp_config[0]['neighbors'] = []

    # add bgp output to the Nornir task.host
    task.host['bgp_config'] = bgp_config[0]

    #print(f"{task.host}: get BGP config complete")


def get_route_maps(task):
    
    # send command to device; parse with textfsm
    output = task.run(
        task=netmiko_send_command, 
        command_string="show route-map",
        use_textfsm=True
        )
    
    # check for empty result
    if output.result:
        # add route-maps output to the Nornir task.host
        task.host['route_maps'] = output.result
    # add empty list to the Nornir task.host if no result returned
    else:
        task.host['route_maps'] = []

    #print(f"{task.host}: get route-maps complete")


def get_as_path(task):
    # send command to device
    output = task.run(
        task=netmiko_send_command, 
        command_string="show run | section ip as-path",
        )

    # TTP template for BGP config output
    as_path_ttp_template = textwrap.dedent("""
        ip as-path access-list {{ as_path_acl_id }} {{ action }} {{ as_path_match }}
        """)

    # magic TTP parsing
    parser = ttp(data=output.result, template=as_path_ttp_template)
    parser.parse()
    as_path = json.loads(parser.result(format='json')[0])

    # deal with empty lists
    if len(as_path) == 0:
        pass
    # deal with double encapsulated lists
    else:
        while type(as_path[0]) == list:
            as_path = as_path.pop()
    
    # add as-path ACLs output to the Nornir task.host
    task.host['as_path_acl'] = as_path

    #print(f"{task.host}: get as-path ACLs complete")


def validate_peer(task):

    # init validated peer list
    task.host['validated_peers'] = []

    if task.host['bgp_config']['neighbors']:
        # check if BGP peer ip is in a list of excluded ranges
        for neighbor in task.host['bgp_config']['neighbors']:
            # convert peer ip address string to ip address object
            peer_ip = ipaddress.ip_address(neighbor['peer_ip'])
            # list of excluded networks
            networks = [
                '10.254.254.0/24',
                '11.0.0.0/8',
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
    
    #print(f"{task.host}: BGP peer validation complete")


def build_route_map(task):

    # init new config string
    new_config = ""

    asn = task.host['bgp_config']['router_bgp'][0]['asn']

    print(f"{task.host} AS Path:")
    print(task.host['as_path_acl'])


    # iterate over neighbors to locate route-maps for validated peers
    for neighbor in task.host['bgp_config']['neighbors']:

        # check if route-map exists        
        if 'route_map_out' not in neighbor:
            neighbor['route_map_out'] = 'NONE'

        # set variables for easier access
        peer_ip = neighbor['peer_ip']
        route_map_out = neighbor['route_map_out']
        
        # validated peer check
        if peer_ip in task.host['validated_peers']:
            print(
                f"{task.host}: peer {peer_ip}, route-map: {route_map_out}"
            )
            
            # create a new route-map if one doesn't exist
            if route_map_out == "NONE":
                print("Create new route-map:")
                # TODO create new route-map

                if task.host['as_path_acl'] == []:
                    as_path_acl_id = "1"
                    
                else:
                    for acl in task.host['as_path_acl']:
                        # TODO check as-path ACLs
                        # TODO check if as-path ACL exists
                    
                        if acl['action'] == "permit" and acl['as_path_match'] == "^$":
                            as_path_acl_id = acl['as_path_acl_id']

                

                new_config = new_config + textwrap.dedent(f"""
                    ip as-path access-list { as_path_acl_id } permit ^$
                    route-map COMMUNITY_OUT permit 10
                     match as-path 1
                     set community { task.host['community'] }
                    route-map COMMUNITY_OUT deny 20                    
                    router bgp { asn }
                     neighbor { peer_ip } route-map COMMUNITY_OUT out
                    """)


            else:

                pp(task.host['as_path_acl'])

                # iterate over route-maps
                for route_map in task.host['route_maps']:

                    # match route-map name to neighbor
                    if  route_map_out == route_map['name']:
                        print(route_map)

    task.host['new_config'] = new_config

    print(task.host['new_config'])
                

    # TODO check if as-path ACL exists
    # TODO create or update route-map
    # TODO set communities
    # TODO apply new route maps
    # TODO verify route maps applied


    #print(f"{task.host}: route-map creation complete")

        
def print_results(task):
    #print(task.host['bgp_config'])
    #print(task.host['route_maps'])
    #print(task.host['as_path_acl'])
    print(f"{task.host} all operations complete")


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
    print(f"\nFailed hosts:\n{nr.data.failed_hosts}\n")
    

if __name__ == "__main__":
    main()