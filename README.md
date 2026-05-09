# Security Tools Dashboard

Local ethical hacking dashboard with:

- Nmap scan presets
- Email syntax and MX record check
- PC and Termux-friendly Python server

## Run

```bash
python server.py
```

Open:

```text
http://127.0.0.1:8787
```

## Termux

```bash
pkg update
pkg install python nmap dnsutils git
python server.py
```

## Rule

Use only on systems you own or have permission to test.

Email checks do not prove a mailbox exists. They only check format and mail server records.
