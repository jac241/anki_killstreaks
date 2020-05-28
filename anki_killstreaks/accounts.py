class UserRepository:
    def __init__(self, get_db_connection):
        self.get_db_connection = get_db_connection

    def create(self, uid, token):
        with self.get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users(uid, token) VALUES (?, ?)",
                (uid, token)
            )
