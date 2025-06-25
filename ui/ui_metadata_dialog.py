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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QGroupBox, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QRadioButton,
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

class Ui_MetadataDialog(object):
    def setupUi(self, MetadataDialog):
        if not MetadataDialog.objectName():
            MetadataDialog.setObjectName(u"MetadataDialog")
        MetadataDialog.resize(638, 501)
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
        self.verticalLayout_3 = QVBoxLayout(self.TagsTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.listTags = QListWidget(self.TagsTab)
        self.listTags.setObjectName(u"listTags")

        self.verticalLayout_3.addWidget(self.listTags)

        self.hboxTagEdit = QHBoxLayout()
        self.hboxTagEdit.setObjectName(u"hboxTagEdit")
        self.editTag = QLineEdit(self.TagsTab)
        self.editTag.setObjectName(u"editTag")

        self.hboxTagEdit.addWidget(self.editTag)

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
        self.tabs.addTab(self.AttributesTab, "")
        self.PresetsTab = QWidget()
        self.PresetsTab.setObjectName(u"PresetsTab")
        self.tabs.addTab(self.PresetsTab, "")

        self.verticalLayout.addWidget(self.tabs)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.grpScope = QGroupBox(MetadataDialog)
        self.grpScope.setObjectName(u"grpScope")
        sizePolicy.setHeightForWidth(self.grpScope.sizePolicy().hasHeightForWidth())
        self.grpScope.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.grpScope)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.radSelected = QRadioButton(self.grpScope)
        self.radSelected.setObjectName(u"radSelected")
        self.radSelected.setChecked(True)

        self.horizontalLayout.addWidget(self.radSelected)

        self.radFolder = QRadioButton(self.grpScope)
        self.radFolder.setObjectName(u"radFolder")
        self.radFolder.setEnabled(True)

        self.horizontalLayout.addWidget(self.radFolder)

        self.radThis = QRadioButton(self.grpScope)
        self.radThis.setObjectName(u"radThis")
        self.radThis.setEnabled(True)

        self.horizontalLayout.addWidget(self.radThis)


        self.horizontalLayout_2.addWidget(self.grpScope)

        self.chkVariants = QCheckBox(MetadataDialog)
        self.chkVariants.setObjectName(u"chkVariants")

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
        self.btnRemoveTag.setText(QCoreApplication.translate("MetadataDialog", u"Remove", None))
        self.btnAddTag.setText(QCoreApplication.translate("MetadataDialog", u"Add", None))
        self.tabs.setTabText(self.tabs.indexOf(self.TagsTab), QCoreApplication.translate("MetadataDialog", u"Tags", None))
        self.tabs.setTabText(self.tabs.indexOf(self.AttributesTab), QCoreApplication.translate("MetadataDialog", u"Attributes", None))
        self.tabs.setTabText(self.tabs.indexOf(self.PresetsTab), QCoreApplication.translate("MetadataDialog", u"Presets", None))
        self.grpScope.setTitle(QCoreApplication.translate("MetadataDialog", u"Apply to", None))
        self.radSelected.setText(QCoreApplication.translate("MetadataDialog", u"Current Selection", None))
        self.radFolder.setText(QCoreApplication.translate("MetadataDialog", u"All Files in This Folder", None))
        self.radThis.setText(QCoreApplication.translate("MetadataDialog", u"This File Only", None))
        self.chkVariants.setText(QCoreApplication.translate("MetadataDialog", u"Apply to Variants", None))
    # retranslateUi

