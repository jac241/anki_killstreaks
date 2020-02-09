from anki_killstreaks._vendor.yoyo import step

steps = [
    step(
"""CREATE TABLE acheivements (
        id integer PRIMARY KEY AUTOINCREMENT,
        medal_id text NOT NULL,
        created_at text NOT NULL
)""",
    """CREATE INDEX IF NOT EXISTS acheivements_created_at ON acheivements(created_at)"""
    )
]
