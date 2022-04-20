import MySQLdb
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from datetime import date, datetime
from .models import Course, Content, Assessment, Question, Student, Teacher, Comment
from . import mysql


views = Blueprint('views', __name__)


@views.route('/')
def home():
    return render_template('home.html', user=current_user)


@views.route('/account', methods=['GET'])
def account():
    cur = mysql.connection.cursor()
    if current_user.account_type == 'student':
        cur.execute("""SELECT firstname, lastname FROM student WHERE account_id = %s""",
                    (current_user.account_id, ))
    elif current_user.account_type == 'teacher':
        cur.execute("""SELECT firstname, lastname FROM teacher WHERE account_id = %s""",
                    (current_user.account_id, ))
    firstname, lastname = cur.fetchone()
    cur.close()
    return render_template('account.html', user=current_user, firstname=firstname, lastname=lastname)


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
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""SELECT * FROM student WHERE account_id = %s""",
                    (current_user.account_id, ))
        result = cur.fetchone()
        student_obj = Student(result['student_id'], result['firstname'],
                              result['lastname'], result['join_date'], result['account_id'])
        cur.execute("""SELECT * FROM course c WHERE c.course_id in (SELECT course_id FROM enrollment WHERE student_id = %s)""",
                    (student_obj.student_id, ))
        ls = cur.fetchall()
        courses = []
        for course in ls:
            courses.append(Course(course['course_id'], course['course_title'],
                           course['category'], course['description'], course['teacher_id']))

        cur.execute("""SELECT * FROM assessment a WHERE a.assessment_id in (SELECT assessment_id FROM attended_assessment WHERE student_id = %s)""",
                    (student_obj.student_id, ))
        ls = cur.fetchall()

        return render_template('student.html', user=current_user, student=student_obj, courses=courses, course_count=len(courses), assessment_count=len(ls))


@ views.route('/teacher_profile', methods=['GET', 'POST'])
@ login_required
def teacher():
    # print(current_user.account_id)
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""SELECT * FROM teacher WHERE account_id = %s""",
                    (current_user.account_id, ))
        result = cur.fetchone()
        teacher_obj = Teacher(result['teacher_id'], result['firstname'],
                              result['lastname'], result['join_date'], result['account_id'])
        cur.execute("""SELECT * FROM course WHERE teacher_id = %s""",
                    (teacher_obj.teacher_id, ))
        ls = cur.fetchall()
        courses = []
        for course in ls:
            courses.append(Course(course['course_id'], course['course_title'],
                           course['category'], course['description'], course['teacher_id']))

        return render_template('teacher.html', user=current_user, teacher=teacher_obj, courses=courses, course_count=len(courses))

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
        cur.close()
        return redirect(url_for('views.course', course_id=course_id))


@ views.route('/course/<course_id>', methods=['GET', 'POST'])
@ login_required
def course(course_id):
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT * FROM course WHERE course_id = %s""", (course_id, ))
        result = cur.fetchone()
        if result is None:
            # no page
            pass
        else:
            cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                        (current_user.account_id, ))
            teacher = cur.fetchone()['teacher_id']
            cur.execute(
                """SELECT COUNT(star) as count, AVG(star) as avg FROM feedback WHERE course_id = %s""", (course_id, ))
            rating_result = cur.fetchone()
            rating_count, rating = rating_result['count'], rating_result['avg']
            course = Course(result['course_id'], result['course_title'],
                            result['category'], result['description'], teacher)
            contents = []
            cur.execute(
                """SELECT * FROM content WHERE course_id = %s""", (course_id, ))
            ls = cur.fetchall()
            # print(ls)
            for content in ls:
                contents.append(Content(content['content_id'], content['content_title'],
                                content['link'], content['course_id'], content['teacher_id']))
            # print(contents)
            assessments = []
            cur.execute(
                """SELECT * FROM assessment WHERE course_id = %s""", (course_id, ))
            ls = cur.fetchall()
            cur.close()
            for assessment in ls:
                assessments.append(Assessment(assessment['assessment_id'], assessment['assessment_title'],
                                              assessment['course_id'], assessment['teacher_id']))
            return render_template('course.html', user=current_user, course=course, rating=rating, rating_count=rating_count, study_materials=contents, assessments=assessments)

    # return render_template('course.html', user=current_user, course=course, rating=rating, rating_count=rating_count, study_materials=contents, assessments=assessments)


@views.route('/course/<course_id>/enroll', methods=['POST'])
def enroll(course_id):
    return redirect(url_for('views.course', course_id=course_id))


@views.route('/course/<course_id>/feedback')
@login_required
def feedback(course_id):
    return render_template('feedback.html', user=current_user)


@views.route('/course/<course_id>/add_content', methods=['POST'])
@login_required
def add_content(course_id):
    content_title = request.form.get('content_title')
    link = request.form.get('link')

    cur = mysql.connection.cursor()
    cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                (current_user.account_id, ))
    teacher = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO content (content_title, link, course_id, teacher_id) VALUES (%s, %s, %s, %s)""", (content_title, link, course_id, teacher))
    mysql.connection.commit()
    cur.execute("""SELECT content_id FROM content WHERE content_title = %s and link = %s and course_id = %s and teacher_id = %s""",
                (content_title, link, course_id, teacher))
    content_id = cur.fetchone()[0]
    cur.close()
    return redirect(url_for('views.content', course_id=course_id, content_id=content_id))


