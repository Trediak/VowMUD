from core.user_manager import UserManager

class ManagerHub:
    def __init__(self):
        self.user_manager = UserManager()

manager_hub = ManagerHub()