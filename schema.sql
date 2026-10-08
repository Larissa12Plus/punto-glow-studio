-- =====================================================================
-- Punto Glow Studio - Esquema de base de datos (PostgreSQL / Supabase)
-- =====================================================================
-- Diseno:
--   * Soft-delete en todas las tablas de datos (is_deleted BOOLEAN).
--   * Auditoria de tiempos: created_at / updated_at en cada tabla de datos.
--   * Trigger BEFORE UPDATE que mantiene updated_at al dia.
--   * Tabla audit_log para historial de transacciones.
--   * Script IDEMPOTENTE: se puede ejecutar varias veces sin error.
--
-- Ejecutar en: Supabase -> SQL Editor -> pegar y Run.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. USUARIOS (acceso a la app; passwords con bcrypt desde la app)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id            BIGSERIAL PRIMARY KEY,
    nombre        TEXT NOT NULL,
    correo        TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol           TEXT CHECK (rol IN ('Admin', 'Especialista', 'Recepcion')),
    is_deleted    BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 2. CLIENTES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id         BIGSERIAL PRIMARY KEY,
    nombre     TEXT NOT NULL,
    telefono   TEXT,
    notas      TEXT,
    is_deleted BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 3. SERVICIOS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS servicios (
    id         BIGSERIAL PRIMARY KEY,
    nombre     TEXT NOT NULL,
    tarifa     NUMERIC(10, 2) DEFAULT 0,
    is_deleted BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 4. CITAS (agenda)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS citas (
    id                  BIGSERIAL PRIMARY KEY,
    fecha               DATE NOT NULL,
    hora                TEXT NOT NULL,
    cliente_id          BIGINT REFERENCES clientes(id),
    cliente_nombre      TEXT,
    servicio            TEXT,
    especialista        TEXT,
    link_meet           TEXT,
    anticipo            NUMERIC(10, 2) DEFAULT 0,
    estatus             TEXT CHECK (estatus IN ('Confirmada', 'Cancelada')),
    motivo_cancelacion  TEXT,
    is_deleted          BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 5. VENTAS (ingresos)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ventas (
    id             BIGSERIAL PRIMARY KEY,
    fecha          DATE NOT NULL,
    cliente_id     BIGINT REFERENCES clientes(id),
    cliente_nombre TEXT,
    servicio       TEXT,
    ubicacion      TEXT CHECK (ubicacion IN ('Santa Fe', 'Arguettas', 'A domicilio')),
    atendido_por   TEXT,
    cobro_total    NUMERIC(10, 2),
    pago_talento   NUMERIC(10, 2),
    arguettas_20   NUMERIC(10, 2),
    utilidad       NUMERIC(10, 2),
    metodo_pago    TEXT,
    comentarios    TEXT,
    is_deleted     BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 6. GASTOS (egresos)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gastos (
    id         BIGSERIAL PRIMARY KEY,
    fecha      DATE NOT NULL,
    concepto   TEXT NOT NULL,
    categoria  TEXT,
    monto      NUMERIC(10, 2),
    is_deleted BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 7. AUDIT_LOG (historial de transacciones / integridad)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id        BIGSERIAL PRIMARY KEY,
    tabla     TEXT NOT NULL,
    fila_id   BIGINT,
    accion    TEXT NOT NULL CHECK (accion IN ('INSERT', 'UPDATE', 'SOFT_DELETE')),
    datos     JSONB,
    usuario   TEXT,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- FUNCION + TRIGGERS: mantener updated_at automaticamente
-- =====================================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Un trigger BEFORE UPDATE por cada tabla de datos.
DROP TRIGGER IF EXISTS trg_usuarios_updated_at ON usuarios;
CREATE TRIGGER trg_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_clientes_updated_at ON clientes;
CREATE TRIGGER trg_clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_servicios_updated_at ON servicios;
CREATE TRIGGER trg_servicios_updated_at
    BEFORE UPDATE ON servicios
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_citas_updated_at ON citas;
CREATE TRIGGER trg_citas_updated_at
    BEFORE UPDATE ON citas
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_ventas_updated_at ON ventas;
CREATE TRIGGER trg_ventas_updated_at
    BEFORE UPDATE ON ventas
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_gastos_updated_at ON gastos;
CREATE TRIGGER trg_gastos_updated_at
    BEFORE UPDATE ON gastos
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =====================================================================
-- INDICES
-- =====================================================================
-- Unicidad por nombre (case-insensitive) solo entre registros activos.
CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_nombre_activo
    ON clientes (lower(nombre))
    WHERE is_deleted = FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS idx_servicios_nombre_activo
    ON servicios (lower(nombre))
    WHERE is_deleted = FALSE;

-- Indices por fecha para consultas de agenda y reportes.
CREATE INDEX IF NOT EXISTS idx_citas_fecha  ON citas (fecha);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas (fecha);
