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

# ---------------- CSV desde GitHub ----------------
# Reemplaza estos enlaces con los tuyos
ARCHIVO_INSTRUCTORES = "https://raw.githubusercontent.com/tu_usuario/tu_repo/main/Clasificación%20de%20Instructores.csv"
ARCHIVO_CURSOS = "https://raw.githubusercontent.com/tu_usuario/tu_repo/main/Planificación%20Cursos%20TRA%20(3).csv"

# Carpeta para guardar inscripciones
CARPETA_INSCRIPCIONES = "Inscripciones"
if not os.path.exists(CARPETA_INSCRIPCIONES):
    os.makedirs(CARPETA_INSCRIPCIONES)

ARCHIVO_INSCRIPCIONES = os.path.join(CARPETA_INSCRIPCIONES, "inscripciones.csv")

# ---------------- CARGA DE DATOS ----------------
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
        cursos["Año"] = (
            cursos["Año"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
        )

    return instructores, cursos

# ---------------- INSCRIPCIONES ----------------
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

# Mantener inscripciones en tiempo real
if "inscripciones_df" not in st.session_state:
    st.session_state.inscripciones_df = cargar_inscripciones()

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
    cursos_habilitados = (
        instructores_df[instructores_df["Instructor"] == instructor]["Cursos"]
        .dropna()
        .unique()
    )

    if len(cursos_habilitados) == 0:
        st.warning("⚠️ No hay cursos asociados a este instructor.")
        st.stop()

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
        insc = st.session_state.inscripciones_df[
            (st.session_state.inscripciones_df["Curso"] == instancia["Nombre corto"]) &
            (st.session_state.inscripciones_df["Teórico Virtual (inicio)"] == instancia.get("Teórico Virtual (inicio)", "")) &
            (st.session_state.inscripciones_df["Instancia Presencial (inicio)"] == instancia.get("Instancia Presencial (inicio)", ""))
        ]

        if len(insc) >= CUPO_MAXIMO:
            st.error("❌ Cupo completo para esta instancia.")
        else:
            # Evitar doble inscripción
            ya_inscripto = st.session_state.inscripciones_df[
                (st.session_state.inscripciones_df["Instructor"] == instructor) &
                (st.session_state.inscripciones_df["Curso"] == instancia["Nombre corto"])
            ]
            if not ya_inscripto.empty:
                st.error("❌ Ya estás inscripto en este curso.")
            else:
                # Guardar inscripción
                nueva = pd.DataFrame([{
                    "Instructor": instructor,
                    "Curso": instancia["Nombre corto"],
                    "Teórico Virtual (inicio)": instancia.get("Teórico Virtual (inicio)", ""),
                    "Instancia Presencial (inicio)": instancia.get("Instancia Presencial (inicio)", "")
                }])

                st.session_state.inscripciones_df = pd.concat(
                    [st.session_state.inscripciones_df, nueva],
                    ignore_index=True
                )
                guardar_inscripcion(st.session_state.inscripciones_df)
                st.success(f"✅ Inscripción confirmada. Archivo guardado en: `{ARCHIVO_INSCRIPCIONES}`")

# ---------------- TABLA DE INSCRIPCIONES ----------------
st.subheader("📄 Inscripciones actuales")
st.dataframe(st.session_state.inscripciones_df)

# ---------------- OPCIÓN DE DESCARGA ----------------
csv = st.session_state.inscripciones_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar CSV de inscripciones",
    data=csv,
    file_name="inscripciones.csv",
    mime="text/csv"
)

