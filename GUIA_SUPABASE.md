# Guia de configuracion de Supabase - Punto Glow Studio

Esta guia te lleva paso a paso para crear tu base de datos en la nube (gratis),
cargar el esquema y conectar la app de Streamlit de forma segura. No necesitas
saber programar: solo copiar, pegar y seguir los pasos en orden.

---

## 1. Crear cuenta y proyecto gratis en Supabase

1. Entra a [supabase.com](https://supabase.com) y haz clic en **Start your project**.
2. Crea una cuenta (puedes usar tu correo de Google / GitHub).
3. Dentro del panel, haz clic en **New project**.
4. Llena los datos:
   - **Name:** `punto-glow-studio` (o el nombre que prefieras).
   - **Database Password:** elige una contrasena segura y **guardala**, la vas a
     necesitar mas adelante para la cadena de conexion.
   - **Region:** elige la mas cercana a Mexico (por ejemplo *East US* o *West US*).
   - **Plan:** deja seleccionado el plan **Free**.
5. Haz clic en **Create new project** y espera 1-2 minutos a que se aprovisione.

---

## 2. Cargar el esquema (crear las tablas)

1. En el menu lateral del proyecto, abre el **SQL Editor**.
2. Haz clic en **New query**.
3. Abre el archivo `schema.sql` de este proyecto, copia **todo** su contenido y
   pegalo en el editor.
4. Haz clic en **Run** (o presiona `Ctrl + Enter`).
5. Debe aparecer **Success. No rows returned**. Eso significa que las tablas,
   la funcion y los triggers se crearon correctamente.
6. El script es *idempotente*: si lo vuelves a ejecutar, no borra datos ni da
   error, simplemente deja todo como esta.

> Puedes verificar las tablas en el menu lateral **Table Editor**: deberias ver
> `usuarios`, `clientes`, `servicios`, `citas`, `ventas`, `gastos` y `audit_log`.

---

## 3. Obtener la cadena de conexion

1. En el menu lateral, abre **Project Settings** (el engrane).
2. Entra a la seccion **Database**.
3. Busca **Connection string** y selecciona la pestana **URI**.
4. Veras una cadena parecida a esta:

   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```

5. Para que funcione con esta app (que usa SQLAlchemy + psycopg2), hay que
   **convertir el prefijo** `postgresql://` a `postgresql+psycopg2://` y
   reemplazar `[YOUR-PASSWORD]` por la contrasena que elegiste en el paso 1.

   Resultado final (ejemplo):

   ```
   postgresql+psycopg2://postgres:TU_PASSWORD@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```

> Si tu contrasena tiene caracteres especiales (`@`, `:`, `/`, `#`, etc.),
> conviene cambiarla por una que solo tenga letras y numeros, o codificarla,
> para evitar que rompa la cadena de conexion.

---

## 4. Configurar los secrets en tu computadora

1. En la carpeta del proyecto hay un archivo de plantilla:
   `.streamlit/secrets.toml.example`.
2. Haz una **copia** de ese archivo y renombrala a `.streamlit/secrets.toml`
   (sin el `.example`).
3. Abre `.streamlit/secrets.toml` y pega tu cadena de conexion real en el campo
   `db_url`, dentro de la seccion `[supabase]`.
4. Guarda el archivo.

> **IMPORTANTE (seguridad):** el archivo `.streamlit/secrets.toml` contiene tu
> contrasena y **NUNCA** debe subirse a GitHub ni compartirse. Ya esta incluido
> en `.gitignore` para que Git lo ignore. Solo se comparte la plantilla
> `secrets.toml.example`, que no tiene credenciales reales.

---

## 5. Configurar los secrets en Streamlit Community Cloud (al desplegar)

1. Entra a [share.streamlit.io](https://share.streamlit.io) y despliega la app
   desde tu repositorio.
2. En la app desplegada, abre el menu **Settings > Secrets**.
3. Copia y pega el **mismo contenido** de tu `.streamlit/secrets.toml` local
   (la seccion `[supabase]` con tu `db_url`).
4. Guarda. Streamlit Cloud leera esos secrets igual que lo hace en tu
   computadora, sin exponer la contrasena en el codigo.

---

Con esto tu base de datos queda 100% en la nube: los datos no se pierden si
apagas o cambias de laptop, y las credenciales nunca quedan en el codigo.
