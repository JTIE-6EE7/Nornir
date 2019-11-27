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

def upgrade_os(task):

    test_file = 'c3750-ipbasek9-mz.122-55.SE7.bin'

    version = task.run(
        task=netmiko_send_command,
        command_string="show version",
        use_textfsm=True,
    )

    current = version.result[0]['running_image']

    if current == f"/{test_file}":
        print("Current version is current")
    else:
        print("Upgrade now or die.")

    #print_result(version)      ['running_image']

#    transfer = task.run(
#        task=netmiko_file_transfer,
#        source_file=f"images/{test_file}",
#        dest_file=test_file,
#        direction='put',
#    )
#
#    print_result(transfer)

    upgrade = task.run(
        task=netmiko_send_config,
        config_commands=[f"boot system flash:/{test_file}", "end", "wr mem", "reload"]
    )       

    print_result(upgrade)

def main():
    # initialize The Norn
    nr = InitNornir()
    
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")

    # run The Norn
    nr.run(task=upgrade_os)


if __name__ == "__main__":
    main()