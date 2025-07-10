# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'comment_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy,
    QSpacerItem, QToolButton, QVBoxLayout, QWidget)
from resources import resources_rc

class Ui_CommentWidget(object):
    def setupUi(self, CommentWidget):
        if not CommentWidget.objectName():
            CommentWidget.setObjectName(u"CommentWidget")
        CommentWidget.resize(577, 354)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(CommentWidget.sizePolicy().hasHeightForWidth())
        CommentWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(CommentWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.topLayout = QHBoxLayout()
        self.topLayout.setObjectName(u"topLayout")
        self.topLayout.setContentsMargins(0, 0, 0, -1)
        self.labelAuthor = QLabel(CommentWidget)
        self.labelAuthor.setObjectName(u"labelAuthor")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.labelAuthor.sizePolicy().hasHeightForWidth())
        self.labelAuthor.setSizePolicy(sizePolicy1)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.labelAuthor.setFont(font)
        self.labelAuthor.setStyleSheet(u"color:#f6f6f6;")

        self.topLayout.addWidget(self.labelAuthor)

        self.labelTime = QLabel(CommentWidget)
        self.labelTime.setObjectName(u"labelTime")
        font1 = QFont()
        font1.setPointSize(8)
        font1.setItalic(True)
        self.labelTime.setFont(font1)

        self.topLayout.addWidget(self.labelTime)

        self.btnEdit = QToolButton(CommentWidget)
        self.btnEdit.setObjectName(u"btnEdit")
        icon = QIcon()
        icon.addFile(u":/icons/cil-pencil.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnEdit.setIcon(icon)
        self.btnEdit.setAutoRaise(True)

        self.topLayout.addWidget(self.btnEdit)

        self.btnDelete = QToolButton(CommentWidget)
        self.btnDelete.setObjectName(u"btnDelete")
        icon1 = QIcon()
        icon1.addFile(u":/icons/icon_close.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnDelete.setIcon(icon1)

        self.topLayout.addWidget(self.btnDelete)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.topLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.topLayout)

        self.labelText = QLabel(CommentWidget)
        self.labelText.setObjectName(u"labelText")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.labelText.sizePolicy().hasHeightForWidth())
        self.labelText.setSizePolicy(sizePolicy2)
        self.labelText.setStyleSheet(u"border:1px solid #444; border-radius:6px; background:#333; margin:2px;")
        self.labelText.setWordWrap(True)
        self.labelText.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout.addWidget(self.labelText)


        self.retranslateUi(CommentWidget)

        QMetaObject.connectSlotsByName(CommentWidget)
    # setupUi

    def retranslateUi(self, CommentWidget):
        CommentWidget.setWindowTitle(QCoreApplication.translate("CommentWidget", u"Form", None))
        self.labelAuthor.setText(QCoreApplication.translate("CommentWidget", u"TextLabel", None))
        self.labelTime.setText(QCoreApplication.translate("CommentWidget", u"TextLabel", None))
#if QT_CONFIG(tooltip)
        self.btnEdit.setToolTip(QCoreApplication.translate("CommentWidget", u"btnEdit", None))
#endif // QT_CONFIG(tooltip)
        self.btnEdit.setText(QCoreApplication.translate("CommentWidget", u"...", None))
        self.btnDelete.setText("")
        self.labelText.setText(QCoreApplication.translate("CommentWidget", u"TextLabel", None))
    # retranslateUi

