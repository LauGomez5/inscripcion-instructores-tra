import streamlit as st
import pandas as pd
import os

# ===============================
# CONFIGURACIÓN GENERAL
# ===============================
CUPO_MAX = 2
ANIO_PERMITIDO = 2026
INSCRIPCIONES_FILE = "inscripciones.csv"

st.set_page_config(page_title="Inscripción Instructores TRA 2026")

st.title("📋 Inscripción de Instructores – Cursos TRA 2026")

# ===============================
# CARGA DE DATOS
# ===============================

@st.cache_data
def cargar_datos():
    instructores = pd.read_csv("Clasificación de Instructores.csv")
    cursos = pd.read_csv("Planificación Cursos TRA (3).csv")

    instructores["Instructor"] = instructores["Instructor"].astype(str).str.strip()
    instructores["Cursos"] = instructores["Cursos"].astype(str).str.strip()

    cursos["Nombre corto"] = cursos["Nombre corto"].astype(str).str.strip()
    cursos["Año"] = (
        cursos["Año"]
        .astype(str)
        .str.strip()
        .str.replace(".0", "", regex=False)
    )
    cursos["Año"] = pd.to_numeric(cursos["Año"], errors="coerce")

    return instructores, cursos


instructores, cursos = cargar_datos()

# ===============================
# CARGA / CREACIÓN INSCRIPCIONES
# ===============================

if os.path.exists(INSCRIPCIONES_FILE):
    inscripciones = pd.read_csv(INSCRIPCIONES_FILE)
else:
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

    instructor = st.selectbox(
        "Instructor",
        sorted(instructores["Instructor"].unique())
    )

    cursos_habilitados = instructores[
        instructores["Instructor"] == instructor
    ]["Cursos"].unique()

    curso = st.selectbox(
        "Curso",
        cursos_habilitados
    )

    instancias = cursos[
        (cursos["Nombre corto"] == curso) &
        (cursos["Año"] == ANIO_PERMITIDO)
    ].reset_index(drop=True)

    if instancias.empty:
        st.warning("No hay instancias planificadas para 2026")
        st.stop()

    opciones_instancias = [
        f"Virtual: {row['Teórico Virtual (inicio)']} → {row['Teórico Virtual (fin)']} | "
        f"Presencial: {row['Instancia Presencial (inicio)']} → {row['Presencial (fin)']}"
        for _, row in instancias.iterrows()
    ]

    instancia_elegida = st.selectbox(
        "Instancia",
        opciones_instancias
    )

    enviar = st.form_submit_button("Confirmar inscripción")

# ===============================
# PROCESAR INSCRIPCIÓN
# ===============================

if enviar:

    idx = opciones_instancias.index(instancia_elegida)
    fila = instancias.iloc[idx]

    inscriptos = inscripciones[
        (inscripciones["Curso"] == curso) &
        (inscripciones["Teórico Virtual (inicio)"] == fila["Teórico Virtual (inicio)"]) &
        (inscripciones["Instancia Presencial (inicio)"] == fila["Instancia Presencial (inicio)"])
    ]

    if len(inscriptos) >= CUPO_MAX:
        st.error("❌ Cupo completo para esta instancia")
        st.stop()

    if not inscripciones[
        (inscripciones["Instructor"] == instructor) &
        (inscripciones["Curso"] == curso)
    ].empty:
        st.error("❌ Ya estás inscripto en este curso")
        st.stop()

    nueva = pd.DataFrame([{
        "Instructor": instructor,
        "Curso": curso,
        "Teórico Virtual (inicio)": fila["Teórico Virtual (inicio)"],
        "Instancia Presencial (inicio)": fila["Instancia Presencial (inicio)"]
    }])

    inscripciones = pd.concat([inscripciones, nueva], ignore_index=True)
    inscripciones.to_csv(INSCRIPCIONES_FILE, index=False)

    st.success("✅ Inscripción confirmada")
