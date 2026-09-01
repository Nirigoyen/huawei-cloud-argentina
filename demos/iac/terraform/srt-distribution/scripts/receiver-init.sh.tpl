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

## start_consumers.sh
cat > /opt/${project_name}/start_consumers.sh << CONEOF
#!/usr/bin/env bash
set -u
FF=/usr/local/bin/ffmpeg
RELAY=${relay_ip}
LATENCY=${srt_latency_us}
CONSUMER_COUNT=${consumer_count}
HALF=\$((CONSUMER_COUNT / 2))
run_con() {
  local op=\$1 ch=\$2
  while true; do
    \$FF -nostats -i "srt://\${RELAY}:8890?streamid=read:\${ch}:\${op}&latency=\${LATENCY}" \\
      -c copy -f null /dev/null >/tmp/consumer_\${op}.log 2>&1
    sleep 2
  done
}
for op in \$(seq -f "op%03g" 1 \$HALF); do run_con "\$op" canal1 & done
for op in \$(seq -f "op%03g" \$((HALF + 1)) \$CONSUMER_COUNT); do run_con "\$op" canal2 & done
wait
CONEOF
chmod +x /opt/${project_name}/start_consumers.sh

## systemd service
cat > /etc/systemd/system/srt-consumers.service << 'SVCEOF'
[Unit]
Description=SRT consumers
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/opt/${project_name}/start_consumers.sh
Restart=always
RestartSec=5
KillMode=control-group

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable --now srt-consumers.service
