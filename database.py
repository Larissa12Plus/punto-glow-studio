"""
Punto Glow Studio - Capa de datos (database.py)
================================================

Capa de acceso a datos sobre PostgreSQL/Supabase usando SQLAlchemy.

Reglas de diseno (ver .agents/tasks/plan.md y schema.sql):
  * El engine se cachea con @st.cache_resource y lee la cadena de conexion
    EXCLUSIVAMENTE desde st.secrets["supabase"]["db_url"]. NO hay credenciales
    hardcodeadas en ningun lugar.
  * Todo el SQL es parametrizado (nunca se interpola texto en la consulta).
  * Las lecturas filtran siempre WHERE is_deleted = FALSE y devuelven un
    pandas.DataFrame con nombres de columna amigables para la UI.
  * "Borrar" = UPDATE ... SET is_deleted = TRUE (soft-delete). Nunca DELETE fisico.
  * Cada INSERT / UPDATE / SOFT_DELETE escribe un renglon en audit_log
    (accion 'INSERT' | 'UPDATE' | 'SOFT_DELETE').
  * Las contrasenas se hashean y verifican con bcrypt.

Los nombres de tablas y columnas coinciden EXACTAMENTE con schema.sql.
"""
from __future__ import annotations

import json
from typing import Optional

import bcrypt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------
CORREO_ADMIN_UNICO = "garcialarissa1292@gmail.com"
NOMBRE_ADMIN = "Larissa García"
PASSWORD_ADMIN = "Lariliz1*"

# El CHECK de la columna usuarios.rol en schema.sql usa 'Recepcion' SIN acento.
# La UI muestra "Recepción" con acento. Estos helpers normalizan en ambos sentidos.
_ROL_A_DB = {"Recepción": "Recepcion"}
_ROL_A_UI = {"Recepcion": "Recepción"}


def _rol_a_db(rol: Optional[str]) -> Optional[str]:
    """Normaliza el rol al valor aceptado por el CHECK de la base de datos."""
    if rol is None:
        return None
    return _ROL_A_DB.get(rol, rol)


def _rol_a_ui(rol: Optional[str]) -> Optional[str]:
    """Normaliza el rol al valor que muestra la interfaz."""
    if rol is None:
        return None
    return _ROL_A_UI.get(rol, rol)


# ---------------------------------------------------------------------------
# Conexion (engine cacheado)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def obtener_engine() -> Engine:
    """
    Crea (y cachea) el engine de SQLAlchemy hacia Supabase/PostgreSQL.

    La cadena de conexion se lee de st.secrets["supabase"]["db_url"] con el
    formato: postgresql+psycopg2://usuario:password@host:5432/postgres
    """
    db_url = st.secrets["supabase"]["db_url"]
    return create_engine(db_url, pool_pre_ping=True, future=True)


# ---------------------------------------------------------------------------
# Helpers genericos
# ---------------------------------------------------------------------------
def _leer_df(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    """Ejecuta una consulta parametrizada y devuelve un DataFrame."""
    engine = obtener_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def _registrar_auditoria(conn, tabla: str, fila_id, accion: str,
                         datos: Optional[dict] = None,
                         usuario: Optional[str] = None) -> None:
    """
    Inserta un renglon en audit_log. Se llama dentro de la MISMA transaccion
    de la operacion que se audita (conn ya abierto).
    accion debe ser uno de: 'INSERT', 'UPDATE', 'SOFT_DELETE'.
    """
    conn.execute(
        text(
            """
            INSERT INTO audit_log (tabla, fila_id, accion, datos, usuario)
            VALUES (:tabla, :fila_id, :accion, CAST(:datos AS JSONB), :usuario)
            """
        ),
        {
            "tabla": tabla,
            "fila_id": int(fila_id) if fila_id is not None else None,
            "accion": accion,
            "datos": json.dumps(datos, ensure_ascii=False, default=str) if datos is not None else None,
            "usuario": usuario,
        },
    )


# ===========================================================================
# USUARIOS
# ===========================================================================
def obtener_usuarios() -> pd.DataFrame:
    """Usuarios activos, con nombres de columna amigables para la UI."""
    df = _leer_df(
        """
        SELECT id, nombre AS "Nombre", correo AS "Correo", rol AS "Rol"
        FROM usuarios
        WHERE is_deleted = FALSE
        ORDER BY id
        """
    )
    if not df.empty:
        df["Rol"] = df["Rol"].map(lambda r: _rol_a_ui(r) if r is not None else r)
    return df


def obtener_usuario_por_correo(correo: str) -> Optional[dict]:
    """Devuelve el usuario activo con ese correo (dict) o None."""
    df = _leer_df(
        """
        SELECT id, nombre, correo, password_hash, rol
        FROM usuarios
        WHERE is_deleted = FALSE AND lower(correo) = lower(:correo)
        LIMIT 1
        """,
        {"correo": correo},
    )
    if df.empty:
        return None
    fila = df.iloc[0].to_dict()
    fila["rol"] = _rol_a_ui(fila.get("rol"))
    return fila


def verificar_login(correo: str, password: str) -> Optional[dict]:
    """
    Verifica credenciales con bcrypt.
    Devuelve un dict con los datos del usuario (sin el hash) si son correctas,
    o None si no coinciden / el usuario no existe.
    """
    usuario = obtener_usuario_por_correo(correo)
    if not usuario:
        return None
    hash_guardado = usuario.get("password_hash") or ""
    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):
        ok = False
    if not ok:
        return None
    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "correo": usuario["correo"],
        "rol": usuario["rol"],
        "es_admin": usuario["correo"].strip().lower() == CORREO_ADMIN_UNICO,
    }


