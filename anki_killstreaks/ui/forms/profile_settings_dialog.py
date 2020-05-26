# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/profile_settings_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ProfileSettingsDialog(object):
    def setupUi(self, ProfileSettingsDialog):
        ProfileSettingsDialog.setObjectName("ProfileSettingsDialog")
        ProfileSettingsDialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(ProfileSettingsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(ProfileSettingsDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.emailLabel = QtWidgets.QLabel(ProfileSettingsDialog)
        self.emailLabel.setObjectName("emailLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.emailLabel)
        self.emailLineEdit = QtWidgets.QLineEdit(ProfileSettingsDialog)
        self.emailLineEdit.setObjectName("emailLineEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.emailLineEdit)
        self.tokenLabel = QtWidgets.QLabel(ProfileSettingsDialog)
        self.tokenLabel.setObjectName("tokenLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.tokenLabel)
        self.tokenLineEdit = QtWidgets.QLineEdit(ProfileSettingsDialog)
        self.tokenLineEdit.setObjectName("tokenLineEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.tokenLineEdit)
        self.verifyLoginButton = QtWidgets.QPushButton(ProfileSettingsDialog)
        self.verifyLoginButton.setObjectName("verifyLoginButton")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.verifyLoginButton)
        self.statusLabel = QtWidgets.QLabel(ProfileSettingsDialog)
        self.statusLabel.setText("")
        self.statusLabel.setObjectName("statusLabel")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.statusLabel)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(ProfileSettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ProfileSettingsDialog)
        self.buttonBox.accepted.connect(ProfileSettingsDialog.accept)
        self.buttonBox.rejected.connect(ProfileSettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ProfileSettingsDialog)

    def retranslateUi(self, ProfileSettingsDialog):
        _translate = QtCore.QCoreApplication.translate
        ProfileSettingsDialog.setWindowTitle(_translate("ProfileSettingsDialog", "Dialog"))
        self.label.setText(_translate("ProfileSettingsDialog", "Log in to Killstreaks/Achievements leaderboard"))
        self.emailLabel.setText(_translate("ProfileSettingsDialog", "Email"))
        self.tokenLabel.setText(_translate("ProfileSettingsDialog", "Token"))
        self.verifyLoginButton.setText(_translate("ProfileSettingsDialog", "Verify Login"))
