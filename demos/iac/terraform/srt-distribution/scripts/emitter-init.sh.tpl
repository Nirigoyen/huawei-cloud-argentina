#!/bin/bash
set -euo pipefail

## Install static ffmpeg (johnvansickle 7.0.2 amd64)
FF_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
curl -fsSL "$FF_URL" | tar xJ -C /tmp
FF_DIR=$(find /tmp -maxdepth 1 -name "ffmpeg-*-static" -type d | head -1)
cp "$FF_DIR/ffmpeg" /usr/local/bin/
cp "$FF_DIR/ffprobe" /usr/local/bin/ 2>/dev/null || true
chmod +x /usr/local/bin/ffmpeg

## App directory
mkdir -p /opt/${project_name}

## start_publishers.sh
cat > /opt/${project_name}/start_publishers.sh << PUBEOF
#!/usr/bin/env bash
set -u
FF=/usr/local/bin/ffmpeg
RELAY=${relay_ip}
LATENCY=${srt_latency_us}
run_pub() {
  local name=\$1 src=\$2 sid=\$3
  while true; do
    \$FF -re -f lavfi -i "\$src" -c:v libx265 -b:v 3M -x265-params keyint=60:min-keyint=60 \\
      -f mpegts -pes_payload_size 1316 "srt://\${RELAY}:8890?streamid=\${sid}&latency=\${LATENCY}" \\
      >/tmp/pub_\${name}.log 2>&1
    sleep 3
  done
}
run_pub canal1 "testsrc2=size=1280x720:rate=30" "publish:canal1" &
run_pub canal2 "smptebars=size=1280x720:rate=30" "publish:canal2" &
wait
PUBEOF
chmod +x /opt/${project_name}/start_publishers.sh

## systemd service
cat > /etc/systemd/system/srt-publishers.service << 'SVCEOF'
[Unit]
Description=SRT publishers (2 channels)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/opt/${project_name}/start_publishers.sh
Restart=always
RestartSec=5
KillMode=control-group

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable --now srt-publishers.service
