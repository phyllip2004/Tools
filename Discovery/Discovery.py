"""
VERSION 0.2
Written by phyllip2004
This script takes an input CSV and provides a report of device information for each IP listed.
v0.2.1 - Add log file and clean up console logging
v0.2.2 - Added prompt for initials for file naming. Changed log file name to include date/time.
v0.2.3 - Added prompt for debug logging
v0.2.4 - Added telnet support
v0.2.5 - Added folders for inventory and config backups
"""

import os, csv, re, time, logging
from datetime import datetime, timedelta
from netmiko import ConnectHandler

# set starting time
start = time.time()

# define variables
ip_list = []
user_list = []
pass_list = []
secret_list = []
count = 0


def connect(ip, user, password, secret):
    # try ssh
    logging.info(f'Trying to connect to {ip} over SSH')
    cisco = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': user,
        'password': password,
        'secret': secret
    }
    try:
        return ConnectHandler(**cisco)
    except Exception:
        try:
            # try telnet
            logging.info(f'Trying to connect to {ip} over telnet')
            cisco = {
                'device_type': 'cisco_ios_telnet',
                'ip': ip,
                'username': user,
                'password': password,
                'secret': secret
            }
            return ConnectHandler(**cisco)
        except Exception:
            pass


while True:
    initials = input('Enter your initials (max 3): ')
    if not initials.isalpha() or len(initials) > 3:
        print('Try again.')
    else:
        break

while True:
    debug_level = input('Enable debugging? (y/n): ')
    if not debug_level == 'y' and not debug_level == 'n':
        print('Try again.')
    elif debug_level == 'y':
        print('logging level set to debug')
        logging.basicConfig(filename=f'Discovery_Log_{time.strftime("%m_%d_%Y_%H%M%S")}.txt', level=logging.DEBUG,
                            format='%(asctime)s:%(levelname)s:%(message)s')
        break
    else:
        logging.basicConfig(filename=f'Discovery_Log_{time.strftime("%m_%d_%Y_%H%M%S")}.txt', level=logging.INFO,
                            format='%(asctime)s:%(levelname)s:%(message)s')
        break

try:
    logging.info('Creating subdirectories in working directory')
    os.mkdir('DeviceConfigs')
    os.mkdir('DeviceInventories')
except Exception:
    pass

with open('DeviceList.csv') as csv_file:
    print('Found DeviceList.csv Thank you.')
    logging.info('Found DeviceList.csv. Thank you.')
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
        else:
            ip_list.append(row[0])
            user_list.append(row[1])
            pass_list.append(row[2])
            secret_list.append(row[3])

            line_count += 1
    print('Found ' + str(len(ip_list)) + ' IP addresses.')
    logging.info('Found ' + str(len(ip_list)) + ' IP addresses.')

with open(f'Discovery_Report_{time.strftime("%m_%d_%Y_%H%M%S")}.csv', mode='a', newline='') as device_report:
    device_report_writer = csv.writer(device_report, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for ip in ip_list:
        print('PROGRESS: ' + str(count + 1) + '/' + str(len(ip_list)))
        logging.info('PROGRESS: ' + str(count + 1) + '/' + str(len(ip_list)))

        # ping with OS and look for Received = 4
        ping_response = os.popen(f"ping {ip}").read()
        if f"Received = 4" in ping_response:
            logging.info(f'{ip} is reachable.')
            try:
                logging.info(f'Trying to connect to {ip}...')

                # connect to device
                try:
                    net_connect = connect(ip, str(user_list[count]), str(pass_list[count]), str(secret_list[count]))
                except:
                    net_connect = connect(ip, str(user_list[count]), str(pass_list[count]), '')

                if net_connect.check_enable_mode is False:
                    logging.info(f'Not in enable mode on {ip}. Enabling.')
                    net_connect.enable()

                # execute show version on router and save output to output object
                output = net_connect.send_command('show version')

                # finding hostname in output using regular expressions
                regex_hostname = re.compile(r'(\S+)\suptime')
                hostname = regex_hostname.findall(output)
                logging.debug(f'hostname is {hostname}')

                # finding uptime in output using regular expressions
                regex_uptime = re.compile(r'\S+\suptime\sis\s(.+)')
                uptime = regex_uptime.findall(output)
                logging.debug(f'uptime is {uptime}')
                regex_uptime_years = re.compile(r'(\S)\syear')
                regex_uptime_weeks = re.compile(r'(\d+)\sweek')
                regex_uptime_days = re.compile(r'(\S)\sday')
                uptime_years = regex_uptime_years.findall(str(uptime))
                uptime_weeks = regex_uptime_weeks.findall(str(uptime))
                uptime_days = regex_uptime_days.findall(str(uptime))
                days_ago = 0
                if len(uptime_years) > 0:
                    days_ago = days_ago + (int(str(uptime_years[0])) * 365)
                if len(uptime_weeks) > 0:
                    days_ago = days_ago + (int(str(uptime_weeks[0])) * 7)
                if len(uptime_days) > 0:
                    days_ago = days_ago + int(str(uptime_days[0]))
                boot_date = (datetime.today() - timedelta(days=days_ago)).strftime('%m-%d-%Y')
                logging.debug(f'boot_date is {boot_date}')

                # finding version in output using regular expressions
                regex_version = re.compile(r'Cisco\sIOS\sSoftware.+Version\s([^,]+)')
                version = regex_version.findall(output)
                logging.debug(f'version is {version}')

                # finding serial in output using regular expressions
                regex_serial = re.compile(r'Processor\sboard\sID\s(\S+)')
                serial = regex_serial.findall(output)
                logging.debug(f'serial is {serial}')

                # finding model in output using regular expressions
                regex_model = re.compile(r'[Cc]isco\s(\S+).*memory.')
                model = regex_model.findall(output)
                logging.debug(f'model is {model}')

                # save running-config
                logging.info(f'Saving running-config for {ip}.')
                try:
                    show_run = open(f'DeviceConfigs/{hostname[0]}_config_{time.strftime("%m_%d_%Y")}_{initials}.txt',
                                    "w")
                except Exception:
                    show_run = open(f'{hostname[0]}_config_{time.strftime("%m_%d_%Y")}_{initials}.txt', "w")
                output = net_connect.send_command('show running-config')
                print(output, file=show_run)
                show_run.close()

                # save inventory
                logging.info(f'Saving inventory for {ip}.')
                try:
                    show_inventory = open(f'DeviceInventories/{hostname[0]}_inventory_{time.strftime("%m_%d_%Y")}'
                                          f'_{initials}.txt', "w")
                except:
                    show_inventory = open(f'{hostname[0]}_inventory_{time.strftime("%m_%d_%Y")}_{initials}.txt', "w")
                output = net_connect.send_command('show inventory')
                print(output, file=show_inventory)
                show_inventory.close()

                device_report_writer.writerow([hostname[0], ip, boot_date, version[0], serial[0], model[0]])
            except Exception as e:
                device_report_writer.writerow(['-', ip, '-', '-', '-', '-', e])
            count += 1
        else:
            print(f'No reply from {ip}.')
            device_report_writer.writerow(['-', ip, '-', '-', '-', '-', 'No ping reply'])
            count += 1
    print('PROGRESS: COMPLETE')
    logging.info('PROGRESS: COMPLETE')
    logging.info('Runtime - ' + str(time.time() - start))
