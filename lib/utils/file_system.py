import storage
import os


# Guarda o actualiza un par clave:valor en un archivo.
def guarda_valor(nombre_archivo, clave, valor):
    datos = {}
    
    # Intentamos leer lo que ya existe
    try:
        with open(nombre_archivo, "r") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if ":" in linea:
                    k, v = linea.split(":", 1)
                    datos[k.strip()] = v.strip()
    except OSError as e:
        if e.args[0] != 2:
            print(f"Error de sistema de archivos: {e}")
        # Si no existe, no pasa nada, 'datos' se queda vacío {}

    # Añadimos el dato
    datos[str(clave)] = str(valor)

    # Escribimos (esto crea el archivo si no existe)
    try:
        with open(nombre_archivo, "w") as archivo:
            for k, v in datos.items():
                archivo.write(f"{k}:{v}\n")
        return True
    except OSError as e:
        print(f"No se pudo escribir en {nombre_archivo}: {e}")
        return False
    
def lee_valor(nombre_archivo, clave):
    try:
        # Reconstruir el diccionario igual que en guarda_valor
        datos = {}
        try:
            with open(nombre_archivo, 'r') as archivo:
                for linea in archivo:
                    if ':' in linea:
                        k, v = linea.strip().split(':', 1)
                        datos[k] = v
        except FileNotFoundError:
            return None
        
        # Devolver el valor si existe
        clave_str = str(clave)
        if clave_str in datos:
            return datos[clave_str]
        else:
            print(f"Clave '{clave}' no encontrada")
            return None
            
    except Exception as e:
        print(f"Error al leer {nombre_archivo}")
        return None
    