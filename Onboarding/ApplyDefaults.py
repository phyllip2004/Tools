import csv, paramiko, os, re, time
from paramiko_expect import SSHClientInteraction
from netmiko import ConnectHandler

def set_snmp(connection, snmpstring, loggingserver):
    connection.send('utils snmp config 1/2c community-string add')
    connection.expect('Enter the community string:: ')
    time.sleep(1)
    connection.send(f'{snmpstring}')
    connection.expect('.*')
    time.sleep(1)
    connection.send('ReadOnly')
    connection.expect('.*')
    time.sleep(1)
    connection.send(f'{loggingserver}')
    connection.expect('.*')
    time.sleep(1)
    connection.send('yes')
    connection.expect('admin:')

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

def network_set_defaults(connection, loggingserver, snmpstring, accesslist):
    running_config = connection.send_command('show run')
    config_commands = ['snmp-server enable traps voice',            #enabling traps
                      'snmp-server enable traps isdn',
                      'snmp-server enable traps dial',
                      'snmp-server enable traps dsp',
                      'logging trap errors',                        #set trap level errors
                      f'ip access-list standard {accesslist}',   #configure acl to only permit the logging server
                      f'permit ip {loggingserver}',
                      f'snmp-server community {snmpstring} RO {accesslist}',
                      f'snmp-server host {loggingserver} version 2c {snmpstring}',
                      f'logging host {loggingserver}']
    connection.send_config_set(config_commands=config_commands)
    running_config = connection.send_command('show run')
    for i in config_commands:
        if i != f'permit ip {loggingserver}':
            if i in running_config:
                print('Successfully set ' + i + ' on network device.')
            else:
                print('Failed to set ' + i + ' on network device.')
    connection.save_config()
    connection.disconnect()

def cucm_connect(ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password)
    connection = SSHClientInteraction(ssh, timeout=60, display=True)  # Change to False for production
    return connection

def cucm_set_defaults(connection, loggingserver, axlusername, acgname, snmpstring, ip):
    connection.expect('admin:')
    connection.send('show network cluster')
    connection.expect('admin:')
    for i in connection.current_output_clean.split('\n'):
        if ip in i and 'Publisher' in i:
            connection.send(f'run sql insert into applicationuser (name) values (\'{axlusername}\')')
            connection.expect('admin:')
            connection.send(f'run sql select pkid,name from applicationuser where name = \'{axlusername}\'')
            connection.expect('admin:')
            userpkid = (re.compile(f'(.*)\s{axlusername}').findall(connection.current_output_clean))[0]
            connection.send(f'run sql insert into dirgroup (name) values (\'{acgname}\')')
            connection.expect('admin:')
            connection.send(f'run sql select pkid,name from dirgroup where name = (\'{acgname}\')')
            connection.expect('admin:')
            acgpkid = (re.compile(f'(.*)\s{acgname}').findall(connection.current_output_clean))[0]
            connection.send(
                'run sql select pkid,name from functionrole where name = \'Standard SERVICEABILITY Read Only\'')
            connection.expect('admin:')
            servicabilitypkid = \
            re.compile(f'(.*)\sStandard\sSERVICEABILITY\sRead\sOnly').findall(connection.current_output_clean)[0]
            connection.send('run sql select pkid,name from functionrole where name = \'Standard AXL API Access\'')
            connection.expect('admin:')
            axlapipkid = re.compile(f'(.*)\sStandard\sAXL\sAPI\sAccess').findall(connection.current_output_clean)[0]
            connection.send('run sql select pkid,name from functionrole where name = \'Standard CCM Admin Users\'')
            connection.expect('admin:')
            adminuserspkid = re.compile(f'(.*)\sStandard\sCCM\sAdmin\sUsers').findall(connection.current_output_clean)[0]
            connection.send(
                f'run sql insert into functionroledirgroupmap (fkfunctionrole, fkdirgroup) values (\'{servicabilitypkid}\',\'{acgpkid}\')')
            connection.expect('admin:')
            connection.send(
                f'run sql insert into functionroledirgroupmap (fkfunctionrole, fkdirgroup) values (\'{axlapipkid}\',\'{acgpkid}\')')
            connection.expect('admin:')
            connection.send(
                f'run sql insert into functionroledirgroupmap (fkfunctionrole, fkdirgroup) values (\'{adminuserspkid}\',\'{acgpkid}\')')
            connection.expect('admin:')
            connection.send(f'run sql select fkfunctionrole,fkdirgroup from functionroledirgroupmap where fkdirgroup = \'{acgpkid}\'')
            connection.expect('admin:')
            if servicabilitypkid in connection.current_output_clean:
                print(f'Successfully set Standard SERVICEABILITY Read Only to {acgname}.')
            else:
                print(f'Failed to set Standard SERVICEABILITY Read Only to {acgname}.')
            if axlapipkid in connection.current_output_clean:
                print(f'Successfully set Standard AXL API Access to {acgname}.')
            else:
                print(f'Failed to set Standard AXL API Access to {acgname}.')
            if adminuserspkid in connection.current_output_clean:
                print(f'Successfully set Standard CCM Admin Users to {acgname}.')
            else:
                print(f'Failed to set Standard CCM Admin Users to {acgname}.')
            connection.send(f'run sql insert into applicationuserdirgroupmap (fkapplicationuser,fkdirgroup) values (\'{userpkid}\',\'{acgpkid}\')')
            connection.expect('admin:')
            connection.send(f'run sql select fkapplicationuser,fkdirgroup from applicationuserdirgroupmap where fkapplicationuser = \'{userpkid}\'')
            connection.expect('admin:')
            if userpkid in connection.current_output_clean and acgpkid in connection.current_output_clean:
                print('Successfully associated ' + axlusername + ' to ' + acgname + ' on CUCM.')
            else:
                print('Failed to associate ' + axlusername + ' to ' + acgname + ' on CUCM.')
            connection.send(
                f'run sql update processconfig set paramvalue = \'{loggingserver}\' where paramname = \'RemoteSyslogServerName5\'')
            connection.expect('admin:')
            connection.send(
                'run sql select paramvalue from processconfig where paramname = \'RemoteSyslogServerName5\'')
            connection.expect('admin:')
            if loggingserver in connection.current_output_clean:
                print('Successfully set RemoteSyslogServername5 on CUCM.')
            else:
                print('Failed to set RemoteSyslogServername5 on CUCM.')
    set_snmp(connection, snmpstring, loggingserver)
    connection.send('utils snmp config 1/2c community-string list')
    connection.expect('admin:')
    if snmpstring in connection.current_output_clean:
        print('Successfully set community string on CUCM node.')
    else:
        print('Failed to set community string on CUCM node.')
    connection.send('exit')
    
