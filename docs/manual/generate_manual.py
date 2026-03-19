#!/usr/bin/env python3
from __future__ import annotations

import collections
import datetime as dt
import html
import json
import pathlib
import re
from typing import Dict, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANUAL_TXT = ROOT / "docs/manual/source/ManualBennuGD_Osk_v1.txt"
OUT_HTML = ROOT / "docs/manual/BennuGD2_Manual_Comparado.html"
OUT_JSON = ROOT / "docs/manual/BennuGD2_Manual_Comparado.json"
OUT_PDF = ROOT / "docs/manual/BennuGD2_Manual_Comparado.pdf"

FUNC_RE = re.compile(
    r'FUNC\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*([^,]+?)\s*,\s*([A-Za-z0-9_]+)\s*\)'
)
COMMENT_RE = re.compile(r"/\*\s*(.*?)\s*\*/")

SIG_MAP = {
    "I": "INT (64-bit)",
    "i": "INT32 (32-bit)",
    "W": "WORD (16-bit)",
    "B": "BYTE (8-bit)",
    "S": "STRING",
    "P": "POINTER",
    "D": "DOUBLE",
    "F": "FLOAT",
    "N": "NULO/VOID",
}

RET_MAP = {
    "TYPE_INT": "INT",
    "TYPE_DWORD": "DWORD",
    "TYPE_WORD": "WORD",
    "TYPE_BYTE": "BYTE",
    "TYPE_STRING": "STRING",
    "TYPE_DOUBLE": "DOUBLE",
    "TYPE_FLOAT": "FLOAT",
    "TYPE_POINTER": "POINTER",
    "TYPE_QWORD": "QWORD",
    "TYPE_UNDEFINED": "UNDEFINED",
}

STOPWORDS_OLD = {
    "FUNCIONES", "FUNCION", "ORDEN", "ORDENES", "PROCESO", "PROCESOS", "CAPITULO",
    "COORDENADA", "COORDENADAS", "VECTOR", "INT", "FLOAT", "DOUBLE", "IF", "FOR", "MAIN",
    "BEGIN", "END", "RETURN", "USUARIO", "OPERACIONES", "EN", "CON", "VALOR", "CADENA",
    "MEMORIA", "RUTA", "ACTUAL", "FICAS", "NGULO", "RCULO", "NEA", "NEAS", "XELES",
    "JUEGO", "PUNTO", "PANTALLA", "ELEMENTOS", "PRIMITIVAS", "DIBUJAR", "COMPLETA", "DUREZAS",
    "SECUENCIALMENTE", "ERROR", "METRO", "BENNU", "PERSONAJE", "PERSONAJE2", "ENEMIGO", "NAVE",
    "PROCESO1", "PROCESO2", "PROCESO3", "MIPROCESO", "MI_PROCESO", "BOLA", "BOLA2", "DISPARO",
    "HORIZONTAL", "VERTICAL", "ROJO", "ZONA", "SIGUIENTE", "PRINCIPIO", "VALORES", "ENTERA",
    "SECCIONES", "DECLARE", "INCLUDE", "FIBONACCI", "FACTORIAL", "MIRRORSTR", "CUMPLIR", "WIKI",
    "MAPA", "TEXTO", "SCROLL", "SCROLLS",
}

RENAME_HINTS = {
    "START_SCROLL": "SCROLL_START",
    "STOP_SCROLL": "SCROLL_STOP",
    "MOVE_TEXT": "WRITE_MOVE",
    "DELETE_TEXT": "WRITE_DELETE",
    "SET_TEXT_COLOR": "WRITE_SET_RGBA",
    "GET_TEXT_COLOR": "WRITE_GET_RGBA",
    "SET_ICON": "WINDOW_SET_ICON",
    "SET_TITLE": "WINDOW_SET_TITLE",
    "GET_MODES": "SCREEN_GET / DESKTOP_GET_SIZE",
    "LOAD_PNG": "MAP_LOAD",
    "SAVE_PNG": "MAP_SAVE",
    "LOAD_MAP": "MAP_LOAD",
    "SAVE_MAP": "MAP_SAVE",
    "UNLOAD_MAP": "MAP_UNLOAD",
    "LOAD_FPG": "FPG_LOAD",
    "SAVE_FPG": "FPG_SAVE",
    "UNLOAD_FPG": "FPG_UNLOAD",
    "PLAY_WAV": "SOUND_PLAY",
    "LOAD_WAV": "SOUND_LOAD",
    "STOP_WAV": "SOUND_STOP",
    "SET_WAV_VOLUME": "SOUND_SET_VOLUME / CHANNEL_SET_VOLUME",
    "PLAY_SONG": "MUSIC_PLAY",
    "LOAD_SONG": "MUSIC_LOAD",
    "STOP_SONG": "MUSIC_STOP",
    "FADE_MUSIC_OFF": "MUSIC_FADE_OFF",
    "SET_CHANNEL_VOLUME": "CHANNEL_SET_VOLUME",
    "SET_POSITION": "SOUND_SET_LOCATION / SOUND_SET_SPATIAL_POSITION",
}


