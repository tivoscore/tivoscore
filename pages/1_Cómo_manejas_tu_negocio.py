"""
Autodiagnóstico TIVOSCORE
--------------------------------------
Formulario de autodiagnóstico con motor de análisis profundo.

Flujo:
1. La persona responde el formulario (~3 minutos).
2. En pantalla solo ve un agradecimiento breve — nunca el análisis completo.
3. Por cada respuesta se genera automáticamente:
   - Una fila nueva en Google Sheets.
   - Un informe en PDF (para tu revisión).
   - Un archivo de texto con el mensaje sugerido.
4. Tú revisas el informe y envías el mensaje personalizado cuando quieras.
"""

import datetime as dt
import hashlib
import re
import base64  # <--- AGREGAR ESTA LÍNEA
from pathlib import Path
from typing import Any, Dict, List, Optional

import gspread
import streamlit as st
from fpdf import FPDF
from google.oauth2.service_account import Credentials
from PIL import Image

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
def _img_b64(path: str):
    """Carga una imagen local como base64 para embeberla en HTML."""
    try:
        return base64.b64encode(Path(path).read_bytes()).decode()
    except FileNotFoundError:
        return None


AVATAR_B64 = _img_b64("avatar_tivoscore.png")

try:
    _favicon = Image.open("avatar_tivoscore.png")
except FileNotFoundError:
    _favicon = "📊"

st.set_page_config(
    page_title="TIVOSCORE · Autodiagnóstico Operativo",
    page_icon=_favicon,
    layout="centered",
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SHEET_TAB_NAME = "Autodiagnosticos"
CARPETA_INFORMES = Path("informes_generados")

HEADERS = [
    "Fecha", "Nombre", "Negocio", "Tipo de Negocio", "Contacto", "Canal",
    "Perfil Detectado", "Puntaje Perfil",
    "Madurez", "Dependencia", "Visibilidad", "Delegacion", "Estabilidad", "Brecha Percepcion",
    "Costo Hora", "Tiempo Admin %", "Horas Admin Semana", "Costo Admin Mes",
    "Mensaje Sugerido", "Hash Sesion",
]

# ============================================================
# PREGUNTAS: PUNTO CIEGO
# ============================================================
CATEGORIAS = {
    "ventas_cobros": {
        "nombre": "Ventas y Cobros",
        "preguntas": [
            "Sé exactamente cuánto vendí ayer, sin revisar varios lugares.",
            "Sé cuánto me deben mis clientes en total, en este momento.",
        ],
    },
    "pedidos_entregas": {
        "nombre": "Pedidos y Entregas",
        "preguntas": [
            "Sé en qué va cada pedido pendiente, sin tener que preguntar.",
            "Mis pedidos casi nunca se retrasan o se pierden.",
        ],
    },
    "produccion": {
        "nombre": "Producción / Entrega",
        "preguntas": [
            "Sé cuánto me cuesta realmente producir o entregar lo que vendo.",
            "Cumplo los tiempos que prometo cuando fabrico o preparo un pedido.",
        ],
    },
    "procesos": {
        "nombre": "Procesos y Estructura",
        "preguntas": [
            "Si yo falto un día, mi equipo sabe cómo seguir sin mí.",
            "Los procesos clave de mi negocio están escritos en algún lugar.",
        ],
    },
}

OPCIONES_ESCALA = {
    "1 · Para nada": 1,
    "2 · Muy poco": 2,
    "3 · A veces": 3,
    "4 · Casi siempre": 4,
    "5 · Totalmente": 5,
    "No aplica a mi negocio": None,
}

TIPOS_NEGOCIO = [
    "Comercio / tienda", "Ferretería o distribuidora", "Taller o servicio técnico",
    "Alimentos / delivery", "Fabricación o producción propia", "Servicios profesionales", "Otro",
]
CANALES = ["Búsqueda en Google", "Recomendación de alguien", "LinkedIn", "WhatsApp", "Otro"]


# ============================================================
# LIMPIAR TEXTO PARA PDF (evita errores de codificación)
# ============================================================
def limpiar_texto_pdf(texto: str) -> str:
    """Convierte cualquier texto a ASCII básico (compatible con latin-1)."""
    if not texto:
        return texto
    reemplazos = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201C": '"', "\u201D": '"', "\u2026": "...", "\u2022": "*",
        "\u00B7": "*", "\u2212": "-", "\u2010": "-", "\u2011": "-",
    }
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    texto = texto.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    texto = texto.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    texto = texto.replace("ñ", "n").replace("Ñ", "N")
    texto = texto.replace("ü", "u").replace("Ü", "U")
    texto = texto.replace("ç", "c").replace("Ç", "C")
    resultado = []
    for char in texto:
        codigo = ord(char)
        if 32 <= codigo <= 126 or 160 <= codigo <= 255:
            resultado.append(char)
        elif codigo in (10, 13):
            resultado.append(' ')
    texto_limpio = ''.join(resultado)
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
    return texto_limpio


# ============================================================
# ESTILO PARA PDF (alineado con Brief de Identidad Visual)
# ============================================================
def pdf_set_style(pdf: FPDF, tipo: str = "normal", color: str = "ink"):
    """Aplica estilos predefinidos al PDF según el brief de marca."""
    colores = {
        "ink": (22, 35, 58),      # #16233A
        "slate": (61, 84, 112),   # #3D5470
        "amber": (192, 138, 62),  # #C08A3E
        "paper": (246, 243, 236), # #F6F3EC
        "green": (75, 122, 91),   # #4B7A5B
        "brick": (166, 71, 58),   # #A6473A
        "text": (28, 31, 38),     # #1C1F26
        "text_soft": (91, 100, 114), # #5B6472
        "white": (255, 255, 255),
    }
    rgb = colores.get(color, colores["text"])
    pdf.set_text_color(*rgb)
    if tipo == "title":
        pdf.set_font("Helvetica", "B", 16)
    elif tipo == "subtitle":
        pdf.set_font("Helvetica", "B", 12)
    elif tipo == "section":
        pdf.set_font("Helvetica", "B", 11)
    elif tipo == "normal":
        pdf.set_font("Helvetica", "", 10)
    elif tipo == "small":
        pdf.set_font("Helvetica", "", 8)
    elif tipo == "mono":
        pdf.set_font("Courier", "", 9)
    else:
        pdf.set_font("Helvetica", "", 10)


