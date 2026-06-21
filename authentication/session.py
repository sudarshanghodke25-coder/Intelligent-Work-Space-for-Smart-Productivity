class Session:
    """Stores the current logged-in user's details."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
            cls._instance.user_id = None
            cls._instance.username = None
            cls._instance.email = None
            cls._instance.full_name = None
            cls._instance.login_time = None
        return cls._instance

    def login(self, user_id, username, email, full_name, login_time):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.login_time = login_time

    def logout(self):
        self.user_id = None
        self.username = None
        self.email = None
        self.full_name = None
        self.login_time = None

    def is_logged_in(self):
        return self.user_id is not None

# Global session instance
current_session = Session()
