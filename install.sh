#!/bin/bash
add_line() {
  file="$1"
  line="$2"
  grep -qF "$line" "$file" || echo "$line" >> "$file"
}

apt-get install -y apparmor-utils python3-yaml python-passfd ecryptfs-utils lxd python3-pylxd python3-pampy openssh-server
apt-get install -y x11-xserver-utils xauth xinit pulseaudio alsa-utils # X support
install bin/hades /usr/local/bin

install -m0644 misc/hades.target /etc/systemd/system/

install -m0644 misc/hades-login.service /etc/systemd/system
systemctl enable hades-login.service

install -m0644 misc/hades-lock.service /etc/systemd/system/
systemctl enable hades-lock.service

install -m0644 misc/hades-init.service /etc/systemd/system/
systemctl enable hades-init.service

add_line /etc/subuid root:200000:1
add_line /etc/subuid root:1000:1
add_line /etc/subgid root:200000:1
add_line /etc/subgid root:1000:1
