"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>

The goal of these controller classes is to have these be the only objects that
hold state in the add-on. The other classes ideally should be immutable.
This pattern has worked alright so far for this simple application.
"""
from functools import wraps, partial

from anki_killstreaks._vendor import attr

from anki_killstreaks.persistence import (
    migrate_database,
    DbSettings,
    get_db_connection,
    AchievementsRepository,
    SettingsRepository,
)
from anki_killstreaks.streaks import (
    did_card_pass,
    NewAchievement,
    Store,
    InitialStreakState,
    HALO_MULTIKILL_STATES,
    HALO_KILLING_SPREE_STATES,
    get_stores_by_game_id,
    get_next_game_id,
)


# Dirty hack that we need because profileLoaded hook called after DeckBrowser shown
def ensure_loaded(f):
    @wraps(f)
    def new_method(self, *args, **kwargs):
        if not self.is_loaded:
            self.load_profile()
        return f(self, *args, **kwargs)

    return new_method


@attr.s
class ProfileController:
    """
    Class that contains the parts of the application that need to change
    when the profile changes. This class (plus potentially others like it)
    will be bound to all of the Anki classes. Whenever a user changes profiles,
    the state contained in this class will be mutated to reflect the new
    profile. This ensures that the hooks and method wrapping around Anki objects
    only occurs once. This is necessary because their is no way to unwrap methods or
    unbind hook handlers.

    Unfortunate that this basically became a god object...


    Get placed in front of accessors to let you know they rely on profile
    dependent state that changes when you switch profiles.
    """
    # required attributes for class
    _local_conf = attr.ib()
    _show_achievements = attr.ib()
    _get_profile_folder_path = attr.ib()
    _stores_by_game_id = attr.ib()

    # Attributes modified in load_profile
    is_loaded = attr.ib(default=False)
    _db_settings = attr.ib(default=None)
    _achievements_repo = attr.ib(default=None)
    _reviewing_controller = attr.ib(default=None)

    def load_profile(self):
        self._db_settings = DbSettings.from_profile_folder_path(
            profile_folder_path=self._get_profile_folder_path()
        )

        migrate_database(settings=self._db_settings)

        with get_db_connection(self._db_settings) as db_connection:
            settings_repo = SettingsRepository(db_connection)
            store = self._stores_by_game_id[settings_repo.current_game_id]

            self._achievements_repo = AchievementsRepository(
                db_connection=db_connection,
            )

            self._reviewing_controller = self._build_reviewing_controller(
                game_id=settings_repo.current_game_id,
                should_auto_switch_game=settings_repo.should_auto_switch_game,
            )

        self.is_loaded = True

    def _build_reviewing_controller(self, game_id, should_auto_switch_game):
        new_controller = ReviewingController(
            store=self._stores_by_game_id[game_id],
            achievements_repo=self._achievements_repo,
            show_achievements=self._show_achievements
        )

        if should_auto_switch_game:
            return AllMedalsAcheivedNotifier(
                controller=new_controller,
                remaining_medals=new_controller.all_displayable_medals,
                notify=partial(
                    self.change_game,
                    game_id=get_next_game_id(current_game_id=game_id),
                ),
            )
        else:
            return new_controller

    def unload_profile(self):
        self._db_settings = None
        self._reviewing_controller = None
        self._acheivements_repo = None
        self.is_loaded = False

    def change_game(self, game_id):
        self._reviewing_controller = self._build_reviewing_controller(
            game_id=game_id,
            should_auto_switch_game=self.get_settings_repo().should_auto_switch_game
        )

    def toggle_auto_switch_game(self, should_auto_switch_game):
        pass

    @ensure_loaded
    def get_db_settings(self):
        """
        not using properties or attr built in methods because we need to be
        able to bind the getters for certain wrapping functions in the add-on
        """
        return self._db_settings

    @ensure_loaded
    def get_achievements_repo(self):
        return self._achievements_repo

    def get_db_connection(self):
        return get_db_connection(self._db_settings)

    @ensure_loaded
    def get_current_game_id(self):
        with get_db_connection(self._db_settings) as db_connection:
            return SettingsRepository(db_connection).current_game_id

    @ensure_loaded
    def get_reviewing_controller(self):
        return self._reviewing_controller

    @ensure_loaded
    def get_settings_repo(self):
        with get_db_connection(self._db_settings) as db_connection:
            return SettingsRepository(db_connection=db_connection)


def call_method_on_object_from_factory_function(
    method,
    factory_function,
    *args,
    **kwargs
):
    """
    This function takes a factory method, and then calls the passed method
    on the created object with the passed arguments. This lets us not delegate
    to the reviewing controller within the ProfileController.
    """
    def call_method(*args, **kwargs):
        return getattr(factory_function(), method)(*args, **kwargs)
    return call_method


# for handling undo, make Action class that takes store instance,
# repo instance, and answer and has undo and redo (or call) methods
# store these in a stack on the controller (maybe pass in so we can
# reinstanciate the controller on profile change) maybe immutable
# list? when undo hit, pop the stack and call undo on the action,
# replacing the controller's current store instance with the
# popped action's.
class ReviewingController:
    def __init__(self, store, achievements_repo, show_achievements):
        self.store = store
        self.achievements_repo = achievements_repo
        self.show_achievements = show_achievements

    def on_answer(self, ease, deck_id, grade_card=did_card_pass):
        self.store = self.store.on_answer(did_card_pass(ease))

        self.achievements_repo.create_all(
            [
                NewAchievement(medal=medal, deck_id=deck_id)
                for medal
                in self.store.current_displayable_medals
            ]
        )

        self.show_achievements(self.store.current_displayable_medals)
        return self.store.current_displayable_medals

    def on_show_question(self):
        self.store = self.store.on_show_question()

    def on_show_answer(self):
        self.store = self.store.on_show_answer()

    @property
    def all_displayable_medals(self):
        return self.store.all_displayable_medals


def build_on_answer_wrapper(reviewer, ease, on_answer):
    deck_id = reviewer.mw.col.decks.current()['id']
    on_answer(ease=ease, deck_id=deck_id)


@attr.s
class AllMedalsAcheivedNotifier:
    _controller = attr.ib()
    _remaining_medals = attr.ib(type=frozenset)
    _notify = attr.ib()

    def on_answer(self, *args, **kwargs):
        earned_medals = self._controller.on_answer(*args, **kwargs)
        self._remaining_medals -= frozenset(earned_medals)

        if len(self._remaining_medals) == 0:
            self._notify()

        return earned_medals

    def __getattr__(self, attr):
        return getattr(self._controller, attr)
