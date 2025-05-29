#app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload # Make sure to import joinedload
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
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'faculty':
            abort(403) # Forbidden
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
    # appraisals relation will be added by Appraisal model's backref

class AcademicYear(db.Model):
    __tablename__ = 'AcademicYear'
    ID = db.Column(db.Integer, primary_key=True)
    YearStart = db.Column(db.Integer, nullable=False)
    YearEnd = db.Column(db.Integer, nullable=False)
    subjects_in_year = db.relationship('Subject', back_populates='academic_year_info', foreign_keys='Subject.AcademicYearID', lazy='dynamic')
    activities_in_year = db.relationship('Activity', backref='academic_year_info', lazy='dynamic')
    # appraisals relation will be added by Appraisal model's backref

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
    Date = db.Column(db.Date, nullable=False) # Field name matches general usage
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

# NEW/UPDATED Appraisal Model
class Appraisal(db.Model):
    __tablename__ = 'Appraisal'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID'), nullable=False)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID'), nullable=False)
    Date = db.Column(db.Date, nullable=False)  # Matches template: appraisal_date
    Rating = db.Column(db.String(50))         # Matches template: overall_rating
    Status = db.Column(db.String(50), nullable=False) # Matches template: status
    Comments = db.Column(db.Text, nullable=True) # Matches template: comments (was Summary in ERD)

    faculty = db.relationship('Faculty', backref=db.backref('appraisals', lazy='dynamic'))
    academic_year = db.relationship('AcademicYear', backref=db.backref('appraisals_for_year', lazy='dynamic')) # Adjusted backref name slightly

    def __repr__(self):
        return f'<Appraisal {self.ID} for Faculty {self.FacultyID} on {self.Date}>'

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
        
        if username == 'admin' and password == 'admin': #hard coded the password 
            session['user_id'] = 'admin_user_id_placeholder' # Use a placeholder or actual admin ID if you have an Admins table
            session['user_type'] = 'admin'
            return redirect(url_for('index')) # Redirect to admin dashboard
        
        try:
            faculty_id = int(username) # Assuming username for faculty is their ID
            faculty = db.session.get(Faculty, faculty_id) # Use db.session.get for SQLAlchemy 2.0+
            if faculty and (faculty.Phone == password or (faculty.Phone1 and faculty.Phone1 == password)):
                session['user_id'] = faculty.ID
                session['user_type'] = 'faculty'
                return redirect(url_for('facultydashboard')) # Changed to facultydashboard, removed faculty_id param
            flash('Invalid Faculty ID or Phone Number', 'danger')
        except ValueError:
            flash('Invalid credentials format', 'danger') # More specific error for non-integer faculty ID
        # return redirect(url_for('login')) # Avoid redirect loop on failed login, let template re-render
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin_dashboard') # Renamed from '/' to avoid conflict
@login_required
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
            'faculty_name': f"{r.faculty_first_name} {r.faculty_last_name or ''}".strip(),
            'academic_year': f"{r.academic_year_start}-{r.academic_year_end}"
        })

    return render_template('Admin/index.html',
        faculty_count=faculty_count,
        activity_count=activity_count,
        subject_count=subject_count,
        current_year=current_year,
        recent_activities=formatted_recent_activities,
        faculty_list=Faculty.query.limit(10).all(), # This might not be used in index.html
        activity_types=ActivityType.query.all(),   # For modals or forms on dashboard
        faculties=Faculty.query.all(),             # For modals or forms on dashboard
        academic_years=AcademicYear.query.all()    # For modals or forms on dashboard
    )

@app.route('/faculty')
@login_required
@admin_required
def faculty():
    faculty_list = Faculty.query.order_by(Faculty.ID).all()
    current_year = datetime.now().year
    return render_template('Admin/faculty.html', faculty_list=faculty_list, current_year=current_year, active_page='faculty')

