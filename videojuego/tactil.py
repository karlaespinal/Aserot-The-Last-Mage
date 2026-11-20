"""
tactil.py - Controles táctiles para móviles y tablets (Android / iOS) de "Aserot: The Last Mage".

Los botones en pantalla se traducen a las mismas teclas virtuales que usa el teclado, así que el
resto del juego no necesita saber si se juega con teclado o con los dedos:

    izquierda / derecha  -> K_LEFT / K_RIGHT   (se mantienen; puedes deslizar el dedo de uno a otro)
    correr               -> K_LSHIFT            (automático: al mantener una dirección SEG_CORRER segundos)
    saltar               -> K_SPACE             (mantener = salto más alto)
    magia                -> K_j                 (mantener = disparo automático)
    magias especiales    -> K_1, K_2, K_3
    pausa                -> K_p

Admite varios dedos a la vez (por ejemplo: mover + saltar + disparar).
"""
import math

import pygame


class Boton:
    def __init__(self, nombre, cx, cy, r, tecla, tipo):
        self.nombre = nombre
        self.cx, self.cy, self.r = cx, cy, r
        self.tecla = tecla
        self.tipo = tipo                 # 'mover': activo mientras haya un dedo encima | 'accion': pulsación

    def contiene(self, pos, holgura=1.0):
        return math.hypot(pos[0] - self.cx, pos[1] - self.cy) <= self.r * holgura


