#!/usr/bin/env python3
# coding: utf-8

import os
import subprocess
import threading
import time
import argparse
import sys
import signal
import json
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ["PYTHONIOENCODING"] = "UTF-8"
LOG_DIR = os.path.join(BASE_DIR, 'logs')
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
START_TIMEOUT = 10
DAEMON = False
with open('cfg.json') as f:
    gconfig = json.loads(f.read())
f.close()

platform_host = gconfig['heartbeat']['host']
platform_port = gconfig['heartbeat']['port']

get_token_url = "http://{0}:{1}{2}".format(platform_host,platform_port,gconfig['heartbeat']['verify_token_uri'])
verif_token_url = "http://{0}:{1}{2}".format(platform_host,platform_port,gconfig['heartbeat']['verify_token_uri'])
platform_info_url = "http://{0}:{1}{2}".format(platform_host,platform_port,gconfig['heartbeat']['platform_info_uri'])

def get_token():
    headers = {'Content-Type': 'application/json'}
    data = {"username":gconfig["username"],"password":gconfig["password"]}
    r = requests.post(get_token_url,headers=headers,data=json.dumps(data))
    token = r.json()['data']['token']
    return token

def get_all_proxy():
    token = get_token()
    headers = {'Content-Type': 'application/json'}
    headers['Authorization'] = token
    r = requests.get(platform_info_url,headers=headers)
    platforms = r.json()['data']
    return platforms

def start_proxy(listen_port,proxyurl):
    os.environ.setdefault('PYTHONOPTIMIZE', '1')

    if os.getuid() == 0:
        os.environ.setdefault('C_FORCE_ROOT', '1')

    cmd = [
        "./jproxy",
        '-proxyport', str(listen_port),
        '-proxyurl',  proxyurl,
    ]
    p = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, cwd=BASE_DIR)
    return p

def start_all_proxy():
    platforms = get_all_proxy()
    for platform in platforms:
        start_proxy(platform['proxyport'],platform['platform_url'])

def stop_all_proxy():
    os.popen("ps aux|grep jproxy|awk '{print $2}'|xargs kill -9").read()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""
        Easemob Ops service control tools;
        Example: \r\n
        %(prog)s start all -d;
        """
    )
    parser.add_argument(
        'action', type=str,
        choices=("start", "stop", "restart", "status"),
        help="Action to run"
    )
    args = parser.parse_args()

    action = args.action

    if action == "start":
        start_all_proxy()
    elif action == "stop":
        stop_all_proxy()
    elif action == "restart":
        start_all_proxy()
        stop_all_proxy()
