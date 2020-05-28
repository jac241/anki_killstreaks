from aqt.qt import QDialog, QThread
from .ui.forms.profile_settings_dialog import Ui_ProfileSettingsDialog
import urllib.request
from urllib.parse import urljoin
import json
import requests
from queue import Queue
from functools import partial


sra_base_url = "http://localhost:5000"


def show_dialog(parent, network_thread):
    ProfileSettingsDialog(parent, network_thread).exec_()


class ProfileSettingsDialog(QDialog):
    loginPageIndex = 0
    logoutPageIndex = 1

    def __init__(self, parent, network_thread):
        super().__init__(parent)
        self.ui = Ui_ProfileSettingsDialog()
        self.ui.setupUi(self)

        self._network_thread = network_thread

        self._connect_login_button()

    def _connect_login_button(self):
        self.ui.loginButton.clicked.connect(self._verify_login)

    def _verify_login(self):
        email = self.ui.emailLineEdit.text()
        password = self.ui.passwordLineEdit.text()

        job = partial(
            verify_login_on_remote,
            email,
            password,
            self
        )
        self._network_thread.perform_later(job)

    def on_successful_login(self, user_attrs):
        self._switchToLogoutPage(user_attrs)

    def _switchToLogoutPage(self, user_attrs):
        self.ui.userEmailLabel.setText(user_attrs["email"])
        self.ui.stackedWidget.setCurrentIndex(self.logoutPageIndex)

    def on_unauthorized(self, response):
        self.ui.statusLabel.setText(response["errors"][0])

    def on_connection_error(self):
        self.ui.statusLabel.setText("Error connecting to server. Try again later.")


def verify_login_on_remote(email, password, listener):
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

    try:
        response = requests.post(url, headers=headers, json=body)

        print(response.status_code)
        print(response.text)

        if response.status_code == 200:
            listener.on_successful_login(response.json()["data"])
        elif response.status_code == 401:
            listener.on_unauthorized(response.json())
        else:
            raise RuntimeError("Unhandled response status", response)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        listener.on_connection_error()
