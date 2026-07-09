# -*- coding: utf-8 -*-
"""
Build de la calculadora internacional UTEL.

Toma los 3 CSV de datos_trabajo/ (copiados desde Downloads) y genera, para
cada uno de los 7 paises internacionales, un archivo autocontenido en
internacional/<slug>/index.html con SOLO los datos de ese pais embebidos.

Re-ejecutable: al reemplazar los CSV en datos_trabajo/ y volver a correr
este script, se regeneran los 7 archivos con los datos nuevos.

NO toca Documents/precios-utel/index.html (Mexico, produccion).
"""
import csv
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_DIR = os.path.join(BASE_DIR, 'datos_trabajo')
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates', 'internacional_template.html')
OUT_DIR = os.path.join(BASE_DIR, 'internacional')

CONSOLIDADO_CSV = os.path.join(DATOS_DIR, 'consolidado_programas.csv')
RESUMEN_CSV = os.path.join(DATOS_DIR, 'resumen_precios_internacional.csv')
ACCESORIOS_CSV = os.path.join(DATOS_DIR, 'precio_accesorios.csv')

BUILD_VERSION = '2026070801'

# slug, nombre para mostrar, clave de acceso, nombre exacto en columna "Pais" del CSV de precios,
# y nombre exacto de columna en el bloque de accesorios (grupo de a 3: Lic/Maestria/Doctorado)
PAISES = [
    {'slug': 'peru',         'nombre': 'Perú',           'clave': 'UTELPER2026*', 'csv_pais': 'Peru'},
    {'slug': 'colombia',     'nombre': 'Colombia',       'clave': 'UTELCOL2026*', 'csv_pais': 'Colombia'},
    {'slug': 'ecuador',      'nombre': 'Ecuador',        'clave': 'UTELECU2026*', 'csv_pais': 'Ecuador'},
    {'slug': 'r-dominicana', 'nombre': 'República Dominicana', 'clave': 'UTELDOM2026*', 'csv_pais': 'R.Dominicana'},
    {'slug': 'el-salvador',  'nombre': 'El Salvador',    'clave': 'UTELSLV2026*', 'csv_pais': 'El Salvador'},
    {'slug': 'guatemala',    'nombre': 'Guatemala',      'clave': 'UTELGTM2026*', 'csv_pais': 'Guatemala'},
    {'slug': 'usa',          'nombre': 'Estados Unidos', 'clave': 'UTELUSA2026*', 'csv_pais': 'USA'},
]

# Orden de columnas en el CSV de accesorios: Mexico, Peru, Colombia, Ecuador,
# Dominicana, Salvador, Guatemala, USA -- en grupos de 3 (Lic, Maestria, Doctorado)
ACCESORIOS_PAIS_ORDEN = ['Mexico', 'Peru', 'Colombia', 'Ecuador', 'Dominicana', 'Salvador', 'Guatemala', 'USA']
CSV_PAIS_TO_ACC_COL = {
    'Peru': 'Peru',
    'Colombia': 'Colombia',
    'Ecuador': 'Ecuador',
    'R.Dominicana': 'Dominicana',
    'El Salvador': 'Salvador',
    'Guatemala': 'Guatemala',
    'USA': 'USA',
}

