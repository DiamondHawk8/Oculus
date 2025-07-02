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
    QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout,
    QHeaderView, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QRadioButton, QSizePolicy, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_MetadataDialog(object):
    def setupUi(self, MetadataDialog):
        if not MetadataDialog.objectName():
            MetadataDialog.setObjectName(u"MetadataDialog")
        MetadataDialog.resize(818, 446)
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
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.listTags = QListWidget(self.TagsTab)
        self.listTags.setObjectName(u"listTags")

        self.horizontalLayout_3.addWidget(self.listTags)

        self.listFiles = QListWidget(self.TagsTab)
        self.listFiles.setObjectName(u"listFiles")

        self.horizontalLayout_3.addWidget(self.listFiles)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.hboxTagEdit = QHBoxLayout()
        self.hboxTagEdit.setObjectName(u"hboxTagEdit")
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
        self.tabs.addTab(self.AttributesTab, "")
        self.PresetsTab = QWidget()
        self.PresetsTab.setObjectName(u"PresetsTab")
        self.verticalLayout_2 = QVBoxLayout(self.PresetsTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tblPresets = QTableWidget(self.PresetsTab)
        if (self.tblPresets.columnCount() < 3):
            self.tblPresets.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tblPresets.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.tblPresets.setObjectName(u"tblPresets")
        self.tblPresets.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblPresets.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblPresets.setColumnCount(3)
        self.tblPresets.horizontalHeader().setStretchLastSection(True)
        self.tblPresets.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_2.addWidget(self.tblPresets)

        self.hboxPresetBtns = QHBoxLayout()
        self.hboxPresetBtns.setObjectName(u"hboxPresetBtns")
        self.editPresetName = QLineEdit(self.PresetsTab)
        self.editPresetName.setObjectName(u"editPresetName")
        self.editPresetName.setReadOnly(True)
        self.editPresetName.setClearButtonEnabled(True)

        self.hboxPresetBtns.addWidget(self.editPresetName)

        self.btnLoadPreset = QPushButton(self.PresetsTab)
        self.btnLoadPreset.setObjectName(u"btnLoadPreset")

        self.hboxPresetBtns.addWidget(self.btnLoadPreset)

        self.btnDeletePreset = QPushButton(self.PresetsTab)
        self.btnDeletePreset.setObjectName(u"btnDeletePreset")

        self.hboxPresetBtns.addWidget(self.btnDeletePreset)


        self.verticalLayout_2.addLayout(self.hboxPresetBtns)

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

        self.tabs.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MetadataDialog)
    # setupUi

    def retranslateUi(self, MetadataDialog):
        MetadataDialog.setWindowTitle(QCoreApplication.translate("MetadataDialog", u"Edit Metadata", None))
        self.btnCopyTags.setText(QCoreApplication.translate("MetadataDialog", u"Copy", None))
        self.btnPasteTags.setText(QCoreApplication.translate("MetadataDialog", u"Paste", None))
        self.btnRemoveTag.setText(QCoreApplication.translate("MetadataDialog", u"Remove", None))
        self.btnAddTag.setText(QCoreApplication.translate("MetadataDialog", u"Add", None))
        self.tabs.setTabText(self.tabs.indexOf(self.TagsTab), QCoreApplication.translate("MetadataDialog", u"Tags", None))
        self.tabs.setTabText(self.tabs.indexOf(self.AttributesTab), QCoreApplication.translate("MetadataDialog", u"Attributes", None))
        ___qtablewidgetitem = self.tblPresets.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MetadataDialog", u"Name", None));
        ___qtablewidgetitem1 = self.tblPresets.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MetadataDialog", u"Scope", None));
        ___qtablewidgetitem2 = self.tblPresets.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MetadataDialog", u"Properties", None));
        self.editPresetName.setText(QCoreApplication.translate("MetadataDialog", u"New preset name...", None))
        self.btnLoadPreset.setText(QCoreApplication.translate("MetadataDialog", u"Load", None))
        self.btnDeletePreset.setText(QCoreApplication.translate("MetadataDialog", u"Delete", None))
        self.tabs.setTabText(self.tabs.indexOf(self.PresetsTab), QCoreApplication.translate("MetadataDialog", u"Presets", None))
        self.grpScope.setTitle(QCoreApplication.translate("MetadataDialog", u"Apply to", None))
        self.radSelected.setText(QCoreApplication.translate("MetadataDialog", u"Current Selection", None))
        self.radFolder.setText(QCoreApplication.translate("MetadataDialog", u"All Files in This Folder", None))
        self.radThis.setText(QCoreApplication.translate("MetadataDialog", u"This File Only", None))
        self.chkVariants.setText(QCoreApplication.translate("MetadataDialog", u"Apply to Variants", None))
    # retranslateUi

