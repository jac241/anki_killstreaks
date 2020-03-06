"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from datetime import datetime, timedelta
import itertools
from os.path import join, dirname

from anki_killstreaks._vendor import attr


DEFAULT_GAME_ID = 'halo_3'


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
    is_displayable_medal = False
    num_states_to_advance_if_on_streak = 1
    rank = 0


class MultikillFirstAnswerState(MultikillMixin):
    is_displayable_medal = False
    num_states_to_advance_if_on_streak = 1
    rank = 1


class MultikillMedalState(MultikillMixin):
    is_displayable_medal = True
    num_states_to_advance_if_on_streak = 1

    def __init__(self, name, medal_image, rank):
        self.name = name
        self.medal_image = medal_image
        self.rank = rank


class EndState(MultikillMixin):
    is_displayable_medal = False
    num_states_to_advance_if_on_streak = 0

    def __init__(self, rank):
        self.rank = rank

class KillingSpreeNoMedalState(KillingSpreeMixin):
    is_displayable_medal = False
    num_states_to_advance_if_on_streak = 1

    def __init__(self, rank):
        self.rank = rank


class KillingSpreeMedalState(KillingSpreeMixin):
    is_displayable_medal = True
    num_states_to_advance_if_on_streak = 1

    def __init__(self, name, medal_image, rank):
        self.name = name
        self.medal_image = medal_image
        self.rank = rank


class KillingSpreeEndState(KillingSpreeMixin):
    is_displayable_medal = False
    num_states_to_advance_if_on_streak = 0

    def __init__(self, rank):
        self.rank = rank


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


def did_card_pass(answer, again_answer=1):
    return answer > again_answer


class Store:
    def __init__(self, state_machines):
        self.state_machines = state_machines

    def on_show_question(self):
        return self.__class__(
            state_machines = [
                m.on_show_question()
                for m
                in self.state_machines
            ]
        )

    def on_show_answer(self):
        return self.__class__(
            state_machines=[
                m.on_show_answer()
                for m
                in self.state_machines
            ]
        )

    def on_answer(self, card_did_pass):
        return self.__class__(
            state_machines=[
                m.on_answer(card_did_pass=card_did_pass)
                for m
                in self.state_machines
            ]
        )

    @property
    def displayable_medals(self):
        return [
            m.current_medal_state
            for m
            in self.state_machines
            if m.current_medal_state.is_displayable_medal
        ]



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

    def on_show_question(self):
        return QuestionShownState(
            states=self._states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index
        )

    def on_show_answer(self):
        return AnswerShownState(
            states=self._states,
            question_shown_at=self._question_shown_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index
        )

    def on_answer(self, card_did_pass):
        answer_state = AnswerShownState(
            states=self._states,
            question_shown_at=self._question_shown_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index
        )

        return answer_state.on_answer(card_did_pass)


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

    def on_answer(self, card_did_pass):
        if (
            self._advancement_requirements_met(
                card_did_pass,
                self._answer_shown_at
            )
        ):
            return self._advanced_state_machine()
        elif card_did_pass:
            # want this one to count for first kill in new streak
            return self._reset_state_machine(new_index=1)
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
        card_did_pass,
        question_answered_at
    ):
        requirements_for_current_state_met = self.current_medal_state.requirements_met(
            question_shown_at=self._question_shown_at,
            question_answered_at=question_answered_at,
            interval_s=self._interval_s
        )

        return card_did_pass and requirements_for_current_state_met

    def _advanced_state_machine(self):
        return QuestionShownState(
            states=self._states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index + self.current_medal_state.num_states_to_advance_if_on_streak
        )

    def _reset_state_machine(self, new_index=0):
        return QuestionShownState(
            states=self._states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=new_index
        )

    @property
    def current_medal_state(self):
        return self._states[self._current_streak_index]


images_dir = join(dirname(__file__), 'images')


def image_path(filename):
    return join(images_dir, filename)


@attr.s(frozen=True)
class NewAchievement:
    medal = attr.ib()
    deck_id = attr.ib()

    @property
    def medal_name(self):
        return self.medal.name

    @property
    def medal_img_src(self):
        return self.medal.medal_image


