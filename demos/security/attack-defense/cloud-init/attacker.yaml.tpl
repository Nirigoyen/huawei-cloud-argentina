#cloud-config
ssh_pwauth: true
chpasswd:
  expire: false
  list: |
    root:${ecs_password}
package_update: true
packages:
  - python3-pip
  - git

runcmd:
  - pip3 install --break-system-packages paramiko
  - git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap

write_files:
  - path: /opt/ssh_bruteforce.py
    encoding: b64
    content: ${bruteforce_b64}
  - path: /opt/run_attacks.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      echo "=== Attack & Defense demo ==="
      echo "Host IP: ${host_ip}"
      echo ""
      echo "1. SSH brute-force:"
      echo "   python3 /opt/ssh_bruteforce.py"
      echo ""
      echo "2. SQLmap (SQL injection against DVWA):"
      echo "   python3 /opt/sqlmap/sqlmap.py -u http://${host_ip}/vulnerabilities/sqli/?id=1 --dbs --level 3"
      echo ""
      echo "Run the commands above to start the attacks."