@app.route('/add_faculty', methods=['POST'])
@login_required
@admin_required
def add_faculty():
    try:
        dob_str = request.form.get('dob')
        join_date_str = request.form.get('join_date')

        new_faculty = Faculty(
            FirstName=request.form.get('first_name'),
            LastName=request.form.get('last_name'),
            DOB=datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None,
            Email=request.form.get('email'),
            Phone=request.form.get('phone'),
            Phone1=request.form.get('phone1'),
            Department=request.form.get('department'),
            Designation=request.form.get('designation'),
            JoinDate=datetime.strptime(join_date_str, '%Y-%m-%d').date() if join_date_str else None
        )
        # Basic validation
        if not new_faculty.FirstName or not new_faculty.DOB or not new_faculty.Email or not new_faculty.Department or not new_faculty.Designation:
            flash('First Name, DOB, Email, Department, and Designation are required.', 'danger')
        else:
            db.session.add(new_faculty)
            db.session.commit()
            flash('Faculty added successfully!', 'success')
    except ValueError:
        db.session.rollback()
        flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding faculty: {str(e)}', 'danger')
    return redirect(request.referrer or url_for('faculty'))


@app.route('/subjects')
@login_required
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
        current_year=current_year,
        active_page='subjects'
    )

@app.route('/add_subject', methods=['POST'])
@login_required
@admin_required
def add_subject():
    try:
        new_subject = Subject(
            CourseCode=request.form.get('course_code'),
            SubjectName=request.form.get('subject_name'),
            FacultyID=int(request.form.get('faculty_id')) if request.form.get('faculty_id') and request.form.get('faculty_id').isdigit() else None,
            AcademicYearID=int(request.form.get('academic_year_id')) if request.form.get('academic_year_id') and request.form.get('academic_year_id').isdigit() else None
        )
        if not new_subject.CourseCode or not new_subject.SubjectName:
             flash('Course Code and Subject Name are required.', 'danger')
        else:
            db.session.add(new_subject)
            db.session.commit()
            flash('Subject added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding subject: {str(e)}", 'danger')
    return redirect(url_for('subjects_view'))

@app.route('/activities')
@login_required
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
    ).join(Faculty, Activity.FacultyID == Faculty.ID)\
     .join(ActivityType, Activity.ActivityTypeID == ActivityType.ID)\
     .join(AcademicYear, Activity.AcademicYearID == AcademicYear.ID)\
     .order_by(Activity.Date.desc()).all() # Changed Activity.Date to Activity.Date
    
    activities_list = []
    for result in activities_query:
        activity_obj = result[0]
        activity_obj.faculty_name = f"{result[1]} {result[2] or ''}".strip()
        activity_obj.type_name = result[3]
        activity_obj.type_category = result[4]
        activity_obj.academic_year_str = f"{result[5]} - {result[6]}" # Renamed for clarity
        activities_list.append(activity_obj)
    
    return render_template('Admin/activities.html',
        activities=activities_list,
        faculties=Faculty.query.order_by(Faculty.FirstName).all(),
        activity_types=ActivityType.query.order_by(ActivityType.Name).all(),
        academic_years=AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all(),
        current_year=datetime.now().year,
        active_page='activities'
    )

@app.route('/add_admin_activity', methods=['POST'])
@login_required
@admin_required
def add_admin_activity():
    try:
        date_str = request.form.get('date')
        new_activity = Activity(
            Name=request.form.get('activity_name'),
            Title=request.form.get('title'),
            Date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None, # Changed to .date()
            Description=request.form.get('description'),
            AcademicYearID=request.form.get('academic_year'),
            ActivityTypeID=request.form.get('activity_type'),
            FacultyID=request.form.get('faculty_id')
        )
        if not all([new_activity.Name, new_activity.Title, new_activity.Date, new_activity.AcademicYearID, new_activity.ActivityTypeID, new_activity.FacultyID]):
            flash('All fields except description are required for activity.', 'danger')
        else:
            db.session.add(new_activity)
            db.session.commit()
            flash('Activity added successfully!', 'success')
    except ValueError:
        db.session.rollback()
        flash('Invalid date format for activity.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding activity: {str(e)}', 'danger')
    return redirect(url_for('activities_view'))

