# hooks/hook-PyQt5.py
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Coletar todos os submódulos do PyQt5
hiddenimports = collect_submodules('PyQt5')

# Coletar arquivos de dados do PyQt5
datas = collect_data_files('PyQt5')