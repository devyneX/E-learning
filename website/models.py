from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, account_id, account_type, email, username, enc_password):
        self.account_id = account_id
        self.account_type = account_type
        self.email = email
        self.username = username
        self.enc_password = enc_password


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
