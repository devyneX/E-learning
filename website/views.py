from unicodedata import category
import MySQLdb
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from datetime import date
from .models import Course, Content, Assessment
from . import mysql


views = Blueprint('views', __name__)


@views.route('/')
def home():
    return render_template('home.html', user=current_user)


# @views.route('/<search_term>')
# def browse():
#     pass
@views.route('/profile')
@login_required
def profile():
    if current_user.account_type == 'student':
        return redirect(url_for('views.student'))
    elif current_user.account_type == 'teacher':
        return redirect(url_for('views.teacher'))
    else:
        return redirect(url_for('views.home'))


@views.route('/student_profile')
@login_required
def student():
    pass


@views.route('/teacher_profile', methods=['GET', 'POST'])
@login_required
def teacher():
    print(current_user.account_id)
    if request.method == 'POST':
        course_title = request.form.get('course_title')
        category = request.form.get('category')
        description = request.form.get('description')
        cur = mysql.connection.cursor()
        cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                    (current_user.account_id, ))
        teacher_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO course (course_title, category, description, teacher_id, created_on) VALUES (%s, %s, %s, %s, %s)""",
                    (course_title, category, description, teacher_id, date.today()))
        mysql.connection.commit()
        cur.execute("""SELECT course_id FROM course WHERE course_title = %s and category = %s and description = %s and teacher_id = %s""",
                    (course_title, category, description, teacher_id))
        course_id = cur.fetchone()[0]
        return redirect(url_for(views.course, course_id=course_id))
    return render_template('teacher.html', user=current_user)


@views.route('/course/<course_id>')
@login_required
def course(course_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""SELECT * FROM course WHERE course_id = %s""", (course_id, ))
    result = cur.fetchone()
    if result is None:
        # no page
        pass
    else:
        teacher = None
        rating = None
        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], teacher, rating)
        contents = []
        cur.execute(
            """SELECT * FROM content WHERE course_id = %s""", (course_id, ))
        ls = cur.fetchall()
        for content in ls:
            contents.append(Content(content['content_id'], content['content_title'],
                            content['link'], content['course_id'], content['teacher_id']))
        assessments = []
        cur.execute(
            """SELECT * FROM assessment WHERE course_id = %s""", (course_id, ))
        ls = cur.fetchall()
        cur.close()
        for assessment in ls:
            assessments.append(Assessment(
                assessment['assessment_id'], assessment['assessment_title'], assessment['course_id'], assessment['teacher_id']))
        return render_template('course.html', user=current_user, study_materials=contents, assessments=assessments)
    return render_template('course.html', user=current_user, study_materials=contents, assessments=assessments)


# @views.route('/add_course')
# @login_required
# def add_course():
#     pass


@views.route('courses/<course_id>/<content_id>')
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


# @views.route('/add_content')
# @login_required
# def add_content():
#     pass


@views.route('courses/<course_id>/<assessment_id>')
@login_required
def assessment(course_id, assessment_id):
    pass


@views.route('/add_assessment')
@login_required
def add_assessment():
    assessments = []
    return render_template('assessment_add.html', user=current_user, assessments=assessments)
