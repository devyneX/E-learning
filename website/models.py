from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, account_id, account_type, email, username, enc_password):
        self.account_id = account_id
        self.account_type = account_type
        self.username = username
        self.email = email
        self.enc_password = enc_password

    def get_id(self):
        return str(self.account_id)


class Student:
    def __init__(self):
        pass


class Teacher:
    def __init__(self):
        pass


class Course:
    def __init__(self):
        pass


class Content:
    def __init__(self):
        pass


class Assessment:
    def __init__(self):
        pass


class Question:
    def __init__(self):
        pass


class Comment:
    def __init__(self):
        pass


class Feedback:
    def __init__(self):
        pass
