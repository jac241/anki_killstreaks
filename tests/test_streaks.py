"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from datetime import datetime

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

    assert machine._question_shown_at < result._question_shown_at

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
    new_q_machine = answer_shown_machine.on_answer(answer_was_good_or_easy=True)

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
    new_q_state = answer_shown_state.on_answer(answer_was_good_or_easy=False)

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

    assert question_shown_state._question_shown_at > answer_shown_state._question_shown_at
