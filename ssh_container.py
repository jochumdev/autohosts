#!/usr/bin/env python3

import argparse
import os
import sys
import logging

import autohosts.incus as incus


def main():
    parser = argparse.ArgumentParser(description='SSH into an Incus container')
    parser.add_argument('--prefix', default='test', help='Prefix for container name')
    parser.add_argument('number', type=int, help='Number of the container')
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    
    container_name = incus.generate_name(args.prefix, args.number)
    
    if not incus.container_exists(container_name):
        incus.log_message(f"Container {container_name} does not exist")
        sys.exit(1)
    
    # Get container info
    info = incus.container_info(container_name)
    ip = info['state']['network']['eth0']['addresses'][0]['address']
    
    # Execute SSH with interactive terminal
    # -o StrictHostKeyChecking=no and -o UserKnownHostsFile=/dev/null to ignore known_hosts
    os.execvp('ssh', [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        f'root@{ip}'
    ])

if __name__ == '__main__':
    main()