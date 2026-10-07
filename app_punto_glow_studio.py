"""
Punto Glow Beauty Management Studio - Aplicación Principal
Sistema integral de gestión con hora sincronizada a CDMX (America/Mexico_City).
Incluye sesión persistente diaria, conversión directa de Citas a Ventas,
registro de ventas basado únicamente en fecha, gestión exclusiva de usuarios y
links ultra-cortos garantizados (is.gd) de Google Calendar para WhatsApp.
"""
import io
import os
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# Zona horaria oficial Ciudad de México
TZ_CDMX = ZoneInfo("America/Mexico_City")

# -----------------------------------------------------------------------------
# RUTAS ABSOLUTAS FIJAS A LA CARPETA LOCAL (PREVIENE PÉRDIDA DE ARCHIVOS)
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_USUARIOS = os.path.join(BASE_DIR, "usuarios_punto_glow.csv")
FILE_SESION = os.path.join(BASE_DIR, "sesion_punto_glow.json")
FILE_VENTAS = os.path.join(BASE_DIR, "ventas_punto_glow.csv")
FILE_GASTOS = os.path.join(BASE_DIR, "gastos_punto_glow.csv")
FILE_CITAS = os.path.join(BASE_DIR, "citas_punto_glow.csv")

CORREO_ADMIN_UNICO = "garcialarissa1292@gmail.com"

def obtener_ahora_cdmx() -> datetime:
    """Retorna la fecha y hora actual en la zona horaria de Ciudad de México."""
    return datetime.now(TZ_CDMX)

def calcular_hora_fin(hora_str: str, min_duracion: int) -> str:
    """Calcula la hora de término a partir de una hora en formato '10:00 am' y los minutos de duración."""
    try:
        dt = datetime.strptime(hora_str, "%I:%M %p")
        dt_fin = dt + timedelta(minutes=min_duracion)
        return dt_fin.strftime("%I:%M %p").lower()
    except Exception:
        return hora_str