def cuc_connect(ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password)
    connection = SSHClientInteraction(ssh, timeout=60, display=True)  # Change to False for production
    return connection

def cuc_set_defaults(connection, loggingserver, snmpstring, pawsaccount, pawspassword, ip):
    connection.expect('admin:')
    connection.send('show status')
    connection.expect('admin:')
    grab = connection.current_output_clean
    connection.send('show network cluster')
    connection.expect('admin:')
    for i in connection.current_output_clean.split('\n'):
        if ip in i and 'Publisher' in i:
            connection.send(
                f'run sql update processconfig set paramvalue = \'{loggingserver}\' where paramname = \'RemoteSyslogServerName5\'')
            connection.expect('admin:')
            connection.send(
                'run sql select paramvalue from processconfig where paramname = \'RemoteSyslogServerName5\'')
            connection.expect('admin:')

            if loggingserver in connection.current_output_clean:
                print('Successfully set RemoteSyslogServername5 on CUC publisher.')
            else:
                print('Failed to set RemoteSyslogServername5 on CUC publisher.')
            connection.send(
                f'run sql update processconfig set paramvalue = \'7\' where paramname = \'RemoteSyslogSeverity\'')
            connection.expect('admin:')
            connection.send(
                f'run sql select paramvalue from processconfig where paramname = \'RemoteSyslogSeverity\'')
            connection.expect('admin:')
            if '7' in connection.current_output_clean:
                print('Successfully set RemoteSyslogSeverity on CUC publisher.')
            else:
                print('Failed to set RemoteSyslogSeverity on CUC publisher.')
        else:
            pass
    set_cuc_paws(connection, pawsaccount, pawspassword, grab)
    set_snmp(connection, snmpstring, loggingserver)
    connection.send('utils snmp config 1/2c community-string list')
    connection.expect('admin:')
    if snmpstring in connection.current_output_clean:
        print('Successfully set community string on CUC node.')
    else:
        print('Failed to set community string on CUC node.')
    connection.send('exit')