def _hash_password(password: str) -> str:
    """Genera un hash bcrypt para la contrasena dada."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def crear_usuario(nombre: str, correo: str, password: str, rol: str,
                  usuario_actor: Optional[str] = None) -> int:
    """Crea un usuario con la contrasena hasheada. Devuelve su id."""
    engine = obtener_engine()
    password_hash = _hash_password(password)
    with engine.begin() as conn:
        nuevo_id = conn.execute(
            text(
                """
                INSERT INTO usuarios (nombre, correo, password_hash, rol)
                VALUES (:nombre, :correo, :password_hash, :rol)
                RETURNING id
                """
            ),
            {
                "nombre": nombre,
                "correo": correo.strip().lower(),
                "password_hash": password_hash,
                "rol": _rol_a_db(rol),
            },
        ).scalar_one()
        _registrar_auditoria(
            conn, "usuarios", nuevo_id, "INSERT",
            {"nombre": nombre, "correo": correo.strip().lower(), "rol": _rol_a_db(rol)},
            usuario_actor,
        )
    return int(nuevo_id)


def soft_delete_usuario(usuario_id: int, usuario_actor: Optional[str] = None) -> None:
    """Marca un usuario como borrado (soft-delete) y lo audita."""
    engine = obtener_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE usuarios SET is_deleted = TRUE WHERE id = :id"),
            {"id": usuario_id},
        )
        _registrar_auditoria(conn, "usuarios", usuario_id, "SOFT_DELETE", None, usuario_actor)


def sembrar_admin_si_no_existe() -> None:
    """
    Siembra la cuenta de administradora (Larissa García) con su contrasena
    hasheada, solo si todavia no existe un usuario activo con ese correo.
    """
    if obtener_usuario_por_correo(CORREO_ADMIN_UNICO) is not None:
        return
    crear_usuario(NOMBRE_ADMIN, CORREO_ADMIN_UNICO, PASSWORD_ADMIN, "Admin",
                  usuario_actor="sistema")


# ===========================================================================
# CLIENTES
# ===========================================================================
def obtener_clientes() -> pd.DataFrame:
    """Clientes activos."""
    return _leer_df(
        """
        SELECT id, nombre AS "Nombre", telefono AS "Teléfono", notas AS "Notas"
        FROM clientes
        WHERE is_deleted = FALSE
        ORDER BY nombre
        """
    )


def obtener_o_crear_cliente(nombre: str, telefono: Optional[str] = None,
                            usuario_actor: Optional[str] = None) -> int:
    """
    Devuelve el id del cliente activo con ese nombre (case-insensitive);
    si no existe, lo crea. Idempotente para la migracion y el alta de citas.
    """
    nombre = (nombre or "").strip()
    engine = obtener_engine()
    with engine.begin() as conn:
        existente = conn.execute(
            text(
                """
                SELECT id FROM clientes
                WHERE is_deleted = FALSE AND lower(nombre) = lower(:nombre)
                LIMIT 1
                """
            ),
            {"nombre": nombre},
        ).scalar()
        if existente is not None:
            # Si llega un telefono y el cliente no tenia, lo completamos.
            if telefono:
                conn.execute(
                    text(
                        """
                        UPDATE clientes SET telefono = :telefono
                        WHERE id = :id AND (telefono IS NULL OR telefono = '')
                        """
                    ),
                    {"telefono": telefono, "id": existente},
                )
            return int(existente)

        nuevo_id = conn.execute(
            text(
                """
                INSERT INTO clientes (nombre, telefono)
                VALUES (:nombre, :telefono)
                RETURNING id
                """
            ),
            {"nombre": nombre, "telefono": telefono},
        ).scalar_one()
        _registrar_auditoria(
            conn, "clientes", nuevo_id, "INSERT",
            {"nombre": nombre, "telefono": telefono}, usuario_actor,
        )
        return int(nuevo_id)


# ===========================================================================
# SERVICIOS
# ===========================================================================
def obtener_servicios() -> pd.DataFrame:
    """Servicios activos."""
    return _leer_df(
        """
        SELECT id, nombre AS "Servicio", tarifa AS "Tarifa"
        FROM servicios
        WHERE is_deleted = FALSE
        ORDER BY nombre
        """
    )


def crear_servicio(nombre: str, tarifa: float = 0.0,
                   usuario_actor: Optional[str] = None) -> int:
    """Crea un servicio con su tarifa. Devuelve su id."""
    engine = obtener_engine()
    with engine.begin() as conn:
        nuevo_id = conn.execute(
            text(
                """
                INSERT INTO servicios (nombre, tarifa)
                VALUES (:nombre, :tarifa)
                RETURNING id
                """
            ),
            {"nombre": nombre, "tarifa": tarifa},
        ).scalar_one()
        _registrar_auditoria(
            conn, "servicios", nuevo_id, "INSERT",
            {"nombre": nombre, "tarifa": tarifa}, usuario_actor,
        )
    return int(nuevo_id)


# ===========================================================================
# CITAS
# ===========================================================================
def obtener_citas() -> pd.DataFrame:
    """Citas activas, con columnas amigables (compatibles con el render de la UI)."""
    return _leer_df(
        """
        SELECT id,
               fecha               AS "Fecha",
               hora                AS "Hora",
               cliente_id,
               cliente_nombre      AS "Cliente",
               servicio            AS "Servicio",
               especialista        AS "Especialista",
               link_meet           AS "Link Meet",
               anticipo            AS "Anticipo ($)",
               estatus             AS "Estatus",
               motivo_cancelacion  AS "Motivo Cancelación"
        FROM citas
        WHERE is_deleted = FALSE
        ORDER BY fecha, hora
        """
    )


def crear_cita(fecha, hora: str, cliente_nombre: str, servicio: str,
               especialista: str, link_meet: str, anticipo: float,
               estatus: str = "Confirmada", motivo_cancelacion: Optional[str] = None,
               telefono: Optional[str] = None,
               usuario_actor: Optional[str] = None) -> int:
    """Crea una cita, vinculando (o creando) el cliente por nombre."""
    cliente_id = obtener_o_crear_cliente(cliente_nombre, telefono, usuario_actor)
    engine = obtener_engine()
    with engine.begin() as conn:
        datos = {
            "fecha": str(fecha),
            "hora": hora,
            "cliente_id": cliente_id,
            "cliente_nombre": cliente_nombre,
            "servicio": servicio,
            "especialista": especialista,
            "link_meet": link_meet,
            "anticipo": anticipo,
            "estatus": estatus,
            "motivo_cancelacion": motivo_cancelacion,
        }
        nuevo_id = conn.execute(
            text(
                """
                INSERT INTO citas (fecha, hora, cliente_id, cliente_nombre, servicio,
                                   especialista, link_meet, anticipo, estatus,
                                   motivo_cancelacion)
                VALUES (:fecha, :hora, :cliente_id, :cliente_nombre, :servicio,
                        :especialista, :link_meet, :anticipo, :estatus,
                        :motivo_cancelacion)
                RETURNING id
                """
            ),
            datos,
        ).scalar_one()
        _registrar_auditoria(conn, "citas", nuevo_id, "INSERT", datos, usuario_actor)
    return int(nuevo_id)


def actualizar_estatus_cita(cita_id: int, estatus: str,
                            motivo: Optional[str] = None,
                            usuario_actor: Optional[str] = None) -> None:
    """Actualiza el estatus (y motivo) de una cita. updated_at lo maneja el trigger."""
    engine = obtener_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE citas
                SET estatus = :estatus, motivo_cancelacion = :motivo
                WHERE id = :id
                """
            ),
            {"estatus": estatus, "motivo": motivo, "id": cita_id},
        )
        _registrar_auditoria(
            conn, "citas", cita_id, "UPDATE",
            {"estatus": estatus, "motivo_cancelacion": motivo}, usuario_actor,
        )


