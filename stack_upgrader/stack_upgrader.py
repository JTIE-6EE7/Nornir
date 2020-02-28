#!/usr/local/bin/python3

'''
This script is used to upgrade software on Cisco switch stacks.
'''

from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_config
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.networking import netmiko_file_transfer

# TODO determin switch model
def check_model(task):
    _model = None


# Check "show version" for current software
def check_ver(task):

    # upgraded image to be used
    img_file = task.host['upgrade_img']

    # run "show version" on each host
    version = task.run(
        task=netmiko_send_command,
        command_string="show version",
        use_textfsm=True,
    )

    # record current software version
    current = version.result[0]['running_image']

    # compare current with desired version
    if current == f"/{img_file}":
        print(f"\n{task.host} is running {current} and doe not need to be upgraded")
        # set host upgrade flag to False
        task.host['upgrade'] = False
    else:
        print(f"\n{task.host} is running {current} and must be upgraded.")
        # set host upgrade flag to True
        task.host['upgrade'] = True


# Copy IOS file to device
def file_copy(task):

    # Check if upgraded needed
    if task.host['upgrade'] == True:
            
        # upgraded image to be used
        img_file = task.host['upgrade_img']

        # transfer image file to switch
        transfer = task.run(
            task=netmiko_file_transfer,
            source_file=f"images/{img_file}",
            dest_file=img_file,
            direction='put',
        )

        # print message if transfer successful
        if transfer.result == True:
            print(f"{task.host} IOS image file has been transferred.")

        # print message if transfer fails
        elif transfer.result == False:
            print(f"{task.host} IOS image file transfer has failed.")

        # check switch stack information
        switch_stack = task.run(
            task=netmiko_send_command,
            command_string="show switch detail",
            use_textfsm=True,
        )

        # if more than 1 switch, copy software to other switches
        for sw in switch_stack.result:
            if sw['switch'] > "1":
                # file copy
                copy = task.run(
                    task=netmiko_send_command,
                    use_timing=True,
                    command_string=f"copy flash:/{img_file} flash{sw['switch']}:/test{img_file}",
                )
                # confirm switch responses
                while 'confirm' in copy.result or 'Destination' in copy.result:
                    copy = task.run(
                        task=netmiko_send_command,
                        use_timing=True,
                        command_string="",
                    )

                # print message when complete
                print(f"{task.host} flash copy to switch {sw['switch']} in progress.")


# Set switch bootvar
def set_boot(task):

    # Check if upgraded needed
    if task.host['upgrade'] == True:

        # upgraded image to be used
        img_file = task.host['upgrade_img']

        # set switch bootvar to new image
        upgrade = task.run(
            task=netmiko_send_config,
            config_commands=[f"boot system flash:/{img_file}", "end", "wr mem"]
        )       

        # print message if successful
        if upgrade.failed == False:
            print(f"{task.host} bootvar has been set.")


# Reload switches
def reload_sw(task):

    confirm = "YES"
    #confirm = input("All switches are ready for reload.\nProceed with reloading all selected switches?\nType 'YES' to continue:\n")
    if confirm == "YES":
        print("\n*** RELOADING ALL SELECTED SWITCHES ***\n")

    # Check if upgrade reload needed
    if task.host['upgrade'] == True:
        print(f"{task.host} reloading...")

        reload = task.run(
            task=netmiko_send_command,
            command_string="reload",
            use_timing=True,
        )        
        
        # Confirm the reload (if 'confirm' is in the output)
        for host in reload.result:

            if 'confirm' in reload.result:
                task.run(
                    task=netmiko_send_command,
                    use_timing=True,
                    command_string="",
                )

        print_result(reload)
   

def main():

    # initialize The Norn
    nr = InitNornir()
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn model check
    nr.run(task=check_model)
    # run The Norn version check
    #nr.run(task=check_ver)
    # run The Norn file copy
    #nr.run(task=file_copy)
    # run The Norn set boot
    #nr.run(task=set_boot)
    # run The Norn reload
    #nr.run(task=reload_sw)


if __name__ == "__main__":
    main()
    