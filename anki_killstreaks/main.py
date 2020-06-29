# -*- coding: utf-8 -*-
"""
Original Copyright/License statement
------
Anki Add-on: Puppy Reinforcement

Uses intermittent reinforcement to encourage card review streaks

Copyright: (c) Glutanimate 2016-2018 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
------

Modifications by jac241 <https://github.com/jac241> for Anki Killstreaks addon
"""

from datetime import datetime, timedelta
from functools import partial, wraps
import os
from pathlib import Path
from queue import Queue
import random
from threading import Thread
from urllib.parse import urljoin

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.deckbrowser import DeckBrowser
from aqt.reviewer import Reviewer
from aqt.overview import Overview
from anki.hooks import addHook, wrap
from anki.stats import CollectionStats

from . import chase_mode
from .config import local_conf
from .controllers import (
    ProfileController,
    ReviewingController,
    build_on_answer_wrapper,
    call_method_on_object_from_factory_function,
)
from .menu import connect_menu
from .networking import process_queue, stop_thread_on_app_close
from .persistence import day_start_time, min_datetime
from .streaks import get_stores_by_game_id
from .views import (
    MedalsOverviewHTML,
    TodaysMedalsJS,
    TodaysMedalsForDeckJS,
    js_content,
    html_content,
)
from ._vendor import attr


def show_tool_tip_if_medals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


def _get_profile_folder_path(profile_manager=mw.pm):
    folder = profile_manager.profileFolder()
    return Path(folder)


_stores_by_game_id = get_stores_by_game_id(config=local_conf)

job_queue = Queue()
_network_thread = Thread(target=process_queue, args=(job_queue,))
stop_thread_on_app_close(app=QApplication.instance(), queue=job_queue)


_profile_controller = ProfileController(
    local_conf=local_conf,
    show_achievements=show_tool_tip_if_medals,
    get_profile_folder_path=_get_profile_folder_path,
    stores_by_game_id=_stores_by_game_id,
    job_queue=job_queue,
    main_window=mw,
)

# for debugging
mw.killstreaks_profile_controller = _profile_controller


def main():
    _wrap_anki_objects(_profile_controller)
    connect_menu(main_window=mw, profile_controller=_profile_controller, network_thread=job_queue)
    _network_thread.start()


def _wrap_anki_objects(profile_controller):
    """
    profileLoaded hook fired after deck broswer gets shown(???), so we can't
    actually rely on that hook for anything... To get around this,
    made a decorator that I'll decorate any method that uses the profile
    controller to make sure it's loaded
    """
    addHook("unloadProfile", profile_controller.unload_profile)

    # Need to make sure we call these methods on the current reviewing controller.
    # Reviewing controller instance changes when profile changes.
    call_method_on_reviewing_controller = partial(
        call_method_on_object_from_factory_function,
        factory_function=profile_controller.get_reviewing_controller,
    )

    addHook(
        "showQuestion", call_method_on_reviewing_controller("on_show_question")
    )
    addHook("showAnswer", call_method_on_reviewing_controller("on_show_answer"))

    Reviewer._answerCard = wrap(
        Reviewer._answerCard,
        partial(
            build_on_answer_wrapper,
            on_answer=call_method_on_reviewing_controller("on_answer"),
        ),
        "before",
    )

    todays_medals_injector = partial(
        inject_medals_with_js,
        view=TodaysMedalsJS,
        get_achievements_repo=profile_controller.get_achievements_repo,
        get_current_game_id=profile_controller.get_current_game_id,
    )

    DeckBrowser.refresh = wrap(
        old=DeckBrowser.refresh, new=todays_medals_injector, pos="after"
    )
    DeckBrowser.show = wrap(
        old=DeckBrowser.show, new=todays_medals_injector, pos="after"
    )

    Overview.refresh = wrap(
        old=Overview.refresh,
        new=partial(
            inject_medals_for_deck_overview,
            get_achievements_repo=profile_controller.get_achievements_repo,
            get_current_game_id=profile_controller.get_current_game_id,
        ),
        pos="after",
    )

    CollectionStats.todayStats = wrap(
        old=CollectionStats.todayStats,
        new=partial(
            show_medals_overview,
            get_achievements_repo=profile_controller.get_achievements_repo,
            get_current_game_id=profile_controller.get_current_game_id,
        ),
        pos="around",
    )
    chase_mode.setup_hooks(mw, gui_hooks, Reviewer, profile_controller)


_tooltipTimer = None
_tooltipLabel = None


