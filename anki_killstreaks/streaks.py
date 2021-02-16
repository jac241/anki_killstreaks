"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from datetime import datetime, timedelta
import itertools
from os.path import join, dirname

from ._vendor import attr


DEFAULT_GAME_ID = "halo_3"
all_game_ids = ["halo_3", "mw2", "halo_5", "ca"]


class MultikillMixin:
    def requirements_met(
        self,
        question_shown_at,
        question_answered_at,
        interval_s,
        min_interval_s=0,
    ):
        delta = question_answered_at - question_shown_at
        return (
            timedelta(seconds=min_interval_s)
            <= delta
            < timedelta(seconds=interval_s)
        )


class KillingSpreeMixin:
    def requirements_met(
        self,
        question_shown_at,
        question_answered_at,
        interval_s,
        min_interval_s=0,
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


@attr.s(frozen=True)
class MultikillMedalState(MultikillMixin):
    is_displayable_medal = True
    num_states_to_advance_if_on_streak = 1

    id_ = attr.ib()
    name = attr.ib()
    medal_image = attr.ib()
    medal_sound = attr.ib()
    rank = attr.ib()
    game_id = attr.ib()
    _call = attr.ib(default=None)

    @property
    def call(self):
        return self._call if self._call else self.name


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


@attr.s(frozen=True)
class KillingSpreeMedalState(KillingSpreeMixin):
    is_displayable_medal = True
    num_states_to_advance_if_on_streak = 1

    id_ = attr.ib()
    name = attr.ib()
    medal_image = attr.ib()
    medal_sound = attr.ib()
    rank = attr.ib()
    game_id = attr.ib()
    _call = attr.ib(default=None)

    @property
    def call(self):
        return self._call if self._call else self.name


class KillingSpreeEndState(KillingSpreeMixin):
    is_displayable_medal = False
    num_states_to_advance_if_on_streak = 0

    def __init__(self, rank):
        self.rank = rank


class InitialStreakState:
    def __init__(self, states, interval_s=8, current_streak_index=0):
        self.states = states
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index
        # If you switch games while reviewing, need to have a time to start with
        self._initialized_at = datetime.now()

    def on_show_question(self):
        return QuestionShownState(
            states=self.states,
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
            question_shown_at=datetime.now(),
        )

    # For case of switching games while reviewing
    def on_show_answer(self):
        return AnswerShownState(
            states=self.states,
            question_shown_at=self._initialized_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

    def on_answer(self, card_did_pass):
        answer_state = AnswerShownState(
            states=self.states,
            question_shown_at=self._initialized_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

        return answer_state.on_answer(card_did_pass)

    @property
    def current_medal_state(self):
        return self.states[self._current_streak_index]


def did_card_pass(answer, again_answer=1):
    return answer > again_answer


class Store:
    def __init__(self, state_machines):
        self.state_machines = state_machines

    def on_show_question(self):
        return self.__class__(
            state_machines=[m.on_show_question() for m in self.state_machines]
        )

    def on_show_answer(self):
        return self.__class__(
            state_machines=[m.on_show_answer() for m in self.state_machines]
        )

    def on_answer(self, card_did_pass):
        return self.__class__(
            state_machines=[
                m.on_answer(card_did_pass=card_did_pass)
                for m in self.state_machines
            ]
        )

    @property
    def current_displayable_medals(self):
        return [
            m.current_medal_state
            for m in self.state_machines
            if m.current_medal_state.is_displayable_medal
        ]

    @property
    def all_displayable_medals(self):
        all_medals = itertools.chain.from_iterable(
            m.states for m in self.state_machines
        )

        return frozenset(
            medal for medal in all_medals if medal.is_displayable_medal
        )


class QuestionShownState:
    def __init__(
        self, states, question_shown_at, interval_s=8, current_streak_index=0
    ):
        self.states = states
        self._question_shown_at = question_shown_at
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index

    def on_show_question(self):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

    def on_show_answer(self):
        return AnswerShownState(
            states=self.states,
            question_shown_at=self._question_shown_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

    def on_answer(self, card_did_pass):
        answer_state = AnswerShownState(
            states=self.states,
            question_shown_at=self._question_shown_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

        return answer_state.on_answer(card_did_pass)

    @property
    def current_medal_state(self):
        return self.states[self._current_streak_index]


class AnswerShownState:
    def __init__(
        self,
        states,
        question_shown_at,
        answer_shown_at,
        interval_s,
        current_streak_index,
    ):
        self.states = states
        self._question_shown_at = question_shown_at
        self._answer_shown_at = answer_shown_at
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index

    def on_answer(self, card_did_pass):
        if self._advancement_requirements_met(
            card_did_pass, self._answer_shown_at
        ):
            return self._advanced_state_machine()
        elif card_did_pass:
            # want this one to count for first kill in new streak
            return self._reset_state_machine(new_index=1)
        else:
            return self._reset_state_machine()

    def on_show_question(self):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )


    def on_show_answer(self):
        """Can be triggered by edit field in review add-on"""
        return self


    def _advancement_requirements_met(
        self, card_did_pass, question_answered_at
    ):
        requirements_for_current_state_met = self.current_medal_state.requirements_met(
            question_shown_at=self._question_shown_at,
            question_answered_at=question_answered_at,
            interval_s=self._interval_s,
        )

        return card_did_pass and requirements_for_current_state_met

    def _advanced_state_machine(self):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index
            + self.current_medal_state.num_states_to_advance_if_on_streak,
        )

    def _reset_state_machine(self, new_index=0):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=new_index,
        )

    @property
    def current_medal_state(self):
        return self.states[self._current_streak_index]


images_dir = join(dirname(__file__), "images")
sounds_dir = join(dirname(__file__), "sounds")


def image_path(filename):
    return join(images_dir, filename)

def sound_path(filename):
    return join(sounds_dir, filename)


@attr.s(frozen=True)
class NewAchievement:
    medal = attr.ib()
    deck_id = attr.ib()

    @property
    def medal_id(self):
        return self.medal.id_

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
        id_="Double Kill",
        medal_image=image_path("Doublekill_Medal.webp.png"),
        medal_sound=sound_path("Double Kill.mp3"),
        name="Double Kill",
        game_id="halo_3",
        rank=2,
    ),
    MultikillMedalState(
        id_="Triple Kill",
        medal_image=image_path("Triplekill_Medal.webp.png"),
        medal_sound=sound_path("Triple Kill.mp3"),
        name="Triple Kill",
        game_id="halo_3",
        rank=3,
    ),
    MultikillMedalState(
        id_="Overkill",
        medal_image=image_path("Overkill_Medal.png"),
        medal_sound=sound_path("Overkill.mp3"),
        name="Overkill",
        game_id="halo_3",
        rank=4,
    ),
    MultikillMedalState(
        id_="Killtacular",
        medal_image=image_path("Killtacular_Medal.webp.png"),
        medal_sound=sound_path("Killtacular.mp3"),
        name="Killtacular",
        game_id="halo_3",
        rank=5,
    ),
    MultikillMedalState(
        id_="Killtrocity",
        medal_image=image_path("Killtrocity_Medal.webp.png"),
        medal_sound=sound_path("Killtrocity.mp3"),
        name="Killtrocity",
        game_id="halo_3",
        rank=6,
    ),
    MultikillMedalState(
        id_="Killimanjaro",
        medal_image=image_path("Killimanjaro_Medal.webp.png"),
        medal_sound=sound_path("Killimanjaro.mp3"),
        name="Killimanjaro",
        game_id="halo_3",
        rank=7,
    ),
    MultikillMedalState(
        id_="Killtastrophe",
        medal_image=image_path("Killtastrophe_Medal.webp.png"),
        medal_sound=sound_path("Killtastrophe.mp3"),
        name="Killtastrophe",
        game_id="halo_3",
        rank=8,
    ),
    MultikillMedalState(
        id_="Killpocalypse",
        medal_image=image_path("Killpocalypse_Medal.webp.png"),
        medal_sound=sound_path("Killpocalypse.mp3"),
        name="Killpocalypse",
        game_id="halo_3",
        rank=9,
    ),
    MultikillMedalState(
        id_="Killionaire",
        medal_image=image_path("Killionaire_Medal.webp.png"),
        medal_sound=sound_path("Killionaire.mp3"),
        name="Killionaire",
        game_id="halo_3",
        rank=10,
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
        id_="Killing Spree",
        medal_image=image_path("Killing_Spree_Medal.png"),
        medal_sound=sound_path("Killing Spree.mp3"),
        name="Killing Spree",
        game_id="halo_3",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="Killing Frenzy",
        medal_image=image_path("Killing_Frenzy_Medal.webp.png"),
        medal_sound=sound_path("Killing Frenzy.mp3"),
        name="Killing Frenzy",
        game_id="halo_3",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="Running Riot",
        medal_image=image_path("Running_Riot_Medal.webp.png"),
        medal_sound=sound_path("Running Riot.mp3"),
        name="Running Riot",
        game_id="halo_3",
        rank=15,
    ),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    KillingSpreeMedalState(
        id_="Rampage",
        medal_image=image_path("Rampage_Medal.webp.png"),
        medal_sound=sound_path("Rampage.mp3"),
        name="Rampage",
        game_id="halo_3",
        rank=20,
    ),
    KillingSpreeNoMedalState(rank=21),
    KillingSpreeNoMedalState(rank=22),
    KillingSpreeNoMedalState(rank=23),
    KillingSpreeNoMedalState(rank=24),
    KillingSpreeMedalState(
        id_="Untouchable",
        medal_image=image_path("Untouchable_Medal.webp.png"),
        medal_sound=sound_path("Untouchable.mp3"),
        name="Untouchable",
        game_id="halo_3",
        rank=25,
    ),
    KillingSpreeNoMedalState(rank=26),
    KillingSpreeNoMedalState(rank=27),
    KillingSpreeNoMedalState(rank=28),
    KillingSpreeNoMedalState(rank=29),
    KillingSpreeMedalState(
        id_="Invincible",
        medal_image=image_path("Invincible_Medal.webp.png"),
        medal_sound=sound_path("Invincible.mp3"),
        name="Invincible",
        game_id="halo_3",
        rank=30,
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
        id_="Perfection",
        medal_image=image_path("Perfection_Medal.webp.png"),
        medal_sound=sound_path("Perfection.mp3"),
        name="Perfection",
        game_id="halo_3",
        rank=50,
    ),
    KillingSpreeEndState(rank=51),
]

