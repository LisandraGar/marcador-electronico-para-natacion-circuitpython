import supervisor

# Dos slots independientes de cronómetro para nadadores en simultáneo (Carril 1 y Carril 2)
_slot1 = {
    "id": "1",
    "running": False,
    "start_ticks": 0,
    "elapsed_raw": 0,
}

_slot2 = {
    "id": "2",
    "running": False,
    "start_ticks": 0,
    "elapsed_raw": 0,
}

def _calc_raw(slot):
    if slot["running"]:
        now = supervisor.ticks_ms()
        dif = (now - slot["start_ticks"]) & 0x1FFFFFFF
        slot["elapsed_raw"] = dif
        return dif
    return slot["elapsed_raw"]

def _format_single(slot):
    total_ms = _calc_raw(slot)
    ms = (total_ms % 1000) // 10  # Centésimas
    segundos_totales = total_ms // 1000
    ss = segundos_totales % 60
    mm = (segundos_totales // 60) % 60
    hh = segundos_totales // 3600
    return {
        "hh": hh,
        "mm": mm,
        "ss": ss,
        "ms": ms,
        "id": str(slot["id"]),
        "status": "started" if slot["running"] else "stoped"
    }

def start_chrono(id_num, slot_num=None):
    """
    Inicia el cronómetro para un nadador de forma individual.
    Si se especifica slot_num (1 o 2), se asigna a ese carril.
    De lo contrario, busca el slot correspondiente al id o uno disponible.
    """
    id_str = str(id_num)
    now = supervisor.ticks_ms()

    target_slot = None
    if slot_num == 1:
        target_slot = _slot1
    elif slot_num == 2:
        target_slot = _slot2
    elif str(_slot1["id"]) == id_str:
        target_slot = _slot1
    elif str(_slot2["id"]) == id_str:
        target_slot = _slot2
    elif not _slot1["running"]:
        target_slot = _slot1
    elif not _slot2["running"]:
        target_slot = _slot2
    else:
        target_slot = _slot1

    target_slot["id"] = id_str
    target_slot["start_ticks"] = now
    target_slot["running"] = True
    target_slot["elapsed_raw"] = 0
    return _format_single(target_slot)

def start_all_chrono(id1=None, id2=None):
    """
    Inicia simultáneamente ambos cronómetros (Salida Global / Largada).
    Garantiza que ambos nadadores comiencen exactamente en el mismo tick.
    """
    now = supervisor.ticks_ms()
    if id1 is not None:
        _slot1["id"] = str(id1)
    _slot1["start_ticks"] = now
    _slot1["running"] = True
    _slot1["elapsed_raw"] = 0

    if id2 is not None:
        _slot2["id"] = str(id2)
    _slot2["start_ticks"] = now
    _slot2["running"] = True
    _slot2["elapsed_raw"] = 0

def stop_chrono(id_num):
    """
    Detiene el cronómetro del nadador especificado de forma individual.
    """
    id_str = str(id_num)
    now = supervisor.ticks_ms()
    stopped = None

    c1_id = str(_slot1.get("id", ""))
    c2_id = str(_slot2.get("id", ""))

    match_c1 = (c1_id == id_str) or (c1_id.isdigit() and id_str.isdigit() and int(c1_id) == int(id_str))
    match_c2 = (c2_id == id_str) or (c2_id.isdigit() and id_str.isdigit() and int(c2_id) == int(id_str))

    if match_c1:
        if _slot1["running"]:
            _slot1["running"] = False
            _slot1["elapsed_raw"] = (now - _slot1["start_ticks"]) & 0x1FFFFFFF
        stopped = _slot1
    elif match_c2:
        if _slot2["running"]:
            _slot2["running"] = False
            _slot2["elapsed_raw"] = (now - _slot2["start_ticks"]) & 0x1FFFFFFF
        stopped = _slot2
    else:
        # Si no coincide exactamente con el ID, detener el primero que esté corriendo
        if _slot1["running"]:
            _slot1["running"] = False
            _slot1["elapsed_raw"] = (now - _slot1["start_ticks"]) & 0x1FFFFFFF
            stopped = _slot1
        elif _slot2["running"]:
            _slot2["running"] = False
            _slot2["elapsed_raw"] = (now - _slot2["start_ticks"]) & 0x1FFFFFFF
            stopped = _slot2
        else:
            stopped = _slot1

    return _format_single(stopped)

def stop_all_chrono():
    """
    Detiene ambos cronómetros simultáneamente (Parada Global).
    Ambos slots quedan congelados en el mismo tick instantáneo.
    """
    now = supervisor.ticks_ms()
    if _slot1["running"]:
        _slot1["running"] = False
        _slot1["elapsed_raw"] = (now - _slot1["start_ticks"]) & 0x1FFFFFFF
    if _slot2["running"]:
        _slot2["running"] = False
        _slot2["elapsed_raw"] = (now - _slot2["start_ticks"]) & 0x1FFFFFFF
    return _format_single(_slot1), _format_single(_slot2)

def clr_chrono(slot_num=None):
    """
    Limpia y resetea cronómetros a cero.
    """
    if slot_num in (None, 1):
        _slot1["running"] = False
        _slot1["start_ticks"] = 0
        _slot1["elapsed_raw"] = 0
    if slot_num in (None, 2):
        _slot2["running"] = False
        _slot2["start_ticks"] = 0
        _slot2["elapsed_raw"] = 0

def get_chrono_raw(slot_num=1):
    slot = _slot2 if slot_num == 2 else _slot1
    return _calc_raw(slot)

def get_chrono_formatted():
    """
    Retorna el estado de los cronómetros.
    Incluye c1 (carril 1) y c2 (carril 2) para soporte dual,
    manteniendo además campos raíz de nivel superior para total compatibilidad.
    """
    f1 = _format_single(_slot1)
    f2 = _format_single(_slot2)

    # El cronómetro principal para retrocompatibilidad es el que esté activo, o c1
    primary = f1 if (_slot1["running"] or not _slot2["running"]) else f2

    return {
        "hh": primary["hh"],
        "mm": primary["mm"],
        "ss": primary["ss"],
        "ms": primary["ms"],
        "id": primary["id"],
        "status": "started" if (_slot1["running"] or _slot2["running"]) else "stoped",
        "c1": f1,
        "c2": f2,
        "active_count": (1 if _slot1["running"] else 0) + (1 if _slot2["running"] else 0),
        "both_running": _slot1["running"] and _slot2["running"]
    }

def get_chrono_status(slot_num=None):
    if slot_num == 1:
        return 'started' if _slot1["running"] else 'stoped'
    if slot_num == 2:
        return 'started' if _slot2["running"] else 'stoped'
    if _slot1["running"] or _slot2["running"]:
        return 'started'
    return 'stoped'
