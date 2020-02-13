from pathlib import Path
import sqlite3

import pytest
from anki_killstreaks.persistence import DbSettings, migrate_database, AcheivementsRepository
from anki_killstreaks.streaks import MultikillMedalState, NewAcheivement


def test_migrate_database_creates_a_medals_database(db_settings):
    returned_settings = migrate_database(settings=db_settings)

    assert returned_settings.db_path.exists()


def test_AcheivementsRepository_create_all_should_save_acheivements(db_connection):
    repo = AcheivementsRepository(db_connection=db_connection)

    repo.create_all(
        [
            NewAcheivement(
                medal=MultikillMedalState(
                    name='Double Kill',
                    medal_image=None
                )
            )
        ]
    )

    acheivements = repo.all()

    assert len(acheivements) == 1

