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
import random
from threading import Thread

from aqt import mw
from aqt.qt import *
from aqt.deckbrowser import DeckBrowser
from aqt.reviewer import Reviewer
from aqt.overview import Overview
from anki.hooks import addHook, wrap
from anki.stats import CollectionStats

from anki_killstreaks.config import local_conf
from anki_killstreaks.controllers import (
    ProfileController,
    ReviewingController,
    build_on_answer_wrapper,
    GameController,
)
from anki_killstreaks.persistence import day_start_time, min_datetime
from anki_killstreaks.streaks import get_stores_by_game_id
from anki_killstreaks.views import MedalsOverviewHTML, TodaysMedalsJS, TodaysMedalsForDeckJS
from anki_killstreaks._vendor import attr


def show_tool_tip_if_medals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


def _get_profile_folder_path(profile_manager=mw.pm):

    folder = profile_manager.profileFolder()
    # not sure when addons are loaded
    assert folder

    return Path(folder)

_stores_by_game_id = get_stores_by_game_id(config=local_conf)

_profile_controller = ProfileController(
    local_conf=local_conf,
    show_achievements=show_tool_tip_if_medals,
    get_profile_folder_path=_get_profile_folder_path,
    stores_by_game_id=_stores_by_game_id,
)

_game_controller = GameController(
    profile_controller=_profile_controller
)


def main():
    _wrap_anki_objects(_profile_controller)
    _connect_menu(main_window=mw, game_controller=_game_controller)


def _wrap_anki_objects(profile_controller):
    """
    profileLoaded hook fired after deck broswer gets shown(???), so we can't
    actually rely on that hook for anything... To get around this,
    made a decorator that I'll decorate any method that uses the profile
    controller to make sure it's loaded
    """
    addHook("unloadProfile", _profile_controller.unload_profile)

    addHook("showQuestion", profile_controller.on_show_question)
    addHook("showAnswer", profile_controller.on_show_answer)

    Reviewer._answerCard = wrap(
        Reviewer._answerCard,
        partial(
            build_on_answer_wrapper,
            on_answer=profile_controller.on_answer
        ),
        'before',
    )

    todays_medals_injector = partial(
        inject_medals_with_js,
        view=TodaysMedalsJS,
        get_achievements_repo=profile_controller.get_achievements_repo,
    )

    DeckBrowser.refresh = wrap(
        old=DeckBrowser.refresh,
        new=todays_medals_injector,
        pos="after"
    )
    DeckBrowser.show = wrap(
        old=DeckBrowser.show,
        new=todays_medals_injector,
        pos="after"
    )
    Overview.refresh = wrap(
        old=Overview.refresh,
        new=partial(
            inject_medals_for_deck_overview,
            get_achievements_repo=profile_controller.get_achievements_repo
        ),
        pos="after"
    )
    CollectionStats.todayStats = wrap(
        old=CollectionStats.todayStats,
        new=partial(
            show_medals_overview,
            get_achievements_repo=profile_controller.get_achievements_repo
        ),
        pos="around"
    )


selected_game = 'halo_3'


def check_correct_game_in_menu(menu_actions_by_game_id, game_controller):
    current_game_id = game_controller.load_current_game_id()

    for game_id, action in menu_actions_by_game_id.items():
        if game_id == current_game_id:
            action.setChecked(True)
        else:
            action.setChecked(False)


def select_game(game):
    global selected_game
    selected_game = game


def _connect_menu(main_window, game_controller):
    top_menu = QMenu('Killstreaks', main_window)
    game_menu = QMenu('Select game', main_window)

    halo_3_action = game_menu.addAction('Halo 3')
    halo_3_action.setCheckable(True)
    halo_3_action.triggered.connect(
        partial(game_controller.set_current_game_id, game_id='halo_3')
    )

    mw2_action = game_menu.addAction('Call of Duty: Modern Warfare 2')
    mw2_action.setCheckable(True)
    mw2_action.triggered.connect(
        partial(game_controller.set_current_game_id, game_id='mw2')
    )

    top_menu.addMenu(game_menu)

    game_menu.aboutToShow.connect(
        partial(
            check_correct_game_in_menu,
            menu_actions_by_game_id=dict(
                halo_3=halo_3_action,
                mw2=mw2_action
            ),
            game_controller=game_controller,
        )
    )

    main_window.form.menubar.addMenu(top_menu)


