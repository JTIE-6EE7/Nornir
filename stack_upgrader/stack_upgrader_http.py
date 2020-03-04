#!/usr/local/bin/python3

'''
This script is used to upgrade software on Cisco Catalyst switch stacks.
'''

import threading
import socketserver
import os, sys, time, socket
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_config
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.networking import netmiko_file_transfer
from http.server import SimpleHTTPRequestHandler
from pprint import pprint as pp


# Run show commands on each switch
def run_commands(task):
    print(f'{task.host}: running show comands.')
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
    # init and build list of active switches in stack
    task.host['switches'] = []
    for sw in sh_switch.result:
        if sw['state'] == 'Ready':
            task.host['switches'].append(sw['switch'])


# Compare current and desired software version
def check_ver(task):

    # upgraded image to be used
    desired = task.host['upgrade_version']
    # record current software version
    current = task.host['current_version']

    # compare current with desired version
    if current == desired:
        print(f"{task.host}: running {current} *** upgrade NOT needed ***")
        # set host upgrade flag to False
        task.host['upgrade'] = False
    else:
        print(f"{task.host}: running {current} *** must be upgraded ***")
        # set host upgrade flag to True
        task.host['upgrade'] = True


# http server for file transfer
class ThreadedHTTPServer(object):
    handler = SimpleHTTPRequestHandler
    def __init__(self, host, port):
        self.server = socketserver.TCPServer((host, port), self.handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

    def start(self):
        self.server_thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


# Stack upgrader main function
def stack_upgrader(task):
    # check software version
    check_ver(task)
    # pull model from show version
    sw_model = task.host['sh_version']['hardware'][0].split("-")
    sw_model = sw_model[1]
    # list of possible switch models
    upgrader = {
        'C3750V2': upgrade_3750,
        'C3750X': upgrade_3750,
        'C3650': upgrade_3650,
    }

  
    if task.host['upgrade'] == True:
        # copy file to switch
        #file_copy(task)
        # run function to upgrade
        upgrader[sw_model](task)


def upgrade_3750(task):
    print(f"{task.host}: Upgraging 3750v2 software.")
    upgrade_img = task.host['upgrade_img']
    cmd = f"archive download-sw /imageonly /allow-feature-upgrade /safe \
        http://172.20.58.101:8000/{upgrade_img}"

    # run upgrade command on switch stack
    upgrade_sw = task.run(
        task=netmiko_send_command,
        use_timing=True,
        command_string=cmd,
        delay_factor=100
    )

    print(upgrade_sw.result)


def upgrade_3750x():
    print("3750x upgrade function goes here.")
            

def upgrade_3650():
    print("3650 upgrade function goes here.")
    

# Reload switches
def reload_sw(task):

    confirm = "YES"
    """
    #confirm = input("All switches are ready for reload.\n
    # Proceed with reloading all selected switches?\n
    # Type 'YES' to continue:\n")
    """
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
    
    svr_ip = "172.20.58.101"
    # Start the threaded HTTP server
    os.chdir("/Users/jt/JTGIT/Nornir/stack_upgrader/images")
    
    print("Starting HTTP server.")
    server = ThreadedHTTPServer(svr_ip, 8000)
    server.start()


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

    # Close the server
    server.stop()
    print("Stopping HTTP server.")

    print(f"Failed hosts: {nr.data.failed_hosts}")



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
