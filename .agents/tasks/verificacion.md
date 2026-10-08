# Verificación — Refactor Supabase (Punto Glow Studio)

Fecha: iteración 1. Entorno: Windows / PowerShell / Python 3.14. **Sin credenciales
reales de Supabase**, por lo que NO se conectó a la base de datos: la verificación se
hizo con compilación, coherencia con `schema.sql` y pruebas ligeras con SQLite + mocks.

## 1. Compilación (sintaxis)

Comando:

```
python -m py_compile app.py database.py migrar_csv_a_supabase.py
```

Salida: `EXIT=0` (sin errores de sintaxis en los tres archivos).

## 2. Prueba ligera de `database.py` (SQLite en memoria + mock de streamlit)

Se parcheó `obtener_engine()` para apuntar a `sqlite://` y se mockeó `st.secrets` /
`st.cache_resource`. Resultado: **`OK: todas las pruebas ligeras de database.py pasaron.`**

Casos verificados:
- `verificar_login` con contraseña **correcta** → devuelve el dict del admin (`es_admin=True`).
- `verificar_login` con contraseña **incorrecta** → `None`.
- `verificar_login` con usuario **inexistente** → `None`.
- `sembrar_admin_si_no_existe()` es **idempotente** (no duplica el admin al correrlo 2 veces).
- `crear_usuario(..., "Recepción")` guarda **`Recepcion`** (sin acento) en la columna `rol`
  para cumplir el CHECK de `schema.sql`, y `obtener_usuarios()` lo muestra como **`Recepción`** en la UI.
- `soft_delete_usuario` deja la fila con **`is_deleted = TRUE`** (no la borra físicamente) y
  `obtener_usuarios()` ya **no** la muestra (filtra `WHERE is_deleted = FALSE`).
- `obtener_o_crear_cliente` es **idempotente** y case-insensitive.
- `audit_log` registra acciones **INSERT** y **SOFT_DELETE**.

> Nota: en SQLite se neutralizó el `CAST(:datos AS JSONB)` (propio de PostgreSQL) solo
> para la prueba. En Supabase/PostgreSQL ese cast es válido y necesario para `audit_log.datos JSONB`.

## 3. Prueba ligera del parser de `migrar_csv_a_supabase.py`

Resultado: **`OK: parser de CSV ignora marcadores de conflicto y helpers funcionan.`**

Casos verificados:
- `leer_csv` **salta** líneas con marcadores de conflicto de Git (`<<<<<<<`, `=======`,
  `>>>>>>>`) y filas vacías; parsea correctamente 1 usuario real.
- `_a_float("$1,500.00") == 1500.0`; maneja vacío/`None` → `0.0`.
- `_texto` recorta espacios y normaliza `""`/`None`/`nan` a cadena vacía (conserva `N/A`
  literal donde aplica, p. ej. `Link Meet`).

## 4. Revisiones estáticas (grep/lectura)

- **Sin credenciales hardcodeadas de infraestructura**: `database.py` lee la conexión
  **solo** de `st.secrets["supabase"]["db_url"]`. No hay cadenas `postgresql+psycopg2://`
  embebidas. (La constante `PASSWORD_ADMIN` es la contraseña de **login de la app** de la
  administradora, tomada del CSV autoritativo, que se **hashea con bcrypt** antes de
  guardarse mediante `sembrar_admin_si_no_existe()`; no es una credencial de servicio.)
- **Sin borrados físicos en `app.py`**: no hay `df.drop(...)` ni `DELETE`; todas las
  operaciones de "borrar" usan `db.soft_delete_*` (que hace `UPDATE ... is_deleted = TRUE`).
- **WhatsApp arreglado**: existe un **único** helper `crear_link_wa(mensaje)` que arma
  `https://wa.me/5215530350615?text=<urlencoded>` con el número **FIJO** `WHATSAPP_FIJO`.
  No se usa el número por-cliente ni el formato viejo `api.whatsapp.com`. Se usa en el flujo
  de confirmación de cita (Agenda & Meet).
- **Coherencia con `schema.sql`**: `database.py` y `migrar_csv_a_supabase.py` usan
  exactamente los nombres de tabla/columna del esquema (usuarios, clientes, servicios,
  citas, ventas, gastos, audit_log). El `rol` se normaliza a `Recepcion` (sin acento) para
  el CHECK; `updated_at` lo mantiene el trigger (no se escribe manualmente).

## 5. Lógica de negocio preservada (revisión de `app.py`)

- Sedes `Santa Fe / Arguettas / A domicilio`; `20% Arguettas = cobro*0.20` solo si sede
  Arguettas; `utilidad = cobro - talento - 20%`.
- Zona horaria `America/Mexico_City`; métodos de pago y categorías de gasto idénticos.
- UI/CSS (paleta #F089AB/#000000, fuentes Bodoni Moda/Great Vibes/Josefin Sans), sidebar
  con `option_menu`, banner + reloj CDMX + Exportar Excel (xlsxwriter, 3 hojas), 3 modales
  `st.dialog`, dashboard (4 KPIs + Plotly 7 días + citas de hoy), conversión Cita→Venta,
  Google Calendar (is.gd/tinyurl). Se añadió un bloque `@media (max-width:640px)` para móvil.
- Lecturas con `@st.cache_data(ttl=60)` e **invalidación** (`st.cache_data.clear()` vía
  `invalidar_cache()`) después de cada escritura/soft-delete.
- `app_punto_glow_studio.py` se dejó **intacto** como respaldo.

## 6. Qué le queda por probar a la usuaria con su Supabase

El entorno de desarrollo no tiene credenciales de Supabase, así que estos pasos (que
requieren la base real) quedan para la usuaria:

1. Crear el proyecto en Supabase y correr `schema.sql` en el SQL Editor (ver `GUIA_SUPABASE.md`).
2. Copiar `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` y pegar su `db_url` real.
3. Ejecutar la migración una vez: `python migrar_csv_a_supabase.py`
   (debe crear el admin, 1 cita de Sofía Mendoza, 1 venta y vincular al cliente).
4. Levantar la app: `streamlit run app.py` e iniciar sesión con
   `garcialarissa1292@gmail.com` / `Lariliz1*`.
5. Verificar en Supabase que "borrar" marca `is_deleted = TRUE` y que `audit_log` crece.