# Mapeo id interno -> (grupo mostrado, nombre mostrado, nombre de fila en el CSV de accesorios)
ACCESORIOS_DEF = [
    ('tit',                'Titulación',    'Titulación',           'Tit'),
    ('titulo50',           'Titulación',    'Título 50%',           'Título 50%'),
    ('welbe',              'Bienestar',     'Welbe',                'Welbe'),
    ('welbe_premium',      'Bienestar',     'Welbe Premium',        'Welbe Premium'),
    ('asistencia_plus',    'Bienestar',     'Asistencia Plus',      'Asistencia Plus'),
    ('sesiones_ejecutivas','Experiencia',   'Sesiones Ejecutivas',  'Sesiones Ejecutivas'),
    ('hibridas',           'Experiencia',   'Híbridas',             'Híbridas'),
    ('senior_mayor',       'Experiencia',   'Senior/Mayor',         'Senior/Mayor'),
    ('utel_joven',         'Experiencia',   'Utel Jóven',           'Utel Jóven'),
    ('utel_x',             'Plataforma',    'Utel x',               'Utel x'),
    ('ucamp',              'Plataforma',    'U-Camp',               'U generico'),  # ver nota abajo
    ('cambridge',          'Idioma',        'Cambridge',            'Cambridge'),
    ('voxy',               'Idioma',        'Voxy',                 'Voxy'),
    ('duolingo',           'Idioma',        'Duolingo',             'Duolingo'),
    ('utel_ingles',        'Idioma',        'Utel en Inglés',       'Utel en Ingles'),
    ('coursera',           'Certificación', 'Coursera',             'Coursera'),
    ('facebook',           'Certificación', 'Facebook',             'Facebook'),
    ('cifal',              'Certificación', 'Cifal Ciberseguridad', 'Cifal Ciberseguridad'),
    ('microsoft',          'Certificación', 'Microsoft',            'Microsoft'),
    ('tableau',            'Certificación', 'Tableau',              'Tableau'),
    ('gcloud',             'Certificación', 'Google Cloud',         'Google Cloud'),
    ('gads',               'Certificación', 'Google Ads',           'Google Ads'),
    ('legal',              'Certificación', 'Legaltech',            'Legaltech'),
    ('platzi',             'Certificación', 'Platzi',               'Platzi'),
]
# Nota: "U generico" fue reemplazado por "U-Camp" segun Reglas.csv ("U-Camp es el
# unico accesorio de plataforma, se elimino U Generico"). Como el CSV de accesorios
# todavia trae la fila "U generico", la usamos como fuente de precio para U-Camp.

NIVELES_VALIDOS = ('Licenciatura', 'Maestria', 'Doctorado')

UCAMP_PROGRAMAS = [
    "LICENCIATURA EN INGENIERÍA INDUSTRIAL",
    "LICENCIATURA EN INGENIERÍA EN SISTEMAS COMPUTACIONALES",
    "LICENCIATURA EN INGENIERÍA INDUSTRIAL Y ADMINISTRACIÓN",
    "LICENCIATURA EN INGENIERÍA EN LOGÍSTICA Y TRANSPORTE",
    "LICENCIATURA EN INTELIGENCIA ARTIFICIAL",
    "LICENCIATURA EN INGENIERÍA EN ENERGÍAS RENOVABLES",
    "LICENCIATURA EN INGENIERÍA EN DESARROLLO DE SOFTWARE",
    "LICENCIATURA EN SEGURIDAD INFORMÁTICA",
    "LICENCIATURA EN INTELIGENCIA ARTIFICIAL APLICADA A NEGOCIOS, INDUSTRIA Y AUTOMATIZACIÓN",
    "Licenciatura en Ética y Gobernanza de la Inteligencia Artificial",
    "Licenciatura en Ciberseguridad y Riesgos en Inteligencia Artificial",
    "Licenciatura en Innovación y Emprendimiento con Inteligencia Artificial",
    "Licenciatura en Inteligencia Artificial en Educación",
    "Licenciatura en Ingeniería en Ciencias de Datos e Inteligencia Analítica",
    "Licenciatura en Ingeniería en Programación en la Nube",
    "Licenciatura en Software para Entretenimiento Digital",
    "Licenciatura en Ingeniería en Sistemas Inteligentes",
    "Licenciatura en Ingeniería en Tecnología de Videojuegos y Realidad Virtual",
    "Licenciatura en Comercio Electrónico y Negocios Digitales",
    "Licenciatura en Tecnologías Interactivas y Virtuales",
    "Licenciatura en Ingeniería Ambiental",
    "Licenciatura en Ingeniería Robótica",
]
UCAMP_PROGRAMAS_LOWER = set(p.lower() for p in UCAMP_PROGRAMAS)


def norm_nivel(nivel):
    nivel = (nivel or '').strip()
    if nivel in ('Licenciaturas',):
        return 'Licenciatura'
    if nivel in ('Maestrias',):
        return 'Maestria'
    return nivel


