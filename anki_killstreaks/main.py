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

import os
import random
from datetime import datetime, timedelta
from functools import partial
from threading import Thread

from aqt import mw
from aqt.qt import *
from aqt.deckbrowser import DeckBrowser
from aqt.reviewer import Reviewer
from aqt.overview import Overview
from anki.hooks import addHook, wrap

from anki_killstreaks.config import local_conf
from anki_killstreaks.controllers import ReviewingController, build_on_answer_wrapper
from anki_killstreaks.persistence import migrate_database
from anki_killstreaks.streaks import InitialStreakState, HALO_MULTIKILL_STATES, \
    HALO_KILLING_SPREE_STATES, Acheivement, Store
from anki_killstreaks.views import MedalsOverviewJS


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

    reviewing_controller = ReviewingController(
        store=store,
        acheivements=[],
        show_acheivements=show_tool_tip_if_medals,
    )

    migrate_database()

    Reviewer._answerCard = wrap(
        Reviewer._answerCard,
        partial(build_on_answer_wrapper, on_answer=reviewing_controller.on_answer),
        'before',
    )

    addHook("showQuestion", reviewing_controller.on_show_question)
    addHook("showAnswer", reviewing_controller.on_show_answer)

    DeckBrowser.refresh = wrap(
        old=DeckBrowser.refresh,
        new=partial(
            inject_medals_with_js,
            acheivements=reviewing_controller.acheivements,
        ),
        pos="after"
    )
    DeckBrowser.show = wrap(
        old=DeckBrowser.show,
        new=partial(
            inject_medals_with_js,
            acheivements=reviewing_controller.acheivements,
        ),
        pos="after"
    )
    Overview.refresh = wrap(
        old=Overview.refresh,
        new=partial(
            inject_medals_with_js,
            acheivements=reviewing_controller.acheivements,
        ),
        pos="after"
    )


def show_tool_tip_if_medals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


def inject_medals_with_js(self: Overview, acheivements):
    def compute_then_inject():
        self.mw.web.eval(MedalsOverviewJS(acheivements=acheivements))

    Thread(target=compute_then_inject).start()


main()
