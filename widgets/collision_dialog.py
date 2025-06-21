from PySide6.QtWidgets import QDialog
from ui.ui_collision_dialog import Ui_CollisionDialog


class CollisionDialog(QDialog):
    """
    Modal dialog for name collisions
    """
    _MAP = {
        "btn_overwrite": "overwrite",
        "btn_auto": "auto",
        "btn_skip": "skip",
        "btn_cancel": "cancel",
    }

    def __init__(self, src: str, dst: str, parent=None):
        super().__init__(parent)
        self.ui = Ui_CollisionDialog()
        self.ui.setupUi(self)

        self._choice = "cancel"

        self.ui.label_info.setText(
            f"Destination already exists:\n\n{dst}\n\nHow would you like to proceed?"
        )

        for obj_name, tag in self._MAP.items():
            getattr(self.ui, obj_name).clicked.connect(
                lambda _=None, t=tag: self._pick(t)
            )

    def _pick(self, tag: str):
        self._choice = tag
        self.accept()

    @classmethod
    def ask(cls, src: str, dst: str, parent=None) -> str:
        dlg = cls(src, dst, parent)
        dlg.exec()
        return dlg._choice
