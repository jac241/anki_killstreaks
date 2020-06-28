from aqt.qt import QObject, pyqtSignal
from functools import partialmethod, partial
import random
from threading import Thread
import time
import requests
import os
import traceback
from ._vendor import attr
from . import accounts, tooltips

sra_base_url = "http://192.168.200.192:5000/"
# sra_base_url = "http://localhost:5000"
if not os.environ.get("KILLSTREAKS_ENV", "development") == "development":
    sra_base_url = "https://ankiachievements.com"


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


class DaemonTimer:
    def __init__(self, function, interval):
        self._function = function
        self._interval = interval

    def start(self):
        thread = Thread(target=self._wait_then_call_func, daemon=True)
        thread.start()
        return thread

    def _wait_then_call_func(self):
        time.sleep(self._interval)
        self._function()


@attr.s(frozen=True)
class RequeuingJob:
    _job = attr.ib()
    _exception_to_retry_on = attr.ib()
    _job_queue = attr.ib()
    _backoff_n = attr.ib(default=1)

    def __call__(self):
        try:
            self._job()
        except self._exception_to_retry_on as e:
            self._requeue_after_backoff()

    def _requeue_after_backoff(self):
        print("Will requeue job after", self._backoff, "seconds")
        new_instance = attr.evolve(
            self,
            backoff_n=self._backoff_n + 1,
        )
        requeue_job = partial(
            self._job_queue.put,
            new_instance
        )
        timer = DaemonTimer(
            interval=self._backoff,
            function=requeue_job,
        )
        timer.start()

    @property
    def _backoff(self):
        jitter_s = random.uniform(0, 1)
        return (2 ** self._backoff_n) + jitter_s


def show_logged_out_tooltip():
    message = (
        "<td>Anki killstreaks tried to make a request to its server, "
        "but you were no longer signed in. <br>"
        "Sign in again to see your live progress. <br>"
        "Medals earned while you are not signed in will be synced the next time "
        "you sign in.</td>"
    )
    tooltips.showToolTip(html=message, period=10000)