MW2_KILLSTREAK_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeMedalState(
        id_="mw2_uav",
        medal_image=image_path("mw2/uav.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_radar.wav"),
        name="UAV",
        game_id="mw2",
        call="UAV recon standing by",
        rank=3,
    ),
    KillingSpreeMedalState(
        id_="mw2_care_package",
        medal_image=image_path("mw2/care_package.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_carepackage.wav"),
        name="Care Package",
        game_id="mw2",
        call="Care package waiting for your mark",
        rank=4,
    ),
    KillingSpreeMedalState(
        id_="mw2_predator_missile",
        medal_image=image_path("mw2/predator_missile.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_hellfire.wav"),
        name="Predator Missile",
        game_id="mw2",
        call="Predator missile ready for launch",
        rank=5,
    ),
    KillingSpreeMedalState(
        id_="mw2_precision_airstrike",
        medal_image=image_path("mw2/precision_airstrike.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_jetstart.wav"),
        name="Precision Airstrike",
        game_id="mw2",
        call="Airstrike standing by",
        rank=6,
    ),
    KillingSpreeMedalState(
        id_="mw2_harrier_strike",
        medal_image=image_path("mw2/harrier_strike.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_harrierstrike.wav"),
        name="Harrier Strike",
        game_id="mw2",
        call="Harrier's waiting for your mark",
        rank=7,
    ),
    KillingSpreeMedalState(
        id_="mw2_emergency_airdrop",
        medal_image=image_path("mw2/emergency_airdrop.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_emergencyairdrop.wav"),
        name="Emergency Airdrop",
        game_id="mw2",
        call="Emergency airdrop, show us where you want it",
        rank=8,
    ),
    KillingSpreeMedalState(
        id_="mw2_pave_low",
        medal_image=image_path("mw2/pave_low.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_pavelow.wav"),
        name="Pave Low",
        game_id="mw2",
        call="Pave low ready for deployment",
        rank=9,
    ),
    KillingSpreeNoMedalState(rank=10),
    KillingSpreeMedalState(
        id_="mw2_chopper_gunner",
        medal_image=image_path("mw2/chopper_gunner.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_choppergunner.wav"),
        name="Chopper Gunner",
        game_id="mw2",
        call="Chopper ready for deployment",
        rank=11,
    ),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="mw2_emp",
        medal_image=image_path("mw2/emp.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_emp.wav"),
        name="EMP",
        game_id="mw2",
        call="EMP ready to go",
        rank=15,
    ),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    KillingSpreeNoMedalState(rank=20),
    KillingSpreeNoMedalState(rank=21),
    KillingSpreeNoMedalState(rank=22),
    KillingSpreeNoMedalState(rank=23),
    KillingSpreeNoMedalState(rank=24),
    KillingSpreeMedalState(
        id_="mw2_tactical_nuke",
        medal_image=image_path("mw2/tactical_nuke.webp.png"),
        medal_sound=sound_path("mw2/mp_killstrk_nuclearstrike.wav"),
        name="Tactical Nuke",
        game_id="mw2",
        call="Tactical nuke ready, turn the key",
        rank=25,
    ),
    KillingSpreeEndState(rank=26),
]

