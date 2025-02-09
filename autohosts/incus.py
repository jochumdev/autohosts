import json
import subprocess
import sys
import time
import logging
import tempfile

logger = logging.getLogger(__name__)

def generate_name(prefix, number):
    return f"{prefix}{number:03d}"

def log_message(message):
    logger.info(message)

def run_command(cmd):
    """Run a command and return its output."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log_message(f"Error executing command: {' '.join(cmd)}")
        log_message(f"Error message: {e.stderr}")
        sys.exit(1)


def container_info(name):
    try:
        status = run_command(['incus', 'list', name, '--format', 'json'])
        containers_info = json.loads(status)
        for container_info in containers_info:
            if container_info['name'] == name:
                return container_info
    except subprocess.CalledProcessError:
        return {}

    return {}

def container_ipv4(name):
    info = container_info(name)
    return info['state']['network']['eth0']['addresses'][0]['address']

def container_exists(name):
    """Check if a container with the given name exists."""
    return container_info(name) != {}

def container_create(name, image, type):
    """Create a new container with the given name and image."""
    log_message(f"Creating container {name}...")
    run_command(['incus', 'launch', image, name, '--type', type])
    
    # Wait for container to be running and have an IP
    while True:
        info = container_info(name)
        if info['status'] == 'Running':
            break
        time.sleep(1)


def container_setup_ssh(name, ssh_pub_key):
    """Setup SSH access for the container."""
    log_message(f"Setting up SSH access for {name}...")
    
    # Ensure .ssh directory exists
    run_command(['incus', 'exec', name, '--', 'mkdir', '-p', '/root/.ssh'])
    
    # Add the SSH key
    run_command(['incus', 'exec', name, '--', 'sh', '-c', 
                f'echo "{ssh_pub_key}" >> /root/.ssh/authorized_keys'])
    
    # Set proper permissions
    run_command(['incus', 'exec', name, '--', 'chmod', '700', '/root/.ssh'])
    run_command(['incus', 'exec', name, '--', 'chmod', '600', 
                '/root/.ssh/authorized_keys'])

    # Install SSH server
    run_command(['incus', 'exec', name, '--', 'apt-get', 'update'])
    run_command(['incus', 'exec', name, '--', 'apt-get', 'install', '-qy', 'openssh-server'])

def container_remove(name):
    log_message(f"Removing container {name}...")
    run_command(['incus', 'rm', '--force', name])

def container_execute_script(name: str, script: bytes):
    log_message(f"Executing script on container {name}...")

    temp_file = tempfile.NamedTemporaryFile(delete=True)
    temp_file.write(script)
    temp_file.seek(0)
    run_command(['incus', 'file', 'push', temp_file.name, f'{name}{temp_file.name}'])
    temp_file.close()

    logger.info(run_command(['incus', 'exec', name, '--', 'bash', temp_file.name]))
    run_command(['incus', 'file', 'delete', f'{name}{temp_file.name}'])

