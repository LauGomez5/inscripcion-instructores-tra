import streamlit as st
import pandas as pd
import unicodedata

# ===============================
# CONFIGURACIÓN
# ===============================
CUPO_MAX = 2
ANIO_PERMITIDO = 2026

st.set_page_config(page_title="Inscripción Instructores TRA", layout="centered")
st.title("📋 Inscripción de Instructores – Cursos TRA")

# ===============================
# FUNCIONES
# ===============================

def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto)
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.upper().strip()

# ===============================
# CARGA DE DATOS
# ===============================

@st.cache_data
def cargar_datos():
    instructores = pd.read_csv("Clasificación de Instructores.csv")
    cursos = pd.read_csv("Planificación Cursos TRA (3).csv")

    # Instructor
    instructores["Instructor"] = instructores["Instructor"].astype(str).str.strip()
    instructores["Instructor_key"] = instructores["Instructor"].apply(normalizar)

    # Cursos asociados (lista)
    instructores["Cursos"] = (
        instructores["Cursos"]
        .astype(str)
        .str.replace(";", ",")
        .str.replace("/", ",")
        .str.split(",")
    )

    # Cursos planificación
    cursos["Nombre corto"] = cursos["Nombre corto"].astype(str).str.strip()

    if "AÑO" in cursos.columns:
        cursos["AÑO_LIMPIO"] = (
            cursos["AÑO"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )
    else:
        cursos["AÑO_LIMPIO"] = None

    return instructores, cursos


instructores, cursos = cargar_datos()

# ===============================
# INSCRIPCIONES
# ===============================

try:
    inscripciones = pd.read_csv("inscripciones.csv")
except FileNotFoundError:
    inscripciones = pd.DataFrame(columns=[
        "Instructor",
        "Curso",
        "Teórico Virtual (inicio)",
        "Instancia Presencial (inicio)"
    ])

# ===============================
# FORMULARIO
# ===============================

with st.form("form_inscripcion"):

    nombres = sorted(instructores["Instructor"].unique())
    instructor = st.selectbox("👤 Seleccione su nombre", nombres)

    instructor_key = normalizar(instructor)

    cursos_habilitados = (
        instructores[instructores["Instructor_key"] == instructor_key]
        .explode("Cursos")["Cursos"]
        .str.strip()
        .unique()
    )

    curso = st.selectbox(
        "📘 Seleccione el curso",
        sorted(cursos_habilitados)
    )

    instancias = cursos[
        (cursos["Nombre corto"] == curso) &
        (cursos["AÑO_LIMPIO"] == ANIO_PERMITIDO)
    ].reset_index(drop=True)

    opciones = []
    if not instancias.empty:
        for _, row in instancias.iterrows():
            opciones.append(
                f"Virtual: {row['Teórico Virtual (inicio)']} → {row['Teórico Virtual (fin)']} | "
                f"Presencial: {row['Instancia Presencial (inicio)']} → {row['Presencial (fin)']}"
            )

    opcion = st.selectbox(
        "🗓️ Seleccione la instancia",
        opciones if opciones else ["No hay instancias disponibles"]
    )

    submit = st.form_submit_button("✅ Confirmar inscripción")

# ===============================
# PROCESO
# ===============================

if submit:

    if instancias.empty:
        st.warning("📅 No hay instancias planificadas para este curso en 2026.")
        st.stop()

    idx = opciones.index(opcion)
    instancia = instancias.iloc[idx]

    inscriptos = inscripciones[
        (inscripciones["Curso"] == curso) &
        (inscripciones["Teórico Virtual (inicio)"] == instancia["Teórico Virtual (inicio)"]) &
        (inscripciones["Instancia Presencial (inicio)"] == instancia["Instancia Presencial (inicio)"])
    ]

    if len(inscriptos) >= CUPO_MAX:
        st.error("❌ Cupo completo para esta instancia.")
        st.stop()

    ya_inscripto = inscripciones[
        (inscripciones["Instructor"] == instructor) &
        (inscripciones["Curso"] == curso)
    ]

    if not ya_inscripto.empty:
        st.error("❌ Ya estás inscripto en este curso.")
        st.stop()

    nueva = pd.DataFrame([{
        "Instructor": instructor,
        "Curso": curso,
        "Teórico Virtual (inicio)": instancia["Teórico Virtual (inicio)"],
        "Instancia Presencial (inicio)": instancia["Instancia Presencial (inicio)"]
    }])

    inscripciones = pd.concat([inscripciones, nueva], ignore_index=True)
    inscripciones.to_csv("inscripciones.csv", index=False)

    st.success("🎉 Inscripción confirmada correctamente.")