HALO_5_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillFirstAnswerState(),
    MultikillMedalState(
        id_="halo_5_double_kill",
        medal_image=image_path("halo_5/double_kill.png"),
        medal_sound=sound_path("halo_5/Double Kill.mp3"),
        name="Double Kill",
        game_id="halo_5",
        rank=2,
    ),
    MultikillMedalState(
        id_="halo_5_triple_Kill",
        medal_image=image_path("halo_5/triple_kill.png"),
        medal_sound=sound_path("halo_5/Triple Kill.mp3"),
        name="Triple Kill",
        game_id="halo_5",
        rank=3,
    ),
    MultikillMedalState(
        id_="halo_5_overkill",
        medal_image=image_path("halo_5/overkill.png"),
        medal_sound=sound_path("halo_5/Overkill.mp3"),
        name="Overkill",
        game_id="halo_5",
        rank=4,
    ),
    MultikillMedalState(
        id_="halo_5_killtacular",
        medal_image=image_path("halo_5/killtacular.png"),
        medal_sound=sound_path("halo_5/Killtacular.mp3"),
        name="Killtacular",
        game_id="halo_5",
        rank=5,
    ),
    MultikillMedalState(
        id_="halo_5_killtrocity",
        medal_image=image_path("halo_5/killtrocity.png"),
        medal_sound=sound_path("halo_5/Killtrocity.mp3"),
        name="Killtrocity",
        game_id="halo_5",
        rank=6,
    ),
    MultikillMedalState(
        id_="halo_5_killimanjaro",
        medal_image=image_path("halo_5/killimanjaro.png"),
        medal_sound=sound_path("halo_5/Killimanjaro.mp3"),
        name="Killimanjaro",
        game_id="halo_5",
        rank=7,
    ),
    MultikillMedalState(
        id_="halo_5_killtastrophe",
        medal_image=image_path("halo_5/killtastrophe.png"),
        medal_sound=sound_path("halo_5/Killtastrophe.mp3"),
        name="Killtastrophe",
        game_id="halo_5",
        rank=8,
    ),
    MultikillMedalState(
        id_="halo_5_killpocalypse",
        medal_image=image_path("halo_5/killpocalypse.png"),
        medal_sound=sound_path("halo_5/Killpocalypse.mp3"),
        name="Killpocalypse",
        game_id="halo_5",
        rank=9,
    ),
    MultikillMedalState(
        id_="halo_5_killionaire",
        medal_image=image_path("halo_5/killionaire.png"),
        medal_sound=sound_path("halo_5/Killionaire.mp3"),
        name="Killionaire",
        game_id="halo_5",
        rank=10,
    ),
    EndState(rank=11),
]

