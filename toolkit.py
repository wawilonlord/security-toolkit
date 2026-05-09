from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HOST_PATTERN = re.compile(r"^[a-zA-Z0-9.-]{1,253}$")

NMAP_PRESETS = {
    "1": ("Quick ports", ["-T3", "-F"]),
    "2": ("Top 100 ports", ["-T3", "--top-ports", "100"]),
    "3": ("Light service scan", ["-T3", "-sV", "--version-light", "--top-ports", "50"]),
}


class C:
    reset = "\033[0m"
    bold = "\033[1m"
    dim = "\033[2m"
    cyan = "\033[36m"
    green = "\033[32m"
    yellow = "\033[33m"
    red = "\033[31m"
    blue = "\033[34m"
    gray = "\033[90m"


@dataclass
class Box:
    width: int = 72

    def line(self, char: str = "-") -> str:
        return f"{C.gray}+{char * (self.width - 2)}+{C.reset}"

    def row(self, text: str = "", color: str = "") -> str:
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
    input(f"\n{C.gray}Press Enter to continue...{C.reset}")


def header(box: Box) -> None:
    clear()
    box.title("SECURITY TOOLKIT")
    print(box.row("Nmap scans + email domain checks"))
    print(box.row("PC / Termux / Linux"))
    print(box.line())


def find_nmap() -> str | None:
    nmap = shutil.which("nmap")
    if nmap:
        return nmap
    windows_path = r"C:\Program Files (x86)\Nmap\nmap.exe"
    if os.path.exists(windows_path):
        return windows_path
    return None


def validate_host(value: str) -> str:
    host = value.strip()
    if not host or len(host) > 253 or not HOST_PATTERN.match(host):
        raise ValueError("Use a domain or IP address.")
    if ".." in host or host.startswith(".") or host.endswith("."):
        raise ValueError("Host format is invalid.")
    return host


def print_output(title: str, output: str) -> None:
    print(f"\n{C.bold}{C.cyan}{title}{C.reset}")
    print(f"{C.gray}{'-' * 72}{C.reset}")
    print(output.strip() or "No output.")
    print(f"{C.gray}{'-' * 72}{C.reset}")


def nmap_menu(box: Box) -> None:
    header(box)
    print(box.row("Nmap scan presets", C.bold + C.green))
    print(box.line())
    for key, (name, args) in NMAP_PRESETS.items():
        print(box.row(f"{key}. {name}  {' '.join(args)}"))
    print(box.row("0. Back"))
    print(box.line())

    choice = input(f"{C.cyan}Preset > {C.reset}").strip()
    if choice == "0":
        return
    if choice not in NMAP_PRESETS:
        print(f"{C.red}Unknown preset.{C.reset}")
        pause()
        return

    target_raw = input(f"{C.cyan}Target > {C.reset}")
    try:
        target = validate_host(target_raw)
    except ValueError as exc:
        print(f"{C.red}{exc}{C.reset}")
        pause()
        return

    nmap = find_nmap()
    if not nmap:
        print(f"{C.red}Nmap was not found. Install it first.{C.reset}")
        print(f"{C.gray}Termux: pkg install nmap{C.reset}")
        pause()
        return

    name, args = NMAP_PRESETS[choice]
    command = [nmap, *args, target]
    print(f"\n{C.yellow}Running:{C.reset} {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"{C.red}Scan timed out.{C.reset}")
        pause()
        return

    output = result.stdout if result.stdout else result.stderr
    print_output(name, output)
    pause()


def query_mx(domain: str) -> list[str]:
    command = ["nslookup", "-type=mx", domain]
    if shutil.which("dig"):
        command = ["dig", "mx", domain, "+short"]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    output = result.stdout + "\n" + result.stderr
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


def email_menu(box: Box) -> None:
    header(box)
    print(box.row("Email check", C.bold + C.green))
    print(box.line())
    print(box.row("Checks syntax and MX records only."))
    print(box.row("It does not prove that a mailbox exists."))
    print(box.line())

    email = input(f"{C.cyan}Email > {C.reset}").strip().lower()
    if not EMAIL_PATTERN.match(email):
        print(f"{C.red}Invalid email syntax.{C.reset}")
        pause()
        return

    domain = email.rsplit("@", 1)[1]
    print(f"\n{C.yellow}Checking domain:{C.reset} {domain}")
    try:
        mx_records = query_mx(domain)
    except subprocess.TimeoutExpired:
        print(f"{C.red}DNS query timed out.{C.reset}")
        pause()
        return

    if not mx_records:
        print(f"{C.red}No MX records found.{C.reset}")
        pause()
        return

    print(f"{C.green}Domain can receive mail.{C.reset}")
    print_output("MX records", "\n".join(mx_records))
    pause()


def about(box: Box) -> None:
    header(box)
    print(box.row("About", C.bold + C.green))
    print(box.line())
    print(box.row("1. Use only on targets you own or have permission to test."))
    print(box.row("2. Nmap results depend on network/firewall rules."))
    print(box.row("3. Email check verifies domain mail records, not mailbox existence."))
    print(box.line())
    pause()


def main() -> int:
    if os.name == "nt":
        os.system("")

    box = Box()
    while True:
        header(box)
        print(box.row("1. Nmap scan", C.green))
        print(box.row("2. Email check", C.green))
        print(box.row("3. About / rules", C.green))
        print(box.row("0. Exit", C.yellow))
        print(box.line())

        choice = input(f"{C.cyan}Select > {C.reset}").strip()
        if choice == "1":
            nmap_menu(box)
        elif choice == "2":
            email_menu(box)
        elif choice == "3":
            about(box)
        elif choice == "0":
            print(f"{C.green}Bye.{C.reset}")
            return 0
        else:
            print(f"{C.red}Unknown option.{C.reset}")
            pause()


if __name__ == "__main__":
    raise SystemExit(main())
