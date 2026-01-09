import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIGURACIÓN ----------------
st.set_page_config(
    page_title="Inscripción Instructores TRA",
    layout="centered"
)

ANIO_PERMITIDO = 2026
CUPO_MAXIMO = 2

# ---------------- ARCHIVOS LOCALES ----------------
ARCHIVO_INSTRUCTORES = "Clasificación de Instructores.csv"
ARCHIVO_CURSOS = "Planificación Cursos TRA (3).csv"

# ---------------- GOOGLE SHEETS ----------------
# Ruta al JSON de credenciales del Service Account
CREDENCIALES_JSON = "service_account.json"
# ID del Google Sheet
GOOGLE_SHEET_ID = "TU_GOOGLE_SHEET_ID"

# Autenticación
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(CREDENCIALES_JSON, scopes=scopes)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(GOOGLE_SHEET_ID)
try:
    worksheet = sheet.worksheet("Inscripciones")
except gspread.WorksheetNotFound:
    worksheet = sheet.add_worksheet(title="Inscripciones", rows="100", cols="10")
    worksheet.append_row(["Instructor","Curso","Teórico Virtual (inicio)","Instancia Presencial (inicio)"])

# ---------------- FUNCIONES ----------------
@st.cache_data
def cargar_datos():
    instructores = pd.read_csv(ARCHIVO_INSTRUCTORES)
    cursos = pd.read_csv(ARCHIVO_CURSOS)

    # Normalizar columnas
    instructores.columns = instructores.columns.str.strip()
    cursos.columns = cursos.columns.str.strip()

    instructores["Instructor"] = instructores["Instructor"].astype(str).str.strip()
    instructores["Cursos"] = instructores["Cursos"].astype(str).str.strip()
    cursos["Nombre corto"] = cursos["Nombre corto"].astype(str).str.strip()

    # Limpiar año
    if "Año" in cursos.columns:
        cursos["Año"] = pd.to_numeric(cursos["Año"], errors="coerce")

    return instructores, cursos

def cargar_inscripciones():
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def guardar_inscripcion(df):
    worksheet.clear()
    worksheet.append_row(list(df.columns))
    for _, row in df.iterrows():
        worksheet.append_row(list(row))

# ---------------- APP ----------------
instructores_df, cursos_df = cargar_datos()
inscripciones_df = cargar_inscripciones()

st.title("📋 Inscripción de Instructores – Cursos TRA")

# ---------------- FORMULARIO 1 ----------------
with st.form("form_seleccion"):
    instructor = st.selectbox(
        "Seleccione su nombre",
        sorted(instructores_df["Instructor"].dropna().unique())
    )
    ver_cursos = st.form_submit_button("Ver cursos disponibles")

# ---------------- LÓGICA ----------------
if ver_cursos:
    # Cursos habilitados para el instructor
    cursos_habilitados = (
        instructores_df[instructores_df["Instructor"] == instructor]["Cursos"]
        .dropna()
        .unique()
    )

    if len(cursos_habilitados) == 0:
        st.warning("⚠️ No hay cursos asociados a este instructor.")
        st.stop()

    # Filtrar cursos 2026
    cursos_2026 = cursos_df[
        (cursos_df["Nombre corto"].isin(cursos_habilitados)) &
        ("Año" in cursos_df.columns) &
        (cursos_df["Año"] == ANIO_PERMITIDO)
    ].reset_index(drop=True)

    if cursos_2026.empty:
        st.info("ℹ️ No hay instancias planificadas para el año 2026.")
        st.stop()

    st.success("Instancias disponibles")

    # ---------------- FORMULARIO 2 ----------------
    with st.form("form_inscripcion"):
        opciones = []
        for _, row in cursos_2026.iterrows():
            opciones.append(
                f"{row['Nombre corto']} | "
                f"Virtual: {row.get('Teórico Virtual (inicio)', '—')} | "
                f"Presencial: {row.get('Instancia Presencial (inicio)', '—')}"
            )

        opcion = st.selectbox("Seleccione la instancia", opciones)
        confirmar = st.form_submit_button("Confirmar inscripción")

    if confirmar:
        idx = opciones.index(opcion)
        instancia = cursos_2026.loc[idx]

        # Validar cupo
        insc = inscripciones_df[
            (inscripciones_df["Curso"] == instancia["Nombre corto"]) &
            (inscripciones_df["Teórico Virtual (inicio)"] == instancia.get("Teórico Virtual (inicio)", "")) &
            (inscripciones_df["Instancia Presencial (inicio)"] == instancia.get("Instancia Presencial (inicio)", ""))
        ]

        if len(insc) >= CUPO_MAXIMO:
            st.error("❌ Cupo completo para esta instancia.")
            st.stop()

        # Evitar doble inscripción
        ya_inscripto = inscripciones_df[
            (inscripciones_df["Instructor"] == instructor) &
            (inscripciones_df["Curso"] == instancia["Nombre corto"])
        ]
        if not ya_inscripto.empty:
            st.error("❌ Ya estás inscripto en este curso.")
            st.stop()

        # Guardar inscripción
        nueva = pd.DataFrame([{
            "Instructor": instructor,
            "Curso": instancia["Nombre corto"],
            "Teórico Virtual (inicio)": instancia.get("Teórico Virtual (inicio)", ""),
            "Instancia Presencial (inicio)": instancia.get("Instancia Presencial (inicio)", "")
        }])

        inscripciones_df = pd.concat([inscripciones_df, nueva], ignore_index=True)
        guardar_inscripcion(inscripciones_df)

        st.success(f"✅ Inscripción confirmada. Guardada en Google Sheet.")

# ---------------- TABLA DE INSCRIPCIONES ----------------
st.subheader("📄 Inscripciones actuales")
st.dataframe(inscripciones_df)

# ---------------- OPCIÓN DE DESCARGA ----------------
csv = inscripciones_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar CSV de inscripciones",
    data=csv,
    file_name="inscripciones.csv",
    mime="text/csv"
)