@app.route('/edit_admin_activity/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_admin_activity(id):
    try:
        activity = db.session.get(Activity, id) # Use db.session.get
        if not activity:
            flash('Activity not found.', 'danger')
            return redirect(url_for('activities_view'))

        date_str = request.form.get('date')
        activity.Name = request.form.get('activity_name')
        activity.Title = request.form.get('title')
        activity.Date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        activity.Description = request.form.get('description')
        activity.AcademicYearID = request.form.get('academic_year')
        activity.ActivityTypeID = request.form.get('activity_type')
        activity.FacultyID = request.form.get('faculty_id')
        
        if not all([activity.Name, activity.Title, activity.Date, activity.AcademicYearID, activity.ActivityTypeID, activity.FacultyID]):
            flash('All fields except description are required for activity.', 'danger')
        else:
            db.session.commit()
            flash('Activity updated successfully!', 'success')
    except ValueError:
        db.session.rollback()
        flash('Invalid date format for activity update.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating activity: {str(e)}', 'danger')
    return redirect(url_for('activities_view'))

@app.route('/delete_admin_activity/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_admin_activity(id):
    try:
        activity = db.session.get(Activity, id) # Use db.session.get
        if activity:
            db.session.delete(activity)
            db.session.commit()
            flash('Activity deleted successfully!', 'success')
        else:
            flash('Activity not found for deletion.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting activity: {str(e)}', 'danger')
    return redirect(url_for('activities_view'))


@app.route('/appraisals', methods=['GET', 'POST']) # Allow POST requests
@login_required
@admin_required
def appraisals():
    if request.method == 'POST':
        try:
            faculty_id = request.form.get('faculty_id')
            academic_year_id = request.form.get('academic_year_id')
            appraisal_date_str = request.form.get('appraisal_date') # from template name="appraisal_date"
            overall_rating = request.form.get('overall_rating')     # from template name="overall_rating"
            status = request.form.get('status')                     # from template name="status"
            comments = request.form.get('comments')                 # from template name="comments"

            if not all([faculty_id, academic_year_id, appraisal_date_str, overall_rating, status]):
                flash('Faculty, Academic Year, Appraisal Date, Rating, and Status are required.', 'danger')
            else:
                # Convert string date to Python date object
                appraisal_date_obj = datetime.strptime(appraisal_date_str, '%Y-%m-%d').date()
                
                new_appraisal = Appraisal(
                    FacultyID=int(faculty_id),
                    AcademicYearID=int(academic_year_id),
                    Date=appraisal_date_obj,    # Model field: Date
                    Rating=overall_rating,      # Model field: Rating
                    Status=status,              # Model field: Status
                    Comments=comments           # Model field: Comments
                )
                db.session.add(new_appraisal)
                db.session.commit()
                flash('Appraisal added successfully!', 'success')
            return redirect(url_for('appraisals')) # Redirect after POST
        except ValueError: # Catches date parsing errors
            db.session.rollback()
            flash('Invalid date format for appraisal. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('appraisals'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding appraisal: {str(e)}', 'danger')
            return redirect(url_for('appraisals'))

    # GET request logic:
    # Fetch appraisals with eager loading for related faculty and academic year
    appraisal_list = db.session.query(Appraisal)\
        .options(
            joinedload(Appraisal.faculty),
            joinedload(Appraisal.academic_year)
        )\
        .order_by(Appraisal.Date.desc(), Appraisal.ID.desc()).all()

    faculties = Faculty.query.order_by(Faculty.FirstName, Faculty.LastName).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    current_year = datetime.now().year

    return render_template('Admin/appraisals.html',
        appraisal_list=appraisal_list, # Pass the list of Appraisal objects
        faculties=faculties,
        academic_years=academic_years,
        current_year=current_year,
        active_page='appraisals'
    )

# Faculty Routes
@app.route('/faculty_dashboard') # Changed route name slightly for clarity
@login_required
@faculty_required
def facultydashboard():
    faculty_id = session.get('user_id')
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found.", 'danger')
        return redirect(url_for('login'))

    subject_count = faculty.subjects_taught.count()
    
    # Query activities for the faculty
    activities_query = db.session.query(
        Activity.Title,
        Activity.Date, # Activity model's Date field
        ActivityType.Name.label('Type')
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID)\
     .filter(Activity.FacultyID == faculty.ID)\
     .order_by(Activity.Date.desc()).all() # Order by Activity's Date

    color_map = {
        'Workshop': 'bg-primary', 'Seminar': 'bg-success',
        'Research': 'bg-warning', 'Other': 'bg-secondary',
        'Conference': 'bg-info', 'Publication': 'bg-danger' # Added more examples
    }

    activities_list = [{
        'Title': a.Title,
        'Date': a.Date, # Accessing Date directly
        'Type': a.Type,
        'color': color_map.get(a.Type, 'bg-secondary')
    } for a in activities_query]

    activity_type_counts = db.session.query(
        ActivityType.Name,
        db.func.count(Activity.ID).label('count')
    ).join(Activity, Activity.ActivityTypeID == ActivityType.ID)\
     .filter(Activity.FacultyID == faculty.ID)\
     .group_by(ActivityType.Name).all()

    total_activities = sum(item.count for item in activity_type_counts)
    activity_distribution = [{
        'name': name,
        'count': count,
        'percentage': round((count / total_activities) * 100, 1) if total_activities > 0 else 0,
        'color': color_map.get(name, 'bg-secondary') # Use color map for consistency
    } for name, count in activity_type_counts]


    return render_template('Faculty/dashboard.html',
        faculty=faculty,
        subject_count=subject_count,
        activities_count=len(activities_list),
        activity_distribution=activity_distribution,
        activities=activities_list, # Pass the formatted list
        current_faculty_id=faculty.ID
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@faculty_required
def profile():
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found for profile.", 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            faculty.FirstName = request.form['first_name']
            faculty.LastName = request.form.get('last_name') # Use .get for optional fields
            dob_str = request.form['dob']
            faculty.DOB = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else faculty.DOB
            faculty.Email = request.form['email']
            faculty.Phone = request.form['phone']
            faculty.Phone1 = request.form.get('alt_phone')
            faculty.Department = request.form['department']
            faculty.Designation = request.form['designation']
            join_date_str = request.form.get('join_date')
            faculty.JoinDate = datetime.strptime(join_date_str, '%Y-%m-%d').date() if join_date_str else faculty.JoinDate
            
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile'))
        except ValueError:
            db.session.rollback()
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "danger")
    
    return render_template('Faculty/profile.html', faculty=faculty, current_faculty_id=faculty.ID)

@app.route('/subject') # URL for faculty viewing their subjects
@login_required
@faculty_required
def subjects(): # Function name for faculty subjects
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found for subjects.", 'danger')
        return redirect(url_for('login'))

    # subjects_taught relationship on Faculty model returns a query object.
    # We need to join with AcademicYear to get year info.
    subjects_data = faculty.subjects_taught.join(AcademicYear, Subject.AcademicYearID == AcademicYear.ID)\
                                       .add_entity(AcademicYear)\
                                       .all()
    
    # Reformat if necessary, or pass directly if template handles (Subject, AcademicYear) tuples
    formatted_subjects = []
    for subject_obj, academic_year_obj in subjects_data:
        formatted_subjects.append({
            'CourseCode': subject_obj.CourseCode,
            'SubjectName': subject_obj.SubjectName,
            'AcademicYear': f"{academic_year_obj.YearStart}-{academic_year_obj.YearEnd}"
        })

    return render_template('Faculty/subjects.html', subjects=formatted_subjects, current_faculty_id=faculty.ID)


@app.route('/activity') # URL for faculty viewing their activities
@login_required
@faculty_required
def activity(): # Function name for faculty activities
    faculty_id = session['user_id']
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        flash(f"Faculty with ID {faculty_id} not found for activities.", 'danger')
        return redirect(url_for('login'))

    # Eager load related objects
    activities_data = Activity.query.filter_by(FacultyID=faculty.ID)\
        .options(
            joinedload(Activity.activity_type_info),
            joinedload(Activity.academic_year_info)
        )\
        .order_by(Activity.Date.desc()).all() # Order by Activity's Date

    return render_template('Faculty/activities.html', # Check template name, likely Activities.html
        activities=activities_data, # Pass the list of Activity objects
        activity_types=ActivityType.query.all(),
        academic_years=AcademicYear.query.all(),
        current_faculty_id=faculty.ID
    )

@app.route('/add_activity', methods=['POST'])
@login_required
@faculty_required
def add_activity():
    faculty_id = session['user_id']
    try:
        date_str = request.form['date']
        new_activity = Activity(
            Name=request.form['activity_name'],
            Title=request.form['title'],
            Date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None, # Parse date
            Description=request.form.get('description'),
            AcademicYearID=int(request.form['academic_year']),
            ActivityTypeID=int(request.form['activity_type']),
            FacultyID=faculty_id
        )
        if not all([new_activity.Name, new_activity.Title, new_activity.Date, new_activity.AcademicYearID, new_activity.ActivityTypeID]):
            flash('Name, Title, Date, Academic Year, and Activity Type are required.', 'danger')
        else:
            db.session.add(new_activity)
            db.session.commit()
            flash('Activity added successfully!', 'success')
    except ValueError:
        db.session.rollback()
        flash('Invalid data or date format for activity.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding activity: {str(e)}', 'danger')
    return redirect(url_for('activity')) # Redirect to faculty's activity view

@app.route('/edit_activity/<int:id>', methods=['POST'])
@login_required
@faculty_required
def edit_activity(id):
    faculty_id = session['user_id']
    try:
        activity_to_edit = db.session.get(Activity, id) # Use db.session.get
        if not activity_to_edit:
            flash("Activity not found.", 'danger')
            return redirect(url_for('activity'))

        if activity_to_edit.FacultyID != faculty_id:
            flash("You do not have permission to edit this activity.", 'danger')
            return redirect(url_for('activity'))
        
        date_str = request.form['date']
        activity_to_edit.Name = request.form['activity_name']
        activity_to_edit.Title = request.form['title']
        activity_to_edit.Date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        activity_to_edit.Description = request.form.get('description')
        activity_to_edit.AcademicYearID = int(request.form['academic_year'])
        activity_to_edit.ActivityTypeID = int(request.form['activity_type'])
        
        if not all([activity_to_edit.Name, activity_to_edit.Title, activity_to_edit.Date, activity_to_edit.AcademicYearID, activity_to_edit.ActivityTypeID]):
             flash('Name, Title, Date, Academic Year, and Activity Type are required for update.', 'danger')
        else:
            db.session.commit()
            flash('Activity updated successfully!', 'success')
    except ValueError:
        db.session.rollback()
        flash('Invalid data or date format for activity update.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating activity: {str(e)}', 'danger')
    return redirect(url_for('activity'))

# Consider adding a delete_activity route for faculty as well if needed

if __name__ == '__main__':
    # If you have a create_db.py, ensure it's run once to create tables.
    # Example:
    # with app.app_context():
    #     db.create_all() # This should ideally be managed by migrations (e.g., Flask-Migrate)
    app.run(debug=True, port=8000)