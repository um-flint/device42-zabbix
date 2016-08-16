#!/usr/bin/env python

#
# modules
#
import ConfigParser
import requests

#
# stats
#
updated = []
failed = []
skipped = []

#
# pull in the config
#
config = ConfigParser.ConfigParser()
config.read('device42-zabbix.ini')

#
# auth to zabbix
#
zabbix_auth = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": config.get('ZABBIX', 'username'),
        "password": config.get('ZABBIX', 'password')
    },
    "id": 1
}
r = requests.post(config.get('ZABBIX', 'apiurl'), json=zabbix_auth)
res = r.json()
zabbix_key = res['result']

#
# auth to device42 and get all of the devices
#
# args = {'limit': 5, 'include_cols': 'name,custom_fields'}
args = {'include_cols': 'name,custom_fields,os'}
r = requests.get(config.get('DEVICE42', 'apiurl'), auth=(config.get('DEVICE42', 'username'), config.get('DEVICE42', 'password')), params=args)
devices = r.json()

for device in devices['Devices']:
    print '=' * 80
    d42_name = str(device['name'])
    print "Device42 device name: {}".format(d42_name)

    #
    # get the matching zabbix host
    #
    zabbix_host = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": "extend",
            "filter": {
                "host": [
                    d42_name
                ]
            }
        },
        "auth": zabbix_key,
        "id": 1
    }
    r = requests.get(config.get('ZABBIX', 'apiurl'), json=zabbix_host)
    res = r.json()

    #
    # update the zabbix host (software)
    #
    if len(res['result']):
        zabbix_hostname = res['result'][0]['host']
        zabbix_hostid = res['result'][0]['hostid']
        print "  Zabbix device name (id): {} ({})".format(zabbix_hostname, zabbix_hostid)

        try:
            software       = device['os']
            software_app_a = device['custom_fields'][0]['key'] + ': ' + device['custom_fields'][0]['value']
            software_app_b = device['custom_fields'][1]['key'] + ': ' + device['custom_fields'][1]['value']
            software_app_c = device['custom_fields'][2]['key'] + ': ' + device['custom_fields'][2]['value']
            software_app_d = device['custom_fields'][3]['key'] + ': ' + device['custom_fields'][3]['value']

            print "    Setting inventory 'software' -> {}".format(software)
            print "    Setting inventory 'software_app_a' -> {}".format(software_app_a)
            print "    Setting inventory 'software_app_b' -> {}".format(software_app_b)
            print "    Setting inventory 'software_app_c' -> {}".format(software_app_c)
            print "    Setting inventory 'software_app_d' -> {}".format(software_app_d)

            zabbix_inventory = {
                "jsonrpc": "2.0",
                "method": "host.update",
                "params": {
                    "hostid": zabbix_hostid,
                    "inventory_mode": 1, # automatic
                    "inventory": {
                        "software": software,
                        "software_app_a": software_app_a,
                        "software_app_b": software_app_b,
                        "software_app_c": software_app_c,
                        "software_app_d": software_app_d
                    }
                },
                "auth": zabbix_key,
                "id": 1
            }
            r = requests.post(config.get('ZABBIX', 'apiurl'), json=zabbix_inventory)

            if r.status_code != 200:
                print r.status_code
                print r.text
                failed.append(d42_name)
            else:
                updated.append(d42_name)

        except Exception as e:
            print "Exception: {}".format(e)
            failed.append(d42_name)

    else:
        print "  Not found in Zabbix"
        skipped.append(d42_name)

#
# display summary
#
print '=' * 80
print "Processed {} hosts ({} updated, {} failed and {} skipped)".format(len(updated)+len(failed)+len(skipped), len(updated), len(failed), len(skipped))
