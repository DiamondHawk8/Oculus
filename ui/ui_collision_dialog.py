# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'collision_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_CollisionDialog(object):
    def setupUi(self, CollisionDialog):
        if not CollisionDialog.objectName():
            CollisionDialog.setObjectName(u"CollisionDialog")
        CollisionDialog.resize(338, 227)
        self.verticalLayout_2 = QVBoxLayout(CollisionDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_info = QLabel(CollisionDialog)
        self.label_info.setObjectName(u"label_info")
        self.label_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_info)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btn_overwrite = QPushButton(CollisionDialog)
        self.btn_overwrite.setObjectName(u"btn_overwrite")

        self.horizontalLayout_2.addWidget(self.btn_overwrite)

        self.btn_auto = QPushButton(CollisionDialog)
        self.btn_auto.setObjectName(u"btn_auto")

        self.horizontalLayout_2.addWidget(self.btn_auto)

        self.btn_skip = QPushButton(CollisionDialog)
        self.btn_skip.setObjectName(u"btn_skip")

        self.horizontalLayout_2.addWidget(self.btn_skip)

        self.btn_cancel = QPushButton(CollisionDialog)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.horizontalLayout_2.addWidget(self.btn_cancel)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.retranslateUi(CollisionDialog)

        QMetaObject.connectSlotsByName(CollisionDialog)
    # setupUi

    def retranslateUi(self, CollisionDialog):
        CollisionDialog.setWindowTitle(QCoreApplication.translate("CollisionDialog", u"Dialog", None))
        self.label_info.setText(QCoreApplication.translate("CollisionDialog", u"If you are seeing this text something has gone wrong", None))
        self.btn_overwrite.setText(QCoreApplication.translate("CollisionDialog", u"Overwrite", None))
        self.btn_auto.setText(QCoreApplication.translate("CollisionDialog", u"Rename", None))
        self.btn_skip.setText(QCoreApplication.translate("CollisionDialog", u"Skip", None))
        self.btn_cancel.setText(QCoreApplication.translate("CollisionDialog", u"Cancel", None))
    # retranslateUi

