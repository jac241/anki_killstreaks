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

def test_PausedStreakStateMachine_on_show_question_should_return_a_StreakStateMachine():
    paused = PausedStreakStateMachine(states=[], interval_s=10)
    result = paused.on_show_question()
    assert result._interval_s == 10


def test_StreakStateMachine_on_show_question_should_return_a_new_machine_with_question_show_at_set():
    machine = StreakStateMachine(
        states=[],
        interval_s=10,
        current_streak_index=0,
        question_shown_at=datetime.now()
    )

    result = machine.on_show_question()

    assert machine._question_shown_at < result._question_shown_at
