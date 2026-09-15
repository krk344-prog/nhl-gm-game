"""Start the local NHL GM API and Expo client with one command."""

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"


def discover_lan_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def wait_for_api(port, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(f"http://127.0.0.1:{port}/api/v1/health", timeout=1):
                return
        except (OSError, URLError):
            time.sleep(0.25)
    raise RuntimeError("The NHL GM API did not become ready within 10 seconds")


def stop_process(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def main():
    parser = argparse.ArgumentParser(description="Start NHL GM Alpha 0.2 locally")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--lan-ip", help="LAN address visible to the test phone")
    parser.add_argument("--db", help="Optional SQLite save path")
    args = parser.parse_args()

    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        raise SystemExit("Node.js/npm is required. Install Node 20 or newer first.")

    if not (MOBILE / "node_modules").exists():
        print("Installing mobile dependencies for the first run...")
        subprocess.run([npm, "install"], cwd=MOBILE, check=True)

    lan_ip = args.lan_ip or discover_lan_ip()
    env = os.environ.copy()
    env["EXPO_PUBLIC_API_URL"] = f"http://{lan_ip}:{args.port}/api/v1"

    api_command = [
        sys.executable,
        str(ROOT / "src" / "season_context_api.py"),
        "--host",
        "0.0.0.0",
        "--port",
        str(args.port),
    ]
    if args.db:
        api_command.extend(["--db", args.db])

    api = None
    expo = None
    try:
        api = subprocess.Popen(api_command, cwd=ROOT, env=env)
        wait_for_api(args.port)
        print(f"API ready for Expo Go at {env['EXPO_PUBLIC_API_URL']}")
        print("Scan the Expo QR code below with the test phone.")
        expo = subprocess.Popen([npm, "start"], cwd=MOBILE, env=env)
        return expo.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        stop_process(expo)
        stop_process(api)


if __name__ == "__main__":
    raise SystemExit(main())