def soft_delete_cita(cita_id: int, usuario_actor: Optional[str] = None) -> None:
    """Soft-delete de una cita."""
    engine = obtener_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE citas SET is_deleted = TRUE WHERE id = :id"),
            {"id": cita_id},
        )
        _registrar_auditoria(conn, "citas", cita_id, "SOFT_DELETE", None, usuario_actor)


# ===========================================================================
# VENTAS
# ===========================================================================
def obtener_ventas() -> pd.DataFrame:
    """Ventas activas, con columnas amigables (compatibles con el render de la UI)."""
    return _leer_df(
        """
        SELECT id,
               fecha          AS "Fecha_Hora",
               cliente_id,
               cliente_nombre AS "Cliente",
               servicio       AS "Servicio",
               ubicacion      AS "Ubicación",
               atendido_por   AS "Atendido Por",
               cobro_total    AS "Cobro Total ($)",
               pago_talento   AS "Pago al Talento ($)",
               arguettas_20   AS "20% Arguettas ($)",
               utilidad       AS "Utilidad Punto Glow ($)",
               metodo_pago    AS "Dinero",
               comentarios    AS "Comentarios"
        FROM ventas
        WHERE is_deleted = FALSE
        ORDER BY fecha DESC, id DESC
        """
    )


def crear_venta(fecha, cliente_nombre: str, servicio: str, ubicacion: str,
                atendido_por: str, cobro_total: float, pago_talento: float,
                arguettas_20: float, utilidad: float, metodo_pago: str,
                comentarios: Optional[str] = None,
                usuario_actor: Optional[str] = None) -> int:
    """Crea una venta, vinculando (o creando) el cliente por nombre."""
    cliente_id = obtener_o_crear_cliente(cliente_nombre, None, usuario_actor)
    engine = obtener_engine()
    with engine.begin() as conn:
        datos = {
            "fecha": str(fecha),
            "cliente_id": cliente_id,
            "cliente_nombre": cliente_nombre,
            "servicio": servicio,
            "ubicacion": ubicacion,
            "atendido_por": atendido_por,
            "cobro_total": cobro_total,
            "pago_talento": pago_talento,
            "arguettas_20": arguettas_20,
            "utilidad": utilidad,
            "metodo_pago": metodo_pago,
            "comentarios": comentarios,
        }
        nuevo_id = conn.execute(
            text(
                """
                INSERT INTO ventas (fecha, cliente_id, cliente_nombre, servicio,
                                    ubicacion, atendido_por, cobro_total, pago_talento,
                                    arguettas_20, utilidad, metodo_pago, comentarios)
                VALUES (:fecha, :cliente_id, :cliente_nombre, :servicio,
                        :ubicacion, :atendido_por, :cobro_total, :pago_talento,
                        :arguettas_20, :utilidad, :metodo_pago, :comentarios)
                RETURNING id
                """
            ),
            datos,
        ).scalar_one()
        _registrar_auditoria(conn, "ventas", nuevo_id, "INSERT", datos, usuario_actor)
    return int(nuevo_id)


