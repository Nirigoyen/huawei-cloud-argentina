#!/bin/bash
set -euo pipefail

## Sysctl tuning for SRT / high-throughput UDP
cat > /etc/sysctl.d/99-srt-relay.conf << 'SYSCTL'
net.core.rmem_max = 26214400
net.core.wmem_max = 26214400
net.core.udp_mem = 379008 504512 759360
net.core.netdev_max_backlog = 250000
net.core.somaxconn = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.core.default_qdisc = fq
fs.file-max = 2097152
fs.nr_open = 1048576
SYSCTL
sysctl --system

## File limits
cat > /etc/security/limits.d/srt-relay.conf << 'LIMITS'
* soft nofile 1048576
* hard nofile 1048576
LIMITS

## Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

## App directory
mkdir -p /opt/${project_name}/backend
cd /opt/${project_name}

## mediamtx.yml
cat > mediamtx.yml << 'EOF'
logLevel: info
logDestinations: [stdout]

authMethod: http
authHTTPAddress: http://backend:8000/auth
authHTTPExclude:
  - action: api
  - action: metrics
  - action: pprof

api: true
apiAddress: :9997

rtsp: false
rtmp: false
hls: false
webrtc: false
moq: false

srt: true
srtAddress: :8890

paths:
  canal1:
  canal2:
EOF

## docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  mediamtx:
    image: bluenviron/mediamtx:latest
    volumes:
      - ./mediamtx.yml:/mediamtx.yml:ro
    ports:
      - "8890:8890"
      - "8890:8890/udp"
    restart: always

  backend:
    build: ./backend
    ports:
      - "80:8000"
    environment:
      - MTX_API=http://mediamtx:9997
    volumes:
      - ./blacklist.json:/app/blacklist.json
    depends_on:
      - mediamtx
    restart: always
EOF

## blacklist.json
cat > blacklist.json << 'EOF'
[]
EOF

## backend/Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY app.py index.html ./
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

## backend/requirements.txt
cat > backend/requirements.txt << 'EOF'
fastapi
uvicorn[standard]
httpx
EOF

## backend/app.py
cat > backend/app.py << 'PYEOF'
import asyncio
import json
import time
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MTX_API = os.environ.get("MTX_API", "http://mediamtx:9997")
BL_FILE = Path("/app/blacklist.json")

_prev: dict[str, tuple[int, float]] = {}
_first: dict[str, float] = {}
_bl: set[str] = set()


def _load_bl():
    global _bl
    if BL_FILE.exists():
        try:
            _bl = set(json.loads(BL_FILE.read_text()))
        except (json.JSONDecodeError, TypeError):
            _bl = set()


def _save_bl():
    BL_FILE.write_text(json.dumps(sorted(_bl)))


_load_bl()


@app.get("/")
async def index():
    return FileResponse("/app/index.html")


@app.get("/api/clients")
async def clients():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{MTX_API}/v3/srtconns/list")
        items = r.json().get("items", []) if r.status_code == 200 else []
    except Exception:
        return []
    now = time.time()
    out = []
    for cn in items:
        if cn.get("state") != "read":
            continue
        cid = cn.get("id", "")
        op_id = cn.get("user", "") or cn.get("query", "")
        if op_id == "preview":
            continue
        bs = cn.get("bytesSent", 0)
        br = None
        if cid in _prev:
            pb, pt = _prev[cid]
            dt = now - pt
            if dt > 0:
                br = round((bs - pb) * 8 / 1000 / dt)
        _prev[cid] = (bs, now)
        if cid not in _first:
            _first[cid] = now
        out.append({
            "id": cid,
            "op_id": op_id,
            "channel": cn.get("path", ""),
            "ip": cn.get("remoteAddr", ""),
            "bitrate_kbps": br,
            "loss_pct": cn.get("packetsReceivedLossRate", 0),
            "uptime_s": round(now - _first[cid], 1),
        })
    active = {c["id"] for c in out}
    for k in list(_prev):
        if k not in active:
            del _prev[k]
    for k in list(_first):
        if k not in active:
            del _first[k]
    return out


@app.get("/api/blacklist")
async def get_bl():
    return sorted(_bl)


@app.post("/api/blacklist/{op_id}")
async def add_bl(op_id: str):
    _bl.add(op_id)
    _save_bl()
    kicked = []
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{MTX_API}/v3/srtconns/list")
            items = r.json().get("items", []) if r.status_code == 200 else []
            for cn in items:
                if cn.get("state") == "read" and (cn.get("user", "") or cn.get("query", "")) == op_id:
                    cid = cn.get("id", "")
                    await c.post(f"{MTX_API}/v3/srtconns/kick/{cid}")
                    kicked.append(cid)
    except Exception:
        pass
    return {"kicked": kicked}


@app.delete("/api/blacklist/{op_id}")
async def del_bl(op_id: str):
    _bl.discard(op_id)
    _save_bl()
    return {"ok": True}


@app.api_route("/auth", methods=["GET", "POST"])
async def auth(request: Request):
    if request.method == "GET":
        return Response(status_code=200)
    try:
        body = await request.json()
    except Exception:
        return Response(status_code=200)
    op_id = body.get("user", "") or body.get("query", "")
    if body.get("action") == "read" and op_id in _bl:
        return Response(status_code=403)
    return Response(status_code=200)


_PREVIEW_CHANNELS = {"canal1", "canal2"}
_MJPEG_BOUNDARY = b"srtframe"


async def _mjpeg_stream(srt_url: str):
    cmd = [
        "ffmpeg", "-nostats", "-hwaccel", "auto", "-i", srt_url,
        "-an", "-c:v", "mjpeg", "-q:v", "4", "-s", "640x360", "-r", "8",
        "-f", "mjpeg", "pipe:1",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
    )
    buf = bytearray()
    try:
        while True:
            chunk = await proc.stdout.read(4096)
            if not chunk:
                break
            buf.extend(chunk)
            while True:
                soi = buf.find(b"\xff\xd8")
                if soi == -1:
                    buf.clear()
                    break
                eoi = buf.find(b"\xff\xd9", soi + 2)
                if eoi == -1:
                    if soi > 0:
                        del buf[:soi]
                    break
                jpeg = bytes(buf[soi:eoi + 2])
                del buf[:eoi + 2]
                yield (
                    b"--" + _MJPEG_BOUNDARY + b"\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )
    finally:
        if proc.returncode is None:
            proc.terminate()


@app.get("/api/preview/{channel}")
async def preview(channel: str):
    if channel not in _PREVIEW_CHANNELS:
        return Response(status_code=404)
    host = urlparse(MTX_API).hostname or "mediamtx"
    srt_url = f"srt://{host}:8890?streamid=read:{channel}:preview&latency=2000000"
    return StreamingResponse(
        _mjpeg_stream(srt_url),
        media_type=f"multipart/x-mixed-replace; boundary={_MJPEG_BOUNDARY.decode()}",
    )
PYEOF

## backend/index.html (de-branded, title already substituted by Terraform)
cat > backend/index.html << 'HTMLEOF'
${index_html}
HTMLEOF

## Start
docker compose up -d --build
