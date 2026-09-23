import json


def main(ocr_json: str) -> dict:
    """
    Limpieza de layout para salida General Text.
    Toma el JSON de respuesta de Huawei OCR y arma un texto más limpio
    por columnas/secciones, agrupando words_block_list en líneas.

    Secciones definidas por coordenadas:
      - HEADER / TOPBAR:   y1 < 70
      - CUERPO PRINCIPAL:   y1 >= 70  AND  160 <= cx < 700
      - PANEL DERECHO:      y1 >= 70  AND  cx >= 700
      - MENU IZQUIERDO:     y1 >= 70  AND  cx < 160

    Líneas agrupadas por proximidad vertical (cy dentro de 12px).
    """
    try:
        response = json.loads(ocr_json) if isinstance(ocr_json, str) else ocr_json
    except (json.JSONDecodeError, TypeError) as e:
        return {"texto_limpio": "", "estado": f"ERROR parseando JSON: {e}", "bloques": 0}

    # Extraer words_block_list (Huawei General Text API)
    result = response.get("result", {})
    # Si result es una lista (multi-página), tomar la primera
    if isinstance(result, list):
        result = result[0] if result else {}

    # words_block_list está dentro de ocr_result (respuesta real del OCR)
    ocr_result = result.get("ocr_result", {})
    words_block_list = ocr_result.get("words_block_list", [])

    # Fallback: buscar directamente en result (compatibilidad con otros formatos)
    if not words_block_list:
        words_block_list = result.get("words_block_list", [])

    if not words_block_list:
        return {"texto_limpio": "", "estado": "ERROR: no hay words_block_list", "bloques": 0}

    # Calcular bounding box y centro para cada bloque
    blocks = []
    for wb in words_block_list:
        location = wb.get("location", [])
        if not location or len(location) < 1:
            continue

        xs = [loc[0] for loc in location]
        ys = [loc[1] for loc in location]

        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

        blocks.append({
            "text": wb.get("words", ""),
            "confidence": wb.get("confidence", 0),
            "x1": x1, "x2": x2, "y1": y1, "y2": y2,
            "cx": cx, "cy": cy,
        })

    if not blocks:
        return {"texto_limpio": "", "estado": "ERROR: sin bloques válidos", "bloques": 0}

    # Definir secciones por coordenadas
    sections = [
        ("HEADER / TOPBAR",    lambda b: b["y1"] < 70),
        ("CUERPO PRINCIPAL",   lambda b: b["y1"] >= 70 and 160 <= b["cx"] < 700),
        ("PANEL DERECHO",      lambda b: b["y1"] >= 70 and b["cx"] >= 700),
        ("MENU IZQUIERDO",     lambda b: b["y1"] >= 70 and b["cx"] < 160),
    ]

    lines_out = []

    for sec_name, sec_filter in sections:
        lines_out.append("")
        lines_out.append(f"===== {sec_name} =====")

        # Filtrar bloques de esta sección y ordenar por (y1, x1)
        items = sorted(
            [b for b in blocks if sec_filter(b)],
            key=lambda b: (b["y1"], b["x1"]),
        )

        # Agrupar en líneas por proximidad vertical (cy dentro de 12px)
        current_line = []
        current_y = None

        for item in items:
            if current_y is None:
                current_y = item["cy"]
                current_line.append(item)
                continue

            if abs(item["cy"] - current_y) <= 12:
                # Misma línea: agregar y promediar cy
                current_line.append(item)
                current_y = (current_y + item["cy"]) / 2
            else:
                # Nueva línea: finalizar la anterior
                line_text = " ".join(
                    b["text"] for b in sorted(current_line, key=lambda b: b["x1"])
                )
                if line_text.strip():
                    lines_out.append(line_text)
                current_line = [item]
                current_y = item["cy"]

        # Última línea pendiente
        if current_line:
            line_text = " ".join(
                b["text"] for b in sorted(current_line, key=lambda b: b["x1"])
            )
            if line_text.strip():
                lines_out.append(line_text)

    return {
        "texto_limpio": "\n".join(lines_out).strip(),
        "estado": "OK",
        "bloques": len(blocks),
    }