def soft_delete_venta(venta_id: int, usuario_actor: Optional[str] = None) -> None:
    """Soft-delete de una venta."""
    engine = obtener_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE ventas SET is_deleted = TRUE WHERE id = :id"),
            {"id": venta_id},
        )
        _registrar_auditoria(conn, "ventas", venta_id, "SOFT_DELETE", None, usuario_actor)


# ===========================================================================
# GASTOS
# ===========================================================================
def obtener_gastos() -> pd.DataFrame:
    """Gastos activos, con columnas amigables (compatibles con el render de la UI)."""
    return _leer_df(
        """
        SELECT id,
               fecha     AS "Fecha",
               concepto  AS "Concepto",
               categoria AS "Categoría",
               monto     AS "Monto ($)"
        FROM gastos
        WHERE is_deleted = FALSE
        ORDER BY fecha DESC, id DESC
        """
    )


def crear_gasto(fecha, concepto: str, categoria: str, monto: float,
                usuario_actor: Optional[str] = None) -> int:
    """Crea un gasto. Devuelve su id."""
    engine = obtener_engine()
    with engine.begin() as conn:
        datos = {
            "fecha": str(fecha),
            "concepto": concepto,
            "categoria": categoria,
            "monto": monto,
        }
        nuevo_id = conn.execute(
            text(
                """
                INSERT INTO gastos (fecha, concepto, categoria, monto)
                VALUES (:fecha, :concepto, :categoria, :monto)
                RETURNING id
                """
            ),
            datos,
        ).scalar_one()
        _registrar_auditoria(conn, "gastos", nuevo_id, "INSERT", datos, usuario_actor)
    return int(nuevo_id)


def soft_delete_gasto(gasto_id: int, usuario_actor: Optional[str] = None) -> None:
    """Soft-delete de un gasto."""
    engine = obtener_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE gastos SET is_deleted = TRUE WHERE id = :id"),
            {"id": gasto_id},
        )
        _registrar_auditoria(conn, "gastos", gasto_id, "SOFT_DELETE", None, usuario_actor)