HALO_5_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="halo_5_killing_spree",
        medal_image=image_path("halo_5/killing_spree.png"),
        medal_sound=sound_path("halo_5/Killing Spree.mp3"),
        name="Killing Spree",
        game_id="halo_5",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="halo_5_killing_frenzy",
        medal_image=image_path("halo_5/killing_frenzy.png"),
        medal_sound=sound_path("halo_5/Killing Frenzy.mp3"),
        name="Killing Frenzy",
        game_id="halo_5",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="halo_5_running_riot",
        medal_image=image_path("halo_5/running_riot.png"),
        medal_sound=sound_path("halo_5/Running Riot.mp3"),
        name="Running Riot",
        game_id="halo_5",
        rank=15,
    ),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    KillingSpreeMedalState(
        id_="halo_5_rampage",
        medal_image=image_path("halo_5/rampage.png"),
        medal_sound=sound_path("halo_5/Rampage.mp3"),
        name="Rampage",
        game_id="halo_5",
        rank=20,
    ),
    KillingSpreeNoMedalState(rank=21),
    KillingSpreeNoMedalState(rank=22),
    KillingSpreeNoMedalState(rank=23),
    KillingSpreeNoMedalState(rank=24),
    KillingSpreeMedalState(
        id_="halo_5_untouchable",
        medal_image=image_path("halo_5/untouchable.png"),
        medal_sound=sound_path("halo_5/Untouchable.mp3"),
        name="Untouchable",
        game_id="halo_5",
        rank=25,
    ),
    KillingSpreeNoMedalState(rank=26),
    KillingSpreeNoMedalState(rank=27),
    KillingSpreeNoMedalState(rank=28),
    KillingSpreeNoMedalState(rank=29),
    KillingSpreeMedalState(
        id_="halo_5_invincible",
        medal_image=image_path("halo_5/invincible.png"),
        medal_sound=sound_path("halo_5/Invincible.mp3"),
        name="Invincible",
        game_id="halo_5",
        rank=30,
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
    KillingSpreeMedalState(
        id_="halo_5_unfriggenbelievable",
        medal_image=image_path("halo_5/unfriggenbelievable.png"),
        medal_sound=sound_path("halo_5/Unfriggenbelievable.mp3"),
        name="Unfriggen believable",
        game_id="halo_5",
        rank=40,
    ),
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
        id_="halo_5_perfection",
        medal_image=image_path("halo_5/perfection.png"),
        medal_sound=sound_path("halo_5/Perfection.mp3"),
        name="Perfection",
        game_id="halo_5",
        rank=50,
    ),
    KillingSpreeEndState(rank=51),
]


