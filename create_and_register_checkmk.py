#!/usr/bin/env python3

import random
import argparse
import logging
from pathlib import Path
import concurrent.futures

import autohosts.incus as incus
from autohosts.checkmk import CheckmkAPI, CheckmkException
from jinja2 import Template

FOLDERS = [
    "~example~production~db",
    "~example~production~web",
    "~example~test~db",
    "~example~test~web",
    "~example~dev~db",
    "~example~dev~web",
    "~example~staging~db",
    "~example~staging~web",
]

logger = logging.getLogger(__name__)

def register_container(params):
    container_name, prefix, server, site, version, user, password, client_install_script = params
    logger.info(f"Registering container {container_name}")

    if not incus.container_exists(container_name):
        logger.warning(f"Container {container_name} does not exist")
        return

    ipv4 = incus.container_ipv4(container_name)
    
    checkmk = CheckmkAPI(server, site, user, password)
    if not checkmk.has_host(container_name):
        try:
            checkmk.create_host(container_name, ipv4, random.choice(FOLDERS))
        except CheckmkException as e:
            logger.error(e)

    incus.container_execute_script(container_name, str.encode(client_install_script))

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
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    template = Template(Path("scripts/checkmk_install_agent.sh.j2").read_text())
    client_install_script = template.render(server=args.server, site=args.site, version=args.version, user=args.user, password=args.password)

    logger.info("Creating folders")
    checkmk = CheckmkAPI(args.server, args.site, args.user, args.password)
    for folder in FOLDERS:
        try:
            checkmk.create_folder_recursive(folder)
        except CheckmkException as e:
            logger.error(e)
    
    # Prepare parameters for parallel processing
    params = [(
        incus.generate_name(args.prefix, i),
        args.prefix,
        args.server,
        args.site,
        args.version,
        args.user,
        args.password,
        client_install_script
    ) for i in range(args.start, args.start + args.count)]

    # Register containers in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        list(executor.map(register_container, params))

if __name__ == '__main__':
    main()