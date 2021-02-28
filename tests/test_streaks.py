"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from datetime import datetime
from functools import partial
from pathlib import Path

import pytest

from anki_killstreaks import addons
from anki_killstreaks.streaks import *


@pytest.fixture
def question_shown_state():
    return QuestionShownState(
        states=[
            MultikillStartingState(),
            MultikillMedalState(
                id_='Double Kill',
                name='Double Kill',
                medal_image=None,
                rank=1,
                game_id='halo_3'
            ),
            KillingSpreeEndState(rank=2)
        ],
        question_shown_at=datetime.now(),
    )


@pytest.fixture
def answer_shown_state():
    return AnswerShownState(
        states=[
            MultikillStartingState(),
            MultikillMedalState(
                id_='Double Kill',
                name='Double Kill',
                medal_image=None,
                rank=1,
                game_id='halo_3'
            ),
            KillingSpreeEndState(rank=2)
        ],
        question_shown_at=datetime.now(),
        answer_shown_at=datetime.now() + timedelta(seconds=1),
        interval_s=8,
        current_streak_index=0
    )


def test_states_requirements_met_should_return_true_if_within_interval():
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        EndState(
            medal_state=MultikillMedalState(id_='t', name='test', medal_image=None, rank=2, game_id='tg'),
            index_to_return_to=1
        )
    ]

    for state in states:
        assert state.requirements_met(
            question_shown_at=datetime.now(),
            question_answered_at=datetime.now(),
            interval_s=5,
            min_interval_s=0
        )

def test_InitialStreakState_on_show_question_should_return_a_QuestionShownState():
    initial_state = InitialStreakState(
        states=[],
        interval_s=10,
        current_streak_index=0
    )

    result = initial_state.on_show_question()
    assert result._interval_s == 10


def test_QuestionShownState_on_show_question_should_return_a_new_machine_with_question_show_at_set():
    machine = QuestionShownState(
        states=[],
        interval_s=10,
        current_streak_index=0,
        question_shown_at=datetime.now()
    )

    result = machine.on_show_question()

    assert machine._question_shown_at <= result._question_shown_at


def test_QuestionShownState_on_answer_should_advance():
    """
    This state occurs when pressing 3 or 4 when question shown,
    want to display medal if eligible
    """
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        EndState(
            medal_state=MultikillMedalState(id_='t', name='test', medal_image=None, rank=2, game_id='tg'),
            index_to_return_to=2
        ),
    ]

    machine = QuestionShownState(
        states=states,
        interval_s=10,
        current_streak_index=0,
        question_shown_at=datetime.now()
    )

    result = machine.on_answer(card_did_pass=True)
    return result.current_medal_state == states[1]


def test_QuestionShownState_on_answer_should_only_advance_if_right_hand_reviews_is_installed(test_support_dir):
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        EndState(
            medal_state=MultikillMedalState(id_='t', name='test', medal_image=None, rank=2, game_id='tg'),
            index_to_return_to=2
        ),
    ]
    machine_with_rhr = QuestionShownState(
        states=states,
        interval_s=10,
        current_streak_index=0,
        question_shown_at=datetime.now(),
        addon_is_installed_and_enabled=partial(
            addons.is_installed_and_enabled,
            addons_dir_path=Path(test_support_dir, "sample_addons_dir_with_right_hand_reviews")
        ),
    )

    result = machine_with_rhr.on_answer(card_did_pass=True)
    assert result.current_medal_state == states[1]

    machine_without_rhr = QuestionShownState(
        states=states,
        interval_s=10,
        current_streak_index=0,
        question_shown_at=datetime.now(),
        addon_is_installed_and_enabled=partial(
            addons.is_installed_and_enabled,
            addons_dir_path=Path(test_support_dir, "sample_addons_dir_without_right_hand_reviews")
        ),
    )

    result = machine_without_rhr.on_answer(card_did_pass=True)
    assert result == machine_without_rhr


def test_multikill_flow_should_work():
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        MultikillMedalState(
            id_='test',
            name='test',
            medal_image=None,
            rank=2,
            game_id='t',
        ),
    ]

    multikill_machine = QuestionShownState(
        states,
        question_shown_at=datetime.now(),
        interval_s=8,
        current_streak_index=0
    )

    question_shown_machine = multikill_machine.on_show_question()
    answer_shown_machine = question_shown_machine.on_show_answer()
    new_q_machine = answer_shown_machine.on_answer(card_did_pass=True)

    assert new_q_machine.current_medal_state == multikill_machine.states[1]


def test_multikill_should_restart_streak_automatically_if_all_medals_achieved():
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        MultikillMedalState(
            id_='test1',
            name='test1',
            medal_image=None,
            rank=2,
            game_id='t',
        ),
        EndState(
            medal_state=MultikillMedalState(
                id_='test2',
                name='test2',
                medal_image=None,
                rank=3,
                game_id='t',
            ),
            index_to_return_to=2,
        ),
    ]

    multikill_machine = QuestionShownState(
        states,
        question_shown_at=datetime.now(),
        interval_s=8,
        current_streak_index=3
    )

    new_state = multikill_machine.on_answer(card_did_pass=True)
    assert new_state.current_medal_state == states[2]



