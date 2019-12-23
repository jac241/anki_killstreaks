from datetime import datetime, timedelta
from os.path import join, dirname

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


# first just needs to be after minimum time
class MultikillStartingState(KillingSpreeMixin):
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


class InitialStreakState:
    def __init__(self, states, interval_s=8, current_streak_index=0):
        self._states = states
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index

    def on_show_question(self):
        return QuestionShownState(
            states=self._states,
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
            question_shown_at=datetime.now()
        )

    @property
    def current_medal_state(self):
        return self._states[self._current_streak_index]


class QuestionShownState:
    def __init__(
        self,
        states,
        question_shown_at,
        interval_s=8,
        current_streak_index=0
    ):
        self._states = states
        self._question_shown_at = question_shown_at
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index


    def on_show_answer(self):
        return AnswerShownState(
            states=self._states,
            question_shown_at=self._question_shown_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index
        )

    def on_show_question(self):
        return QuestionShownState(
            states=self._states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index
        )

    @property
    def current_medal_state(self):
        return self._states[self._current_streak_index]


class AnswerShownState:
    def __init__(
        self,
        states,
        question_shown_at,
        answer_shown_at,
        interval_s,
        current_streak_index
    ):
        self._states = states
        self._question_shown_at=question_shown_at
        self._answer_shown_at=answer_shown_at
        self._interval_s=interval_s
        self._current_streak_index=current_streak_index

    def on_answer(self, answer_was_good_or_easy):
        if (
            self._advancement_requirements_met(
                answer_was_good_or_easy,
                self._answer_shown_at
            )
        ):
            return self._advanced_state_machine()
        else:
            return self._reset_state_machine()

    def on_show_question(self):
        return QuestionShownState(
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

    def _advanced_state_machine(self):
        return QuestionShownState(
            states=self._states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index + self.current_medal_state.num_states_to_advance_if_on_streak
        )

    def _reset_state_machine(self):
        return QuestionShownState(
            states=self._states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=0
        )

    @property
    def current_medal_state(self):
        return self._states[self._current_streak_index]


images_dir = join(dirname(__file__), 'images')


def image_path(filename):
    return join(images_dir, filename)


HALO_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillFirstAnswerState(),
    MultikillMedalState(
        medal_image=image_path('Doublekill_Medal.webp.png'),
        name='Double Kill'
    ),
    MultikillMedalState(
        medal_image=image_path('Triplekill_Medal.webp.png'),
        name='Triple Kill'
    ),
    MultikillMedalState(
        medal_image=image_path('Overkill_Medal.png'),
        name='Overkill'
    ),
    MultikillMedalState(
        medal_image=image_path('Killtacular_Medal.webp.png'),
        name='Killtacular'
    ),
    MultikillMedalState(
        medal_image=image_path('Killtrocity_Medal.webp.png'),
        name='Killtrocity'
    ),
    MultikillMedalState(
        medal_image=image_path('Killimanjaro_Medal.webp.png'),
        name='Killimanjaro'
    ),
    MultikillMedalState(
        medal_image=image_path('Killtastrophe_Medal.webp.png'),
        name='Killtastrophe'
    ),
    MultikillMedalState(
        medal_image=image_path('Killpocalypse_Medal.webp.png'),
        name='Killpocalypse'
    ),
    MultikillMedalState(
        medal_image=image_path('Killionaire_Medal.webp.png'),
        name='Killionaire'
    ),
    EndState(),
]

HALO_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(
        medal_image=image_path('Killing_Spree_Medal.png'),
        name='Killing Spree'
    ),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(
        medal_image=image_path('Killing_Frenzy_Medal.webp.png'),
        name='Killing Frenzy'
    ),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(
        medal_image=image_path('Running_Riot_Medal.webp.png'),
        name='Running Riot'
    ),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(
        medal_image=image_path('Rampage_Medal.webp.png'),
        name='Rampage'
    ),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(
        medal_image=image_path('Untouchable_Medal.webp.png'),
        name='Untouchable'
    ),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeNoMedalState(),
    KillingSpreeMedalState(
        medal_image=image_path('Invincible_Medal.webp.png'),
        name='Invincible'
    ),
    KillingSpreeEndState(),
]
