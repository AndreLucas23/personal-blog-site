from flask_login import UserMixin


class AuthUser(UserMixin):
    def __init__(self, user: dict):
        self._user = user

    def get_id(self) -> str:
        return str(self._user['user_id'])

    @property
    def user_id(self) -> int:
        return self._user['user_id']

    @property
    def is_admin(self) -> bool:
        return bool(self._user.get('is_admin'))

    @property
    def username(self) -> str:
        return self._user['username']

    @property
    def email(self) -> str:
        return self._user['email']