def normalize_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9_]", "", name.upper())


def decode_signature(sig: str) -> str:
    if not sig:
        return "sin parámetros"
    return ", ".join(SIG_MAP.get(ch, ch) for ch in sig)


def ret_type_name(raw: str) -> str:
    raw = raw.strip()
    return RET_MAP.get(raw, raw)


def short_comment(text: str) -> str:
    t = (text or "").strip().strip("/").strip()
    if not t:
        return ""
    return t


def infer_category(module: str, fname: str) -> str:
    n = fname.upper()

    if module == "libmod_sound":
        return "Sonido y Música"
    if module == "libmod_input":
        return "Entrada (Teclado/Ratón/Mandos)"
    if module == "libmod_net":
        return "Red"
    if module == "libmod_debug":
        return "Depuración"
    if module == "libmod_gfx":
        return "Pantalla y Gráficos"

    # libmod_misc se reparte por temas
    if n.startswith(("F", "DIR", "CD", "CHDIR", "MKDIR", "RM", "RMDIR", "GLOB", "LOAD", "SAVE", "FILE", "FIND")):
        return "Archivos y Directorios"
    if n.startswith(("STR", "STRING_", "LEN", "LCASE", "UCASE", "TRIM", "SUBSTR", "SPLIT", "JOIN", "CHR", "ASC", "TOLOWER", "TOUPPER", "FORMAT", "ATO", "ITOA", "FTOA")):
        return "Cadenas y Texto"
    if n.startswith(("ABS", "SIN", "COS", "TAN", "ASIN", "ACOS", "ATAN", "SQRT", "POW", "LOG", "EXP", "RAND", "ROUND", "CEIL", "FLOOR", "FMOD", "MMOD", "DIST", "NEAR_", "GET_ANGLE", "GET_DIST", "RANGECHK", "CLAMP", "WRAP", "LERP", "INVLERP", "REMAP", "PROJECT", "ORTHO", "MAG", "NORMALIZE", "RAD", "DEG", "SGN", "SIGN", "FRAC", "TRUNC", "MODULUS")):
        return "Matemáticas y Geometría"
    if n.startswith(("ALLOC", "CALLOC", "REALLOC", "FREE", "MEM", "LIST_", "SORT", "ISORT", "KSORT")):
        return "Memoria y Estructuras"
    if n.startswith(("SAY", "TRACE")):
        return "Depuración"

    return "Sistema y Procesos"


