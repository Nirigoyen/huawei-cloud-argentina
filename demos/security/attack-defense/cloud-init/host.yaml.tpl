#cloud-config
# admin_pass alone doesn't stick on public Ubuntu images when user_data is set
# (user_data overrides the platform's password injection). Set it explicitly.
ssh_pwauth: true
chpasswd:
  expire: false
  list: |
    root:${ecs_password}
package_update: true
packages:
  - docker.io

runcmd:
  - systemctl enable --now docker
  - docker run -d --name dvwa --restart unless-stopped -p 80:80 vulnerables/web-dvwa

write_files:
  - path: /opt/eicar1.txt
    content: |
      X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
  - path: /opt/eicar2.com
    content: |
      X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
