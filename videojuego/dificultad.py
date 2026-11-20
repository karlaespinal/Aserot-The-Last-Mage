"""
dificultad.py - Dificultad progresiva de "Aserot: The Last Mage".

Cada nivel (indice 0 = nivel 1 ... 7 = nivel 8) recibe un conjunto de multiplicadores que se
aplican sobre los valores base de los enemigos y del mago. Todo se ajusta en AJUSTES.

    vel        velocidad de patrulla y persecución de los enemigos
    cd         tiempo entre ataques (menor = atacan más seguido)
    proy       velocidad de los proyectiles enemigos
    rango      distancia a la que los enemigos detectan al mago
    dano_proy  daño de los proyectiles enemigos (en corazones)
    hp_extra   vida extra de todos los enemigos
    regen      regeneración de magia del mago por segundo (baja un poco con el nivel)
    extra      proporción de enemigos añadidos respecto a los que ya trae el nivel
    estrellas  valor 1-5 que se muestra en el menú

Este módulo no depende de pygame, así que se puede probar solo:  python dificultad.py
"""
import math
import random

ULTIMO = 7                      # índice del último nivel (8 niveles)

AJUSTES = dict(
    vel=(1.00, 1.40),           # (nivel 1, nivel 8): se interpola linealmente entre ambos
    cd=(1.00, 0.62),
    proy=(1.00, 1.30),
    rango=(1.00, 1.25),
    regen=(5.0, 3.4),
    extra=(0.0, 0.60),
)
NIVEL_DANO_2 = 5                # desde el nivel 6 (indice 5) los proyectiles enemigos quitan 2 corazones
NIVEL_HP_EXTRA = 5              # desde el nivel 6 los enemigos aguantan 1 golpe más


def _lerp(par, t):
    a, b = par
    return a + (b - a) * t


def parametros(indice):
    """Multiplicadores de dificultad para el nivel 'indice' (0-7)."""
    t = max(0, min(ULTIMO, indice)) / ULTIMO
    return dict(
        vel=_lerp(AJUSTES['vel'], t),
        cd=_lerp(AJUSTES['cd'], t),
        proy=_lerp(AJUSTES['proy'], t),
        rango=_lerp(AJUSTES['rango'], t),
        regen=_lerp(AJUSTES['regen'], t),
        extra=_lerp(AJUSTES['extra'], t),
        dano_proy=2 if indice >= NIVEL_DANO_2 else 1,
        hp_extra=1 if indice >= NIVEL_HP_EXTRA else 0,
        estrellas=estrellas(indice),
    )


def estrellas(indice):
    """1 a 5 estrellas para mostrar en el menú."""
    return 1 + round(max(0, min(ULTIMO, indice)) * 4 / ULTIMO)


def _tipos(indice):
    """Tipos de enemigo que se pueden añadir en cada tramo del juego."""
    if indice < 2:
        return ['F', 'G']
    if indice < 4:
        return ['F', 'L', 'G', 'H']
    if indice < 6:
        return ['F', 'L', 'H', 'H', 'I']
    return ['L', 'H', 'I', 'I', 'F']


def enemigos_extra(nivel, indice):
    """Enemigos adicionales (tipo, col, fila) colocados sobre el suelo del nivel.

    Es determinista (misma semilla por nivel): el nivel siempre es igual en cada partida.
    Respeta zonas seguras: cerca del inicio, de la salida y de los puntos de control, y no los
    pone sobre pinchos, techos bajos ni demasiado cerca de otros enemigos.
    """
    n_extra = math.ceil(len(nivel.enemigos) * _lerp(AJUSTES['extra'], max(0, indice) / ULTIMO) - 1e-9)
    if n_extra <= 0:
        return []
    rnd = random.Random(7000 + indice)
    grid = nivel.grid
    filas = len(grid)

    def libre(c, f):
        # f = fila donde estará de pie; necesita 3 bloques de aire por encima y sin pinchos delante
        for ff in range(max(0, f - 2), f + 1):
            if grid[ff][c] != ' ':
                return False
        return True

    candidatos = []
    for f in range(1, filas):                         # f = fila del suelo
        c = 0
        while c < nivel.cols:
            if grid[f][c] == '#' and grid[f - 1][c] == ' ':
                c0 = c
                while c < nivel.cols and grid[f][c] == '#' and grid[f - 1][c] == ' ':
                    c += 1
                c1 = c - 1
                if c1 - c0 + 1 >= 5:                  # plataforma lo bastante ancha para patrullar
                    for cc in range(c0 + 2, c1 - 1):
                        if libre(cc, f - 1):
                            candidatos.append((cc, f - 1))
            else:
                c += 1

    ic, _ = nivel.inicio_pos
    sc, _ = nivel.salida_pos
    ocupados = [c for _, c, _ in nivel.enemigos]
    prohibidos = [ic, sc] + [c for c, _ in nivel.checkpoints]
    candidatos = [(c, f) for c, f in candidatos
                  if abs(c - ic) > 14 and abs(c - sc) > 8
                  and all(abs(c - p) > 3 for p in prohibidos)
                  and not any(grid[ff][cc] == '^' for ff in range(len(grid)) for cc in (c - 1, c, c + 1))]
    rnd.shuffle(candidatos)

    tipos = _tipos(indice)
    resultado = []
    for c, f in candidatos:
        if len(resultado) >= n_extra:
            break
        if all(abs(c - o) >= 4 for o in ocupados):
            t = rnd.choice(tipos)
            resultado.append((t, c, f))
            ocupados.append(c)
    return resultado


if __name__ == "__main__":
    import niveles
    print("nivel  vel   cd    proy  rango regen dano hp+ estrellas  extra(real)")
    for i, fn in enumerate(niveles.NIVELES):
        p = parametros(i)
        nv = fn()
        ex = enemigos_extra(nv, i)
        print(f"{i + 1:>5}  {p['vel']:.2f}  {p['cd']:.2f}  {p['proy']:.2f}  {p['rango']:.2f}  "
              f"{p['regen']:.1f}   {p['dano_proy']}    {p['hp_extra']}    {p['estrellas']}"
              f"         {len(ex)} (+{len(nv.enemigos)} base)")