def showToolTip(medals, period=local_conf["duration"]):
    global _tooltipTimer, _tooltipLabel

    class CustomLabel(QLabel):
        def mousePressEvent(self, evt):
            evt.accept()
            self.hide()

    closeTooltip()
    medals_html = "\n".join(medal_html(m) for m in medals)

    aw = mw.app.activeWindow() or mw
    lab = CustomLabel(
        """\
<table cellpadding=10>
<tr>
%s
</tr>
</table>"""
        % (medals_html),
        aw,
    )
    lab.setFrameStyle(QFrame.Panel)
    lab.setLineWidth(2)
    lab.setWindowFlags(Qt.ToolTip)
    p = QPalette()
    p.setColor(QPalette.Window, QColor(local_conf["tooltip_color"]))
    p.setColor(QPalette.WindowText, QColor("#f7f7f7"))
    lab.setPalette(p)
    vdiff = (local_conf["image_height"] - 128) / 2
    lab.move(aw.mapToGlobal(QPoint(0, -260 - vdiff + aw.height())))
    lab.show()
    _tooltipTimer = mw.progress.timer(period, closeTooltip, False)
    _tooltipLabel = lab


def closeTooltip():
    global _tooltipLabel, _tooltipTimer
    if _tooltipLabel:
        try:
            _tooltipLabel.deleteLater()
        except:
            # already deleted as parent window closed
            pass
        _tooltipLabel = None
    if _tooltipTimer:
        _tooltipTimer.stop()
        _tooltipTimer = None


def medal_html(medal):
    return """
        <td valign="middle" style="text-align:center">
            <img src="{img_src}">
            <center><b>{call}!</b><br></center>
        </td>
    """.format(
        img_src=medal.medal_image, call=medal.call,
    )


def inject_medals_with_js(
    self: Overview, get_achievements_repo, get_current_game_id, view
):
    self.mw.web.eval(
        view(
            achievements=get_achievements_repo().todays_achievements(
                cutoff_datetime(self)
            ),
            current_game_id=get_current_game_id(),
        )
    )
    self.mw.web.eval(js_content("medals_overview.js"))


def inject_medals_for_deck_overview(
    self: Overview, get_achievements_repo, get_current_game_id,
):
    decks = get_current_deck_and_children(deck_manager=self.mw.col.decks)
    deck_ids = [d.id_ for d in decks]

    self.mw.web.eval(
        TodaysMedalsForDeckJS(
            achievements=get_achievements_repo().todays_achievements_for_deck_ids(
                day_start_time=cutoff_datetime(self), deck_ids=deck_ids
            ),
            deck=decks[0],
            current_game_id=get_current_game_id(),
        )
    )
    self.mw.web.eval(js_content("medals_overview.js"))


@attr.s
class Deck:
    id_ = attr.ib()
    name = attr.ib()


def get_current_deck_and_children(deck_manager):
    current_deck_attrs = deck_manager.current()

    current_deck = Deck(current_deck_attrs["id"], current_deck_attrs["name"])
    children = [
        Deck(name=name_id_pair[0], id_=name_id_pair[1])
        for name_id_pair in deck_manager.children(current_deck.id_)
    ]

    return [current_deck, *children]


def show_medals_overview(
    self: CollectionStats, _old, get_achievements_repo, get_current_game_id,
):
    current_deck = self.col.decks.current()["name"]

    header_text = _get_stats_header(
        deck_name=current_deck,
        scope_is_whole_collection=self.wholeCollection,
        period=self.type,
    )

    deck_ids = [d.id_ for d in get_current_deck_and_children(self.col.decks)]

    achievements = _get_achievements_scoped_to_deck_or_collection(
        deck_ids=deck_ids,
        scope_is_whole_collection=self.wholeCollection,
        achievements_repo=get_achievements_repo(),
        start_datetime=_get_start_datetime_for_period(self.type),
    )

    return _old(self) + MedalsOverviewHTML(
        achievements=achievements,
        header_text=header_text,
        current_game_id=get_current_game_id(),
    )


def _get_stats_header(deck_name, scope_is_whole_collection, period):
    scope_name = (
        "your whole collection"
        if scope_is_whole_collection
        else f'deck "{deck_name}"'
    )
    time_period_description = _get_time_period_description(period)
    return (
        f"Medals earned while reviewing {scope_name} {time_period_description}:"
    )


PERIOD_MONTH = 0
PERIOD_YEAR = 1


def _get_time_period_description(period):
    if period == PERIOD_MONTH:
        return "over the past month"
    elif period == PERIOD_YEAR:
        return "over the past year"
    else:
        return "over the deck's life"


def _get_start_datetime_for_period(period):
    if period == PERIOD_MONTH:
        return datetime.now() - timedelta(days=30)
    elif period == PERIOD_YEAR:
        return datetime.now() - timedelta(days=365)
    else:
        return min_datetime


def _get_achievements_scoped_to_deck_or_collection(
    deck_ids, scope_is_whole_collection, achievements_repo, start_datetime
):
    if scope_is_whole_collection:
        return achievements_repo.achievements_for_whole_collection_since(
            since_datetime=start_datetime
        )
    else:
        return achievements_repo.achievements_for_deck_ids_since(
            deck_ids=deck_ids, since_datetime=start_datetime
        )


def cutoff_datetime(self):
    return day_start_time(rollover_hour=self.mw.col.conf.get("rollover", 4))


main()
