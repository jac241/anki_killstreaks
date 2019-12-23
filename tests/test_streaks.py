from datetime import datetime

from anki_killstreaks.streaks import *

def test_states_requirements_met_should_return_true_if_within_interval():
    states = [
        StartingState(),
        FirstAnswerState(),
        MedalState(name='test', medal_image=None),
        EndState()
    ]

    for state in states:
        assert state.requirements_met(
            question_shown_at=datetime.now(),
            question_answered_at=datetime.now(),
            interval_s=5
        )

def test_PausedStreakStateMachine_on_show_question_should_return_a_StreakStateMachine():
    paused = PausedStreakStateMachine(states=[], interval_s=10)
    result = paused.on_show_question()
    assert result._interval_s == 10