_tooltipTimer = None
_tooltipLabel = None


def showToolTip(medals, period=local_conf["duration"]):
    global _tooltipTimer, _tooltipLabel
    class CustomLabel(QLabel):
        def mousePressEvent(self, evt):
            evt.accept()
            self.hide()
    closeTooltip()
    medals_html = '\n'.join(medal_html(m) for m in medals)

    aw = mw.app.activeWindow() or mw
    lab = CustomLabel("""\
<table cellpadding=10>
<tr>
%s
</tr>
</table>""" % (medals_html), aw)
    lab.setFrameStyle(QFrame.Panel)
    lab.setLineWidth(2)
    lab.setWindowFlags(Qt.ToolTip)
    p = QPalette()
    p.setColor(QPalette.Window, QColor(local_conf["tooltip_color"]))
    p.setColor(QPalette.WindowText, QColor("#f7f7f7"))
    lab.setPalette(p)
    vdiff = (local_conf["image_height"] - 128) / 2
    lab.move(
        aw.mapToGlobal(QPoint(0, -260-vdiff + aw.height())))
    lab.show()
    _tooltipTimer = mw.progress.timer(
        period, closeTooltip, False)
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
        img_src=medal.medal_image,
        call=medal.call,
    )


def inject_medals_with_js(self: Overview, get_achievements_repo, view):
    self.mw.web.eval(
        view(
            achievements=get_achievements_repo().todays_achievements(
                cutoff_datetime(self)
            )
        )
    )


def inject_medals_for_deck_overview(self: Overview, get_achievements_repo):
    decks = get_current_deck_and_children(deck_manager=self.mw.col.decks)
    deck_ids = [d.id_ for d in decks]

    self.mw.web.eval(
        TodaysMedalsForDeckJS(
            achievements=get_achievements_repo().todays_achievements_for_deck_ids(
                day_start_time=cutoff_datetime(self),
                deck_ids=deck_ids
            ),
            deck=decks[0]
        )
    )


@attr.s
class Deck:
    id_ = attr.ib()
    name = attr.ib()


def get_current_deck_and_children(deck_manager):
    current_deck_attrs = deck_manager.current()

    current_deck = Deck(current_deck_attrs['id'], current_deck_attrs['name'])
    children = [
        Deck(name=name_id_pair[0], id_=name_id_pair[1])
        for name_id_pair
        in deck_manager.children(current_deck.id_)
    ]

    return [current_deck, *children]


def show_medals_overview(self: CollectionStats, _old, get_achievements_repo):
    # if self.wholeCollection:
    current_deck = self.col.decks.current()["name"]

    header_text = _get_stats_header(
        deck_name=current_deck,
        scope_is_whole_collection=self.wholeCollection,
        period=self.type
    )

    deck_ids = [d.id_ for d in get_current_deck_and_children(self.col.decks)]

    achievements = _get_achievements_scoped_to_deck_or_collection(
        deck_ids=deck_ids,
        scope_is_whole_collection=self.wholeCollection,
        achievements_repo=get_achievements_repo(),
        start_datetime=_get_start_datetime_for_period(self.type)
    )

    return _old(self) + MedalsOverviewHTML(
        achievements=achievements,
        header_text=header_text
    )


def _get_stats_header(deck_name, scope_is_whole_collection, period):
    scope_name = "your whole collection" if scope_is_whole_collection else f'deck "{deck_name}"'
    time_period_description = _get_time_period_description(period)
    return f"Medals earned while reviewing {scope_name} {time_period_description}:"


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
    deck_ids,
    scope_is_whole_collection,
    achievements_repo,
    start_datetime
):
    if scope_is_whole_collection:
        return achievements_repo.achievements_for_whole_collection_since(
            since_datetime=start_datetime
        )
    else:
        return achievements_repo.achievements_for_deck_ids_since(
            deck_ids=deck_ids,
            since_datetime=start_datetime
        )


def cutoff_datetime(self):
    return day_start_time(rollover_hour=self.mw.col.conf.get("rollover", 4))


main()
