from flask import Flask,render_template,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:test1234@localhost/iseTestDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. Faculty
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
    JoinDate = db.Column(db.Date)    # 'subjects_taught' will be a list of Subject objects.
    subjects_taught = db.relationship(
        'Subject',
        back_populates='assigned_faculty',
        foreign_keys='Subject.FacultyID',
        lazy='dynamic' 
    )

# 2. AcademicYear
class AcademicYear(db.Model):
    __tablename__ = 'AcademicYear'
    ID = db.Column(db.Integer, primary_key=True)
    YearStart = db.Column(db.Integer, nullable=False)
    YearEnd = db.Column(db.Integer, nullable=False)

    subjects_in_year = db.relationship(
        'Subject',
        back_populates='academic_year_info',
        foreign_keys='Subject.AcademicYearID', # Explicitly name the FK column in the Subject model
        lazy='dynamic'
    )

# 3. ActivityType 
class ActivityType(db.Model):
    __tablename__ = 'ActivityType'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False, unique=True)
    Category = db.Column(db.String(100), nullable=False)

# 4. Activity 
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

# 8. Subject (UPDATED)
class Subject(db.Model):
    __tablename__ = 'Subject'
    CourseCode = db.Column(db.String(10), primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=False)
    
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='SET NULL', onupdate='CASCADE'))
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='SET NULL', onupdate='CASCADE'))


    assigned_faculty = db.relationship(
        'Faculty',
        back_populates='subjects_taught',
        foreign_keys=[FacultyID] 
    )

    academic_year_info = db.relationship(
        'AcademicYear',
        back_populates='subjects_in_year',
        foreign_keys=[AcademicYearID]
    )


# -- Application Routes --

@app.route('/')
def index():
    faculty_count = Faculty.query.count()
    activity_count = Activity.query.count()
    subject_count = Subject.query.count()
    current_year = datetime.now().year

    recent_activities_query = db.session.query(
        Activity.Title,
        Activity.Date,
        ActivityType.Category.label('activity_type'), 
        Faculty.FirstName,                          
        Faculty.LastName
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID)\
     .join(Faculty, Activity.FacultyID == Faculty.ID)\
     .order_by(Activity.Date.desc()).limit(5)
    recent_activities_result = recent_activities_query.all()


    faculty_list = Faculty.query.limit(10).all()

    return render_template('index.html',
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
    return render_template('faculty.html', faculty_list=faculty_list, current_year=current_year)

@app.route('/add_faculty', methods=['POST'])
def add_faculty():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    dob = request.form.get('dob')
    email = request.form.get('email')
    phone = request.form.get('phone')
    phone1 = request.form.get('phone1') 
    department = request.form.get('department')
    designation = request.form.get('designation')
    join_date = request.form.get('join_date')

    new_faculty = Faculty(
        FirstName=first_name,
        LastName=last_name,
        DOB=datetime.strptime(dob, '%Y-%m-%d'),
        Email=email,
        Phone=phone,
        Phone1=phone1,
        Department=department,
        Designation=designation,
        JoinDate=datetime.strptime(join_date, '%Y-%m-%d') if join_date else None
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
    
    return render_template('subjects.html', 
                           subject_list=subject_list, 
                           faculties=faculties,
                           academic_years=academic_years,
                           current_year=current_year)

@app.route('/add_subject', methods=['POST'])
def add_subject():
    course_code = request.form.get('course_code')
    subject_name = request.form.get('subject_name')
    faculty_id = request.form.get('faculty_id')
    academic_year_id = request.form.get('academic_year_id')

    if not course_code or not subject_name:
        return redirect(request.referrer or url_for('subjects_view'))

    new_subject = Subject(
        CourseCode=course_code,
        SubjectName=subject_name,
        FacultyID=int(faculty_id) if faculty_id and faculty_id.isdigit() else None,
        AcademicYearID=int(academic_year_id) if academic_year_id and academic_year_id.isdigit() else None
    )
    
    try:
        db.session.add(new_subject)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error adding subject: {e}") 
    
    return redirect(url_for('subjects_view'))


if __name__ == '__main__':
    app.run(debug=True, port=8000)