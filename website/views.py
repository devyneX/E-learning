import MySQLdb
from flask import Blueprint, abort, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from datetime import date, datetime
from .models import Course, Content, Assessment, Question, Student, Teacher, Comment
from . import mysql


views = Blueprint('views', __name__)


@views.route('/')
def home():
    # home page
    return render_template('home.html', user=current_user)


@views.route('/search', methods=['POST'])
def search():
    # search
    search_term = request.form.get('search_term')
    return redirect(url_for('views.browse_search', search_term=search_term))


@views.route('/search/<search_term>')
def browse_search(search_term):
    # search page
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # fetching courses with titles like search term
    cur.execute(
        """SELECT * FROM course WHERE course_title LIKE %s""", (f'%{search_term}%', ))
    ls = cur.fetchall()
    courses = []
    for course in ls:
        courses.append(Course(course['course_id'], course['course_title'],
                              course['category'], course['description'], course['teacher_id']))
        # fetching the name of the teacher
        cur.execute(
            """SELECT firstname, lastname FROM teacher WHERE teacher_id = %s""", (course['teacher_id'], ))
        result = cur.fetchone()
        courses[-1].teacher = result['firstname'] + ' ' + result['lastname']
    return render_template('browse.html', user=current_user, title=search_term, courses=courses)


@views.route('/category/<category>')
def browse_categories(category):
    # browsing by categories
    category = category.replace('-', ' ')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # fetching courses with the searched category
    cur.execute(
        """SELECT * FROM course WHERE category = %s""", (category, ))
    ls = cur.fetchall()
    courses = []
    for course in ls:
        courses.append(Course(course['course_id'], course['course_title'],
                              course['category'], course['description'], course['teacher_id']))
        # fetching the name of the teacher
        cur.execute(
            """SELECT firstname, lastname FROM teacher WHERE teacher_id = %s""", (course['teacher_id'], ))
        result = cur.fetchone()
        courses[-1].teacher = result['firstname'] + ' ' + result['lastname']
    return render_template('browse.html', user=current_user, title=category, courses=courses)


@views.route('/account', methods=['GET'])
@login_required
def account():
    cur = mysql.connection.cursor()
    if current_user.account_type == 'student':
        # fetching name of the student
        cur.execute("""SELECT firstname, lastname FROM student WHERE account_id = %s""",
                    (current_user.account_id, ))
        firstname, lastname = cur.fetchone()
        cur.close()
        return render_template('account.html', user=current_user, firstname=firstname, lastname=lastname)
    elif current_user.account_type == 'teacher':
        # fetching the name of the teacher
        cur.execute("""SELECT firstname, lastname FROM teacher WHERE account_id = %s""",
                    (current_user.account_id, ))
        firstname, lastname = cur.fetchone()
        cur.close()
        return render_template('account.html', user=current_user, firstname=firstname, lastname=lastname)
    else:
        return redirect(url_for('auth.login'))


@views.route('/profile')
@login_required
def profile():
    if current_user.account_type == 'student':
        return redirect(url_for('views.student'))
    elif current_user.account_type == 'teacher':
        return redirect(url_for('views.teacher'))
    else:
        return redirect(url_for('auth.login'))


@views.route('/student_profile')
@login_required
def student():
    # checking if current user is student
    if current_user.account_type == 'student':
        if request.method == 'GET':
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # fetching the student id from db
            cur.execute("""SELECT * FROM student WHERE account_id = %s""",
                        (current_user.account_id, ))
            result = cur.fetchone()
            # creating student object with info collected from db
            student_obj = Student(result['student_id'], result['firstname'],
                                  result['lastname'], result['join_date'], result['account_id'])
            # fetching the enrolled courses
            cur.execute("""SELECT * FROM course c WHERE c.course_id in (SELECT course_id FROM enrollment WHERE student_id = %s)""",
                        (student_obj.student_id, ))
            ls = cur.fetchall()
            # making objects for courses and adding to list
            courses = []
            for course in ls:
                courses.append(Course(course['course_id'], course['course_title'],
                                      course['category'], course['description'], course['teacher_id']))
                cur.execute(
                    """SELECT firstname, lastname FROM teacher WHERE teacher_id = %s""", (courses[-1].teacher, ))
                name = cur.fetchone()
                courses[-1].teacher = name['firstname'] + \
                    ' ' + name['lastname']
            # fetching the assessment count from student
            cur.execute("""SELECT COUNT(*) as count FROM assessment a WHERE a.assessment_id in (SELECT assessment_id FROM attended_assessment WHERE student_id = %s)""",
                        (student_obj.student_id, ))
            assessment_count = cur.fetchone()['count']

            return render_template('student.html', user=current_user, student=student_obj, courses=courses, course_count=len(courses), assessment_count=assessment_count)
    # checking if account type is teacher
    elif current_user.account_type == 'teacher':
        # redirecting to teacher profile
        return redirect(url_for('views.teacher'))
    else:
        # not logged in
        return redirect(url_for('auth.login'))


