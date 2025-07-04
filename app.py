import streamlit as st
import xml.etree.ElementTree as ET
import io

# Namespaces BPMN estándar
NS = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
    'dc': 'http://www.omg.org/spec/DD/20100524/DC',
    'di': 'http://www.omg.org/spec/DD/20100524/DI'
}

def punto_dentro_de_area(px, py, area):
    ax, ay, aw, ah = area
    return ax <= px <= ax + aw and ay <= py <= ay + ah

def es_elemento_bpmn_relevante(tag):
    return tag in [
        'task', 'userTask', 'manualTask', 'serviceTask', 'receiveTask',
        'sendTask', 'scriptTask', 'businessRuleTask', 'callActivity',
        'startEvent', 'endEvent', 'intermediateCatchEvent', 'intermediateThrowEvent',
        'boundaryEvent',
        'exclusiveGateway', 'inclusiveGateway', 'parallelGateway',
        'eventBasedGateway', 'complexGateway'
    ]

def parse_bpmn_from_string(bpmn_content):
    root = ET.fromstring(bpmn_content)

    # Pools
    pools = []
    for participant in root.findall('bpmn:collaboration/bpmn:participant', NS):
        pools.append(f"Pool: {participant.get('name', '(sin nombre)')} (Proceso: {participant.get('processRef')})")

    # Shapes y posiciones
    shape_bounds = {}
    for shape in root.findall('.//bpmndi:BPMNShape', NS):
        bpmn_id = shape.get('bpmnElement')
        bounds = shape.find('dc:Bounds', NS)
        if bpmn_id and bounds is not None:
            x = float(bounds.get('x'))
            y = float(bounds.get('y'))
            w = float(bounds.get('width'))
            h = float(bounds.get('height'))
            shape_bounds[bpmn_id] = (x, y, w, h)

    procesos = []
    for process in root.findall('bpmn:process', NS):
        process_id = process.get('id')
        process_name = process.get('name', '(sin nombre)')
        lines = [f"\nProceso: {process_name} (ID: {process_id})"]

        # Lanes y sus áreas
        lane_areas = {}
        lane_nombres = {}
        for lane in process.findall('bpmn:laneSet/bpmn:lane', NS):
            lane_name = lane.get('name', '(sin nombre)')
            lane_id = lane.get('id')
            lane_nombres[lane_id] = lane_name
            lines.append(f"  Lane: {lane_name} (ID: {lane_id})")
            if lane_id in shape_bounds:
                lane_areas[lane_id] = shape_bounds[lane_id]

        # Elementos y asignación por posición a lane
        id_a_lane = {}
        elementos = {}
        for elem in process:
            tag = elem.tag.split('}')[-1]
            elem_id = elem.get('id')
            name = elem.get('name', '(sin nombre)')
            if not elem_id:
                continue
            if es_elemento_bpmn_relevante(tag):
                if elem_id in shape_bounds:
                    ex, ey, ew, eh = shape_bounds[elem_id]
                    cx, cy = ex + ew / 2, ey + eh / 2
                    for lid, area in lane_areas.items():
                        if punto_dentro_de_area(cx, cy, area):
                            id_a_lane[elem_id] = lid
                            break
                lane_id = id_a_lane.get(elem_id, 'SinLane')
                lane_nombre = lane_nombres.get(lane_id, 'Sin rol')
                elementos[elem_id] = f"{tag}: {name}"
                lines.append(f"  [{tag}] {name} (ID: {elem_id}, Rol: {lane_nombre})")

        # Sequence flows con nombre del rol
        for seq in process.findall('bpmn:sequenceFlow', NS):
            flow_id = seq.get('id')
            source = seq.get('sourceRef')
            target = seq.get('targetRef')
            source_name = elementos.get(source, source)
            target_name = elementos.get(target, target)
            source_lane = lane_nombres.get(id_a_lane.get(source, ''), 'Sin rol')
            target_lane = lane_nombres.get(id_a_lane.get(target, ''), 'Sin rol')
            lines.append(
                f"  [sequenceFlow] {source_name} (Rol: {source_lane}) ➝ {target_name} (Rol: {target_lane})"
            )

        procesos.append('\n'.join(lines))

    output = ""
    if pools:
        output += "=== POOLS ===\n" + '\n'.join(pools) + "\n"
    output += "\n=== PROCESOS ===\n" + '\n\n'.join(procesos)
    return output

# Streamlit App
st.title("Convertidor de BPMN a Texto")

uploaded_file = st.file_uploader("Carga un archivo BPMN", type=["bpmn"])

if uploaded_file:
    bpmn_bytes = uploaded_file.read()
    try:
        output_text = parse_bpmn_from_string(bpmn_bytes.decode("utf-8"))
        st.success("✅ Conversión realizada correctamente.")
        st.text_area("Resultado:", output_text, height=500)

        st.download_button(
            label="📥 Descargar .txt",
            data=output_text,
            file_name=uploaded_file.name.replace(".bpmn", ".txt"),
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")

