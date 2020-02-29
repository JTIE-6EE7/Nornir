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
from pprint import pprint as pp

# Run commands on each switch
def run_commands(task):

    # run "show version" on each host
    sh_version = task.run(
        task=netmiko_send_command,
        command_string="show version",
        use_textfsm=True,
    )

    # run "show switch detail" on each host
    sh_switch = task.run(
        task=netmiko_send_command,
        command_string="show switch detail",
        use_textfsm=True,
    )

    # save show version output to task.host
    task.host['sh_version'] = sh_version.result[0]
    # pull version from show version
    task.host['current_version'] = task.host['sh_version']['version']
    # save show switch detail output to task.host
    task.host['sh_switch'] = sh_switch.result
    # init and build list of switches in stack
    task.host['switches'] = []
    for sw in sh_switch.result:
        task.host['switches'].append(sw['switch'])


# Check "show version" for current software
def check_ver(task):

    # upgraded image to be used
    desired = task.host['upgrade_version']
    # record current software version
    current = task.host['current_version']

    # compare current with desired version
    if current == desired:
        print(f"\n{task.host} is running {current} and does not need to be upgraded.")
        # set host upgrade flag to False
        task.host['upgrade'] = False
    else:
        print(f"\n{task.host} is running {current} and must be upgraded.")
        # set host upgrade flag to True
        task.host['upgrade'] = True


# Stack upgrader
def stack_upgrader(task):
    
    # check software version
    check_ver(task)
    # pull model from show version
    sw_model = task.host['sh_version']['hardware'][0]
    # list of possible switch models
    models = ['C3650', 'C3750V2', 'C3750X']

    # iterate over model list
    for model in models:
        # compare model to sh ver
        if model in sw_model and task.host['upgrade'] == True:
            # set model in task.host
            task.host['model'] = model
            # run function to upgrade
            upgrade_sw(task,model)
            

def upgrade_sw(task, model):
    print(task.host['model'])
    print(task.host['upgrade_version'])
    print(task.host['current_version'])

    


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
    # run The Norn run commands
    nr.run(task=run_commands)
    # run The Norn model check
    nr.run(task=stack_upgrader)
    # run The Norn version check
    #nr.run(task=check_ver)
    # run The Norn file copy
    #nr.run(task=file_copy)
    # run The Norn set boot
    #nr.run(task=set_boot)
    # run The Norn reload
    #nr.run(task=reload_sw)

    print(nr.data.failed_hosts)


def ver_output():
    _output = """

    ISE_3650
    [{'config_register': '0x102',
    'hardware': ['WS-C3650-48PD'],
    'hostname': 'ISE_3650',
    'mac': ['38:90:a5:67:5f:00'],
    'reload_reason': 'Reload Command',
    'rommon': 'IOS-XE',
    'running_image': 'packages.conf',
    'serial': ['FDO2129Q2N8'],
    'uptime': '4 weeks, 5 days, 23 hours, 14 minutes',
    'version': '16.9.4'}]

    ISE_3750
    [{'config_register': '0xF',
    'hardware': ['WS-C3750V2-24PS'],
    'hostname': 'ISE_3750',
    'mac': ['B4:A4:E3:DE:FB:80'],
    'reload_reason': 'power-on',
    'rommon': 'Bootstrap',
    'running_image': 'c3750-ipbasek9-mz.122-55.SE12.bin',
    'serial': ['FDO1436V27C'],
    'uptime': '1 week, 2 days, 20 hours, 37 minutes',
    'version': '12.2(55)SE12'}]

    ISE_3750X
    [{'config_register': '0xF',
    'hardware': ['WS-C3750X-24'],
    'hostname': 'ISE_3750X',
    'mac': ['F8:72:EA:A5:47:00'],
    'reload_reason': 'Reload command',
    'rommon': 'Bootstrap',
    'running_image': 'c3750e-universalk9-mz.152-4.E8.bin',
    'serial': ['FDO1720H3EZ'],
    'uptime': '4 weeks, 6 days, 19 hours, 27 minutes',
    'version': '15.2(4)E8'}]

    """


if __name__ == "__main__":
    main()
