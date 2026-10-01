@echo off
cd /d "C:\Users\SoledadMariaTissone\Documents\precios-utel"
"C:\Users\SoledadMariaTissone\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts\actualizar_imagenes.py
git add imagenes_utel.json index.html
git commit -m "Auto: actualizar recursos imagenes_utel.json y galeria"
git pull --rebase
git push
