from functools import partial
from urllib.parse import urljoin

from aqt.qt import QTimer
import requests

from ._vendor import attr

from . import accounts, tooltips
from .networking import (
    StatusListeningHttpClient,
    TokenAuthHttpClient,
    sra_base_url,
    show_logged_out_tooltip
)
from .views import html_content


@attr.s
class ChaseModeContext:
    _profile_controller = attr.ib()
    webview = attr.ib()
    main_window = attr.ib()

    @property
    def user_is_logged_in(self):
        return accounts.check_user_logged_in(self.user_repo)

    @property
    def user_repo(self):
        return self._profile_controller.get_user_repo()

    @property
    def job_queue(self):
        return self._profile_controller.job_queue

    def start_job(self, job):
        self.job_queue.put(job)


def setup_hooks(main_window, gui_hooks, Reviewer, profile_controller):
    def initialize_chase_mode_js(web_content, context=None):
        if isinstance(context, Reviewer):
            addon_package = main_window.addonManager.addonFromModule(__name__)
            web_content.css.append(f"/_addons/{addon_package}/web/chase_mode.css")
            web_content.css.append(f"/_addons/{addon_package}/web/spinner.css")
            web_content.js.append(f"/_addons/{addon_package}/web/chase_mode.js")
            web_content.body += html_content("chase_mode/initialize.html")
        else:
            _stop_timer_if_it_exists()

    main_window.addonManager.setWebExports(__name__, r"web/.*")
    gui_hooks.webview_will_set_content.append(initialize_chase_mode_js)

    def listen_for_chase_mode_loaded(handled, message, context):
        if not isinstance(context, Reviewer):
            # not reviewer, pass on message
            return handled

        if message == "chaseModeLoaded":
            chase_mode_context = ChaseModeContext(
                profile_controller,
                webview=context.web,
                main_window=main_window,
            )

            _initialize_if_logged_in(chase_mode_context)

            return (True, None)
        else:
            return handled
    gui_hooks.webview_did_receive_js_message.append(listen_for_chase_mode_loaded)


def _initialize_if_logged_in(chase_mode_context):
    if chase_mode_context.user_is_logged_in:
        _initialize(chase_mode_context)
    else:
        _render_not_logged_in(chase_mode_context.webview)


def _initialize(chase_mode_context):
    http_client = StatusListeningHttpClient(
        http_client=TokenAuthHttpClient(
            chase_mode_context.user_repo, shared_headers={}
        ),
        status=401,
        on_status=partial(
            _inform_user_they_are_not_logged_in,
            chase_mode_context.webview,
        ),
    )
    _show_chase_mode(http_client, chase_mode_context)
    _start_chase_mode_timer(http_client, chase_mode_context)


def _inform_user_they_are_not_logged_in(webview):
    show_logged_out_tooltip()
    _render_not_logged_in(webview)
    _stop_timer_if_it_exists()


def _render_not_logged_in(webview):
    render(webview, html_content("chase_mode/_not_logged_in.html"))


def _stop_timer_if_it_exists():
    if _chase_mode_timer:
        print("Stopping chase mode timer")
        _chase_mode_timer.stop()


def _show_chase_mode(http_client, chase_mode_context):
    job = partial(
        _fetch_and_display_chase_mode,
        http_client,
        chase_mode_context,
    )
    chase_mode_context.start_job(job)


_chase_mode_timer = None
# _CHASE_MODE_INTERVAL_MS = 2 * 1000
_CHASE_MODE_INTERVAL_MS = 45 * 1000


def _start_chase_mode_timer(http_client, chase_mode_context):
    global _chase_mode_timer
    _chase_mode_timer = QTimer(chase_mode_context.main_window)

    on_timer = partial(
        _fetch_and_display_chase_mode,
        http_client,
        chase_mode_context
    )

    _chase_mode_timer.timeout.connect(on_timer)
    _chase_mode_timer.start(_CHASE_MODE_INTERVAL_MS)


_connection_error_message_shown = False


def _fetch_and_display_chase_mode(http_client, chase_mode_context):
    global _connection_error_message_shown

    try:
        response = http_client.get(url=urljoin(sra_base_url, "/api/v1/rivalries/halo-3"))
        response.raise_for_status()
        _connection_error_message_shown = False
        render(chase_mode_context.webview, response.text)
    except requests.exceptions.ConnectionError as e:
        print("Connection error while updating chase mode")
        _show_conn_err_tooltip_if_first_time()


def render(webview, text):
    webview.eval(fr"setChaseModeHTML(String.raw`{text}`)")


def _show_conn_err_tooltip_if_first_time():
    global _connection_error_message_shown

    if not _connection_error_message_shown:
        tooltips.showToolTip(html=html_content("chase_mode/_connection_error.html"), period=8000)
        _connection_error_message_shown = True

