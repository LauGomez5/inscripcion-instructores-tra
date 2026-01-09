import streamlit as st
import pandas as pd
import os

# ---------------- CONFIGURACIÓN ----------------
st.set_page_config(
    page_title="Inscripción Instructores TRA",
    layout="centered"
)

ANIO_PERMITIDO = 2026
CUPO_MAXIMO = 2
ARCHIVO_INSCRIPCIONES = "inscripciones.csv"

# ---------------- CARGA DE DATOS ----------------
@st.cache_data
def cargar_datos():
    instructores = pd.read_csv("Clasificación de Instructores.csv")
    cursos = pd.read_csv("Planificación Cursos TRA (3).csv")

    # Limpiar nombres de columnas
    instructores.columns = instructores.columns.str.strip()
    cursos.columns = cursos.columns.str.strip()

    # Normalizar textos
    instructores["Instructor"] = instructores["Instructor"].astype(str).str.strip()
    instructores["Cursos"] = instructores["Cursos"].astype(str).str.strip()
    cursos["Nombre corto"] = cursos["Nombre corto"].astype(str).str.strip()

    # Limpiar AÑO
    if "Año" in cursos.columns:
        cursos["Año"] = (
            cursos["Año"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )

    return instructores, cursos


def cargar_inscripciones():
    if os.path.exists(ARCHIVO_INSCRIPCIONES):
        return pd.read_csv(ARCHIVO_INSCRIPCIONES)
    else:
        return pd.DataFrame(columns=[
            "Instructor",
            "Curso",
            "Teórico Virtual (inicio)",
            "Instancia Presencial (inicio)"
        ])


def guardar_inscripcion(df):
    df.to_csv(ARCHIVO_INSCRIPCIONES, index=False)


# ---------------- APP ----------------
instructores_df, cursos_df = cargar_datos()
inscripciones_df = cargar_inscripciones()

st.title("📋 Inscripción de Instructores – Cursos TRA")

# ---------------- FORM 1 ----------------
with st.form("form_seleccion"):
    instructor = st.selectbox(
        "Seleccione su nombre",
        sorted(instructores_df["Instructor"].dropna().unique())
    )
    ver_cursos = st.form_submit_button("Ver cursos disponibles")

# ---------------- LÓGICA ----------------
if ver_cursos:

    # Cursos habilitados desde Clasificación
    cursos_habilitados = (
        instructores_df[instructores_df["Instructor"] == instructor]["Cursos"]
        .dropna()
        .unique()
    )

    if len(cursos_habilitados) == 0:
        st.warning("⚠️ No hay cursos asociados a este instructor.")
        st.stop()

    # Cruce correcto con Nombre corto + año 2026
    cursos_2026 = cursos_df[
        (cursos_df["Nombre corto"].isin(cursos_habilitados)) &
        ("Año" in cursos_df.columns) &
        (cursos_df["Año"] == ANIO_PERMITIDO)
    ].reset_index(drop=True)

    if cursos_2026.empty:
        st.info("ℹ️ No hay instancias planificadas para el año 2026.")
        st.stop()

    st.success("Instancias disponibles")

    # ---------------- FORM 2 ----------------
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

        # ---- Validar cupo ----
        inscriptos = inscripciones_df[
            (inscripciones_df["Curso"] == instancia["Nombre corto"]) &
            (inscripciones_df["Teórico Virtual (inicio)"] == instancia.get("Teórico Virtual (inicio)", "")) &
            (inscripciones_df["Instancia Presencial (inicio)"] == instancia.get("Instancia Presencial (inicio)", ""))
        ]

        if len(inscriptos) >= CUPO_MAXIMO:
            st.error("❌ Cupo completo para esta instancia.")
            st.stop()

        # ---- Evitar doble inscripción ----
        ya_inscripto = inscripciones_df[
            (inscripciones_df["Instructor"] == instructor) &
            (inscripciones_df["Curso"] == instancia["Nombre corto"])
        ]

        if not ya_inscripto.empty:
            st.error("❌ Ya estás inscripto en este curso.")
            st.stop()

        # ---- Guardar ----
        nueva = pd.DataFrame([{
            "Instructor": instructor,
            "Curso": instancia["Nombre corto"],
            "Teórico Virtual (inicio)": instancia.get("Teórico Virtual (inicio)", ""),
            "Instancia Presencial (inicio)": instancia.get("Instancia Presencial (inicio)", "")
        }])

        inscripciones_df = pd.concat([inscripciones_df, nueva], ignore_index=True)
        guardar_inscripcion(inscripciones_df)

        st.success("✅ Inscripción confirmada correctamente")
