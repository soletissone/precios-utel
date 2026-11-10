"""
Aplica precios del Excel v18 al index_original.html.
Lee RESUMEN PRECIOS, zona Centro, LIC+MAE, y actualiza p[] en el HTML.
"""
import sys, os, re, openpyxl

EXCEL = r"C:\Users\SoledadMariaTissone\Downloads\TABLA_PRECIOS_2026_ABRIL_COMPLETA (18).xlsx"
SRC   = os.path.join(os.path.dirname(__file__), '..', 'index_original.html')

NIVEL_MAP = {
    'Pricing Alto':            'alto',
    'Pricing Medio':           'medio',
    'Pricing Bajo':            'bajo',
    'Ing robotica':            'robotica',
    'Arquitectura':            'arq',
    'ARQUITECTURA DE SOFTWARE':'arq_sw',
    'Egresados':               'egresados',
}
LEAD_MAP = {'Hotlead':'hot','RMKT+30':'rmkt30','RMKT+60':'rmkt60','Egresados':'rmkt'}

def leer_excel(path):
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb['RESUMEN PRECIOS']
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if i < 3: continue
        tipo = str(row[1] or '').strip()
        zona = str(row[3] or '').strip()
        if zona != 'Centro': continue
        if tipo not in ('Licenciatura','Maestría','Maestria','Maestra'): continue
        nivel = NIVEL_MAP.get(str(row[4] or '').strip(), '')
        lead  = LEAD_MAP.get(str(row[5] or '').strip(), '')
        if not nivel or not lead: continue
        pkg = str(row[11] or '').strip()
        if not pkg or pkg == 'None': continue
        p1, p2, p3 = row[6], row[7], row[8]
        if p1 is None: continue
        rows.append(dict(tipo=tipo, nivel=nivel, lead=lead, pkg=pkg,
                         p1=int(p1), p2=int(p2) if p2 else None,
                         p3=int(p3) if p3 else None))
        if i > 400: break
    wb.close()
    return rows

def aplicar(html, rows):
    changes = 0
    not_found = []
    for r in rows:
        # Buscar pkg en HTML
        pat = r"(pkg:'" + re.escape(r['pkg']) + r"',esc:'[^']+',p:\[)([^\]]+)(\])"
        m = re.search(pat, html)
        if not m:
            not_found.append(r['pkg'])
            continue
        precios_old = [float(x.strip()) for x in m.group(2).split(',')]

        # Calcular nuevos precios
        # MAE: stored p1/p2 = display+100, p3+ = display directo
        mae = r['tipo'] in ('Maestría','Maestria','Maestra')
        p_new = list(precios_old)
        if r['p1'] is not None:
            p_new[0] = (r['p1'] + 100) if mae else r['p1']
        if r['p2'] is not None and len(p_new) > 1:
            p_new[1] = (r['p2'] + 100) if mae else r['p2']
        if r['p3'] is not None and len(p_new) > 2:
            p_new[2] = r['p3']

        # Solo reemplazar si cambió algo
        if p_new == precios_old:
            continue

        # Reconstruir string respetando el resto de precios (p4, p5...)
        resto = precios_old[3:]
        p_str = ', '.join([str(int(x)) for x in p_new[:3]] + [str(int(x)) for x in resto])
        old_str = m.group(0)
        new_str = m.group(1) + p_str + m.group(3)
        html = html.replace(old_str, new_str, 1)
        print(f"  {r['pkg']:20} {r['nivel']:10} {r['lead']:8}  {[int(x) for x in precios_old[:3]]} -> {[int(x) for x in p_new[:3]]}")
        changes += 1

    if not_found:
        print(f"\nNo encontrados: {not_found}")
    return html, changes

def main():
    rows = leer_excel(EXCEL)
    print(f"Filas Excel leídas: {len(rows)}")
    html = open(SRC, encoding='utf-8').read()
    html, changes = aplicar(html, rows)
    if changes:
        open(SRC, 'w', encoding='utf-8').write(html)
        print(f"\n✓ {changes} paquetes actualizados en {os.path.basename(SRC)}")
    else:
        print("Sin cambios.")

if __name__ == '__main__':
    main()
