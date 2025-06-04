#app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "Ramaiah Institute of Technology"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:test1234@localhost/iseTestDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Authentication Decorators (No changes) ---
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

# --- Models ---
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

class Appraisal(db.Model):
    __tablename__ = 'Appraisal'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID'), nullable=False)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID'), nullable=False)
    Date = db.Column(db.Date, nullable=False)
    Rating = db.Column(db.String(50))
    Status = db.Column(db.String(50), nullable=False)
    Comments = db.Column(db.Text, nullable=True)

    faculty = db.relationship('Faculty', backref=db.backref('appraisals', lazy='select'))
    academic_year = db.relationship('AcademicYear', backref=db.backref('appraisals_for_year', lazy='select'))

    def __repr__(self):
        return f'<Appraisal {self.ID} for Faculty {self.FacultyID} on {self.Date}>'
    
    def to_dict(self): # Enhanced for view modal
        faculty_name = f"{self.faculty.FirstName} {self.faculty.LastName or ''}".strip() if self.faculty else "N/A"
        academic_year_str = f"{self.academic_year.YearStart} - {self.academic_year.YearEnd}" if self.academic_year else "N/A"
        department = self.faculty.Department if self.faculty else "N/A"
        designation = self.faculty.Designation if self.faculty else "N/A"

        return {
            'id': self.ID,
            'faculty_id': self.FacultyID, # For edit form
            'faculty_name': faculty_name, # For view
            'department': department, # For view
            'designation': designation, # For view
            'academic_year_id': self.AcademicYearID, # For edit form
            'academic_year_str': academic_year_str, # For view
            'date': self.Date.strftime('%Y-%m-%d') if self.Date else None, # For edit form
            'date_formatted': self.Date.strftime('%d %B %Y') if self.Date else 'N/A', # For view display
            'rating': self.Rating,
            'status': self.Status,
            'comments': self.Comments
        }

# --- Template Filter (No changes) ---
@app.template_filter('format_date_for_input')
def format_date_for_input(value):
    if value is None:
        return ""
    return value.strftime('%Y-%m-%d')

