from functools import partial
from urllib.parse import urljoin

from . import accounts
from .networking import StatusListeningHttpClient, TokenAuthHttpClient, sra_base_url


def initialize(webview, get_user_repo, job_queue):
    user_repo = get_user_repo()
    if accounts.check_user_logged_in(user_repo):
        html = "<b>logged in</b>"
        webview.eval(fr"setChaseModeHTML('{html}')")
        show_chase_mode(user_repo, job_queue, webview)
    else:
        html = "<b>not logged in now, hide from killstreaks menu</b>"
        webview.eval(fr"setChaseModeHTML('{html}')")


def show_chase_mode(user_repo, job_queue, webview):
    http_client = TokenAuthHttpClient(user_repo, shared_headers={})
    job = partial(
        _fetch_and_display_chase_mode,
        user_repo,
        http_client,
        webview,
    )
    job_queue.put(job)


def _fetch_and_display_chase_mode(user_repo, http_client, webview):
    response = http_client.get(url=urljoin(sra_base_url, "/api/v1/rivalries/halo-3"))
    response.raise_for_status()

    render(webview, response.text)


def render(webview, text):
    webview.eval(fr"setChaseModeHTML(String.raw`{text}`)")

