"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from datetime import datetime
import pytest

from anki_killstreaks.streaks import *

def test_states_requirements_met_should_return_true_if_within_interval():
    states = [
        MultikillStartingState(),
        MultikillFirstAnswerState(),
        MultikillMedalState(name='test', medal_image=None),
        EndState()
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
        MultikillMedalState(name='test', medal_image=None),
        EndState()
    ]

    machine = QuestionShownState(
        states=states,
        interval_s=10,
        current_streak_index=0,
        question_shown_at=datetime.now()
    )

    result = machine.on_answer(card_did_pass=True)
    return result.current_medal_state == states[1]

def test_multikill_flow_should_work():
    states = [
        MultikillStartingState(),
        MultikillMedalState(name='test', medal_image=None),
        EndState()
    ]

    machine = QuestionShownState(
        states,
        question_shown_at=datetime.now(),
        interval_s=8,
        current_streak_index=0
    )

    question_shown_machine = machine.on_show_question()
    answer_shown_machine = question_shown_machine.on_show_answer()
    new_q_machine = answer_shown_machine.on_answer(card_did_pass=True)

    assert new_q_machine.current_medal_state == states[1]


def test_multikill_should_reset_when_again_pressed():
    states = [
        MultikillStartingState(),
        MultikillMedalState(name='test', medal_image=None),
        EndState()
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
        MultikillMedalState(name='test', medal_image=None),
        EndState()
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
        MultikillMedalState(name='test', medal_image=None),
        EndState()
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

@pytest.fixture
def question_shown_state():
    return QuestionShownState(
        states=[
            MultikillStartingState(),
            KillingSpreeMedalState(name='test', medal_image=None),
            KillingSpreeEndState()
        ],
        question_shown_at=datetime.now(),
    )


@pytest.fixture
def answer_shown_state():
    return AnswerShownState(
        states=[
            MultikillStartingState(),
            KillingSpreeMedalState(name='test', medal_image=None),
            KillingSpreeEndState()
        ],
        question_shown_at=datetime.now(),
        answer_shown_at=datetime.now() + timedelta(seconds=1),
        interval_s=8,
        current_streak_index=0
    )


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

    medals = store.displayable_medals
    assert len(medals) == 1
    assert medals[0] == machine_with_medal.current_medal_state
