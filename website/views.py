from flask import Blueprint, render_template
from flask_login import current_user, login_required
from . import mysql


views = Blueprint('views', __name__)


@views.route('/')
def home():
    # query to get courses
    courses = []

    return render_template('home.html', user=current_user)


# @views.route('/<search_term>')
# def browse():
#     pass


@views.route('/student_profile')
@login_required
def student():
    pass


@views.route('/teacher_profile')
@login_required
def teacher():
    pass


@views.route('/<course_id>')
@login_required
def course(course_id):
    course = None
    if course is not None:
        # no page
        pass
    else:
        contents = []
        assessments = []
        return render_template('course_student.html', user=current_user, study_materials=contents, assessments=assessments)


@views.route('/add_course')
@login_required
def add_course():
    pass


@views.route('/<course_id>/<content_id>')
@login_required
def content(course_id, content_id):
    course = None
    content = None
    if course is None:
        # no page
        pass
    elif content is None:
        # no page
        pass
    else:
        return render_template('course_student.html', user=current_user, content=content)


@views.route('/add_content')
@login_required
def add_content():
    pass


@views.route('/<course_id>/<assessment_id>')
@login_required
def assessment(course_id, assessment_id):
    pass


@views.route('/add_assessment')
@login_required
def add_assessment():
    pass
