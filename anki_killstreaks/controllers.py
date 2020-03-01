"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""
from anki_killstreaks.streaks import did_card_pass, NewAcheivement


# for handling undo, make Action class that takes store instance,
# repo instance, and answer and has undo and redo (or call) methods
# store these in a stack on the controller (maybe pass in so we can
# reinstanciate the controller on profile change) maybe immutable
# list? when undo hit, pop the stack and call undo on the action,
# replacing the controller's current store instance with the
# popped action's.

class ReviewingController:
    def __init__(self, store, acheivements_repo, show_acheivements):
        self.store = store
        self.acheivements_repo = acheivements_repo
        self.show_acheivements = show_acheivements

    def on_answer(self, ease, deck_id, grade_card=did_card_pass):
        self.store = self.store.on_answer(did_card_pass(ease))

        self.acheivements_repo.create_all(
            [
                NewAcheivement(medal=medal, deck_id=deck_id)
                for medal
                in self.store.displayable_medals
            ]
        )

        self.show_acheivements(self.store.displayable_medals)

    def on_show_question(self):
        self.store = self.store.on_show_question()

    def on_show_answer(self):
        self.store = self.store.on_show_answer()


def build_on_answer_wrapper(reviewer, ease, on_answer):
    deck_id = reviewer.mw.col.decks.current()['id']
    on_answer(ease=ease, deck_id=deck_id)

