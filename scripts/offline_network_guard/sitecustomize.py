"""Opt-in audit hook for isolated tests, never loaded by normal Mage startup.

Set MAGE_OFFLINE_AUDIT=1 and add this directory to PYTHONPATH. Only loopback, bind addresses and local hostname
discovery are allowed; blocked attempts are recorded even if callers catch errors.
"""
import ipaddress
import json
import os
import sys
import socket
import traceback

LOCAL_HOSTS = {'localhost', socket.gethostname(), f'{socket.gethostname()}.local', '0.0.0.0', '::'}


def audit_network(event, args):
    if event in ('socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr'):
        host = args[0]
    elif event in ('socket.connect', 'socket.sendto'):
        address = args[1]
        if not isinstance(address, tuple):
            return  # Unix domain sockets.
        host = address[0]
    else:
        return
    if host is None:
        return
    if isinstance(host, bytes):
        host = host.decode()
    if host in LOCAL_HOSTS:
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    with open(os.environ['MAGE_OFFLINE_AUDIT_LOG'], 'a') as output:
        output.write(json.dumps({'event': event, 'host': host, 'stack': traceback.format_stack(limit=25)}) + '\n')
    raise OSError(f'Offline audit blocked network access to {host}')


if os.getenv('MAGE_OFFLINE_AUDIT') == '1':
    sys.addaudithook(audit_network)
