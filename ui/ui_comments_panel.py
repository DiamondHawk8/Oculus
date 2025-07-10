# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'comments_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_CommentsPanel(object):
    def setupUi(self, CommentsPanel):
        if not CommentsPanel.objectName():
            CommentsPanel.setObjectName(u"CommentsPanel")
        CommentsPanel.resize(526, 326)
        self.verticalLayout = QVBoxLayout(CommentsPanel)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.labelHeader = QLabel(CommentsPanel)
        self.labelHeader.setObjectName(u"labelHeader")

        self.verticalLayout.addWidget(self.labelHeader)

        self.scrollArea = QScrollArea(CommentsPanel)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.commentsContainer = QWidget()
        self.commentsContainer.setObjectName(u"commentsContainer")
        self.commentsContainer.setGeometry(QRect(0, 0, 506, 54))
        self.verticalLayout_2 = QVBoxLayout(self.commentsContainer)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.scrollArea.setWidget(self.commentsContainer)

        self.verticalLayout.addWidget(self.scrollArea)

        self.editComment = QTextEdit(CommentsPanel)
        self.editComment.setObjectName(u"editComment")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.editComment.sizePolicy().hasHeightForWidth())
        self.editComment.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.editComment)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btnPost = QPushButton(CommentsPanel)
        self.btnPost.setObjectName(u"btnPost")

        self.horizontalLayout.addWidget(self.btnPost)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(CommentsPanel)

        QMetaObject.connectSlotsByName(CommentsPanel)
    # setupUi

    def retranslateUi(self, CommentsPanel):
        CommentsPanel.setWindowTitle(QCoreApplication.translate("CommentsPanel", u"Form", None))
        self.labelHeader.setText(QCoreApplication.translate("CommentsPanel", u"<b>Comments<b>", None))
        self.editComment.setPlaceholderText(QCoreApplication.translate("CommentsPanel", u"Add a comment...", None))
        self.btnPost.setText(QCoreApplication.translate("CommentsPanel", u"Post", None))
    # retranslateUi

