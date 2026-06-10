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
        #### 1) Instrucción para análisis con IA (posterior al texto generado):

                Hola, te voy a cargar un archivo .txt que contiene información de un proceso BPMN representado en texto plano. Este archivo contiene roles o responsables definidos como Lane, las tareas como [task], [sendTask] o [receiveTask], y el flujo de trabajo como [sequenceFlow].
                
                De esto, necesito que realices un análisis de lo que se realiza en el proceso y luego de ello separes el proceso por etapas. Posterior a eso necesito que me entregues un listado de las etapas generadas. 
                
                Después de eso, por cada etapa necesito que me entregues las entradas, salidas y el objetivo de la etapa, posteriormente quiero que me elabores un relato extenso, claro y estructurado que describa el paso a paso de las actividades dentro de la etapa, como si estuvieras explicándoselo a alguien que no conoce el funcionamiento interno. Quiero que el resultado sea un texto narrativo, redactado en párrafos, explicando qué sucede, qué rol realiza qué actividad, y cómo avanza el flujo de un paso a otro. En caso de que existan gateways, describe en el relato cuáles son las posibles decisiones que puede tomar el proceso y cómo cada camino afecta la continuidad. El estilo de redacción debe ser similar a este ejemplo: “El proceso comienza cuando un proyecto o funcionalidad ha sido certificado en el ambiente de preproducción. Si esta funcionalidad tiene prioridad o corresponde a una necesidad urgente (como un P1)...” 
                
                Y al final, necesito que me entregues para la totalidad del proceso, los criterios de aceptación del proceso, 3 propuestas de indicadores, que información debería quedar como registro y su relación con la norma ISO 9001
                
                En resumen: analiza las tareas, cruza los LaneID con los roles, interpreta el flujo secuencial, y conviértelo en un texto fluido, comprensible y detallado. Luego quiero que me entregues un listado con las etapas principales del proceso, con el objetivo de cada una.
                
                        Cuando te diga que el archivo fue subido, genera la descripción.


        2) Para generar JSON, el siguiente prompt:
        Hola, te voy a cargar un archivo `.txt` que contiene información de un proceso BPMN representado en texto plano.

        Este archivo contiene roles o responsables definidos como `Lane`, tareas como `[task]`, `[userTask]`, `[sendTask]`, `[receiveTask]`, gateways como `[exclusiveGateway]`, `[parallelGateway]`, `[inclusiveGateway]`, y flujos de trabajo como `[sequenceFlow]`.
        
        Necesito que analices el proceso completo, cruces los LaneID con los roles, interpretes las tareas, gateways y flujos secuenciales, y generes una estructura JSON válida para ser utilizada posteriormente en una plantilla Word.
        
        El resultado debe ser exclusivamente un JSON válido. No incluyas explicaciones antes ni después del JSON. No uses markdown. No uses bloques de código. No incluyas comentarios.
        
        El JSON debe tener exactamente la siguiente estructura:
        
        {
        "nombre_proceso": "",
        "objetivo": "",
        "alcance": "",
        "descripcion_general": "",
        "roles": [],
        "etapas": [
        {
        "nombre": "",
        "objetivo": "",
        "entrada": "",
        "salida": "",
        "descripcion_narrativa": "",
        "roles_participantes": [],
        "riesgos": [],
        "criterios_aceptacion": []
        }
        ],
        "criterios_aceptacion": [],
        "indicadores": [
        {
        "nombre": "",
        "descripcion": "",
        "formula": "",
        "frecuencia": "",
        "responsable": ""
        }
        ],
        "registros": [],
        "relacion_iso_9001": [
        {
        "clausula": "",
        "relacion": ""
        }
        ]
        }
        
        Instrucciones específicas:
        
        1. Identifica el nombre del proceso a partir del contenido del archivo. Si no existe un nombre explícito, propón uno coherente según las actividades descritas.
        
        2. Redacta un objetivo general del proceso, claro y formal, orientado a gestión de procesos.
        
        3. Redacta un alcance del proceso, indicando desde qué evento o actividad comienza y hasta qué punto termina.
        
        4. En `descripcion_general`, redacta un relato extenso, claro y estructurado del proceso completo. Debe estar escrito en prosa, en párrafos, explicando cómo inicia el proceso, cómo avanza, qué roles intervienen y cómo se conectan las actividades principales.
        
        5. Divide el proceso en etapas principales. Cada etapa debe agrupar actividades relacionadas de forma lógica. No generes etapas demasiado pequeñas; deben representar fases relevantes del proceso.
        
        6. Para cada etapa, completa:
        
           * `nombre`: nombre claro de la etapa.
           * `objetivo`: propósito específico de la etapa.
           * `entrada`: insumo, evento o condición que permite iniciar la etapa.
           * `salida`: resultado, producto o condición que deja la etapa para continuar.
           * `descripcion_narrativa`: relato extenso y descriptivo, en prosa, explicando el paso a paso de las actividades de la etapa. Debe indicar qué rol realiza cada actividad, cómo avanza el flujo y qué ocurre cuando existen gateways o decisiones.
           * `roles_participantes`: listado de roles que intervienen en la etapa.
           * `riesgos`: riesgos asociados a la etapa.
           * `criterios_aceptacion`: criterios que permiten validar que la etapa fue correctamente ejecutada.
        
        7. Si existen gateways, interpreta las decisiones posibles y describe en la narrativa cómo cada camino afecta la continuidad del proceso.
        
        8. En `criterios_aceptacion`, entrega criterios generales de aceptación para la totalidad del proceso.
        
        9. En `indicadores`, entrega 3 propuestas de indicadores de desempeño. Cada indicador debe incluir nombre, descripción, fórmula, frecuencia y responsable.
        
        10. En `registros`, indica qué información documentada debería conservarse como evidencia del proceso.
        
        11. En `relacion_iso_9001`, vincula el proceso con cláusulas relevantes de ISO 9001:2015, indicando la cláusula y una breve explicación de la relación. Considera, cuando corresponda, cláusulas como 4.4, 5.3, 6.1, 7.5, 8.1, 8.5, 9.1 y 10.2.
        
        12. El estilo de redacción debe ser formal, técnico y narrativo, similar a este ejemplo:
        
        “El proceso comienza cuando un proyecto o funcionalidad ha sido certificado en el ambiente de preproducción. Si esta funcionalidad tiene prioridad o corresponde a una necesidad urgente, el flujo avanza hacia una evaluación diferenciada que permite determinar si corresponde activar un tratamiento especial. Posteriormente, el rol responsable revisa los antecedentes disponibles, coordina las acciones necesarias y registra la información que permitirá asegurar la trazabilidad del proceso.”
        
        Cuando te indique que el archivo fue subido, genera exclusivamente el archivo JSON solicitado para descargar.

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
                    label="Descargar Word",
                    data=resultado_word,
                    file_name="resultado.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
            except Exception as e:
                st.error(f"Error al generar el documento: {e}")
