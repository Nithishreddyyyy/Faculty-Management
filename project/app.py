from flask import Flask,render_template,request,redirect
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
    JoinDate = db.Column(db.Date)

# 2. AcademicYear
class AcademicYear(db.Model):
    __tablename__ = 'AcademicYear'
    ID = db.Column(db.Integer, primary_key=True)
    YearStart = db.Column(db.Integer, nullable=False)
    YearEnd = db.Column(db.Integer, nullable=False)

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

# 5. PersonalDetails
class PersonalDetails(db.Model):
    __tablename__ = 'PersonalDetails'
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ActivityID = db.Column(db.Integer, db.ForeignKey('Activity.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

# 6. ProfessionalDetails
class ProfessionalDetails(db.Model):
    __tablename__ = 'ProfessionalDetails'
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ActivityID = db.Column(db.Integer, db.ForeignKey('Activity.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

# 7. Appraisal
class Appraisal(db.Model):
    __tablename__ = 'Appraisal'
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Summary = db.Column(db.Text, nullable=False)

# 8. Subject
class Subject(db.Model):
    __tablename__ = 'Subject'
    CourseCode = db.Column(db.String(10), primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=False)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='SET NULL', onupdate='CASCADE'))
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='SET NULL', onupdate='CASCADE'))

# 9. SubjectTaught
class SubjectTaught(db.Model):
    __tablename__ = 'SubjectTaught'
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Semester = db.Column(db.Integer, primary_key=True)

@app.route('/')
def index():
    faculty_count = Faculty.query.count()
    activity_count = Activity.query.count()
    subject_count = Subject.query.count()
    current_year = datetime.now().year

    recent_activities = db.session.query(
        Activity.Title,
        Activity.Date,
        ActivityType.Category.label('activity_type'),
        Faculty.FirstName,
        Faculty.LastName
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID)\
     .join(Faculty, Activity.FacultyID == Faculty.ID)\
     .order_by(Activity.Date.desc()).limit(5).all()

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
        } for a in recent_activities],
        faculty_list=faculty_list
    )

if __name__ == '__main__':
    app.run(debug=True, port=8000)
