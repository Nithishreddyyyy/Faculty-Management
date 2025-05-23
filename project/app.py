#app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "Ramaiah Institute of Technology"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:test1234@localhost/iseTestDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Authentication Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'faculty':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

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
    activities = db.relationship('Activity', backref='faculty_member', lazy='dynamic')

class AcademicYear(db.Model):
    __tablename__ = 'AcademicYear'
    ID = db.Column(db.Integer, primary_key=True)
    YearStart = db.Column(db.Integer, nullable=False)
    YearEnd = db.Column(db.Integer, nullable=False)
    subjects_in_year = db.relationship('Subject', back_populates='academic_year_info', foreign_keys='Subject.AcademicYearID', lazy='dynamic')
    activities_in_year = db.relationship('Activity', backref='academic_year_info', lazy='dynamic')

class ActivityType(db.Model):
    __tablename__ = 'ActivityType'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False, unique=True)
    Category = db.Column(db.String(100), nullable=False)
    activities = db.relationship('Activity', backref='activity_type_info', lazy='dynamic')

class Activity(db.Model):
    __tablename__ = 'Activity'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Title = db.Column(db.String(150), nullable=False)
    Date = db.Column(db.Date, nullable=False)
    Description = db.Column(db.Text)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID'), nullable=False)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID'), nullable=False)
    ActivityTypeID = db.Column(db.Integer, db.ForeignKey('ActivityType.ID'), nullable=False)

class Subject(db.Model):
    __tablename__ = 'Subject'
    CourseCode = db.Column(db.String(10), primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=False)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID'))
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID'))
    assigned_faculty = db.relationship('Faculty', back_populates='subjects_taught', foreign_keys=[FacultyID])
    academic_year_info = db.relationship('AcademicYear', back_populates='subjects_in_year', foreign_keys=[AcademicYearID])

# Template Filter
@app.template_filter('format_date_for_input')
def format_date_for_input(value):
    if value is None:
        return ""
    return value.strftime('%Y-%m-%d')

# Auth Routes
@app.route('/')
def root_redirect_to_login():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            session['user_id'] = 'admin'
            session['user_type'] = 'admin'
            return redirect(url_for('index'))
        
        try:
            faculty_id = int(username)
            faculty = Faculty.query.get(faculty_id)
            if faculty and (faculty.Phone == password or faculty.Phone1 == password):
                session['user_id'] = faculty_id
                session['user_type'] = 'faculty'
                return redirect(url_for('facultydashboard', faculty_id=faculty_id))
            flash('Invalid Faculty ID or Phone Number', 'danger')
        except ValueError:
            flash('Invalid credentials', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin_dashboard') # Renamed from '/' to avoid conflict
@admin_required
def index():
    faculty_count = Faculty.query.count()
    activity_count = Activity.query.count()
    subject_count = Subject.query.count()
    current_year = datetime.now().year

    recent_activities_raw = db.session.query(
        Activity.ID.label('ID'),
        Activity.Name.label('Name'),
        Activity.Title.label('Title'),
        Activity.Date.label('Date'),
        Activity.Description.label('Description'),
        Activity.ActivityTypeID.label('ActivityTypeID'),
        Activity.FacultyID.label('FacultyID'),
        Activity.AcademicYearID.label('AcademicYearID'),
        ActivityType.Name.label('activity_type'),
        Faculty.FirstName.label('faculty_first_name'),
        Faculty.LastName.label('faculty_last_name'),
        AcademicYear.YearStart.label('academic_year_start'),
        AcademicYear.YearEnd.label('academic_year_end')
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID) \
     .join(Faculty, Activity.FacultyID == Faculty.ID) \
     .join(AcademicYear, Activity.AcademicYearID == AcademicYear.ID) \
     .order_by(Activity.Date.desc()).limit(5).all()

    formatted_recent_activities = []
    for r in recent_activities_raw:
        formatted_recent_activities.append({
            'ID': r.ID,
            'Name': r.Name,
            'Title': r.Title,
            'Date': r.Date,
            'Description': r.Description,
            'ActivityTypeID': r.ActivityTypeID,
            'FacultyID': r.FacultyID,
            'AcademicYearID': r.AcademicYearID,
            'activity_type': r.activity_type,
            'faculty_name': f"{r.faculty_first_name} {r.faculty_last_name}",
            'academic_year': f"{r.academic_year_start}-{r.academic_year_end}"
        })

    return render_template('Admin/index.html',
        faculty_count=faculty_count,
        activity_count=activity_count,
        subject_count=subject_count,
        current_year=current_year,
        recent_activities=formatted_recent_activities,
        faculty_list=Faculty.query.limit(10).all(),
        activity_types=ActivityType.query.all(),
        faculties=Faculty.query.all(),
        academic_years=AcademicYear.query.all()
    )

@app.route('/faculty')
@admin_required
def faculty():
    faculty_list = Faculty.query.order_by(Faculty.ID).all()
    current_year = datetime.now().year
    return render_template('Admin/faculty.html', faculty_list=faculty_list, current_year=current_year)

@app.route('/add_faculty', methods=['POST'])
@admin_required
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
@admin_required
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
        current_year=current_year
    )