def infer_description(name: str, category: str) -> str:
    n = name.upper()

    hardcoded = {
        "KEY": "Consulta si una tecla está pulsada.",
        "KEYDOWN": "Devuelve evento de pulsación de tecla (flanco de bajada).",
        "KEYUP": "Devuelve evento de liberación de tecla.",
        "SAY": "Escribe texto en consola de depuración.",
        "SAY_FAST": "Escribe texto en consola con menor sobrecarga.",
        "TRACE": "Genera traza de depuración.",
        "SET_MODE": "Configura modo de vídeo (resolución/profundidad/opciones).",
        "SET_FPS": "Configura FPS objetivo y lógica de temporización.",
        "WINDOW_SET_TITLE": "Cambia el título de la ventana.",
        "WINDOW_SET_ICON": "Cambia el icono de la ventana.",
    }
    if n in hardcoded:
        return hardcoded[n]

    parts = n.split("_")
    p0 = parts[0]

    if p0 == "GET":
        return "Obtiene un valor de estado o propiedad."
    if p0 == "SET":
        return "Configura un valor de estado o propiedad."
    if p0 == "LOAD":
        return "Carga un recurso desde disco o memoria."
    if p0 == "SAVE":
        return "Guarda un recurso en disco."
    if p0 in {"UNLOAD", "FREE", "DEL", "DELETE", "REMOVE"}:
        return "Libera o elimina recursos asociados."
    if p0 in {"PLAY", "STOP", "PAUSE", "RESUME"}:
        return "Control de reproducción/ejecución."
    if p0 == "DRAW":
        return "Dibuja primitivas o formas en pantalla/mapa."
    if p0 == "MAP":
        return "Operaciones sobre mapas/imágenes (bitmap)."
    if p0 == "FPG":
        return "Operaciones sobre contenedores de gráficos FPG."
    if p0 == "FNT":
        return "Operaciones sobre fuentes FNT."
    if p0 == "WRITE":
        return "Escritura de texto o valores en pantalla/mapa."
    if p0 == "SOUND":
        return "Control de efectos de sonido (SFX)."
    if p0 == "MUSIC":
        return "Control de música de fondo."
    if p0 == "CHANNEL":
        return "Control de canales de audio."
    if p0 == "JOY":
        return "Consulta/control de dispositivos de mando (joystick/gamepad)."
    if p0 == "NET":
        return "Operaciones de red (apertura, envío, recepción y espera)."
    if p0 == "REGEX":
        return "Evaluación o sustitución mediante expresiones regulares."
    if p0 == "PATH":
        return "Gestión de caminos/pathfinding."
    if p0 == "MEM" or n.startswith("MEM"):
        return "Operaciones de memoria (reservar/copiar/mover/rellenar)."
    if p0 == "LIST":
        return "Gestión de listas dinámicas."

    if category == "Matemáticas y Geometría":
        return "Función matemática o geométrica."
    if category == "Archivos y Directorios":
        return "Operación de E/S de archivos o directorios."
    if category == "Sistema y Procesos":
        return "Utilidad general del sistema/procesos."

    return "Función del módulo correspondiente."


def parse_exports() -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []

    files = sorted((ROOT / "modules").glob("**/*_exports.h"))
    for path in files:
        module = path.parent.name
        current_group = ""

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines, start=1):
            if "FUNC(" not in line:
                cm = COMMENT_RE.search(line)
                if cm:
                    label = short_comment(cm.group(1))
                    if label and len(label) <= 50 and "Copyright" not in label and "-" not in label:
                        current_group = label
                continue

            m = FUNC_RE.search(line)
            if not m:
                continue

            name, sig, ret_type_raw, impl = m.groups()
            if name == "0" or impl == "0":
                continue

            inline_comment = ""
            if "//" in line:
                inline_comment = short_comment(line.split("//", 1)[1])

            entry = {
                "module": module,
                "exports_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "line": idx,
                "group": current_group,
                "name": name,
                "name_norm": normalize_name(name),
                "signature": sig,
                "signature_readable": decode_signature(sig),
                "return_type": ret_type_name(ret_type_raw),
                "impl": impl,
                "inline_comment": inline_comment,
            }
            entry["category"] = infer_category(module, name)
            entry["description"] = infer_description(name, entry["category"])
            entries.append(entry)

    return entries


def old_manual_presence(entries: List[Dict[str, str]], manual_text: str) -> None:
    lower_text = manual_text.lower()
    for e in entries:
        # Match robusto de nombre de función seguido de '(' en el manual v1.0
        pat = re.compile(rf"\b{re.escape(e['name'].lower())}\s*\(")
        in_old = bool(pat.search(lower_text))
        e["in_manual_v1"] = in_old
        e["compatibility"] = "Vigente desde v1" if in_old else "Nueva en BennuGD2"


