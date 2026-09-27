#!/usr/bin/env python3
"""
Herramienta de sincronización y limpieza para el Firmware CircuitPython.
Evita el error 'Exit code 1' en Thonny o al copiar archivos a la unidad CIRCUITPY:
1. Elimina carpetas __pycache__ y archivos .pyc no compatibles con microcontroladores.
2. Filtra archivos pesados innecesarios (fuentes no usadas de >1MB, PDFs, .Trashes).
3. Detecta automáticamente la unidad CIRCUITPY en Windows y copia de forma segura.
4. Funciona en cualquier entorno de Python (incluso sin librería externa 'shutil').
5. Detecta bloqueos de 'Solo Lectura' (read-only) y guía para desbloquear en Modo Seguro.
"""

import os
import sys
import stat
import string
from pathlib import Path

# Soporte opcional de shutil si existe en el entorno, con fallback 100% nativo
try:
    import shutil
except ImportError:
    shutil = None

# Carpetas y archivos estrictamente necesarios para el marcador
ESSENTIAL_ROOT_FILES = ["code.py", "boot.py", "data.txt", "settings.toml"]
ESSENTIAL_FONTS = ["12-Fixed-SemiCond.bdf"]

def safe_rmtree(path):
    """Elimina un directorio y su contenido usando solo funciones nativas de os."""
    if shutil is not None:
        try:
            shutil.rmtree(path)
            return
        except Exception:
            pass

    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            full_f = os.path.join(root, f)
            try:
                os.chmod(full_f, stat.S_IWRITE)
                os.remove(full_f)
            except Exception:
                pass
        for d in dirs:
            full_d = os.path.join(root, d)
            try:
                os.rmdir(full_d)
            except Exception:
                pass
    try:
        os.rmdir(path)
    except Exception:
        pass

def safe_copy(src, dst):
    """Copia un archivo usando I/O nativo con desbloqueo de atributos de solo lectura."""
    if os.path.exists(dst):
        try:
            os.chmod(dst, stat.S_IWRITE)
        except Exception:
            pass

    if shutil is not None and hasattr(shutil, "copy2"):
        try:
            shutil.copy2(src, dst)
            return
        except Exception:
            pass

    with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
            while True:
                buf = fsrc.read(65536)
                if not buf:
                    break
                fdst.write(buf)

def clean_pycache(base_dir):
    """Elimina directorios __pycache__ recursivamente en el proyecto."""
    count = 0
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d == "__pycache__":
                full_path = os.path.join(root, d)
                try:
                    safe_rmtree(full_path)
                    count += 1
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar {full_path}: {e}")
    print(f"🧹 Limpieza completada: {count} carpetas __pycache__ eliminadas.")

def check_drive_writable(dest_drive):
    """Verifica si la unidad CIRCUITPY permite escritura o si está bloqueada en solo lectura."""
    test_file = os.path.join(dest_drive, ".test_perm_check.tmp")
    try:
        with open(test_file, "wb") as f:
            f.write(b"ok")
        if os.path.exists(test_file):
            try:
                os.chmod(test_file, stat.S_IWRITE)
                os.remove(test_file)
            except Exception:
                pass
        return True
    except (PermissionError, OSError):
        return False

def print_readonly_help(drive_letter):
    """Muestra instrucciones claras para desbloquear la unidad en Modo Seguro."""
    print("\n" + "=" * 75)
    print(f"🛑 [ACCESO DENEGADO]: LA UNIDAD {drive_letter} ESTÁ BLOQUEADA EN 'SOLO LECTURA'")
    print("=" * 75)
    print("¿Por qué ocurre esto?")
    print("  En CircuitPython, cuando 'boot.py' habilita la escritura interna para")
    print("  guardar datos (como en data.txt), el microcontrolador bloquea la escritura")
    print("  a la computadora por el puerto USB para prevenir corrupción del disco.")
    print("\n💡 CÓMO DESBLOQUEARLA EN 5 SEGUNDOS (MODO SEGURO / SAFE MODE):")
    print("  1. En la placa Adafruit MatrixPortal S3, pulsa el botón RESET 2 VECES SEGUIDAS")
    print("     rápidamente (o justo mientras el LED de estado parpadea).")
    print("  2. La placa entrará en MODO SEGURO (el LED de estado parpadeará en color amarillo continuo).")
    print("     En Modo Seguro, CircuitPython NO ejecuta boot.py y desbloquea el USB a Lectura/Escritura.")
    print(f"  3. Vuelve a ejecutar este script:")
    print("         python sync_to_device.py")
    print("  4. Una vez copiados los archivos, pulsa el botón RESET UNA VEZ para arrancar normalmente.")
    print("=" * 75 + "\n")

