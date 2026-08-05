"""
Actualiza imagenes_utel.json listando recursivamente la carpeta de Drive.
Corre todos los lunes via tarea programada.
Usa gdown (no requiere credenciales ni API key).
"""
import json, sys, os

FOLDER_URL  = "https://drive.google.com/drive/folders/1os5IimeysAOk3Q-kxpfOZS3_uydArmv8"
OUTPUT_PATH = r"C:\Users\SoledadMariaTissone\Documents\precios-utel\imagenes_utel.json"

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}

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

    SKIP_FOLDERS_STARTSWITH = ('no usar', 'no_usar', 'no-usar')

    results = []
    for item in items:
        path = item.path.replace('\\', '/')
        # Excluir archivos dentro de carpetas "no usar"
        path_parts = [p.strip().lower() for p in path.split('/')]
        if any(p.startswith(sw) for p in path_parts for sw in SKIP_FOLDERS_STARTSWITH):
            continue
        ext = os.path.splitext(item.path)[1].lower()
        if ext in IMAGE_EXTS:
            results.append({
                "id":   item.id,
                "name": os.path.basename(item.path),
                "path": path
            })

    results.sort(key=lambda x: x["path"])
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"OK {len(results)} imagenes guardadas en imagenes_utel.json")

if __name__ == "__main__":
    main()
