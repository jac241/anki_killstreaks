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

from aqt import mw
from aqt.qt import *
from aqt.deckbrowser import DeckBrowser
from aqt.reviewer import Reviewer
from aqt.overview import Overview
from anki.hooks import addHook, wrap

from .config import local_conf
from .streaks import InitialStreakState, HALO_MULTIKILL_STATES, \
    HALO_KILLING_SPREE_STATES, Acheivement, Store
from .views import MedalsOverviewJS


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
acheivements=[]


def on_card_answered(self, ease):
    global store
    store.on_answer(card_did_pass=did_card_pass(ease))

    acheivements.extend(
        Acheivement(medal=medal)
        for medal
        in store.displayable_medals
    )

    show_tool_tip_if_medals(store.displayable_medals)


def show_tool_tip_if_medals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


def did_card_pass(answer, again_answer=1):
    return answer > again_answer


def on_show_question():
    global store
    store.on_show_question()


def on_show_answer():
    global store
    store.on_show_answer()


def inject_medals_with_js(self: Overview, acheivements):
    self.mw.web.eval(MedalsOverviewJS(acheivements=acheivements))


# before required b/c Reviewer._answerCard triggers the showQuestion hook.
Reviewer._answerCard = wrap(Reviewer._answerCard, on_card_answered, 'before')
addHook("showQuestion", on_show_question)
addHook("showAnswer", on_show_answer)
DeckBrowser.refresh = wrap(
    old=DeckBrowser.refresh,
    new=partial(inject_medals_with_js, acheivements=acheivements),
    pos="after"
)
DeckBrowser.show = wrap(
    old=DeckBrowser.show,
    new=partial(inject_medals_with_js, acheivements=acheivements),
    pos="after"
)
Overview.refresh = wrap(
    old=Overview.refresh,
    new=partial(inject_medals_with_js, acheivements=acheivements),
    pos="after"
)