# ============================================================
# MOTOR DE ANÁLISIS
# ============================================================
def _avg(values: List[Optional[int]]) -> Optional[float]:
    validos = [v for v in values if v is not None]
    return round(sum(validos) / len(validos), 2) if validos else None


def _norm_5(value: Optional[float], reverse: bool = False) -> float:
    if value is None:
        return 50.0
    score = ((value - 1) / 4) * 100
    return round(100 - score if reverse else score, 1)


def calcular_punto_ciego(respuestas: Dict[str, List[Optional[int]]]) -> Dict[str, Any]:
    promedios = {cat: _avg(vals) for cat, vals in respuestas.items() if _avg(vals) is not None}
    if not promedios:
        return {"promedios": {}, "perfil_debil": None, "perfil_fuerte": None, "brecha": 0}
    perfil_debil = min(promedios, key=promedios.get)
    perfil_fuerte = max(promedios, key=promedios.get)
    return {
        "promedios": promedios,
        "perfil_debil": perfil_debil,
        "perfil_fuerte": perfil_fuerte,
        "brecha": round(promedios[perfil_fuerte] - promedios[perfil_debil], 2),
    }


def calcular_metricas(r: Dict[str, Any]) -> Dict[str, Any]:
    punto = calcular_punto_ciego(r["punto_ciego"])
    prom = punto["promedios"]

    visibilidad = round((len(r["puede_saber"]) / 4) * 100, 1)

    registro_map = {
        "En un sistema centralizado": 100,
        "En diferentes lugares (Excel, WhatsApp, papel)": 45,
        "No tengo un registro claro": 10,
    }
    registro = registro_map.get(r["registro_informacion"], 30)

    interv_map = {"Ninguna": 0, "1-2 veces": 30, "3-5 veces": 65, "Más de 5 veces": 100}
    interv = interv_map.get(r["intervenciones_semanales"], 50)

    resolucion_map = {
        "Las resuelve el equipo": 0,
        "Las resuelvo yo, pero el equipo también participa": 55,
        "Las resuelvo yo mismo": 100,
    }
    resolucion = resolucion_map.get(r["resolucion_incidencias"], 50)

    percepcion_dependencia_norm = _norm_5(r["percepcion_dependencia"])
    percepcion_control_norm = _norm_5(r["percepcion_control"])
    percepcion_independencia_norm = _norm_5(r["percepcion_dependencia"], reverse=True)

    delegacion = round(100 - (interv * 0.40 + resolucion * 0.35 + percepcion_dependencia_norm * 0.25), 1)

    if r["problemas_repetitivos"] == "No":
        estabilidad = 90
    elif r["solucion_problemas"] == "Se soluciona de manera definitiva":
        estabilidad = 80
    elif r["solucion_problemas"] == "Se vuelve a resolver de la misma manera":
        estabilidad = 35
    else:
        estabilidad = 15

    punto_ciego_score = sum(_norm_5(v) for v in prom.values()) / len(prom) if prom else 50

    madurez = round(punto_ciego_score * 0.35 + visibilidad * 0.20 + registro * 0.15 + delegacion * 0.20 + estabilidad * 0.10, 1)

    dependencia = round(100 - (delegacion * 0.50 + percepcion_independencia_norm * 0.25 + estabilidad * 0.25), 1)

    evidencia_control = round(punto_ciego_score * 0.5 + visibilidad * 0.3 + estabilidad * 0.2, 1)
    brecha_percepcion = round(percepcion_control_norm - evidencia_control, 1)

    costo_hora = r.get("costo_hora", 0)
    tiempo_administrativo = r.get("tiempo_administrativo", 50)

    horas_admin_semana = round((tiempo_administrativo / 100) * 40, 1)
    costo_admin_semana = round(horas_admin_semana * costo_hora, 2) if costo_hora > 0 else 0
    costo_admin_mes = round(costo_admin_semana * 4.3, 2) if costo_hora > 0 else 0

    if tiempo_administrativo > 60:
        nivel_fuga = "Alta"
    elif tiempo_administrativo > 40:
        nivel_fuga = "Media"
    else:
        nivel_fuga = "Baja"

    return {
        "punto_ciego": punto,
        "visibilidad": visibilidad,
        "registro": registro,
        "delegacion": delegacion,
        "estabilidad": estabilidad,
        "madurez": madurez,
        "dependencia": dependencia,
        "evidencia_control": evidencia_control,
        "brecha_percepcion": brecha_percepcion,
        "costo_hora": costo_hora,
        "tiempo_administrativo": tiempo_administrativo,
        "horas_admin_semana": horas_admin_semana,
        "costo_admin_semana": costo_admin_semana,
        "costo_admin_mes": costo_admin_mes,
        "nivel_fuga": nivel_fuga,
    }


