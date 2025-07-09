# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'metadata_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QCheckBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QRadioButton, QSizePolicy, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
import resources.resources_rc

class Ui_MetadataDialog(object):
    def setupUi(self, MetadataDialog):
        if not MetadataDialog.objectName():
            MetadataDialog.setObjectName(u"MetadataDialog")
        MetadataDialog.resize(927, 627)
        MetadataDialog.setStyleSheet(u"QWidget{\n"
"	color: rgb(221, 221, 221);\n"
"	font: 10pt \"Segoe UI\";\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"Tooltip */\n"
"QToolTip {\n"
"	color: #ffffff;\n"
"	background-color: rgba(33, 37, 43, 180);\n"
"	border: 1px solid rgb(44, 49, 58);\n"
"	background-image: none;\n"
"	background-position: left center;\n"
"    background-repeat: no-repeat;\n"
"	border: none;\n"
"	border-left: 2px solid rgb(255, 121, 198);\n"
"	text-align: left;\n"
"	padding-left: 8px;\n"
"	margin: 0px;\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"Bg App */\n"
"#bgApp {\n"
"	background-color: rgb(40, 44, 52);\n"
"	border: 1px solid rgb(44, 49, 58);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"Left Menu */\n"
"#leftMenuBg {\n"
"	background-color: rgb(33, 37, 43);\n"
"}\n"
"#topLogo {\n"
"	background-color: rgb(3"
                        "3, 37, 43);\n"
"	background-image: url(:/images/images/images/PyDracula.png);\n"
"	background-position: centered;\n"
"	background-repeat: no-repeat;\n"
"}\n"
"#titleLeftApp { font: 63 12pt \"Segoe UI Semibold\"; }\n"
"#titleLeftDescription { font: 8pt \"Segoe UI\"; color: rgb(189, 147, 249); }\n"
"\n"
"/* MENUS */\n"
"#topMenu .QPushButton {\n"
"	background-position: left center;\n"
"    background-repeat: no-repeat;\n"
"	border: none;\n"
"	border-left: 22px solid transparent;\n"
"	background-color: transparent;\n"
"	text-align: left;\n"
"	padding-left: 44px;\n"
"}\n"
"#topMenu .QPushButton:hover {\n"
"	background-color: rgb(40, 44, 52);\n"
"}\n"
"#topMenu .QPushButton:pressed {\n"
"	background-color: rgb(189, 147, 249);\n"
"	color: rgb(255, 255, 255);\n"
"}\n"
"#bottomMenu .QPushButton {\n"
"	background-position: left center;\n"
"    background-repeat: no-repeat;\n"
"	border: none;\n"
"	border-left: 20px solid transparent;\n"
"	background-color:transparent;\n"
"	text-align: left;\n"
"	padding-left: 44px;\n"
""
                        "}\n"
"#bottomMenu .QPushButton:hover {\n"
"	background-color: rgb(40, 44, 52);\n"
"}\n"
"#bottomMenu .QPushButton:pressed {\n"
"	background-color: rgb(189, 147, 249);\n"
"	color: rgb(255, 255, 255);\n"
"}\n"
"#leftMenuFrame{\n"
"	border-top: 3px solid rgb(44, 49, 58);\n"
"}\n"
"\n"
"/* Toggle Button */\n"
"#toggleButton {\n"
"	background-position: left center;\n"
"    background-repeat: no-repeat;\n"
"	border: none;\n"
"	border-left: 20px solid transparent;\n"
"	background-color: rgb(37, 41, 48);\n"
"	text-align: left;\n"
"	padding-left: 44px;\n"
"	color: rgb(113, 126, 149);\n"
"}\n"
"#toggleButton:hover {\n"
"	background-color: rgb(40, 44, 52);\n"
"}\n"
"#toggleButton:pressed {\n"
"	background-color: rgb(189, 147, 249);\n"
"}\n"
"\n"
"/* Title Menu */\n"
"#titleRightInfo { padding-left: 10px; }\n"
"\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"Extra Tab */\n"
"#extraLeftBox {\n"
"	background-color: rgb(44, 49, 58);\n"
"}\n"
"#extraTopBg{\n"
""
                        "	background-color: rgb(189, 147, 249)\n"
"}\n"
"\n"
"/* Icon */\n"
"#extraIcon {\n"
"	background-position: center;\n"
"	background-repeat: no-repeat;\n"
"	background-image: url(:/icons/icon_settings.png);\n"
"}\n"
"\n"
"/* Label */\n"
"#extraLabel { color: rgb(255, 255, 255); }\n"
"\n"
"/* Btn Close */\n"
"#extraCloseColumnBtn { background-color: rgba(255, 255, 255, 0); border: none;  border-radius: 5px; }\n"
"#extraCloseColumnBtn:hover { background-color: rgb(196, 161, 249); border-style: solid; border-radius: 4px; }\n"
"#extraCloseColumnBtn:pressed { background-color: rgb(180, 141, 238); border-style: solid; border-radius: 4px; }\n"
"\n"
"/* Extra Content */\n"
"#extraContent{\n"
"	border-top: 3px solid rgb(40, 44, 52);\n"
"}\n"
"\n"
"/* Extra Top Menus */\n"
"#extraTopMenu .QPushButton {\n"
"background-position: left center;\n"
"    background-repeat: no-repeat;\n"
"	border: none;\n"
"	border-left: 22px solid transparent;\n"
"	background-color:transparent;\n"
"	text-align: left;\n"
"	padding-left: 44px;\n"
""
                        "}\n"
"#extraTopMenu .QPushButton:hover {\n"
"	background-color: rgb(40, 44, 52);\n"
"}\n"
"#extraTopMenu .QPushButton:pressed {\n"
"	background-color: rgb(189, 147, 249);\n"
"	color: rgb(255, 255, 255);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"Content App */\n"
"#contentTopBg{\n"
"	background-color: rgb(33, 37, 43);\n"
"}\n"
"#contentBottom{\n"
"	border-top: 3px solid rgb(44, 49, 58);\n"
"}\n"
"\n"
"/* Top Buttons */\n"
"#rightButtons .QPushButton { background-color: rgba(255, 255, 255, 0); border: none;  border-radius: 5px; }\n"
"#rightButtons .QPushButton:hover { background-color: rgb(44, 49, 57); border-style: solid; border-radius: 4px; }\n"
"#rightButtons .QPushButton:pressed { background-color: rgb(23, 26, 30); border-style: solid; border-radius: 4px; }\n"
"\n"
"/* Theme Settings */\n"
"#extraRightBox { background-color: rgb(44, 49, 58); }\n"
"#themeSettingsTopDetail { background-color: rgb(189, 147, 249); }\n"
"\n"
"/* Bottom "
                        "Bar */\n"
"#bottomBar { background-color: rgb(44, 49, 58); }\n"
"#bottomBar QLabel { font-size: 11px; color: rgb(113, 126, 149); padding-left: 10px; padding-right: 10px; padding-bottom: 2px; }\n"
"\n"
"/* CONTENT SETTINGS */\n"
"/* MENUS */\n"
"#contentSettings .QPushButton {\n"
"	background-position: left center;\n"
"    background-repeat: no-repeat;\n"
"	border: none;\n"
"	border-left: 22px solid transparent;\n"
"	background-color:transparent;\n"
"	text-align: left;\n"
"	padding-left: 44px;\n"
"}\n"
"#contentSettings .QPushButton:hover {\n"
"	background-color: rgb(40, 44, 52);\n"
"}\n"
"#contentSettings .QPushButton:pressed {\n"
"	background-color: rgb(189, 147, 249);\n"
"	color: rgb(255, 255, 255);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"QTableWidget */\n"
"QTableWidget {\n"
"	background-color: transparent;\n"
"	padding: 10px;\n"
"	border-radius: 5px;\n"
"	gridline-color: rgb(44, 49, 58);\n"
"	border-bottom: 1px solid rgb(44, 49"
                        ", 60);\n"
"}\n"
"QTableWidget::item{\n"
"	border-color: rgb(44, 49, 60);\n"
"	padding-left: 5px;\n"
"	padding-right: 5px;\n"
"	gridline-color: rgb(44, 49, 60);\n"
"}\n"
"QTableWidget::item:selected{\n"
"	background-color: rgb(189, 147, 249);\n"
"}\n"
"QHeaderView::section{\n"
"	background-color: rgb(33, 37, 43);\n"
"	max-width: 30px;\n"
"	border: 1px solid rgb(44, 49, 58);\n"
"	border-style: none;\n"
"    border-bottom: 1px solid rgb(44, 49, 60);\n"
"    border-right: 1px solid rgb(44, 49, 60);\n"
"}\n"
"QTableWidget::horizontalHeader {\n"
"	background-color: rgb(33, 37, 43);\n"
"}\n"
"QHeaderView::section:horizontal\n"
"{\n"
"    border: 1px solid rgb(33, 37, 43);\n"
"	background-color: rgb(33, 37, 43);\n"
"	padding: 3px;\n"
"	border-top-left-radius: 7px;\n"
"    border-top-right-radius: 7px;\n"
"}\n"
"QHeaderView::section:vertical\n"
"{\n"
"    border: 1px solid rgb(44, 49, 60);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"LineEdit */"
                        "\n"
"QLineEdit {\n"
"	background-color: rgb(33, 37, 43);\n"
"	border-radius: 5px;\n"
"	border: 2px solid rgb(33, 37, 43);\n"
"	padding-left: 10px;\n"
"	selection-color: rgb(255, 255, 255);\n"
"	selection-background-color: rgb(255, 121, 198);\n"
"}\n"
"QLineEdit:hover {\n"
"	border: 2px solid rgb(64, 71, 88);\n"
"}\n"
"QLineEdit:focus {\n"
"	border: 2px solid rgb(91, 101, 124);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"PlainTextEdit */\n"
"QPlainTextEdit {\n"
"	background-color: rgb(27, 29, 35);\n"
"	border-radius: 5px;\n"
"	padding: 10px;\n"
"	selection-color: rgb(255, 255, 255);\n"
"	selection-background-color: rgb(255, 121, 198);\n"
"}\n"
"QPlainTextEdit  QScrollBar:vertical {\n"
"    width: 8px;\n"
" }\n"
"QPlainTextEdit  QScrollBar:horizontal {\n"
"    height: 8px;\n"
" }\n"
"QPlainTextEdit:hover {\n"
"	border: 2px solid rgb(64, 71, 88);\n"
"}\n"
"QPlainTextEdit:focus {\n"
"	border: 2px solid rgb(91, 101, 124);\n"
"}\n"
"\n"
"/* "
                        "/////////////////////////////////////////////////////////////////////////////////////////////////\n"
"ScrollBars */\n"
"QScrollBar:horizontal {\n"
"    border: none;\n"
"    background: rgb(52, 59, 72);\n"
"    height: 8px;\n"
"    margin: 0px 21px 0 21px;\n"
"	border-radius: 0px;\n"
"}\n"
"QScrollBar::handle:horizontal {\n"
"    background: rgb(189, 147, 249);\n"
"    min-width: 25px;\n"
"	border-radius: 4px\n"
"}\n"
"QScrollBar::add-line:horizontal {\n"
"    border: none;\n"
"    background: rgb(55, 63, 77);\n"
"    width: 20px;\n"
"	border-top-right-radius: 4px;\n"
"    border-bottom-right-radius: 4px;\n"
"    subcontrol-position: right;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:horizontal {\n"
"    border: none;\n"
"    background: rgb(55, 63, 77);\n"
"    width: 20px;\n"
"	border-top-left-radius: 4px;\n"
"    border-bottom-left-radius: 4px;\n"
"    subcontrol-position: left;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizon"
                        "tal\n"
"{\n"
"     background: none;\n"
"}\n"
"QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal\n"
"{\n"
"     background: none;\n"
"}\n"
" QScrollBar:vertical {\n"
"	border: none;\n"
"    background: rgb(52, 59, 72);\n"
"    width: 8px;\n"
"    margin: 21px 0 21px 0;\n"
"	border-radius: 0px;\n"
" }\n"
" QScrollBar::handle:vertical {\n"
"	background: rgb(189, 147, 249);\n"
"    min-height: 25px;\n"
"	border-radius: 4px\n"
" }\n"
" QScrollBar::add-line:vertical {\n"
"     border: none;\n"
"    background: rgb(55, 63, 77);\n"
"     height: 20px;\n"
"	border-bottom-left-radius: 4px;\n"
"    border-bottom-right-radius: 4px;\n"
"     subcontrol-position: bottom;\n"
"     subcontrol-origin: margin;\n"
" }\n"
" QScrollBar::sub-line:vertical {\n"
"	border: none;\n"
"    background: rgb(55, 63, 77);\n"
"     height: 20px;\n"
"	border-top-left-radius: 4px;\n"
"    border-top-right-radius: 4px;\n"
"     subcontrol-position: top;\n"
"     subcontrol-origin: margin;\n"
" }\n"
" QScrollBar::up-arrow:vertical"
                        ", QScrollBar::down-arrow:vertical {\n"
"     background: none;\n"
" }\n"
"\n"
" QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n"
"     background: none;\n"
" }\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"CheckBox */\n"
"QCheckBox::indicator {\n"
"    border: 3px solid rgb(52, 59, 72);\n"
"	width: 15px;\n"
"	height: 15px;\n"
"	border-radius: 10px;\n"
"    background: rgb(44, 49, 60);\n"
"}\n"
"QCheckBox::indicator:hover {\n"
"    border: 3px solid rgb(58, 66, 81);\n"
"}\n"
"QCheckBox::indicator:checked {\n"
"    background: 3px solid rgb(52, 59, 72);\n"
"	border: 3px solid rgb(52, 59, 72);\n"
"	background-image: url(:/icons/cil-check-alt.png);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"RadioButton */\n"
"QRadioButton::indicator {\n"
"    border: 3px solid rgb(52, 59, 72);\n"
"	width: 15px;\n"
"	height: 15px;\n"
"	border-radius: 10px;\n"
"    backgrou"
                        "nd: rgb(44, 49, 60);\n"
"}\n"
"QRadioButton::indicator:hover {\n"
"    border: 3px solid rgb(58, 66, 81);\n"
"}\n"
"QRadioButton::indicator:checked {\n"
"    background: 3px solid rgb(94, 106, 130);\n"
"	border: 3px solid rgb(52, 59, 72);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"ComboBox */\n"
"QComboBox{\n"
"	background-color: rgb(27, 29, 35);\n"
"	border-radius: 5px;\n"
"	border: 2px solid rgb(33, 37, 43);\n"
"	padding: 5px;\n"
"	padding-left: 10px;\n"
"}\n"
"QComboBox:hover{\n"
"	border: 2px solid rgb(64, 71, 88);\n"
"}\n"
"QComboBox::drop-down {\n"
"	subcontrol-origin: padding;\n"
"	subcontrol-position: top right;\n"
"	width: 25px;\n"
"	border-left-width: 3px;\n"
"	border-left-color: rgba(39, 44, 54, 150);\n"
"	border-left-style: solid;\n"
"	border-top-right-radius: 3px;\n"
"	border-bottom-right-radius: 3px;\n"
"	background-image: url(:/icons/cil-arrow-bottom.png);\n"
"	background-position: center;\n"
"	background-repeat: no-rep"
                        "erat;\n"
" }\n"
"QComboBox QAbstractItemView {\n"
"	color: rgb(255, 121, 198);\n"
"	background-color: rgb(33, 37, 43);\n"
"	padding: 10px;\n"
"	selection-background-color: rgb(39, 44, 54);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"Sliders */\n"
"QSlider::groove:horizontal {\n"
"    border-radius: 5px;\n"
"    height: 10px;\n"
"	margin: 0px;\n"
"	background-color: rgb(52, 59, 72);\n"
"}\n"
"QSlider::groove:horizontal:hover {\n"
"	background-color: rgb(55, 62, 76);\n"
"}\n"
"QSlider::handle:horizontal {\n"
"    background-color: rgb(189, 147, 249);\n"
"    border: none;\n"
"    height: 10px;\n"
"    width: 10px;\n"
"    margin: 0px;\n"
"	border-radius: 5px;\n"
"}\n"
"QSlider::handle:horizontal:hover {\n"
"    background-color: rgb(195, 155, 255);\n"
"}\n"
"QSlider::handle:horizontal:pressed {\n"
"    background-color: rgb(255, 121, 198);\n"
"}\n"
"\n"
"QSlider::groove:vertical {\n"
"    border-radius: 5px;\n"
"    width: 10px;\n"
"    "
                        "margin: 0px;\n"
"	background-color: rgb(52, 59, 72);\n"
"}\n"
"QSlider::groove:vertical:hover {\n"
"	background-color: rgb(55, 62, 76);\n"
"}\n"
"QSlider::handle:vertical {\n"
"    background-color: rgb(189, 147, 249);\n"
"	border: none;\n"
"    height: 10px;\n"
"    width: 10px;\n"
"    margin: 0px;\n"
"	border-radius: 5px;\n"
"}\n"
"QSlider::handle:vertical:hover {\n"
"    background-color: rgb(195, 155, 255);\n"
"}\n"
"QSlider::handle:vertical:pressed {\n"
"    background-color: rgb(255, 121, 198);\n"
"}\n"
"\n"
"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
"CommandLinkButton */\n"
"QCommandLinkButton {\n"
"	color: rgb(255, 121, 198);\n"
"	border-radius: 5px;\n"
"	padding: 5px;\n"
"}\n"
"QCommandLinkButton:hover {\n"
"	color: rgb(255, 170, 255);\n"
"	background-color: rgb(44, 49, 60);\n"
"}\n"
"QCommandLinkButton:pressed {\n"
"	color: rgb(189, 147, 249);\n"
"	background-color: rgb(52, 58, 71);\n"
"}\n"
"\n"
"/* //////////////////////////////////////"
                        "///////////////////////////////////////////////////////////\n"
"Button */\n"
"#pagesContainer QPushButton {\n"
"	border: 2px solid rgb(52, 59, 72);\n"
"	border-radius: 5px;\n"
"	background-color: rgb(52, 59, 72);\n"
"}\n"
"#pagesContainer QPushButton:hover {\n"
"	background-color: rgb(57, 65, 80);\n"
"	border: 2px solid rgb(61, 70, 86);\n"
"}\n"
"#pagesContainer QPushButton:pressed {\n"
"	background-color: rgb(35, 40, 49);\n"
"	border: 2px solid rgb(43, 50, 61);\n"
"}\n"
"#title_bar {\n"
"    background-color: #21252e;\n"
"}\n"
"\n"
"\n"
"QToolButton:checked {\n"
"    background-color: rgb(52, 59, 72)\n"
"    border: none;\n"
"}")
        self.verticalLayout = QVBoxLayout(MetadataDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabs = QTabWidget(MetadataDialog)
        self.tabs.setObjectName(u"tabs")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabs.sizePolicy().hasHeightForWidth())
        self.tabs.setSizePolicy(sizePolicy)
        self.tabs.setMinimumSize(QSize(0, 200))
        self.TagsTab = QWidget()
        self.TagsTab.setObjectName(u"TagsTab")
        self.verticalLayout_3 = QVBoxLayout(self.TagsTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(-1, -1, 0, -1)
        self.label = QLabel(self.TagsTab)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_7.addWidget(self.label)

        self.listTags = QListWidget(self.TagsTab)
        self.listTags.setObjectName(u"listTags")

        self.verticalLayout_7.addWidget(self.listTags)


        self.horizontalLayout_3.addLayout(self.verticalLayout_7)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(-1, -1, 0, -1)
        self.label_2 = QLabel(self.TagsTab)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_9.addWidget(self.label_2)

        self.listFiles = QListWidget(self.TagsTab)
        self.listFiles.setObjectName(u"listFiles")

        self.verticalLayout_9.addWidget(self.listFiles)


        self.horizontalLayout_3.addLayout(self.verticalLayout_9)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.label_3 = QLabel(self.TagsTab)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_3)

        self.listPending = QListWidget(self.TagsTab)
        self.listPending.setObjectName(u"listPending")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.listPending.sizePolicy().hasHeightForWidth())
        self.listPending.setSizePolicy(sizePolicy2)

        self.verticalLayout_3.addWidget(self.listPending)

        self.hboxTagEdit = QHBoxLayout()
        self.hboxTagEdit.setObjectName(u"hboxTagEdit")
        self.chkReplace = QCheckBox(self.TagsTab)
        self.chkReplace.setObjectName(u"chkReplace")

        self.hboxTagEdit.addWidget(self.chkReplace)

        self.editTag = QLineEdit(self.TagsTab)
        self.editTag.setObjectName(u"editTag")

        self.hboxTagEdit.addWidget(self.editTag)

        self.btnCopyTags = QPushButton(self.TagsTab)
        self.btnCopyTags.setObjectName(u"btnCopyTags")

        self.hboxTagEdit.addWidget(self.btnCopyTags)

        self.btnPasteTags = QPushButton(self.TagsTab)
        self.btnPasteTags.setObjectName(u"btnPasteTags")

        self.hboxTagEdit.addWidget(self.btnPasteTags)

        self.btnRemoveTag = QPushButton(self.TagsTab)
        self.btnRemoveTag.setObjectName(u"btnRemoveTag")

        self.hboxTagEdit.addWidget(self.btnRemoveTag)

        self.btnAddTag = QPushButton(self.TagsTab)
        self.btnAddTag.setObjectName(u"btnAddTag")

        self.hboxTagEdit.addWidget(self.btnAddTag)


        self.verticalLayout_3.addLayout(self.hboxTagEdit)

        self.tabs.addTab(self.TagsTab, "")
        self.AttributesTab = QWidget()
        self.AttributesTab.setObjectName(u"AttributesTab")
        self.verticalLayout_4 = QVBoxLayout(self.AttributesTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.editArtist = QLineEdit(self.AttributesTab)
        self.editArtist.setObjectName(u"editArtist")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.editArtist)

        self.spinWeight = QDoubleSpinBox(self.AttributesTab)
        self.spinWeight.setObjectName(u"spinWeight")
        self.spinWeight.setKeyboardTracking(False)
        self.spinWeight.setMaximum(1.000000000000000)
        self.spinWeight.setSingleStep(0.010000000000000)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.spinWeight)

        self.chkFavorite = QCheckBox(self.AttributesTab)
        self.chkFavorite.setObjectName(u"chkFavorite")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.chkFavorite)


        self.verticalLayout_4.addLayout(self.formLayout)

        self.tabs.addTab(self.AttributesTab, "")
        self.PresetsTab = QWidget()
        self.PresetsTab.setObjectName(u"PresetsTab")
        self.verticalLayout_2 = QVBoxLayout(self.PresetsTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tblPresets = QTableWidget(self.PresetsTab)
        if (self.tblPresets.columnCount() < 5):
            self.tblPresets.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        self.tblPresets.setObjectName(u"tblPresets")
        self.tblPresets.setStyleSheet(u"            QTableWidget QLineEdit {\n"
"                background: palette(base);   /* opaque, matches normal textbox */\n"
"                border: none;                /* no double border */\n"
"                padding: 0px;\n"
"            }")
        self.tblPresets.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.tblPresets.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblPresets.setColumnCount(5)
        self.tblPresets.horizontalHeader().setStretchLastSection(True)
        self.tblPresets.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_2.addWidget(self.tblPresets)

        self.hboxPresetBtns = QHBoxLayout()
        self.hboxPresetBtns.setObjectName(u"hboxPresetBtns")
        self.editPresetName = QLineEdit(self.PresetsTab)
        self.editPresetName.setObjectName(u"editPresetName")
        self.editPresetName.setText(u"")
        self.editPresetName.setReadOnly(False)
        self.editPresetName.setClearButtonEnabled(True)

        self.hboxPresetBtns.addWidget(self.editPresetName)

        self.vLayoutPresetOps = QVBoxLayout()
        self.vLayoutPresetOps.setObjectName(u"vLayoutPresetOps")
        self.vLayoutPresetOps.setContentsMargins(-1, -1, 0, -1)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(-1, 0, -1, -1)
        self.spinZoom = QDoubleSpinBox(self.PresetsTab)
        self.spinZoom.setObjectName(u"spinZoom")
        self.spinZoom.setMinimum(0.010000000000000)
        self.spinZoom.setMaximum(100.000000000000000)

        self.horizontalLayout_5.addWidget(self.spinZoom)

        self.spinPanX = QSpinBox(self.PresetsTab)
        self.spinPanX.setObjectName(u"spinPanX")
        self.spinPanX.setMinimum(-99999)
        self.spinPanX.setMaximum(99999)

        self.horizontalLayout_5.addWidget(self.spinPanX)

        self.spinPanY = QSpinBox(self.PresetsTab)
        self.spinPanY.setObjectName(u"spinPanY")
        self.spinPanY.setMinimum(-99999)
        self.spinPanY.setMaximum(99999)

        self.horizontalLayout_5.addWidget(self.spinPanY)


        self.vLayoutPresetOps.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, 0, -1, -1)
        self.btnLoadPreset = QPushButton(self.PresetsTab)
        self.btnLoadPreset.setObjectName(u"btnLoadPreset")

        self.horizontalLayout_4.addWidget(self.btnLoadPreset)

        self.btnDeletePreset = QPushButton(self.PresetsTab)
        self.btnDeletePreset.setObjectName(u"btnDeletePreset")

        self.horizontalLayout_4.addWidget(self.btnDeletePreset)

        self.btnSavePreset = QPushButton(self.PresetsTab)
        self.btnSavePreset.setObjectName(u"btnSavePreset")

        self.horizontalLayout_4.addWidget(self.btnSavePreset)


        self.vLayoutPresetOps.addLayout(self.horizontalLayout_4)


        self.hboxPresetBtns.addLayout(self.vLayoutPresetOps)


        self.verticalLayout_2.addLayout(self.hboxPresetBtns)

        self.tabs.addTab(self.PresetsTab, "")

        self.verticalLayout.addWidget(self.tabs)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.grpScope = QGroupBox(MetadataDialog)
        self.grpScope.setObjectName(u"grpScope")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.grpScope.sizePolicy().hasHeightForWidth())
        self.grpScope.setSizePolicy(sizePolicy3)
        self.horizontalLayout = QHBoxLayout(self.grpScope)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.radSelected = QRadioButton(self.grpScope)
        self.radSelected.setObjectName(u"radSelected")
        sizePolicy2.setHeightForWidth(self.radSelected.sizePolicy().hasHeightForWidth())
        self.radSelected.setSizePolicy(sizePolicy2)
        self.radSelected.setChecked(True)

        self.horizontalLayout.addWidget(self.radSelected)

        self.radFolder = QRadioButton(self.grpScope)
        self.radFolder.setObjectName(u"radFolder")
        self.radFolder.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.radFolder.sizePolicy().hasHeightForWidth())
        self.radFolder.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.radFolder)

        self.radThis = QRadioButton(self.grpScope)
        self.radThis.setObjectName(u"radThis")
        self.radThis.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.radThis.sizePolicy().hasHeightForWidth())
        self.radThis.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.radThis)


        self.horizontalLayout_2.addWidget(self.grpScope)

        self.chkVariants = QCheckBox(MetadataDialog)
        self.chkVariants.setObjectName(u"chkVariants")
        self.chkVariants.setChecked(True)

        self.horizontalLayout_2.addWidget(self.chkVariants)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.buttonBox = QDialogButtonBox(MetadataDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(MetadataDialog)
        self.buttonBox.accepted.connect(MetadataDialog.accept)
        self.buttonBox.rejected.connect(MetadataDialog.reject)

        self.tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MetadataDialog)
    # setupUi

    def retranslateUi(self, MetadataDialog):
        MetadataDialog.setWindowTitle(QCoreApplication.translate("MetadataDialog", u"Edit Metadata", None))
        self.label.setText(QCoreApplication.translate("MetadataDialog", u"Current Tags", None))
        self.label_2.setText(QCoreApplication.translate("MetadataDialog", u"Files", None))
        self.label_3.setText(QCoreApplication.translate("MetadataDialog", u"Pending Tags", None))
        self.chkReplace.setText(QCoreApplication.translate("MetadataDialog", u"Remove Tags", None))
        self.btnCopyTags.setText(QCoreApplication.translate("MetadataDialog", u"Copy", None))
        self.btnPasteTags.setText(QCoreApplication.translate("MetadataDialog", u"Paste", None))
        self.btnRemoveTag.setText(QCoreApplication.translate("MetadataDialog", u"Remove", None))
        self.btnAddTag.setText(QCoreApplication.translate("MetadataDialog", u"Add", None))
        self.tabs.setTabText(self.tabs.indexOf(self.TagsTab), QCoreApplication.translate("MetadataDialog", u"Tags", None))
        self.chkFavorite.setText(QCoreApplication.translate("MetadataDialog", u"Favorite \u2605", None))
        self.tabs.setTabText(self.tabs.indexOf(self.AttributesTab), QCoreApplication.translate("MetadataDialog", u"Attributes", None))
        ___qtablewidgetitem = self.tblPresets.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MetadataDialog", u"Name", None));
        ___qtablewidgetitem1 = self.tblPresets.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MetadataDialog", u"Scope", None));
        ___qtablewidgetitem2 = self.tblPresets.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MetadataDialog", u"Properties", None));
        ___qtablewidgetitem3 = self.tblPresets.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MetadataDialog", u"Default", None));
        ___qtablewidgetitem4 = self.tblPresets.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MetadataDialog", u"Keybind", None));
        self.editPresetName.setPlaceholderText(QCoreApplication.translate("MetadataDialog", u"New preset name...", None))
        self.spinZoom.setPrefix(QCoreApplication.translate("MetadataDialog", u"Zoom: ", None))
        self.spinPanX.setPrefix(QCoreApplication.translate("MetadataDialog", u"X: ", None))
        self.spinPanY.setPrefix(QCoreApplication.translate("MetadataDialog", u"Y: ", None))
        self.btnLoadPreset.setText(QCoreApplication.translate("MetadataDialog", u"Load", None))
        self.btnDeletePreset.setText(QCoreApplication.translate("MetadataDialog", u"Delete", None))
        self.btnSavePreset.setText(QCoreApplication.translate("MetadataDialog", u"Save", None))
        self.tabs.setTabText(self.tabs.indexOf(self.PresetsTab), QCoreApplication.translate("MetadataDialog", u"Presets", None))
        self.grpScope.setTitle(QCoreApplication.translate("MetadataDialog", u"Apply to", None))
        self.radSelected.setText(QCoreApplication.translate("MetadataDialog", u"Current Selection", None))
        self.radFolder.setText(QCoreApplication.translate("MetadataDialog", u"All Files in This Folder", None))
        self.radThis.setText(QCoreApplication.translate("MetadataDialog", u"This File Only", None))
        self.chkVariants.setText(QCoreApplication.translate("MetadataDialog", u"Apply to Variants", None))
    # retranslateUi

