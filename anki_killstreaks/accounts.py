from urllib.parse import urljoin
import requests
from .networking import sra_base_url




class UserRepository:
    def __init__(self, get_db_connection):
        self.get_db_connection = get_db_connection

    def save(self, uid, token, client, expiry):
        with self.get_db_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET uid = ?,
                    token = ?,
                    client = ?,
                    expiry = ?
                """,
                (uid, token, client, expiry)
            )


def login(email, password, listener, user_repo):
    headers={
        "user_email": "JimmyYoshi@gmail.com",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    body = dict(
        email=email,
        password=password,
    )
    url = urljoin(sra_base_url, "api/v1/auth/sign_in")

    try:
        response = requests.post(url, headers=headers, json=body)

        print(response.status_code)
        print(response.text)

        if response.status_code == 200:
            headers = response.headers

            user_repo.save(
                uid=headers["uid"],
                token=headers["access-token"],
                client=headers["client"],
                expiry=headers["expiry"],
            )

            listener.on_successful_login(response.json()["data"])
        elif response.status_code == 401:
            listener.on_unauthorized(response.json())
        else:
            raise RuntimeError("Unhandled response status", response)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        listener.on_connection_error()
