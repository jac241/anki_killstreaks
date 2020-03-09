"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""
import itertools
from unittest.mock import Mock

import pytest
from .test_streaks import question_shown_state

from anki_killstreaks.controllers import ReviewingController, AllMedalsAchievedNotifier
from anki_killstreaks.persistence import AchievementsRepository
from anki_killstreaks.streaks import Store


@pytest.fixture
def reviewing_controller(store, achievements_repo):
    return ReviewingController(
        store=store,
        show_achievements=Mock(),
        achievements_repo=achievements_repo
    )

@pytest.fixture
def achievements_repo(db_connection):
    return AchievementsRepository(db_connection=db_connection)


@pytest.fixture
def store(question_shown_state):
    return Store(
        state_machines=[
            question_shown_state,
        ]
    )


def test_ReviewingController_on_answer_should_update_store(reviewing_controller):
    initial_store = reviewing_controller.store

    reviewing_controller.on_answer(ease=3, deck_id=0)

    assert type(reviewing_controller.store) == type(initial_store)
    assert reviewing_controller.store != initial_store


def test_ReviewingController_on_answer_should_store_earned_achievements(reviewing_controller):
    reviewing_controller.achievements = []

    reviewing_controller.on_answer(ease=3, deck_id=0)

    assert len(reviewing_controller.achievements_repo.all()) == 1


def test_ReviewingController_on_answer_should_show_achievements_with_earned_medals(reviewing_controller):
    reviewing_controller.on_answer(ease=3, deck_id=0)

    reviewing_controller.show_achievements.assert_called_once()


def test_ReviewingController_on_answer_should_not_have_no_achievements_if_card_does_not_pass(reviewing_controller):
    reviewing_controller.on_answer(ease=1, deck_id=0)

    assert len(reviewing_controller.achievements_repo.all()) == 0


def test_ReviewingController_on_show_question_should_update_store(reviewing_controller):
    initial_store = reviewing_controller.store

    reviewing_controller.on_show_question()

    assert type(reviewing_controller.store) == type(initial_store)
    assert reviewing_controller.store != initial_store


def test_ReviewingController_on_show_answer_should_update_store(reviewing_controller):
    initial_store = reviewing_controller.store

    reviewing_controller.on_show_answer()

    assert type(reviewing_controller.store) == type(initial_store)
    assert reviewing_controller.store != initial_store


def test_ReviewingController_all_displayable_medals_delegates_to_store(reviewing_controller):
    assert reviewing_controller.all_displayable_medals == reviewing_controller.store.all_displayable_medals


def test_AllMedalsAcheivedNotifier_should_call_callback_when_all_medals_acheived(reviewing_controller):
    flag = False
    def notify():
        nonlocal flag
        flag = True

    notifier = AllMedalsAchievedNotifier(
        controller=reviewing_controller,
        remaining_medals=reviewing_controller.all_displayable_medals,
        notify=notify
    )

    all_medals = list(
        itertools.chain.from_iterable(
            m.states
            for m
            in reviewing_controller.store.state_machines
        )
    )

    for _ in all_medals:
        notifier.on_answer(ease=4, deck_id=0)

    assert flag == True
