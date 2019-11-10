#!/usr/local/bin/python3

'''
This script is used to collect discovery information from devices. 
'''

from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks import text, files
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command


cmd = "reload in 60"

def reloader(task, cmd):
        output = task.run(task=netmiko_send_command, command_string=cmd)
        # save results to aggregate result
        print_result(output.result)

def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn to nxos
    nr = nr.filter(platform="cisco_ios")
    # run The Norn
    #nr.run(task=reloader,cmd=cmd)
    
    # Save the config
    result = nr.run(
        task=netmiko_send_command,
        command_string="write mem",
    )
    print_result(result)

    # Reload
    continue_func(msg="Do you want to reload the device (y/n)? ")
    result = nr.run(
        task=netmiko_send_command,
        use_timing=True,
        command_string="reload",
    )

    # Confirm the reload (if 'confirm' is in the output)
    for device_name, multi_result in result.items():
        if 'confirm' in multi_result[0].result:
            result = nr.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string="y",
            )

    print("Reload scheduled in 60 minutes.") 

if __name__ == "__main__":
    main()