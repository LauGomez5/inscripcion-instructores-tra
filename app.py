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

    # Limpiar nombres de columnas
    instructores.columns = instructores.columns.str.strip()
    cursos.columns = cursos.columns.str.strip()

    # Normalizar instructores
    instructores["Instructor"] = instructores["Instructor"].astype(str).str.strip()
    instructores["Cursos"] = instructores["Cursos"].astype(str).str.strip()

    # Normalizar cursos
    cursos["Nombre corto"] = cursos["Nombre corto"].astype(str).str.strip()

    # Buscar columna año real
    col_anio = None
    for c in cursos.columns:
        c_norm = c.upper().replace("Ñ", "N").strip()
        if c_norm in ["AÑO", "ANIO"]:
            col_anio = c
            break

    if col_anio is None:
        st.error(
            "No se encontró columna de año.\n\n"
            f"Columnas disponibles:\n{list(cursos.columns)}"
        )
        st.stop()

    # Crear AÑO_LIMPIO SIEMPRE
    cursos["AÑO_LIMPIO"] = (
        cursos[col_anio]
        .astype(str)
        .str.strip()
        .str.replace(".0", "", regex=False)
    )

    cursos["AÑO_LIMPIO"] = pd.to_numeric(cursos["AÑO_LIMPIO"], errors="coerce")

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
        (cursos["AÑO_LIMPIO"] == ANIO_PERMITIDO)
    ].reset_index(drop=True)

    opciones_instancias = [
        f"Virtual: {row['Teórico Virtual (inicio)']} → {row['Teórico Virtual (fin)']} | "
        f"Presencial: {row['Instancia Presencial (inicio)']} → {row['Presencial (fin)']}"
        for _, row in instancias.iterrows()
    ]

    instancia_elegida = st.selectbox(
        "Instancia",
        opciones_instancias
    )

    # 👉 ESTE BOTÓN ES OBLIGATORIO
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