@ views.route('/teacher_profile', methods=['GET', 'POST'])
@ login_required
def teacher():
    if current_user.account_type == 'teacher':
        if request.method == 'GET':
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # fetching teacher info from db
            cur.execute("""SELECT * FROM teacher WHERE account_id = %s""",
                        (current_user.account_id, ))
            result = cur.fetchone()
            teacher_obj = Teacher(result['teacher_id'], result['firstname'],
                                  result['lastname'], result['join_date'], result['account_id'])
            # fetching created courses from db
            cur.execute("""SELECT * FROM course WHERE teacher_id = %s""",
                        (teacher_obj.teacher_id, ))
            ls = cur.fetchall()
            courses = []
            for course in ls:
                courses.append(Course(course['course_id'], course['course_title'],
                                      course['category'], course['description'], course['teacher_id']))
                # fetching course teacher name from db
                cur.execute(
                    """SELECT firstname, lastname FROM teacher WHERE teacher_id = %s""", (courses[-1].teacher, ))
                name = cur.fetchone()
                courses[-1].teacher = name['firstname'] + \
                    ' ' + name['lastname']

            cur.close()
            cur = mysql.connection.cursor()
            # fetching average course rating
            cur.execute(
                """SELECT AVG(star) FROM feedback f WHERE f.course_id in (SELECT course_id FROM course WHERE teacher_id = %s)""", (teacher_obj.teacher_id, ))
            rating = cur.fetchone()[0]
            rating = str(rating)[:3] if rating is not None else "Not rated yet"
            cur.close()

            return render_template('teacher.html', user=current_user, teacher=teacher_obj, rating=rating, courses=courses, course_count=len(courses))

        if request.method == 'POST':
            course_title = request.form.get('course_title')
            category = request.form.get('category')
            description = request.form.get('description')
            cur = mysql.connection.cursor()
            # checking if a valid category is selected
            if category not in ['Web Development', 'Software Development', 'Machine Learning', 'Deep Learning']:
                redirect(url_for('views.teacher'))

            # fetching teacher id
            cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                        (current_user.account_id, ))
            teacher_id = cur.fetchone()[0]
            # inserting into the course table
            cur.execute("""INSERT INTO course (course_title, category, description, teacher_id, created_on) VALUES (%s, %s, %s, %s, %s)""",
                        (course_title, category, description, teacher_id, date.today()))
            mysql.connection.commit()
            # getting the id of the last inserted course
            cur.execute("""SELECT course_id FROM course WHERE course_title = %s AND category = %s AND description = %s AND teacher_id = %s ORDER BY course_id DESC""",
                        (course_title, category, description, teacher_id))
            course_id = cur.fetchone()[0]
            cur.close()
            return redirect(url_for('views.course', course_id=course_id))
    elif current_user.account_type == 'student':
        # if current user is student redirectig to student page
        return redirect(url_for('views.student'))
    else:
        return redirect(url_for('auth.login'))


