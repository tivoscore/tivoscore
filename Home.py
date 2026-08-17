import streamlit as st
from PIL import Image

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
icono = Image.open("favicon.png")
st.set_page_config(
    page_title="TivoScore — Sistema de Control Operativo",
    page_icon=icono,
    layout="centered",
)

# ============================================================
# ESTILOS GLOBALES
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
    padding-top: 2rem;
    max-width: 760px;
}

/* --- HERO --- */
.hero {
    background: var(--ink);
    border-radius: 14px;
    padding: 3rem 2.5rem 2.5rem 2.5rem;
    margin-bottom: 2.5rem;
}
.hero .eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--amber);
    margin-bottom: 0.9rem;
}
.hero h1 {
    color: #F6F3EC;
    font-size: 2.15rem;
    font-weight: 700;
    line-height: 1.25;
    margin: 0 0 0.9rem 0;
}
.hero h1 .highlight { color: var(--amber); }
.hero p.sub {
    color: #C7CFDA;
    font-size: 1.05rem;
    font-weight: 400;
    line-height: 1.55;
    max-width: 48ch;
    margin: 0 0 0.5rem 0;
}

/* --- score display --- */
.score-display {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: #1A2840;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin-top: 1.4rem;
    border: 1px solid #33456A;
}
.score-display .number {
    font-family: 'Roboto Slab', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--amber);
    line-height: 1;
}
.score-display .label { color: #9AA7B8; font-size: 0.82rem; font-family: 'Inter', sans-serif; }
.score-display .desc { color: #C7CFDA; font-size: 0.9rem; font-family: 'Inter', sans-serif; }
.score-note {
    font-family: 'Inter', sans-serif;
    font-size: 0.76rem;
    color: #7C8AA0;
    margin-top: 0.6rem;
}

/* --- panel preview --- */
.panel-preview {
    margin-top: 1.6rem;
    background: #1E2E48;
    border: 1px solid #33456A;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
}
.panel-preview .row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.55rem 0;
    border-bottom: 1px solid #2A3A57;
    font-family: 'IBM Plex Mono', monospace;
}
.panel-preview .row:last-child { border-bottom: none; }
.panel-preview .label { color: #9AA7B8; font-size: 0.82rem; }
.panel-preview .value { color: #F6F3EC; font-size: 1rem; font-weight: 500; }
.panel-preview .value.warn { color: #E0A458; }
.panel-preview .value.good { color: #7BC47F; }
.panel-preview .caption {
    margin-top: 0.9rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.76rem;
    color: #7C8AA0;
}

/* --- ledger --- */
.ledger {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
    border: 1px solid #DDD6C4;
    border-radius: 10px;
    overflow: hidden;
    margin: 1.6rem 0 2.4rem 0;
}
.ledger .col { padding: 1.4rem 1.5rem; }
.ledger .col.hoy { background: var(--paper-alt); border-right: 1px solid #DDD6C4; }
.ledger .col.con { background: #EFF3EE; }
.ledger h4 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.9rem 0;
}
.ledger .col.hoy h4 { color: var(--brick); }
.ledger .col.con h4 { color: var(--green); }
.ledger ul { margin: 0; padding-left: 1.1rem; }
.ledger li { margin-bottom: 0.55rem; font-size: 0.94rem; line-height: 1.4; color: var(--text); }

/* --- pasos --- */
.step { display: flex; gap: 1rem; padding: 1.1rem 0; border-bottom: 1px solid #E4DFD0; }
.step:last-child { border-bottom: none; }
.step .num {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--amber-dark);
    font-weight: 500;
    font-size: 0.95rem;
    min-width: 1.6rem;
}
.step h5 { margin: 0 0 0.25rem 0; font-size: 1rem; font-weight: 600; }
.step p { margin: 0; font-size: 0.92rem; color: var(--text-soft); line-height: 1.5; }

/* --- piloto --- */
.piloto-box {
    background: var(--paper-alt);
    border-left: 3px solid var(--amber);
    border-radius: 6px;
    padding: 1.2rem 1.4rem;
    margin: 1.5rem 0 2.5rem 0;
}
.piloto-box p { margin: 0; font-size: 0.94rem; color: var(--text); line-height: 1.55; }
.piloto-box ul { margin: 0.5rem 0 0 0; padding-left: 1.2rem; font-size: 0.92rem; color: var(--text-soft); }
.piloto-box ul li { margin-bottom: 0.3rem; }

/* --- cta --- */
.cta-final {
    background: var(--ink);
    border-radius: 14px;
    padding: 2.4rem 2rem;
    text-align: center;
    margin: 1rem 0 2rem 0;
}
.cta-final h3 { color: #F6F3EC; margin: 0 0 0.5rem 0; font-size: 1.5rem; }
.cta-final p { color: #B9C2D0; font-size: 0.94rem; margin: 0 0 0.8rem 0; }

.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--slate);
    margin: 0 0 0.6rem 0;
}

/* --- botones --- */
div.stButton > button {
    background: var(--amber) !important;
    color: #1C1F26 !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.7rem 1.8rem !important;
    font-size: 1rem !important;
}
div.stButton > button:hover { background: var(--amber-dark) !important; color: #F6F3EC !important; }

/* --- beneficios --- */
.benefits-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin: 0.5rem 0 2rem 0;
}
.benefits-grid .benefit {
    background: var(--paper-alt);
    border-radius: 8px;
    padding: 1.1rem 1.2rem;
    text-align: center;
}
.benefits-grid .benefit svg { color: var(--slate); }
.benefits-grid .benefit h6 {
    margin: 0.5rem 0 0 0;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
}
.benefits-grid .benefit p {
    margin: 0.2rem 0 0 0;
    font-size: 0.78rem;
    color: var(--text-soft);
}

@media (max-width: 600px) {
    .benefits-grid { grid-template-columns: 1fr; }
    .ledger { grid-template-columns: 1fr; }
    .ledger .col.hoy { border-right: none; border-bottom: 1px solid #DDD6C4; }
    .score-display { flex-direction: column; text-align: center; gap: 0.3rem; }
    .hero h1 { font-size: 1.5rem; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================
st.markdown("""
<div class="hero">
    <div class="eyebrow">TivoScore · Sistema de Control Operativo</div>
    <h1>¿Qué tan controlado está <span class="highlight">tu negocio</span>?</h1>
    <p class="sub">
        Descúbrelo en 2 minutos. Respondes unas preguntas sobre cómo manejas
        hoy tus ventas, cobros y operación, y te devolvemos tu
        <strong>TivoScore (0-100)</strong> — un número que resume qué tan bajo
        control está tu negocio hoy.
    </p>
    <div class="score-display">
        <div>
            <span class="number">78</span>
            <span class="label">/ 100</span>
        </div>
        <div>
            <div class="label">TivoScore · Nivel de control</div>
            <div class="desc">Ejemplo ilustrativo — así se ve tu resultado</div>
        </div>
    </div>
    <p class="score-note">Tu TivoScore lo ves apenas terminas el formulario. El diagnóstico completo, con lo que significa y qué hacer al respecto, te lo enviamos personalmente en las próximas horas.</p>
    <p style="font-family:'IBM Plex Mono',monospace; font-size:0.76rem; letter-spacing:0.06em; text-transform:uppercase; color:#9AA7B8; margin: 1.8rem 0 0.6rem 0;">Así se vería tu panel una vez implementado</p>
    <div class="panel-preview">
        <div class="row"><span class="label">VENTAS DE HOY</span><span class="value">$1,240.00</span></div>
        <div class="row"><span class="label">COBRADO HOY</span><span class="value">$860.00</span></div>
        <div class="row"><span class="label">SALDO PENDIENTE TOTAL</span><span class="value warn">$2,915.00</span></div>
        <div class="row"><span class="label">CLIENTES EN MORA</span><span class="value warn">3</span></div>
        <div class="row"><span class="label">TIVOSCORE ACTUAL</span><span class="value good">78</span></div>
        <div class="caption">Ejemplo ilustrativo, construido sobre tu propia hoja de cálculo.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# EL PROBLEMA
# ============================================================
st.markdown("""
<div style="margin-bottom: 1.6rem;">
    <p style="font-size: 1.02rem; line-height: 1.65; color: var(--text); margin-bottom: 0.9rem;">
        Tu negocio genera información todos los días. El problema no es que no
        tengas datos — es que están dispersos, y no hay una sola cifra que te
        diga, de un vistazo, qué tan controlado está todo.
    </p>
    <p style="font-size: 1.02rem; line-height: 1.65; color: var(--text); margin-bottom: 1.3rem;">
        Tu TivoScore combina varias señales de tu operación en un solo número,
        para que sepas rápido si vas bien o si algo necesita tu atención —
        y en qué área exactamente.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# BENEFICIOS (iconos SVG)
# ============================================================
ICON_SCORE = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10"></path><path d="M18 20V4"></path><path d="M6 20v-4"></path></svg>'
ICON_PANEL = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M3 9h18"></path><path d="M9 21V9"></path></svg>'
ICON_TARGET = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><circle cx="12" cy="12" r="5"></circle><circle cx="12" cy="12" r="1"></circle></svg>'

st.markdown(f"""
<div class="benefits-grid">
    <div class="benefit">
        {ICON_SCORE}
        <h6>Un número, no una lista</h6>
        <p>Tu TivoScore resume tu situación real — no otro tablero con 20 indicadores sueltos.</p>
    </div>
    <div class="benefit">
        {ICON_PANEL}
        <h6>Panel a tu medida</h6>
        <p>Si decides avanzar, tu panel se conecta a tu propia hoja de cálculo.</p>
    </div>
    <div class="benefit">
        {ICON_TARGET}
        <h6>Sabes por dónde empezar</h6>
        <p>El diagnóstico señala tu punto más urgente, no todo a la vez.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PROBLEMA / SOLUCIÓN
# ============================================================
st.markdown('<p class="section-label">La situación</p>', unsafe_allow_html=True)
st.markdown("""
<div class="ledger">
    <div class="col hoy">
        <h4>Hoy</h4>
        <ul>
            <li>Ventas repartidas entre WhatsApp, mostrador y encargos.</li>
            <li>Nadie sabe con certeza cuánto le deben en total los clientes.</li>
            <li>Los cobros se anotan en varios lugares distintos, o en ninguno.</li>
            <li>Revisar "cómo va el mes" toma horas de buscar y sumar a mano.</li>
        </ul>
    </div>
    <div class="col con">
        <h4>Con tu TivoScore</h4>
        <ul>
            <li>Un número (0-100) que resume tu nivel de control real.</li>
            <li>Un diagnóstico que identifica tu punto más urgente.</li>
            <li>Una recomendación clara de por dónde empezar.</li>
            <li>Si decides avanzar, implementamos tu panel a la medida.</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# QUIÉN ESTÁ DETRÁS (VERSIÓN CORREGIDA SIN AVATAR_B64)
# ============================================================
st.markdown('<p class="section-label">Quién está detrás de TivoScore</p>', unsafe_allow_html=True)

st.markdown("""
<div style="display: flex; gap: 1.5rem; align-items: flex-start; margin-bottom: 2.4rem; background: var(--paper-alt); border-radius: 10px; padding: 1.4rem 1.6rem;">
    <div style="width: 64px; height: 64px; border-radius: 50%; background: #D9D2BE; flex-shrink: 0; display:flex; align-items:center; justify-content:center; font-family:'Roboto Slab',serif; font-size:1.1rem; color:#5B6472; overflow:hidden;">
        [Foto]
    </div>
    <div>
        <p style="margin:0 0 0.3rem 0; font-weight:600; font-size:1rem; color:var(--text);">[Tu nombre]</p>
        <p style="margin:0; font-size:0.9rem; color:var(--text-soft); line-height:1.55;">
            [Una frase corta y real sobre tu experiencia]. Detrás de TivoScore
            no hay un equipo de ventas — soy yo quien revisa cada diagnóstico
            y responde personalmente.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CÓMO FUNCIONA
# ============================================================
st.markdown('<p class="section-label">Cómo funciona</p>', unsafe_allow_html=True)
st.markdown("""
<div>
    <div class="step">
        <span class="num">01</span>
        <div>
            <h5>Responde el formulario (2 minutos)</h5>
            <p>Preguntas concretas sobre cómo manejas hoy tus ventas, cobros y operación.</p>
        </div>
    </div>
    <div class="step">
        <span class="num">02</span>
        <div>
            <h5>Ve tu TivoScore al instante</h5>
            <p>Un número (0-100) que resume tu nivel de control actual — sin explicación todavía, solo el punto de partida.</p>
        </div>
    </div>
    <div class="step">
        <span class="num">03</span>
        <div>
            <h5>Recibe tu diagnóstico completo (en las próximas horas)</h5>
            <p>Te escribimos personalmente con lo que significa tu resultado, tu punto más urgente, y una recomendación concreta.</p>
        </div>
    </div>
    <div class="step">
        <span class="num">04</span>
        <div>
            <h5>Si decides avanzar, implementamos tu panel</h5>
            <p>Un panel a la medida, conectado a tu propia hoja de cálculo — solo si tú decides que vale la pena dar ese paso.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# BOTÓN PRIMARIO
# ============================================================
st.write("")
col_a, col_b, col_c = st.columns([1, 2, 1])
with col_b:
    st.button("Descubre tu TivoScore gratis →", use_container_width=True, icon=":material/monitoring:")

# ============================================================
# PILOTO
# ============================================================
st.markdown('<p class="section-label">Sobre este programa</p>', unsafe_allow_html=True)
st.markdown("""
<div class="piloto-box">
    <p><strong>Estamos seleccionando un grupo pequeño de negocios</strong> para la primera fase de validación.</p>
    <ul>
        <li>Recibes tu TivoScore y tu diagnóstico personalizado, sin costo.</li>
        <li>Tu experiencia ayuda a definir cómo evoluciona el sistema.</li>
        <li>Accedes a condiciones preferenciales por ser parte de los primeros.</li>
    </ul>
    <p style="margin-top:0.5rem; font-size:0.9rem; color:var(--text-soft);">
        El diagnóstico es gratuito. La implementación del panel solo se hace si decides avanzar.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CTA FINAL
# ============================================================
st.markdown("""
<div class="cta-final">
    <h3>¿Cuál es tu TivoScore?</h3>
    <p>Descúbrelo en 2 minutos. En las próximas horas te escribimos con tu diagnóstico completo — sin compromiso de implementación.</p>
</div>
""", unsafe_allow_html=True)

col_a2, col_b2, col_c2 = st.columns([1, 2, 1])
with col_b2:
    st.button("Descubre tu TivoScore gratis →", use_container_width=True, key="cta2", icon=":material/monitoring:")

# ============================================================
# PIE DE PÁGINA
# ============================================================
st.markdown("""
<div style="text-align:center; margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid #E4DFD0;">
    <p style="font-size: 0.85rem; color: var(--text-soft); margin: 0 0 0.4rem 0;">
        <a href="https://www.linkedin.com/in/tu-usuario" target="_blank" style="color: var(--slate); text-decoration:none;">LinkedIn</a>
        &nbsp;·&nbsp;
        <a href="mailto:info@tivoscore.com" style="color: var(--slate); text-decoration:none;">info@tivoscore.com</a>
    </p>
    <p style="font-size: 0.78rem; color: #9AA7B8; margin:0;">TivoScore · Sistema de Control Operativo</p>
    <p style="font-size: 0.7rem; color: #B0B8C4; margin: 0.2rem 0 0 0;">Diagnóstico gratuito · Implementación a la medida sobre tu propia hoja de cálculo</p>
</div>
""", unsafe_allow_html=True)