#!/usr/bin/env sh
set -eu

echo "[*] Security Toolkit installer"

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

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

chmod +x "$PROJECT_DIR/toolkit.py"

if command -v pkg >/dev/null 2>&1; then
  BIN_DIR="${PREFIX:-$HOME/.local}/bin"
else
  BIN_DIR="$HOME/.local/bin"
fi

mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/security-toolkit" <<EOF
#!/usr/bin/env sh
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$PROJECT_DIR/toolkit.py" "\$@"
fi
exec python "$PROJECT_DIR/toolkit.py" "\$@"
EOF

cat > "$BIN_DIR/stk" <<EOF
#!/usr/bin/env sh
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$PROJECT_DIR/toolkit.py" "\$@"
fi
exec python "$PROJECT_DIR/toolkit.py" "\$@"
EOF

chmod +x "$BIN_DIR/security-toolkit" "$BIN_DIR/stk"

echo "[*] Done"
echo "[*] Run: stk"
echo "[*] Or:  security-toolkit"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo "[!] Add this to PATH if the command is not found:"
    echo "    export PATH=\"\$PATH:$BIN_DIR\""
    ;;
esac
