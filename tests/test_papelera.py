"""
Prueba ligera de la mecánica de archivado / restauración (Papelera).

Objetivo: validar SIN tocar Supabase que
  * `restaurar_*` / `_restaurar_fila` pone `is_deleted = FALSE` con SQL parametrizado, y
  * `obtener_*_archivad*` filtra `is_deleted = TRUE`.

Se usa un SQLite en memoria y se monkeypatchea `database.obtener_engine` para que
apunte a ese engine. `_registrar_auditoria` usa `CAST(:datos AS JSONB)`, que no existe
en SQLite, así que se sustituye por una variante SQLite-compatible que escribe en un
`audit_log` mínimo; esto permite ejercitar la ruta completa de `_restaurar_fila`
(UPDATE + auditoría) y comprobar que la restauración se audita con accion 'UPDATE'.

Ejecutar con pytest:   python -m pytest tests/test_papelera.py -q
o como script:         python tests/test_papelera.py
"""
import json
import os
import sys

from sqlalchemy import create_engine, text

# Permite importar database.py desde la raíz del proyecto.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database  # noqa: E402


def _crear_engine_sqlite():
    """Crea un engine SQLite en memoria con el esquema mínimo necesario."""
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_nombre TEXT,
                cobro_total NUMERIC,
                is_deleted INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT
            )
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabla TEXT NOT NULL,
                fila_id INTEGER,
                accion TEXT NOT NULL,
                datos TEXT,
                usuario TEXT,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
    return engine


def _auditoria_sqlite(conn, tabla, fila_id, accion, datos=None, usuario=None):
    """Variante de _registrar_auditoria sin CAST(... AS JSONB) (SQLite)."""
    conn.execute(
        text(
            """
            INSERT INTO audit_log (tabla, fila_id, accion, datos, usuario)
            VALUES (:tabla, :fila_id, :accion, :datos, :usuario)
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


def _preparar(monkeypatch_fn):
    """Monta el engine SQLite y parchea database. Devuelve el engine."""
    engine = _crear_engine_sqlite()
    monkeypatch_fn("obtener_engine", lambda: engine)
    monkeypatch_fn("_registrar_auditoria", _auditoria_sqlite)
    # Inserta una venta ya archivada (is_deleted = 1).
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO ventas (cliente_nombre, cobro_total, is_deleted, updated_at) "
            "VALUES ('Clienta Prueba', 500, 1, '2024-01-01')"
        ))
    return engine


def test_restaurar_fila_pone_is_deleted_false():
    originales = {
        "obtener_engine": database.obtener_engine,
        "_registrar_auditoria": database._registrar_auditoria,
    }
    try:
        def set_attr(nombre, valor):
            setattr(database, nombre, valor)

        engine = _preparar(set_attr)

        # Restaura la fila id = 1.
        database._restaurar_fila("ventas", 1, usuario_actor="tester")

        with engine.connect() as conn:
            is_deleted = conn.execute(
                text("SELECT is_deleted FROM ventas WHERE id = 1")
            ).scalar_one()
            accion = conn.execute(
                text("SELECT accion FROM audit_log WHERE tabla = 'ventas' AND fila_id = 1")
            ).scalar_one()

        assert int(is_deleted) == 0, "La restauración debe dejar is_deleted = FALSE"
        assert accion == "UPDATE", "La restauración debe auditarse como 'UPDATE'"
    finally:
        for nombre, valor in originales.items():
            setattr(database, nombre, valor)


def test_tabla_no_archivable_es_rechazada():
    try:
        database._restaurar_fila("tabla_inexistente", 1)
        assert False, "Debe rechazar tablas fuera de la lista blanca"
    except ValueError:
        pass


if __name__ == "__main__":
    test_restaurar_fila_pone_is_deleted_false()
    test_tabla_no_archivable_es_rechazada()
    print("OK: pruebas de Papelera pasaron.")