def set_cuc_paws(connection, pawsaccount, pawspassword, grab):
    connection.send(f'set account name {pawsaccount}')
    connection.expect('Please enter the privilege level :')
    connection.send('0')
    connection.expect('.*')
    time.sleep(1)
    if '12.5' in grab:
        connection.send('No')
        connection.expect('.*')
        time.sleep(1)
        connection.send(f'{pawsaccount}')
        connection.expect('.*')
        time.sleep(1)
    connection.send(f'{pawspassword}')
    connection.expect('.*')
    time.sleep(1)
    connection.send(f'{pawspassword}')
    connection.expect('admin:')
    connection.send(f'set password change-at-login disable {pawsaccount}')
    connection.expect('admin:')
    connection.send('show account')
    connection.expect('admin:')
    if f'{pawsaccount}' in connection.current_output_clean:
        print('Successfully created PAWS API user account on CUC node.')
    else:
        print('Failed to set PAWS API user account on CUC node.')

def imp_connect(ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password)
    connection = SSHClientInteraction(ssh, timeout=60, display=True)  # Change to False for production
    return connection

def imp_set_defaults(connection, loggingserver, snmpstring, pawsaccount, pawspassword):
    connection.expect('admin:')
    connection.send(f'set account name {pawsaccount}')
    connection.expect('Please enter the privilege level :')
    connection.send('0')
    connection.expect('.*')
    time.sleep(1)
    connection.send(f'{pawspassword}')
    connection.expect('.*')
    time.sleep(1)
    connection.send(f'{pawspassword}')
    connection.expect('admin:')
    connection.send(f'set password change-at-login disable {pawsaccount}')
    connection.expect('admin:')
    connection.send('show account')
    connection.expect('admin:')
    if f'{pawsaccount}' in connection.current_output_clean:
        print('Successfully created PAWS API user account on IMP node.')
    else:
        print('Failed to set PAWS API user account on IMP node.')
    set_snmp(connection, snmpstring, loggingserver)
    connection.send('utils snmp config 1/2c community-string list')
    connection.expect('admin:')
    if snmpstring in connection.current_output_clean:
        print('Successfully set community string on IMP node.')
    else:
        print('Failed to set community string on IMP node.')
    connection.send('exit')


# if these are set then you will not be prompted for them
loggingserver = ''
snmpstring = ''
pawsaccount = ''
pawspassword = ''
axlusername = ''
acgname = ''
accesslist = ''

if loggingserver == '':
    while True:
        loggingserver = input('Enter logging server: ')
        break

if snmpstring == '':
    while True:
        snmpstring = input('Enter snmp community string: ')
        break

if pawsaccount == '' and pawspassword == ':':
    while True:
        pawsaccount = input('Enter PAWS API username: ')
        pawspassword = input('Enter PAWS API password: ')
        break

if axlusername == '':
    while True:
        axlusername = input('Enter CUCM AXL username: ')
        break

start = time.time()

with open('DeviceList.csv', 'r') as device_list_csv:    # read this csv file with headers
                                                        # ip,username,password,enablesecret,devicetype
    csv_dict_reader = csv.DictReader(device_list_csv, delimiter=',')
    for row in csv_dict_reader:
        ping_response = os.popen(f"ping {row['ip']}").read()
        if f"Received = 4" in ping_response:
            if row['devicetype'] == 'NETWORK':
                print('Connecting to network device: ' + row['ip'])
                connection = network_connect(row['ip'], row['username'], row['password'], row['enablesecret'])
                network_set_defaults(connection, loggingserver, snmpstring, accesslist)
            if row['devicetype'] == 'CUCM':
                print('Connecting to CUCM device: ' + row['ip'])
                connection = cucm_connect(row['ip'], row['username'], row['password'])
                cucm_set_defaults(connection, loggingserver, axlusername, acgname, snmpstring, row['ip'])
            if row['devicetype'] == 'CUC':
                print('Connecting to CUC device: ' + row['ip'])
                connection = cuc_connect(row['ip'], row['username'], row['password'])
                cuc_set_defaults(connection, loggingserver, snmpstring, pawsaccount, pawspassword, row['ip'])
            if row['devicetype'] == 'IMP':
                print('Connecting to IMP device: ' + row['ip'])
                connection = imp_connect(row['ip'], row['username'], row['password'])
                imp_set_defaults(connection, loggingserver, snmpstring, pawsaccount, pawspassword)

print('Runtime - ' + str(time.time() - start))