# Punto Glow Beauty Management Studio ✨

Sistema de gestión integral para **Punto Glow Studio**: citas, servicios, ventas
(ingresos), gastos (egresos), clientes y usuarios. Construido con **Streamlit** y
**PostgreSQL en la nube (Supabase)**.

La información **nunca se borra físicamente ni se pierde** si tu laptop se apaga,
falla o cambias de equipo: todo vive en Supabase con **borrado lógico (soft delete)**
y una **bitácora de auditoría** (`audit_log`) que registra cada alta, cambio y borrado.

---

## ✨ Características

- **Dashboard** con 4 KPIs (ventas de hoy, cobro del mes, gastos del mes y utilidad
  neta con margen), gráfico de los últimos 7 días y citas del día.
- **Ventas (Ingresos)** con desglose de pago al talento, 20% Arguettas y utilidad.
- **Gastos (Egresos)** por categoría.
- **Agenda & Meet**: citas con conversión directa a venta, control de estatus,
  enlace de Google Calendar y notificación por **WhatsApp** al número fijo del estudio.
- **Cierres de Caja** y exportación a **Excel** (3 hojas).
- **Gestión de Usuarios** (solo Admin) con contraseñas **bcrypt**.
- **Sesión diaria persistente** ("recordar durante el día").

---

## 1. Requisitos

- Python 3.10 o superior.
- Instalar dependencias:

```bash
pip install -r requirements.txt
```

Dependencias principales: `streamlit`, `pandas`, `plotly`, `xlsxwriter`,
`streamlit-option-menu`, `sqlalchemy`, `psycopg2-binary`, `bcrypt`.

---

## 2. Configurar la base de datos (Supabase)

Sigue la guía detallada en **[GUIA_SUPABASE.md](GUIA_SUPABASE.md)**. En resumen:

1. Crea una cuenta y un proyecto gratis en [supabase.com](https://supabase.com).
2. Abre el **SQL Editor** y ejecuta el contenido de **`schema.sql`** (crea las 7 tablas
   con soft-delete, auditoría y triggers; es idempotente, puedes correrlo varias veces).
3. Obtén la **cadena de conexión** (Project Settings → Database → Connection string).

### Configurar los secrets

Copia la plantilla y renómbrala:

```
.streamlit/secrets.toml.example  ->  .streamlit/secrets.toml
```

Y edita `.streamlit/secrets.toml` con tu cadena real:

```toml
[supabase]
db_url = "postgresql+psycopg2://postgres:TU_PASSWORD@TU_HOST:5432/postgres"
```

> ⚠️ **Nunca** subas `secrets.toml` a GitHub. Ya está en `.gitignore`.

---

## 3. Migrar los datos actuales (una sola vez)

Si ya tienes datos en los CSV locales (`usuarios_punto_glow.csv`,
`citas_punto_glow.csv`, `ventas_punto_glow.csv`, `gastos_punto_glow.csv`), impórtalos
a Supabase con:

```bash
python migrar_csv_a_supabase.py
```

El script:
- Hashea las contraseñas con bcrypt.
- Crea/vincula clientes por nombre.
- Es **idempotente**: puedes correrlo más de una vez sin duplicar registros.
- Tolera marcadores de conflicto de Git residuales en los CSV.

---

## 4. Levantar la aplicación

```bash
streamlit run app.py
```

Ingresa con la cuenta de administradora (correo `garcialarissa1292@gmail.com` y la
contraseña definida en los usuarios migrados).

> El archivo `app_punto_glow_studio.py` se conserva **intacto como respaldo** de la
> versión anterior basada en CSV. La versión activa y en la nube es `app.py`.

---

## 5. Desplegar en Streamlit Community Cloud

1. Sube el repositorio a GitHub (sin `secrets.toml`).
2. En [share.streamlit.io](https://share.streamlit.io) crea una nueva app apuntando a
   `app.py`.
3. En **Settings → Secrets** pega el mismo contenido de tu `.streamlit/secrets.toml`:

   ```toml
   [supabase]
   db_url = "postgresql+psycopg2://postgres:TU_PASSWORD@TU_HOST:5432/postgres"
   ```

4. Guarda y la app quedará conectada a tu base de datos en Supabase.

---

## Estructura del proyecto

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Aplicación Streamlit (versión en la nube, activa). |
| `database.py` | Capa de datos (SQLAlchemy + Supabase, soft-delete, auditoría, bcrypt). |
| `schema.sql` | Esquema PostgreSQL idempotente para Supabase. |
| `migrar_csv_a_supabase.py` | Migración única de los CSV a Supabase. |
| `GUIA_SUPABASE.md` | Guía paso a paso de configuración de Supabase. |
| `.streamlit/secrets.toml.example` | Plantilla de credenciales. |
| `app_punto_glow_studio.py` | Respaldo de la versión anterior (CSV). |

---

## Seguridad y persistencia

- **Credenciales** solo en `st.secrets` (`.streamlit/secrets.toml`), nunca en el código.
- **Contraseñas** con hash **bcrypt**.
- **Soft delete**: borrar marca `is_deleted = TRUE`; nunca se ejecuta un `DELETE` físico.
- **Auditoría**: cada `INSERT`/`UPDATE`/`SOFT_DELETE` se registra en `audit_log` con
  `created_at`/`updated_at` mantenidos por triggers.
