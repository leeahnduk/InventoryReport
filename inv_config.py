from tetpyclient import RestClient
import tetpyclient
import json
import requests.packages.urllib3
import sys
import os
import argparse
import time
import datetime
import csv
from columnar import columnar



CEND = "\33[0m"
CGREEN = "\33[32m"
CYELLOW = "\33[33m"
CRED = "\33[31m"
URED = "\33[4;31m" 
Cyan = "\33[0;36m"

# =================================================================================
# See reason below -- why verify=False param is used
# python3 inv_config.py --url https://asean-tetration.cisco.com/ --credential asean_api_credentials.json
# feedback: Le Anh Duc - anhdle@cisco.com
# =================================================================================
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser(description='Tetration Get all inventories')
parser.add_argument('--url', help='Tetration URL', required=True)
parser.add_argument('--credential', help='Path to Tetration json credential file', required=True)
args = parser.parse_args()


def CreateRestClient():
    rc = RestClient(args.url,
                    credentials_file=args.credential, verify=False)
    return rc

def GetVRFs(rc):
    # Get all VRFs in the cluster
    resp = rc.get('/vrfs')

    if resp.status_code != 200:
        print("Failed to retrieve VRFs")
        print(resp.status_code)
        print(resp.text)
    else:
        return resp.json()

def ShowVRFs(vrfs):
    """
        List all VRF ID with Tenant Name
        VRF Name | VRF ID | Tenant Name
        """
    data_list = []
    headers = ['VRF Name', 'VRF ID', 'Tenant Name']
    data_list = [[x['name'], x['vrf_id'],
                    x['tenant_name']] for x in vrfs ]
    table = columnar(data_list, headers, no_borders=False)
    print(table)


def Get_inv_Detail(rc, IP_Address, vrf_id):
    """
        Get all detail information for an IP Address in a VRF
    """
    resp = rc.get('/inventory/' + IP_Address + '-' + vrf_id)

    if resp.status_code != 200:
        print("Failed to retrieve inventory detail for " + IP_Address)
        print(resp.status_code)
        print(resp.text)
    else:
        return resp.json()

def Show_inv_Agent_Config(details):
    """
        List all the Agent config detail for an inventory
        Hostname | OS | Scopes| Auto Upgrade | PID Lookup | Enforcement Enabled | Forensics | Meltdown | SideChannel
        """
    data_list = []
    headers = ['Hostname', 'OS', 'Scopes', 'Auto Upgrade Disabled', 'PID Lookup', 'Enforcement Enabled', 'Forensics', 'Meltdown', 'SideChannel' ]
    data_list.append([details['hostname'],[details['os'] + details['os_version']],details['tags_scope_name'], details['auto_upgrade_opt_out'], details['enable_pid_lookup'], details['enforcement_enabled'], details['enable_forensics'], details['enable_meltdown'], details['enable_cache_sidechannel']])
    table = columnar(data_list, headers, no_borders=False)
    print(table)


def main():
    rc = CreateRestClient()
    vrfs = GetVRFs(rc)
    print (CGREEN + "Here is VRF and the ID in your cluster: " + CEND)
    ShowVRFs(vrfs)
    vrf_id = input(CYELLOW + "Which VRF ID above your inventory belong to: " +CEND)
    IP_Address = input (CYELLOW + "Which IP address (X.X.X.X) of inventory you want to query: " +CEND)
    inv_detail = Get_inv_Detail(rc,IP_Address,vrf_id)
    print (CGREEN + "Here is the Agent Config detail of your inventory " + IP_Address + " : " + CEND)
    Show_inv_Agent_Config(inv_detail)

if __name__ == '__main__':
    main()
