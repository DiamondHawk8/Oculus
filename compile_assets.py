import subprocess
import os

# Paths
UI_PATH = "ui/main.ui"
UI_OUTPUT = "ui/ui_main.py"
QRC_PATH = "resources/resources.qrc"
QRC_OUTPUT = "resources/resources_rc.py"

WIDGETS_PATHS = {
    "ui/gallery_tab.ui": "ui/ui_gallery_tab.py",
    "ui/collision_dialog.ui": "ui/ui_collision_dialog.py",
    "ui/metadata_dialog.ui": "ui/ui_metadata_dialog.py",
}


def compile_ui():
    print(f"[UI] Compiling {UI_PATH} → {UI_OUTPUT}")
    result = subprocess.run(["pyside6-uic", UI_PATH, "-o", UI_OUTPUT])
    if result.returncode == 0:
        print("[UI] ui_main.py compiled successfully.")
    else:
        print("[UI] Failed to compile main.ui")


def compile_widgets():
    for ui, output_file in WIDGETS_PATHS.items():
        print(f"[WIDGET] COMPILING {ui} → {output_file}")
        result = subprocess.run(["pyside6-uic", ui, "-o", output_file])
        if result.returncode == 0:
            print(f"[WIDGET] {ui} compiled successfully.")
        else:
            print(f"[WIDGET] Failed to compile {ui}")


def compile_qrc():
    print(f"[QRC] Compiling {QRC_PATH} → {QRC_OUTPUT}")
    result = subprocess.run(["pyside6-rcc", QRC_PATH, "-o", QRC_OUTPUT])
    if result.returncode == 0:
        print("[QRC] resources_rc.py compiled successfully.")
    else:
        print("[QRC] Failed to compile resources.qrc")


def patch_import():
    file_paths = ["ui/ui_main.py", "ui/ui_gallery_tab.py", "ui/ui_floating_pane.py"]
    for file_path in file_paths:
        with open(file_path, "r+", encoding="utf-8") as f:
            lines = f.readlines()
            f.seek(0)
            for line in lines:
                if line.strip() == "import resources_rc":
                    f.write("from resources import resources_rc\n")
                else:
                    f.write(line)
            f.truncate()
        print(f"[Patch] Patched {file_path} import")


if __name__ == "__main__":
    if not os.path.exists(UI_PATH):
        print(f"[X] main.ui not found at {UI_PATH}")
    else:
        compile_ui()

    if not os.path.exists(QRC_PATH):
        print(f"[X] resources.qrc not found at {QRC_PATH}")
    else:
        compile_qrc()

    compile_widgets()

    patch_import()