@app.route('/add_subject', methods=['POST'])
@admin_required
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

@app.route('/activities')
@admin_required
def activities_view():
    activities_query = db.session.query(
        Activity,
        Faculty.FirstName,
        Faculty.LastName,
        ActivityType.Name.label('type_name'),
        ActivityType.Category.label('type_category'),
        AcademicYear.YearStart,
        AcademicYear.YearEnd
    ).join(Faculty).join(ActivityType).join(AcademicYear).order_by(Activity.Date.desc()).all()
    
    activities = []
    for result in activities_query:
        activity = result[0]
        activity.faculty_name = f"{result[1]} {result[2] or ''}"
        activity.type_name = result[3]
        activity.type_category = result[4]
        activity.academic_year = f"{result[5]} - {result[6]}"
        activities.append(activity)
    
    return render_template('Admin/activities.html',
        activities=activities,
        faculties=Faculty.query.order_by(Faculty.FirstName).all(),
        activity_types=ActivityType.query.order_by(ActivityType.Name).all(),
        academic_years=AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all(),
        current_year=datetime.now().year,
        active_page='activities'
    )

@app.route('/add_admin_activity', methods=['POST'])
@admin_required
def add_admin_activity():
    try:
        new_activity = Activity(
            Name=request.form.get('activity_name'),
            Title=request.form.get('title'),
            Date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            Description=request.form.get('description'),
            AcademicYearID=request.form.get('academic_year'),
            ActivityTypeID=request.form.get('activity_type'),
            FacultyID=request.form.get('faculty_id')
        )
        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding activity: {str(e)}', 'danger')
    return redirect(url_for('activities_view'))

@app.route('/edit_admin_activity/<int:id>', methods=['POST'])
@admin_required
def edit_admin_activity(id):
    try:
        activity = Activity.query.get_or_404(id)
        activity.Name = request.form.get('activity_name')
        activity.Title = request.form.get('title')
        activity.Date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        activity.Description = request.form.get('description')
        activity.AcademicYearID = request.form.get('academic_year')
        activity.ActivityTypeID = request.form.get('activity_type')
        activity.FacultyID = request.form.get('faculty_id')
        db.session.commit()
        flash('Activity updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating activity: {str(e)}', 'danger')
    return redirect(url_for('activities_view'))

@app.route('/delete_admin_activity/<int:id>', methods=['POST'])
@admin_required
def delete_admin_activity(id):
    try:
        activity = Activity.query.get_or_404(id)
        db.session.delete(activity)
        db.session.commit()
        flash('Activity deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting activity: {str(e)}', 'danger')
    return redirect(url_for('activities_view'))

@app.route('/appraisals')
@admin_required
def appraisals():
    faculties = Faculty.query.order_by(Faculty.FirstName, Faculty.LastName).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    current_year = datetime.now().year
    return render_template('Admin/appraisals.html',
        appraisal_list=[],
        faculties=faculties,
        academic_years=academic_years,
        current_year=current_year
    )

