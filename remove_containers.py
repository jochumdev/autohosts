#!/usr/bin/env python3

import argparse
import logging

import autohosts.incus as incus


def main():
    parser = argparse.ArgumentParser(description='Remove Incus containers')
    parser.add_argument('--prefix', default='test', help='Prefix for container names')
    parser.add_argument('--start', type=int, default=1, help='First id of container to remove')
    parser.add_argument('--count', type=int, required=True, help='Number of containers to remove')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    for i in range(args.start, args.start + args.count):
        container_name = incus.generate_name(args.prefix, i)
        if incus.container_exists(container_name):
            incus.container_remove(container_name)

if __name__ == '__main__':
    main()