#!/usr/bin/env sh
set -eu

echo "[*] Security Toolkit installer"

if command -v pkg >/dev/null 2>&1; then
  echo "[*] Termux detected"
  pkg update
  pkg install -y python nmap dnsutils git
elif command -v apt >/dev/null 2>&1; then
  echo "[*] Debian/Ubuntu detected"
  sudo apt update
  sudo apt install -y python3 nmap dnsutils git
elif command -v pacman >/dev/null 2>&1; then
  echo "[*] Arch Linux detected"
  sudo pacman -Sy --needed python nmap bind git
else
  echo "[!] Unknown package manager."
  echo "[!] Install Python, Nmap, DNS tools, and Git manually."
fi

echo "[*] Done"
echo "[*] Run: python toolkit.py"
