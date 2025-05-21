from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "Ramaiah Institute of Technology"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:test1234@localhost/iseTestDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Faculty(db.Model):
    __tablename__ = 'Faculty'
    ID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(50), nullable=False)
    LastName = db.Column(db.String(50))
    DOB = db.Column(db.Date, nullable=False)
    Email = db.Column(db.String(100), nullable=False, unique=True)
    Phone = db.Column(db.String(15), unique=True)
    Phone1 = db.Column(db.String(15), unique=True)
    Department = db.Column(db.String(100), nullable=False)
    Designation = db.Column(db.String(100), nullable=False)
    JoinDate = db.Column(db.Date)
    subjects_taught = db.relationship('Subject', back_populates='assigned_faculty', foreign_keys='Subject.FacultyID', lazy='dynamic')

class AcademicYear(db.Model):
    __tablename__ = 'AcademicYear'
    ID = db.Column(db.Integer, primary_key=True)
    YearStart = db.Column(db.Integer, nullable=False)
    YearEnd = db.Column(db.Integer, nullable=False)
    subjects_in_year = db.relationship('Subject', back_populates='academic_year_info', foreign_keys='Subject.AcademicYearID', lazy='dynamic')

class ActivityType(db.Model):
    __tablename__ = 'ActivityType'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False, unique=True)
    Category = db.Column(db.String(100), nullable=False)

class Activity(db.Model):
    __tablename__ = 'Activity'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Title = db.Column(db.String(150), nullable=False)
    Date = db.Column(db.Date, nullable=False)
    Description = db.Column(db.Text)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ActivityTypeID = db.Column(db.Integer, db.ForeignKey('ActivityType.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

class Subject(db.Model):
    __tablename__ = 'Subject'
    CourseCode = db.Column(db.String(10), primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=False)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='SET NULL', onupdate='CASCADE'))
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='SET NULL', onupdate='CASCADE'))

    assigned_faculty = db.relationship('Faculty', back_populates='subjects_taught', foreign_keys=[FacultyID])
    academic_year_info = db.relationship('AcademicYear', back_populates='subjects_in_year', foreign_keys=[AcademicYearID])

# Routes -- Admin Views
@app.route('/')
def index():
    faculty_count = Faculty.query.count()
    activity_count = Activity.query.count()
    subject_count = Subject.query.count()
    current_year = datetime.now().year

    recent_activities_result = db.session.query(
        Activity.Title,
        Activity.Date,
        ActivityType.Category.label('activity_type'),
        Faculty.FirstName,
        Faculty.LastName
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID) \
     .join(Faculty, Activity.FacultyID == Faculty.ID) \
     .order_by(Activity.Date.desc()).limit(5).all()

    faculty_list = Faculty.query.limit(10).all()

    return render_template('Admin/index.html',
        faculty_count=faculty_count,
        activity_count=activity_count,
        subject_count=subject_count,
        current_year=current_year,
        recent_activities=[{
            'Title': a.Title,
            'Date': a.Date,
            'activity_type': a.activity_type,
            'faculty_name': f"{a.FirstName} {a.LastName}"
        } for a in recent_activities_result],
        faculty_list=faculty_list
    )

@app.route('/faculty')
def faculty():
    faculty_list = Faculty.query.order_by(Faculty.ID).all()
    current_year = datetime.now().year
    return render_template('Admin/faculty.html', faculty_list=faculty_list, current_year=current_year)

@app.route('/add_faculty', methods=['POST'])
def add_faculty():
    new_faculty = Faculty(
        FirstName=request.form.get('first_name'),
        LastName=request.form.get('last_name'),
        DOB=datetime.strptime(request.form.get('dob'), '%Y-%m-%d'),
        Email=request.form.get('email'),
        Phone=request.form.get('phone'),
        Phone1=request.form.get('phone1'),
        Department=request.form.get('department'),
        Designation=request.form.get('designation'),
        JoinDate=datetime.strptime(request.form.get('join_date'), '%Y-%m-%d') if request.form.get('join_date') else None
    )

    db.session.add(new_faculty)
    db.session.commit()
    return redirect(request.referrer or url_for('faculty'))

