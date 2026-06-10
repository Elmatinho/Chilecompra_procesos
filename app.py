import streamlit as st
from conversor_bpmn import parse_bpmn_from_string
from transformador_word import transformar_archivo
from generador_word_json import generar_word_desde_json
import io
import os
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool

st.set_page_config(page_title="Procesador BPMN / Word", layout="wide")

st.title("Herramienta de Procesamiento")

opcion = st.sidebar.selectbox(
    "Selecciona una funcionalidad",
    [
        "Conversor BPMN a Texto",
        "Aplicar Plantilla a Excel/Word",
        "Generar Word desde JSON"
    ]
)
# --- Conversor BPMN a Texto ---
if opcion == "Conversor BPMN a Texto":
    st.header("Conversión de archivo BPMN a texto")

    archivo_bpmn = st.file_uploader("Carga tu archivo BPMN", type=["bpmn"])
    if archivo_bpmn:
        contenido = archivo_bpmn.read().decode("utf-8")

        # ⬇️ NUEVO: la función ahora retorna (texto, stats)
        # Llama a la función
        res = parse_bpmn_from_string(contenido)
        
        # Soporta versiones antiguas (solo texto) y nuevas (texto, stats)
        if isinstance(res, tuple) and len(res) == 2:
            texto, stats = res
        else:
            texto = res
            stats = {
                "total_tareas": 0,
                "total_gateways": 0,
                "tareas_por_rol": [],
                "gateways_por_rol": [],
                "tareas_por_rol_raw": {},
                "gateways_por_rol_raw": {},
            }

        # Texto completo (POOLS/PROCESOS/SECUENCIAS + estadísticas en texto)
        st.text_area("Resultado", texto, height=500)

        # Instrucción para análisis con IA (como tenías antes)
        st.markdown("""
        ---
        #### Instrucción para análisis con IA (posterior al texto generado):

Hola, te voy a cargar un archivo .txt que contiene información de un proceso BPMN representado en texto plano. Este archivo contiene roles o responsables definidos como Lane, las tareas como [task], [sendTask] o [receiveTask], y el flujo de trabajo como [sequenceFlow].

De esto, necesito que realices un análisis de lo que se realiza en el proceso y luego de ello separes el proceso por etapas. Posterior a eso necesito que me entregues un listado de las etapas generadas. 

Después de eso, por cada etapa necesito que me entregues las entradas, salidas y el objetivo de la etapa, posteriormente quiero que me elabores un relato extenso, claro y estructurado que describa el paso a paso de las actividades dentro de la etapa, como si estuvieras explicándoselo a alguien que no conoce el funcionamiento interno. Quiero que el resultado sea un texto narrativo, redactado en párrafos, explicando qué sucede, qué rol realiza qué actividad, y cómo avanza el flujo de un paso a otro. En caso de que existan gateways, describe en el relato cuáles son las posibles decisiones que puede tomar el proceso y cómo cada camino afecta la continuidad. El estilo de redacción debe ser similar a este ejemplo: “El proceso comienza cuando un proyecto o funcionalidad ha sido certificado en el ambiente de preproducción. Si esta funcionalidad tiene prioridad o corresponde a una necesidad urgente (como un P1)...” 

Y al final, necesito que me entregues para la totalidad del proceso, los criterios de aceptación del proceso, 3 propuestas de indicadores, que información debería quedar como registro y su relación con la norma ISO 9001

En resumen: analiza las tareas, cruza los LaneID con los roles, interpreta el flujo secuencial, y conviértelo en un texto fluido, comprensible y detallado. Luego quiero que me entregues un listado con las etapas principales del proceso, con el objetivo de cada una.

        Cuando te diga que el archivo fue subido, genera la descripción.
        """)

        # ⬇️ NUEVO: Tablas con estadísticas estructuradas (sin parsear texto)
        import pandas as pd

        st.subheader("📊 Estadísticas del proceso")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de tareas", stats.get("total_tareas", 0))
        with col2:
            st.metric("Total de gateways", stats.get("total_gateways", 0))

        if stats.get("tareas_por_rol"):
            st.markdown("**Distribución de tareas por rol (Lane)**")
            df_tareas = pd.DataFrame(stats["tareas_por_rol"])  # columnas: rol, cantidad, porcentaje
            st.dataframe(df_tareas, use_container_width=True)
           
        if stats.get("gateways_por_rol"):
            st.markdown("**Distribución de gateways por rol (Lane)**")
            df_gateways = pd.DataFrame(stats["gateways_por_rol"])  # columnas: rol, cantidad, porcentaje
            st.dataframe(df_gateways, use_container_width=True)

        # Descargas
        st.download_button("📥 Descargar texto (.txt)", data=texto, file_name="resultado.txt", mime="text/plain")

        # (Opcional) Descarga de estadísticas como CSV
        if stats.get("tareas_por_rol") or stats.get("gateways_por_rol"):
            csv_tareas = pd.DataFrame(stats.get("tareas_por_rol", [])).to_csv(index=False).encode("utf-8")
            csv_gate = pd.DataFrame(stats.get("gateways_por_rol", [])).to_csv(index=False).encode("utf-8")
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button("⬇️ Tareas por rol (CSV)", data=csv_tareas, file_name="tareas_por_rol.csv", mime="text/csv")
            with col_b:
                st.download_button("⬇️ Gateways por rol (CSV)", data=csv_gate, file_name="gateways_por_rol.csv", mime="text/csv")


elif opcion == "Aplicar Plantilla a Excel/Word":
    st.header("Aplicar Plantilla Word a contenido")

    archivo = st.file_uploader("Carga archivo Excel o Word", type=["xlsx", "docx"])
    if archivo:
        ruta_plantilla = os.path.join("plantilla", "Plantilla Documentación Procesos.docx")
        resultado = transformar_archivo(archivo, ruta_plantilla)


elif opcion == "Generar Word desde JSON":
    st.header("Generar Word desde JSON estructurado")

    st.markdown("""
    Pega el JSON generado por la IA o carga un archivo `.json`.
    La aplicación lo aplicará sobre la plantilla Word definida.
    """)

    entrada = st.radio(
        "Selecciona la forma de ingreso del JSON",
        ["Pegar JSON", "Cargar archivo JSON"]
    )

    json_texto = None

    if entrada == "Pegar JSON":
        json_texto = st.text_area(
            "Pega aquí el JSON",
            height=400,
            placeholder='{"nombre_proceso": "...", "objetivo": "...", "etapas": [...]}'
        )

    elif entrada == "Cargar archivo JSON":
        archivo_json = st.file_uploader("Carga archivo JSON", type=["json"])
        if archivo_json:
            json_texto = archivo_json.read().decode("utf-8")

    if json_texto:
        if st.button("Generar documento Word"):
            try:
                ruta_plantilla = os.path.join("plantilla", "plantilla_ia.docx")

                resultado_word = generar_word_desde_json(
                    json_input=json_texto,
                    ruta_plantilla=ruta_plantilla
                )

                st.success("Documento Word generado correctamente.")

                st.download_button(
                    label="Descargar Word generado",
                    data=resultado_word,
                    file_name="documento_proceso_generado.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"Error al generar el documento: {e}")
        st.success("Archivo generado con éxito.")
        st.download_button("Descargar Word", resultado, file_name="resultado.docx")