def detectar_relaciones(r: Dict[str, Any], m: Dict[str, Any]) -> List[Dict[str, str]]:
    relaciones = []
    prom = m["punto_ciego"]["promedios"]

    if m["registro"] < 60 and m["visibilidad"] < 50:
        relaciones.append({
            "titulo": "La falta de visibilidad está relacionada con la fragmentación de la información.",
            "detalle": "No basta con tener datos: si están repartidos entre herramientas, hojas y WhatsApp, hace falta reconstruir la situación cada vez que se necesita saber algo.",
        })

    if m["dependencia"] >= 60 and m["estabilidad"] < 60:
        relaciones.append({
            "titulo": "Las incidencias repetitivas están reforzando la dependencia del dueño.",
            "detalle": "Cada problema que vuelve a resolverse manualmente consume tiempo y evita que el equipo lo convierta en un procedimiento propio.",
        })

    if prom.get("ventas_cobros", 5) < 3 and m["visibilidad"] < 50:
        relaciones.append({
            "titulo": "El punto débil de ventas y cobros está acompañado por baja visibilidad general.",
            "detalle": "La combinación dificulta saber rápido qué se vendió, qué está pendiente de cobro, y dónde concentrar la gestión de cobranza.",
        })

    if prom.get("pedidos_entregas", 5) < 3 and prom.get("procesos", 5) < 3:
        relaciones.append({
            "titulo": "Los problemas de pedidos probablemente se originan en procesos poco estandarizados.",
            "detalle": "Cuando el seguimiento depende de preguntar y los procesos no están documentados, los retrasos tienden a repetirse con distintas personas.",
        })

    if m["brecha_percepcion"] >= 20:
        relaciones.append({
            "titulo": "La percepción de control es considerablemente mayor que la evidencia operativa real.",
            "detalle": "Vale la pena validar el control percibido con datos y tiempos de respuesta reales, no solo con la sensación del día a día.",
        })

    if m["tiempo_administrativo"] > 50 and m["dependencia"] > 50:
        relaciones.append({
            "titulo": "El alto tiempo administrativo está directamente relacionado con la dependencia del dueño.",
            "detalle": f"Dedicar el {m['tiempo_administrativo']}% de tu tiempo a tareas operativas te impide enfocarte en hacer crecer el negocio. Esto equivale a {m['costo_admin_mes']:,.0f} en costo de oportunidad mensual.",
        })

    return relaciones


