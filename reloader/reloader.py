#!/usr/local/bin/python3

'''
This script is used to schedule a reload in 60 minutes for all devices.
'''

from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn to nxos
    nr = nr.filter(platform="cisco_ios")
    # Save the config
    result = nr.run(
        task=netmiko_send_command,
        command_string="write mem",
    )    

    # Reload devices in 60 minutes
    result = nr.run(
        task=netmiko_send_command,
        use_timing=True,
        command_string="reload in 60",
    )

    # Confirm the reload (if 'confirm' is in the output)
    for device_name, multi_result in result.items():
        if 'confirm' in multi_result[0].result:
            result = nr.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string="",
            )
            
    print("Reload scheduled in 60 minutes for all devices.") 

if __name__ == "__main__":
    main()