# Faculty Routes
@app.route('/facultydashboard')
@faculty_required
def facultydashboard():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found.", 'danger')
        return redirect(url_for('login'))

    subject_count = faculty.subjects_taught.count()
    activities_query = db.session.query(
        Activity.Title,
        Activity.Date,
        ActivityType.Name.label('Type')
    ).join(ActivityType).filter(Activity.FacultyID == faculty.ID).all()

    color_map = {
        'Workshop': 'bg-primary',
        'Seminar': 'bg-success',
        'Research': 'bg-warning',
        'Other': 'bg-secondary'
    }

    activities = [{
        'Title': a.Title,
        'Date': a.Date,
        'Type': a.Type,
        'color': color_map.get(a.Type, 'bg-secondary')
    } for a in activities_query]

    activity_type_counts = db.session.query(
        ActivityType.Name,
        db.func.count(Activity.ID)
    ).join(Activity).filter(Activity.FacultyID == faculty.ID).group_by(ActivityType.Name).all()

    total = sum(count for _, count in activity_type_counts)
    activity_distribution = [{
        'name': name,
        'count': count,
        'percentage': round((count / total) * 100, 1) if total > 0 else 0,
        'color': 'bg-info' if i % 3 == 0 else 'bg-success' if i % 3 == 1 else 'bg-warning'
    } for i, (name, count) in enumerate(activity_type_counts)]

    return render_template('Faculty/dashboard.html',
        faculty=faculty,
        subject_count=subject_count,
        activities_count=len(activities),
        activity_distribution=activity_distribution,
        activities=activities,
        current_faculty_id=faculty.ID
    )

@app.route('/profile', methods=['GET', 'POST'])
@faculty_required
def profile():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found for profile.", 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        faculty.FirstName = request.form['first_name']
        faculty.LastName = request.form['last_name']
        faculty.DOB = datetime.strptime(request.form['dob'], '%Y-%m-%d')
        faculty.Email = request.form['email']
        faculty.Phone = request.form['phone']
        faculty.Phone1 = request.form['alt_phone']
        faculty.Department = request.form['department']
        faculty.Designation = request.form['designation']
        faculty.JoinDate = datetime.strptime(request.form['join_date'], '%Y-%m-%d') if request.form['join_date'] else None
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))
    
    return render_template('Faculty/profile.html', faculty=faculty, current_faculty_id=faculty.ID)

@app.route('/subject')
@faculty_required
def subjects():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found for subjects.", 'danger')
        return redirect(url_for('login'))

    subjects = faculty.subjects_taught.join(AcademicYear).add_entity(AcademicYear).all()
    return render_template('Faculty/subjects.html', subjects=subjects, current_faculty_id=faculty.ID)

@app.route('/activity')
@faculty_required
def activity():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found for activities.", 'danger')
        return redirect(url_for('login'))

    activities = Activity.query.filter_by(FacultyID=faculty.ID).join(ActivityType).join(AcademicYear).add_columns(
        ActivityType.Name.label('type_name'),
        ActivityType.Category.label('category'),
        AcademicYear.YearStart,
        AcademicYear.YearEnd
    ).all()

    return render_template('Faculty/activities.html',
        activities=activities,
        activity_types=ActivityType.query.all(),
        academic_years=AcademicYear.query.all(),
        current_faculty_id=faculty.ID
    )

@app.route('/add_activity', methods=['POST'])
@faculty_required
def add_activity():
    faculty_id = session['user_id']
    try:
        new_activity = Activity(
            Name=request.form['activity_name'],
            Title=request.form['title'],
            Date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            Description=request.form.get('description'),
            AcademicYearID=int(request.form['academic_year']),
            ActivityTypeID=int(request.form['activity_type']),
            FacultyID=faculty_id
        )
        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding activity: {str(e)}', 'danger')
    return redirect(url_for('activity'))

@app.route('/edit_activity/<int:id>', methods=['POST'])
@faculty_required
def edit_activity(id):
    faculty_id = session['user_id']
    try:
        activity = Activity.query.get_or_404(id)
        if activity.FacultyID != faculty_id:
            flash("You do not have permission to edit this activity.", 'danger')
            return redirect(url_for('activity'))

        activity.Name = request.form['activity_name']
        activity.Title = request.form['title']
        activity.Date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        activity.Description = request.form.get('description')
        activity.AcademicYearID = int(request.form['academic_year'])
        activity.ActivityTypeID = int(request.form['activity_type'])
        db.session.commit()
        flash('Activity updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating activity: {str(e)}', 'danger')
    return redirect(url_for('activity'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)