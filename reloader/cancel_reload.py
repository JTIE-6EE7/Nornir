#!/usr/local/bin/python3

'''
This script is used to save the config and cancel a reload for all devices.
'''

from nornir import InitNornir
from nornir.core.filter import F
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
        command_string="reload cancel",
    )

    # Print hostnames
    print("\nConfig saved and reload cancelled for the following devices:") 
    for device_name in result.keys():
        print(device_name)
            
if __name__ == "__main__":
    main()