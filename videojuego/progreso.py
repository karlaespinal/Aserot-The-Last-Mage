"""
progreso.py - Progreso guardado de "Aserot: The Last Mage".

Guarda cuántos mundos tiene desbloqueados el jugador:
  - escritorio: archivo progreso.json junto a main.py
  - navegador (Pygbag): localStorage del navegador
Todo está envuelto en try/except: si no se puede leer o escribir, el juego sigue funcionando
(simplemente empezará con solo el mundo 1 desbloqueado).
"""
import json
import os
import sys

WEB = sys.platform == "emscripten"
CLAVE = "aserot_progreso"


def _archivo(base):
    return os.path.join(base, "progreso.json")


def cargar(base, total):
    """Devuelve cuántos mundos están desbloqueados (1 .. total)."""
    n = 1
    try:
        if WEB:
            from platform import window
            valor = window.localStorage.getItem(CLAVE)
            if valor:
                n = int(json.loads(str(valor)).get("desbloqueado", 1))
        elif os.path.exists(_archivo(base)):
            with open(_archivo(base), encoding="utf-8") as f:
                n = int(json.load(f).get("desbloqueado", 1))
    except Exception:
        n = 1
    return max(1, min(total, n))


def guardar(base, desbloqueado):
    try:
        datos = json.dumps({"desbloqueado": int(desbloqueado)})
        if WEB:
            from platform import window
            window.localStorage.setItem(CLAVE, datos)
        else:
            with open(_archivo(base), "w", encoding="utf-8") as f:
                f.write(datos)
    except Exception:
        pass
