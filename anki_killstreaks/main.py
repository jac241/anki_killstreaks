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
from functools import partial
import os
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
from anki_killstreaks.controllers import ReviewingController, build_on_answer_wrapper
from anki_killstreaks.persistence import (
    migrate_database,
    get_db_connection,
    AchievementsRepository,
)
from anki_killstreaks.streaks import InitialStreakState, HALO_MULTIKILL_STATES, \
    HALO_KILLING_SPREE_STATES, Store
from anki_killstreaks.views import MedalsOverviewHTML, TodaysMedalsJS, TodaysMedalsForDeckJS
from anki_killstreaks._vendor import attr


@attr.s
class ProfileController:
    """
    Class that contains the parts of the application that need to change
    when the profile changes. This class (plus potentially others like it)
    will be bound to all of the Anki classes. Whenever a user changes profiles,
    the state contained in this class will be mutated to reflect the new
    profile. This ensures that the hooks and method wrapping around Anki objects
    only occurs once. This is necessary because their is no way to unwrap methods or
    unbind hook handlers.
    """
    _db_settings = attr.ib(default=None)
    _achievements_repo = attr.ib(default=None)
    _reviewing_controller = attr.ib(default=None)

    def load_profile(self):
        self._db_settings = migrate_database()

        with get_db_connection(self._db_settings) as db_connection:
            store = Store(
                state_machines=[
                    InitialStreakState(
                        states=HALO_MULTIKILL_STATES,
                        interval_s=local_conf["multikill_interval_s"]
                    ),
                    InitialStreakState(
                        states=HALO_KILLING_SPREE_STATES,
                        interval_s=local_conf["killing_spree_interval_s"]
                    )
                ]
            )

            self._achievements_repo = AchievementsRepository(
                db_connection=db_connection,
            )

            self._reviewing_controller = ReviewingController(
                store=store,
                achievements_repo=self._achievements_repo,
                show_achievements=show_tool_tip_if_medals,
            )

    def get_db_settings(self):
        """
        not using properties or attr built in methods because we need to be
        able to bind the getters for certain wrapping functions in the add-on
        """
        return self._db_settings

    def get_achievements_repo(self):
        return self._achievements_repo

    def on_show_question(self):
        self._reviewing_controller.on_show_question()

    def on_show_answer(self):
        self._reviewing_controller.on_show_answer()

    def on_answer(self, *args, **kwargs):
        self._reviewing_controller.on_answer(*args, **kwargs)

    def unload_profile(self):
        self._db_settings = None
        self._reviewing_controller = None
        self._acheivements_repo = None


profile_controller = ProfileController()


def main():
    addHook("profileLoaded", _load_addon_for_profile)
    addHook("unloadProfile", profile_controller.unload_profile)


def _load_addon_for_profile():
    profile_controller.load_profile()
    _wrap_anki_objects()
    # db_settings = migrate_database()

    # with get_db_connection(db_settings) as db_connection:
        # store = Store(
            # state_machines=[
                # InitialStreakState(
                    # states=HALO_MULTIKILL_STATES,
                    # interval_s=local_conf["multikill_interval_s"]
                # ),
                # InitialStreakState(
                    # states=HALO_KILLING_SPREE_STATES,
                    # interval_s=local_conf["killing_spree_interval_s"]
                # )
            # ]
        # )

        # achievements_repo = AchievementsRepository(
            # db_connection=db_connection,
        # )

        # reviewing_controller = ReviewingController(
            # store=store,
            # achievements_repo=achievements_repo,
            # show_achievements=show_tool_tip_if_medals,
        # )

        # Reviewer._answerCard = wrap(
            # Reviewer._answerCard,
            # partial(build_on_answer_wrapper, on_answer=reviewing_controller.on_answer),
            # 'before',
        # )

def _wrap_anki_objects():
    addHook("showQuestion", profile_controller.on_show_question)
    addHook("showAnswer", profile_controller.on_show_answer)

    Reviewer._answerCard = wrap(
        Reviewer._answerCard,
        partial(build_on_answer_wrapper, on_answer=profile_controller.on_answer),
        'before',
    )

    todays_medals_injector = partial(
        inject_medals_with_js,
        view=TodaysMedalsJS,
        get_db_settings=profile_controller.get_db_settings
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
            get_db_settings=profile_controller.get_db_settings
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


def show_tool_tip_if_medals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


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
            <center><b>{name}!</b><br></center>
        </td>
    """.format(
        img_src=medal.medal_image,
        name=medal.name,
    )


def inject_medals_with_js(
    self: Overview,
    get_db_settings,
    view
):
    def compute_then_inject():
        with get_db_connection(get_db_settings()) as db_connection:
            achievements_repo = AchievementsRepository(
                db_connection=db_connection,
            )

            self.mw.web.eval(
                view(
                    achievements=achievements_repo.todays_achievements(
                        cutoff_time(self)
                    )
                )
            )

    Thread(target=compute_then_inject).start()


def inject_medals_for_deck_overview(self: Overview, get_db_settings):
    def compute_then_inject():
        with get_db_connection(get_db_settings()) as db_connection:
            achievements_repo = AchievementsRepository(
                db_connection=db_connection,
            )

            decks = get_current_deck_and_children(deck_manager=self.mw.col.decks)
            deck_ids = [d.id_ for d in decks]

            self.mw.web.eval(
                TodaysMedalsForDeckJS(
                    achievements=achievements_repo.todays_achievements_for_deck_ids(
                        day_start_time=cutoff_time(self),
                        deck_ids=deck_ids
                    ),
                    deck=decks[0]
                )
            )

    Thread(target=compute_then_inject).start()


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
        return datetime.min


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


def cutoff_time(self):
    one_day_s = 86400
    rolloverHour = self.mw.col.conf.get("rollover", 4)
    return self.mw.col.sched.dayCutoff - (rolloverHour * 3600) - one_day_s


main()
