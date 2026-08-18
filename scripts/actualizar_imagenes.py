"""
Actualiza imagenes_utel.json listando recursivamente la carpeta de Drive.
Corre todos los lunes via tarea programada.
Usa gdown (no requiere credenciales ni API key).
"""
import json, sys, os

FOLDER_URL  = "https://drive.google.com/drive/folders/1os5IimeysAOk3Q-kxpfOZS3_uydArmv8"
OUTPUT_PATH = r"C:\Users\SoledadMariaTissone\Documents\precios-utel\imagenes_utel.json"

# Subcarpetas que gdown no trae completas desde la raíz — listar por separado
EXTRA_FOLDERS = {
    "Catalogo Programas": "https://drive.google.com/drive/folders/1CUyiBXbT4EAi14a5z8Oj5oQeQMvj7VRl",
}

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.mp4', '.mov', '.avi', '.webm', '.pdf'}
SKIP_FOLDERS_STARTSWITH = ('no usar', 'no_usar', 'no-usar')

def should_skip(path):
    parts = [p.strip().lower() for p in path.split('/')]
    return any(p.startswith(sw) for p in parts for sw in SKIP_FOLDERS_STARTSWITH)

def collect(items, prefix, seen_ids, results):
    for item in (items or []):
        path = item.path.replace('\\', '/')
        if prefix:
            path = prefix + '/' + path
        if should_skip(path):
            continue
        ext = os.path.splitext(item.path)[1].lower()
        if (ext in IMAGE_EXTS or ext == '') and item.id not in seen_ids:
            seen_ids.add(item.id)
            results.append({
                "id":   item.id,
                "name": os.path.basename(item.path),
                "path": path
            })

def list_folder_with_retry(gdown, url, retries=4, delay=15):
    import time
    for attempt in range(1, retries + 1):
        try:
            items = gdown.download_folder(url, skip_download=True, quiet=True) or []
            return items
        except Exception as e:
            print(f"  Error intento {attempt}/{retries}: {e}")
            if attempt < retries:
                print(f"  Reintentando en {delay}s...")
                time.sleep(delay)
    print("  Todos los reintentos fallaron, se omite esta carpeta.")
    return []

def main():
    try:
        import gdown
    except ImportError:
        print("Instalando gdown...")
        os.system(f"{sys.executable} -m pip install gdown -q")
        import gdown

    sys.setrecursionlimit(5000)
    seen_ids = set()
    results = []

    # 1. Listar subcarpetas extra PRIMERO para que sus IDs tengan prioridad
    for folder_name, folder_url in EXTRA_FOLDERS.items():
        print(f"Listando {folder_name}...")
        extra_items = list_folder_with_retry(gdown, folder_url)
        before = len(results)
        collect(extra_items, folder_name, seen_ids, results)
        print(f"  +{len(results)-before} items de {folder_name}")

    # 2. Listar carpeta raíz (los IDs ya en EXTRA_FOLDERS se saltan automáticamente)
    print("Listando carpeta raíz...")
    root_items = list_folder_with_retry(gdown, FOLDER_URL)
    before = len(results)
    collect(root_items, '', seen_ids, results)
    print(f"  +{len(results)-before} items desde raíz")

    results.sort(key=lambda x: x["path"])
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    cats = sorted(set(r['path'].split('/')[0] for r in results))
    print(f"\nOK {len(results)} recursos guardados")
    print(f"  Carpetas: {cats}")

if __name__ == "__main__":
    main()
