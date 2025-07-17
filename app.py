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
        st.markdown("""
        ---
        #### Instrucción para análisis con IA
        ##### Copia y pega el siguiente script en cualquier GenAI para poder tener el resultado optimo de la descripción:

        Hola, te voy a cargar un archivo .txt que contiene información de un proceso BPMN representado en texto plano.

        Este archivo contiene roles o responsables definidos como Lane, las tareas como [task], [sendTask] o [receiveTask], y el flujo de trabajo como [sequenceFlow].

        Necesito que me generes un relato extenso, claro y estructurado que describa el paso a paso del proceso, como si estuvieras explicándoselo a alguien que no conoce el funcionamiento interno.

        Quiero que el resultado sea un texto narrativo, redactado en párrafos, explicando qué sucede en cada etapa del proceso, qué rol realiza qué actividad, y cómo avanza el flujo de un paso a otro.

        En caso de que existan gateways, describe en el relato cuáles son las posibles decisiones que puede tomar el proceso y cómo cada camino afecta la continuidad.

        El estilo de redacción debe ser similar a este ejemplo:

        *“El proceso comienza cuando un proyecto o funcionalidad ha sido certificado en el ambiente de preproducción. Si esta funcionalidad tiene prioridad o corresponde a una necesidad urgente (como un P1)...”*

        En resumen: analiza las tareas, cruza los LaneID con los roles, interpreta el flujo secuencial, y conviértelo en un texto fluido, comprensible y detallado.

        Cuando te diga que el archivo fue subido, genera la descripción.
        """)

       
        st.download_button("Descargar .txt", texto, file_name="resultado.txt")



elif opcion == "Aplicar Plantilla a Excel/Word":
    st.header("Aplicar Plantilla Word a contenido")
    

    archivo = st.file_uploader("Carga archivo Excel o Word", type=["xlsx", "docx"])
    if archivo:
        ruta_plantilla = os.path.join("plantilla", "Plantilla Documentación Procesos.docx")
        resultado = transformar_archivo(archivo, ruta_plantilla)

        st.success("Archivo generado con éxito.")
        st.download_button("Descargar Word", resultado, file_name="resultado.docx")
