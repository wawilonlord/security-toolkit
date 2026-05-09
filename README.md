# Security Toolkit

Simple terminal tool for ethical hacking labs.

## Features

- Nmap scan presets
- Email syntax check
- Email domain MX record check
- Works on PC and Termux

## Quick Start

```bash
git clone https://github.com/wawilonlord/security-toolkit.git
cd security-toolkit
sh install.sh
stk
```

## Install

Termux:

```bash
pkg update
pkg install python nmap dnsutils git
git clone https://github.com/wawilonlord/security-toolkit.git
cd security-toolkit
sh install.sh
stk
```

Linux:

```bash
git clone https://github.com/wawilonlord/security-toolkit.git
cd security-toolkit
sh install.sh
stk
```

## Windows

Install:

- Python
- Nmap

Then run:

```powershell
python toolkit.py
```

## Commands

```bash
stk
security-toolkit
python toolkit.py
```

## Rule

Use only on systems you own or have permission to test.

Email checks do not prove a mailbox exists. They only check format and mail server records.
