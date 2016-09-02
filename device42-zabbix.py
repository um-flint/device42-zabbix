#!/usr/bin/env python

#
# modules
#
import ConfigParser
import json
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
# args = {'limit': 5, 'include_cols': 'name,custom_fields,os,customer,service_level'}
args = {'include_cols': 'name,custom_fields,os,customer,service_level'}
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
            "selectGroups": "extend",
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

    if len(res['result']):
        #
        # update the zabbix host (inventory > software)
        #
        zabbix_hostname = res['result'][0]['host']
        zabbix_hostid = res['result'][0]['hostid']
        print "  Zabbix device name (id): {} ({})".format(zabbix_hostname, zabbix_hostid)

        try:

            if device['os'] and device['custom_fields'][0]['value'] and device['custom_fields'][1]['value'] and device['custom_fields'][2]['value'] and device['custom_fields'][3]['value']:

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

        #
        # holds the host group ids for customer and service_level
        #
        zabbix_groupid = []

        #
        # update the zabbix host (host group based on customer)
        #
        try:

            zabbix_host_group = {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "output": "extend",
                    "filter": {
                        "name": [
                            device['customer']
                        ]
                    }
                },
                "auth": zabbix_key,
                "id": 1
            }

            r2 = requests.post(config.get('ZABBIX', 'apiurl'), json=zabbix_host_group)

            if r2.status_code != 200:
                print r2.status_code
                print r2.text

            else:
                if r2.json()['result']:
                    print "  Zabbix host group ({}) found".format(device['customer'])
                    zabbix_groupid.append(r2.json()['result'][0]['groupid'])

                else:
                    print "  Zabbix host group ({}) not found, creating".format(device['customer'])

                    zabbix_host_group = {
                        "jsonrpc": "2.0",
                        "method": "hostgroup.create",
                        "params": {
                            "name": device['customer']
                        },
                        "auth": zabbix_key,
                        "id": 1
                    }

                    r3 = requests.post(config.get('ZABBIX', 'apiurl'), json=zabbix_host_group)

                    if r3.status_code != 200:
                        print r3.status_code
                        print r3.text
                    else:
                        zabbix_groupid.append(r3.json()['result']['groupids'][0])

        except Exception as e:
            print "Exception: {}".format(e)

        #
        # update the zabbix host (host group based on service_level)
        #
        try:

            zabbix_host_group = {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "output": "extend",
                    "filter": {
                        "name": [
                            device['service_level']
                        ]
                    }
                },
                "auth": zabbix_key,
                "id": 1
            }

            r2 = requests.post(config.get('ZABBIX', 'apiurl'), json=zabbix_host_group)

            if r2.status_code != 200:
                print r2.status_code
                print r2.text

            else:
                if r2.json()['result']:
                    print "  Zabbix host group ({}) found".format(device['service_level'])
                    zabbix_groupid.append(r2.json()['result'][0]['groupid'])

                else:
                    print "  Zabbix host group ({}) not found, creating".format(device['service_level'])

                    zabbix_host_group = {
                        "jsonrpc": "2.0",
                        "method": "hostgroup.create",
                        "params": {
                            "name": device['service_level']
                        },
                        "auth": zabbix_key,
                        "id": 1
                    }

                    r3 = requests.post(config.get('ZABBIX', 'apiurl'), json=zabbix_host_group)

                    if r3.status_code != 200:
                        print r3.status_code
                        print r3.text
                    else:
                        zabbix_groupid.append(r3.json()['result']['groupids'][0])

            #
            # make sure the host is in the host group
            #
            if zabbix_groupid:

                print "    Ensuring host {} is in host group(s) {}".format(zabbix_hostid, ','.join(zabbix_groupid))

                zabbix_group_ids = [dict(groupid=int(i)) for i in zabbix_groupid]
                # print zabbix_group_ids

                zabbix_host_massadd = {
                    "jsonrpc": "2.0",
                    "method": "hostgroup.massadd",
                    "params": {
                        "groups": zabbix_group_ids,
                        "hosts": [{
                            "hostid": int(zabbix_hostid)
                        }]
                    },
                    "auth": zabbix_key,
                    "id": 1
                }

                # print zabbix_host_massadd

                r4 = requests.post(config.get('ZABBIX', 'apiurl'), json=zabbix_host_massadd)

                if r4.status_code != 200:
                    print r4.status_code
                    print r4.text

        except Exception as e:
            print "Exception: {}".format(e)

    else:
        print "  Not found in Zabbix"
        skipped.append(d42_name)

#
# display summary
#
print '=' * 80
print "Processed {} hosts ({} updated, {} failed and {} skipped)".format(len(updated)+len(failed)+len(skipped), len(updated), len(failed), len(skipped))
