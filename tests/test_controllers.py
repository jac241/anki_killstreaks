"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""
from unittest.mock import Mock

import pytest
from tests.test_streaks import question_shown_state

from anki_killstreaks.controllers import ReviewingController
from anki_killstreaks.persistence import AcheivementsRepository
from anki_killstreaks.streaks import Store


@pytest.fixture
def reviewing_controller(store, acheivements_repo):
    return ReviewingController(
        store=store,
        show_acheivements=Mock(),
        acheivements_repo=acheivements_repo
    )

@pytest.fixture
def acheivements_repo(db_connection):
    return AcheivementsRepository(db_connection=db_connection)


@pytest.fixture
def store(question_shown_state):
    return Store(
        state_machines=[
            question_shown_state,
        ]
    )


def test_ReviewingController_on_answer_should_update_store(reviewing_controller):
    initial_store = reviewing_controller.store

    reviewing_controller.on_answer(3)

    assert type(reviewing_controller.store) == type(initial_store)
    assert reviewing_controller.store != initial_store


def test_ReviewingController_on_answer_should_store_earned_acheivements(reviewing_controller):
    reviewing_controller.acheivements = []

    reviewing_controller.on_answer(3)

    assert len(reviewing_controller.acheivements_repo.all()) == 1


def test_ReviewingController_on_answer_should_show_acheivements_with_earned_medals(reviewing_controller):
    reviewing_controller.on_answer(4)

    reviewing_controller.show_acheivements.assert_called_once()


def test_ReviewingController_on_answer_should_not_have_no_acheivements_if_card_does_not_pass(reviewing_controller):
    reviewing_controller.on_answer(1)

    assert len(reviewing_controller.acheivements_repo.all()) == 0


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