# --- Auth Routes (No changes) ---
@app.route('/')
def root_redirect_to_login():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            session['user_id'] = 'admin_user_id_placeholder'
            session['user_type'] = 'admin'
            return redirect(url_for('index'))
        try:
            faculty_id = int(username)
            faculty = db.session.get(Faculty, faculty_id)
            if faculty and (faculty.Phone == password or (faculty.Phone1 and faculty.Phone1 == password)):
                session['user_id'] = faculty.ID
                session['user_type'] = 'faculty'
                return redirect(url_for('facultydashboard'))
            flash('Invalid Faculty ID or Phone Number', 'danger')
        except ValueError:
            flash('Invalid credentials format', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Admin Routes ---
@app.route('/admin_dashboard')
@login_required
@admin_required
def index():
    faculty_count = Faculty.query.count()
    activity_count = Activity.query.count()
    subject_count = Subject.query.count()
    
    # Fetch all faculties for the list
    all_faculties = Faculty.query.order_by(Faculty.FirstName).all()

    recent_activities_raw = db.session.query(
        Activity.ID.label('ID'), Activity.Name.label('Name'), Activity.Title.label('Title'),
        Activity.Date.label('Date'), Activity.Description.label('Description'),
        Activity.ActivityTypeID.label('ActivityTypeID'), Activity.FacultyID.label('FacultyID'),
        Activity.AcademicYearID.label('AcademicYearID'), ActivityType.Name.label('activity_type'),
        Faculty.FirstName.label('faculty_first_name'), Faculty.LastName.label('faculty_last_name'),
        AcademicYear.YearStart.label('academic_year_start'), AcademicYear.YearEnd.label('academic_year_end')
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID) \
     .join(Faculty, Activity.FacultyID == Faculty.ID) \
     .join(AcademicYear, Activity.AcademicYearID == AcademicYear.ID) \
     .order_by(Activity.Date.desc()).limit(5).all()
    formatted_recent_activities = [{
        'ID': r.ID, 'Name': r.Name, 'Title': r.Title, 'Date': r.Date, 'Description': r.Description,
        'ActivityTypeID': r.ActivityTypeID, 'FacultyID': r.FacultyID, 'AcademicYearID': r.AcademicYearID,
        'activity_type': r.activity_type, 'faculty_name': f"{r.faculty_first_name} {r.faculty_last_name or ''}".strip(),
        'academic_year': f"{r.academic_year_start}-{r.academic_year_end}"
    } for r in recent_activities_raw]
    return render_template('Admin/index.html',
        faculty_count=faculty_count, activity_count=activity_count, subject_count=subject_count,
        current_year=datetime.now().year, recent_activities=formatted_recent_activities,
        faculties=all_faculties, academic_years=AcademicYear.query.all(), activity_types=ActivityType.query.all()
    )

@app.route('/faculty')
@login_required
@admin_required
def faculty():
    faculty_list = Faculty.query.order_by(Faculty.ID).all()
    return render_template('Admin/faculty.html', faculty_list=faculty_list, active_page='faculty')

@app.route('/add_faculty', methods=['POST'])
@login_required
@admin_required
def add_faculty():
    try:
        dob_str = request.form.get('dob')
        join_date_str = request.form.get('join_date')
        new_faculty = Faculty(
            FirstName=request.form.get('first_name'), LastName=request.form.get('last_name'),
            DOB=datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None,
            Email=request.form.get('email'), Phone=request.form.get('phone'), Phone1=request.form.get('phone1'),
            Department=request.form.get('department'), Designation=request.form.get('designation'),
            JoinDate=datetime.strptime(join_date_str, '%Y-%m-%d').date() if join_date_str else None
        )
        if not all([new_faculty.FirstName, new_faculty.DOB, new_faculty.Email, new_faculty.Department, new_faculty.Designation]):
            flash('First Name, DOB, Email, Department, and Designation are required.', 'danger')
        else:
            db.session.add(new_faculty); db.session.commit(); flash('Faculty added successfully!', 'success')
    except ValueError: flash('Invalid date format. Please use YYYY-MM-DD.', 'danger'); db.session.rollback()
    except Exception as e: flash(f'Error adding faculty: {str(e)}', 'danger'); db.session.rollback()
    return redirect(request.referrer or url_for('faculty'))

@app.route('/subjects')
@login_required
@admin_required
def subjects_view():
    subject_list = db.session.query(Subject).options(joinedload(Subject.assigned_faculty), joinedload(Subject.academic_year_info)).order_by(Subject.CourseCode).all()
    return render_template('Admin/subjects.html',
        subject_list=subject_list, faculties=Faculty.query.order_by(Faculty.FirstName).all(),
        academic_years=AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all(), active_page='subjects'
    )

@app.route('/add_subject', methods=['POST'])
@login_required
@admin_required
def add_subject():
    try:
        new_subject = Subject(
            CourseCode=request.form.get('course_code'), SubjectName=request.form.get('subject_name'),
            FacultyID=int(request.form.get('faculty_id')) if request.form.get('faculty_id', '').isdigit() else None,
            AcademicYearID=int(request.form.get('academic_year_id')) if request.form.get('academic_year_id', '').isdigit() else None
        )
        if not new_subject.CourseCode or not new_subject.SubjectName:
             flash('Course Code and Subject Name are required.', 'danger')
        else:
            db.session.add(new_subject); db.session.commit(); flash('Subject added successfully!', 'success')
    except Exception as e: flash(f"Error adding subject: {str(e)}", 'danger'); db.session.rollback()
    return redirect(url_for('subjects_view'))

@app.route('/activities')
@login_required
@admin_required
def activities_view():
    activities_query = db.session.query(Activity, Faculty.FirstName, Faculty.LastName, ActivityType.Name.label('type_name'), ActivityType.Category.label('type_category'), AcademicYear.YearStart, AcademicYear.YearEnd)\
        .join(Faculty, Activity.FacultyID == Faculty.ID).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID).join(AcademicYear, Activity.AcademicYearID == AcademicYear.ID).order_by(Activity.Date.desc()).all()
    activities_list = []
    for res in activities_query:
        act, f_name, l_name, type_n, type_c, yr_s, yr_e = res
        act.faculty_name = f"{f_name} {l_name or ''}".strip()
        act.type_name = type_n; act.type_category = type_c
        act.academic_year_str = f"{yr_s} - {yr_e}"
        activities_list.append(act)
    return render_template('Admin/activities.html',
        activities=activities_list, faculties=Faculty.query.order_by(Faculty.FirstName).all(),
        activity_types=ActivityType.query.order_by(ActivityType.Name).all(), academic_years=AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all(), active_page='activities'
    )

