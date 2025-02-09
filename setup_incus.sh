#!/usr/bin/env bash

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root"
        exit 1
    fi
}

# Function to detect package manager
detect_package_manager() {
    if [ -f "/etc/debian_version" ]; then
        echo "debian"
    elif [ -f "/etc/arch-release" ]; then
        echo "arch"
    else
        echo "unsupported"
    fi
}

# Function to install Incus on Debian-based systems
install_debian() {
    # Add Incus repository
    apt update
    apt install -y curl gpg
    curl -fsSL https://pkgs.zabbly.com/key.asc | gpg --dearmor -o /usr/share/keyrings/zabbly.gpg
    sh -c 'echo "deb [signed-by=/usr/share/keyrings/zabbly.gpg] https://pkgs.zabbly.com/incus/stable $(. /etc/os-release && echo ${VERSION_CODENAME}) main" > /etc/apt/sources.list.d/zabbly-incus-stable.list'
    apt update
    
    # Install Incus
    apt install -y incus
}

# Function to install Incus on Arch-based systems
install_arch() {
    # Install Incus from AUR
    pacman -Sy --noconfirm incus
    systemctl enable --now incus
}

# Function to configure /etc/subuid and /etc/subgid
configure_ids() {
    ! grep 'root:' /etc/subuid 1>/dev/null 2>&1 && echo "root:1000000:1000000000" >> /etc/subuid
    ! grep 'root:' /etc/subgid 1>/dev/null 2>&1 && echo "root:1000000:1000000000" >> /etc/subgid
}

# Function to add the SUDO_USER to the incus group
add_to_incus_admin_group() {
    if [[ -z "$SUDO_USER" ]]; then
        echo "SUDO_USER is not set can't add you to the incus-admin group"
        return
    fi

    echo "Adding $SUDO_USER to the incus-admin group..."
    usermod -a -G incus-admin "$SUDO_USER"
}

# Main script
check_root

configure_ids

# Detect system and install accordingly
SYSTEM_TYPE=$(detect_package_manager)

case "$SYSTEM_TYPE" in
    "debian")
        echo "Detected Debian-based system. Installing Incus..."
        install_debian
        ;;
    "arch")
        echo "Detected Arch-based system. Installing Incus..."
        install_arch
        ;;
    *)
        echo "Unsupported system. This script only supports Debian and Arch based systems."
        exit 1
        ;;
esac

add_to_incus_admin_group

echo "Incus installation completed."

incuse admin init
