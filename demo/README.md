# Predice-IA — vista de demostración web

El archivo `index.html` es una copia autónoma del panel de demostración con datos ficticios. Se despliega en GitHub Pages y permite explorar navegación, gráficos, analítica y simulación visual.

**No contiene ni ejecuta el motor Python** y **no permite guardar ni importar información**. Para funcionalidades reales hay que ejecutar `mvp/server.py` en entorno autenticado. Nunca subas datos personales o secretos a `demo/`.

Workflow: `.github/workflows/pages-demo.yml`. Para habilitar Pages en un repositorio por primera vez, es posible que el administrador deba seleccionar `Settings → Pages → Source: GitHub Actions` si el permiso de automatización no alcanza.
