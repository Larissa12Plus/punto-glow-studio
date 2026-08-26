import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import urllib.parse
import plotly.graph_objects as go
import io
from streamlit_option_menu import option_menu

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
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

    /* Sidebar */
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
        color: #E8799E;
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

    /* Banner Superior */
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
    .top-title span { color: #E8799E; }
    .top-sub { color: #888888; font-size: 0.95rem; margin-top: 2px; }

    .clock-badge {
        background-color: #FDF0F5;
        color: #E8799E;
        padding: 8px 18px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
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

    /* BOTONES LATERALES */
    div[data-testid="stSidebar"] div.stButton > button[key="btn_reg_v_img"] {
        background: linear-gradient(135deg, #E8799E 0%, #D8688D 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 20px !important;
        font-family: 'Josefin Sans', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(232, 121, 158, 0.4) !important;
        margin-bottom: 8px !important;
        width: 100% !important;
    }

    div[data-testid="stSidebar"] div.stButton > button[key="btn_agen_c_img"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 20px !important;
        font-family: 'Josefin Sans', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25) !important;
        margin-bottom: 8px !important;
        width: 100% !important;
    }

    div[data-testid="stSidebar"] div.stButton > button[key="btn_reg_g_img"] {
        background-color: #FFF0F5 !important;
        color: #E8799E !important;
        border: 1px solid #E8799E !important;
        border-radius: 25px !important;
        padding: 12px 20px !important;
        font-family: 'Josefin Sans', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 10px rgba(232, 121, 158, 0.15) !important;
        width: 100% !important;
    }

    div.stButton > button[key="btn_nueva_venta_header"] {
        background: linear-gradient(135deg, #E8799E 0%, #D8688D 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 24px !important;
        font-family: 'Josefin Sans', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(232, 121, 158, 0.4) !important;
    }

    /* Cards y Tablas */
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
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. PERSISTENCIA Y MIGRACIÓN AUTOLIMPIANTE DE DATOS
# -----------------------------------------------------------------------------
FILE_VENTAS = "ventas_punto_glow.csv"
FILE_GASTOS = "gastos_punto_glow.csv"
FILE_CITAS = "citas_punto_glow.csv"

def inicializar_y_migrar_archivos():
    if not os.path.exists(FILE_VENTAS):
        pd.DataFrame([
            {
                "Fecha_Hora": "2026-08-26 11:00",
                "Cliente": "Lucía Fernández",
                "Servicio": "Uñas Gel / Acrílico",
                "Ubicación": "Arguettas",
                "Atendido Por": "Mariana",
                "Pago Total ($)": 650.0,
                "Pago a Talento ($)": 325.0,
                "20% Arguettas ($)": 130.0,
                "Utilidad Punto Glow ($)": 195.0,
                "Dinero": "Efectivo",
                "Comentarios": "Diseño con cristales"
            },
            {
                "Fecha_Hora": "2026-08-26 13:30",
                "Cliente": "Valeria Gómez",
                "Servicio": "Diseño de Cejas / Microblading",
                "Ubicación": "Santa Fe",
                "Atendido Por": "Andrea",
                "Pago Total ($)": 1200.0,
                "Pago a Talento ($)": 600.0,
                "20% Arguettas ($)": 0.0,
                "Utilidad Punto Glow ($)": 600.0,
                "Dinero": "Transferencia SPEI",
                "Comentarios": "Cliente frecuente"
            }
        ]).to_csv(FILE_VENTAS, index=False)
    else:
        # MIGRACIÓN AUTOMÁTICA EN CASO DE DETECTAR ESTRUCTURA ANTERIOR
        df_temp = pd.read_csv(FILE_VENTAS)
        if "Pago Total ($)" not in df_temp.columns:
            if "Monto ($)" in df_temp.columns:
                df_temp["Pago Total ($)"] = df_temp["Monto ($)"]
            else:
                df_temp["Pago Total ($)"] = 0.0
            
            df_temp["Ubicación"] = "Santa Fe"
            df_temp["Pago a Talento ($)"] = df_temp["Pago Total ($)"] * 0.5
            df_temp["20% Arguettas ($)"] = 0.0
            df_temp["Utilidad Punto Glow ($)"] = df_temp["Pago Total ($)"] - df_temp["Pago a Talento ($)"]
            
            if "Método Pago" in df_temp.columns:
                df_temp["Dinero"] = df_temp["Método Pago"]
            else:
                df_temp["Dinero"] = "Efectivo"
                
            df_temp["Comentarios"] = "Migrado automáticamente"
            df_temp.to_csv(FILE_VENTAS, index=False)

    if not os.path.exists(FILE_GASTOS):
        pd.DataFrame([
            {"Fecha": "2026-08-24", "Concepto": "Insumos Pestañas", "Categoría": "Insumos / Productos", "Monto ($)": 850.0},
            {"Fecha": "2026-08-25", "Concepto": "Gelish Base Base", "Categoría": "Insumos / Productos", "Monto ($)": 490.0}
        ]).to_csv(FILE_GASTOS, index=False)
        
    if not os.path.exists(FILE_CITAS):
        pd.DataFrame([
            {"Fecha": "2026-08-26", "Hora": "11:00 a. m.", "Cliente": "Sofía Mendoza", "Tel_Cliente": "5215512345678", "Servicio": "Uñas & Lash Lift", "Especialista": "Mariana", "Tel_Especialista": "524420001122", "Link Meet": "https://meet.google.com/new"}
        ]).to_csv(FILE_CITAS, index=False)

inicializar_y_migrar_archivos()

df_ventas = pd.read_csv(FILE_VENTAS)
df_gastos = pd.read_csv(FILE_GASTOS)
df_citas = pd.read_csv(FILE_CITAS)

def generar_excel_cierre(df_v, df_g, df_c):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_v.to_excel(writer, sheet_name='Ventas (Ingresos)', index=False)
        df_g.to_excel(writer, sheet_name='Gastos (Egresos)', index=False)
        df_c.to_excel(writer, sheet_name='Agenda de Citas', index=False)
    output.seek(0)
    return output

# -----------------------------------------------------------------------------
# 3. MODALES FLOTANTES CON REGLAS FINANCIERAS
# -----------------------------------------------------------------------------
@st.dialog("Registrar Nueva Venta 💖")
def modal_nueva_venta():
    with st.form("form_modal_venta"):
        f1, f2 = st.columns(2)
        fv_fecha = f1.date_input("FECHA", datetime.now().date())
        fv_hora = f1.time_input("HORA", datetime.now().time())
        fv_cliente = f2.text_input("NOMBRE DE LA CLIENTA *", placeholder="Ej. Lucía Fernández")
        fv_atiende = f2.text_input("ATENDIDO POR *", value="Mariana")
        
        f3, f4, f5 = st.columns(3)
        fv_servicio = f3.selectbox("SERVICIO", ["Uñas Gel / Acrílico", "Diseño de Cejas / Microblading", "Lash Lifting / Pestañas", "Alaciado Permanente", "Facial Glowing", "Otro"])
        fv_ubicacion = f4.selectbox("UBICACIÓN / SEDE *", ["Santa Fe", "Arguettas", "A domicilio"])
        fv_dinero = f5.selectbox("DINERO (MÉTODO PAGO)", ["Efectivo", "Transferencia SPEI", "Tarjeta de Débito/Crédito"])
        
        c_m1, c_m2, c_m3 = st.columns(3)
        fv_pago_total = c_m1.number_input("PAGO TOTAL ($) *", min_value=0.0, step=50.0)
        fv_pago_talento = c_m2.number_input("PAGO A TALENTO ($) *", min_value=0.0, step=50.0)
        
        descuento_arguettas = (fv_pago_total * 0.20) if fv_ubicacion == "Arguettas" else 0.0
        utilidad_glow = fv_pago_total - fv_pago_talento - descuento_arguettas
        
        c_m3.text_input("20% ARGUETTAS ($)", value=f"${descuento_arguettas:,.2f}", disabled=True)
        st.info(f"💡 **Utilidad estimada para Punto Glow:** ${utilidad_glow:,.2f}")
        
        fv_comentarios = st.text_area("COMENTARIOS", placeholder="Notas adicionales sobre el servicio o pago...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_v1, col_v2 = st.columns(2)
        cancelar = col_v1.form_submit_button("Cancelar", use_container_width=True)
        guardar = col_v2.form_submit_button("Guardar Venta", use_container_width=True)
        
        if guardar:
            if fv_cliente and fv_pago_total > 0:
                nueva_v = pd.DataFrame([{
                    "Fecha_Hora": f"{fv_fecha} {fv_hora.strftime('%H:%M')}",
                    "Cliente": fv_cliente,
                    "Servicio": fv_servicio,
                    "Ubicación": fv_ubicacion,
                    "Atendido Por": fv_atiende,
                    "Pago Total ($)": fv_pago_total,
                    "Pago a Talento ($)": fv_pago_talento,
                    "20% Arguettas ($)": descuento_arguettas,
                    "Utilidad Punto Glow ($)": utilidad_glow,
                    "Dinero": fv_dinero,
                    "Comentarios": fv_comentarios
                }])
                pd.concat([pd.read_csv(FILE_VENTAS), nueva_v], ignore_index=True).to_csv(FILE_VENTAS, index=False)
                st.success("✨ Venta registrada con éxito.")
                st.rerun()

@st.dialog("Agendar Cita Punto Glow 🎆")
def modal_agendar_cita():
    st.caption("Genera la cita y comparte por WhatsApp con Google Meet opcional")
    with st.form("form_modal_cita"):
        fc_cliente = st.text_input("NOMBRE DE LA CLIENTA *", placeholder="Ej. Sofía Mendoza")
        fc_tel = st.text_input("NÚMERO DE WHATSAPP (CON CLAVE PAÍS) *", placeholder="Ej. 5215512345678")
        
        col_s1, col_s2 = st.columns(2)
        fc_servicio = col_s1.text_input("SERVICIO *", placeholder="Ej. Uñas & Lash Lift")
        fc_especialista = col_s2.text_input("ESPECIALISTA", placeholder="Ej. Mariana")
        
        col_f1, col_f2 = st.columns(2)
        fc_fecha = col_f1.date_input("FECHA *", datetime.now().date())
        fc_hora = col_f2.time_input("HORA *", datetime.now().time())
        
        generar_meet = st.checkbox("✨ Generar enlace de Google Meet para consulta/sesión", value=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        cancelar = col_btn1.form_submit_button("Cancelar", use_container_width=True)
        guardar = col_btn2.form_submit_button("Agendar Cita", use_container_width=True)
        
        if guardar:
            if fc_cliente and fc_tel and fc_servicio:
                link_meet = "https://meet.google.com/new" if generar_meet else "N/A"
                nueva_cita = pd.DataFrame([{
                    "Fecha": str(fc_fecha),
                    "Hora": fc_hora.strftime("%I:%M %p").lower(),
                    "Cliente": fc_cliente,
                    "Tel_Cliente": fc_tel,
                    "Servicio": fc_servicio,
                    "Especialista": fc_especialista if fc_especialista else "Por asignar",
                    "Tel_Especialista": "524420001122",
                    "Link Meet": link_meet
                }])
                pd.concat([pd.read_csv(FILE_CITAS), nueva_cita], ignore_index=True).to_csv(FILE_CITAS, index=False)
                st.success("✨ Cita agendada correctamente.")
                st.rerun()

@st.dialog("Registrar Gasto Operativo 💸")
def modal_nuevo_gasto():
    with st.form("form_modal_gasto"):
        fg_fecha = st.date_input("FECHA DEL GASTO", datetime.now().date())
        fg_concepto = st.text_input("CONCEPTO DEL GASTO *", placeholder="Ej. Compra de gelish y acetona")
        fg_cat = st.selectbox("CATEGORÍA", ["Insumos / Productos", "Renta / Servicios", "Publicidad", "Nómina", "Otros Egresos"])
        fg_monto = st.number_input("MONTO ($) *", min_value=0.0, step=50.0)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        cancelar = col_g1.form_submit_button("Cancelar", use_container_width=True)
        guardar = col_g2.form_submit_button("Guardar Gasto", use_container_width=True)
        
        if guardar:
            if fg_concepto and fg_monto > 0:
                nuevo_g = pd.DataFrame([{
                    "Fecha": str(fg_fecha),
                    "Concepto": fg_concepto,
                    "Categoría": fg_cat,
                    "Monto ($)": fg_monto
                }])
                pd.concat([pd.read_csv(FILE_GASTOS), nuevo_g], ignore_index=True).to_csv(FILE_GASTOS, index=False)
                st.success("💸 Gasto registrado correctamente.")
                st.rerun()

# -----------------------------------------------------------------------------
# 4. SIDEBAR DE NAVEGACIÓN
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-glow-title">punto<span>Glow✦</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-glow-sub">B E A U T Y</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#E8799E; font-weight:600; font-size:0.85rem; margin-top:8px;'>✨ Beauty Management Studio ✨</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#FCE4EC; margin-bottom:20px;'>", unsafe_allow_html=True)

    menu_seleccionado = option_menu(
        menu_title=None,
        options=["Dashboard Panel", "Ventas (Ingresos)", "Gastos (Egresos)", "Agenda & Meet", "Cierres de Caja"],
        icons=["pie-chart-fill", "wallet2", "receipt", "calendar-heart", "cash-stack"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#E8799E", "font-size": "1.1rem"},
            "nav-link": {
                "font-size": "1rem",
                "text-align": "left",
                "margin": "6px 0px",
                "color": "#333333",
                "font-family": "Josefin Sans, sans-serif",
                "font-weight": "600",
                "border-radius": "25px",
                "padding": "10px 18px",
            },
            "nav-link-selected": {
                "background-color": "#000000",
                "color": "#FFFFFF",
                "font-weight": "700",
                "box-shadow": "0px 4px 12px rgba(0,0,0,0.15)",
            },
        }
    )

    st.markdown("<br><hr style='border-color:#FCE4EC; margin-bottom:20px;'>", unsafe_allow_html=True)

    if st.button("⊕ Registrar Venta", use_container_width=True, key="btn_reg_v_img"):
        modal_nueva_venta()
    if st.button("📅+ Agendar Cita", use_container_width=True, key="btn_agen_c_img"):
        modal_agendar_cita()
    if st.button("💸 Registrar Gasto", use_container_width=True, key="btn_reg_g_img"):
        modal_nuevo_gasto()

# -----------------------------------------------------------------------------
# 5. BANNER SUPERIOR
# -----------------------------------------------------------------------------
col_b1, col_b2 = st.columns([3.2, 1.8])
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
    hora_actual = datetime.now().strftime("%I:%M:%S %p").lower()
    c_time.markdown(f'<div class="clock-badge">🕒 {hora_actual}</div>', unsafe_allow_html=True)
    
    excel_data = generar_excel_cierre(df_ventas, df_gastos, df_citas)
    c_btn.download_button(
        label="📊 Exportar Excel",
        data=excel_data,
        file_name=f"cierre_punto_glow_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# -----------------------------------------------------------------------------
# 6. DASHBOARD PANEL EN TIEMPO REAL
# -----------------------------------------------------------------------------
if menu_seleccionado == "Dashboard Panel":
    v_mes = df_ventas["Pago Total ($)"].sum() if not df_ventas.empty else 0.0
    g_mes = df_gastos["Monto ($)"].sum() if not df_gastos.empty else 0.0
    utilidad_glow_total = df_ventas["Utilidad Punto Glow ($)"].sum() if not df_ventas.empty else 0.0
    ganancia_neta = utilidad_glow_total - g_mes
    margen_rent = (ganancia_neta / v_mes * 100) if v_mes > 0 else 0.0

    k1, k2, k3, k4 = st.columns([1, 1, 1, 1.2])
    k1.markdown('<div class="card-metric"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">VENTAS DE HOY</div><div class="metric-val">$1,850.00</div><div style="color:#2ECC71; font-weight:600; font-size:0.85rem;">↗ Ingreso diario</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="card-metric"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">VENTAS BRUTAS DEL MES</div><div class="metric-val">${v_mes:,.2f}</div><div style="color:#888888; font-size:0.85rem;">{len(df_ventas)} servicios realizados</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="card-metric"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">GASTOS DEL MES</div><div class="metric-val" style="color:#E74C3C;">${g_mes:,.2f}</div><div style="color:#E74C3C; font-size:0.85rem;">{len(df_gastos)} egresos registrados</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="card-metric-black"><div style="font-size:0.8rem; font-weight:700; color:#A0A0A0;">UTILIDAD NETA GLOW</div><div class="metric-val-black">${ganancia_neta:,.2f}</div><div style="color:#E8799E; font-weight:600; font-size:0.85rem;">Margen: {margen_rent:.1f}% de rentabilidad</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    g_col1, g_col2 = st.columns([1.6, 1.1])
    
    with g_col1:
        st.markdown("### **Resumen Financiero (Últimos 7 Días)**")
        fechas_7d = [(datetime.now() - timedelta(days=i)).strftime("%d/%m") for i in range(6, -1, -1)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fechas_7d, y=[0, 550, 1850, 0, 0, 0, 0], mode='lines+markers', name='Ventas ($)', line=dict(color='#E8799E', width=4, shape='spline'), fill='tozeroy', fillcolor='rgba(232, 121, 158, 0.15)'))
        fig.add_trace(go.Scatter(x=fechas_7d, y=[0, 850, 490, 0, 0, 0, 0], mode='lines+markers', name='Gastos ($)', line=dict(color='#000000', width=2, dash='dash', shape='spline')))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white', height=330, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with g_col2:
        st.markdown("### **📅 Citas para Hoy**")
        with st.container():
            st.markdown('<div class="table-container-card">', unsafe_allow_html=True)
            if not df_citas.empty:
                for idx, row in df_citas.iterrows():
                    st.markdown(f"""
                    <div style="background-color:#FFF0F5; border-radius:14px; padding:12px; margin-bottom:10px; border-left:5px solid #E8799E;">
                        <div style="font-weight:700; color:#000000;">⏰ {row['Hora']} - {row['Cliente']}</div>
                        <div style="color:#E8799E; font-size:0.85rem; font-weight:600;">💅 {row['Servicio']} (Atiende: {row['Especialista']})</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay citas programadas.")
            st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. REGISTRO DE VENTAS DETALLADO
# -----------------------------------------------------------------------------
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
            df_filtrado["Cliente"].str.contains(busqueda, case=False, na=False) |
            df_filtrado["Servicio"].str.contains(busqueda, case=False, na=False) |
            df_filtrado["Ubicación"].str.contains(busqueda, case=False, na=False)
        ]

    total_filtrado = df_filtrado["Pago Total ($)"].sum() if not df_filtrado.empty else 0.0
    with b_col2:
        st.markdown(f'<div style="text-align:right; font-size:1.05rem; font-weight:600; color:#333; margin-top:8px;">Total Filtrado: <span style="color:#E8799E; font-weight:700;">${total_filtrado:,.2f}</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.dataframe(
        df_filtrado[[
            "Fecha_Hora", "Cliente", "Servicio", "Ubicación", "Atendido Por",
            "Pago Total ($)", "Pago a Talento ($)", "20% Arguettas ($)", "Utilidad Punto Glow ($)",
            "Dinero", "Comentarios"
        ]],
        use_container_width=True,
        column_config={
            "Pago Total ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Pago a Talento ($)": st.column_config.NumberColumn(format="$%.2f"),
            "20% Arguettas ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Utilidad Punto Glow ($)": st.column_config.NumberColumn(format="$%.2f"),
        }
    )
        
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 8. GASTOS, AGENDA Y CIERRES DE CAJA
# -----------------------------------------------------------------------------
elif menu_seleccionado == "Gastos (Egresos)":
    st.markdown('<div class="section-title">💸 Registro de Gastos Operativos</div>', unsafe_allow_html=True)
    st.dataframe(df_gastos, use_container_width=True)

elif menu_seleccionado == "Agenda & Meet":
    st.markdown('<div class="section-title">✨ Agenda & Notificaciones</div>', unsafe_allow_html=True)
    st.dataframe(df_citas, use_container_width=True)

elif menu_seleccionado == "Cierres de Caja":
    st.markdown('<div class="section-title">💰 Cierres de Caja & Auditoría</div>', unsafe_allow_html=True)
    tab_v, tab_g = st.tabs(["📊 Reporte Completo de Ventas", "💸 Reporte Completo de Gastos"])
    with tab_v:
        st.dataframe(df_ventas, use_container_width=True)
    with tab_g:
        st.dataframe(df_gastos, use_container_width=True)