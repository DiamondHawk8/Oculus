# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gallery_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QListView,
    QPushButton, QSizePolicy, QSpacerItem, QToolButton,
    QVBoxLayout, QWidget)
from resources import resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(974, 626)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(10, 10, 10, 10)
        self.btn_back = QPushButton(Form)
        self.btn_back.setObjectName(u"btn_back")
        icon = QIcon()
        icon.addFile(u":/icons/cil-arrow-left.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_back.setIcon(icon)

        self.horizontalLayout_13.addWidget(self.btn_back)

        self.btn_forward = QPushButton(Form)
        self.btn_forward.setObjectName(u"btn_forward")
        icon1 = QIcon()
        icon1.addFile(u":/icons/cil-arrow-right.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_forward.setIcon(icon1)

        self.horizontalLayout_13.addWidget(self.btn_forward)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer)

        self.btn_gallery_sortDir = QToolButton(Form)
        self.btn_gallery_sortDir.setObjectName(u"btn_gallery_sortDir")
        palette = QPalette()
        brush = QBrush(QColor(221, 221, 221, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        brush1 = QBrush(QColor(0, 0, 0, 0))
        brush1.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, brush1)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, brush1)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, brush1)
        brush2 = QBrush(QColor(221, 221, 221, 128))
        brush2.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, brush2)
#endif
#if QT_VERSION >= QT_VERSION_CHECK(6, 6, 0)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Accent, brush1)
#endif
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, brush1)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, brush1)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, brush2)
#endif
#if QT_VERSION >= QT_VERSION_CHECK(6, 6, 0)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Accent, brush1)
#endif
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, brush1)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, brush)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, brush1)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, brush2)
#endif
#if QT_VERSION >= QT_VERSION_CHECK(6, 6, 0)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Accent, brush1)
#endif
        self.btn_gallery_sortDir.setPalette(palette)
        icon2 = QIcon()
        icon2.addFile(u":/icons/cil-arrow-bottom.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon2.addFile(u":/icons/cil-arrow-top.png", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.btn_gallery_sortDir.setIcon(icon2)
        self.btn_gallery_sortDir.setCheckable(True)
        self.btn_gallery_sortDir.setChecked(False)

        self.horizontalLayout_13.addWidget(self.btn_gallery_sortDir)

        self.cmb_gallery_sortKey = QComboBox(Form)
        self.cmb_gallery_sortKey.addItem("")
        self.cmb_gallery_sortKey.addItem("")
        self.cmb_gallery_sortKey.addItem("")
        self.cmb_gallery_sortKey.setObjectName(u"cmb_gallery_sortKey")

        self.horizontalLayout_13.addWidget(self.cmb_gallery_sortKey)

        self.cmb_gallery_size = QComboBox(Form)
        self.cmb_gallery_size.setObjectName(u"cmb_gallery_size")

        self.horizontalLayout_13.addWidget(self.cmb_gallery_size)

        self.btn_gallery_view = QToolButton(Form)
        self.btn_gallery_view.setObjectName(u"btn_gallery_view")
        palette1 = QPalette()
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, brush1)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, brush)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, brush1)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, brush2)
#endif
        brush3 = QBrush(QColor(40, 44, 52, 0))
        brush3.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(6, 6, 0)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Accent, brush3)
#endif
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, brush1)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, brush)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, brush1)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, brush2)
#endif
#if QT_VERSION >= QT_VERSION_CHECK(6, 6, 0)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Accent, brush3)
#endif
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, brush1)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, brush)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, brush1)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, brush2)
#endif
#if QT_VERSION >= QT_VERSION_CHECK(6, 6, 0)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Accent, brush3)
#endif
        self.btn_gallery_view.setPalette(palette1)
        icon3 = QIcon()
        icon3.addFile(u":/icons/cil-size-grip.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon3.addFile(u":/icons/cil-featured-playlist.png", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.btn_gallery_view.setIcon(icon3)
        self.btn_gallery_view.setCheckable(True)
        self.btn_gallery_view.setChecked(True)

        self.horizontalLayout_13.addWidget(self.btn_gallery_view)


        self.verticalLayout.addLayout(self.horizontalLayout_13)

        self.galleryList = QListView(Form)
        self.galleryList.setObjectName(u"galleryList")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.galleryList.sizePolicy().hasHeightForWidth())
        self.galleryList.setSizePolicy(sizePolicy)
        self.galleryList.setLineWidth(0)

        self.verticalLayout.addWidget(self.galleryList)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.btn_back.setText("")
        self.btn_forward.setText("")
        self.btn_gallery_sortDir.setText(QCoreApplication.translate("Form", u"...", None))
        self.cmb_gallery_sortKey.setItemText(0, QCoreApplication.translate("Form", u"Name", None))
        self.cmb_gallery_sortKey.setItemText(1, QCoreApplication.translate("Form", u"Date", None))
        self.cmb_gallery_sortKey.setItemText(2, QCoreApplication.translate("Form", u"Size", None))

        self.btn_gallery_view.setText(QCoreApplication.translate("Form", u"...", None))
    # retranslateUi

