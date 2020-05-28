from aqt.qt import QDialog, QThread
from .ui.forms.profile_settings_dialog import Ui_ProfileSettingsDialog
import urllib.request
from urllib.parse import urljoin
import json
import requests
from queue import Queue
from functools import partial


sra_base_url = "https://ankiachievements.com"


class ProfileSettingsDialog(QDialog):
    def __init__(self, parent, network_thread):
        super().__init__(parent)
        self.ui = Ui_ProfileSettingsDialog()
        self.ui.setupUi(self)

        self._network_thread = network_thread

        self._connect_verify_login_button()

    def _connect_verify_login_button(self):
        self.ui.loginButton.clicked.connect(self._verify_login)

    def _verify_login(self):
        email = self.ui.emailLineEdit.text()
        password = self.ui.passwordLineEdit.text()

        job = partial(
            verify_login_on_remote,
            email,
            password,
            self._on_successful_login
        )
        self._network_thread.perform_later(job)

    def _on_successful_login(self, user):
        self.ui.statusLabel.setText(user["email"])


def show_dialog(parent, network_thread):
    ProfileSettingsDialog(parent, network_thread).exec_()


def verify_login_on_remote(email, password, on_success):
    headers={
        "user_email": "JimmyYoshi@gmail.com",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    body = dict(
        email=email,
        password=password,
    )
    url = urljoin(sra_base_url, "api/v1/auth/sign_in")

    response = requests.post(url, headers=headers, json=body)
    print(response.text)
    on_success(response.json()["data"])
