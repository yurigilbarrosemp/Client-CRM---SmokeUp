#!/bin/bash
# build_nuitka.sh

echo "Compilando com Nuitka..."

# Instalar dependências do sistema para Nuitka
sudo apt-get update
sudo apt-get install -y patchelf

# Compilar com Nuitka
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyqt5 \
    --include-package=PyQt5 \
    --include-package=matplotlib \
    --include-package=numpy \
    --include-package=sqlite3 \
    --output-dir=dist \
    tabacaria_crm.py

echo "Compilação concluída! Verifique a pasta dist/"