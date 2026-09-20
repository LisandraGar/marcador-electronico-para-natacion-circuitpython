#!/usr/bin/env python3
"""
Hook de seguridad Pre-Commit para CircuitPython.
Evita la filtración de contraseñas de WiFi, broker MQTT y claves privadas.
"""

import subprocess
import sys
import re

FORBIDDEN_FILES = [
    re.compile(r"^\.env.*$", re.IGNORECASE),
    re.compile(r"^.*\.pem$", re.IGNORECASE),
    re.compile(r"^.*\.key$", re.IGNORECASE),
    re.compile(r"^.*id_rsa.*$", re.IGNORECASE),
]

FORBIDDEN_DIFF_PATTERNS = [
    (
        "Contraseña WiFi en settings.toml o código",
        re.compile(r'^\+[ \t]*CIRCUITPY_WIFI_PASSWORD[ \t]*=[ \t]*["\']([^\s"\']{2,})["\']', re.MULTILINE),
    ),
    (
        "Contraseña MQTT en settings.toml o código",
        re.compile(r'^\+[ \t]*MQTT_PASSWORD[ \t]*=[ \t]*["\']([^\s"\']{2,})["\']', re.MULTILINE),
    ),
    (
        "Clave privada",
        re.compile(r'^\+[ \t]*-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----', re.MULTILINE),
    ),
]

def main():
    try:
        output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            universal_newlines=True
        )
        staged_files = [f.strip() for f in output.splitlines() if f.strip()]
    except Exception as e:
        print(f"Error comprobando archivos staged: {e}", file=sys.stderr)
        sys.exit(1)

    if not staged_files:
        sys.exit(0)

    errors = []

    # 1. Comprobar nombres de archivo prohibidos
    for f in staged_files:
        for pat in FORBIDDEN_FILES:
            if pat.search(f):
                errors.append(f'📁 Archivo prohibido detectado en staged: "{f}"')

    # 2. Comprobar contenido sensible agregado (+)
    try:
        diff_output = subprocess.check_output(
            ["git", "diff", "--cached", "-U0"],
            universal_newlines=True
        )
    except Exception as e:
        print(f"Error comprobando diff: {e}", file=sys.stderr)
        sys.exit(1)

    for line in diff_output.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue

        for desc, pat in FORBIDDEN_DIFF_PATTERNS:
            if pat.search(line):
                errors.append(f'🔑 {desc}\n   Línea detectada: {line.strip()}')

    if errors:
        print("\n" + "=" * 70, file=sys.stderr)
        print("🛑 [PRE-COMMIT BLOQUEADO]: AUDITORÍA DE SEGURIDAD FALLIDA", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print("Se detectaron secretos o contraseñas reales en los cambios preparados:\n", file=sys.stderr)
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}", file=sys.stderr)
        print("\n💡 Solución:", file=sys.stderr)
        print("  - Deja las contraseñas vacías en settings.toml (las reales van en el hardware local).", file=sys.stderr)
        print("  - Desvincula archivos sensibles con: git reset HEAD <archivo>", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
        sys.exit(1)

    print("🛡️ [Pre-Commit]: Auditoría de seguridad aprobada. Ningún secreto detectado.")
    sys.exit(0)

if __name__ == "__main__":
    main()
