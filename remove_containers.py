#!/usr/bin/env python3

import argparse
import logging
import concurrent.futures

import autohosts.incus as incus


def remove_container(params):
    prefix, i = params
    container_name = incus.generate_name(prefix, i)
    if incus.container_exists(container_name):
        incus.container_remove(container_name)


def main():
    parser = argparse.ArgumentParser(description='Remove Incus containers')
    parser.add_argument('--prefix', default='test', help='Prefix for container names')
    parser.add_argument('--start', type=int, default=1, help='First id of container to remove')
    parser.add_argument('--count', type=int, required=True, help='Number of containers to remove')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    # Prepare parameters for parallel processing
    params = [(args.prefix, i) for i in range(args.start, args.start + args.count)]

    # Remove containers in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        list(executor.map(remove_container, params))


if __name__ == '__main__':
    main()