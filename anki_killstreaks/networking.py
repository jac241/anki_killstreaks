from aqt.qt import QDialog, QThread, QObject, pyqtSignal
from functools import partialmethod
from queue import Queue
import requests
import traceback
from ._vendor import attr, backoff
from . import accounts, tooltips


sra_base_url = "http://192.168.200.192:5000/"
# sra_base_url = "https://ankiachievements.com"
# sra_base_url = "http://localhost:5000"
shared_headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


stop_sentinel = "__stop!__"


def process_queue(queue):
    while True:
        job = queue.get()

        if job == stop_sentinel:
            print("network thread stopped! :-)")
            break

        try:
            print("Executing -", job)
            job()
            print("Finished.")
        except Exception as e:
            print("Exception encountered in killstreaks job thread:")
            print(traceback.format_exc())
        finally:
            queue.task_done()
    return


def stop_thread_on_app_close(app, queue):
    def stop():
        queue.put(stop_sentinel)

    app.aboutToQuit.connect(stop)


@attr.s
class TokenAuthHttpClient:
    _user_repo = attr.ib()
    _shared_headers = attr.ib(default=shared_headers)

    def _do_request(self, method, skip_shared_headers=False, **kwargs):
        response = getattr(requests, method)(
            **kwargs,
            headers=self._headers_for_request(skip_shared_headers)
        )

        if response.status_code != 401:
            accounts.store_auth_headers(self._user_repo, response.headers)
        else:
            accounts.clear_auth_headers(self._user_repo)

        return response

    get = partialmethod(_do_request, 'get')
    post = partialmethod(_do_request, 'post')
    put = partialmethod(_do_request, 'put')
    delete = partialmethod(_do_request, 'delete')

    def _headers_for_request(self, skip_shared_headers):
        headers = dict() if skip_shared_headers else self._shared_headers.copy()
        headers.update(self._auth_headers)
        return headers

    @property
    def _auth_headers(self):
        return accounts.load_auth_headers(self._user_repo)


class StatusListeningHttpClient(QObject):
    status_occurred = pyqtSignal(object)

    def __init__(self, http_client, status, on_status, parent=None):
        super().__init__(parent)
        self._http_client = http_client
        self._status = status

        self.status_occurred.connect(on_status)

    def _do_request(self, method, **kwargs):
        response = getattr(self._http_client, method)(**kwargs)

        if response.status_code == self._status:
            self.status_occurred.emit(response)

        return response

    get = partialmethod(_do_request, 'get')
    post = partialmethod(_do_request, 'post')
    put = partialmethod(_do_request, 'put')
    delete = partialmethod(_do_request, 'delete')


def show_logged_out_tooltip():
    message = (
        "<td>Anki killstreaks tried to make a request to its server, "
        "but you were no longer signed in. <br>"
        "Sign in again to see your live progress. <br>"
        "Medals earned while you are not signed in will be synced the next time "
        "you sign in.</td>"
    )
    tooltips.showToolTip(html=message, period=10000)
