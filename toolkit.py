#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HOST_PATTERN = re.compile(r"^[a-zA-Z0-9.-]{1,253}$")
OPEN_PORT_PATTERN = re.compile(r"^(\d+)/(tcp|udp)\s+open\s+(\S+)", re.IGNORECASE)

NMAP_PRESETS = {
    "1": ("Quick ports", ["-T3", "-F"]),
    "2": ("Top 100 ports", ["-T3", "--top-ports", "100"]),
    "3": ("Light service scan", ["-T3", "-sV", "--version-light", "--top-ports", "50"]),
}


class C:
    reset = "\033[0m"
    bold = "\033[1m"
    cyan = "\033[36m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    blue = "\033[34m"
    gray = "\033[90m"


@dataclass
class Box:
    width: int = 76

    def line(self, char: str = "-") -> str:
        return f"{C.gray}+{char * (self.width - 2)}+{C.reset}"

    def row(self, text: str = "", color: str = "") -> str:
        clean = strip_ansi(text)
        if len(clean) > self.width - 4:
            text = clean[: self.width - 7] + "..."
            clean = strip_ansi(text)
        pad = max(0, self.width - 4 - len(clean))
        return f"{C.gray}|{C.reset} {color}{text}{C.reset}{' ' * pad} {C.gray}|{C.reset}"

    def title(self, text: str) -> None:
        print(self.line("="))
        print(self.row(text, C.bold + C.cyan))
        print(self.line("="))


def strip_ansi(value: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", value)


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    input(f"\n{C.gray}Enter to continue...{C.reset}")


def status(label: str, text: str, color: str = C.green) -> None:
    print(f"{color}[{label}]{C.reset} {text}")


def header(box: Box) -> None:
    clear()
    box.title("SECURITY TOOLKIT")
    print(box.row("Terminal tools for legal labs"))
    print(box.row("Nmap | DNS | Headers | Ping | Email MX"))
    print(box.line())


def menu_row(box: Box, key: str, name: str, hint: str = "") -> None:
    left = f"{key}. {name}"
    if hint:
        left = f"{left:<24} {C.gray}{hint}{C.reset}"
    print(box.row(left, C.green if key != "0" else C.yellow))


def ask(prompt: str, default: str = "") -> str:
    label = f"{prompt}"
    if default:
        label += f" [{default}]"
    value = input(f"{C.cyan}{label} > {C.reset}").strip()
    return value or default


def find_nmap() -> str | None:
    nmap = shutil.which("nmap")
    if nmap:
        return nmap
    windows_path = r"C:\Program Files (x86)\Nmap\nmap.exe"
    if os.path.exists(windows_path):
        return windows_path
    return None


def validate_host(value: str) -> str:
    host = value.strip().lower()
    host = host.removeprefix("http://").removeprefix("https://").split("/", 1)[0]
    if not host or len(host) > 253 or not HOST_PATTERN.match(host):
        raise ValueError("Use a domain or IP address.")
    if ".." in host or host.startswith(".") or host.endswith("."):
        raise ValueError("Host format is invalid.")
    return host


def normalize_url(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("Use a URL or domain.")
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urllib.parse.urlparse(raw)
    if not parsed.netloc:
        raise ValueError("URL format is invalid.")
    return raw


def run_command(command: list[str], timeout: int) -> tuple[int, str]:
    spinner = "|/-\\"
    show_spinner = sys.stdout.isatty()
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    start = time.time()
    index = 0
    while proc.poll() is None:
        if time.time() - start > timeout:
            proc.kill()
            return 124, "Command timed out."
        if show_spinner:
            print(f"\r{C.yellow}[RUN]{C.reset} {spinner[index % len(spinner)]} working...", end="")
        index += 1
        time.sleep(0.15)
    if show_spinner:
        print("\r" + " " * 36 + "\r", end="")
    stdout, stderr = proc.communicate()
    output = stdout if stdout else stderr
    return proc.returncode, output.strip()


def print_block(title: str, output: str) -> None:
    print(f"\n{C.bold}{C.cyan}{title}{C.reset}")
    print(f"{C.gray}{'-' * 76}{C.reset}")
    print(output.strip() or "No output.")
    print(f"{C.gray}{'-' * 76}{C.reset}")


def summarize_nmap(output: str) -> str:
    ports = []
    for line in output.splitlines():
        match = OPEN_PORT_PATTERN.match(line.strip())
        if match:
            ports.append(f"[OPEN] {match.group(1)}/{match.group(2)} {match.group(3)}")
    return "\n".join(ports) if ports else "[INFO] No open ports found in this preset."


def run_nmap(target_raw: str, preset_key: str = "1", pause_after: bool = True) -> None:
    try:
        target = validate_host(target_raw)
    except ValueError as exc:
        status("ERR", str(exc), C.red)
        if pause_after:
            pause()
        return

    nmap = find_nmap()
    if not nmap:
        status("ERR", "Nmap was not found. Install it first.", C.red)
        status("TIP", "Termux: pkg install nmap", C.yellow)
        if pause_after:
            pause()
        return

    name, args = NMAP_PRESETS.get(preset_key, NMAP_PRESETS["1"])
    command = [nmap, *args, target]
    status("CMD", " ".join(command), C.yellow)
    code, output = run_command(command, timeout=120)
    if code == 124:
        status("ERR", output, C.red)
    elif code != 0:
        status("WARN", f"Nmap exited with code {code}", C.yellow)

    print_block(f"Nmap: {name}", summarize_nmap(output))
    print_block("Raw output", output)
    if pause_after:
        pause()


def query_dns(domain_raw: str, record_type: str = "A") -> str:
    domain = validate_host(domain_raw)
    record = record_type.upper()
    if shutil.which("dig"):
        command = ["dig", record, domain, "+short"]
    else:
        command = ["nslookup", f"-type={record}", domain]
    _, output = run_command(command, timeout=20)
    return output


def query_mx(domain: str) -> list[str]:
    output = query_dns(domain, "MX")
    records: list[str] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if "mail exchanger =" in line:
            records.append(line.split("mail exchanger =", 1)[1].strip().rstrip("."))
        elif re.match(r"^\d+\s+\S+", line):
            records.append(line.rstrip("."))
    return sorted(set(records))


def run_email(email: str, pause_after: bool = True) -> None:
    address = email.strip().lower()
    if not EMAIL_PATTERN.match(address):
        status("ERR", "Invalid email syntax.", C.red)
        if pause_after:
            pause()
        return

    domain = address.rsplit("@", 1)[1]
    status("DNS", f"Checking MX for {domain}", C.yellow)
    try:
        mx_records = query_mx(domain)
    except (subprocess.TimeoutExpired, ValueError) as exc:
        status("ERR", str(exc), C.red)
        if pause_after:
            pause()
        return

    if not mx_records:
        status("WARN", "No MX records found.", C.yellow)
    else:
        status("OK", "Domain can receive mail.", C.green)
        print_block("MX records", "\n".join(mx_records))
    status("INFO", "This does not prove that the mailbox exists.", C.gray)
    if pause_after:
        pause()


def run_dns(domain_raw: str, record_type: str = "A", pause_after: bool = True) -> None:
    try:
        output = query_dns(domain_raw, record_type)
    except ValueError as exc:
        status("ERR", str(exc), C.red)
        if pause_after:
            pause()
        return
    print_block(f"DNS {record_type.upper()}", output)
    if pause_after:
        pause()


def run_headers(url_raw: str, pause_after: bool = True) -> None:
    try:
        url = normalize_url(url_raw)
    except ValueError as exc:
        status("ERR", str(exc), C.red)
        if pause_after:
            pause()
        return

    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "security-toolkit"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            lines = [f"Status: {response.status} {response.reason}"]
            for key, value in response.headers.items():
                lines.append(f"{key}: {value}")
    except urllib.error.HTTPError as exc:
        lines = [f"Status: {exc.code} {exc.reason}"]
        for key, value in exc.headers.items():
            lines.append(f"{key}: {value}")
    except Exception as exc:
        status("ERR", str(exc), C.red)
        if pause_after:
            pause()
        return

    print_block("HTTP headers", "\n".join(lines))
    if pause_after:
        pause()


def run_ping(target_raw: str, pause_after: bool = True) -> None:
    try:
        target = validate_host(target_raw)
    except ValueError as exc:
        status("ERR", str(exc), C.red)
        if pause_after:
            pause()
        return

    if os.name == "nt":
        command = ["ping", "-n", "4", target]
    else:
        command = ["ping", "-c", "4", target]
    status("CMD", " ".join(command), C.yellow)
    _, output = run_command(command, timeout=20)
    print_block("Ping", output)
    if pause_after:
        pause()


def target_dashboard(box: Box) -> None:
    header(box)
    print(box.row("Target dashboard", C.bold + C.green))
    print(box.line())
    target = ask("Target/domain")
    try:
        target = validate_host(target)
    except ValueError as exc:
        status("ERR", str(exc), C.red)
        pause()
        return

    while True:
        header(box)
        print(box.row(f"Target: {target}", C.bold + C.blue))
        print(box.line())
        menu_row(box, "1", "Nmap quick")
        menu_row(box, "2", "DNS A")
        menu_row(box, "3", "DNS MX")
        menu_row(box, "4", "HTTP headers")
        menu_row(box, "5", "Ping")
        menu_row(box, "0", "Back")
        print(box.line())
        choice = ask("Select")
        if choice == "1":
            run_nmap(target, "1")
        elif choice == "2":
            run_dns(target, "A")
        elif choice == "3":
            run_dns(target, "MX")
        elif choice == "4":
            run_headers(target)
        elif choice == "5":
            run_ping(target)
        elif choice == "0":
            return
        else:
            status("ERR", "Unknown option.", C.red)
            pause()


def nmap_menu(box: Box) -> None:
    header(box)
    print(box.row("Nmap scan presets", C.bold + C.green))
    print(box.line())
    for key, (name, args) in NMAP_PRESETS.items():
        menu_row(box, key, name, " ".join(args))
    menu_row(box, "0", "Back")
    print(box.line())

    choice = ask("Preset", "1")
    if choice == "0":
        return
    if choice not in NMAP_PRESETS:
        status("ERR", "Unknown preset.", C.red)
        pause()
        return
    target = ask("Target")
    run_nmap(target, choice)


def email_menu(box: Box) -> None:
    header(box)
    print(box.row("Email check", C.bold + C.green))
    print(box.line())
    print(box.row("Syntax + MX records only"))
    print(box.row("No mailbox probing"))
    print(box.line())
    run_email(ask("Email"))


def dns_menu(box: Box) -> None:
    header(box)
    print(box.row("DNS lookup", C.bold + C.green))
    print(box.line())
    menu_row(box, "1", "A")
    menu_row(box, "2", "AAAA")
    menu_row(box, "3", "MX")
    menu_row(box, "4", "NS")
    menu_row(box, "5", "TXT")
    menu_row(box, "0", "Back")
    print(box.line())
    choice = ask("Record", "1")
    if choice == "0":
        return
    record_map = {"1": "A", "2": "AAAA", "3": "MX", "4": "NS", "5": "TXT"}
    record = record_map.get(choice)
    if not record:
        status("ERR", "Unknown record type.", C.red)
        pause()
        return
    run_dns(ask("Domain"), record)


def about(box: Box) -> None:
    header(box)
    print(box.row("Rules", C.bold + C.green))
    print(box.line())
    print(box.row("Use only on targets you own or have permission to test."))
    print(box.row("Nmap results depend on network and firewall rules."))
    print(box.row("Email check verifies mail records, not mailbox existence."))
    print(box.line())
    print(box.row("Fast commands", C.bold + C.green))
    print(box.line())
    print(box.row("stk scan example.com"))
    print(box.row("stk dns example.com MX"))
    print(box.row("stk headers example.com"))
    print(box.row("stk ping example.com"))
    print(box.row("stk mail user@example.com"))
    print(box.line())
    pause()


def show_help() -> None:
    print("Security Toolkit")
    print()
    print("Usage:")
    print("  stk")
    print("  stk scan <target> [1|2|3]")
    print("  stk dns <domain> [A|AAAA|MX|NS|TXT]")
    print("  stk headers <domain-or-url>")
    print("  stk ping <target>")
    print("  stk mail <email>")


def run_cli(argv: list[str]) -> int:
    if len(argv) <= 1:
        return interactive()

    command = argv[1].lower()
    if command in {"-h", "--help", "help"}:
        show_help()
        return 0
    if command in {"scan", "nmap"} and len(argv) >= 3:
        run_nmap(argv[2], argv[3] if len(argv) >= 4 else "1", pause_after=False)
        return 0
    if command == "dns" and len(argv) >= 3:
        run_dns(argv[2], argv[3] if len(argv) >= 4 else "A", pause_after=False)
        return 0
    if command in {"headers", "http"} and len(argv) >= 3:
        run_headers(argv[2], pause_after=False)
        return 0
    if command == "ping" and len(argv) >= 3:
        run_ping(argv[2], pause_after=False)
        return 0
    if command in {"mail", "email"} and len(argv) >= 3:
        run_email(argv[2], pause_after=False)
        return 0

    show_help()
    return 1


def interactive() -> int:
    if os.name == "nt":
        os.system("")

    box = Box()
    while True:
        header(box)
        menu_row(box, "1", "Target dashboard", "one target, many checks")
        menu_row(box, "2", "Nmap scan", "ports and services")
        menu_row(box, "3", "Email check", "syntax + MX")
        menu_row(box, "4", "DNS lookup", "A, MX, NS, TXT")
        menu_row(box, "5", "HTTP headers", "status and headers")
        menu_row(box, "6", "Ping", "basic reachability")
        menu_row(box, "7", "About / commands")
        menu_row(box, "0", "Exit")
        print(box.line())

        choice = ask("Select")
        if choice == "1":
            target_dashboard(box)
        elif choice == "2":
            nmap_menu(box)
        elif choice == "3":
            email_menu(box)
        elif choice == "4":
            dns_menu(box)
        elif choice == "5":
            run_headers(ask("Domain or URL"))
        elif choice == "6":
            run_ping(ask("Target"))
        elif choice == "7":
            about(box)
        elif choice == "0":
            status("OK", "Bye.", C.green)
            return 0
        else:
            status("ERR", "Unknown option.", C.red)
            pause()


def main() -> int:
    return run_cli(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
