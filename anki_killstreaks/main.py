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
    AcheivementsRepository,
)
from anki_killstreaks.streaks import InitialStreakState, HALO_MULTIKILL_STATES, \
    HALO_KILLING_SPREE_STATES, Store
from anki_killstreaks.views import MedalsOverviewHTML, TodaysMedalsJS, TodaysMedalsForDeckJS
from anki_killstreaks._vendor import attr


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

def main():
    db_settings = migrate_database()

    with get_db_connection(db_settings) as db_connection:
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

        acheivements_repo = AcheivementsRepository(
            db_connection=db_connection,
        )

        reviewing_controller = ReviewingController(
            store=store,
            acheivements_repo=acheivements_repo,
            show_acheivements=show_tool_tip_if_medals,
        )

        Reviewer._answerCard = wrap(
            Reviewer._answerCard,
            partial(build_on_answer_wrapper, on_answer=reviewing_controller.on_answer),
            'before',
        )

        addHook("showQuestion", reviewing_controller.on_show_question)
        addHook("showAnswer", reviewing_controller.on_show_answer)

        todays_medals_injector = partial(
            inject_medals_with_js,
            view=TodaysMedalsJS,
            db_settings=db_settings
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
            new=partial(inject_medals_for_deck_overview, db_settings=db_settings),
            pos="after"
        )
        CollectionStats.todayStats = wrap(
            old=CollectionStats.todayStats,
            new=partial(
                show_medals_overview, acheivements_repo=acheivements_repo
            ),
            pos="around"
        )


def show_tool_tip_if_medals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


def inject_medals_with_js(
    self: Overview,
    db_settings,
    view
):
    def compute_then_inject():
        with get_db_connection(db_settings) as db_connection:
            acheivements_repo = AcheivementsRepository(
                db_connection=db_connection,
            )

            self.mw.web.eval(
                view(
                    acheivements=acheivements_repo.todays_acheivements(
                        cutoff_time(self)
                    )
                )
            )

    Thread(target=compute_then_inject).start()


def inject_medals_for_deck_overview(self: Overview, db_settings):
    def compute_then_inject():
        with get_db_connection(db_settings) as db_connection:
            acheivements_repo = AcheivementsRepository(
                db_connection=db_connection,
            )

            decks = get_current_deck_and_children(deck_manager=self.mw.col.decks)
            deck_ids = [d.id_ for d in decks]

            self.mw.web.eval(
                TodaysMedalsForDeckJS(
                    acheivements=acheivements_repo.todays_acheivements_for_deck_ids(
                        day_start_time=cutoff_time(self),
                        deck_ids=deck_ids
                    ),
                    deck=decks[0]
                )
            )

    Thread(target=compute_then_inject).start()




def show_medals_overview(self: CollectionStats, _old, acheivements_repo):
    return _old(self) + MedalsOverviewHTML(
        acheivements=acheivements_repo.count_by_medal_id(),
        header_text="All Medals Earned:"
    )


def cutoff_time(self):
    one_day_s = 86400
    rolloverHour = self.mw.col.conf.get("rollover", 4)
    return self.mw.col.sched.dayCutoff - (rolloverHour * 3600) - one_day_s


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



main()
