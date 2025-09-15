import sys
import os
from cx_Freeze import setup, Executable

# Dependências automaticamente detectadas
build_exe_options = {
    "packages": ["os", "sys", "sqlite3", "datetime", "json", "PyQt5", "matplotlib", "numpy"],
    "excludes": ["tkinter", "unittest", "email", "http", "urllib", "xml", "pydoc"],
    "include_files": [],
    "optimize": 2
}

# Configuração base
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Nome do aplicativo
app_name = "TabacariaCRM"

setup(
    name=app_name,
    version="1.0",
    description="Sistema de CRM para Tabacaria",
    options={"build_exe": build_exe_options},
    executables=[Executable("tabacaria_crm.py", base=base, target_name=app_name)]
)