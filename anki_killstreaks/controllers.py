"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""
from anki_killstreaks.streaks import did_card_pass, NewAcheivement


class ReviewingController:
    def __init__(self, store, acheivements_repo, show_acheivements):
        self.store = store
        self.acheivements_repo = acheivements_repo
        self.show_acheivements = show_acheivements

    def on_answer(self, ease, grade_card=did_card_pass):
        self.store = self.store.on_answer(did_card_pass(ease))

        self.acheivements_repo.create_all(
            [
                NewAcheivement(medal=medal)
                for medal
                in self.store.displayable_medals
            ]
        )

        self.show_acheivements(self.store.displayable_medals)

    def on_show_question(self):
        self.store = self.store.on_show_question()

    def on_show_answer(self):
        self.store = self.store.on_show_answer()


def build_on_answer_wrapper(_reviewer, ease, on_answer):
    on_answer(ease)

