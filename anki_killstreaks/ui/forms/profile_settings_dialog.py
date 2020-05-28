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
        ProfileSettingsDialog.resize(307, 226)
        self.verticalLayout = QtWidgets.QVBoxLayout(ProfileSettingsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(ProfileSettingsDialog)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
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
        self.passwordLabel = QtWidgets.QLabel(ProfileSettingsDialog)
        self.passwordLabel.setObjectName("passwordLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.passwordLabel)
        self.passwordLineEdit = QtWidgets.QLineEdit(ProfileSettingsDialog)
        self.passwordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordLineEdit.setObjectName("passwordLineEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.passwordLineEdit)
        self.loginButton = QtWidgets.QPushButton(ProfileSettingsDialog)
        self.loginButton.setObjectName("loginButton")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.loginButton)
        self.statusLabel = QtWidgets.QLabel(ProfileSettingsDialog)
        self.statusLabel.setText("")
        self.statusLabel.setObjectName("statusLabel")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.statusLabel)
        self.label_2 = QtWidgets.QLabel(ProfileSettingsDialog)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.label_2)
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
        self.passwordLabel.setText(_translate("ProfileSettingsDialog", "Password"))
        self.loginButton.setText(_translate("ProfileSettingsDialog", "Login"))
        self.label_2.setText(_translate("ProfileSettingsDialog", "<html><head/><body><p><a href=\"https://ankiachievements.com\"><span style=\" text-decoration: underline; color:#0068da;\">Sign Up</span></a></p></body></html>"))
