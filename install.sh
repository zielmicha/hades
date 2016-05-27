#!/bin/bash
add_line() {
  file="$1"
  line="$2"
  grep -qF "$line" "$file" || echo "$line" >> "$file"
}

apt-get install -y apparmor-utils python3-yaml python-passfd ecryptfs-utils lxd python3-pylxd
apt-get install -y x11-xserver-utils xauth xinit pulseaudio alsa-utils # X support
install -m0644 misc/hades-lock.service /etc/systemd/system/
install bin/hades /usr/local/bin
systemctl enable hades-lock.service

add_line /etc/subuid root:200000:1
add_line /etc/subuid root:1000:1
add_line /etc/subgid root:200000:1
add_line /etc/subgid root:1000:1
