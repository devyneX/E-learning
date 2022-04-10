from flask import Blueprint, render_template
from flask_login import current_user


views = Blueprint('views', __name__)


@views.route('/')
def home():
    # query to get courses
    courses = []

    return render_template('home.html', user=current_user, courses=courses)


def student():
    pass


def teacher():
    pass


@views.route('/<course_id>')
def course():
    # if course_id not in database:
    #     no page
    # else:
    #     return course_student.html
    pass


@views.route('/<course_id>/<content_id>')
def content(course_id, content_id):
    # if course_id not in database:
    #     no page
    # elif content_id not in database:
    #     no page
    # else:
    #     return course_student.html
    pass
