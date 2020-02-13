from anki_killstreaks._vendor.yoyo import step

steps = [
    step(
"""CREATE TABLE acheivements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medal_id TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
)""",
    """CREATE INDEX IF NOT EXISTS acheivements_created_at ON acheivements(created_at)"""
    )
]
