"""
preparar_web.py - Ajusta la página generada por Pygbag para móviles y pantalla completa.

Ejecutar DESPUÉS de   pygbag --build videojuego   y ANTES de subir a GitHub/Vercel:

    python videojuego/preparar_web.py          (desde la carpeta que contiene a videojuego)
    python preparar_web.py                     (desde dentro de videojuego)

Qué hace en build/web/index.html (se puede ejecutar varias veces sin problema):
  - Título de la pestaña: "Aserot: The Last Mage".
  - Viewport sin zoom ni scroll, con fondo negro y sin gestos del navegador que molesten al jugar.
  - El juego (16:9) se escala para ocupar la mayor parte posible de la pantalla, centrado y sin deformarse,
    en cualquier tamaño de móvil, tablet o PC (se recalcula al girar el dispositivo).
  - Al primer toque en un móvil/tablet pide pantalla completa y bloquear la orientación horizontal
    (iPhone no permite pantalla completa desde la web: ver "Añadir a pantalla de inicio" en GUIA_WEB.md).
"""
import os
import sys

TITULO = "Aserot: The Last Mage"
MARCA = "<!-- aserot-movil -->"
RAIZ = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(RAIZ, "build", "web", "index.html")

CABECERA = MARCA + """
<meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-title" content="Aserot">
<meta name="apple-mobile-web-app-status-bar-style" content="black-fullscreen">
<meta name="theme-color" content="#000000">
<style>
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #000 !important;
               overscroll-behavior: none; touch-action: none; -webkit-user-select: none; user-select: none;
               -webkit-touch-callout: none; -webkit-tap-highlight-color: transparent; }
  /* El lienzo mantiene la proporción 16:9 y se centra; el JS de abajo ajusta el tamaño exacto en píxeles. */
  canvas.emscripten { position: fixed !important; top: 0 !important; bottom: 0 !important; left: 0 !important;
                      right: 0 !important; margin: auto !important; border: 0 !important; padding: 0 !important;
                      background: #000 !important; touch-action: none; outline: none; }
</style>
<style id="aserot-tam"></style>
<script>
(function () {
  var RATIO = 16 / 9;
  function ajustar() {
    var w = window.innerWidth, h = window.innerHeight;
    var cw = Math.min(w, h * RATIO), ch = cw / RATIO;
    var st = document.getElementById('aserot-tam');
    if (st) st.textContent = 'canvas.emscripten{width:' + Math.floor(cw) + 'px !important;height:' +
                             Math.floor(ch) + 'px !important;max-width:none !important;max-height:none !important}';
  }
  window.addEventListener('resize', ajustar);
  window.addEventListener('orientationchange', function () { setTimeout(ajustar, 200); });
  document.addEventListener('DOMContentLoaded', ajustar);
  setInterval(ajustar, 1000);                      // por si la barra del navegador cambia de tamaño
  ajustar();

  // Pantalla completa en el primer toque (los navegadores solo la permiten tras un gesto del usuario)
  var tactil = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  function pantallaCompleta() {
    var el = document.documentElement;
    var pedir = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
    if (!pedir || document.fullscreenElement || document.webkitFullscreenElement) return;
    try {
      var r = pedir.call(el, { navigationUI: 'hide' });
      var bloquear = function () {
        try { if (screen.orientation && screen.orientation.lock) screen.orientation.lock('landscape').catch(function () {}); }
        catch (e) {}
      };
      if (r && r.then) r.then(bloquear).catch(function () {}); else bloquear();
    } catch (e) {}
  }
  if (tactil) {
    ['touchend', 'click'].forEach(function (ev) { document.addEventListener(ev, pantallaCompleta, { capture: true }); });
  }
  document.addEventListener('fullscreenchange', function () { setTimeout(ajustar, 200); });
  document.addEventListener('gesturestart', function (e) { e.preventDefault(); });   // sin zoom con pellizco (iOS)
  document.addEventListener('contextmenu', function (e) { e.preventDefault(); });    // sin menú al mantener pulsado
})();
</script>
"""


def main():
    if not os.path.isfile(INDEX):
        print("No existe", INDEX)
        print("Primero ejecuta:  pygbag --build videojuego   (desde la carpeta que contiene a videojuego)")
        return 1
    with open(INDEX, encoding="utf-8") as f:
        html = f.read()
    if MARCA in html:
        print("build/web/index.html ya estaba preparado. Nada que hacer.")
        return 0

    # 1) título de la pestaña
    import re
    html, n = re.subn(r"<title>.*?</title>", "<title>" + TITULO + "</title>", html, count=1, flags=re.S)
    if n == 0:
        print("Aviso: no encontré <title>")

    # 2) los viewport que trae Pygbag (dos, y el segundo anula al primero) se sustituyen por el nuestro
    html = re.sub(r'\s*<meta name="viewport"[^>]*>', "", html)
    for marca in ("</head>", "<body>", "<body "):
        i = html.find(marca)
        if i != -1:
            html = html[:i] + CABECERA + html[i:]
            break
    else:
        print("No encontré </head> ni <body> en index.html: no se aplicó el parche.")
        return 1

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print("build/web/index.html preparado para móviles y pantalla completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
