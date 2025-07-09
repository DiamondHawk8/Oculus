# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'comment_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_CommentPanel(object):
    def setupUi(self, CommentPanel):
        if not CommentPanel.objectName():
            CommentPanel.setObjectName(u"CommentPanel")
        CommentPanel.resize(468, 617)
        self.verticalLayout = QVBoxLayout(CommentPanel)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.listComments = QListWidget(CommentPanel)
        self.listComments.setObjectName(u"listComments")

        self.verticalLayout.addWidget(self.listComments)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 10, -1, -1)
        self.EditComment = QTextEdit(CommentPanel)
        self.EditComment.setObjectName(u"EditComment")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.EditComment.sizePolicy().hasHeightForWidth())
        self.EditComment.setSizePolicy(sizePolicy)

        self.verticalLayout_2.addWidget(self.EditComment)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btnAdd = QPushButton(CommentPanel)
        self.btnAdd.setObjectName(u"btnAdd")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btnAdd.sizePolicy().hasHeightForWidth())
        self.btnAdd.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.btnAdd)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout.addLayout(self.verticalLayout_2)


        self.retranslateUi(CommentPanel)

        QMetaObject.connectSlotsByName(CommentPanel)
    # setupUi

    def retranslateUi(self, CommentPanel):
        CommentPanel.setWindowTitle(QCoreApplication.translate("CommentPanel", u"Form", None))
        self.btnAdd.setText(QCoreApplication.translate("CommentPanel", u"PushButton", None))
    # retranslateUi