@ views.route('/course/<course_id>', methods=['GET'])
@ login_required
def course(course_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        """SELECT * FROM course WHERE course_id = %s""", (course_id, ))
    result = cur.fetchone()
    # checking if course exists in db
    if result is None:
        # no page
        abort(404)
    else:
        # fetching ratings from db
        cur.execute(
            """SELECT COUNT(star) as count, AVG(star) as avg FROM feedback WHERE course_id = %s""", (course_id, ))
        rating_result = cur.fetchone()
        rating_count, rating = rating_result['count'], rating_result['avg']
        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], result['teacher_id'])

        enrolled_student = False
        creator_teacher = False
        rated = False
        if current_user.account_type == 'student':
            # checking if the student is enrolled
            cur.execute("""SELECT * FROM enrollment e WHERE e.course_id = %s and e.student_id = (SELECT student_id FROM student WHERE account_id = %s)""",
                        (course_id, current_user.account_id))
            enrollment = cur.fetchone()
            if enrollment is not None:
                enrolled_student = True
            # checking if the student has given feedback
            cur.execute(
                """SELECT * FROM feedback f WHERE f.course_id = %s and f.student_id = (SELECT student_id FROM student WHERE account_id = %s)""", (course_id, current_user.account_id))
            feedback = cur.fetchone()
            if feedback is not None:
                rated = True
        if current_user.account_type == 'teacher':
            # checking if the user is the creator of the course
            cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                        (current_user.account_id, ))
            current_tid = cur.fetchone()['teacher_id']
            if current_tid == course.teacher:
                creator_teacher = True

        contents = []
        # fetching the content
        cur.execute(
            """SELECT * FROM content WHERE course_id = %s""", (course_id, ))
        ls = cur.fetchall()
        for content in ls:
            contents.append(Content(content['content_id'], content['content_title'],
                            content['link'], content['course_id'], content['teacher_id']))
        assessments = []
        # fetching the assessments
        cur.execute(
            """SELECT * FROM assessment WHERE course_id = %s""", (course_id, ))
        ls = cur.fetchall()
        cur.close()
        for assessment in ls:
            assessments.append(Assessment(assessment['assessment_id'], assessment['assessment_title'],
                                          assessment['course_id'], assessment['teacher_id']))
        return render_template('course.html', user=current_user, enrolled=enrolled_student, rated=rated, creator=creator_teacher, course=course, rating=str(rating)[:4], rating_count=rating_count, study_materials=contents, assessments=assessments)


@views.route('/course/<course_id>/enroll')
@login_required
def enroll(course_id):
    if current_user.account_type != 'student':
        return redirect(url_for('views.home'))
    cur = mysql.connection.cursor()
    # fetching the student id of the current user
    cur.execute("""SELECT student_id FROM student WHERE account_id = %s""",
                (current_user.account_id, ))
    student_id = cur.fetchone()[0]
    # inserting the enrollment info
    cur.execute("""INSERT INTO enrollment (student_id, course_id) VALUES (%s, %s)""",
                (student_id, course_id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('views.course', course_id=course_id))


@views.route('/course/<course_id>/feedback', methods=['GET', 'POST'])
@login_required
def feedback(course_id):
    if request.method == 'GET':
        if current_user.account_type == 'teacher':
            # teachers will be redirected
            return redirect(url_for('views.course', course_id=course_id))
        return render_template('feedback.html', user=current_user)
    if request.method == 'POST':
        # fetching info from the form
        star = request.form.get('rate')
        review = request.form.get('review')

        # getting the student id of the current user
        cur = mysql.connection.cursor()
        cur.execute("""SELECT student_id FROM student WHERE account_id = %s""",
                    (current_user.account_id, ))
        student_id = cur.fetchone()[0]
        # inserting into the feedback table
        cur.execute("""INSERT INTO feedback (course_id, student_id, star, review) VALUES (%s, %s, %s, %s)""",
                    (course_id, student_id, star, review))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.course', course_id=course_id))


@views.route('/course/<course_id>/add_content', methods=['POST'])
@login_required
def add_content(course_id):
    if current_user.account_type == 'student':
        return redirect(url_for('views.course', course_id=course_id))

    cur = mysql.connection.cursor()
    # checking if the course exists
    cur.execute("""SELECT course_id FROM course c WHERE c.course_id = %s AND c.teacher_id = (SELECT teacher_id FROM teacher WHERE account_id = %s)""",
                (course_id, current_user.account_id))
    result = cur.fetchone()
    if result is None:
        return redirect(url_for('views.course', course_id=course_id))

    # fetching info from the form
    content_title = request.form.get('content_title')
    link = request.form.get('link')

    # fetching teacher id
    cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                (current_user.account_id, ))
    teacher = cur.fetchone()[0]
    # inserting into the content page
    cur.execute(
        """INSERT INTO content (content_title, link, course_id, teacher_id) VALUES (%s, %s, %s, %s)""", (content_title, link, course_id, teacher))
    mysql.connection.commit()
    # getting the content id of the last inserted content
    cur.execute("""SELECT content_id FROM content WHERE content_title = %s and link = %s and course_id = %s and teacher_id = %s ORDER BY content_id DESC""",
                (content_title, link, course_id, teacher))
    content_id = cur.fetchone()[0]
    cur.close()
    return redirect(url_for('views.content', course_id=course_id, content_id=content_id))


