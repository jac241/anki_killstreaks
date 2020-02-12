from anki_killstreaks.streaks import did_card_pass, Acheivement


class ReviewingController:
    def __init__(self, store, acheivements, show_acheivements):
        self.store = store
        self.acheivements = acheivements
        self.show_acheivements = show_acheivements

    def on_answer(self, ease, grade_card=did_card_pass):
        self.store = self.store.on_answer(did_card_pass(ease))

        self.acheivements.extend(
            Acheivement(medal=medal)
            for medal
            in self.store.displayable_medals
        )

        self.show_acheivements(self.store.displayable_medals)

    def on_show_question(self):
        self.store = self.store.on_show_question()

    def on_show_answer(self):
        self.store = self.store.on_show_answer()


def build_on_answer_wrapper(_reviewer, ease, on_answer):
    on_answer(ease)