def find_circuitpy_drive():
    """Detecta automáticamente la letra de unidad de CIRCUITPY en Windows."""
    if sys.platform != "win32":
        return None

    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        bitmask = kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                vol_name_buf = ctypes.create_unicode_buffer(1024)
                res = kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(drive_path),
                    vol_name_buf,
                    ctypes.sizeof(vol_name_buf),
                    None, None, None, None, 0
                )
                if res and vol_name_buf.value.upper() == "CIRCUITPY":
                    return drive_path
            bitmask >>= 1
    except Exception:
        pass
    return None

def sync_to_drive(dest_drive, src_dir):
    """Copia los archivos limpios y necesarios hacia la unidad del microcontrolador."""
    dest_path = Path(dest_drive)
    if not dest_path.exists():
        print(f"❌ La ruta de destino no existe: {dest_drive}")
        return False

    # Verificar permisos de escritura antes de proceder
    if not check_drive_writable(dest_drive):
        print_readonly_help(dest_drive)
        return False

    print(f"\n🚀 Sincronizando firmware hacia: {dest_path.resolve()} ...")

    try:
        # 1. Copiar archivos raíz
        for f in ESSENTIAL_ROOT_FILES:
            src_f = os.path.join(src_dir, f)
            dst_f = os.path.join(dest_drive, f)
            if os.path.exists(src_f):
                # No sobreescribir settings.toml si el micro ya tiene credenciales reales
                if f == "settings.toml" and os.path.exists(dst_f):
                    print(f"  ℹ️ Omitiendo '{f}' en destino (ya existe y conserva credenciales locales)")
                    continue
                safe_copy(src_f, dst_f)
                print(f"  ✅ Copiado: {f}")

        # 2. Copiar fuentes seleccionadas (evitando fuentes gigantescas > 1MB no usadas)
        dst_fonts = os.path.join(dest_drive, "fonts")
        os.makedirs(dst_fonts, exist_ok=True)
        for font_file in ESSENTIAL_FONTS:
            src_font = os.path.join(src_dir, "fonts", font_file)
            dst_font = os.path.join(dst_fonts, font_file)
            if os.path.exists(src_font):
                safe_copy(src_font, dst_font)
                print(f"  ✅ Fuente copiada: fonts/{font_file}")

        # 3. Copiar lib/ recursivamente (sin __pycache__)
        src_lib = os.path.join(src_dir, "lib")
        dst_lib = os.path.join(dest_drive, "lib")
        os.makedirs(dst_lib, exist_ok=True)

        copied_files = 0
        for root, dirs, files in os.walk(src_lib):
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            
            rel_path = os.path.relpath(root, src_lib)
            target_dir = os.path.join(dst_lib, rel_path) if rel_path != "." else dst_lib
            os.makedirs(target_dir, exist_ok=True)

            for file in files:
                if file.endswith((".pyc", ".swp")):
                    continue
                s_file = os.path.join(root, file)
                d_file = os.path.join(target_dir, file)
                safe_copy(s_file, d_file)
                copied_files += 1

        print(f"  ✅ Carpeta 'lib' sincronizada ({copied_files} archivos copiados sin cache).")
        print("\n🎉 ¡Sincronización finalizada exitosamente!")
        print("👉 Puedes pulsar RESET en la placa para reiniciar y aplicar los cambios.")
        return True

    except PermissionError:
        print_readonly_help(dest_drive)
        return False

def main():
    # Localizar directorio base del firmware (incluso si se llama desde la carpeta scripts/)
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_script_dir) == "scripts":
        base_dir = os.path.dirname(current_script_dir)
    else:
        base_dir = current_script_dir

    clean_pycache(base_dir)

    target_drive = sys.argv[1] if len(sys.argv) > 1 else find_circuitpy_drive()

    if target_drive:
        success = sync_to_drive(target_drive, base_dir)
        sys.exit(0 if success else 1)
    else:
        print("\n💡 Unidad 'CIRCUITPY' no detectada automáticamente.")
        print("  - Si tu placa está conectada como unidad USB, ejecuta:")
        print("      python scripts/sync_to_device.py <LETRA_DE_UNIDAD> (ejemplo: E:\\)")
        print("  - Los archivos en 'lib/' y el proyecto ya quedaron limpios de cache.")
        sys.exit(0)

if __name__ == "__main__":
    main()
