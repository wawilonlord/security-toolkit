# Security Toolkit

Simple terminal tool for ethical hacking labs.

## Features

- Nmap scan presets
- Email syntax check
- Email domain MX record check
- Works on PC and Termux

## Run

```bash
python toolkit.py
```

## Install

Termux:

```bash
pkg update
pkg install python nmap dnsutils git
python toolkit.py
```

or:

```bash
sh install.sh
python toolkit.py
```

Linux:

```bash
sh install.sh
python3 toolkit.py
```

## Windows

Install:

- Python
- Nmap

Then run:

```powershell
python toolkit.py
```

## Clone

```bash
git clone https://github.com/wawilonlord/security-toolkit.git
cd security-toolkit
python toolkit.py
```

## Rule

Use only on systems you own or have permission to test.

Email checks do not prove a mailbox exists. They only check format and mail server records.