@app.route('/subjects')
def subjects_view():
    subject_list = db.session.query(Subject).options(
        db.joinedload(Subject.assigned_faculty),
        db.joinedload(Subject.academic_year_info)
    ).order_by(Subject.CourseCode).all()

    faculties = Faculty.query.order_by(Faculty.FirstName).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    current_year = datetime.now().year

    return render_template('Admin/subjects.html',
                           subject_list=subject_list,
                           faculties=faculties,
                           academic_years=academic_years,
                           current_year=current_year)

@app.route('/add_subject', methods=['POST'])
def add_subject():
    new_subject = Subject(
        CourseCode=request.form.get('course_code'),
        SubjectName=request.form.get('subject_name'),
        FacultyID=int(request.form.get('faculty_id')) if request.form.get('faculty_id') and request.form.get('faculty_id').isdigit() else None,
        AcademicYearID=int(request.form.get('academic_year_id')) if request.form.get('academic_year_id') and request.form.get('academic_year_id').isdigit() else None
    )

    try:
        db.session.add(new_subject)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error adding subject: {e}")

    return redirect(url_for('subjects_view'))

@app.route('/appraisals')
def appraisals():
    faculties = Faculty.query.order_by(Faculty.FirstName, Faculty.LastName).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    current_year = datetime.now().year

    return render_template('Admin/appraisals.html',
                           appraisal_list=[],
                           faculties=faculties,
                           academic_years=academic_years,
                           current_year=current_year)

# Routes -- Faculty Views
@app.route('/facultydashboard')
def facultydashboard():
    faculty = Faculty.query.first()
    subject_count = faculty.subjects_taught.count()
    activities_count = Activity.query.filter_by(FacultyID=faculty.ID).count()
    return render_template('Faculty/dashboard.html',
                           faculty=faculty,
                           subject_count=subject_count,
                           activities_count=activities_count)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    faculty = Faculty.query.first()

    if request.method == 'POST':
        faculty.FirstName = request.form['first_name']
        faculty.LastName = request.form['last_name']
        faculty.DOB = request.form['dob']
        faculty.Email = request.form['email']
        faculty.Phone = request.form['phone']
        faculty.Phone1 = request.form['alt_phone']
        faculty.Department = request.form['department']
        faculty.Designation = request.form['designation']
        faculty.JoinDate = request.form['join_date']
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('Faculty/profile.html', faculty=faculty)

@app.route('/subject')
def subjects():
    faculty = Faculty.query.first()
    subjects = faculty.subjects_taught.join(AcademicYear).add_entity(AcademicYear).all()
    return render_template('Faculty/subjects.html', subjects=subjects)

@app.route('/activity')
def activity():
    faculty = Faculty.query.first()
    activities = Activity.query.filter_by(FacultyID=faculty.ID).join(ActivityType).join(AcademicYear).add_columns(
        ActivityType.Name.label('type_name'),
        ActivityType.Category.label('category'),
        AcademicYear.YearStart,
        AcademicYear.YearEnd
    ).all()

    activity_types = ActivityType.query.all()
    academic_years = AcademicYear.query.all()

    return render_template('Faculty/activities.html',
                           activities=activities,
                           activity_types=activity_types,
                           academic_years=academic_years)

@app.route('/add_activity', methods=['POST'])
def add_activity():
    new_activity = Activity(
        Name=request.form['activity_name'],
        Title=request.form['title'],
        Date=request.form['date'],
        Description=request.form.get('description'),
        AcademicYearID=request.form['academic_year'],
        ActivityTypeID=request.form['activity_type'],
        FacultyID=1
    )
    db.session.add(new_activity)
    db.session.commit()
    flash('Activity added successfully!', 'success')
    return redirect(url_for('activity'))

@app.route('/edit_activity/<int:id>', methods=['POST'])
def edit_activity(id):
    activity = Activity.query.get_or_404(id)
    activity.Name = request.form['activity_name']
    activity.Title = request.form['title']
    activity.Date = request.form['date']
    activity.Description = request.form.get('description')
    activity.AcademicYearID = request.form['academic_year']
    activity.ActivityTypeID = request.form['activity_type']
    db.session.commit()
    flash('Activity updated successfully!', 'success')
    return redirect(url_for('activity'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
