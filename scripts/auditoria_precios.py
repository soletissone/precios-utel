"""
AUDITORÍA DE PRECIOS — precios-utel
Compara el Excel de tabla de precios contra index_original.html
y muestra TODAS las diferencias antes de tocar el código.

Uso:
    py auditoria_precios.py [ruta_excel]

Si no se pasa ruta, busca el archivo más reciente en Downloads
que tenga "TABLA_PRECIOS" en el nombre.
"""
import sys, os, re, glob, openpyxl

SRC_HTML = os.path.join(os.path.dirname(__file__), '..', 'index_original.html')

def encontrar_excel():
    downloads = os.path.expanduser(r'~\Downloads')
    pattern = os.path.join(downloads, '*TABLA_PRECIOS*.xlsx')
    archivos = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return archivos[0] if archivos else None

# ── Leer Excel (solo Centro) ─────────────────────────────────────
NIVEL_MAP = {
    'Pricing Alto':            'alto',
    'Pricing Medio':           'medio',
    'Pricing Bajo':            'bajo',
    'Ing robotica':            'robotica',
    'Arquitectura':            'arq',
    'ARQUITECTURA DE SOFTWARE':'arq_sw',
    'Egresados':               'egresados',
}
LEAD_MAP = {
    'Hotlead':  'hot',
    'RMKT+30':  'rmkt30',
    'RMKT+60':  'rmkt60',
    'Egresados':'rmkt',
}

def leer_excel(path):
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb['RESUMEN PRECIOS']
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        vals = list(row)
        tipo  = str(vals[1] or '').strip()
        jorx  = str(vals[2] or '').strip()
        zona  = str(vals[3] or '').strip()
        if zona != 'Centro': continue
        if tipo not in ('Licenciatura','Maestría','Maestria'): continue
        nivel = NIVEL_MAP.get(str(vals[4] or '').strip(), '')
        lead  = LEAD_MAP.get(str(vals[5] or '').strip(), '')
        if not nivel or not lead: continue
        pkg = str(vals[11] or '').strip()
        esc = str(vals[12] or '').strip()
        if not pkg or pkg == 'None': continue
        rows.append(dict(
            tipo=tipo, jornada=jorx, nivel=nivel, lead=lead,
            p1=vals[6], p2=vals[7], p3=vals[8],
            pkg=pkg, esc=esc
        ))
        if i > 200: break
    wb.close()
    return rows

# ── Leer HTML: extraer PROG completo por sección ─────────────────
SECTION_KEYWORDS = {
    'Intensiva':       ['online_general','intensiva'],
    'Super Intensiva': ['online_general','super'],
    'Completa':        ['online_general','completa'],
    'Maestría':        ['mae_online'],
    'Maestria':        ['mae_online'],
}

# Para cada (pkg, sección_esperada) extraer esc/p[] desde el HTML
# Buscamos el pkg dentro del bloque correcto de PROG
def extraer_bloque(html, seccion_key):
    """Extrae el sub-bloque de PROG que comienza con seccion_key:{"""
    pat = re.escape(seccion_key) + r':\{(.*?)(?=\n  [a-z_]+:\{|\nvar |\Z)'
    m = re.search(pat, html, re.DOTALL)
    return m.group(0) if m else ''

def buscar_en_bloque(bloque, pkg):
    pat = r"pkg:'" + re.escape(pkg) + r"',esc:'([^']+)',p:\[([^\]]+)\]"
    m = re.search(pat, bloque)
    if not m: return None, None, None, None
    esc = m.group(1)
    precios = [float(x.strip()) for x in m.group(2).split(',')]
    return esc, precios[0], precios[1] if len(precios)>1 else None, precios[2] if len(precios)>2 else None

# Para robotica/arq intensiva: buscar en el bloque específico
NIVEL_PROG_KEY = {
    'alto':'alto','medio':'medio','bajo':'bajo',
    'robotica':'robotica','arq':'arquitectura','arq_sw':'mae_online',
    'egresados':'mae_online',
}

def encontrar_pkg(html, row):
    pkg = row['pkg']
    jornada = row['jornada']
    nivel   = row['nivel']

    # MAE: buscar en mae_online
    if row['tipo'] in ('Maestría','Maestria'):
        bloque = extraer_bloque(html, 'mae_online')
        return buscar_en_bloque(bloque, pkg)

    # LIC Robótica: buscar en bloque robotica
    if nivel == 'robotica':
        bloque = extraer_bloque(html, 'robotica')
        return buscar_en_bloque(bloque, pkg)

    # LIC Arquitectura: buscar en bloque arquitectura
    if nivel == 'arq':
        bloque = extraer_bloque(html, 'arquitectura')
        return buscar_en_bloque(bloque, pkg)

    # LIC regular: buscar en online_general
    bloque = extraer_bloque(html, 'online_general')
    return buscar_en_bloque(bloque, pkg)

# ── Comparar ─────────────────────────────────────────────────────
def comparar(excel_rows, html):
    diffs = []
    ok_count = 0
    for r in excel_rows:
        esc_html, p1_html, p2_html, p3_html = encontrar_pkg(html, r)
        if esc_html is None:
            diffs.append({**r, 'campo':'TODO', 'actual':'???', 'esperado':'???', 'nota':'⚠ pkg no encontrado'})
            continue
        # MAE: p[] guarda display+100 para p1/p2 (el JS hace v-100 al mostrar)
        mae_offset = 100 if r['tipo'] in ('Maestría','Maestria') else 0
        checks = [
            ('p1', p1_html - mae_offset if p1_html else p1_html, r['p1']),
            ('p2', p2_html - mae_offset if p2_html else p2_html, r['p2']),
            ('p3', p3_html, r['p3']),
            ('esc', esc_html, r['esc']),
        ]
        for campo, actual, esperado in checks:
            if esperado is None: continue
            try:
                match = abs(float(actual) - float(esperado)) < 0.01
            except:
                match = str(actual) == str(esperado)
            if not match:
                diffs.append({**r, 'campo':campo, 'actual':actual, 'esperado':esperado, 'nota':'✗'})
            else:
                ok_count += 1
    return diffs, ok_count

# ── Main ─────────────────────────────────────────────────────────
def main():
    excel_path = sys.argv[1] if len(sys.argv) > 1 else encontrar_excel()
    if not excel_path:
        print("No se encontró archivo Excel. Pasá la ruta como argumento.")
        sys.exit(1)
    print(f"Excel : {os.path.basename(excel_path)}")
    print(f"HTML  : {os.path.abspath(SRC_HTML)}\n")

    rows  = leer_excel(excel_path)
    html  = open(SRC_HTML, encoding='utf-8').read()
    diffs, ok_count = comparar(rows, html)

    if not diffs:
        print(f"✓ Todo cuadra ({ok_count} campos verificados, 0 diferencias)")
        return

    print(f"{'Jornada':15} {'Nivel':10} {'Lead':8} {'Pkg':18} {'Campo':5}  {'Actual':12} {'Excel':12}")
    print("-" * 85)
    for d in diffs:
        print(f"{d['jornada']:15} {d['nivel']:10} {d['lead']:8} {d['pkg']:18} {d['campo']:5}  {str(d['actual']):12} {str(d['esperado']):12}")
    print(f"\n{len(diffs)} diferencias  |  {ok_count} campos OK")

if __name__ == '__main__':
    main()
