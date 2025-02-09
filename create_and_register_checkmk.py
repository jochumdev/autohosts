#!/usr/bin/env python3

import random
import argparse
import logging
from pathlib import Path

import autohosts.incus as incus
from autohosts.checkmk import CheckmkAPI, CheckmkException
from jinja2 import Template

FOLDERS = [
    "~production~db",
    "~production~web",
    "~test~db",
    "~test~web",
    "~dev~db",
    "~dev~web",
    "~staging~db",
    "~staging~web",
]

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Register Incus containers in Checkmk')
    parser.add_argument('--prefix', default='test', help='Prefix for container name')
    parser.add_argument('--start', type=int, default=1, help='First id of container to register')
    parser.add_argument('--count', type=int, default=1, help='Number of containers')
    parser.add_argument('--server', help='Checkmk server', default='10.160.168.2')
    parser.add_argument('--site', help='Checkmk site', default='test')
    parser.add_argument('--version', help='Checkmk version', default='2.3.0p26-1')
    parser.add_argument('--user', help='Checkmk user', default='installer')
    parser.add_argument('password', help='Checkmk password')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    template = Template(Path("scripts/checkmk_install_agent.sh.j2").read_text())
    client_install_script = template.render(server=args.server, site=args.site, version=args.version, user=args.user, password=args.password)

    checkmk = CheckmkAPI(args.server, args.site, args.user, args.password)

    logger.info("Creating folders")
    changed = False
    for folder in FOLDERS:
        try:
            if checkmk.create_folder_recursive(folder):
                changed = True
        except CheckmkException as e:
            logger.error(e)

    if changed:
        try:
            checkmk.activate_changes()
        except CheckmkException as e:
            logger.error(e)

    for i in range(args.start, args.start + args.count):
        container_name = incus.generate_name(args.prefix, i)
        logger.info(f"Registering container {container_name}")

        if not incus.container_exists(container_name):
            logger.warning(f"Container {container_name} does not exist")
            continue

        ipv4 = incus.container_ipv4(container_name)

        changed = False
        if not checkmk.has_host(container_name):
            try:
                if checkmk.create_host(container_name, ipv4, random.choice(FOLDERS)):
                    changed = True
            except CheckmkException as e:
                logger.error(e)
        
        if changed:
            try:
                checkmk.activate_changes()
            except CheckmkException as e:
                logger.error(e)

        incus.container_execute_script(container_name, str.encode(client_install_script))

if __name__ == '__main__':
    main()