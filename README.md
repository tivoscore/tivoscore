# TivoScore — Landing + Autodiagnóstico

App multipágina de Streamlit: la landing (`Home.py`) enlaza directo al
formulario de autodiagnóstico (`pages/1_📝_Cómo_manejas_tu_negocio.py`), que guarda
cada respuesta en Google Sheets y genera un informe en PDF para tu revisión
interna antes de enviar nada al cliente.

**Importante:** este repositorio es solo la landing + el autodiagnóstico.
El paquete de Control de Ventas y Cobros (el producto gratuito que se
entrega después del diagnóstico) es un proyecto aparte, de autoinstalación
local — no va aquí ni se despliega en la nube. Ver el Plan Definitivo,
Sección 3, para la razón.

---

## Estructura

```
tivoscore-app/
├── Home.py                          ← la landing
├── pages/
│   └── 1_📝_Cómo_manejas_tu_negocio.py  ← el formulario
├── avatar_tivoscore.png             ← tu foto/logo (usada en Home.py)
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml.example         ← copiar como secrets.toml y completar
```

## Configuración

Sigue los Pasos 1 a 4 de la guía de credenciales de Google que ya tienes
(crear proyecto en Google Cloud, cuenta de servicio, compartir tu hoja de
leads con esa cuenta). Luego:

1. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml`.
2. Completa `autodiagnostico_sheet_id` con el ID de tu hoja de leads.
3. Elige una contraseña para `admin_password` — con ella entras al Panel
   Interno del autodiagnóstico para revisar los informes en PDF.
4. Completa los 4 campos `recurso_...` con los enlaces reales a tus
   recursos de valor (o dejalos así hasta tenerlos listos — la app no
   se rompe si faltan, solo muestra un enlace de marcador).
5. Completa el bloque `[gcp_service_account]` con los datos del archivo
   `.json` de tu cuenta de servicio.

## Ejecutar en local

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Publicar en Streamlit Cloud (gratis)

1. Sube esta carpeta a GitHub (sin `secrets.toml` real — ya está en
   `.gitignore`).
2. Ve a [share.streamlit.io](https://share.streamlit.io), conecta tu
   cuenta de GitHub, selecciona el repositorio y el archivo principal
   `Home.py`.
3. En la configuración de la app → "Secrets", pega el contenido completo
   de tu `secrets.toml` real (ahí es seguro, es un campo separado del
   repositorio, nunca queda expuesto públicamente).
4. Publica. Obtienes un link tipo `https://tu-app.streamlit.app` para
   compartir en LinkedIn y usar como el botón de tu landing en Carrd.

## Nota sobre `pages/1_📝_Cómo_manejas_tu_negocio.py`

Si ya tienes tu propia versión actualizada de este archivo, reemplaza el
que viene en esta carpeta antes de subir a GitHub — el que está aquí es
la última versión reconstruida y probada que tenemos en el proyecto,
pero puede no ser tu versión más reciente.
