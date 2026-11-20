"""
preparar_web.py - Ajusta la página generada por Pygbag para usar TODA la pantalla (PC, Android, iOS).

Ejecutar DESPUÉS de   pygbag --build videojuego   y ANTES de subir a GitHub/Vercel:

    python videojuego/preparar_web.py          (desde la carpeta que contiene a videojuego)
    python preparar_web.py                     (desde dentro de videojuego)

Qué hace en build/web/index.html (se puede ejecutar varias veces sin problema):
  - Título de la pestaña: "Aserot: The Last Mage".
  - El lienzo del juego ocupa toda el área útil de la ventana/pantalla (respetando el notch de los móviles).
    La página mide la proporción de la pantalla y se la comunica al juego (window.ASEROT_ASPECTO); el juego
    ajusta entonces su ancho lógico (alto fijo de 720) para llenarla sin barras negras ni deformaciones.
    Límites de proporción: de 16:9 a 2.5:1. Fuera de ese rango quedan franjas negras.
  - Se recalcula solo al girar el dispositivo, cambiar el tamaño de la ventana o entrar en pantalla completa.
  - Emscripten (el motor de Pygbag) fija el tamaño del lienzo con estilos "!important" en línea; por eso el
    ajuste se reaplica en cada cuadro y cada vez que alguien cambia esos estilos.
  - En móviles/tablets, el primer toque pide pantalla completa y orientación horizontal (iPhone no lo permite
    desde la web: ver "Añadir a pantalla de inicio" en GUIA_WEB.md).
"""
import os
import re
import sys

TITULO = "Aserot: The Last Mage"
INICIO = "<!-- aserot-movil:inicio v2 -->"
FIN = "<!-- aserot-movil:fin -->"
RAIZ = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(RAIZ, "build", "web", "index.html")

BLOQUE = INICIO + """
<meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-title" content="Aserot">
<meta name="apple-mobile-web-app-status-bar-style" content="black-fullscreen">
<meta name="theme-color" content="#000000">
<style>
  html, body { margin: 0 !important; padding: 0 !important; width: 100% !important; height: 100% !important;
               overflow: hidden !important; background: #000 !important; overscroll-behavior: none;
               touch-action: none; -webkit-user-select: none; user-select: none;
               -webkit-touch-callout: none; -webkit-tap-highlight-color: transparent; }
  canvas.emscripten { position: fixed !important; margin: 0 !important; border: 0 !important; padding: 0 !important;
                      background: #000 !important; touch-action: none; outline: none; }
</style>
<script>
(function () {
  var MIN = 16 / 9, MAX = 2.5;                 // proporciones admitidas (igual que ASPECTO_MIN/MAX en main.py)
  var sonda = null, margen = { t: 0, r: 0, b: 0, l: 0 }, medidas = null, ultimaMedida = 0;

  // Zonas seguras (notch, barras redondeadas): se leen una vez y al cambiar el tamaño
  function leerMargenes() {
    try {
      if (!sonda) {
        sonda = document.createElement('div');
        sonda.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;visibility:hidden;pointer-events:none;' +
          'padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) ' +
          'env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)';
        document.documentElement.appendChild(sonda);
      }
      var cs = getComputedStyle(sonda);
      margen = { t: parseFloat(cs.paddingTop) || 0, r: parseFloat(cs.paddingRight) || 0,
                 b: parseFloat(cs.paddingBottom) || 0, l: parseFloat(cs.paddingLeft) || 0 };
    } catch (e) {}
  }

  function medir() {
    leerMargenes();
    var w = Math.max(1, window.innerWidth - margen.l - margen.r);
    var h = Math.max(1, window.innerHeight - margen.t - margen.b);
    var asp = Math.max(MIN, Math.min(MAX, w / h));
    var cw = Math.min(w, h * asp), ch = cw / asp;
    medidas = { left: Math.round(margen.l + (w - cw) / 2), top: Math.round(margen.t + (h - ch) / 2),
                w: Math.round(cw), h: Math.round(ch), asp: asp };
    window.ASEROT_ASPECTO = asp;                // el juego lo lee para calcular su ancho lógico
    ultimaMedida = performance.now();
  }

  function fijar(c, k, v) {
    if (c.style.getPropertyValue(k) !== v || c.style.getPropertyPriority(k) !== 'important')
      c.style.setProperty(k, v, 'important');
  }

  function aplicar() {
    if (!medidas || performance.now() - ultimaMedida > 500) medir();
    var c = document.getElementById('canvas');
    if (!c) return;
    fijar(c, 'position', 'fixed');
    fijar(c, 'left', medidas.left + 'px');
    fijar(c, 'top', medidas.top + 'px');
    fijar(c, 'right', 'auto');
    fijar(c, 'bottom', 'auto');
    fijar(c, 'width', medidas.w + 'px');
    fijar(c, 'height', medidas.h + 'px');
    fijar(c, 'max-width', 'none');
    fijar(c, 'max-height', 'none');
    fijar(c, 'margin', '0');
    fijar(c, 'transform', 'none');
  }

  function remedir() { medidas = null; aplicar(); }
  window.addEventListener('resize', remedir);
  window.addEventListener('orientationchange', function () { setTimeout(remedir, 150); setTimeout(remedir, 500); });
  document.addEventListener('fullscreenchange', function () { setTimeout(remedir, 150); });
  document.addEventListener('webkitfullscreenchange', function () { setTimeout(remedir, 150); });
  if (window.visualViewport) window.visualViewport.addEventListener('resize', remedir);

  // Si Emscripten/Pygbag cambian el estilo del lienzo, se restaura al instante
  function vigilar() {
    var c = document.getElementById('canvas');
    if (!c || c._aserotVigilado) return;
    c._aserotVigilado = true;
    try { new MutationObserver(aplicar).observe(c, { attributes: true, attributeFilter: ['style', 'width', 'height'] }); }
    catch (e) {}
  }
  (function bucle() { vigilar(); aplicar(); requestAnimationFrame(bucle); })();
  medir();

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
  document.addEventListener('gesturestart', function (e) { e.preventDefault(); });   // sin zoom con pellizco (iOS)
  document.addEventListener('contextmenu', function (e) { e.preventDefault(); });    // sin menú al mantener pulsado
})();
</script>
""" + FIN + "\n"


def main():
    if not os.path.isfile(INDEX):
        print("No existe", INDEX)
        print("Primero ejecuta:  pygbag --build videojuego   (desde la carpeta que contiene a videojuego)")
        return 1
    with open(INDEX, encoding="utf-8") as f:
        html = f.read()

    # quitar parches anteriores (versión 1 sin marca de fin, o versión 2 ya aplicada)
    html = re.sub(re.escape(INICIO) + r".*?" + re.escape(FIN) + r"\n?", "", html, flags=re.S)
    html = re.sub(r"<!-- aserot-movil -->.*?</script>\n?", "", html, count=1, flags=re.S)

    # título de la pestaña
    html, n = re.subn(r"<title>.*?</title>", "<title>" + TITULO + "</title>", html, count=1, flags=re.S)
    if n == 0:
        print("Aviso: no encontré <title>")

    # los viewport que trae Pygbag (dos; el segundo anula al primero) se sustituyen por el nuestro
    html = re.sub(r'\s*<meta name="viewport"[^>]*>', "", html)

    i = html.find("</head>")
    if i == -1:
        print("No encontré </head> en index.html: no se aplicó el parche.")
        return 1
    html = html[:i] + BLOQUE + html[i:]

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print("build/web/index.html preparado: pantalla completa y adaptable (PC, Android, iOS).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
