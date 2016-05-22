# apt-get install -y apparmor-utils python3-yaml python-passfd
install -m0644 misc/hades-lock.service /etc/systemd/system/
systemctl enable hades-lock.service
