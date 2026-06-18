import json
from io import BytesIO
from docxtpl import DocxTemplate


def preparar_data(data):
    """
    Normaliza campos para que la plantilla no falle si falta algún dato.
    """

    data.setdefault("nombre_proceso", "")
    data.setdefault("objetivo", "")
    data.setdefault("alcance", "")
    data.setdefault("descripcion_general", "")
    data.setdefault("roles", [])
    data.setdefault("etapas", [])
    data.setdefault("riesgos", [])
    data.setdefault("criterios_aceptacion", [])
    data.setdefault("indicadores", [])
    data.setdefault("documentos_referencia", [])
    data.setdefault("registros", [])

    for etapa in data["etapas"]:
        etapa.setdefault("nombre", "")
        etapa.setdefault("objetivo", "")
        etapa.setdefault("entrada", "")
        etapa.setdefault("salida", "")
        etapa.setdefault("descripcion_narrativa", "")
        etapa.setdefault("riesgos", [])
        etapa.setdefault("criterios_aceptacion", [])

    return data


def generar_word_desde_json(json_input, ruta_plantilla):
    """
    Recibe un JSON como string o dict y devuelve un Word en memoria.
    """

    if isinstance(json_input, str):
        data = json.loads(json_input)
    else:
        data = json_input

    data = preparar_data(data)

    doc = DocxTemplate(ruta_plantilla)
    doc.render(data)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer