"""
Punto Glow Studio - Migración de CSV a Supabase/PostgreSQL
==========================================================

Script STANDALONE que lee los CSV actuales de la app y los inserta en Supabase
usando la capa de datos database.py.

Características:
  * Tolera marcadores de conflicto de Git residuales en los CSV (salta las
    líneas que empiezan con <<<<<<<, ======= o >>>>>>>).
  * Hashea las contraseñas de usuarios con bcrypt (vía database.crear_usuario).
  * Crea/vincula clientes por nombre con obtener_o_crear_cliente.
  * Es IDEMPOTENTE: si se corre dos veces no duplica registros (comprueba la
    existencia por claves naturales antes de insertar).

Uso:
    python migrar_csv_a_supabase.py

Requisitos:
  * .streamlit/secrets.toml con la sección [supabase] y la clave db_url
    (database.py lee la conexión desde ahí vía st.secrets).
  * Haber ejecutado schema.sql en Supabase (ver GUIA_SUPABASE.md).
"""
from __future__ import annotations

import csv
import io
import os
from typing import Iterator

from sqlalchemy import text

import database as db

# Archivos CSV de origen.
FILE_USUARIOS = "usuarios_punto_glow.csv"
FILE_CITAS = "citas_punto_glow.csv"
FILE_VENTAS = "ventas_punto_glow.csv"
FILE_GASTOS = "gastos_punto_glow.csv"

MARCADORES_CONFLICTO = ("<<<<<<<", "=======", ">>>>>>>")


# ---------------------------------------------------------------------------
# Lectura tolerante a marcadores de conflicto de Git
# ---------------------------------------------------------------------------
def _lineas_limpias(ruta: str) -> Iterator[str]:
    """Devuelve las líneas del archivo saltando los marcadores de conflicto de Git."""
    with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
        for linea in f:
            if linea.lstrip().startswith(MARCADORES_CONFLICTO):
                continue
            yield linea


def leer_csv(ruta: str) -> list[dict]:
    """Lee un CSV (ignorando marcadores de conflicto) y devuelve una lista de dicts."""
    if not os.path.exists(ruta):
        print(f"  [aviso] No existe {ruta}; se omite.")
        return []
    contenido = "".join(_lineas_limpias(ruta))
    lector = csv.DictReader(io.StringIO(contenido))
    filas = []
    for fila in lector:
        # Salta filas totalmente vacías.
        if not any((v or "").strip() for v in fila.values()):
            continue
        filas.append(fila)
    return filas