@views.route('course/<course_id>/add_assessment', methods=['GET', 'POST'])
@login_required
def add_assessment(course_id):
    assessment_title = request.form.get('assessment_title')
    print(request.form.get('assessment_title'))
    return redirect(url_for('views.course', course_id=course_id))

    cur = mysql.connection.cursor()
    cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                (current_user.account_id, ))
    teacher = cur.fetchone()[0]
    print(teacher)
    cur.execute(
        """INSERT INTO assessment (assessment_title, course_id, teacher_id) VALUES (%s, %s, %s)""", (assessment_title, course_id, teacher))
    mysql.connection.commit()
    cur.execute("""SELECT assessment_id FROM assessment WHERE assessment_title = %s and course_id = %s and teacher_id = %s""",
                (assessment_title, course_id, teacher))
    assessment_id = cur.fetchone()[0]
    cur.close()
    return redirect(url_for('views.add_questions', course_id=course_id, assessment_id=assessment_id))


@views.route('/course/<course_id>/assessment/<assessment_id>/add_questions', methods=['GET', 'POST'])
@login_required
def add_questions(course_id, assessment_id):
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT * FROM course WHERE course_id = %s""", (course_id, ))
        result = cur.fetchone()
        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], teacher)
        cur.execute("""SELECT * FROM assessment WHERE assessment_id = %s""",
                    (assessment_id, ))
        result = cur.fetchone()
        assessment = Assessment(
            result['assessment_id'], result['assessment_title'], result['course_id'], result['teacher_id'])
        # cur.close()
        if course is None:
            # no page
            pass
        elif assessment is None:
            # no page
            pass
        else:
            # cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute(
                """SELECT * FROM questions WHERE assessment_id = %s""", (assessment_id, ))
            ls = cur.fetchall()
            questions = []
            for question in ls:
                print(question)
                questions.append(Question(
                    assessment_id, question['text'], question['option1'], question['option2'], question['option3'], question['option4'], None))
            cur.close()
            return render_template('question_add.html', user=current_user, course=course, assessment=assessment, questions=questions)

    if request.method == 'POST':
        print('here')
        text = request.form.get('text')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct = request.form.get('correct')
        print(text, option1, option2, option3, option4, correct)
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO questions (assessment_id, text, option1, option2, option3, option4, correct) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (assessment_id, text, option1, option2, option3, option4, correct))
        mysql.connection.commit()
        cur.close()
        print('done')
        # return render_template('question_add.html', user=current_user, course=course, assessment=assessment, questions=questions)
        return redirect(url_for('views.add_questions', course_id=course_id, assessment_id=assessment_id))


@views.route('course/<course_id>/content/<content_id>', methods=['GET', 'POST'])
@login_required
def content(course_id, content_id):
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT * FROM course WHERE course_id = %s""", (course_id, ))
        result = cur.fetchone()
        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], teacher)
        cur.execute("""SELECT * FROM content WHERE content_id = %s""",
                    (content_id, ))
        result = cur.fetchone()
        content = Content(result['content_id'], result['content_title'],
                          result['link'], result['course_id'], result['teacher_id'])
        cur.close()
        if course is None:
            # no page
            pass
        elif content is None:
            # no page
            pass
        else:
            cur = mysql.connection.cursor()
            cur.execute(
                """SELECT * FROM comment WHERE content_id = %s ORDER BY post_time""", (content_id, ))
            ls = cur.fetchall()
            comments = []
            for cid, text, sid, tid, post_time in ls:
                if sid is None:
                    cur.execute(
                        """SELECT username FROM authorization a WHERE a.account_id = (SELECT account_id FROM teacher WHERE teacher_id = %s)""", (tid, ))
                    username = cur.fetchone()[0]
                    print(username)
                    comments.append(
                        Comment(cid, text, username, 'Teacher', post_time))
                elif tid is None:
                    cur.execute(
                        """SELECT username FROM authorization a WHERE a.account_id = (SELECT account_id FROM student WHERE studnet_id = %s)""", (sid, ))
                    username = cur.fetchone()[0]
                    comments.append(
                        Comment(cid, text, username, 'Student', post_time))
            return render_template('content.html', user=current_user, course=course, study_material=content, comments=comments)

    if request.method == 'POST':
        text = request.form.get('comment')
        cur = mysql.connection.cursor()
        if current_user.account_type == 'student':
            cur.execute("""SELECT student_id FROM student WHERE account_id = %s""",
                        (current_user.account_id, ))
        elif current_user.account_type == 'teacher':
            cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                        (current_user.account_id, ))

        user_id = cur.fetchone()[0]

        if current_user.account_type == 'student':
            cur.execute("""INSERT INTO comment (content_id, text, student_id, post_time) VALUES (%s, %s, %s, %s)""",
                        (content_id, text, user_id, datetime.now()))
        elif current_user.account_type == 'teacher':
            cur.execute("""INSERT INTO comment (content_id, text, teacher_id, post_time) VALUES (%s, %s, %s, %s)""",
                        (content_id, text, user_id, datetime.now()))

        mysql.connection.commit()
        return redirect(url_for('views.content', course_id=course_id, content_id=content_id))


