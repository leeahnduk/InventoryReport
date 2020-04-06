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
# python3 inv_statistic.py --url https://192.168.30.4/ --credential dmz_api_credentials.json
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

def GetApplicationScopes(rc):
    resp = rc.get('/app_scopes')

    if resp.status_code != 200:
        print("Failed to retrieve app scopes")
        print(resp.status_code)
        print(resp.text)
    else:
        return resp.json()

def GetAppScopeId(scopes,name):
    try:
        return [scope["id"] for scope in scopes if scope["name"] == name][0]
    except:
        print("App Scope {name} not found".format(name=name))        

def ShowScopes(scopes):
    """
        List all the Scopes in Tetration Appliance
        Scope ID | Scope Name | Parent Scope | VRF | Policy Priority
        """
    columns = None
    if columns:
            headers = []
            data_list = []
    else:
        headers = ['Scope ID', 'Name', 'Parent Scope', 'VRF', 'Policy Priority']
        data_list = [[x['id'],
                    x['name'],
                    x['parent_app_scope_id'],
                    x['vrf_id'], x['policy_priority']] for x in scopes ]
    table = columnar(data_list, headers, no_borders=False)
    print(table)


def get_inventory(rc, end_point, req_payload):
    '''
    Get the list of inventory items matching the query
    '''

    all_result = []

    resp = rc.post(end_point, json_body=json.dumps(req_payload))
    results = resp.json()

    all_result += results["results"]

    while results.get("offset"):
        # Get the offset ID for page 2
        next_page = results["offset"]
        # Set the offset to page 2
        req_payload["offset"] = next_page

        resp = rc.post(end_point, json_body=json.dumps(req_payload))
        results = resp.json()

        all_result += results["results"]

    return all_result


def main():
    rc = CreateRestClient()
    scopes = GetApplicationScopes(rc)
    print (CGREEN + "Here is all scopes in your cluster: " + CEND)
    ShowScopes(scopes)
    scope_name = input(CYELLOW + "Which scope name (Root:Sub) above you want to get inventory statistic: " +CEND)
    subnet = input (CYELLOW + "Which subnet (X.X.X.X/Y) of inventory you want to query: " +CEND)
    from_year = input(CYELLOW + "From which year (yyyy) you want to query: "+CEND)
    from_month = input(CYELLOW + "Month (mm)? "+CEND)
    from_day = input(CYELLOW + "Day (dd)? "+CEND)
    to_year = input(CYELLOW + "To which year (yyyy) you want to query: "+CEND)
    to_month = input(CYELLOW + "Month (mm)? "+CEND)
    to_day = input(CYELLOW + "Day (dd)? "+CEND)
    t0 = round(datetime.datetime(int(from_year),int(from_month),int(from_day),0,0).timestamp())
    t1 = round(datetime.datetime(int(to_year),int(to_month),int(to_day),0,0).timestamp())
    # Query inventories in the scope
    req_payload = {
    "filter":
            {
                "type": "subnet",
                "field": "ip",
                "value": subnet
            },
    "scopeName": scope_name
}

#    req_payload = {'filter': {"type": "eq", "field": "ip", "value": "192.168.2.98"}}

    hosts_in_scope = get_inventory(rc, '/inventory/search', req_payload)

    talkative_list = []   # store host data with bytes

    for host in hosts_in_scope:
        req_endpoint = '/inventory/' + str(host["ip"]) + '-' + str(host["vrf_id"] + '/stats?t0=' + str(t0) +'&t1='+str(t1)+'&td=day')
        #print (req_endpoint)
        
        results = rc.get(req_endpoint).json()

        print ('Getting conversation data from ' + req_endpoint)
        for x in results:
            stats_dict = {}
            stats_dict["Hostname"] = host["host_name"]
            stats_dict["IP"] = host["ip"]
            stats_dict["Timestamp"] = x["timestamp"]
            stats_dict["OS"] = host["os"]
            stats_dict["OS Version"] = host["os_version"]
            stats_dict["MAC Address"] = host["iface_mac"]
            stats_dict["Received Bytes"] = x["result"]["rx_byte_count"]
            stats_dict["Transmited Bytes"] = x["result"]["tx_byte_count"]
            stats_dict["Total Flows"] = x["result"]["flow_count"]
            stats_dict["Received Packets"] = x["result"]["rx_packet_count"]
            stats_dict["Transmited Packets"] = x["result"]["tx_packet_count"]
        talkative_list.append(stats_dict)

    # specify csv file for exporting
    export_csvfile = './stats_hosts.csv'

    # specify csv header fields
    csv_header = ["Hostname", "IP", "Timestamp", "OS", "OS Version", "MAC Address", "Received Bytes", "Transmited Bytes",
                  "Total Flows", "Received Packets", "Transmited Packets",]

    # Export file in csv format
    with open(export_csvfile, 'w+') as f:
        writer = csv.DictWriter(f, csv_header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in talkative_list:
            writer.writerow(row)

    print ('Writing csv file to %s with %d columns' % (export_csvfile, len(csv_header)))

if __name__ == '__main__':
    main()