def norm_tier(tipo_promo):
    """Normaliza el TIPO DE PROMO a uno de los tiers validos, o None si no aplica."""
    t = (tipo_promo or '').strip()
    t_up = t.upper()
    # normalizar typo Princing -> Pricing
    t_up = t_up.replace('PRINCING', 'PRICING')
    if t_up in ('PRICING ALTO', 'PRICING BAJO', 'PRICING MEDIO'):
        return t_up.title().replace('Alto', 'Alto').replace('Bajo', 'Bajo').replace('Medio', 'Medio')
    return None


def norm_tier_display(t_up):
    mapping = {
        'PRICING ALTO': 'Pricing Alto',
        'PRICING BAJO': 'Pricing Bajo',
        'PRICING MEDIO': 'Pricing Medio',
    }
    return mapping.get(t_up)


# -------------------- 1) LEER CATALOGO DE PROGRAMAS --------------------

def leer_catalogo():
    """Devuelve lista de dicts: {nombre, nivel, tier, ucamp}
    Excluye Diplomado/Especialidad y filas de alianzas especiales (UNICA, UVE,
    UNAG, CECIP, Arquitectura, Ing robotica, Arquitectura de software,
    CIE DAT E IA...) que no tienen precio en la grilla internacional.

    Doctorado es especial: el tier que se usa para el join de precios NO es
    Pricing Alto/Medio/Bajo sino "Doc. Educacion" / "Resto de los Doc."
    (ver TODO abajo, asuncion a confirmar con Sole).
    """
    incluidos = []
    excluidos_total = 0
    excluidos_detalle = {}

    with open(CONSOLIDADO_CSV, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    data_rows = rows[1:]  # fila 0 es encabezado

    for row in data_rows:
        if len(row) < 5:
            continue
        nivel_raw = row[1].strip()
        nombre = row[3].strip()
        tipo_promo_raw = row[4].strip()

        if not nombre:
            continue

        nivel = norm_nivel(nivel_raw)

        if nivel not in NIVELES_VALIDOS:
            excluidos_total += 1
            excluidos_detalle[nivel_raw] = excluidos_detalle.get(nivel_raw, 0) + 1
            continue

        if nivel == 'Doctorado':
            tier_up = (tipo_promo_raw or '').strip().upper().replace('PRINCING', 'PRICING')
            if tier_up not in ('PRICING ALTO', 'PRICING MEDIO', 'PRICING BAJO'):
                # alianzas especiales de doctorado (UNAG, CIE DAT E IA...)
                excluidos_total += 1
                key = 'Doctorado (alianza: %s)' % tipo_promo_raw
                excluidos_detalle[key] = excluidos_detalle.get(key, 0) + 1
                continue
            # TODO confirmar con Sole: "DOCTORADO EN EDUCACIÓN" usa tier
            # "Doc. Educacion"; todos los demas doctorados con tier
            # Alto/Medio/Bajo usan "Resto de los Doc."
            if nombre.strip().upper() == 'DOCTORADO EN EDUCACIÓN':
                tier_final = 'Doc. Educacion'
            else:
                tier_final = 'Resto de los Doc.'
        else:
            tier_final = norm_tier(tipo_promo_raw)
            if tier_final is None:
                excluidos_total += 1
                key = '%s (alianza: %s)' % (nivel, tipo_promo_raw)
                excluidos_detalle[key] = excluidos_detalle.get(key, 0) + 1
                continue

        incluidos.append({
            'nombre': nombre,
            'nivel': nivel,
            'tier': tier_final,
        })

    return incluidos, excluidos_total, excluidos_detalle


# -------------------- 2) LEER GRILLA DE PRECIOS INTERNACIONAL --------------------

def norm_promo_grid(s):
    s = (s or '').strip()
    s_norm = re.sub(r'(?i)princing', 'Pricing', s)
    return s_norm


def parse_money(s):
    s = (s or '').strip()
    if s == '' or s.upper() == 'N/A':
        return None
    s = s.replace('$', '').strip()
    s = s.replace(',', '')
    # En la hoja de accesorios, Colombia usa "." como separador de miles
    # (ej. "$106.900" = 106900, no 106.9). Como en este negocio no hay
    # precios con centavos, cualquier ".XXX" (punto seguido de 3 digitos)
    # se interpreta como separador de miles, no como decimal.
    s = re.sub(r'\.(\d{3})\b', r'\1', s)
    try:
        if '.' in s:
            return float(s)
        return int(s)
    except ValueError:
        return None


def leer_grilla_precios():
    """Devuelve dict: csv_pais -> lista de filas
    {nivel, jornada, tier, antiguedad, pagos:[...], nombrePaquete, precioLista}

    Detecta claves duplicadas (mismo pais+nivel+jornada+tier+antiguedad con
    valores distintos) y las excluye del resultado (se resuelven como
    "no disponible" en la UI en vez de adivinar cual es la correcta).
    """
    with open(RESUMEN_CSV, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    header = rows[1]
    data = rows[2:]

    todos_por_pais = {}
    for row in data:
        if len(row) < 15:
            continue
        pais = row[0].strip()
        if pais not in CSV_PAIS_TO_ACC_COL:
            continue
        nivel = norm_nivel(row[1].strip())
        jornada = row[2].strip()
        tier_raw = norm_promo_grid(row[4])
        tier_up = tier_raw.upper()
        antig = row[5].strip()

        # tier tal cual aparece en la grilla, pero normalizando el typo Princing->Pricing
        # y dejando pasar los tiers especiales de Doctorado / Colombia
        if tier_up in ('PRICING ALTO', 'PRICING MEDIO', 'PRICING BAJO'):
            tier = norm_tier_display(tier_up)
        else:
            tier = tier_raw  # "Doc. Educacion", "Resto de los Doc.", "Pricing Especial", etc.

        pagos_raw = row[6:11]
        pagos = [parse_money(p) for p in pagos_raw]
        if any(p is None for p in pagos):
            # fila incompleta, no se puede armar tabla de pagos confiable
            continue
        nombre_paquete = row[11].strip() if len(row) > 11 else ''
        precio_lista = parse_money(row[14]) if len(row) > 14 else None

        # "EQUSA" = Titulo con equivalencia en USA (confirmado por Sole). Aparece
        # como un fragmento dentro del codigo de "Nombre paquete" (no hay columna
        # propia). Se trata como una dimension mas del join, igual que Jornada o
        # Antiguedad: si para una misma combinacion existen ambas variantes
        # (con y sin EQUSA), la UI ofrece un selector; si solo existe una, se usa
        # directo sin preguntar.
        equsa = 'EQUSA' in nombre_paquete.upper()

        key = (nivel, jornada, tier, antig, equsa)
        todos_por_pais.setdefault(pais, {}).setdefault(key, []).append({
            'nivel': nivel,
            'jornada': jornada,
            'tier': tier,
            'antiguedad': antig,
            'equsa': equsa,
            'pagos': pagos,
            'nombrePaquete': nombre_paquete,
            'precioLista': precio_lista,
        })

    resultado = {}
    ambiguas_por_pais = {}
    for pais, grupos in todos_por_pais.items():
        filas_ok = []
        ambiguas = 0
        for key, filas in grupos.items():
            if len(filas) == 1:
                filas_ok.append(filas[0])
            else:
                # combinacion ambigua en la fuente (mismo join key, precios
                # distintos) -> no se adivina, se omite. La UI mostrara
                # "No disponible para esta combinacion" para esta llave.
                ambiguas += 1
        resultado[pais] = filas_ok
        ambiguas_por_pais[pais] = ambiguas

    return resultado, ambiguas_por_pais


# -------------------- 3) LEER ACCESORIOS --------------------

def leer_accesorios():
    """Devuelve dict: csv_pais -> lista de accesorios con precio (id, grupo,
    nombre, precios:{nivel: valor}). Si TODOS los valores de un pais estan
    vacios, la lista queda vacia (la UI mostrara "proximamente")."""
    with open(ACCESORIOS_CSV, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # fila 0: nombres de pais cada 3 columnas (col 2 = inicio Mexico, etc.)
    fila_paises = rows[0]
    fila_niveles = rows[1]  # Licenciatura/Maestria/Doctorado repetido

    # localizar el rango de columnas de cada pais
    col_ranges = {}  # pais -> (col_lic, col_mae, col_doc)
    i = 2
    idx_pais = 0
    while i < len(fila_paises) and idx_pais < len(ACCESORIOS_PAIS_ORDEN):
        pais_nombre = ACCESORIOS_PAIS_ORDEN[idx_pais]
        col_ranges[pais_nombre] = (i, i + 1, i + 2)
        i += 3
        idx_pais += 1

    # indexar filas de accesorios por nombre-de-fila (columna 1)
    filas_por_nombre = {}
    for row in rows[2:]:
        if len(row) < 2:
            continue
        nombre_fila = row[1].strip()
        if not nombre_fila:
            continue
        filas_por_nombre[nombre_fila] = row

    resultado = {}
    for csv_pais, acc_col_name in CSV_PAIS_TO_ACC_COL.items():
        col_lic, col_mae, col_doc = col_ranges[acc_col_name]
        lista = []
        for (acc_id, grupo, nombre, nombre_fila_csv) in ACCESORIOS_DEF:
            row = filas_por_nombre.get(nombre_fila_csv)
            if row is None:
                continue
            precios = {}
            for nivel, col in (('Licenciatura', col_lic), ('Maestria', col_mae), ('Doctorado', col_doc)):
                val = None
                if col < len(row):
                    val = parse_money(row[col])
                # "N/A" (o celda vacia) = no se ofrece ese accesorio para ese
                # pais+nivel -> no se agrega la clave, y la UI no muestra el
                # boton (igual que Mexico trata sus "N/A"). Solo se guarda si
                # hay un valor real (incluido $0, ej. Voxy gratis).
                if val is not None:
                    precios[nivel] = val
            lista.append({
                'id': acc_id,
                'grupo': grupo,
                'nombre': nombre,
                'precios': precios,
                'incluido': acc_id == 'voxy',  # Voxy viene incluido de base (ver Reglas.csv)
                })
        resultado[csv_pais] = lista

    return resultado


# -------------------- 4) GENERAR PAGINAS --------------------

def build():
    catalogo, excluidos_total, excluidos_detalle = leer_catalogo()
    grilla_por_pais, ambiguas_por_pais = leer_grilla_precios()
    accesorios_por_pais = leer_accesorios()

    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        template = f.read()

    catalogo_json = json.dumps(catalogo, ensure_ascii=False)

    conteo_por_nivel = {}
    for p in catalogo:
        conteo_por_nivel[p['nivel']] = conteo_por_nivel.get(p['nivel'], 0) + 1

    os.makedirs(OUT_DIR, exist_ok=True)

    reporte = []
    for pais_cfg in PAISES:
        slug = pais_cfg['slug']
        csv_pais = pais_cfg['csv_pais']
        precios_pais = grilla_por_pais.get(csv_pais, [])
        accesorios_pais = accesorios_por_pais.get(csv_pais, [])

        html = template
        html = html.replace('__PAIS_NOMBRE__', pais_cfg['nombre'])
        html = html.replace('__PAIS_CLAVE__', pais_cfg['clave'])
        html = html.replace('__BUILD_VERSION__', BUILD_VERSION)
        html = html.replace('__CATALOGO_JSON__', catalogo_json)
        html = html.replace('__PRECIOS_JSON__', json.dumps(precios_pais, ensure_ascii=False))
        html = html.replace('__ACCESORIOS_JSON__', json.dumps(accesorios_pais, ensure_ascii=False))

        out_dir_pais = os.path.join(OUT_DIR, slug)
        os.makedirs(out_dir_pais, exist_ok=True)
        out_path = os.path.join(out_dir_pais, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)

        reporte.append({
            'pais': pais_cfg['nombre'],
            'slug': slug,
            'filas_precio': len(precios_pais),
            'combinaciones_ambiguas_omitidas': ambiguas_por_pais.get(csv_pais, 0),
            'accesorios_con_precio': len(accesorios_pais),
            'path': out_path,
        })

    print('=== CATALOGO ===')
    print('Incluidos:', len(catalogo), conteo_por_nivel)
    print('Excluidos:', excluidos_total, excluidos_detalle)
    print()
    print('=== PAGINAS GENERADAS ===')
    for r in reporte:
        print(r)


if __name__ == '__main__':
    build()
