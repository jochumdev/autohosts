#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path

import autohosts.incus as incus
import sys
import logging

def main():
    parser = argparse.ArgumentParser(description='Script incus containers')
    parser.add_argument('--prefix', default='test', help='Prefix for container name')
    parser.add_argument('--start', type=int, default=1, help='First id of container to script via ssh')
    parser.add_argument('--count', type=int, default=1, help='Number of containers')
    parser.add_argument('script', type=Path, help='Script to execute')
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    # Read script
    try:
        script = args.script.read_bytes()
    except Exception as e:
        incus.log_message(f"Error reading script file: {e}")
        sys.exit(1)

    for i in range(args.start, args.start + args.count):
        container_name = incus.generate_name(args.prefix, i)

        if not incus.container_exists(container_name):
            incus.log_message(f"Container {container_name} does not exist")
            continue

        incus.container_execute_script(container_name, script)

if __name__ == '__main__':
    main()
