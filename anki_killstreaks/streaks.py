from datetime import datetime, timedelta

class MultikillMixin:
    def requirements_met(
        self,
        question_shown_at,
        question_answered_at,
        interval_s,
        min_interval_s=0
    ):
        delta = question_answered_at - question_shown_at
        return (
            delta >= timedelta(seconds=min_interval_s) and
            delta < timedelta(seconds=interval_s)
        )


class MultikillStartingState(MultikillMixin):
    def __init__(self):
        self.is_displayable_medal = False
        self.num_states_to_advance_if_on_streak = 1

class MultikillFirstAnswerState(MultikillMixin):
    def __init__(self):
        self.is_displayable_medal = False
        self.num_states_to_advance_if_on_streak = 1


class MultikillMedalState(MultikillMixin):
    def __init__(self, name, medal_image):
        self.name = name
        self.medal_image = medal_image
        self.is_displayable_medal = True
        self.num_states_to_advance_if_on_streak = 1


class EndState(MultikillMixin):
    def __init__(self):
        self.is_displayable_medal = False
        self.num_states_to_advance_if_on_streak = 0


class KillingSpreeMixin:
    def requirements_met(
        self,
        question_shown_at,
        question_answered_at,
        interval_s,
        min_interval_s=0
    ):
        delta = question_answered_at - question_shown_at
        return delta >= timedelta(seconds=min_interval_s)


class KillingSpreeNoMedalState(KillingSpreeMixin):
    def __init__(self):
        self.is_displayable_medal = False
        self.num_states_to_advance_if_on_streak = 1


class KillingSpreeMedalState(KillingSpreeMixin):
    def __init__(self, name, medal_image):
        self.name = name
        self.medal_image = medal_image
        self.is_displayable_medal = True
        self.num_states_to_advance_if_on_streak = 1


class KillingSpreeEndState(KillingSpreeMixin):
    def __init__(self):
        self.is_displayable_medal = False
        self.num_states_to_advance_if_on_streak = 0


class StreakStateMachine:
    def __init__(
        self,
        states,
        question_shown_at,
        interval_s,
        current_streak_index
    ):
        self._states = states
        self._question_shown_at = question_shown_at
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index

    def on_answer(self, answer_was_good_or_easy, question_answered_at):
        if (
            self._advancement_requirements_met(
                answer_was_good_or_easy,
                question_answered_at
            )
        ):
            return self._advanced_state_machine()
        else:
            return self._reset_state_machine()

    def on_show_question(self):
        return StreakStateMachine(
            states=self._states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index
        )

    def _advancement_requirements_met(
        self,
        answer_was_good_or_easy,
        question_answered_at
    ):
        requirements_for_current_state_met = self.current_medal_state.requirements_met(
            question_shown_at=self._question_shown_at,
            question_answered_at=question_answered_at,
            interval_s=self._interval_s
        )

        return answer_was_good_or_easy and requirements_for_current_state_met


    @property
    def current_medal_state(self):
        return self._states[self._current_streak_index]

    def _advanced_state_machine(self):
        return PausedStreakStateMachine(
            states=self._states,
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index + self.current_medal_state.num_states_to_advance_if_on_streak
        )

    def _reset_state_machine(self):
        return PausedStreakStateMachine(
            states=self._states,
            interval_s=self._interval_s,
            current_streak_index=0
        )

class PausedStreakStateMachine:
    def __init__(self, states, interval_s=8, current_streak_index=0):
        self._states = states
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index

    def on_show_question(self):
        return StreakStateMachine(
            states=self._states,
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
            question_shown_at=datetime.now()
        )

    @property
    def current_medal_state(self):
        return self._states[self._current_streak_index]

HALO_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillFirstAnswerState(),
    MultikillMedalState(medal_image=None, name='Double Kill'),
    MultikillMedalState(medal_image=None, name='Triple Kill'),
    MultikillMedalState(medal_image=None, name='Overkill'),
    MultikillMedalState(medal_image=None, name='Killtacular'),
    MultikillMedalState(medal_image=None, name='Killtrocity'),
    MultikillMedalState(medal_image=None, name='Killimanjaro'),
    MultikillMedalState(medal_image=None, name='Killtastrophe'),
    MultikillMedalState(medal_image=None, name='Killpocalypse'),
    MultikillMedalState(medal_image=None, name='Killionaire'),
    EndState(),
]

HALO_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(medal_image=None, name='Killing Spree'),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(medal_image=None, name='Killing Frenzy'),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(medal_image=None, name='Running Riot'),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(medal_image=None, name='Rampage'),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(medal_image=None, name='Untouchable'),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(medal_image=None, name='Invincible'),
    KillingSpreeEndState(),
]
