import subprocess
import os

# Paths
UI_PATH = "ui/main.ui"
UI_OUTPUT = "ui/ui_main.py"
QRC_PATH = "resources/resources.qrc"
QRC_OUTPUT = "resources/resources_rc.py"

def compile_ui():
    print(f"[UI] Compiling {UI_PATH} → {UI_OUTPUT}")
    result = subprocess.run(["pyside6-uic", UI_PATH, "-o", UI_OUTPUT])
    if result.returncode == 0:
        print("[UI] ui_main.py compiled successfully.")
    else:
        print("[UI] Failed to compile main.ui")

def compile_qrc():
    print(f"[QRC] Compiling {QRC_PATH} → {QRC_OUTPUT}")
    result = subprocess.run(["pyside6-rcc", QRC_PATH, "-o", QRC_OUTPUT])
    if result.returncode == 0:
        print("[QRC] resources_rc.py compiled successfully.")
    else:
        print("[QRC] Failed to compile resources.qrc")

# Patch ui_main.py to fix import (theres probably a better way to do this)
def patch_ui_import():
    file_path = "ui/ui_main.py"
    with open(file_path, "r+", encoding="utf-8") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line.strip() == "import resources_rc":
                f.write("from resources import resources_rc\n")
            else:
                f.write(line)
        f.truncate()
    print("[Patch] Patched ui_main.py import")


if __name__ == "__main__":
    if not os.path.exists(UI_PATH):
        print(f"[X] main.ui not found at {UI_PATH}")
    else:
        compile_ui()

    if not os.path.exists(QRC_PATH):
        print(f"[X] resources.qrc not found at {QRC_PATH}")
    else:
        compile_qrc()

    patch_ui_import()