def generar_prioridades(m: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidatos = []
    if m["visibilidad"] < 50:
        candidatos.append((95, "Visibilidad y control", "Crear una fuente única de información para los indicadores operativos críticos."))
    if m["delegacion"] < 55:
        candidatos.append((92, "Delegación", "Identificar decisiones repetitivas y convertirlas en reglas que el equipo pueda ejecutar sin pedir autorización."))
    if m["estabilidad"] < 60:
        candidatos.append((90, "Problemas repetitivos", "Documentar las incidencias recurrentes, su causa y la solución estándar."))
    if m["registro"] < 60:
        candidatos.append((85, "Información dispersa", "Reducir la dispersión de datos y definir un único lugar de registro por tipo de dato crítico."))

    perfil_debil = m["punto_ciego"]["perfil_debil"]
    textos_perfil = {
        "ventas_cobros": (90, "Ventas y cobros", "Construir un control diario de ventas, cuentas por cobrar y vencimientos."),
        "pedidos_entregas": (90, "Pedidos y entregas", "Crear un tablero de pedidos con estado, responsable y fecha comprometida."),
        "produccion": (85, "Costos y entrega", "Separar costo, tiempo y cumplimiento para conocer la rentabilidad operativa real."),
        "procesos": (95, "Procesos críticos", "Documentar primero los procesos que hoy dependen directamente del dueño."),
    }
    if perfil_debil in textos_perfil:
        candidatos.append(textos_perfil[perfil_debil])

    if m["nivel_fuga"] == "Alta" and m["costo_hora"] > 0:
        candidatos.append((88, "Reducir el costo de oportunidad", f"Automatizar o delegar tareas administrativas para recuperar {m['horas_admin_semana']} horas/semana que valen {m['costo_admin_semana']:,.0f}."))

    vistos, salida = set(), []
    for prioridad, titulo, accion in sorted(candidatos, reverse=True):
        if titulo not in vistos:
            vistos.add(titulo)
            salida.append({"prioridad": prioridad, "titulo": titulo, "accion": accion})
    return salida[:5]


def nivel_texto(score: float) -> str:
    if score >= 75:
        return "Alto"
    if score >= 50:
        return "Medio"
    return "Bajo"


def generar_informe(r: Dict[str, Any]) -> Dict[str, Any]:
    m = calcular_metricas(r)
    relaciones = detectar_relaciones(r, m)
    prioridades = generar_prioridades(m)

    perfil_key = m["punto_ciego"]["perfil_debil"]
    perfil_nombre = CATEGORIAS.get(perfil_key, {}).get("nombre", "General") if perfil_key else "General"
    puntaje_perfil = m["punto_ciego"]["promedios"].get(perfil_key, 0) if perfil_key else 0

    nivel_dependencia = "alta" if m["dependencia"] >= 65 else "media" if m["dependencia"] >= 40 else "baja"

    resumen_dos_lineas = (
        f"Tu área de mayor oportunidad hoy es {perfil_nombre.lower()}. "
        f"Tu nivel de dependencia del día a día es {nivel_dependencia}."
    )

    resumen_ejecutivo = (
        f"El diagnóstico muestra un punto ciego principal en {perfil_nombre.lower()} "
        f"(puntaje {puntaje_perfil}/5), con una madurez operativa de {m['madurez']}/100 "
        f"({nivel_texto(m['madurez'])}) y una dependencia del dueño de {m['dependencia']}/100 "
        f"({nivel_texto(m['dependencia'])}). "
        f"Además, dedicas {m['tiempo_administrativo']}% de tu tiempo a tareas administrativas, "
        f"lo que equivale a {m['costo_admin_mes']:,.0f} en costo de oportunidad mensual."
    )

    return {
        "perfil_key": perfil_key,
        "perfil_nombre": perfil_nombre,
        "puntaje_perfil": puntaje_perfil,
        "nivel_dependencia": nivel_dependencia,
        "metricas": m,
        "relaciones": relaciones,
        "prioridades": prioridades,
        "resumen_dos_lineas": resumen_dos_lineas,
        "resumen_ejecutivo": resumen_ejecutivo,
    }


# ============================================================
# MENSAJE PERSONALIZADO
# ============================================================
PLANTILLAS_MENSAJE = {
    "ventas_cobros": (
        "Hola {nombre},\n\n"
        "Según tus respuestas, tu punto de atención principal hoy está en el control de ventas y cobros. "
        "No siempre es fácil saber cuánto vendiste ayer ni cuánto te deben en total. "
        "Esto es más común de lo que parece, y casi siempre significa dinero que existe pero que no se está viendo ni cobrando a tiempo.\n\n"
        "{texto_costo}"
        "{nota_dependencia}"
        "Te comparto un recurso práctico para empezar a ordenar tus ventas y cobros.\n"
        "🔹 **Incluye:**\n"
        "   - 📊 Plantilla en Google Sheets (con fórmulas y KPIs listos)\n"
        "   - 🐍 App en Streamlit para ver tu panel de control en el navegador\n"
        "   - 📖 Manual paso a paso para configurarlo en 30-40 minutos\n\n"
        "Puedes descargarlo aquí:\n"
        "{enlace}\n\n"
        "Échale un vistazo y cualquier cosa, por aquí ando."
    ),
    "pedidos_entregas": (
        "Hola {nombre},\n\n"
        "Según tus respuestas, tu punto de atención principal hoy está en el seguimiento de pedidos. "
        "Es fácil que algo se retrase o se pierda cuando no hay un registro claro.\n\n"
        "{texto_costo}"
        "{nota_dependencia}"
        "Te comparto un recurso práctico para empezar a ordenar tus ventas y cobros.\n"
        "🔹 **Incluye:**\n"
        "   - 📊 Plantilla en Google Sheets (con fórmulas y KPIs listos)\n"
        "   - 🐍 App en Streamlit para ver tu panel de control en el navegador\n"
        "   - 📖 Manual paso a paso para configurarlo en 30-40 minutos\n\n"
        "Puedes descargarlo aquí:\n"
        "{enlace}\n\n"
        "Échale un vistazo y cualquier cosa, por aquí ando."
    ),
    "produccion": (
        "Hola {nombre},\n\n"
        "Según tus respuestas, tu punto de atención principal hoy está en el costo y tiempo real de producción. "
        "Muchos negocios producen sin saber exactamente cuánto les cuesta cada unidad.\n\n"
        "{texto_costo}"
        "{nota_dependencia}"
        "Te comparto un recurso práctico para empezar a ordenar tus ventas y cobros.\n"
        "🔹 **Incluye:**\n"
        "   - 📊 Plantilla en Google Sheets (con fórmulas y KPIs listos)\n"
        "   - 🐍 App en Streamlit para ver tu panel de control en el navegador\n"
        "   - 📖 Manual paso a paso para configurarlo en 30-40 minutos\n\n"
        "Puedes descargarlo aquí:\n"
        "{enlace}\n\n"
        "Échale un vistazo y cualquier cosa, por aquí ando."
    ),
    "procesos": (
        "Hola {nombre},\n\n"
        "Según tus respuestas, tu punto de atención principal hoy está en que el negocio depende demasiado de ti. "
        "Si faltas un día, no todo sigue funcionando igual.\n\n"
        "{texto_costo}"
        "{nota_dependencia}"
        "Te comparto un recurso práctico para empezar a ordenar tus ventas y cobros.\n"
        "🔹 **Incluye:**\n"
        "   - 📊 Plantilla en Google Sheets (con fórmulas y KPIs listos)\n"
        "   - 🐍 App en Streamlit para ver tu panel de control en el navegador\n"
        "   - 📖 Manual paso a paso para configurarlo en 30-40 minutos\n\n"
        "Puedes descargarlo aquí:\n"
        "{enlace}\n\n"
        "Échale un vistazo y cualquier cosa, por aquí ando."
    ),
}

def obtener_mensaje(perfil: str, nombre: str, nivel_dependencia: str, tiempo_administrativo: int, costo_admin_mes: float) -> str:
    """Genera el mensaje personalizado incluyendo el costo de oportunidad."""
    notas = {
        "alta": "Además, veo que hoy dependes mucho de tu intervención diaria (eso es agotador y limita el crecimiento). ",
        "media": "También veo que todavía intervienes en varias decisiones operativas del día a día. ",
        "baja": "",
    }

    if costo_admin_mes > 0:
        texto_costo = (
            f"Según tus respuestas, estás dedicando el {tiempo_administrativo}% de tu tiempo a tareas administrativas, "
            f"lo que equivale a ${costo_admin_mes:,.0f} USD al mes que podrías estar dedicando a hacer negocio.\n\n"
        )
    else:
        texto_costo = ""

    plantilla = PLANTILLAS_MENSAJE.get(perfil, PLANTILLAS_MENSAJE["procesos"])
    enlace = "https://drive.google.com/uc?export=download&id=1usoXcSFDTpb29AG8BktQImkyvOmT87Dx"

    return plantilla.format(
        nombre=nombre.split()[0] if nombre else "emprendedor",
        texto_costo=texto_costo,
        nota_dependencia=notas.get(nivel_dependencia, ""),
        enlace=enlace,
    )


# ============================================================
# GENERACIÓN DE PDF
# ============================================================
def _slug(texto: str) -> str:
    texto = re.sub(r"[^\w\s-]", "", texto or "").strip().lower()
    return re.sub(r"[\s]+", "-", texto)[:40] or "sin-nombre"


def generar_pdf_informe(datos_contacto: Dict[str, str], informe: Dict[str, Any], ruta: Path):
    """Genera el PDF del diagnóstico con la identidad visual de TIVOSCORE."""
    m = informe["metricas"]
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # --- FONDO (Paper) ---
    pdf.set_fill_color(246, 243, 236)
    pdf.rect(0, 0, 210, 297, "F")

    # --- BANDA SUPERIOR (Ink) ---
    pdf.set_fill_color(22, 35, 58)
    pdf.rect(0, 0, 210, 28, "F")

    # --- LOGO ---
    logo_path = "logo_tivoscore.png"
    try:
        pdf.image(logo_path, x=8, y=4, w=18)
    except:
        pass

    # --- TÍTULO ---
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(30, 8)
    pdf.cell(0, 10, "TIVOSCORE", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(192, 138, 62)
    pdf.set_xy(30, 18)
    pdf.cell(0, 6, "Sistema de Valoracion Operativa", ln=True)

    # --- FECHA ---
    pdf.set_text_color(246, 243, 236)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(150, 8)
    pdf.cell(0, 6, f"Generado: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.set_xy(150, 14)
    pdf.cell(0, 6, "Uso interno - no enviar tal cual", ln=True)

    y = 34

    # SECCIÓN: Datos de contacto
    pdf_set_style(pdf, "section", "ink")
    pdf.set_xy(20, y)
    pdf.cell(0, 8, "Datos de contacto", ln=True)
    y += 6
    pdf_set_style(pdf, "normal", "text")
    for etiqueta, valor in [
        ("Nombre", datos_contacto.get("nombre", "")),
        ("Negocio", datos_contacto.get("negocio", "")),
        ("Tipo de negocio", datos_contacto.get("tipo_negocio", "")),
        ("Contacto", datos_contacto.get("contacto", "")),
        ("Canal", datos_contacto.get("canal", "")),
    ]:
        pdf.set_xy(20, y)
        pdf_set_style(pdf, "normal", "slate")
        pdf.cell(40, 6, f"{etiqueta}:", ln=0)
        pdf_set_style(pdf, "normal", "text")
        pdf.cell(0, 6, limpiar_texto_pdf(str(valor)), ln=True)
        y += 6
    y += 4

    pdf.set_draw_color(192, 138, 62)
    pdf.line(20, y, 190, y)
    y += 6

    # SECCIÓN: Resumen ejecutivo
    pdf_set_style(pdf, "section", "ink")
    pdf.set_xy(20, y)
    pdf.cell(0, 8, "Resumen ejecutivo", ln=True)
    y += 6
    pdf_set_style(pdf, "normal", "text")
    pdf.set_xy(20, y)
    pdf.multi_cell(170, 6, limpiar_texto_pdf(informe["resumen_ejecutivo"]))
    y = pdf.get_y() + 4

    # NUEVA SECCIÓN: El costo de no delegar
    if m["costo_hora"] > 0:
        pdf_set_style(pdf, "section", "ink")
        pdf.set_xy(20, y)
        pdf.cell(0, 8, "El costo de no delegar", ln=True)
        y += 6
        pdf_set_style(pdf, "normal", "text")
        pdf.set_xy(20, y)
        pdf.multi_cell(170, 6,
            f"Estás dedicando el {m['tiempo_administrativo']}% de tu tiempo a tareas administrativas. "
            f"Eso equivale a {m['horas_admin_semana']} horas por semana, "
            f"que a un costo de {m['costo_hora']} por hora, representan "
            f"{m['costo_admin_mes']:,.0f} al mes que podrías estar dedicando a hacer negocio."
        )
        y = pdf.get_y() + 4
        if m["nivel_fuga"] == "Alta":
            pdf_set_style(pdf, "normal", "brick")
            pdf.set_xy(20, y)
            pdf.multi_cell(170, 5,
                "ATENCION: Mas del 60% de tu tiempo se va en tareas operativas. "
                "Esto es insostenible. El primer paso es identificar que tareas puedes delegar o sistematizar."
            )
        elif m["nivel_fuga"] == "Media":
            pdf_set_style(pdf, "normal", "amber")
            pdf.set_xy(20, y)
            pdf.multi_cell(170, 5,
                "Estas en el limite: dedicar entre 40% y 60% de tu tiempo a lo administrativo "
                "es comun, pero te impide crecer. Vale la pena revisar que tareas puedes automatizar."
            )
        else:
            pdf_set_style(pdf, "normal", "green")
            pdf.set_xy(20, y)
            pdf.multi_cell(170, 5,
                "Bien: dedicas menos del 40% de tu tiempo a tareas administrativas. "
                "Eso significa que tienes margen para enfocarte en hacer negocio. "
                "El siguiente paso es sistematizar para mantener ese balance."
            )
        y = pdf.get_y() + 4

    # SECCIÓN: TIVOSCORE destacado
    pdf.set_draw_color(192, 138, 62)
    pdf.set_fill_color(22, 35, 58)
    pdf.rect(20, y, 170, 18, "FD")
    pdf_set_style(pdf, "section", "amber")
    pdf.set_xy(25, y + 3)
    pdf.cell(0, 6, f"TIVOSCORE: {m['madurez']}/100", ln=True)
    pdf_set_style(pdf, "small", "paper")
    pdf.set_xy(25, y + 11)
    pdf.cell(0, 6, f"Madurez operativa: {nivel_texto(m['madurez'])}", ln=True)
    y += 24

    # SECCIÓN: Métricas clave
    pdf_set_style(pdf, "section", "ink")
    pdf.set_xy(20, y)
    pdf.cell(0, 8, "Metricas clave", ln=True)
    y += 6
    pdf_set_style(pdf, "small", "slate")
    pdf.set_xy(20, y)
    pdf.cell(80, 6, "Indicador", border=1)
    pdf.cell(40, 6, "Valor", border=1)
    pdf.cell(50, 6, "Nivel", border=1, ln=True)
    y += 6
    metricas_tabla = [
        ("Madurez operativa", m["madurez"], nivel_texto(m["madurez"])),
        ("Dependencia del dueño", m["dependencia"], "Alta" if m["dependencia"] >= 65 else "Media" if m["dependencia"] >= 40 else "Baja"),
        ("Visibilidad", m["visibilidad"], nivel_texto(m["visibilidad"])),
        ("Delegacion", m["delegacion"], nivel_texto(m["delegacion"])),
        ("Estabilidad", m["estabilidad"], nivel_texto(m["estabilidad"])),
        ("Brecha percepcion vs. evidencia", m["brecha_percepcion"], "Alta" if m["brecha_percepcion"] >= 20 else "Media" if m["brecha_percepcion"] >= 10 else "Baja"),
    ]
    for etiqueta, valor, nivel in metricas_tabla:
        pdf_set_style(pdf, "small", "text")
        pdf.set_xy(20, y)
        pdf.cell(80, 6, limpiar_texto_pdf(etiqueta), border=1)
        pdf.cell(40, 6, f"{valor}/100", border=1)
        if nivel == "Alto" and etiqueta != "Dependencia del dueño":
            pdf_set_style(pdf, "small", "green")
        elif nivel == "Alto" and etiqueta == "Dependencia del dueño":
            pdf_set_style(pdf, "small", "brick")
        elif nivel == "Baja" and etiqueta != "Dependencia del dueño":
            pdf_set_style(pdf, "small", "brick")
        else:
            pdf_set_style(pdf, "small", "slate")
        pdf.cell(50, 6, nivel, border=1, ln=True)
        y += 6
    y += 4

    # SECCIÓN: Puntajes por categoría
    pdf_set_style(pdf, "section", "ink")
    pdf.set_xy(20, y)
    pdf.cell(0, 8, "Puntaje por area (escala 1-5)", ln=True)
    y += 6
    for cat_key, valor in m["punto_ciego"]["promedios"].items():
        nombre_cat = CATEGORIAS[cat_key]["nombre"]
        pdf.set_xy(20, y)
        if cat_key == informe["perfil_key"]:
            pdf_set_style(pdf, "normal", "amber")
            pdf.cell(0, 6, limpiar_texto_pdf(f"{nombre_cat}: {valor}/5  <- punto ciego principal"), ln=True)
        else:
            pdf_set_style(pdf, "normal", "text")
            pdf.cell(0, 6, limpiar_texto_pdf(f"{nombre_cat}: {valor}/5"), ln=True)
        y += 6
    y += 4

    # SECCIÓN: Relaciones detectadas
    if informe["relaciones"]:
        pdf_set_style(pdf, "section", "ink")
        pdf.set_xy(20, y)
        pdf.cell(0, 8, "Relaciones detectadas", ln=True)
        y += 6
        for rel in informe["relaciones"]:
            pdf_set_style(pdf, "normal", "text")
            pdf.set_xy(20, y)
            pdf.multi_cell(170, 5, limpiar_texto_pdf(f"* {rel['titulo']}"))
            y = pdf.get_y()
            pdf_set_style(pdf, "small", "text_soft")
            pdf.set_xy(25, y)
            pdf.multi_cell(165, 5, limpiar_texto_pdf(rel['detalle']))
            y = pdf.get_y() + 3
        y += 2

    # SECCIÓN: Prioridades sugeridas
    if informe["prioridades"]:
        pdf_set_style(pdf, "section", "ink")
        pdf.set_xy(20, y)
        pdf.cell(0, 8, "Prioridades sugeridas", ln=True)
        y += 6
        for i, p in enumerate(informe["prioridades"], 1):
            pdf_set_style(pdf, "normal", "text")
            pdf.set_xy(20, y)
            pdf.multi_cell(170, 5, limpiar_texto_pdf(f"{i}. {p['titulo']}: {p['accion']}"))
            y = pdf.get_y() + 2

    # SECCIÓN: Mensaje sugerido
    y += 4
    pdf_set_style(pdf, "section", "ink")
    pdf.set_xy(20, y)
    pdf.cell(0, 8, "Mensaje sugerido para enviar", ln=True)
    y += 6
    pdf_set_style(pdf, "normal", "text_soft")
    pdf.set_xy(20, y)
    pdf.multi_cell(170, 5, limpiar_texto_pdf(datos_contacto.get("mensaje_sugerido", "")))

    # --- PIE DE PÁGINA ---
    pdf.set_y(-15)
    pdf.set_draw_color(192, 138, 62)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    try:
        pdf.image(logo_path, x=20, y=pdf.get_y() + 1, w=8)
    except:
        pass
    pdf_set_style(pdf, "small", "slate")
    pdf.set_xy(30, pdf.get_y() + 2)
    pdf.cell(0, 5, "TIVOSCORE · Sistema de Valoracion Operativa", ln=True)
    pdf.set_xy(30, pdf.get_y() + 2)
    pdf.cell(0, 5, "Diagnostico gratuito · Implementacion a medida", ln=True)

    ruta.parent.mkdir(exist_ok=True)
    pdf.output(str(ruta))


def guardar_informe_local(datos_contacto: Dict[str, str], informe: Dict[str, Any], hash_sesion: str) -> Path:
    CARPETA_INFORMES.mkdir(exist_ok=True)
    base = f"{hash_sesion}_{_slug(datos_contacto.get('negocio', ''))}"
    ruta_pdf = CARPETA_INFORMES / f"{base}.pdf"
    ruta_txt = CARPETA_INFORMES / f"{base}.txt"

    generar_pdf_informe(datos_contacto, informe, ruta_pdf)
    ruta_txt.write_text(
        f"Nombre: {datos_contacto.get('nombre','')}\n"
        f"Negocio: {datos_contacto.get('negocio','')}\n"
        f"Contacto: {datos_contacto.get('contacto','')}\n"
        f"Perfil detectado: {informe['perfil_nombre']}\n\n"
        f"Mensaje sugerido:\n{datos_contacto.get('mensaje_sugerido','')}\n",
        encoding="utf-8",
    )
    return ruta_pdf


# ============================================================
# VALIDACIONES
# ============================================================
def validar_email(email: str) -> bool:
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', (email or "").strip()) is not None


def validar_whatsapp(whatsapp: str) -> bool:
    return len(re.sub(r'[^0-9+]', '', (whatsapp or "").strip())) >= 10


def validar_contacto(contacto: str):
    contacto = (contacto or "").strip()
    if validar_email(contacto):
        return True, "email"
    if validar_whatsapp(contacto):
        return True, "whatsapp"
    return False, None


def validar_nombre(nombre: str) -> bool:
    nombre = (nombre or "").strip()
    return len(nombre) >= 2 and not re.match(r'^[0-9\W]+$', nombre)


def validar_negocio(negocio: str) -> bool:
    return len((negocio or "").strip()) >= 2


# ============================================================
# CONEXIÓN A GOOGLE SHEETS
# ============================================================
@st.cache_resource(show_spinner=False)
def get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(show_spinner=False)
def get_worksheet():
    client = get_client()
    sheet_id = st.secrets["autodiagnostico_sheet_id"]
    spreadsheet = client.open_by_key(sheet_id)
    try:
        ws = spreadsheet.worksheet(SHEET_TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SHEET_TAB_NAME, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)
    if not ws.get_all_values():
        ws.append_row(HEADERS)
    return ws


def guardar_respuesta(fila: list):
    ws = get_worksheet()
    ws.append_row(fila, value_input_option="USER_ENTERED")


def obtener_hash_sesion(negocio: str) -> str:
    seed = f"{negocio}_{dt.datetime.now().isoformat()}"
    return hashlib.md5(seed.encode()).hexdigest()[:8]


# ============================================================
# ESTILO UNIFICADO CON LANDING
# ============================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@500;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">

<style>
:root {
    --ink: #16233A;
    --slate: #3D5470;
    --paper: #F6F3EC;
    --paper-alt: #EDE8DB;
    --amber: #C08A3E;
    --amber-dark: #9C6F2E;
    --green: #4B7A5B;
    --brick: #A6473A;
    --text: #1C1F26;
    --text-soft: #5B6472;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

h1, h2, h3, .display {
    font-family: 'Roboto Slab', serif !important;
}

.block-container {
    max-width: 720px;
    padding-top: 2rem;
}

/* --- Hero --- */
.hero {
    background: var(--ink);
    border-radius: 14px;
    padding: 2.5rem 2.5rem 2.5rem 2.5rem;
    margin-bottom: 2.5rem;
}
.hero .eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--amber);
    margin-bottom: 0.5rem;
}
.hero h1 {
    color: #F6F3EC;
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1.25;
    margin: 0 0 0.6rem 0;
}
.hero h1 .highlight { color: var(--amber); }
.hero p {
    color: #C7CFDA;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.55;
    margin: 0;
}

/* --- Secciones --- */
.section-title {
    font-family: 'Roboto Slab', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--ink);
    margin: 1.8rem 0 0.8rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #E8ECF0;
}
.sub-label {
    font-size: 0.85rem;
    color: var(--text-soft);
    margin-top: -0.3rem;
    margin-bottom: 0.8rem;
}

/* --- Botones --- */
div.stButton > button {
    background: var(--amber) !important;
    color: #1C1F26 !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.7rem 1.8rem !important;
    font-size: 1rem !important;
}
div.stButton > button:hover {
    background: var(--amber-dark) !important;
    color: #F6F3EC !important;
}

.stRadio > div {
    gap: 0.5rem;
}
.stRadio label {
    font-size: 0.9rem;
}
.stCheckbox label {
    font-size: 0.95rem;
}
.stSelectbox label {
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="hero">
    <div class="eyebrow">TIVOSCORE · Autodiagnóstico Operativo</div>
    <h1>Respondé estas preguntas con <span class="highlight">honestidad</span></h1>
    <p>
        No hay respuestas correctas ni incorrectas. El objetivo es entender
        dónde está tu principal oportunidad de mejora y qué tan dependiente
        eres de la operación diaria.
        <br><br>
        <strong>Te toma menos de 5 minutos.</strong>
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# VERIFICAR SI YA ENVIÓ
# ============================================================
if 'autodiagnostico_enviado' not in st.session_state:
    st.session_state.autodiagnostico_enviado = False

if st.session_state.autodiagnostico_enviado:
    st.markdown("""
    <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 20px 25px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #155724; margin: 0 0 8px 0;">¡Gracias, ya recibimos tus respuestas!</h3>
        <p style="color: #155724; margin: 0;">En las próximas horas te escribimos con tu diagnóstico completo.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ============================================================
# FORMULARIO
# ============================================================
with st.form("autodiagnostico"):
    # BLOQUE 0: Contexto mínimo
    st.markdown('<div class="section-title">Sobre vos y tu negocio</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Tu nombre", placeholder="Ej: Juan Pérez")
        negocio = st.text_input("Nombre del negocio", placeholder="Ej: Mi Academia Online")
    with col2:
        tipo_negocio = st.selectbox("Tipo de negocio", TIPOS_NEGOCIO)
        contacto = st.text_input("WhatsApp o email de contacto", placeholder="ej: +58 412 1234567")
    canal = st.selectbox("¿Cómo nos conociste?", CANALES)

    # BLOQUE 1: Punto ciego
    st.markdown('<div class="section-title">Punto ciego operativo</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-label">Respondé con honestidad para identificar tu área de mejora principal.</p>', unsafe_allow_html=True)
    respuestas_punto_ciego = {}
    for cat_key, cat_data in CATEGORIAS.items():
        st.markdown(f'<p style="font-family: Roboto Slab, serif; font-weight: 500; margin: 1rem 0 0.2rem 0;">{cat_data["nombre"]}</p>', unsafe_allow_html=True)
        valores = []
        for i, pregunta in enumerate(cat_data["preguntas"]):
            resp = st.radio(pregunta, list(OPCIONES_ESCALA.keys()), index=2, horizontal=True, key=f"pc_{cat_key}_{i}")
            valores.append(OPCIONES_ESCALA[resp])
        respuestas_punto_ciego[cat_key] = valores

    # BLOQUE 2: Dependencia del dueño (ACTUALIZADO)
    st.markdown('<div class="section-title">Dependencia del dueño</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-label">Estas preguntas miden cuánto dependés de tu intervención diaria.</p>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        intervenciones_semanales = st.selectbox(
            "¿Cuántas veces interviniste en incidencias en las últimas 4 semanas?",
            ["Ninguna", "1-2 veces", "3-5 veces", "Más de 5 veces"],
        )
        percepcion_control = st.select_slider("¿Qué tan controlada sientes la operación?", options=[1, 2, 3, 4, 5], value=3)
        costo_hora = st.number_input(
            "¿Cuánto estimás que cuesta tu hora de trabajo? (en tu moneda local)",
            min_value=0,
            value=0,
            step=5,
            help="Pensá en lo que facturarías si estuvieras haciendo ventas o cerrando negocios, no en lo que gastas."
        )
    with col4:
        resolucion_incidencias = st.selectbox(
            "Cuando surge una incidencia, normalmente:",
            ["Las resuelve el equipo", "Las resuelvo yo, pero el equipo también participa", "Las resuelvo yo mismo"],
        )
        percepcion_dependencia = st.select_slider("¿Qué tan dependiente sos de tu intervención diaria?", options=[1, 2, 3, 4, 5], value=3)
        tiempo_administrativo = st.slider(
            "¿Qué porcentaje de tu tiempo laboral dedicas a tareas administrativas u operativas?",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="Ej: revisar correos, facturas, coordinar entregas, resolver incidencias. El resto debería ser hacer negocio (vender, crear, estrategia)."
        )

    # BLOQUE 3: Visibilidad y registro
    st.markdown('<div class="section-title">Visibilidad y registro</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-label">Estas preguntas miden tu visibilidad operativa.</p>', unsafe_allow_html=True)
    puede_saber = st.multiselect(
        "¿Podés saber esto en menos de 5 minutos, sin preguntar a nadie?",
        ["Clientes activos", "Pagos pendientes", "Entregas/pedidos realizados", "Incidencias abiertas"],
    )
    registro_informacion = st.radio(
        "¿Dónde se registra la información clave del negocio?",
        ["En un sistema centralizado", "En diferentes lugares (Excel, WhatsApp, papel)", "No tengo un registro claro"],
    )

    # BLOQUE 4: Estabilidad operativa
    st.markdown('<div class="section-title">Estabilidad operativa</div>', unsafe_allow_html=True)
    problemas_repetitivos = st.radio("¿Existen problemas que se repiten cada semana?", ["Sí", "No"])
    solucion_problemas = "No aplica"
    if problemas_repetitivos == "Sí":
        solucion_problemas = st.radio(
            "Cuando un problema se repite:",
            ["Se soluciona de manera definitiva", "Se vuelve a resolver de la misma manera", "No se le da solución"],
        )

    acepta = st.checkbox(
        "Confirmo que el contacto es correcto y acepto recibir el resultado de mi diagnóstico",
        help="No compartimos tus datos con terceros. Podés darte de baja en cualquier momento."
    )

    enviado = st.form_submit_button("Ver mi resultado →", use_container_width=True)


# ============================================================
# PROCESAMIENTO DEL ENVÍO
# ============================================================
if enviado:
    errores = []
    if not validar_nombre(nombre):
        errores.append("Ingresá tu nombre (mínimo 2 caracteres).")
    if not validar_negocio(negocio):
        errores.append("Ingresá el nombre de tu negocio.")
    valido_contacto, _ = validar_contacto(contacto)
    if not valido_contacto:
        errores.append("Ingresá un email o WhatsApp válido (con código de país).")
    if not acepta:
        errores.append("Debés confirmar el checkbox para continuar.")

    if errores:
        for e in errores:
            st.warning(e)
        st.stop()

    respuestas = {
        "punto_ciego": respuestas_punto_ciego,
        "puede_saber": puede_saber,
        "registro_informacion": registro_informacion,
        "intervenciones_semanales": intervenciones_semanales,
        "resolucion_incidencias": resolucion_incidencias,
        "percepcion_control": percepcion_control,
        "percepcion_dependencia": percepcion_dependencia,
        "problemas_repetitivos": problemas_repetitivos,
        "solucion_problemas": solucion_problemas,
        "costo_hora": costo_hora,
        "tiempo_administrativo": tiempo_administrativo,
    }

    informe = generar_informe(respuestas)
    m = informe["metricas"]

    mensaje_sugerido = obtener_mensaje(
        perfil=informe["perfil_key"] or "procesos",
        nombre=nombre,
        nivel_dependencia=informe["nivel_dependencia"],
        tiempo_administrativo=m["tiempo_administrativo"],
        costo_admin_mes=m["costo_admin_mes"],
    )

    hash_sesion = obtener_hash_sesion(negocio)

    datos_contacto = {
        "nombre": nombre, "negocio": negocio, "tipo_negocio": tipo_negocio,
        "contacto": contacto, "canal": canal, "mensaje_sugerido": mensaje_sugerido,
    }

    fila = [
        dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
        nombre, negocio, tipo_negocio, contacto, canal,
        informe["perfil_nombre"], informe["puntaje_perfil"],
        m["madurez"], m["dependencia"], m["visibilidad"], m["delegacion"], m["estabilidad"], m["brecha_percepcion"],
        m["costo_hora"], m["tiempo_administrativo"], m["horas_admin_semana"], m["costo_admin_mes"],
        mensaje_sugerido, hash_sesion,
    ]

    try:
        guardar_respuesta(fila)
        guardar_informe_local(datos_contacto, informe, hash_sesion)

        st.markdown(f"""
        <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 20px 25px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #155724; margin: 0 0 8px 0;">¡Gracias, {nombre.split()[0]}!</h3>
            <p style="color: #155724; margin: 0;">{informe['resumen_dos_lineas']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.balloons()

    except Exception as e:
        st.error("No se pudo guardar tu respuesta. Intentá de nuevo en unos minutos.")
        st.exception(e)


# ============================================================
# PANEL INTERNO
# ============================================================
with st.sidebar:
    st.markdown("### :material/lock: Panel interno")
    clave = st.text_input("Contraseña", type="password", key="clave_admin")
    if clave and clave == st.secrets.get("admin_password", ""):
        st.success("Acceso concedido")
        if CARPETA_INFORMES.exists():
            archivos_pdf = sorted(CARPETA_INFORMES.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not archivos_pdf:
                st.caption("Todavía no hay informes generados.")
            for pdf_path in archivos_pdf[:20]:
                txt_path = pdf_path.with_suffix(".txt")
                titulo = pdf_path.stem
                with st.expander(titulo):
                    if txt_path.exists():
                        st.text(txt_path.read_text(encoding="utf-8"))
                    st.download_button(
                        "Descargar PDF", data=pdf_path.read_bytes(),
                        file_name=pdf_path.name, mime="application/pdf",
                        key=f"dl_{pdf_path.name}",
                    )
        else:
            st.caption("Todavía no hay informes generados.")
    elif clave:
        st.error("Contraseña incorrecta.")