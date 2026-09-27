import storage

# Permitir que el microcontrolador guarde en data.txt Y que la PC pueda sincronizar archivos por USB
try:
    storage.remount("/", readonly=False, disable_concurrent_write_protection=True)
except TypeError:
    storage.remount("/", readonly=False)