@views.route('course/<course_id>/add_assessment', methods=['POST'])
@login_required
def add_assessment(course_id):
    if current_user.account_type == 'student':
        return redirect(url_for('views.course', course_id=course_id))

    cur = mysql.connection.cursor()
    #  checking if the course exist in db
    cur.execute("""SELECT course_id FROM course c WHERE c.course_id = %s AND c.teacher_id = (SELECT teacher_id FROM teacher WHERE account_id = %s)""",
                (course_id, current_user.account_id))
    result = cur.fetchone()
    if result is None:
        return redirect(url_for('views.course', course_id=course_id))

    assessment_title = request.form.get('assessment_title')

    cur = mysql.connection.cursor()
    # fetching the teacher id
    cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                (current_user.account_id, ))
    teacher = cur.fetchone()[0]
    # inserting into the assessment
    cur.execute(
        """INSERT INTO assessment (assessment_title, course_id, teacher_id) VALUES (%s, %s, %s)""", (assessment_title, course_id, teacher))
    mysql.connection.commit()
    # getting the id of the last inserted assessment
    cur.execute("""SELECT assessment_id FROM assessment WHERE assessment_title = %s and course_id = %s and teacher_id = %s ORDER BY assessment_id DESC""",
                (assessment_title, course_id, teacher))
    assessment_id = cur.fetchone()[0]
    cur.close()
    return redirect(url_for('views.add_questions', course_id=course_id, assessment_id=assessment_id))


