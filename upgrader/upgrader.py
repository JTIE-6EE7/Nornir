#!/usr/local/bin/python3

'''
This script is used to upgrade IOS on 3750 switches
'''

from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_config
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.networking import netmiko_file_transfer


def check_ver(task):

    img_file = task.host['upgrade_img']

    version = task.run(
        task=netmiko_send_command,
        command_string="show version",
        use_textfsm=True,
    )

    current = version.result[0]['running_image']

    if current == f"/{img_file}":
        print("Current version is current")
    else:
        print("Upgrade now or die.")



def file_copy(task):

    img_file = task.host['upgrade_img']

#    transfer = task.run(
#        task=netmiko_file_transfer,
#        source_file=f"images/{img_file}",
#        dest_file=img_file,
#        direction='put',
#    )
#
#    print_result(transfer)

    switch_stack = task.run(
        task=netmiko_send_command,
        command_string="show switch detail",
        use_textfsm=True,
    )

    print_result(switch_stack)

    for sw in switch_stack.result:
        if sw['switch'] == "1":
            print("Flash copy")
            copy = task.run(
                task=netmiko_send_command,
                #command_string=f"copy flash:/{img_file} flash{sw['switch']}:/{img_file}",
                command_string=f"copy flash:/cfg.txt flash1:/cfg2.txt",
            )
                # Confirm the reload (if 'confirm' is in the output)
            for device_name, multi_result in result.items():
                if 'confirm' in multi_result[0].result or 'Destination' in multi_result[0].result:
                    print(device_name)
                    confirm = nr.run(
                        task=netmiko_send_command,
                        use_timing=True,
                        command_string="",
                    )
            print_result(copy)

            

def set_boot(task):

    upgrade = task.run(
        task=netmiko_send_config,
        config_commands=[f"boot system flash:/{img_file}", "end", "wr mem"]
    )       

    print_result(upgrade)

def main():

    # initialize The Norn
    nr = InitNornir()
    
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")

    # run The Norn version check
    nr.run(task=check_ver)

    # run The Norn file copy
    nr.run(task=file_copy)

    
    reload = input("Switches are ready for reload.\nProceed with reloading all switches? (Y/N)")
    if reload.upper() == "Y":
        print("RELOAD!")




if __name__ == "__main__":
    main()