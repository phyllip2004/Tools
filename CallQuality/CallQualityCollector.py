"""
Version 0.1.0
Written by phyllip2004
Connect to a CUBE and log call connection quality for all active calls using "show" commands
"""

import csv
import paramiko
import re
import time
from netmiko import ConnectHandler

ip = ''
username = ''
password = ''
enablesecret = ''

if ip == '':
    while True:
        ip = input('Enter IP to log: ')
        break

if username == '':
    while True:
        username = input('Enter username: ')
        break

if password == '':
    while True:
        password = input('Enter password: ')
        break

frequency = input('Polling rate (in seconds): ')

'''while True:
    enablesecret = input('Enter enablesecret: ')
    break'''


def network_connect(ip, user, password, enablesecret):
    # try ssh
    try:
        cisco = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': user,
            'password': password,
            'secret': enablesecret
        }
        return ConnectHandler(**cisco)
    except paramiko.ssh_exception.SSHException:
        # try telnet
        cisco = {
            'device_type': 'cisco_ios_telnet',
            'ip': ip,
            'username': user,
            'password': password,
            'secret': enablesecret
        }
        return ConnectHandler(**cisco)
    except Exception as e:
        print('Error: ' + str(e))


connection = network_connect(ip, username, password, enablesecret)

with open('CallQualityLog.csv', mode='a', newline='') as call_quality_report:
    call_quality_report_writer = csv.writer(call_quality_report, delimiter=',', quotechar='"',
                                            quoting=csv.QUOTE_MINIMAL)
    call_quality_report_writer.writerow(['CallID', 'RemoteMediaIPAddress', 'ReceiveDelay (ms)', 'TransmitPackets',
                                         'ReceivePackets', 'LostPackets', 'EarlyPackets', 'LatePackets',
                                         'OriginalCallingNumber'])

while True:
    output = connection.send_command('show call active voice | i CallID|RemoteMediaIPAddress|ReceiveDelay|'
                                     'TransmitPackets|ReceivePackets|LostPackets|EarlyPackets|LatePackets|'
                                     'OriginalCallingNumber')

    regex_callid = re.compile(r'CallID=(.*)')
    regex_remotemediaipaddress = re.compile(r'RemoteMediaIPAddress=(.*)')
    regex_receivedelay = re.compile(r'ReceiveDelay=(.*)\sms')
    regex_transmitpackets = re.compile(r'LostPackets=(.*)')
    regex_receivepackets = re.compile(r'LostPackets=(.*)')
    regex_lostpackets = re.compile(r'LostPackets=(.*)')
    regex_earlypackets = re.compile(r'EarlyPackets=(.*)')
    regex_latepackets = re.compile(r'LatePackets=(.*)')
    regex_originalcallingnumber = re.compile(r'OriginalCallingNumber=(.*)')

    callid = regex_callid.findall(output)
    remotemediaipaddress = regex_remotemediaipaddress.findall(output)
    receivedelay = regex_receivedelay.findall(output)
    transmitpackets = regex_transmitpackets.findall(output)
    receivepackets = regex_receivepackets.findall(output)
    lostpackets = regex_lostpackets.findall(output)
    earlypackets = regex_earlypackets.findall(output)
    latepackets = regex_latepackets.findall(output)
    originalcallingnumber = regex_originalcallingnumber.findall(output)

    call_leg_count = len(callid)

    with open('CallQualityLog.csv', mode='a', newline='') as call_quality_report:
        call_quality_report_writer = csv.writer(call_quality_report, delimiter=',', quotechar='"',
                                                quoting=csv.QUOTE_MINIMAL)
        call_quality_report_writer.writerow([time.strftime("%m_%d_%H:%M:%S", time.localtime())])
        count = 0
        entry = ''
        while count < call_leg_count:
            call_quality_report_writer.writerow([callid[count], remotemediaipaddress[count], receivedelay[count],
                                                 transmitpackets[count], receivepackets[count], lostpackets[count],
                                                 earlypackets[count], latepackets[count], originalcallingnumber[count]])
            count += 1
    time.sleep(int(frequency))
