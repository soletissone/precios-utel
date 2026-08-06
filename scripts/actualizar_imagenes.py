"""
Actualiza imagenes_utel.json listando recursivamente la carpeta de Drive.
Corre todos los lunes via tarea programada.
Usa gdown (no requiere credenciales ni API key).
"""
import json, sys, os, re

FOLDER_URL  = "https://drive.google.com/drive/folders/1os5IimeysAOk3Q-kxpfOZS3_uydArmv8"
FOLDER_ID   = "1os5IimeysAOk3Q-kxpfOZS3_uydArmv8"
OUTPUT_PATH = r"C:\Users\SoledadMariaTissone\Documents\precios-utel\imagenes_utel.json"

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.mp4', '.mov', '.avi', '.webm'}
SKIP_FOLDERS_STARTSWITH = ('no usar', 'no_usar', 'no-usar')

def should_skip(path):
    parts = [p.strip().lower() for p in path.split('/')]
    return any(p.startswith(sw) for p in parts for sw in SKIP_FOLDERS_STARTSWITH)

def list_folder_recursive(gdown, folder_id, prefix=''):
    """Lista recursivamente una carpeta de Drive usando gdown internamente."""
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    try:
        items = gdown.download_folder(url, skip_download=True, quiet=True)
        return items or []
    except Exception as e:
        print(f"  Error listando carpeta {folder_id}: {e}")
        return []

def get_subfolder_ids(folder_id):
    """Obtiene los IDs de subcarpetas usando requests + scraping de Drive."""
    try:
        import requests
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        r = requests.get(url, timeout=30)
        # Los IDs de carpetas aparecen como /drive/folders/ID en el HTML
        ids = re.findall(r'"([a-zA-Z0-9_-]{33})"', r.text)
        return list(set(ids))
    except Exception:
        return []

def main():
    try:
        import gdown
    except ImportError:
        print("Instalando gdown...")
        os.system(f"{sys.executable} -m pip install gdown -q")
        import gdown

    sys.setrecursionlimit(5000)
    print("Listando archivos en Google Drive...")
    items = gdown.download_folder(FOLDER_URL, skip_download=True, quiet=True)
    if not items:
        print("No se encontraron archivos.")
        return

    # Detectar cuántas carpetas de primer nivel encontró
    cats_found = set()
    for item in items:
        path = item.path.replace('\\', '/')
        parts = path.split('/')
        if len(parts) >= 1:
            cats_found.add(parts[0])
    print(f"  Carpetas detectadas: {sorted(cats_found)}")

    SKIP_FOLDERS_STARTSWITH_local = SKIP_FOLDERS_STARTSWITH

    results = []
    seen_ids = set()
    for item in items:
        path = item.path.replace('\\', '/')
        if should_skip(path):
            continue
        ext = os.path.splitext(item.path)[1].lower()
        # incluir imágenes, videos, y archivos sin extensión (pueden ser imágenes en Drive)
        if (ext in IMAGE_EXTS or ext == '') and item.id not in seen_ids:
            seen_ids.add(item.id)
            results.append({
                "id":   item.id,
                "name": os.path.basename(item.path),
                "path": path
            })

    results.sort(key=lambda x: x["path"])
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"OK {len(results)} imagenes guardadas en imagenes_utel.json")
    print(f"  Carpetas en JSON: {sorted(set(r['path'].split('/')[0] for r in results))}")

if __name__ == "__main__":
    main()