def extract_old_only_candidates(manual_text: str, current_names: set[str]) -> List[Tuple[str, str]]:
    lines = manual_text.splitlines()
    old_candidates: List[str] = []

    for ln in lines:
        ll = ln.lower()
        if "orden" in ll or "órdenes" in ll or "función" in ll or "funciones" in ll:
            old_candidates.extend(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", ln))

    pref_ok = (
        "SET", "GET", "LOAD", "SAVE", "UNLOAD", "PLAY", "STOP", "PAUSE", "RESUME",
        "MAP", "FPG", "FNT", "DRAW", "TEXT", "WRITE", "MOVE", "DELETE", "SCROLL",
        "REGION", "PATH", "BLEND", "SOUND", "MUSIC", "WAV", "SONG", "JOY", "KEY",
    )

    counts = collections.Counter(normalize_name(raw) for raw in old_candidates)

    filtered: set[str] = set()
    for n, count in counts.items():
        if not n or n in STOPWORDS_OLD:
            continue
        if len(n) < 3:
            continue
        if n in current_names:
            continue
        # Evitar ruido del OCR: exigir prefijo de función o mapeo conocido.
        if not n.startswith(pref_ok) and n not in RENAME_HINTS:
            continue
        # Reforzar confianza mínima de aparición si no está en el mapeo manual.
        if count < 3 and n not in RENAME_HINTS:
            continue
        filtered.add(n)

    result: List[Tuple[str, str]] = []
    for n in sorted(filtered):
        hint = RENAME_HINTS.get(n, "")
        result.append((n, hint))

    return result


def build_html(entries: List[Dict[str, str]], old_only: List[Tuple[str, str]]) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    unique_current = sorted({e["name_norm"] for e in entries})
    unique_legacy = sorted({e["name_norm"] for e in entries if e["in_manual_v1"]})
    unique_new = sorted({e["name_norm"] for e in entries if not e["in_manual_v1"]})

    by_cat: Dict[str, List[Dict[str, str]]] = collections.defaultdict(list)
    for e in entries:
        by_cat[e["category"]].append(e)

    cat_order = [
        "Pantalla y Gráficos",
        "Sonido y Música",
        "Entrada (Teclado/Ratón/Mandos)",
        "Archivos y Directorios",
        "Cadenas y Texto",
        "Matemáticas y Geometría",
        "Memoria y Estructuras",
        "Sistema y Procesos",
        "Red",
        "Depuración",
    ]

    for c in by_cat:
        by_cat[c].sort(key=lambda x: (x["name"], x["signature"], x["module"]))

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    out: List[str] = []
    out.append("<!doctype html>")
    out.append('<html lang="es">')
    out.append("<head>")
    out.append('  <meta charset="utf-8">')
    out.append('  <meta name="viewport" content="width=device-width, initial-scale=1">')
    out.append("  <title>Manual BennuGD2 (comparado con Bennu v1.0)</title>")
    out.append("  <style>")
    out.append(
        """
:root {
  --bg: #f5f7fb;
  --panel: #ffffff;
  --ink: #15202b;
  --sub: #4a5568;
  --line: #d7deea;
  --brand: #0b5fff;
  --ok: #1f8b4c;
  --new: #9b1c1c;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Avenir Next", "Segoe UI", sans-serif;
  color: var(--ink);
  background: linear-gradient(160deg, #f7fbff 0%, #eef4ff 40%, #f6f7fb 100%);
}
.wrap {
  max-width: 1320px;
  margin: 0 auto;
  padding: 22px;
}
h1,h2,h3 { line-height: 1.2; margin: 0 0 10px; }
h1 { font-size: 2rem; }
h2 { font-size: 1.5rem; margin-top: 34px; }
h3 { font-size: 1.1rem; margin-top: 18px; }
p, li { color: var(--sub); }
.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 6px 20px rgba(15, 35, 95, 0.05);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}
.metric {
  background: #f8fbff;
  border: 1px solid #d7e7ff;
  border-radius: 10px;
  padding: 10px;
}
.metric .n { font-size: 1.5rem; font-weight: 700; color: #123e8c; }
.toc a {
  display: inline-block;
  margin: 3px 8px 3px 0;
  padding: 6px 10px;
  border-radius: 999px;
  background: #edf3ff;
  color: #1549aa;
  text-decoration: none;
  font-size: 0.9rem;
}
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
}
table {
  border-collapse: collapse;
  min-width: 1160px;
  width: 100%;
}
th, td {
  padding: 8px 10px;
  border-bottom: 1px solid #edf1f7;
  vertical-align: top;
  font-size: 0.88rem;
}
th {
  position: sticky;
  top: 0;
  background: #f2f7ff;
  color: #143f8f;
  text-align: left;
}
.badge {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 600;
  white-space: nowrap;
}
.badge.ok { background: #e8f8ee; color: var(--ok); }
.badge.new { background: #ffecee; color: var(--new); }
code { background: #f5f7fb; padding: 1px 4px; border-radius: 4px; }
.small { font-size: 0.84rem; color: #64748b; }
.footer { margin: 32px 0 10px; font-size: 0.84rem; color: #64748b; }
ul.tight li { margin: 4px 0; }
        """
    )
    out.append("  </style>")
    out.append("</head>")
    out.append("<body>")
    out.append('  <div class="wrap">')

    out.append('    <div class="card">')
    out.append("      <h1>Manual BennuGD2 (comparado con Bennu v1.0 de Osk)</h1>")
    out.append(
        "      <p>Documento generado automáticamente comparando el manual v1.0 (PDF de Osk) con las funciones realmente exportadas por BennuGD2 en este repositorio.</p>"
    )
    out.append("      <p class=\"small\">Generado: " + esc(now) + "</p>")
    out.append('      <div class="grid">')
    out.append('        <div class="metric"><div class="n">' + str(len(entries)) + '</div><div>Overloads exportados</div></div>')
    out.append('        <div class="metric"><div class="n">' + str(len(unique_current)) + '</div><div>Funciones únicas BennuGD2</div></div>')
    out.append('        <div class="metric"><div class="n">' + str(len(unique_legacy)) + '</div><div>Funciones detectadas también en v1.0</div></div>')
    out.append('        <div class="metric"><div class="n">' + str(len(unique_new)) + '</div><div>Funciones nuevas respecto a v1.0</div></div>')
    out.append('      </div>')
    out.append("    </div>")

    out.append('    <div class="card" style="margin-top:14px">')
    out.append("      <h2>Índice</h2>")
    out.append('      <div class="toc">')
    out.append('        <a href="#leyenda">Leyenda de firmas</a>')
    out.append('        <a href="#cambios">Comparativa v1.0 vs BennuGD2</a>')
    for c in cat_order:
        if c in by_cat:
            anchor = re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")
            out.append(f'        <a href="#{anchor}">{esc(c)}</a>')
    out.append("      </div>")
    out.append("    </div>")

    out.append('    <div class="card" id="leyenda" style="margin-top:14px">')
    out.append("      <h2>Leyenda de firmas Bennu</h2>")
    out.append("      <p>Las firmas de parámetros se leen de izquierda a derecha:</p>")
    out.append("      <ul class=\"tight\">")
    for k in ["I", "i", "W", "B", "S", "P", "D", "F", "N"]:
        out.append(f"        <li><code>{k}</code>: {esc(SIG_MAP[k])}</li>")
    out.append("      </ul>")
    out.append("      <p class=\"small\">Nota: una misma función puede aparecer varias veces con distinta firma (sobrecargas).</p>")
    out.append("    </div>")

    out.append('    <div class="card" id="cambios" style="margin-top:14px">')
    out.append("      <h2>Comparativa v1.0 vs BennuGD2</h2>")
    out.append("      <h3>Funciones detectadas en el manual v1.0 pero no exportadas con ese nombre en BennuGD2</h3>")
    if old_only:
        out.append("      <ul class=\"tight\">")
        for n, hint in old_only[:120]:
            if hint:
                out.append(f"        <li><code>{esc(n)}</code> → sugerencia actual: <code>{esc(hint)}</code></li>")
            else:
                out.append(f"        <li><code>{esc(n)}</code></li>")
        out.append("      </ul>")
    else:
        out.append("      <p>No se detectaron funciones antiguas ausentes con heurística de alta confianza.</p>")

    out.append("      <h3>Criterio usado</h3>")
    out.append("      <ul class=\"tight\">")
    out.append("        <li>Se toma como fuente de verdad de BennuGD2 los <code>functions_exports</code> de <code>modules/*/*_exports.h</code>.</li>")
    out.append("        <li>La presencia en v1.0 se detecta por aparición del nombre de función seguido de <code>(</code> en el texto extraído del PDF.</li>")
    out.append("        <li>La lista de funciones antiguas ausentes se filtra para evitar términos de ejemplo/no-función.</li>")
    out.append("      </ul>")
    out.append("    </div>")

    for c in cat_order:
        if c not in by_cat:
            continue
        anchor = re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")
        rows = by_cat[c]

        out.append(f'    <div class="card" id="{anchor}" style="margin-top:14px">')
        out.append(f"      <h2>{esc(c)}</h2>")
        out.append(f"      <p>Entradas: <strong>{len(rows)}</strong> (overloads). Funciones únicas: <strong>{len(set(r['name'] for r in rows))}</strong>.</p>")
        out.append('      <div class="table-wrap">')
        out.append("      <table>")
        out.append("        <thead><tr>")
        out.append("          <th>Función</th>")
        out.append("          <th>Firma</th>")
        out.append("          <th>Parámetros</th>")
        out.append("          <th>Retorno</th>")
        out.append("          <th>Compat.</th>")
        out.append("          <th>Qué hace</th>")
        out.append("          <th>Módulo / Implementación</th>")
        out.append("        </tr></thead>")
        out.append("        <tbody>")

        for e in rows:
            badge = '<span class="badge ok">Vigente desde v1</span>' if e["in_manual_v1"] else '<span class="badge new">Nueva en BennuGD2</span>'
            note = e["description"]
            if e["inline_comment"]:
                note += " Nota: " + e["inline_comment"]

            out.append("          <tr>")
            out.append(f"            <td><code>{esc(e['name'])}</code></td>")
            out.append(f"            <td><code>{esc(e['signature'])}</code></td>")
            out.append(f"            <td>{esc(e['signature_readable'])}</td>")
            out.append(f"            <td><code>{esc(e['return_type'])}</code></td>")
            out.append(f"            <td>{badge}</td>")
            out.append(f"            <td>{esc(note)}</td>")
            out.append(
                "            <td>"
                + f"<code>{esc(e['module'])}</code><br>"
                + f"<code>{esc(e['impl'])}</code><br>"
                + f"<span class='small'>{esc(e['exports_file'])}:{e['line']}</span>"
                + "</td>"
            )
            out.append("          </tr>")

        out.append("        </tbody>")
        out.append("      </table>")
        out.append("      </div>")
        out.append("    </div>")

    out.append('    <div class="footer">')
    out.append("      Manual generado automáticamente para BennuGD2 (Apple Silicon/macOS).")
    out.append("    </div>")

    out.append("  </div>")
    out.append("</body>")
    out.append("</html>")
    return "\n".join(out)


def try_generate_pdf_from_html(html_doc: str) -> bool:
    try:
        from xhtml2pdf import pisa  # type: ignore
    except Exception:
        return False

    # xhtml2pdf no soporta CSS variables modernas.
    css_vars = {
        "var(--bg)": "#f5f7fb",
        "var(--panel)": "#ffffff",
        "var(--ink)": "#15202b",
        "var(--sub)": "#4a5568",
        "var(--line)": "#d7deea",
        "var(--brand)": "#0b5fff",
        "var(--ok)": "#1f8b4c",
        "var(--new)": "#9b1c1c",
    }
    pdf_html = html_doc
    for k, v in css_vars.items():
        pdf_html = pdf_html.replace(k, v)

    # Limpiamos algunos estilos que suelen romper en renderizadores básicos.
    pdf_html = pdf_html.replace("position: sticky;", "")
    pdf_html = pdf_html.replace("box-shadow: 0 6px 20px rgba(15, 35, 95, 0.05);", "")

    with OUT_PDF.open("wb") as f:
        result = pisa.CreatePDF(pdf_html, dest=f, encoding="utf-8")
    return bool(getattr(result, "err", 1) == 0)


def main() -> None:
    if not MANUAL_TXT.exists():
        raise SystemExit(f"No existe: {MANUAL_TXT}")

    manual_text = MANUAL_TXT.read_text(encoding="utf-8", errors="ignore")
    entries = parse_exports()
    old_manual_presence(entries, manual_text)

    current_names = {e["name_norm"] for e in entries}
    old_only = extract_old_only_candidates(manual_text, current_names)

    html_doc = build_html(entries, old_only)
    OUT_HTML.write_text(html_doc, encoding="utf-8")

    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "source_manual_txt": str(MANUAL_TXT.relative_to(ROOT)).replace("\\", "/"),
        "entries_count": len(entries),
        "unique_functions": len({e["name_norm"] for e in entries}),
        "entries": entries,
        "old_only_candidates": [{"name": n, "hint": h} for n, h in old_only],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    pdf_ok = try_generate_pdf_from_html(html_doc)

    print(f"OK: {OUT_HTML}")
    print(f"OK: {OUT_JSON}")
    if pdf_ok:
        print(f"OK: {OUT_PDF}")
    else:
        print("INFO: PDF no generado (instala xhtml2pdf para exportación automática).")
    print(f"Funciones (overloads): {len(entries)}")
    print(f"Funciones únicas: {len({e['name_norm'] for e in entries})}")


if __name__ == "__main__":
    main()
