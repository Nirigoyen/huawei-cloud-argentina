"""CCI demo backend — Flask API con contador en Redis."""
import os
import socket
import time

from flask import Flask, jsonify
import redis

app = Flask(__name__)
r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, decode_responses=True)
pod = socket.gethostname()


def _ip():
    try:
        return socket.gethostbyname(pod)
    except socket.gaierror:
        return "unknown"


@app.route("/api/health")
def health():
    return jsonify(status="ok")


@app.route("/api/info")
def info():
    try:
        redis_ok = r.ping()
    except redis.ConnectionError:
        redis_ok = False
    return jsonify(
        pod=pod,
        ip=_ip(),
        message=os.getenv("MENSAJE_DEMO", ""),
        redis_ok=redis_ok,
    )


@app.route("/api/visit", methods=["POST"])
def visit():
    count = r.incr("visits")
    return jsonify(count=count, pod=pod, ip=_ip(), timestamp=int(time.time()))


@app.route("/api/visits")
def visits():
    return jsonify(count=int(r.get("visits") or 0))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
