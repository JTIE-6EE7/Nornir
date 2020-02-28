#!/usr/local/bin/python3

'''
This script is used to creat or update BGP route maps to add a community
'''

import ipaddress, textwrap, json
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks import text, files
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.networking import netmiko_send_config
from nornir.plugins.tasks.networking import netmiko_save_config
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
    task.host['as_path_acl_list'] = as_path

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


def route_map_logic(task):

    # set bgp asn and community
    asn = task.host['bgp_config']['router_bgp'][0]['asn']
    community = task.host['community']
    route_maps = task.host['route_maps']

    # create log for each host
    banner = "*" * 60
    task.host['peers'] = banner

    # call function to create or referece existing as-path acl
    as_path_acl_id, new_config = as_path_acl(task.host['as_path_acl_list'])

    # iterate over neighbors to locate route-maps for validated peers
    for neighbor in task.host['bgp_config']['neighbors']:

        # check if route-map exists        
        if 'route_map_out' not in neighbor:
            neighbor['route_map_out'] = 'NONE'

        # set variables from task.host
        peer_ip = neighbor['peer_ip']
        route_map_out = neighbor['route_map_out']
        
        # validated peer check
        if peer_ip not in task.host['validated_peers']:
            # record each peer that will be skipped
            task.host['peers'] += f"\n{task.host}: peer {peer_ip} skipped"
        
        else:
            # record each peer and existing route-map
            task.host['peers'] += f"\n{task.host}: peer {peer_ip}, route-map: {route_map_out}"
            # create or update route-map for each validated peer
            new_config += update_route_map(as_path_acl_id, route_map_out, route_maps, community, peer_ip, asn)

    task.host['peers'] += f"\n{banner}"
    task.host['new_config'] = new_config


def as_path_acl(as_path_acls):
    # init acl exists flag
    as_path_acl_exists = False       

    # init list of unusable acl ids
    bad_acl_ids = []
    
    # check if any as-path acls exist    
    if as_path_acls == []:
        # if not, use id 1
        as_path_acl_id = "1" 
    
    else:        
        # parse existing as-path acls
        for acl in as_path_acls:
            # use existing as-path acls if possible
            if acl['action'] == "permit" and acl['as_path_match'] == "^$":
                as_path_acl_id = acl['as_path_acl_id']
                as_path_acl_exists = True
                as_path_cfg = ""
                break
            else:
                # add acl id to list of unusable acls
                bad_acl_ids.append(acl['as_path_acl_id'])
        
    # create new as-path acl if one does not exist
    if as_path_acl_exists == False:
        # assign a unique as-path acl id
        for i in range(1,500):
            if i not in bad_acl_ids:
                as_path_acl_id = i
                break
        as_path_cfg = textwrap.dedent(f"""
            ip as-path access-list { as_path_acl_id } permit ^$
            """)
    return as_path_acl_id, as_path_cfg


def update_route_map(
    as_path_acl_id, 
    route_map_out, 
    route_maps,
    community, 
    peer_ip, 
    asn
    ):


    # create a new route-map if one doesn't exist
    if route_map_out == "NONE":
        route_map_config = textwrap.dedent(f"""
            route-map COMMUNITY_OUT permit 10
             match as-path { as_path_acl_id }
             set community { community } additive
            route-map COMMUNITY_OUT deny 20                    
            router bgp { asn }
             neighbor { peer_ip } route-map COMMUNITY_OUT out
             neighbor { peer_ip } send-community both
            """)
    else:    
        for map in route_maps:
            if map['name'] == route_map_out and map['action'] == "permit":
                route_map_config = textwrap.dedent(f"""
                    route-map { route_map_out } permit { map['seq'] }
                     match as-path { as_path_acl_id }
                     set community { community } additive
                    router bgp { asn }             
                     neighbor { peer_ip } send-community both
                    """)
    
    return route_map_config
    

def apply_configs(task):

    # print peer status and new configs
    print(task.host['peers'])
    print(task.host['new_config'])   

    # prompt user to continue before applying configs
    banner = "#"*60 + "\n" + "#"*60
    print(f"{banner}\n****** PROCEED WITH APPLYING ABOVE CONFIG? (YES \ NO) ******\n{banner}")
    proceed = "n"
    #proceed = input("")
    if proceed.lower() == "yes":

        # push new config to each device
        task.run(
            task=netmiko_send_config,
            config_commands=task.host['new_config'],
        )
        # copy run start
        task.run(
            task=netmiko_save_config, 
        )
        
        # format and print host completed message
        complete = f"\n{'*' * 40}\n{task.host} COMPELTE\n{'*' * 40}\n"
        print(complete)

        # format log entry to be writter
        output = task.host["peers"] + task.host["new_config"] + complete
        
        # write output to log file
        task.run(
            task=files.write_file,
            filename=f"output/route_map_logs.txt",
            content=output,
            append=True
        )
    else:
        incomplete = f"\n{'*' * 40}\nCONFIG NOT APPLIED TO {task.host}\n{'*' * 40}\n"

        print(incomplete)
             # write output to log file
        
        output = task.host["peers"] + task.host["new_config"] + incomplete


        task.run(
            task=files.write_file,
            filename=f"output/route_map_logs.txt",
            content=output,
            append=True
        )


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
    nr.run(task=route_map_logic)
    # run The Norn to print results
    nr.run(task=apply_configs)
    print(f"\nFailed hosts:\n{nr.data.failed_hosts}\n")
    

if __name__ == "__main__":
    main()