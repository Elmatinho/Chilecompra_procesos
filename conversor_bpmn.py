import xml.etree.ElementTree as ET
from collections import defaultdict
from io import StringIO

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
    """
    Parsea un BPMN (XML como string) y devuelve:
      - texto (str): salida legible con pools, procesos y flows + resumen estadístico
      - stats (dict): estructuras listas para DataFrame (tareas/gateways por rol)

    Ejemplo:
        texto, stats = parse_bpmn_from_string(xml_text)
        # stats["tareas_por_rol"] -> [{'rol': 'Analista', 'cantidad': 5, 'porcentaje': 41.7}, ...]
    """
    root = ET.fromstring(bpmn_content)

    pools = []
    for participant in root.findall('bpmn:collaboration/bpmn:participant', NS):
        pools.append(f"Pool: {participant.get('name', '(sin nombre)')} (Proceso: {participant.get('processRef')})")

    # Shapes y posiciones
    shape_bounds = {}
    for shape in root.findall('.//bpmndi:BPMNShape', NS):
        bpmn_id = shape.get('bpmnElement')
        bounds = shape.find('dc:Bounds', NS)
        if bpmn_id and bounds is not None:
            x = float(bounds.get('x')); y = float(bounds.get('y'))
            w = float(bounds.get('width')); h = float(bounds.get('height'))
            shape_bounds[bpmn_id] = (x, y, w, h)

    procesos = []
    total_tareas = 0
    total_gateways = 0
    conteo_por_lane = defaultdict(int)       # tareas por rol
    gateways_por_lane = defaultdict(int)     # gateways por rol

    for process in root.findall('bpmn:process', NS):
        process_id = process.get('id')
        process_name = process.get('name', '(sin nombre)')
        lines = [f"\nProceso: {process_name} (ID: {process_id})"]

        # Lanes
        lane_areas = {}
        lane_nombres = {}
        for lane in process.findall('bpmn:laneSet/bpmn:lane', NS):
            lane_name = lane.get('name', '(sin nombre)')
            lane_id = lane.get('id')
            lane_nombres[lane_id] = lane_name
            lines.append(f"  Lane: {lane_name} (ID: {lane_id})")
            if lane_id in shape_bounds:
                lane_areas[lane_id] = shape_bounds[lane_id]

        # Elementos → lane
        id_a_lane = {}
        elementos = {}

        for elem in process:
            tag = elem.tag.split('}')[-1]
            elem_id = elem.get('id')
            name = elem.get('name', '(sin nombre)')
            if not elem_id:
                continue

            if es_elemento_bpmn_relevante(tag):
                # Asignar lane por posición geométrica si hay shape
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

                # Contabilizar tareas/gateways

                TASK_TAGS = {'task', 'userTask', 'manualTask', 'serviceTask',
                    'receiveTask', 'sendTask', 'scriptTask', 'businessRuleTask'}
                if tag in TASK_TAGS:
                    conteo_por_lane[lane_nombre] += 1
                    total_tareas += 1
                elif "Gateway" in tag:
                    gateways_por_lane[lane_nombre] += 1
                    total_gateways += 1

        # Sequence flows
        for seq in process.findall('bpmn:sequenceFlow', NS):
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

    # ----- Construir texto legible -----
    salida = StringIO()
    if pools:
        salida.write("=== POOLS ===\n" + '\n'.join(pools) + "\n")
    salida.write("\n=== PROCESOS ===\n" + '\n\n'.join(procesos) + "\n")

    salida.write("\n=== ESTADÍSTICAS DEL PROCESO ===\n")
    salida.write(f"Total de tareas encontradas: {total_tareas}\n")
    salida.write("Tareas por rol:\n")
    for rol, cantidad in sorted(conteo_por_lane.items(), key=lambda x: x[1], reverse=True):
        pct = (cantidad / total_tareas * 100) if total_tareas > 0 else 0.0
        salida.write(f"- {rol}: {cantidad} tareas ({pct:.1f}%)\n")

    salida.write(f"\nTotal de gateways encontrados: {total_gateways}\n")
    salida.write("Gateways por rol:\n")
    for rol, cantidad in sorted(gateways_por_lane.items(), key=lambda x: x[1], reverse=True):
        pct = (cantidad / total_gateways * 100) if total_gateways > 0 else 0.0
        salida.write(f"- {rol}: {cantidad} gateways ({pct:.1f}%)\n")

    texto = salida.getvalue()

    # ----- Estructuras para DataFrame -----
    tareas_por_rol = []
    for rol, cantidad in sorted(conteo_por_lane.items(), key=lambda x: x[1], reverse=True):
        pct = (cantidad / total_tareas * 100) if total_tareas > 0 else 0.0
        tareas_por_rol.append({"rol": rol, "cantidad": cantidad, "porcentaje": round(pct, 1)})

    gateways_por_rol = []
    for rol, cantidad in sorted(gateways_por_lane.items(), key=lambda x: x[1], reverse=True):
        pct = (cantidad / total_gateways * 100) if total_gateways > 0 else 0.0
        gateways_por_rol.append({"rol": rol, "cantidad": cantidad, "porcentaje": round(pct, 1)})

    stats = {
        "total_tareas": total_tareas,
        "total_gateways": total_gateways,
        "tareas_por_rol": tareas_por_rol,                 # lista de dicts → ideal para st.dataframe
        "gateways_por_rol": gateways_por_rol,             # lista de dicts → ideal para st.dataframe
        "tareas_por_rol_raw": dict(conteo_por_lane),      # dict crudo por si lo necesitas
        "gateways_por_rol_raw": dict(gateways_por_lane)   # dict crudo por si lo necesitas
    }

    return texto, stats