def test_multikill_should_reset_when_again_pressed():
    states = [
        MultikillStartingState(),
        MultikillMedalState(
            id_='test',
            name='test',
            medal_image=None,
            rank=2,
            game_id='t',
        ),
    ]

    question_shown_state = QuestionShownState(
        states,
        question_shown_at=datetime.now(),
        interval_s=8,
        current_streak_index=1,
    )

    answer_shown_state = question_shown_state.on_show_answer()
    new_q_state = answer_shown_state.on_answer(card_did_pass=False)

    assert new_q_state.current_medal_state == states[0]


def test_AnswerShownState_should_reset_to_QuestionShownState_when_recieves_on_show_question():
    """This can happen when card is buried with answer shown"""
    states = [
        MultikillStartingState(),
        MultikillMedalState(
            id_='test',
            name='test',
            medal_image=None,
            rank=2,
            game_id='t',
        ),
    ]

    answer_shown_state = AnswerShownState(
        states=states,
        question_shown_at=datetime.now(),
        answer_shown_at=datetime.now(),
        interval_s=8,
        current_streak_index=0
    )

    question_shown_state = answer_shown_state.on_show_question()

    assert question_shown_state._question_shown_at >= answer_shown_state._question_shown_at


def test_AnswerShownState_should_go_to_index_1_if_answer_was_correct_but_out_of_time_window():
    """This answer should still be eligible for a double kill"""
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        MultikillMedalState(
            id_='test',
            name='test',
            medal_image=None,
            rank=2,
            game_id='t',
        ),
    ]

    answer_shown_state = AnswerShownState(
        states=states,
        question_shown_at=datetime.now(),
        answer_shown_at=datetime.now() + timedelta(seconds=10),
        interval_s=8,
        current_streak_index=2
    )

    question_shown_state = answer_shown_state.on_answer(card_did_pass=True)
    assert question_shown_state.current_medal_state == states[1]

def test_AnswerShownState_should_just_repeat_if_on_answer_shown_called():
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        MultikillMedalState(
            id_='test',
            name='test',
            medal_image=None,
            rank=2,
            game_id='t',
        ),
    ]

    answer_shown_state = AnswerShownState(
        states=states,
        question_shown_at=datetime.now(),
        answer_shown_at=datetime.now() + timedelta(seconds=10),
        interval_s=8,
        current_streak_index=2
    )

    repeated_state = answer_shown_state.on_show_answer()
    assert repeated_state == answer_shown_state


def test_should_be_able_to_get_perfection_medal_after_50_kills():
    state = QuestionShownState(
        states=HALO_KILLING_SPREE_STATES,
        question_shown_at=datetime.now(),
        interval_s=8,
        current_streak_index=0,
    )

    for i in range(50):
        state = state.on_answer(card_did_pass=True)
    assert state.current_medal_state.name == 'Perfection'


def test_killing_spree_states_should_return_to_index_one_after_all_medals_achieved():
    for states in [HALO_KILLING_SPREE_STATES, HALO_5_KILLING_SPREE_STATES, MW2_KILLSTREAK_STATES]:
        state = QuestionShownState(
            states=states,
            question_shown_at=datetime.now(),
            interval_s=8,
            current_streak_index=len(states) - 1,
        )

        state = state.on_answer(card_did_pass=True)
        assert state.current_medal_state == states[1]

def test_multikill_states_should_return_to_index_two_after_all_medals_achieved():
    for states in [HALO_5_MULTIKILL_STATES, HALO_MULTIKILL_STATES]:
        state = QuestionShownState(
            states=states,
            question_shown_at=datetime.now(),
            interval_s=8,
            current_streak_index=len(states) - 1,
        )

        state = state.on_answer(card_did_pass=True)
        assert state.current_medal_state == states[2]


def test_Store_on_show_question_should_delegate_to_composing_states(answer_shown_state):
    store = Store(
        state_machines=[
            answer_shown_state
        ]
    )

    new_store = store.on_show_question()

    assert new_store.state_machines[0] is not answer_shown_state


def test_Store_on_show_answer_should_delegate_to_composing_states(question_shown_state):
    store = Store(
        state_machines=[
            question_shown_state
        ]
    )

    new_store = store.on_show_answer()

    assert new_store.state_machines[0] is not question_shown_state


def test_Store_on_answer_should_delegate_to_composing_states(answer_shown_state):
    initial_state = answer_shown_state.current_medal_state

    store = Store(
        state_machines=[
            answer_shown_state
        ]
    )

    new_store = store.on_answer(card_did_pass=True)
    assert new_store.state_machines[0].current_medal_state is not initial_state


def test_Store_displayable_medals_should_return_any_displayable_medals_earned(answer_shown_state):
    machine_with_medal = answer_shown_state.on_answer(card_did_pass=True)
    machine_without_medal = answer_shown_state

    store = Store(
        state_machines=[
            machine_with_medal,
            machine_without_medal
        ]
    )

    medals = store.current_displayable_medals
    assert len(medals) == 1
    assert medals[0] == machine_with_medal.current_medal_state


def test_Store_all_displayable_medals_should_return_all_set_of_possible_displayable_medals_from_machines(answer_shown_state):
    store = Store(
        state_machines=[
            answer_shown_state,
            answer_shown_state,
        ]
    )
    all_displayable_medals = [
        m
        for m in answer_shown_state.states
        if m.is_displayable_medal
    ]

    result = store.all_displayable_medals
    assert len(result) == len(all_displayable_medals)
