# Autohosts - Incus Container Management Tools

A collection of Python scripts for managing Incus containers, with special integration for CheckMK monitoring.

## Scripts Overview

### Container Management

#### `setup_incus.sh`
Sets up Incus on your system. This script handles the installation and initial configuration of Incus on Debian-based and Arch Linux-based systems.

#### `create_containers.py`
Creates multiple Incus containers with SSH access.

```bash
./create_containers.py --count 5 --prefix test --ssh-key ~/.ssh/id_rsa.pub
```

Options:
- `--image`: Container image to use (default: images:debian/bookworm)
- `--start`: First container ID number (default: 1)
- `--count`: Number of containers to create (required)
- `--prefix`: Prefix for container names (default: test)
- `--type`: Type of instance (default: t1.micro)
- `--ssh-key`: Path to SSH public key file (required)
- `--ignore-existing`: Skip creation if container exists (default: False)
- `--workers`: Number of parallel workers (default: 4)

#### `remove_containers.py`
Removes multiple Incus containers.

```bash
./remove_containers.py --count 5 --prefix test
```

Options:
- `--prefix`: Prefix for container names (default: test)
- `--start`: First id of container to remove (default: 1)
- `--count`: Number of containers to remove (required)
- `--workers`: Number of parallel workers (default: 4)

#### `ssh_container.py`
SSH into a specific container with automatic host key handling.

```bash
./ssh_container.py --prefix test 1
```

Options:
- `--prefix`: Prefix for container name (default: test)
- `number`: Container number to SSH into (required)

### CheckMK Integration

#### `create_and_register_checkmk.py`
Creates containers and registers them with a CheckMK instance.

#### `script_containers.py`
Executes scripts across multiple containers.

## Container Naming Convention

Containers are named using the pattern: `{prefix}{number:03d}`
Example: `test001`, `test002`, etc.

## Requirements

- Python 3.6+
- Incus installed and configured
- SSH key pair for container access
- CheckMK instance (for monitoring features)

## Installation

1. Install Incus using the provided setup script:
```bash
sudo ./setup_incus.sh
```

2. Ensure you have an SSH key pair:
```bash
ssh-keygen -t rsa -b 4096
```

3. Install Python dependencies (if any required by your setup)

## Common Usage Examples

1. Create 5 containers starting from ID 1:
```bash
./create_containers.py --count 5 --ssh-key ~/.ssh/id_rsa.pub
```

2. Create 3 more containers starting from ID 6:
```bash
./create_containers.py --start 6 --count 3 --ssh-key ~/.ssh/id_rsa.pub
```

3. SSH into container number 1:
```bash
./ssh_container.py 1
```

4. Remove containers 1-5:
```bash
./remove_containers.py --count 5
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT Licensed