def acortar_url_isgd(url_larga: str) -> str:
    """
    Acorta un enlace largo utilizando la API ultra-rápida y directa de is.gd.
    Si falla por falta de internet, reintenta con TinyURL o regresa el enlace original.
    """
    try:
        api_isgd = f"https://is.gd/create.php?format=simple&url={urllib.parse.quote(url_larga)}"
        req = urllib.request.Request(api_isgd, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            res_text = response.read().decode('utf-8').strip()
            if res_text.startswith("http"):
                return res_text
    except Exception:
        pass
        
    # Respaldo rápido con TinyURL
    try:
        api_tiny = f"http://tinyurl.com/api-create.php?url={urllib.parse.quote(url_larga)}"
        req_tiny = urllib.request.Request(api_tiny, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_tiny, timeout=3) as response:
            return response.read().decode('utf-8').strip()
    except Exception:
        return url_larga

def generar_link_gcal(fecha_str: str, hora_rango: str, servicio: str, cliente: str) -> str:
    """
    Genera un enlace público ultra-corto de Google Calendar con la fecha, hora inicio, hora fin,
    título del servicio y detalles de la cita en Punto Glow.
    """
    try:
        partes = hora_rango.lower().replace("de ", "").split(" a ")
        h_ini_str = partes[0].strip()
        h_fin_str = partes[1].strip() if len(partes) > 1 else h_ini_str
        
        dt_ini = datetime.strptime(f"{fecha_str} {h_ini_str}", "%Y-%m-%d %I:%M %p")
        dt_fin = datetime.strptime(f"{fecha_str} {h_fin_str}", "%Y-%m-%d %I:%M %p")
        
        fmt_gcal = "%Y%m%dT%H%M%S"
        dates_param = f"{dt_ini.strftime(fmt_gcal)}/{dt_fin.strftime(fmt_gcal)}"
        
        titulo = urllib.parse.quote(f"Cita Punto Glow: {servicio}")
        detalles = urllib.parse.quote(f"Cita agendada para {cliente} en Punto Glow Beauty Studio ✨. Servicio: {servicio}.")
        ubicacion = urllib.parse.quote("Punto Glow Beauty Studio")
        
        link_largo = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={titulo}&dates={dates_param}&details={detalles}&location={ubicacion}&ctz=America/Mexico_City"
        
        # Acortar enlace inmediatamente con is.gd
        return acortar_url_isgd(link_largo)
    except Exception:
        return "https://calendar.google.com"

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (#F089AB / #000000)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Punto Glow Beauty Management Studio",
    layout="wide",
    page_icon="✨",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&family=Great+Vibes&family=Josefin+Sans:wght@300;400;600;700&display=swap');
    .stApp {
        background-color: #FDF4F7;
        font-family: 'Josefin Sans', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #FCE4EC !important;
    }
    .brand-glow-title {
        font-family: 'Great Vibes', cursive;
        font-size: 2.8rem;
        text-align: center;
        line-height: 1.1;
        color: #000000;
    }
    .brand-glow-title span {
        font-family: 'Bodoni Moda', serif;
        color: #F089AB;
        font-weight: bold;
    }
    .brand-glow-sub {
        font-family: 'Josefin Sans', sans-serif;
        font-size: 0.75rem;
        letter-spacing: 4px;
        text-align: center;
        font-weight: 700;
        color: #333333;
        margin-top: 2px;
    }
    .top-banner {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 16px 30px;
        box-shadow: 0 4px 15px rgba(240, 137, 171, 0.05);
        margin-bottom: 25px;
    }
    .top-title {
        font-family: 'Bodoni Moda', serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #000000;
        margin: 0;
    }
    .top-title span { color: #F089AB; }
    .top-sub { color: #888888; font-size: 0.95rem; margin-top: 2px; }
    .clock-badge {
        background-color: #FDF0F5;
        color: #F089AB;
        padding: 8px 18px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        text-align: center;
    }
    .section-title {
        font-family: 'Bodoni Moda', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #000000;
        margin: 0;
    }
    .section-sub {
        color: #888888;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    div[data-testid="stSidebar"] div.stButton > button[key="btn_reg_v_img"],
    div[data-testid="stSidebar"] div.stButton > button[key="btn_agen_c_img"],
    div[data-testid="stSidebar"] div.stButton > button[key="btn_reg_g_img"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 25px !important;
        padding: 12px 20px !important;
        font-family: 'Josefin Sans', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 10px !important;
        width: 100% !important;
        transition: all 0.3s ease-in-out !important;
    }
    div[data-testid="stSidebar"] div.stButton > button[key="btn_reg_v_img"]:hover,
    div[data-testid="stSidebar"] div.stButton > button[key="btn_agen_c_img"]:hover,
    div[data-testid="stSidebar"] div.stButton > button[key="btn_reg_g_img"]:hover {
        background-color: #111111 !important;
        color: #F089AB !important;
        border-color: #F089AB !important;
        box-shadow: 0 6px 20px rgba(240, 137, 171, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    div.stButton > button[key="btn_nueva_venta_header"] {
        background: linear-gradient(135deg, #F089AB 0%, #D8688D 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 24px !important;
        font-family: 'Josefin Sans', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(240, 137, 171, 0.4) !important;
    }
    .table-container-card {
        background-color: #FFFFFF;
        border-radius: 24px;
        padding: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    .card-metric {
        background: #FFFFFF;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .card-metric-black {
        background: #0B0E14;
        color: white;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .metric-val { font-size: 2.2rem; font-weight: 700; color: #000000; margin: 6px 0; }
    .metric-val-black { font-size: 2.2rem; font-weight: 700; color: #FFFFFF; margin: 6px 0; }
    .service-badge {
        background-color: #FDF0F5;
        color: #F089AB;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-confirmada { background-color: #E8F8F5; color: #2ECC71; padding: 4px 12px; border-radius: 12px; font-weight:700; }
    .status-cancelada { background-color: #FDEDEC; color: #E74C3C; padding: 4px 12px; border-radius: 12px; font-weight:700; }
    .monto-green { color: #2ECC71; font-weight: 700; }
    .monto-red { color: #E74C3C; font-weight: 700; }
    .btn-wa-pill {
        display: inline-block;
        background-color: #25D366;
        color: white !important;
        padding: 8px 16px;
        border-radius: 20px;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.88rem;
        box-shadow: 0 3px 10px rgba(37, 211, 102, 0.3);
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .login-box {
        background-color: #FFFFFF;
        border-radius: 24px;
        padding: 35px;
        max-width: 480px;
        margin: 30px auto;
        box-shadow: 0 10px 30px rgba(240, 137, 171, 0.15);
        border: 1px solid #FCE4EC;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. AUTENTICACIÓN Y PERSISTENCIA DE SESIÓN DIARIA
# -----------------------------------------------------------------------------
def sanitizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.index.has_duplicates:
        df = df.reset_index(drop=True)
    if df.columns.has_duplicates:
        df = df.loc[:, ~df.columns.duplicated()].copy()
    return df

def obtener_dataframe_usuarios() -> pd.DataFrame:
    cols_requeridas = ["Nombre", "Correo", "Password", "Rol"]
    if not os.path.exists(FILE_USUARIOS) or os.path.getsize(FILE_USUARIOS) == 0:
        df_usr = pd.DataFrame([{
            "Nombre": "Larissa García (Administradora Principal)",
            "Correo": CORREO_ADMIN_UNICO,
            "Password": "admin",
            "Rol": "Admin"
        }])
        df_usr.to_csv(FILE_USUARIOS, index=False)
        return df_usr
    try:
        df_usr = pd.read_csv(FILE_USUARIOS)
        df_usr = sanitizar_dataframe(df_usr)
        if "Rol" not in df_usr.columns:
            df_usr["Rol"] = df_usr["Correo"].apply(
                lambda c: "Admin" if str(c).strip().lower() == CORREO_ADMIN_UNICO else "Especialista"
            )
        for c in cols_requeridas:
            if c not in df_usr.columns:
                df_usr[c] = ""
        df_usr = df_usr[cols_requeridas]
        return df_usr
    except Exception:
        df_usr = pd.DataFrame([{
            "Nombre": "Larissa García (Administradora Principal)",
            "Correo": CORREO_ADMIN_UNICO,
            "Password": "admin",
            "Rol": "Admin"
        }])
        df_usr.to_csv(FILE_USUARIOS, index=False)
        return df_usr

# --- FUNCIONES DE GUARDADO / CARGA DE SESIÓN ---
def guardar_sesion_local(correo: str, nombre: str, es_admin: bool):
    """Guarda los datos de inicio de sesión junto con la fecha del día en un archivo JSON."""
    datos_sesion = {
        "fecha": str(obtener_ahora_cdmx().date()),
        "correo": correo,
        "usuario_actual": f"{nombre} ({correo})",
        "es_admin": es_admin
    }
    with open(FILE_SESION, "w", encoding="utf-8") as f:
        json.dump(datos_sesion, f, ensure_ascii=False, indent=2)

def borrar_sesion_local():
    """Elimina el archivo de sesión cuando se presiona 'Cerrar Sesión'."""
    if os.path.exists(FILE_SESION):
        os.remove(FILE_SESION)

def verificar_y_cargar_sesion():
    """Valida si existe una sesión previa guardada en el día de hoy."""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"] and os.path.exists(FILE_SESION):
        try:
            with open(FILE_SESION, "r", encoding="utf-8") as f:
                datos = json.load(f)
            fecha_hoy_str = str(obtener_ahora_cdmx().date())
            if datos.get("fecha") == fecha_hoy_str:
                st.session_state["autenticado"] = True
                st.session_state["usuario_actual"] = datos.get("usuario_actual", "")
                st.session_state["es_admin"] = datos.get("es_admin", False)
            else:
                borrar_sesion_local()
        except Exception:
            borrar_sesion_local()

obtener_dataframe_usuarios()
verificar_y_cargar_sesion()

def requerir_login():
    st.markdown("""
    <div class="login-box">
        <div class="brand-glow-title">punto<span>Glow✦</span></div>
        <div class="brand-glow-sub">B E A U T Y Management Studio</div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        df_usr = obtener_dataframe_usuarios()
        with st.form("form_login_exclusivo"):
            st.markdown("##### Acceso de Personal Autorizado")
            correo_in = st.text_input("Correo Electrónico ✉️", placeholder="garcialarissa1292@gmail.com").strip().lower()
            pass_in = st.text_input("Contraseña 🔑", type="password")
            recordar_sesion = st.checkbox("🔑 Recordar mi sesión durante todo el día", value=True)
            btn_login = st.form_submit_button("Ingresar a Punto Glow ✨", width="stretch")
            if btn_login:
                usuario_match = df_usr[(df_usr["Correo"].str.lower() == correo_in) & (df_usr["Password"].astype(str) == pass_in)]
                if not usuario_match.empty:
                    nombre_usr = usuario_match.iloc[0]["Nombre"]
                    es_admin = (correo_in == CORREO_ADMIN_UNICO)
                    
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = f"{nombre_usr} ({correo_in})"
                    st.session_state["es_admin"] = es_admin
                    
                    if recordar_sesion:
                        guardar_sesion_local(correo_in, nombre_usr, es_admin)
                        
                    st.success(f"¡Bienvenida/o {nombre_usr}!")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o usuario no autorizado.")

# -----------------------------------------------------------------------------
# 3. MIGRACIÓN Y ESTABLECIMIENTO DE ESTRUCTURAS BASE
# -----------------------------------------------------------------------------
def cargar_csv_seguro(file_path: str, cols_requeridas: list) -> pd.DataFrame:
    """Carga un CSV asegurándose de que contenga las columnas requeridas sin reescribirlo si ya existe."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        df_vacio = pd.DataFrame(columns=cols_requeridas)
        df_vacio.to_csv(file_path, index=False)
        return df_vacio
    try:
        df = pd.read_csv(file_path)
        for col in cols_requeridas:
            if col not in df.columns:
                df[col] = 0.0 if "$" in col else "N/A"
        return sanitizar_dataframe(df[cols_requeridas])
    except Exception:
        df_vacio = pd.DataFrame(columns=cols_requeridas)
        df_vacio.to_csv(file_path, index=False)
        return df_vacio

def inicializar_y_migrar_archivos():
    cols_citas = ["Fecha", "Hora", "Cliente", "Tel_Cliente", "Servicio", "Especialista", "Link Meet", "Anticipo ($)", "Estatus", "Motivo Cancelación"]
    cols_ventas = ["Fecha_Hora", "Cliente", "Servicio", "Ubicación", "Atendido Por", "Cobro Total ($)", "Pago al Talento ($)", "20% Arguettas ($)", "Utilidad Punto Glow ($)", "Dinero", "Comentarios"]
    cols_gastos = ["Fecha", "Concepto", "Categoría", "Monto ($)"]
    
    cargar_csv_seguro(FILE_CITAS, cols_citas)
    cargar_csv_seguro(FILE_VENTAS, cols_ventas)
    cargar_csv_seguro(FILE_GASTOS, cols_gastos)

# -----------------------------------------------------------------------------
# 4. CONTROL PRINCIPAL DE EJECUCIÓN
# -----------------------------------------------------------------------------
if not st.session_state.get("autenticado", False):
    requerir_login()
else:
    inicializar_y_migrar_archivos()
    cols_citas = ["Fecha", "Hora", "Cliente", "Tel_Cliente", "Servicio", "Especialista", "Link Meet", "Anticipo ($)", "Estatus", "Motivo Cancelación"]
    cols_ventas = ["Fecha_Hora", "Cliente", "Servicio", "Ubicación", "Atendido Por", "Cobro Total ($)", "Pago al Talento ($)", "20% Arguettas ($)", "Utilidad Punto Glow ($)", "Dinero", "Comentarios"]
    cols_gastos = ["Fecha", "Concepto", "Categoría", "Monto ($)"]
    
    df_ventas = cargar_csv_seguro(FILE_VENTAS, cols_ventas)
    df_gastos = cargar_csv_seguro(FILE_GASTOS, cols_gastos)
    df_citas = cargar_csv_seguro(FILE_CITAS, cols_citas)

    def generar_excel_cierre(df_v, df_g, df_c):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_v.to_excel(writer, sheet_name='Ventas (Ingresos)', index=False)
            df_g.to_excel(writer, sheet_name='Gastos (Egresos)', index=False)
            df_c.to_excel(writer, sheet_name='Agenda de Citas', index=False)
        output.seek(0)
        return output

    def crear_link_wa(telefono, mensaje):
        msg_encoded = urllib.parse.quote(mensaje)
        return f"https://api.whatsapp.com/send?phone={telefono}&text={msg_encoded}"

    # -------------------------------------------------------------------------
    # MODALES FLOTANTES (VENTAS, CITAS, GASTOS, CONVERSIÓN DE CITAS)
    # -------------------------------------------------------------------------
    @st.dialog("Registrar Nueva Venta 💖")
    def modal_nueva_venta(datos_precargados=None):
        def_cliente = datos_precargados.get("Cliente", "") if datos_precargados else ""
        def_atiende = datos_precargados.get("Especialista", "") if datos_precargados else ""
        def_servicio_txt = datos_precargados.get("Servicio", "") if datos_precargados else ""
        def_anticipo = datos_precargados.get("Anticipo", 0.0) if datos_precargados else 0.0
        
        opciones_servicios = ["Uñas Gel / Acrílico", "Diseño de Cejas / Microblading", "Lash Lifting / Pestañas", "Alaciado Permanente", "Facial Glowing", "Otro"]
        index_serv = 0
        if def_servicio_txt:
            for i, op in enumerate(opciones_servicios):
                if op.lower() in def_servicio_txt.lower():
                    index_serv = i
                    break
                    
        ahora_cdmx = obtener_ahora_cdmx()
        with st.form("form_modal_venta", clear_on_submit=True):
            f1, f2 = st.columns(2)
            fv_fecha = f1.date_input("FECHA DE LA VENTA *", ahora_cdmx.date())
            fv_cliente = f2.text_input("NOMBRE DE LA CLIENTA *", value=def_cliente, placeholder="Ej. Lucía Fernández")
            
            c_atiende, c_serv = st.columns(2)
            fv_atiende = c_atiende.text_input("ATENDIDO POR *", value=def_atiende, placeholder="Nombre de la especialista...")
            fv_servicio = c_serv.selectbox("SERVICIO", opciones_servicios, index=index_serv)
            
            f4, f5 = st.columns(2)
            fv_ubicacion = f4.selectbox("UBICACIÓN / SEDE *", ["Santa Fe", "Arguettas", "A domicilio"])
            fv_dinero = f5.selectbox("DINERO (MÉTODO PAGO)", ["Efectivo", "Transferencia SPEI", "Tarjeta de Débito/Crédito"])
            
            c_m1, c_m2, c_m3 = st.columns(3)
            fv_cobro_total = c_m1.number_input("COBRO TOTAL ($) *", min_value=0.0, step=50.0, value=None, placeholder="0.00")
            fv_pago_talento = c_m2.number_input("PAGO AL TALENTO ($) *", min_value=0.0, step=50.0, value=None, placeholder="0.00")
            
            val_cobro = fv_cobro_total if fv_cobro_total is not None else 0.0
            val_talento = fv_pago_talento if fv_pago_talento is not None else 0.0
            
            descuento_arguettas = (val_cobro * 0.20) if fv_ubicacion == "Arguettas" else 0.0
            utilidad_glow = val_cobro - val_talento - descuento_arguettas
            
            c_m3.text_input("20% ARGUETTAS ($)", value=f"${descuento_arguettas:,.2f}", disabled=True)
            st.info(f"💡 **Utilidad estimada Punto Glow:** ${utilidad_glow:,.2f}")
            
            comentario_default = f"Convertida de Cita. Servicio: {def_servicio_txt}. Anticipo previo: ${def_anticipo:,.2f}" if datos_precargados else ""
            fv_comentarios = st.text_area("COMENTARIOS", value=comentario_default, placeholder="Notas adicionales del servicio...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_v1, col_v2 = st.columns(2)
            cancelar = col_v1.form_submit_button("Cancelar", width="stretch")
            guardar = col_v2.form_submit_button("Guardar Venta", width="stretch")
            
            if guardar:
                if fv_cliente and fv_cobro_total is not None and fv_cobro_total > 0:
                    nueva_v = pd.DataFrame([{
                        "Fecha_Hora": str(fv_fecha),
                        "Cliente": fv_cliente,
                        "Servicio": fv_servicio,
                        "Ubicación": fv_ubicacion,
                        "Atendido Por": fv_atiende,
                        "Cobro Total ($)": val_cobro,
                        "Pago al Talento ($)": val_talento,
                        "20% Arguettas ($)": descuento_arguettas,
                        "Utilidad Punto Glow ($)": utilidad_glow,
                        "Dinero": fv_dinero,
                        "Comentarios": fv_comentarios
                    }])
                    df_actual = cargar_csv_seguro(FILE_VENTAS, cols_ventas)
                    pd.concat([df_actual, nueva_v], ignore_index=True).to_csv(FILE_VENTAS, index=False)
                    st.success("✨ Venta registrada con éxito.")
                    st.rerun()
                else:
                    st.error("Por favor completa el nombre de la clienta y un cobro total válido.")

    @st.dialog("Agendar Cita Punto Glow 🎆")
    def modal_agendar_cita():
        st.caption("Captura la cita, duración, anticipo abonado y datos de contacto")
        ahora_cdmx = obtener_ahora_cdmx()
        with st.form("form_modal_cita", clear_on_submit=True):
            fc_cliente = st.text_input("NOMBRE DE LA CLIENTA *", value="", placeholder="Ej. Sofía Mendoza")
            st.text_input("WHATSAPP CONTACTO (PUNTO GLOW)", value="55 3035 0615", disabled=True)
            
            col_s1, col_s2 = st.columns(2)
            fc_servicio = col_s1.text_input("SERVICIO *", value="", placeholder="Ej. Uñas & Lash Lift")
            fc_especialista = col_s2.text_input("ESPECIALISTA / TALENTO *", value="", placeholder="Ej. Mariana")
            
            col_f1, col_f2 = st.columns(2)
            fc_fecha = col_f1.date_input("FECHA *", ahora_cdmx.date())
            
            opciones_duracion = {
                "30 Minutos": 30,
                "45 Minutos": 45,
                "1 Hora": 60,
                "1.5 Horas (1h 30m)": 90,
                "2 Horas": 120,
                "2.5 Horas (2h 30m)": 150,
                "3 Horas": 180,
                "3.5 Horas (3h 30m)": 210,
                "4 Horas": 240,
                "4.5 Horas (4h 30m)": 270,
                "5 Horas": 300,
                "5.5 Horas (5h 30m)": 330,
                "6 Horas": 360,
                "6.5 Horas (6h 30m)": 390,
                "7 Horas": 420,
                "7.5 Horas (7h 30m)": 450,
                "8 Horas": 480
            }
            duracion_sel = col_f2.selectbox("DURACIÓN ESTIMADA DEL SERVICIO *", list(opciones_duracion.keys()), index=2)
            
            st.write("**HORA DE INICIO DE LA CITA (12 HORAS)**")
            col_h1, col_h2, col_h3 = st.columns(3)
            hora_12 = col_h1.selectbox("HORA", [f"{i:02d}" for i in range(1, 13)], index=9, key="c_h")
            minuto = col_h2.selectbox("MINUTOS", ["00", "15", "30", "45"], index=0, key="c_m")
            periodo = col_h3.selectbox("PERÍODO", ["AM", "PM"], index=1, key="c_p")
            
            fc_anticipo = st.number_input("ANTICIPO ABONADO ($)", min_value=0.0, step=50.0, value=None, placeholder="0.00")
            
            generar_meet = st.checkbox("✨ Incluir enlace de Google Meet", value=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            cancelar = col_btn1.form_submit_button("Cancelar", width="stretch")
            guardar = col_btn2.form_submit_button("Guardar Cita", width="stretch")
            
            if guardar:
                if fc_cliente and fc_servicio:
                    link_meet = "https://meet.google.com/new" if generar_meet else "N/A"
                    
                    hora_inicio_str = f"{hora_12}:{minuto} {periodo.lower()}"
                    minutos_duracion = opciones_duracion[duracion_sel]
                    hora_fin_str = calcular_hora_fin(hora_inicio_str, minutos_duracion)
                    
                    horario_completo_str = f"de {hora_inicio_str} a {hora_fin_str}"
                    val_anticipo = fc_anticipo if fc_anticipo is not None else 0.0
                    
                    nueva_cita = pd.DataFrame([{
                        "Fecha": str(fc_fecha),
                        "Hora": horario_completo_str,
                        "Cliente": fc_cliente,
                        "Tel_Cliente": "5215530350615",
                        "Servicio": fc_servicio,
                        "Especialista": fc_especialista if fc_especialista else "Por asignar",
                        "Link Meet": link_meet,
                        "Anticipo ($)": val_anticipo,
                        "Estatus": "Confirmada",
                        "Motivo Cancelación": "N/A"
                    }])
                    df_c_actual = cargar_csv_seguro(FILE_CITAS, cols_citas)
                    pd.concat([df_c_actual, nueva_cita], ignore_index=True).to_csv(FILE_CITAS, index=False)
                    st.success(f"✨ Cita agendada {horario_completo_str}.")
                    st.rerun()
                else:
                    st.error("Por favor completa el nombre de la clienta y el servicio.")

    @st.dialog("Registrar Gasto Operativo 💸")
    def modal_nuevo_gasto():
        ahora_cdmx = obtener_ahora_cdmx()
        with st.form("form_modal_gasto", clear_on_submit=True):
            fg_fecha = st.date_input("FECHA DEL GASTO", ahora_cdmx.date())
            fg_concepto = st.text_input("CONCEPTO DEL GASTO *", value="", placeholder="Ej. Compra de gelish y acetona")
            fg_cat = st.selectbox("CATEGORÍA", ["Insumos / Productos", "Renta / Servicios", "Publicidad", "Nómina", "Otros Egresos"])
            fg_monto = st.number_input("MONTO ($) *", min_value=0.0, step=50.0, value=None, placeholder="0.00")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_g1, col_g2 = st.columns(2)
            cancelar = col_g1.form_submit_button("Cancelar", width="stretch")
            guardar = col_g2.form_submit_button("Guardar Gasto", width="stretch")
            
            if guardar:
                if fg_concepto and fg_monto is not None and fg_monto > 0:
                    nuevo_g = pd.DataFrame([{
                        "Fecha": str(fg_fecha),
                        "Concepto": fg_concepto,
                        "Categoría": fg_cat,
                        "Monto ($)": fg_monto
                    }])
                    df_g_actual = cargar_csv_seguro(FILE_GASTOS, cols_gastos)
                    pd.concat([df_g_actual, nuevo_g], ignore_index=True).to_csv(FILE_GASTOS, index=False)
                    st.success("💸 Gasto registrado correctamente.")
                    st.rerun()
                else:
                    st.error("Por favor ingresa un concepto y monto válido.")

    # -------------------------------------------------------------------------
    # SIDEBAR CON NAVEGACIÓN Y BOTONES ACCIÓN RÁPIDA
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown('<div class="brand-glow-title">punto<span>Glow✦</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-glow-sub">B E A U T Y</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#F089AB; font-weight:600; font-size:0.85rem; margin-top:8px;'>✨ Beauty Management Studio ✨</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#888888; font-size:0.8rem;'>👤 {st.session_state['usuario_actual']}</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#FCE4EC; margin-bottom:15px;'>", unsafe_allow_html=True)
        
        opciones_menu = ["Dashboard Panel", "Ventas (Ingresos)", "Gastos (Egresos)", "Agenda & Meet", "Cierres de Caja"]
        iconos_menu = ["pie-chart-fill", "wallet2", "receipt", "calendar-heart", "cash-stack"]
        
        if st.session_state.get("es_admin", False):
            opciones_menu.append("Gestión de Usuarios")
            iconos_menu.append("person-gear")
            
        menu_seleccionado = option_menu(
            menu_title=None,
            options=opciones_menu,
            icons=iconos_menu,
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#F089AB", "font-size": "1.1rem"},
                "nav-link": {"font-size": "1rem", "text-align": "left", "margin": "6px 0px", "color": "#333333", "font-family": "Josefin Sans, sans-serif", "font-weight": "600", "border-radius": "25px", "padding": "10px 18px"},
                "nav-link-selected": {"background-color": "#000000", "color": "#FFFFFF", "font-weight": "700", "box-shadow": "0px 4px 12px rgba(0,0,0,0.15)"},
            }
        )
        
        st.markdown("<br><hr style='border-color:#FCE4EC; margin-bottom:15px;'>", unsafe_allow_html=True)
        if st.button("✦ Registrar Venta", width="stretch", key="btn_reg_v_img"):
            modal_nueva_venta()
        if st.button("📅 Agendar Cita", width="stretch", key="btn_agen_c_img"):
            modal_agendar_cita()
        if st.button("💸 Registrar Gasto", width="stretch", key="btn_reg_g_img"):
            modal_nuevo_gasto()
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", width="stretch"):
            borrar_sesion_local()
            st.session_state["autenticado"] = False
            st.session_state["usuario_actual"] = ""
            st.session_state["es_admin"] = False
            st.rerun()

    # -------------------------------------------------------------------------
    # BANNER SUPERIOR CON HORA SINCRONIZADA A CDMX
    # -------------------------------------------------------------------------
    col_b1, col_b2 = st.columns([3.2, 1.8])
    ahora_cdmx = obtener_ahora_cdmx()
    with col_b1:
        st.markdown("""
        <div class="top-banner">
            <div>
                <div class="top-title">Hola, <span>Punto Glow Team</span> ✨</div>
                <div class="top-sub">Control financiero y gestión de citas en tiempo real</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_b2:
        st.write("")
        c_time, c_btn = st.columns([1.2, 1.5])
        hora_cdmx_str = ahora_cdmx.strftime("%I:%M:%S %p").lower()
        c_time.markdown(f'<div class="clock-badge">🕒 {hora_cdmx_str}<br><span style="font-size:0.75rem; color:#888;">CDMX</span></div>', unsafe_allow_html=True)
        
        excel_data = generar_excel_cierre(df_ventas, df_gastos, df_citas)
        c_btn.download_button(
            label="📊 Exportar Excel",
            data=excel_data,
            file_name=f"cierre_punto_glow_{ahora_cdmx.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )

    # -------------------------------------------------------------------------
    # VISTAS PRINCIPALES DE LA APLICACIÓN
    # -------------------------------------------------------------------------
    if menu_seleccionado == "Dashboard Panel":
        fecha_hoy_str = ahora_cdmx.strftime("%Y-%m-%d")
        
        if not df_ventas.empty and "Fecha_Hora" in df_ventas.columns:
            ventas_hoy_df = df_ventas[
                df_ventas["Fecha_Hora"].dropna().astype(str).str.startswith(fecha_hoy_str)
            ]
            v_hoy = float(ventas_hoy_df["Cobro Total ($)"].sum()) if not ventas_hoy_df.empty else 0.0
        else:
            v_hoy = 0.0
            
        v_mes = float(df_ventas["Cobro Total ($)"].sum()) if not df_ventas.empty else 0.0
        g_mes = float(df_gastos["Monto ($)"].sum()) if not df_gastos.empty else 0.0
        utilidad_glow_total = float(df_ventas["Utilidad Punto Glow ($)"].sum()) if not df_ventas.empty else 0.0
        ganancia_neta = utilidad_glow_total - g_mes
        margen_rent = (ganancia_neta / v_mes * 100) if v_mes > 0 else 0.0
        
        k1, k2, k3, k4 = st.columns([1, 1, 1, 1.2])
        k1.markdown(f'<div class="card-metric"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">VENTAS DE HOY</div><div class="metric-val">${v_hoy:,.2f}</div><div style="color:#2ECC71; font-weight:600; font-size:0.85rem;">↗ Ingreso diario CDMX</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="card-metric"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">COBRO TOTAL DEL MES</div><div class="metric-val">${v_mes:,.2f}</div><div style="color:#888888; font-size:0.85rem;">{len(df_ventas)} servicios realizados</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="card-metric"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">GASTOS DEL MES</div><div class="metric-val" style="color:#E74C3C;">${g_mes:,.2f}</div><div style="color:#E74C3C; font-size:0.85rem;">{len(df_gastos)} egresos registrados</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="card-metric-black"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">UTILIDAD NETA GLOW</div><div class="metric-val-black">${ganancia_neta:,.2f}</div><div style="color:#F089AB; font-weight:600; font-size:0.85rem;">Margen: {margen_rent:.1f}% de rentabilidad</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        g_col1, g_col2 = st.columns([1.6, 1.1])
        
        with g_col1:
            st.markdown("### **Resumen Financiero (Últimos 7 Días)**")
            fechas_7d = [(ahora_cdmx - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            fechas_7d_labels = [(ahora_cdmx - timedelta(days=i)).strftime("%d/%m") for i in range(6, -1, -1)]
            
            ventas_diarias = []
            gastos_diarios = []
            
            for f_str in fechas_7d:
                v_sum = df_ventas[df_ventas["Fecha_Hora"].dropna().astype(str).str.startswith(f_str)]["Cobro Total ($)"].sum() if not df_ventas.empty else 0.0
                g_sum = df_gastos[df_gastos["Fecha"].dropna().astype(str).str.startswith(f_str)]["Monto ($)"].sum() if not df_gastos.empty else 0.0
                ventas_diarias.append(float(v_sum))
                gastos_diarios.append(float(g_sum))
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=fechas_7d_labels, y=ventas_diarias, mode='lines+markers', name='Ventas ($)', line=dict(color='#F089AB', width=4, shape='spline'), fill='tozeroy', fillcolor='rgba(240, 137, 171, 0.15)'))
            fig.add_trace(go.Scatter(x=fechas_7d_labels, y=gastos_diarios, mode='lines+markers', name='Gastos ($)', line=dict(color='#000000', width=2, dash='dash', shape='spline')))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white', height=330, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
            
        with g_col2:
            st.markdown("### **📅 Citas para Hoy**")
            with st.container():
                st.markdown('<div class="table-container-card">', unsafe_allow_html=True)
                citas_hoy = df_citas[df_citas["Fecha"].dropna().astype(str) == fecha_hoy_str] if not df_citas.empty else pd.DataFrame()
                if not citas_hoy.empty:
                    for idx, row in citas_hoy.iterrows():
                        st.markdown(f"""
                        <div style="background-color:#FFF0F5; border-radius:14px; padding:12px; margin-bottom:10px; border-left:5px solid #F089AB;">
                            <div style="font-weight:700; color:#000000;">⏰ {row['Hora']} - {row['Cliente']}</div>
                            <div style="color:#F089AB; font-size:0.85rem; font-weight:600;">💅 {row['Servicio']} (Atiende: {row['Especialista']})</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No hay citas programadas para el día de hoy.")
                st.markdown('</div>', unsafe_allow_html=True)

    elif menu_seleccionado == "Ventas (Ingresos)":
        h_col1, h_col2 = st.columns([3, 1])
        with h_col1:
            st.markdown('<div class="section-title">Registro de Ventas y Servicios</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-sub">Historial detallado con desgloses de comisiones y sedes</div>', unsafe_allow_html=True)
        with h_col2:
            if st.button("⊕ Nueva Venta", key="btn_nueva_venta_header"):
                modal_nueva_venta()
                
        st.markdown('<div class="table-container-card">', unsafe_allow_html=True)
        
        b_col1, b_col2 = st.columns([2.5, 1])
        with b_col1:
            busqueda = st.text_input("Buscador", placeholder="🔍 Buscar por cliente, servicio o sede...", label_visibility="collapsed")
        
        df_filtrado = df_ventas.copy()
        if busqueda:
            df_filtrado = df_filtrado[
                df_filtrado['Cliente'].astype(str).str.contains(busqueda, case=False, na=False) |
                df_filtrado['Servicio'].astype(str).str.contains(busqueda, case=False, na=False) |
                df_filtrado['Ubicación'].astype(str).str.contains(busqueda, case=False, na=False)
            ]
        
        total_filtrado = float(df_filtrado["Cobro Total ($)"].sum()) if not df_filtrado.empty else 0.0
        with b_col2:
            st.markdown(f'<div style="text-align:right; font-size:1.05rem; font-weight:600; color:#333; margin-top:8px;">Total Filtrado: <span style="color:#F089AB; font-weight:700;">${total_filtrado:,.2f}</span></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns([1.2, 1.3, 1.6, 1.1, 1.1, 1.1, 1.1, 1.2, 1.0, 0.6])
        c1.markdown("**FECHA**")
        c2.markdown("**CLIENTE**")
        c3.markdown("**SERVICIO**")
        c4.markdown("**SEDE**")
        c5.markdown("**TOTAL ($)**")
        c6.markdown("**TALENTO ($)**")
        c7.markdown("**ARGUETTAS ($)**")
        c8.markdown("**UTILIDAD ($)**")
        c9.markdown("**DINERO**")
        c10.markdown("**BORRAR**")
        
        st.markdown("<hr style='margin:8px 0; border-color:#FCE4EC;'>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            for idx, row in df_filtrado.iterrows():
                r1, r2, r3, r4, r5, r6, r7, r8, r9, r10 = st.columns([1.2, 1.3, 1.6, 1.1, 1.1, 1.1, 1.1, 1.2, 1.0, 0.6])
                r1.write(row["Fecha_Hora"])
                r2.markdown(f"**{row['Cliente']}**")
                r3.markdown(f'<span class="service-badge">{row["Servicio"]}</span>', unsafe_allow_html=True)
                r4.write(row["Ubicación"])
                r5.markdown(f'<span class="monto-green">${float(row["Cobro Total ($)"]):,.2f}</span>', unsafe_allow_html=True)
                r6.write(f'${float(row["Pago al Talento ($)"]):,.2f}')
                r7.write(f'${float(row["20% Arguettas ($)"]):,.2f}')
                r8.markdown(f'**${float(row["Utilidad Punto Glow ($)"]):,.2f}**')
                r9.write(row["Dinero"])
                
                if r10.button("🗑️", key=f"del_venta_{idx}"):
                    df_ventas = df_ventas.drop(idx).reset_index(drop=True)
                    df_ventas.to_csv(FILE_VENTAS, index=False)
                    st.success("Venta eliminada correctamente.")
                    st.rerun()
                st.markdown("<hr style='margin:4px 0; border-color:#FFF0F5;'>", unsafe_allow_html=True)
        else:
            st.info("No se encontraron registros de ventas.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif menu_seleccionado == "Gastos (Egresos)":
        st.markdown('<div class="section-title">💸 Registro de Gastos Operativos</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Control de egresos y costos del estudio</div>', unsafe_allow_html=True)
        st.markdown('<div class="table-container-card">', unsafe_allow_html=True)
        
        g1, g2, g3, g4, g5 = st.columns([1.5, 3, 2, 1.5, 1])
        g1.markdown("**FECHA**")
        g2.markdown("**CONCEPTO**")
        g3.markdown("**CATEGORÍA**")
        g4.markdown("**MONTO ($)**")
        g5.markdown("**BORRAR**")
        
        st.markdown("<hr style='margin:8px 0; border-color:#FCE4EC;'>", unsafe_allow_html=True)
        if not df_gastos.empty:
            for idx, row in df_gastos.iterrows():
                rg1, rg2, rg3, rg4, rg5 = st.columns([1.5, 3, 2, 1.5, 1])
                rg1.write(row["Fecha"])
                rg2.write(row["Concepto"])
                rg3.write(row["Categoría"])
                rg4.markdown(f'<span class="monto-red">${float(row["Monto ($)"]):,.2f}</span>', unsafe_allow_html=True)
                
                if rg5.button("🗑️", key=f"del_gasto_{idx}"):
                    df_gastos = df_gastos.drop(idx).reset_index(drop=True)
                    df_gastos.to_csv(FILE_GASTOS, index=False)
                    st.success("Gasto eliminado correctamente.")
                    st.rerun()
                st.markdown("<hr style='margin:4px 0; border-color:#FFF0F5;'>", unsafe_allow_html=True)
        else:
            st.info("No hay gastos registrados.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif menu_seleccionado == "Agenda & Meet":
        st.markdown('<div class="section-title">✨ Agenda & Notificaciones por WhatsApp</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Gestión de citas, conversión directa a ventas y control de estatus</div>', unsafe_allow_html=True)
        st.markdown('<div class="table-container-card">', unsafe_allow_html=True)
        
        if not df_citas.empty:
            for idx, row in df_citas.iterrows():
                estatus_class = "status-confirmada" if row["Estatus"] == "Confirmada" else "status-cancelada"
                col_c1, col_c2 = st.columns([3.8, 1.2])
                
                with col_c1:
                    st.markdown(f"### 📅 Cita: **{row['Cliente']}** — {row['Fecha']} ({row['Hora']}) <span class='{estatus_class}'>{row['Estatus']}</span>", unsafe_allow_html=True)
                    st.markdown(f"💅 **Servicio:** {row['Servicio']} | 👩‍🎨 **Especialista:** {row['Especialista']} | 💰 **Anticipo Abonado:** ${float(row['Anticipo ($)']):,.2f}")
                    
                    if row["Estatus"] == "Cancelada":
                        st.error(f"❌ **Motivo de Cancelación:** {row['Motivo Cancelación']}")
                
                with col_c2:
                    if st.button("💳 Convertir a Venta", key=f"btn_conv_venta_{idx}"):
                        modal_nueva_venta(datos_precargados={
                            "Cliente": row["Cliente"],
                            "Especialista": row["Especialista"],
                            "Servicio": row["Servicio"],
                            "Anticipo": float(row["Anticipo ($)"])
                        })
                    
                    if st.button("🗑️ Borrar Cita", key=f"btn_del_cita_{idx}"):
                        df_citas = df_citas.drop(idx).reset_index(drop=True)
                        df_citas.to_csv(FILE_CITAS, index=False)
                        st.success("Cita eliminada correctamente.")
                        st.rerun()
                        
                with st.expander(f"⚙️ Administrar Cita de {row['Cliente']}"):
                    with st.form(f"form_estatus_{idx}"):
                        nuevo_estatus = st.selectbox("Estatus de Cita", ["Confirmada", "Cancelada"], index=0 if row["Estatus"] == "Confirmada" else 1)
                        motivo_input = st.text_input("Motivo de Cancelación (Si aplica)", value="" if row["Motivo Cancelación"] == "N/A" else row["Motivo Cancelación"])
                        btn_actualizar = st.form_submit_button("Guardar Cambios")
                        
                        if btn_actualizar:
                            df_citas.at[idx, "Estatus"] = nuevo_estatus
                            df_citas.at[idx, "Motivo Cancelación"] = motivo_input if nuevo_estatus == "Cancelada" else "N/A"
                            df_citas.to_csv(FILE_CITAS, index=False)
                            st.success("Estatus actualizado correctamente.")
                            st.rerun()
                            
                link_gcal_corto = generar_link_gcal(str(row['Fecha']), str(row['Hora']), str(row['Servicio']), str(row['Cliente']))
                
                msg_cli = (
                    f"¡Hola {row['Cliente']}! ✨ Confirmamos tu cita en Punto Glow para el {row['Fecha']} {row['Hora']} ({row['Servicio']}).\n"
                    f"💰 Anticipo abonado: ${float(row['Anticipo ($)']):,.2f}.\n\n"
                    f"📅 Agrega tu cita a Google Calendar aquí:\n{link_gcal_corto}"
                )
                link_cli = crear_link_wa(row.get("Tel_Cliente", "5215530350615"), msg_cli)
                
                st.markdown("**Enviar notificaciones directas por WhatsApp:**")
                wa_html = f'<a href="{link_cli}" target="_blank" class="btn-wa-pill">📲 Confirmar por WhatsApp + Agendar en Google Calendar</a>'
                st.markdown(wa_html, unsafe_allow_html=True)
                
                st.markdown("<hr style='margin:18px 0; border-color:#FCE4EC;'>", unsafe_allow_html=True)
        else:
            st.info("No hay citas registradas.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif menu_seleccionado == "Cierres de Caja":
        st.markdown('<div class="section-title">💰 Cierres de Caja & Auditoría</div>', unsafe_allow_html=True)
        tab_v, tab_g = st.tabs(["📊 Reporte Completo de Ventas", "💸 Reporte Completo de Gastos"])
        
        with tab_v:
            st.dataframe(df_ventas, width="stretch")
        with tab_g:
            st.dataframe(df_gastos, width="stretch")

    elif menu_seleccionado == "Gestión de Usuarios":
        st.markdown('<div class="section-title">👤 Panel Exclusivo Administradora: Gestión de Usuarios</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Solo tú tienes autorización para registrar o eliminar accesos del sistema</div>', unsafe_allow_html=True)
        
        col_u1, col_u2 = st.columns([1.2, 1.4])
        with col_u1:
            st.markdown('<div class="table-container-card">', unsafe_allow_html=True)
            st.markdown("#### **Registrar Nuevo Miembro de Equipo**")
            df_usr_act = obtener_dataframe_usuarios()
            
            with st.form("form_alta_usuario_admin", clear_on_submit=True):
                new_nombre = st.text_input("Nombre Completo *", value="", placeholder="Ej. Ana Lucía Pérez")
                new_correo = st.text_input("Correo Electrónico *", value="", placeholder="ana@glow.com").strip().lower()
                new_pass = st.text_input("Asignar Contraseña *", type="password")
                new_rol = st.selectbox("Asignar Rol", ["Especialista", "Recepción"])
                
                st.markdown("<br>", unsafe_allow_html=True)
                btn_crear = st.form_submit_button("Guardar Acceso 💾", width="stretch")
                
                if btn_crear:
                    if new_nombre and new_correo and new_pass:
                        if new_correo in df_usr_act["Correo"].str.lower().values:
                            st.warning("⚠️ Este correo ya se encuentra registrado.")
                        else:
                            nuevo_registro = pd.DataFrame([{
                                "Nombre": new_nombre,
                                "Correo": new_correo,
                                "Password": new_pass,
                                "Rol": new_rol
                            }])
                            pd.concat([df_usr_act, nuevo_registro], ignore_index=True).to_csv(FILE_USUARIOS, index=False)
                            st.success(f"✨ Acceso creado exitosamente para **{new_nombre}**.")
                            st.rerun()
                    else:
                        st.error("Por favor completa los campos obligatorios.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_u2:
            st.markdown('<div class="table-container-card">', unsafe_allow_html=True)
            st.markdown("#### **Usuarios Autorizados Actualmente**")
            df_usr_display = obtener_dataframe_usuarios()
            if not df_usr_display.empty:
                for u_idx, u_row in df_usr_display.iterrows():
                    u_col1, u_col2 = st.columns([3, 1])
                    with u_col1:
                        st.markdown(f"👤 **{u_row['Nombre']}** ({u_row['Rol']})")
                        st.caption(f"✉️ {u_row['Correo']}")
                    with u_col2:
                        if u_row['Correo'].lower() == CORREO_ADMIN_UNICO:
                            st.markdown("🔒 *Admin*")
                        else:
                            if st.button("🗑️ Borrar", key=f"btn_del_usr_{u_idx}"):
                                df_usr_display = df_usr_display.drop(u_idx).reset_index(drop=True)
                                df_usr_display.to_csv(FILE_USUARIOS, index=False)
                                st.success(f"Usuario {u_row['Nombre']} eliminado.")
                                st.rerun()
                    st.markdown("<hr style='margin:6px 0; border-color:#FFF0F5;'>", unsafe_allow_html=True)
            else:
                st.info("No hay usuarios registrados.")
            st.markdown('</div>', unsafe_allow_html=True)