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
        print(f"\nCurrent version is current:\n{current}")
    else:
        print(f"\nUpgrade now or die.\n{current}")



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

    for sw in switch_stack.result:
        if sw['switch'] > "1":
            print("Flash copy")
            copy = task.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string=f"copy flash:/{img_file} flash{sw['switch']}:/{img_file}",
            )
                       
            print(copy.result)

            if 'confirm' in copy.result or 'Destination' in copy.result:
                copy = task.run(
                    task=netmiko_send_command,
                    use_timing=True,
                    command_string="",
                )

            print(copy.result)

            if 'confirm' in copy.result or 'Destination' in copy.result:
                copy = task.run(
                    task=netmiko_send_command,
                    use_timing=True,
                    command_string="",
                )

            print(copy.result)




            

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