@views.route('/course/<course_id>/assessment/<assessment_id>/add_questions', methods=['GET', 'POST'])
@login_required
def add_questions(course_id, assessment_id):
    if current_user.account_type == 'student':
        # redirecting students
        return redirect(url_for('views.course', course_id=course_id))

    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #  checking if the course exists
        cur.execute(
            """SELECT * FROM course WHERE course_id = %s""", (course_id, ))
        result = cur.fetchone()
        if result is None:
            abort(404)

        # creating course object
        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], result['teacher_id'])

        # checking if assessment exists
        cur.execute("""SELECT * FROM assessment WHERE assessment_id = %s""",
                    (assessment_id, ))
        result = cur.fetchone()
        if result is None:
            abort(404)
        # creating assessment object
        assessment = Assessment(
            result['assessment_id'], result['assessment_title'], result['course_id'], result['teacher_id'])

        # fetching questions of the assessment
        cur.execute(
            """SELECT * FROM questions WHERE assessment_id = %s""", (assessment_id, ))
        ls = cur.fetchall()
        # making objects and adding to the list
        questions = []
        for question in ls:
            print(question)
            questions.append(Question(
                assessment_id, question['text'], question['option1'], question['option2'], question['option3'], question['option4'], None))
        cur.close()
        return render_template('question_add.html', user=current_user, course=course, assessment=assessment, questions=questions)

    if request.method == 'POST':
        # fetching info from the form
        text = request.form.get('text')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct = request.form.get('correct')
        # checking if correct answer input was valid
        if correct not in ['1', '2', '3', '4']:
            flash('Please select one of the valid options', 'error')
            return redirect(url_for('views.add_questions', course_id=course_id, assessment_id=assessment_id))

        cur = mysql.connection.cursor()
        # inserting into the assessment table
        cur.execute("""INSERT INTO questions (assessment_id, text, option1, option2, option3, option4, correct) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (assessment_id, text, option1, option2, option3, option4, correct))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.add_questions', course_id=course_id, assessment_id=assessment_id))


@views.route('course/<course_id>/content/<content_id>', methods=['GET', 'POST'])
@login_required
def content(course_id, content_id):
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # checking if course exists in db
        cur.execute(
            """SELECT * FROM course WHERE course_id = %s""", (course_id, ))
        result = cur.fetchone()
        if result is None:
            abort(404)

        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], result['teacher_id'])

        # checking if content exists in db
        cur.execute("""SELECT * FROM content WHERE content_id = %s""",
                    (content_id, ))
        result = cur.fetchone()
        if result is None:
            abort(404)

        # creating content object
        content = Content(result['content_id'], result['content_title'],
                          result['link'], result['course_id'], result['teacher_id'])

        cur.close()

        # comment

        cur = mysql.connection.cursor()
        # fetching all the comments from db
        cur.execute(
            """SELECT * FROM comment WHERE content_id = %s ORDER BY post_time""", (content_id, ))
        ls = cur.fetchall()
        # making objects of comment and adding to the list
        comments = []
        for cid, text, sid, tid, post_time in ls:
            # if the comment was posted by teacher
            if sid is None:
                # fetching name of the commenter
                cur.execute(
                    """SELECT firstname, lastname FROM teacher WHERE teacher_id = %s""", (tid, ))
                name = cur.fetchone()
                name = name[0] + ' ' + name[1]
                comments.append(
                    Comment(cid, text, name, 'Teacher', post_time))
            # if the comment was posted by student
            elif tid is None:
                cur.execute(
                    """SELECT firstname, lastname FROM student WHERE student_id = %s""", (sid, ))
                name = cur.fetchone()
                name = name[0] + ' ' + name[1]
                comments.append(
                    Comment(cid, text, name, 'Student', post_time))
        return render_template('content.html', user=current_user, course=course, study_material=content, comments=comments)

    if request.method == 'POST':
        # fetching info from the form
        text = request.form.get('comment')
        cur = mysql.connection.cursor()
        # fetching student/teacher id from the db
        if current_user.account_type == 'student':
            cur.execute("""SELECT student_id FROM student WHERE account_id = %s""",
                        (current_user.account_id, ))
        elif current_user.account_type == 'teacher':
            cur.execute("""SELECT teacher_id FROM teacher WHERE account_id = %s""",
                        (current_user.account_id, ))

        user_id = cur.fetchone()[0]

        # inserting the comment into db
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
        # if the does not exist in db
        if result is None:
            abort(404)

        course = Course(result['course_id'], result['course_title'],
                        result['category'], result['description'], teacher)

        cur.execute("""SELECT * FROM assessment WHERE assessment_id = %s""",
                    (assessment_id, ))
        result = cur.fetchone()
        # if the assessment exist in db
        if result is None:
            abort(404)

        assessment = Assessment(
            result['assessment_id'], result['assessment_title'], result['course_id'], result['teacher_id'])

        # checking if the student has already attended the assessment
        if current_user.account_type == 'student':
            cur.execute("""SELECT student_id, assessment_id FROM attended_assessment a WHERE a.student_id  = (SELECT student_id FROM student WHERE account_id = %s) AND a.assessment_id = %s""",
                        (current_user.account_id, assessment_id))
            result = cur.fetchone()
            if result is not None:
                # redirecting to result page if the student has attended the assessment already
                return redirect(url_for('views.result', course_id=course_id, assessment_id=assessment_id))

        # fetching the questions of the assessment
        cur.execute(
            """SELECT * FROM questions WHERE assessment_id = %s""", (assessment_id, ))
        ls = cur.fetchall()
        cur.close()
        # making question objects and adding to the list
        questions = []
        for question in ls:
            questions.append(Question(assessment_id, question['text'], question['option1'],
                                      question['option2'], question['option3'], question['option4'], question['correct']))

        return render_template('assessment.html', user=current_user, course=course, assessment=assessment, questions=questions)

    if request.method == 'POST':
        if current_user.account_type != 'student':
            # redirecting to the course page if user is not student
            return redirect(url_for('views.course', course_id=course_id))
        marks = 0
        cur = mysql.connection.cursor()
        # fetching the correct answers from db
        cur.execute(
            """SELECT correct FROM questions WHERE assessment_id = %s""", (assessment_id, ))
        correct_answers = [x[0] for x in cur.fetchall()]
        # matching the answers in the form with correct answers
        for k, correct in zip(request.form.keys(), correct_answers):
            # print(type(request.form[k]), type(correct))
            if int(request.form[k]) == correct:
                marks += 1

        # fetching the student id of current user
        cur.execute("""SELECT student_id FROM student WHERE account_id = %s""",
                    (current_user.account_id, ))
        student_id = cur.fetchone()[0]

        # inserting the result into db
        cur.execute(
            """INSERT INTO attended_assessment (student_id, assessment_id, result) VALUES (%s, %s, %s)""", (student_id, assessment_id, f'{marks}/{len(correct_answers)}'))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('views.result', course_id=course_id, assessment_id=assessment_id))


@views.route('/course/<course_id>/assessment/<assessment_id>/result', methods=['GET'])
@login_required
def result(course_id, assessment_id):
    cur = mysql.connection.cursor()
    # fetching the result from the db
    cur.execute("""SELECT result FROM attended_assessment a WHERE a.assessment_id = %s AND a.student_id = (SELECT student_id FROM student WHERE account_id= %s)""",
                (assessment_id, current_user.account_id))
    marks = cur.fetchone()[0]
    return render_template('result.html', user=current_user, marks=marks)
