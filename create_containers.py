#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import logging
import concurrent.futures

import autohosts.incus as incus

def create_container(params):
    i, prefix, image, container_type, ssh_pub_key, ignore_existing = params
    container_name = incus.generate_name(prefix, i)
    
    # Skip if container exists and --ignore-existing is set
    if ignore_existing and incus.container_exists(container_name):
        incus.log_message(f"Container {container_name} already exists, skipping...")
        return
        
    incus.container_create(container_name, image, container_type)
    incus.container_setup_ssh(container_name, ssh_pub_key)
    
    # Get and display container IP
    info = incus.container_info(container_name)
    ip = info['state']['network']['eth0']['addresses'][0]['address']
    incus.log_message(f"Container {container_name} created with IP: {ip}")

def main():
    parser = argparse.ArgumentParser(description='Create Incus containers with SSH access')
    parser.add_argument('--image', default="images:debian/bookworm", help='Image to use for containers')
    parser.add_argument('--start', type=int, default=1, help='First id of container to create')
    parser.add_argument('--count', type=int, required=True, help='Number of containers to create')
    parser.add_argument('--prefix', default='test', help='Prefix for container names')
    parser.add_argument('--type', default='t1.micro', help='Type for containers')
    parser.add_argument('--ssh-key', required=True, type=Path, 
                       help='Path to SSH public key file')
    parser.add_argument('--ignore-existing', default=False, action='store_true',
                       help='Skip creation of containers that already exist')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG)

    # Read SSH public key
    try:
        ssh_pub_key = args.ssh_key.read_text().strip()
    except Exception as e:
        incus.log_message(f"Error reading SSH key file: {e}")
        sys.exit(1)
    
    # Create containers in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Prepare parameters for each container
        params = [(i, args.prefix, args.image, args.type, ssh_pub_key, args.ignore_existing)
                 for i in range(args.start, args.start + args.count)]
        list(executor.map(create_container, params))


if __name__ == '__main__':
    main()
