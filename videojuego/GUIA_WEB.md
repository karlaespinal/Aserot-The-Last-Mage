# Publicar "Aserot: The Last Mage" en la web (Pygbag + GitHub + Vercel)

## 1. Probarlo en el navegador (en tu PC)
Desde la carpeta que CONTIENE a `videojuego/` (no dentro):

    pip install pygbag
    pygbag videojuego

Abre http://localhost:8000 (la primera vez descarga el motor y tarda un poco).
Si juega bien ahí, está listo para publicar.

## 2. Generar la versión web
    pygbag --build videojuego

Crea `videojuego/build/web/` (index.html + videojuego.apk + favicon). **Esa carpeta es lo que se publica.**
Cada vez que cambies el código o los assets, vuelve a ejecutar este comando.

### 2b. Preparar para móviles y pantalla completa (OBLIGATORIO tras cada build)
    python videojuego/preparar_web.py

Parchea `build/web/index.html`: pone el título "Aserot: The Last Mage", escala el juego (16:9) para ocupar la
pantalla de cualquier móvil/tablet/PC sin deformarlo, y al primer toque pide pantalla completa y orientación
horizontal. Se puede ejecutar varias veces sin problema. Hay que repetirlo cada vez que vuelvas a hacer `pygbag --build`.

## 3. Subir a GitHub
Dentro de `videojuego/`:

    git init
    git add .
    git commit -m "Aserot: The Last Mage - version web"
    git branch -M main
    git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
    git push -u origin main

IMPORTANTE: `build/web/` debe quedar en el repositorio (el `.gitignore` solo excluye `build/web-cache/`).

## 4. Conectar en Vercel
1. vercel.com -> Add New -> Project -> importa el repositorio de GitHub.
2. Framework Preset: **Other**. No pongas Build Command ni Install Command (ya lo define `vercel.json`).
3. Output Directory: `build/web` (también está en `vercel.json`).
4. Deploy. Cada `git push` con una nueva carpeta `build/web` se republica solo.

## Notas
- Importante: tras estos cambios hay que volver a ejecutar `pygbag --build videojuego`; la carpeta `build/web` que hay ahora es de la versión anterior.
- El título de la pestaña lo pone `preparar_web.py` ("Aserot: The Last Mage").
- Controles en PC: A/D, ESPACIO, SHIFT, J, 1/2/3, P. Haz clic en el juego para darle foco al teclado.
- Móvil / tablet (Android e iOS): abre la URL en el navegador y juega en horizontal. Los botones táctiles aparecen al tocar la pantalla; correr es automático (mantén una dirección 2 s). Si el dispositivo está en vertical, el juego pide girarlo.
- Pantalla completa: en Android (Chrome) se activa sola al primer toque. iPhone/iOS no permite pantalla completa desde la web: en Safari pulsa Compartir -> "Añadir a pantalla de inicio" y abre el juego desde ese icono (se ve sin barras). En iPad suele funcionar el primer toque.
- Niveles bloqueados: el progreso se guarda en el `localStorage` del navegador (cada navegador/dispositivo tiene el suyo; se pierde si se borran los datos del sitio o se usa modo privado).
- En el navegador no existe "salir": ESC solo pausa.
- Si al cargar ves pantalla negra: revisa la consola del navegador (F12) y que estés usando https o localhost.
