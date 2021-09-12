from core.user import User

class UserManager:
    """Class which manages user connections"""
    def __init__(self):
        self.users = {}

    def register(self, user: User) -> None:
        """Register user in UserManager"""
        if user.socket not in self.users:
            self.users[user.socket] = user

        else:
            user.socket.close()

    def unregister(self, user: User) -> None:
        """Unregister user from UserManager"""
        if user.socket in self.users:
            self.users.pop(user.socket, None)

    def is_logged_in(self, account_name: str) -> bool:
        """Return True if user with account_name is in users dictionary else False"""
        for _, user_object in self.users.items():
            if user_object.account_name == account_name:
                return True

        return False

    def get_user_by_account_name(self, account_name: str) -> User:
        for _, user_object in self.users.items():
            if user_object.account_name == account_name:
                return user_object
