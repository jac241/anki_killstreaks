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

from aqt import mw
from aqt.qt import *
from aqt.reviewer import Reviewer
from anki.hooks import addHook, wrap

from .config import local_conf
from .streaks import InitialStreakState, HALO_MULTIKILL_STATES, HALO_KILLING_SPREE_STATES


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


_multikill_state_machine = InitialStreakState(states=HALO_MULTIKILL_STATES)
_killing_spree_state_machine = InitialStreakState(
    states=HALO_KILLING_SPREE_STATES,
    interval_s=60
)


def onCardAnswered(self, ease):
    global _multikill_state_machine
    global _killing_spree_state_machine

    answer_was_good_or_easy = wasAnswerGoodOrEasy(
        defaultEase=self._defaultEase(),
        answer=ease
    )

    _multikill_state_machine = _multikill_state_machine.on_answer(
        answer_was_good_or_easy=answer_was_good_or_easy
    )

    _killing_spree_state_machine = _killing_spree_state_machine.on_answer(
        answer_was_good_or_easy=answer_was_good_or_easy
    )

    displayable_medals = []

    if _multikill_state_machine.current_medal_state.is_displayable_medal:
        displayable_medals.append(_multikill_state_machine.current_medal_state)

    if _killing_spree_state_machine.current_medal_state.is_displayable_medal:
        displayable_medals.append(_killing_spree_state_machine.current_medal_state)

    showToolTipIfMedals(displayable_medals)


def showToolTipIfMedals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


def wasAnswerGoodOrEasy(defaultEase, answer):
    return answer >= defaultEase


def on_show_question():
    global _multikill_state_machine
    global _killing_spree_state_machine
    _multikill_state_machine = _multikill_state_machine.on_show_question()
    _killing_spree_state_machine = _killing_spree_state_machine.on_show_question()


def on_show_answer():
    global _multikill_state_machine
    global _killing_spree_state_machine
    _multikill_state_machine = _multikill_state_machine.on_show_answer()
    _killing_spree_state_machine = _killing_spree_state_machine.on_show_answer()


# before required b/c Reviewer._answerCard triggers the showQuestion hook.
Reviewer._answerCard = wrap(Reviewer._answerCard, onCardAnswered, 'before')
addHook("showQuestion", on_show_question)
addHook("showAnswer", on_show_answer)
