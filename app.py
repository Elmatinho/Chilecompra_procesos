import streamlit as st
from conversor_bpmn import parse_bpmn_from_string
from transformador_word import transformar_archivo
import io
import os

st.set_page_config(page_title="Procesador BPMN / Word", layout="wide")

st.title("Herramienta de Procesamiento")

opcion = st.sidebar.selectbox("Selecciona una funcionalidad", ["Conversor BPMN a Texto", "Aplicar Plantilla a Excel/Word"])

if opcion == "Conversor BPMN a Texto":
    st.header("Conversión de archivo BPMN a texto")

    archivo_bpmn = st.file_uploader("Carga tu archivo BPMN", type=["bpmn"])
    if archivo_bpmn:
        contenido = archivo_bpmn.read().decode("utf-8")
        texto = parse_bpmn_from_string(contenido)
        st.text_area("Resultado", texto, height=500)
        st.download_button("Descargar .txt", texto, file_name="resultado.txt")

elif opcion == "Aplicar Plantilla a Excel/Word":
    st.header("Aplicar Plantilla Word a contenido")

    archivo = st.file_uploader("Carga archivo Excel o Word", type=["xlsx", "docx"])
    if archivo:
        ruta_plantilla = os.path.join("plantilla", "Plantilla.docx")
        resultado = transformar_archivo(archivo, ruta_plantilla)

        st.success("Archivo generado con éxito.")
        st.download_button("Descargar Word", resultado, file_name="resultado.docx")