CA_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillFirstAnswerState(),
    MultikillMedalState(
        id_="Double Kill",
        medal_image=image_path("ca/Double Kill.png"),
        medal_sound=sound_path("ca/Double Kill.wav"),
        name="Double Kill",
        game_id="ca",
        rank=2,
    ),
    MultikillMedalState(
        id_="Multi Kill",
        medal_image=image_path("ca/Multi Kill.png"),
        medal_sound=sound_path("ca/Multi Kill.wav"),
        name="Multi Kill",
        game_id="ca",
        rank=3,
    ),
    MultikillMedalState(
        id_="Ultra Kill",
        medal_image=image_path("ca/Ultra Kill.png"),
        medal_sound=sound_path("ca/Ultra Kill.wav"),
        name="Ultra Kill",
        game_id="ca",
        rank=4,
    ),
    MultikillMedalState(
        id_="Fantastic",
        medal_image=image_path("ca/Fantastic.png"),
        medal_sound=sound_path("ca/Fantastic.wav"),
        name="Fantastic",
        game_id="ca",
        rank=5,
    ),
    MultikillMedalState(
        id_="Unbelievable",
        medal_image=image_path("ca/Unbelievable.png"),
        medal_sound=sound_path("ca/Unbelievable.wav"),
        name="Unbelievable",
        game_id="ca",
        rank=6,
    ),
    EndState(rank=7),
]

def get_all_displayable_medals():
    all_medals = itertools.chain(
        HALO_MULTIKILL_STATES,
        HALO_KILLING_SPREE_STATES,
        MW2_KILLSTREAK_STATES,
        HALO_5_MULTIKILL_STATES,
        HALO_5_KILLING_SPREE_STATES,
        CA_MULTIKILL_STATES
    )
    return filter(lambda m: m.is_displayable_medal, all_medals)


def get_stores_by_game_id(config):
    return dict(
        halo_3=Store(
            state_machines=[
                InitialStreakState(
                    states=HALO_MULTIKILL_STATES,
                    interval_s=config["multikill_interval_s"],
                ),
                InitialStreakState(
                    states=HALO_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
        mw2=Store(
            state_machines=[
                InitialStreakState(
                    states=MW2_KILLSTREAK_STATES,
                    interval_s=config["killing_spree_interval_s"],
                )
            ]
        ),
        halo_5=Store(
            state_machines=[
                InitialStreakState(
                    states=HALO_5_MULTIKILL_STATES,
                    interval_s=config["multikill_interval_s"],
                ),
                InitialStreakState(
                    states=HALO_5_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
        ca=Store(
            state_machines=[
                InitialStreakState(
                    states=CA_MULTIKILL_STATES,
                    interval_s=config["killing_spree_interval_s"],
                )
            ]
        ),
    )


def get_next_game_id(current_game_id):
    next_index = (all_game_ids.index(current_game_id) + 1) % len(all_game_ids)
    return all_game_ids[next_index]