@app.route('/add_admin_activity', methods=['POST'])
@login_required
@admin_required
def add_admin_activity():
    try:
        date_str = request.form.get('date')
        new_activity = Activity(
            Name=request.form.get('activity_name'), Title=request.form.get('title'),
            Date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None,
            Description=request.form.get('description'), AcademicYearID=request.form.get('academic_year'),
            ActivityTypeID=request.form.get('activity_type'), FacultyID=request.form.get('faculty_id')
        )
        if not all([new_activity.Name, new_activity.Title, new_activity.Date, new_activity.AcademicYearID, new_activity.ActivityTypeID, new_activity.FacultyID]):
            flash('All fields except description are required for activity.', 'danger')
        else:
            db.session.add(new_activity); db.session.commit(); flash('Activity added successfully!', 'success')
    except ValueError: flash('Invalid date format for activity.', 'danger'); db.session.rollback()
    except Exception as e: flash(f'Error adding activity: {str(e)}', 'danger'); db.session.rollback()
    return redirect(url_for('activities_view'))

@app.route('/edit_admin_activity/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_admin_activity(id):
    try:
        activity = db.session.get(Activity, id)
        if not activity: flash('Activity not found.', 'danger'); return redirect(url_for('activities_view'))
        date_str = request.form.get('date')
        activity.Name = request.form.get('activity_name'); activity.Title = request.form.get('title')
        activity.Date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        activity.Description = request.form.get('description'); activity.AcademicYearID = request.form.get('academic_year')
        activity.ActivityTypeID = request.form.get('activity_type'); activity.FacultyID = request.form.get('faculty_id')
        if not all([activity.Name, activity.Title, activity.Date, activity.AcademicYearID, activity.ActivityTypeID, activity.FacultyID]):
            flash('All fields except description are required for activity.', 'danger')
        else:
            db.session.commit(); flash('Activity updated successfully!', 'success')
    except ValueError: flash('Invalid date format for activity update.', 'danger'); db.session.rollback()
    except Exception as e: flash(f'Error updating activity: {str(e)}', 'danger'); db.session.rollback()
    return redirect(url_for('activities_view'))

@app.route('/delete_admin_activity/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_admin_activity(id):
    try:
        activity = db.session.get(Activity, id)
        if activity: db.session.delete(activity); db.session.commit(); flash('Activity deleted successfully!', 'success')
        else: flash('Activity not found for deletion.', 'danger')
    except Exception as e: flash(f'Error deleting activity: {str(e)}', 'danger'); db.session.rollback()
    return redirect(url_for('activities_view'))

# --- Appraisal Routes ---
@app.route('/appraisals', methods=['GET', 'POST'])
@login_required
@admin_required
def appraisals():
    if request.method == 'POST': # Handles ADDING a new appraisal
        try:
            faculty_id = request.form.get('faculty_id')
            academic_year_id = request.form.get('academic_year_id')
            appraisal_date_str = request.form.get('appraisal_date')
            overall_rating = request.form.get('overall_rating')
            status = request.form.get('status')
            comments = request.form.get('comments')

            if not all([faculty_id, academic_year_id, appraisal_date_str, overall_rating, status]):
                flash('Faculty, Academic Year, Appraisal Date, Rating, and Status are required.', 'danger')
            else:
                appraisal_date_obj = datetime.strptime(appraisal_date_str, '%Y-%m-%d').date()
                new_appraisal = Appraisal(
                    FacultyID=int(faculty_id), AcademicYearID=int(academic_year_id),
                    Date=appraisal_date_obj, Rating=overall_rating, Status=status, Comments=comments
                )
                db.session.add(new_appraisal); db.session.commit(); flash('Appraisal added successfully!', 'success')
        except ValueError: flash('Invalid date format for appraisal. Please use YYYY-MM-DD.', 'danger'); db.session.rollback()
        except Exception as e: flash(f'Error adding appraisal: {str(e)}', 'danger'); db.session.rollback()
        return redirect(url_for('appraisals'))

    appraisal_list = db.session.query(Appraisal).options(joinedload(Appraisal.faculty), joinedload(Appraisal.academic_year)).order_by(Appraisal.Date.desc(), Appraisal.ID.desc()).all()
    faculties = Faculty.query.order_by(Faculty.FirstName, Faculty.LastName).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    return render_template('Admin/appraisals.html',
        appraisal_list=appraisal_list, faculties=faculties, academic_years=academic_years, active_page='appraisals'
    )

# REMOVED: /appraisal/view/<int:id> route as view is now a modal

@app.route('/appraisal/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_appraisal(id):
    appraisal_to_edit = db.session.get(Appraisal, id)
    if not appraisal_to_edit:
        flash('Appraisal not found.', 'danger'); return redirect(url_for('appraisals'))
    try:
        appraisal_to_edit.FacultyID = int(request.form.get('edit_faculty_id'))
        appraisal_to_edit.AcademicYearID = int(request.form.get('edit_academic_year_id'))
        appraisal_date_str = request.form.get('edit_appraisal_date')
        appraisal_to_edit.Date = datetime.strptime(appraisal_date_str, '%Y-%m-%d').date() if appraisal_date_str else None
        appraisal_to_edit.Rating = request.form.get('edit_overall_rating')
        appraisal_to_edit.Status = request.form.get('edit_status')
        appraisal_to_edit.Comments = request.form.get('edit_comments')

        if not all([appraisal_to_edit.FacultyID, appraisal_to_edit.AcademicYearID, appraisal_to_edit.Date, appraisal_to_edit.Rating, appraisal_to_edit.Status]):
            flash('Faculty, Academic Year, Appraisal Date, Rating, and Status are required for update.', 'danger')
        else:
            db.session.commit(); flash('Appraisal updated successfully!', 'success')
    except ValueError: flash('Invalid data or date format for appraisal update.', 'danger'); db.session.rollback()
    except Exception as e: flash(f'Error updating appraisal: {str(e)}', 'danger'); db.session.rollback()
    return redirect(url_for('appraisals'))

@app.route('/appraisal/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_appraisal(id):
    appraisal_to_delete = db.session.get(Appraisal, id)
    if appraisal_to_delete:
        try:
            db.session.delete(appraisal_to_delete); db.session.commit(); flash('Appraisal deleted successfully!', 'success')
        except Exception as e: flash(f'Error deleting appraisal: {str(e)}', 'danger'); db.session.rollback()
    else:
        flash('Appraisal not found.', 'danger')
    return redirect(url_for('appraisals'))

@app.route('/appraisal/get_data/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_appraisal_data(id):
    appraisal = db.session.query(Appraisal).options(
        joinedload(Appraisal.faculty),
        joinedload(Appraisal.academic_year)
    ).filter(Appraisal.ID == id).first() # Use .first() as get doesn't support options directly

    if appraisal:
        return jsonify(appraisal.to_dict())
    return jsonify({'error': 'Appraisal not found'}), 404

# --- Faculty Routes (No changes) ---
@app.route('/faculty_dashboard')
@login_required
@faculty_required
def facultydashboard():
    faculty_id = session.get('user_id')
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty: flash(f"Faculty with ID {faculty_id} not found.", 'danger'); return redirect(url_for('login'))
    subject_count = faculty.subjects_taught.count()
    activities_query = db.session.query(Activity.Title, Activity.Date, ActivityType.Name.label('Type'))\
        .join(ActivityType, Activity.ActivityTypeID == ActivityType.ID).filter(Activity.FacultyID == faculty.ID).order_by(Activity.Date.desc()).all()
    color_map = {'Workshop': 'bg-primary', 'Seminar': 'bg-success', 'Research': 'bg-warning', 'Other': 'bg-secondary', 'Conference': 'bg-info', 'Publication': 'bg-danger'}
    activities_list = [{'Title': a.Title, 'Date': a.Date, 'Type': a.Type, 'color': color_map.get(a.Type, 'bg-secondary')} for a in activities_query]
    activity_type_counts = db.session.query(ActivityType.Name, db.func.count(Activity.ID).label('count'))\
        .join(Activity, Activity.ActivityTypeID == ActivityType.ID).filter(Activity.FacultyID == faculty.ID).group_by(ActivityType.Name).all()
    total_activities = sum(item.count for item in activity_type_counts)
    academic_years = db.session.query(AcademicYear).order_by(AcademicYear.YearStart.desc()).all()
    activity_types = db.session.query(ActivityType).order_by(ActivityType.Name).all()

    activity_distribution = [{'name': name, 'count': count, 'percentage': round((total_activities and (count / total_activities) * 100) or 0, 1), 'color': color_map.get(name, 'bg-secondary')} for name, count in activity_type_counts]
    return render_template('Faculty/dashboard.html',
        faculty=faculty, subject_count=subject_count, activities_count=len(activities_list),
        activity_distribution=activity_distribution, activities=activities_list, current_faculty_id=faculty.ID,
                           academic_years=academic_years,
                           activity_types=activity_types
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@faculty_required
def profile():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty: flash(f"Faculty with ID {faculty_id} not found for profile.", 'danger'); return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            faculty.FirstName = request.form['first_name']; faculty.LastName = request.form.get('last_name')
            dob_str = request.form['dob']; faculty.DOB = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else faculty.DOB
            faculty.Email = request.form['email']; faculty.Phone = request.form['phone']; faculty.Phone1 = request.form.get('alt_phone')
            faculty.Department = request.form['department']; faculty.Designation = request.form['designation']
            join_date_str = request.form.get('join_date'); faculty.JoinDate = datetime.strptime(join_date_str, '%Y-%m-%d').date() if join_date_str else faculty.JoinDate
            db.session.commit(); flash("Profile updated successfully!", "success"); return redirect(url_for('profile'))
        except ValueError: db.session.rollback(); flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
        except Exception as e: db.session.rollback(); flash(f"Error updating profile: {str(e)}", "danger")
    return render_template('Faculty/profile.html', faculty=faculty, current_faculty_id=faculty.ID)

@app.route('/subject')
@login_required
@faculty_required
def subjects():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty: flash(f"Faculty with ID {faculty_id} not found for subjects.", 'danger'); return redirect(url_for('login'))
    subjects_data = faculty.subjects_taught.join(AcademicYear, Subject.AcademicYearID == AcademicYear.ID).add_entity(AcademicYear).all()
    formatted_subjects = [{'CourseCode': s.CourseCode, 'SubjectName': s.SubjectName, 'AcademicYear': f"{ay.YearStart}-{ay.YearEnd}"} for s, ay in subjects_data]
    return render_template('Faculty/subjects.html', subjects=formatted_subjects, current_faculty_id=faculty.ID)

@app.route('/activity')
@login_required
@faculty_required
def activity():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty: flash(f"Faculty with ID {faculty_id} not found for activities.", 'danger'); return redirect(url_for('login'))
    activities_data = Activity.query.filter_by(FacultyID=faculty.ID).options(joinedload(Activity.activity_type_info), joinedload(Activity.academic_year_info)).order_by(Activity.Date.desc()).all()
    return render_template('Faculty/activities.html', activities=activities_data, activity_types=ActivityType.query.all(), academic_years=AcademicYear.query.all(), current_faculty_id=faculty.ID)

@app.route('/add_activity', methods=['POST'])
@login_required
@faculty_required
def add_activity():
    faculty_id = session['user_id']
    try:
        date_str = request.form['date']
        new_activity = Activity(
            Name=request.form['activity_name'], Title=request.form['title'],
            Date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None,
            Description=request.form.get('description'), AcademicYearID=int(request.form['academic_year']),
            ActivityTypeID=int(request.form['activity_type']), FacultyID=faculty_id
        )
        if not all([new_activity.Name, new_activity.Title, new_activity.Date, new_activity.AcademicYearID, new_activity.ActivityTypeID]):
            flash('Name, Title, Date, Academic Year, and Activity Type are required.', 'danger')
        else: db.session.add(new_activity); db.session.commit(); flash('Activity added successfully!', 'success')
    except ValueError: db.session.rollback(); flash('Invalid data or date format for activity.', 'danger')
    except Exception as e: db.session.rollback(); flash(f'Error adding activity: {str(e)}', 'danger')
    return redirect(url_for('activity'))

@app.route('/edit_activity/<int:id>', methods=['POST'])
@login_required
@faculty_required
def edit_activity(id):
    faculty_id = session['user_id']
    try:
        activity_to_edit = db.session.get(Activity, id)
        if not activity_to_edit: flash("Activity not found.", 'danger'); return redirect(url_for('activity'))
        if activity_to_edit.FacultyID != faculty_id: flash("You do not have permission to edit this activity.", 'danger'); return redirect(url_for('activity'))
        date_str = request.form['date']
        activity_to_edit.Name = request.form['activity_name']; activity_to_edit.Title = request.form['title']
        activity_to_edit.Date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        activity_to_edit.Description = request.form.get('description')
        activity_to_edit.AcademicYearID = int(request.form['academic_year']); activity_to_edit.ActivityTypeID = int(request.form['activity_type'])
        if not all([activity_to_edit.Name, activity_to_edit.Title, activity_to_edit.Date, activity_to_edit.AcademicYearID, activity_to_edit.ActivityTypeID]):
             flash('Name, Title, Date, Academic Year, and Activity Type are required for update.', 'danger')
        else: db.session.commit(); flash('Activity updated successfully!', 'success')
    except ValueError: db.session.rollback(); flash('Invalid data or date format for activity update.', 'danger')
    except Exception as e: db.session.rollback(); flash(f'Error updating activity: {str(e)}', 'danger')
    return redirect(url_for('activity'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)