@views.route('course/<course_id>/assessment/<assessment_id>', methods=['GET', 'POST'])
@login_required
def assessment(course_id, assessment_id):
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT * FROM course WHERE course_id = %s""", (course_id, ))
        result = cur.fetchone()
        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], teacher)
        cur.execute("""SELECT * FROM assessment WHERE assessment_id = %s""",
                    (assessment_id, ))
        result = cur.fetchone()
        assessment = Assessment(
            result['assessment_id'], result['assessment_title'], result['course_id'], result['teacher_id'])
        if course is None:
            # no page
            pass
        elif assessment is None:
            # no page
            pass
        else:
            cur.execute(
                """SELECT * FROM questions WHERE assessment_id = %s""", (assessment_id, ))
            ls = cur.fetchall()
            cur.close()
            questions = []
            for question in ls:
                questions.append(Question(assessment_id, question['text'], question['option1'],
                                 question['option2'], question['option3'], question['option4'], question['correct']))

            return render_template('assessment.html', user=current_user, course=course, assessment=assessment, questions=questions)

    if request.method == 'POST':
        marks = 0
        cur = mysql.connection.cursor()
        cur.execute(
            """SELECT correct FROM questions q WHERE q.assessment_id = %s""", (assessment_id, ))
        correct_answers = [x[0] for x in cur.fetchall()]
        for k, correct in zip(request.form.keys(), correct_answers):
            # print(type(request.form[k]), type(correct))
            if int(request.form[k]) == correct:
                marks += 1

        cur.execute("""SELECT student_id FROM student WHERE account_id = %s""",
                    (current_user.account_id, ))
        student_id = cur.fetchone()[0]
        # print(student_id)
        cur.execute(
            """INSERT INTO attended_assessment (student_id, assessment_id, result) VALUES (%s, %s, %s)""", (student_id, assessment_id, f'{marks}/{len(correct_answers)}'))
        mysql.connection.commit()
        cur.close()
        # print(student_id)
        return redirect(url_for('views.result', course_id=course_id, assessment_id=assessment_id))


@views.route('/course/<course_id>/assessment/<assessment_id>/result', methods=['GET'])
@login_required
def result(course_id, assessment_id):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT result FROM attended_assessment a WHERE a.assessment_id = %s AND a.student_id = (SELECT student_id FROM student WHERE account_id= %s)""",
                (assessment_id, current_user.account_id))
    marks = cur.fetchone()[0]
    return render_template('result.html', user=current_user, marks=marks)
