from aqt.qt import QDialog, QThread, QObject
from functools import partialmethod
from queue import Queue
import requests
import traceback
from ._vendor import attr
from . import accounts


# sra_base_url = "https://ankiachievements.com"
sra_base_url = "http://localhost:5000"
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


# @attr.s
# class StatusListeningHttpClient:
    # _http_client = attr.ib()
    # _status = attr.ib()
    # _on_status = attr.ib()

    # def _do_request(self, method, **kwargs):
        # response = getattr(self._http_client, method)(**kwargs)

        # if response.status_code == self._status:
            # self._on_status(response)

        # return response

    # get = partialmethod(_do_request, 'get')
    # post = partialmethod(_do_request, 'post')
    # put = partialmethod(_do_request, 'put')
    # delete = partialmethod(_do_request, 'delete')
