# widgets/rename_dialog.py
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QPushButton
)


class RenameDialog(QDialog):
    """
    Rename prompt. Caller reads .result_path after exec_().
    Returns None if user cancelled.
    """

    def __init__(self, abs_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename")
        self.setModal(True)

        self._orig_path = Path(abs_path)
        self._result_path: str | None = None

        self._edit = QLineEdit(self._orig_path.name, self)
        self._edit.selectAll()
        self._edit.returnPressed.connect(self.accept)

        main = QVBoxLayout(self)
        main.addWidget(QLabel(f"Rename '{self._orig_path.name}' to:"))
        main.addWidget(self._edit)

        btns = QHBoxLayout()
        ok = QPushButton("OK")

        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        btns.addStretch(1)

        btns.addWidget(ok)
        btns.addWidget(cancel)

        main.addLayout(btns)

    def accept(self):
        new_name = self._edit.text().strip()
        if not new_name:
            return
        self._result_path = str(self._orig_path.with_name(new_name))
        super().accept()

    # read-only property for caller
    @property
    def result_path(self) -> str | None:
        return self._result_path