def _a_float(valor, defecto: float = 0.0) -> float:
    """Convierte a float de forma segura."""
    try:
        if valor is None or str(valor).strip() == "":
            return defecto
        return float(str(valor).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return defecto


def _texto(valor, defecto: str = "") -> str:
    """Normaliza texto; convierte 'N/A'/vacío a defecto."""
    if valor is None:
        return defecto
    s = str(valor).strip()
    if s == "" or s.lower() == "nan":
        return defecto
    return s


# ---------------------------------------------------------------------------
# Helpers de idempotencia (consultas directas por clave natural)
# ---------------------------------------------------------------------------
def _existe(sql: str, params: dict) -> bool:
    engine = db.obtener_engine()
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar() is not None


def _existe_cita(fecha, hora, cliente) -> bool:
    return _existe(
        """
        SELECT 1 FROM citas
        WHERE fecha = :fecha AND hora = :hora
          AND lower(cliente_nombre) = lower(:cliente) AND is_deleted = FALSE
        LIMIT 1
        """,
        {"fecha": str(fecha), "hora": hora, "cliente": cliente},
    )


def _existe_venta(fecha, cliente, cobro_total) -> bool:
    return _existe(
        """
        SELECT 1 FROM ventas
        WHERE fecha = :fecha AND lower(cliente_nombre) = lower(:cliente)
          AND cobro_total = :cobro AND is_deleted = FALSE
        LIMIT 1
        """,
        {"fecha": str(fecha), "cliente": cliente, "cobro": cobro_total},
    )


def _existe_gasto(fecha, concepto, monto) -> bool:
    return _existe(
        """
        SELECT 1 FROM gastos
        WHERE fecha = :fecha AND lower(concepto) = lower(:concepto)
          AND monto = :monto AND is_deleted = FALSE
        LIMIT 1
        """,
        {"fecha": str(fecha), "concepto": concepto, "monto": monto},
    )


# ---------------------------------------------------------------------------
# Migraciones por entidad
# ---------------------------------------------------------------------------
def migrar_usuarios() -> None:
    print("» Migrando usuarios...")
    # Garantiza la cuenta de administradora (bcrypt) aunque el CSV no la tenga.
    db.sembrar_admin_si_no_existe()

    for fila in leer_csv(FILE_USUARIOS):
        nombre = _texto(fila.get("Nombre"))
        correo = _texto(fila.get("Correo")).lower()
        password = _texto(fila.get("Password"))
        rol = _texto(fila.get("Rol"), "Especialista")
        if not correo or not password:
            continue
        if db.obtener_usuario_por_correo(correo) is not None:
            print(f"  = usuario ya existe: {correo}")
            continue
        db.crear_usuario(nombre, correo, password, rol, usuario_actor="migracion")
        print(f"  + usuario creado: {correo}")


def migrar_citas() -> None:
    print("» Migrando citas...")
    for fila in leer_csv(FILE_CITAS):
        cliente = _texto(fila.get("Cliente"))
        fecha = _texto(fila.get("Fecha"))
        hora = _texto(fila.get("Hora"))
        if not cliente or not fecha or not hora:
            continue
        if _existe_cita(fecha, hora, cliente):
            print(f"  = cita ya existe: {cliente} {fecha} {hora}")
            continue
        telefono = _texto(fila.get("Tel_Cliente")) or None
        estatus = _texto(fila.get("Estatus"), "Confirmada")
        db.crear_cita(
            fecha=fecha,
            hora=hora,
            cliente_nombre=cliente,
            servicio=_texto(fila.get("Servicio")),
            especialista=_texto(fila.get("Especialista"), "Por asignar"),
            link_meet=_texto(fila.get("Link Meet"), "N/A"),
            anticipo=_a_float(fila.get("Anticipo ($)")),
            estatus=estatus if estatus in ("Confirmada", "Cancelada") else "Confirmada",
            motivo_cancelacion=_texto(fila.get("Motivo Cancelación")) or None,
            telefono=telefono,
            usuario_actor="migracion",
        )
        print(f"  + cita creada: {cliente} {fecha} {hora}")


def migrar_ventas() -> None:
    print("» Migrando ventas...")
    for fila in leer_csv(FILE_VENTAS):
        cliente = _texto(fila.get("Cliente"))
        fecha = _texto(fila.get("Fecha_Hora"))
        if not cliente or not fecha:
            continue
        cobro_total = _a_float(fila.get("Cobro Total ($)"))
        if _existe_venta(fecha, cliente, cobro_total):
            print(f"  = venta ya existe: {cliente} {fecha} ${cobro_total:,.2f}")
            continue
        db.crear_venta(
            fecha=fecha,
            cliente_nombre=cliente,
            servicio=_texto(fila.get("Servicio")),
            ubicacion=_texto(fila.get("Ubicación"), "Santa Fe"),
            atendido_por=_texto(fila.get("Atendido Por")),
            cobro_total=cobro_total,
            pago_talento=_a_float(fila.get("Pago al Talento ($)")),
            arguettas_20=_a_float(fila.get("20% Arguettas ($)")),
            utilidad=_a_float(fila.get("Utilidad Punto Glow ($)")),
            metodo_pago=_texto(fila.get("Dinero")),
            comentarios=_texto(fila.get("Comentarios")) or None,
            usuario_actor="migracion",
        )
        print(f"  + venta creada: {cliente} {fecha} ${cobro_total:,.2f}")


def migrar_gastos() -> None:
    print("» Migrando gastos...")
    for fila in leer_csv(FILE_GASTOS):
        concepto = _texto(fila.get("Concepto"))
        fecha = _texto(fila.get("Fecha"))
        if not concepto or not fecha:
            continue
        monto = _a_float(fila.get("Monto ($)"))
        if _existe_gasto(fecha, concepto, monto):
            print(f"  = gasto ya existe: {concepto} {fecha} ${monto:,.2f}")
            continue
        db.crear_gasto(
            fecha=fecha,
            concepto=concepto,
            categoria=_texto(fila.get("Categoría"), "Otros Egresos"),
            monto=monto,
            usuario_actor="migracion",
        )
        print(f"  + gasto creado: {concepto} {fecha} ${monto:,.2f}")


def main() -> None:
    print("=" * 60)
    print("Migración de CSV -> Supabase (Punto Glow Studio)")
    print("=" * 60)
    migrar_usuarios()
    migrar_citas()
    migrar_ventas()
    migrar_gastos()
    print("-" * 60)
    print("✓ Migración finalizada. Puedes re-ejecutar este script sin duplicar datos.")


if __name__ == "__main__":
    main()