HALO_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillFirstAnswerState(),
    MultikillMedalState(
        medal_image=image_path('Doublekill_Medal.webp.png'),
        name='Double Kill',
        rank=2
    ),
    MultikillMedalState(
        medal_image=image_path('Triplekill_Medal.webp.png'),
        name='Triple Kill',
        rank=3
    ),
    MultikillMedalState(
        medal_image=image_path('Overkill_Medal.png'),
        name='Overkill',
        rank=4
    ),
    MultikillMedalState(
        medal_image=image_path('Killtacular_Medal.webp.png'),
        name='Killtacular',
        rank=5
    ),
    MultikillMedalState(
        medal_image=image_path('Killtrocity_Medal.webp.png'),
        name='Killtrocity',
        rank=6
    ),
    MultikillMedalState(
        medal_image=image_path('Killimanjaro_Medal.webp.png'),
        name='Killimanjaro',
        rank=7
    ),
    MultikillMedalState(
        medal_image=image_path('Killtastrophe_Medal.webp.png'),
        name='Killtastrophe',
        rank=8
    ),
    MultikillMedalState(
        medal_image=image_path('Killpocalypse_Medal.webp.png'),
        name='Killpocalypse',
        rank=9
    ),
    MultikillMedalState(
        medal_image=image_path('Killionaire_Medal.webp.png'),
        name='Killionaire',
        rank=10
    ),
    EndState(rank=11),
]

HALO_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        medal_image=image_path('Killing_Spree_Medal.png'),
        name='Killing Spree',
        rank=5
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        medal_image=image_path('Killing_Frenzy_Medal.webp.png'),
        name='Killing Frenzy',
        rank=10
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        medal_image=image_path('Running_Riot_Medal.webp.png'),
        name='Running Riot',
        rank=15
    ),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    KillingSpreeMedalState(
        medal_image=image_path('Rampage_Medal.webp.png'),
        name='Rampage',
        rank=20
    ),
    KillingSpreeNoMedalState(rank=21),
    KillingSpreeNoMedalState(rank=22),
    KillingSpreeNoMedalState(rank=23),
    KillingSpreeNoMedalState(rank=24),
    KillingSpreeMedalState(
        medal_image=image_path('Untouchable_Medal.webp.png'),
        name='Untouchable',
        rank=25
    ),
    KillingSpreeNoMedalState(rank=26),
    KillingSpreeNoMedalState(rank=27),
    KillingSpreeNoMedalState(rank=28),
    KillingSpreeNoMedalState(rank=29),
    KillingSpreeMedalState(
        medal_image=image_path('Invincible_Medal.webp.png'),
        name='Invincible',
        rank=30
    ),
    KillingSpreeNoMedalState(rank=31),
    KillingSpreeNoMedalState(rank=32),
    KillingSpreeNoMedalState(rank=33),
    KillingSpreeNoMedalState(rank=34),
    KillingSpreeNoMedalState(rank=35),
    KillingSpreeNoMedalState(rank=36),
    KillingSpreeNoMedalState(rank=37),
    KillingSpreeNoMedalState(rank=38),
    KillingSpreeNoMedalState(rank=39),
    KillingSpreeNoMedalState(rank=40),
    KillingSpreeNoMedalState(rank=41),
    KillingSpreeNoMedalState(rank=42),
    KillingSpreeNoMedalState(rank=43),
    KillingSpreeNoMedalState(rank=44),
    KillingSpreeNoMedalState(rank=45),
    KillingSpreeNoMedalState(rank=46),
    KillingSpreeNoMedalState(rank=47),
    KillingSpreeNoMedalState(rank=48),
    KillingSpreeNoMedalState(rank=49),
    KillingSpreeMedalState(
        medal_image=image_path('Perfection_Medal.webp.png'),
        name='Perfection',
        rank=50
    ),
    KillingSpreeEndState(rank=51),
]

def get_all_displayable_medals():
    all_medals = itertools.chain(
        HALO_MULTIKILL_STATES,
        HALO_KILLING_SPREE_STATES,
    )
    return filter(
        lambda m: m.is_displayable_medal,
        all_medals
    )

