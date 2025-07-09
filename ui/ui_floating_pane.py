# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'floating_pane.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QListWidget, QListWidgetItem,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget)
from resources import resources_rc

class Ui_FloatingPane(object):
    def setupUi(self, FloatingPane):
        if not FloatingPane.objectName():
            FloatingPane.setObjectName(u"FloatingPane")
        FloatingPane.resize(400, 300)
        self.verticalLayout = QVBoxLayout(FloatingPane)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btnToggle = QToolButton(FloatingPane)
        self.btnToggle.setObjectName(u"btnToggle")
        self.btnToggle.setMinimumSize(QSize(20, 20))
        self.btnToggle.setMaximumSize(QSize(20, 20))
        self.btnToggle.setBaseSize(QSize(20, 20))
        icon = QIcon()
        icon.addFile(u":/icons/cil-chevron-left.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnToggle.setIcon(icon)

        self.verticalLayout.addWidget(self.btnToggle)

        self.body = QListWidget(FloatingPane)
        self.body.setObjectName(u"body")

        self.verticalLayout.addWidget(self.body)


        self.retranslateUi(FloatingPane)

        QMetaObject.connectSlotsByName(FloatingPane)
    # setupUi

    def retranslateUi(self, FloatingPane):
        FloatingPane.setWindowTitle(QCoreApplication.translate("FloatingPane", u"Frame", None))
        self.btnToggle.setText("")
    # retranslateUi

