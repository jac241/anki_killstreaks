from anki_killstreaks.accounts import UserRepository

import pytest

@pytest.fixture
def user_repository(get_db_connection):
    return UserRepository(get_db_connection)

def test_UserRepository_create_should_create_user_with_passed_attributes(user_repository):
    user_repository.create(uid="JimmyYoshi@gmail.com", token="token")

    with user_repository.get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM users")
        saved_user = cursor.fetchone()

    assert saved_user[1] == "JimmyYoshi@gmail.com"
    assert saved_user[2] == "token"
