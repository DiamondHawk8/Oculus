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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGroupBox, QHBoxLayout, QLineEdit, QRadioButton,
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

class Ui_MetadataDialog(object):
    def setupUi(self, MetadataDialog):
        if not MetadataDialog.objectName():
            MetadataDialog.setObjectName(u"MetadataDialog")
        MetadataDialog.resize(638, 347)
        self.verticalLayout = QVBoxLayout(MetadataDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabs = QTabWidget(MetadataDialog)
        self.tabs.setObjectName(u"tabs")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabs.sizePolicy().hasHeightForWidth())
        self.tabs.setSizePolicy(sizePolicy)
        self.tabs.setMinimumSize(QSize(0, 200))
        self.TagsTab = QWidget()
        self.TagsTab.setObjectName(u"TagsTab")
        self.tabs.addTab(self.TagsTab, "")
        self.AttributesTab = QWidget()
        self.AttributesTab.setObjectName(u"AttributesTab")
        self.tabs.addTab(self.AttributesTab, "")
        self.PresetsTab = QWidget()
        self.PresetsTab.setObjectName(u"PresetsTab")
        self.tabs.addTab(self.PresetsTab, "")

        self.verticalLayout.addWidget(self.tabs)

        self.grpScope = QGroupBox(MetadataDialog)
        self.grpScope.setObjectName(u"grpScope")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.grpScope.sizePolicy().hasHeightForWidth())
        self.grpScope.setSizePolicy(sizePolicy1)
        self.horizontalLayout = QHBoxLayout(self.grpScope)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.radThis = QRadioButton(self.grpScope)
        self.radThis.setObjectName(u"radThis")

        self.horizontalLayout.addWidget(self.radThis)

        self.radFolder = QRadioButton(self.grpScope)
        self.radFolder.setObjectName(u"radFolder")

        self.horizontalLayout.addWidget(self.radFolder)

        self.radStack = QRadioButton(self.grpScope)
        self.radStack.setObjectName(u"radStack")

        self.horizontalLayout.addWidget(self.radStack)

        self.radSelected = QRadioButton(self.grpScope)
        self.radSelected.setObjectName(u"radSelected")

        self.horizontalLayout.addWidget(self.radSelected)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.radRange = QRadioButton(self.grpScope)
        self.radRange.setObjectName(u"radRange")

        self.verticalLayout_2.addWidget(self.radRange)

        self.editRange = QLineEdit(self.grpScope)
        self.editRange.setObjectName(u"editRange")
        self.editRange.setEnabled(False)

        self.verticalLayout_2.addWidget(self.editRange)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.verticalLayout.addWidget(self.grpScope)

        self.buttonBox = QDialogButtonBox(MetadataDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(MetadataDialog)
        self.buttonBox.accepted.connect(MetadataDialog.accept)
        self.buttonBox.rejected.connect(MetadataDialog.reject)
        self.radRange.toggled.connect(self.editRange.setEnabled)

        self.tabs.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MetadataDialog)
    # setupUi

    def retranslateUi(self, MetadataDialog):
        MetadataDialog.setWindowTitle(QCoreApplication.translate("MetadataDialog", u"Edit Metadata", None))
        self.tabs.setTabText(self.tabs.indexOf(self.TagsTab), QCoreApplication.translate("MetadataDialog", u"Tags", None))
        self.tabs.setTabText(self.tabs.indexOf(self.AttributesTab), QCoreApplication.translate("MetadataDialog", u"Attributes", None))
        self.tabs.setTabText(self.tabs.indexOf(self.PresetsTab), QCoreApplication.translate("MetadataDialog", u"Presets", None))
        self.grpScope.setTitle(QCoreApplication.translate("MetadataDialog", u"Apply to", None))
        self.radThis.setText(QCoreApplication.translate("MetadataDialog", u"This file only", None))
        self.radFolder.setText(QCoreApplication.translate("MetadataDialog", u"All files in this folder", None))
        self.radStack.setText(QCoreApplication.translate("MetadataDialog", u"Whole variant stack", None))
        self.radSelected.setText(QCoreApplication.translate("MetadataDialog", u"Current selection", None))
        self.radRange.setText(QCoreApplication.translate("MetadataDialog", u"Custom range", None))
    # retranslateUi