class Tactil:
    SEG_CORRER = 2.0                     # segundos manteniendo una dirección para empezar a correr solo

    def __init__(self, ancho, alto, fuente):
        self.ancho, self.alto = ancho, alto
        self.fuente = fuente
        self.activo = False              # True cuando se usan los dedos: entonces se dibujan los botones
        self.visto_dedo = False          # ya llegó algún evento táctil (para ignorar el ratón "emulado")
        self.dedos = {}                  # finger_id -> (x, y) en coordenadas del juego
        self.asig = {}                   # finger_id -> Boton de acción que pulsó ese dedo
        self.iconos = None               # iconos de las magias especiales (los pone Juego)
        self.t_dir = 0.0                 # tiempo seguido manteniendo la misma dirección
        self._dir = 0
        self._construir()
        self._cache = {}

    def _construir(self):
        a = self.ancho
        self.botones = [
            Boton('izq', 110, 600, 68, pygame.K_LEFT, 'mover'),
            Boton('der', 285, 600, 68, pygame.K_RIGHT, 'mover'),
            Boton('saltar', a - 120, 590, 76, pygame.K_SPACE, 'accion'),
            Boton('magia', a - 290, 622, 62, pygame.K_j, 'accion'),
            Boton('esp1', a - 350, 455, 42, pygame.K_1, 'accion'),
            Boton('esp2', a - 250, 440, 42, pygame.K_2, 'accion'),
            Boton('esp3', a - 150, 440, 42, pygame.K_3, 'accion'),
            Boton('pausa', a - 54, 130, 28, pygame.K_p, 'accion'),
        ]

    def redimensionar(self, ancho, alto):
        """La pantalla cambió de proporción: recoloca los botones (los dedos apoyados se sueltan)."""
        self.ancho, self.alto = ancho, alto
        self._construir()
        self.soltar_todo()

    # ------------------------------------------------------------------
    def _pos(self, e):
        return (e.x * self.ancho, e.y * self.alto)

    def soltar_todo(self):
        self.dedos.clear()
        self.asig.clear()
        self.t_dir = 0.0
        self._dir = 0

    def actualizar(self, dt):
        """Llamar una vez por cuadro mientras se juega: cuenta cuánto llevas pulsando la misma dirección."""
        d = (1 if self.mantiene(pygame.K_RIGHT) else 0) - (1 if self.mantiene(pygame.K_LEFT) else 0)
        if d != 0 and d == self._dir:
            self.t_dir += dt
        else:
            self.t_dir = 0.0
        self._dir = d

    @property
    def corriendo(self):
        return self._dir != 0 and self.t_dir >= self.SEG_CORRER

    def mantiene(self, tecla):
        """¿Hay un dedo manteniendo esta tecla virtual?"""
        if tecla == pygame.K_LSHIFT:             # no hay botón de correr: se activa solo tras SEG_CORRER s
            return self.corriendo
        if not self.dedos:
            return False
        for b in self.botones:
            if b.tecla != tecla:
                continue
            if b.tipo == 'mover':
                return any(b.contiene(p, 1.25) for p in self.dedos.values())
            return b in self.asig.values()
        return False

    def evento(self, e, jugando):
        """Procesa un evento FINGER*. Devuelve (eventos_de_teclado, toque).
        'toque' es la posición del dedo cuando se toca la pantalla fuera de la partida (menús)."""
        t = e.type
        if t == pygame.FINGERDOWN:
            self.activo = True
            self.visto_dedo = True
            pos = self._pos(e)
            self.dedos[e.finger_id] = pos
            if not jugando:
                return [], pos
            for b in self.botones:
                if b.tipo == 'accion' and b.contiene(pos, 1.15):
                    self.asig[e.finger_id] = b
                    return [pygame.event.Event(pygame.KEYDOWN, key=b.tecla)], None
        elif t == pygame.FINGERMOTION:
            if e.finger_id in self.dedos:
                self.dedos[e.finger_id] = self._pos(e)
        elif t == pygame.FINGERUP:
            self.dedos.pop(e.finger_id, None)
            b = self.asig.pop(e.finger_id, None)
            if b is not None:
                return [pygame.event.Event(pygame.KEYUP, key=b.tecla)], None
        return [], None

    # ------------------------------------------------------------------
    def _disco(self, r, activo):
        clave = (r, activo)
        if clave not in self._cache:
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            relleno = (255, 255, 255, 95) if activo else (20, 20, 40, 110)
            pygame.draw.circle(s, relleno, (r + 2, r + 2), r)
            pygame.draw.circle(s, (230, 235, 255, 200 if activo else 140), (r + 2, r + 2), r, 3)
            self._cache[clave] = s
        return self._cache[clave]

    def dibujar(self, pantalla, jugador=None, especiales=None):
        """Dibuja los botones. 'jugador' y 'especiales' sirven para mostrar enfriamientos."""
        for b in self.botones:
            activo = self.mantiene(b.tecla)
            d = self._disco(b.r, activo)
            pantalla.blit(d, (b.cx - b.r - 2, b.cy - b.r - 2))
            self._glifo(pantalla, b, jugador, especiales)
            if b.nombre in ('izq', 'der') and activo:
                self._indicador_correr(pantalla, b)

    def _indicador_correr(self, p, b):
        """Anillo que se llena mientras mantienes la dirección; al completarse, el mago corre."""
        prog = min(1.0, self.t_dir / self.SEG_CORRER)
        rect = pygame.Rect(b.cx - b.r - 8, b.cy - b.r - 8, (b.r + 8) * 2, (b.r + 8) * 2)
        if prog >= 1.0:
            pygame.draw.circle(p, (255, 190, 80), (b.cx, b.cy), b.r + 8, 5)
            sgn = 1 if b.nombre == 'der' else -1
            for k in (-1, 1):                    # « » encima del botón: indica que está corriendo
                x = b.cx + k * 14
                pygame.draw.polygon(p, (255, 190, 80), [(x + sgn * 10, b.cy - b.r - 30),
                                                        (x - sgn * 4, b.cy - b.r - 42),
                                                        (x - sgn * 4, b.cy - b.r - 18)])
        elif prog > 0.02:
            pygame.draw.arc(p, (255, 230, 120), rect, math.pi / 2, math.pi / 2 + prog * 2 * math.pi, 5)

    def _glifo(self, p, b, jugador, especiales):
        c = (245, 245, 255)
        x, y, r = b.cx, b.cy, b.r
        if b.nombre == 'izq':
            pygame.draw.polygon(p, c, [(x - 26, y), (x + 14, y - 26), (x + 14, y + 26)])
        elif b.nombre == 'der':
            pygame.draw.polygon(p, c, [(x + 26, y), (x - 14, y - 26), (x - 14, y + 26)])
        elif b.nombre == 'saltar':
            pygame.draw.polygon(p, c, [(x, y - 32), (x + 32, y + 10), (x - 32, y + 10)])
            pygame.draw.rect(p, c, (x - 12, y + 8, 24, 22))
        elif b.nombre == 'magia':
            pts = []
            for i in range(8):
                rad = 30 if i % 2 == 0 else 11
                a = i * math.pi / 4 - math.pi / 2
                pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
            pygame.draw.polygon(p, (150, 190, 255), pts)
            pygame.draw.circle(p, (255, 255, 255), (x, y), 8)
        elif b.nombre == 'pausa':
            pygame.draw.rect(p, c, (x - 9, y - 11, 6, 22))
            pygame.draw.rect(p, c, (x + 3, y - 11, 6, 22))
        else:                                    # esp1..esp3
            i = int(b.nombre[-1]) - 1
            if self.iconos:
                ic = self.iconos[i]
                p.blit(ic, (x - ic.get_width() // 2, y - ic.get_height() // 2))
            if jugador is not None and especiales is not None:
                esp = especiales[i]
                cd = jugador.cd_esp[i]
                if cd > 0:
                    pygame.draw.circle(p, (0, 0, 0), (x, y), r - 4, 0)
                    t = self.fuente.render(f"{cd:.0f}", True, (255, 255, 255))
                    p.blit(t, t.get_rect(center=(x, y)))
                elif jugador.mana < esp['coste']:
                    pygame.draw.circle(p, (40, 40, 80), (x, y), r - 4, 0)
            t = self.fuente.render(str(i + 1), True, (255, 230, 120))
            p.blit(t, (x - r + 8, y - r + 6))
