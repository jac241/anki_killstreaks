from anki_killstreaks._vendor.yoyo import step

steps = [
    step("ALTER TABLE settings ADD should_auto_switch_game BOOLEAN DEFAULT 0 NOT NULL")
]
