from __future__ import annotations

import json
import re
import shutil
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"

HOST_PATTERN = re.compile(r"^[a-zA-Z0-9.-]{1,253}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

NMAP_PRESETS = {
    "quick": ["-T3", "-F"],
    "ports": ["-T3", "--top-ports", "100"],
    "service": ["-T3", "-sV", "--version-light", "--top-ports", "50"],
}


def json_response(handler: SimpleHTTPRequestHandler, status: int, payload: dict) -> None:
    data = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def read_json(handler: SimpleHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def validate_host(value: str) -> str:
    host = value.strip()
    if not host or len(host) > 253 or not HOST_PATTERN.match(host):
        raise ValueError("Use a domain or IP address, for example scanme.nmap.org")
    if ".." in host or host.startswith(".") or host.endswith("."):
        raise ValueError("Host format is invalid.")
    return host


def run_nmap(target: str, preset: str) -> dict:
    nmap = shutil.which("nmap")
    if not nmap:
        common_path = r"C:\Program Files (x86)\Nmap\nmap.exe"
        if Path(common_path).exists():
            nmap = common_path
    if not nmap:
        return {
            "ok": False,
            "error": "Nmap was not found. Install it or add it to PATH.",
        }

    args = NMAP_PRESETS.get(preset)
    if args is None:
        raise ValueError("Unknown scan preset.")

    command = [nmap, *args, target]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    return {
        "ok": completed.returncode == 0,
        "command": " ".join(command),
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def query_mx(domain: str) -> list[str]:
    completed = subprocess.run(
        ["nslookup", "-type=mx", domain],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    output = completed.stdout + "\n" + completed.stderr
    records: list[str] = []
    for line in output.splitlines():
        line = line.strip()
        marker = "mail exchanger ="
        if marker in line:
            records.append(line.split(marker, 1)[1].strip().rstrip("."))
        elif "MX preference" in line and "mail exchanger" in line:
            records.append(line)
    return sorted(set(records))


def check_email(email: str) -> dict:
    address = email.strip().lower()
    if not EMAIL_PATTERN.match(address):
        return {
            "ok": False,
            "status": "invalid",
            "message": "Email syntax is invalid.",
            "mxRecords": [],
        }

    domain = address.rsplit("@", 1)[1]
    mx_records = query_mx(domain)
    if mx_records:
        return {
            "ok": True,
            "status": "deliverable-domain",
            "message": "Domain has mail servers. This does not prove the mailbox exists.",
            "domain": domain,
            "mxRecords": mx_records,
        }

    return {
        "ok": False,
        "status": "no-mx",
        "message": "Domain has no visible MX records.",
        "domain": domain,
        "mxRecords": [],
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        try:
            body = read_json(self)
            if route == "/api/nmap":
                target = validate_host(str(body.get("target", "")))
                preset = str(body.get("preset", "quick"))
                json_response(self, 200, run_nmap(target, preset))
                return

            if route == "/api/email":
                email = str(body.get("email", ""))
                json_response(self, 200, check_email(email))
                return

            json_response(self, 404, {"ok": False, "error": "Unknown endpoint."})
        except subprocess.TimeoutExpired:
            json_response(self, 408, {"ok": False, "error": "Command timed out."})
        except ValueError as exc:
            json_response(self, 400, {"ok": False, "error": str(exc)})
        except Exception as exc:
            json_response(self, 500, {"ok": False, "error": str(exc)})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8787), Handler)
    print("Security Tools Dashboard")
    print("Open http://127.0.0.1:8787")
    server.serve_forever()


if __name__ == "__main__":
    main()
