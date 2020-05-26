from aqt.qt import QDialog
from .ui.forms.profile_settings_dialog import Ui_ProfileSettingsDialog


class ProfileSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_ProfileSettingsDialog()
        self.ui.setupUi(self)

        self._connect_verify_login_button()

    def _connect_verify_login_button(self):
        self.ui.verifyLoginButton.clicked.connect(self._verify_login)

    def _verify_login(self):
        email = self.ui.emailLineEdit.text()
        token = self.ui.tokenLineEdit.text()

        print("email", email, "token", token)


def show_dialog(parent):
    ProfileSettingsDialog(parent).exec_()
