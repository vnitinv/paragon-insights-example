from __future__ import print_function
import sys, requests
import json
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

cnf = """
set system syslog file messages any critical
set system syslog file messages authorization info
"""

def configure_syslog(**kwargs):
  #Connect to HealthBot and get kwargs
  try:
    url = 'http://config-server:9000/api/v2/config/device/%s/' % kwargs['device_id']

    r = requests.get(url)
    print(r.status_code, file=sys.stderr)
    if r.status_code != 200:
        return False
    device_info = r.json()
    hostname = device_info['host']
    userid = device_info['authentication']['password']['username']
    password = device_info['authentication']['password']['password']
    #Connect to router using PyEZ
    with Device(host=hostname, user=userid, password=password, normalize=True) as dev:
        print("connected to device")
        with Config(dev) as cu:
            cu.load(cnf, format="set")
            cu.commit()
            # notify user
            notify_url = 'http://config-server:9000/api/v1/notifications'
            r = requests.get(notify_url)
            for item in r.json()['notification']:
                if 'slack' in item:
                    webhook_url = item['slack']['url']
                    slack_data = {
                        'text': "HealthBot Loaded syslog config on device `%s`"% hostname,
                        'channel': '#hbez', 'username': 'webhookbot'}
                    response = requests.post(
                        webhook_url, data=json.dumps(slack_data),
                                            headers={'Content-Type': 'application/json'}
                    )
                    return response.ok==True
    return True
  except Exception as ex:
    print("got ex: %s"% ex)
    return False
