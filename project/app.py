#app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "Ramaiah Institute of Technology" # Should be a strong, random secret in production
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
    Phone = db.Column(db.String(15), unique=True, nullable=True)
    Phone1 = db.Column(db.String(15), unique=True, nullable=True)
    Department = db.Column(db.String(100), nullable=False)
    Designation = db.Column(db.String(100), nullable=False)
    JoinDate = db.Column(db.Date, nullable=True)
    subjects_taught = db.relationship('Subject', back_populates='assigned_faculty', foreign_keys='Subject.FacultyID', lazy='dynamic')
    activities = db.relationship('Activity', back_populates='faculty_member', foreign_keys='Activity.FacultyID', lazy='dynamic')


    def to_dict(self):
        return {
            'ID': self.ID,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'DOB': self.DOB.strftime('%Y-%m-%d') if self.DOB else None,
            'Email': self.Email,
            'Phone': self.Phone,
            'Phone1': self.Phone1,
            'Department': self.Department,
            'Designation': self.Designation,
            'JoinDate': self.JoinDate.strftime('%Y-%m-%d') if self.JoinDate else None,
            'FullName': f"{self.FirstName} {self.LastName if self.LastName else ''}".strip()
        }

class AcademicYear(db.Model):
    __tablename__ = 'AcademicYear'
    ID = db.Column(db.Integer, primary_key=True)
    YearStart = db.Column(db.Integer, nullable=False)
    YearEnd = db.Column(db.Integer, nullable=False)
    subjects_in_year = db.relationship('Subject', back_populates='academic_year_info', foreign_keys='Subject.AcademicYearID', lazy='dynamic')
    activities_in_year = db.relationship('Activity', back_populates='academic_year_obj', foreign_keys='Activity.AcademicYearID', lazy='dynamic')

    def to_dict(self):
        return {
            'ID': self.ID,
            'YearStart': self.YearStart,
            'YearEnd': self.YearEnd,
            'YearRange': f"{self.YearStart}-{self.YearEnd}"
        }

class ActivityType(db.Model):
    __tablename__ = 'ActivityType'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False, unique=True)
    Category = db.Column(db.String(100), nullable=False)
    activities_of_type = db.relationship('Activity', back_populates='activity_type_obj', foreign_keys='Activity.ActivityTypeID', lazy='dynamic')

    def to_dict(self):
        return {
            'ID': self.ID,
            'Name': self.Name,
            'Category': self.Category
        }

class Activity(db.Model):
    __tablename__ = 'Activity'
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False) # e.g., specific workshop name, seminar name
    Title = db.Column(db.String(150), nullable=False) # e.g., "Paper presented on AI" or "Workshop on Python"
    Date = db.Column(db.Date, nullable=False)
    Description = db.Column(db.Text, nullable=True)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ActivityTypeID = db.Column(db.Integer, db.ForeignKey('ActivityType.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    faculty_member = db.relationship('Faculty', back_populates='activities', foreign_keys=[FacultyID])
    academic_year_obj = db.relationship('AcademicYear', back_populates='activities_in_year', foreign_keys=[AcademicYearID])
    activity_type_obj = db.relationship('ActivityType', back_populates='activities_of_type', foreign_keys=[ActivityTypeID])

    def to_dict(self):
        return {
            'ID': self.ID,
            'Name': self.Name,
            'Title': self.Title,
            'Date': self.Date.strftime('%Y-%m-%d') if self.Date else None,
            'Description': self.Description,
            'AcademicYearID': self.AcademicYearID,
            'FacultyID': self.FacultyID,
            'ActivityTypeID': self.ActivityTypeID,
            'FacultyName': f"{self.faculty_member.FirstName} {self.faculty_member.LastName}" if self.faculty_member else "N/A",
            'AcademicYear': f"{self.academic_year_obj.YearStart}-{self.academic_year_obj.YearEnd}" if self.academic_year_obj else "N/A",
            'ActivityTypeName': self.activity_type_obj.Name if self.activity_type_obj else "N/A",
            'ActivityTypeCategory': self.activity_type_obj.Category if self.activity_type_obj else "N/A"
        }

class Subject(db.Model):
    __tablename__ = 'Subject'
    CourseCode = db.Column(db.String(10), primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=False)
    FacultyID = db.Column(db.Integer, db.ForeignKey('Faculty.ID', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    AcademicYearID = db.Column(db.Integer, db.ForeignKey('AcademicYear.ID', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)

    assigned_faculty = db.relationship('Faculty', back_populates='subjects_taught', foreign_keys=[FacultyID])
    academic_year_info = db.relationship('AcademicYear', back_populates='subjects_in_year', foreign_keys=[AcademicYearID])

    def to_dict(self):
        return {
            'CourseCode': self.CourseCode,
            'SubjectName': self.SubjectName,
            'FacultyID': self.FacultyID,
            'AcademicYearID': self.AcademicYearID,
            'FacultyName': f"{self.assigned_faculty.FirstName} {self.assigned_faculty.LastName}" if self.assigned_faculty else "N/A",
            'AcademicYear': f"{self.academic_year_info.YearStart}-{self.academic_year_info.YearEnd}" if self.academic_year_info else "N/A"
        }

# Helper to convert Python date to string for forms
def format_date_for_input(date_obj):
    return date_obj.strftime('%Y-%m-%d') if date_obj else ''


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
        ActivityType.Category.label('activity_type_category'), # Changed label
        Faculty.FirstName,
        Faculty.LastName
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID) \
     .join(Faculty, Activity.FacultyID == Faculty.ID) \
     .order_by(Activity.Date.desc()).limit(5).all()

    faculty_list_short = Faculty.query.limit(10).all()

    return render_template('Admin/index.html',
        faculty_count=faculty_count,
        activity_count=activity_count,
        subject_count=subject_count,
        current_year=current_year,
        recent_activities=[{
            'Title': a.Title,
            'Date': a.Date.strftime('%d %b, %Y') if a.Date else 'N/A',
            'activity_type': a.activity_type_category, # Use new label
            'faculty_name': f"{a.FirstName} {a.LastName if a.LastName else ''}".strip()
        } for a in recent_activities_result],
        faculty_list=faculty_list_short
    )

@app.route('/faculty')
def faculty():
    faculty_data = Faculty.query.order_by(Faculty.ID).all()
    faculty_list_dicts = [fac.to_dict() for fac in faculty_data]
    current_year = datetime.now().year
    return render_template('Admin/faculty.html', 
                           faculty_list=faculty_data, 
                           faculty_list_json=faculty_list_dicts,
                           current_year=current_year,
                           format_date_for_input=format_date_for_input)

@app.route('/add_faculty', methods=['POST'])
def add_faculty():
    try:
        dob_str = request.form.get('dob')
        join_date_str = request.form.get('join_date')

        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date() if join_date_str else None
        
        if not dob:
            flash('Date of Birth is required.', 'danger')
            return redirect(request.referrer or url_for('faculty'))
        
        # Check for unique email
        existing_email = Faculty.query.filter_by(Email=request.form.get('email')).first()
        if existing_email:
            flash('Email address already exists.', 'danger')
            return redirect(request.referrer or url_for('faculty'))

        # Check for unique phone (if provided)
        phone_num = request.form.get('phone')
        if phone_num:
            existing_phone = Faculty.query.filter_by(Phone=phone_num).first()
            if existing_phone:
                flash('Primary phone number already exists.', 'danger')
                return redirect(request.referrer or url_for('faculty'))
        
        phone1_num = request.form.get('phone1')
        if phone1_num:
            existing_phone1 = Faculty.query.filter_by(Phone1=phone1_num).first()
            if existing_phone1:
                flash('Secondary phone number already exists.', 'danger')
                return redirect(request.referrer or url_for('faculty'))


        new_faculty = Faculty(
            FirstName=request.form.get('first_name'),
            LastName=request.form.get('last_name'),
            DOB=dob,
            Email=request.form.get('email'),
            Phone=phone_num if phone_num else None,
            Phone1=phone1_num if phone1_num else None,
            Department=request.form.get('department'),
            Designation=request.form.get('designation'),
            JoinDate=join_date
        )
        db.session.add(new_faculty)
        db.session.commit()
        flash('Faculty member added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding faculty: {str(e)}', 'danger')
        app.logger.error(f"Error adding faculty: {e}")
    return redirect(url_for('faculty'))

@app.route('/edit_faculty/<int:faculty_id>', methods=['POST'])
def edit_faculty(faculty_id):
    faculty_member = Faculty.query.get_or_404(faculty_id)
    try:
        dob_str = request.form.get('edit_dob')
        join_date_str = request.form.get('edit_join_date')

        new_email = request.form.get('edit_email')
        if new_email != faculty_member.Email:
            existing_email = Faculty.query.filter(Faculty.Email == new_email, Faculty.ID != faculty_id).first()
            if existing_email:
                flash('Email address already exists for another faculty.', 'danger')
                return redirect(url_for('faculty'))
        
        new_phone = request.form.get('edit_phone')
        if new_phone and new_phone != faculty_member.Phone:
            existing_phone = Faculty.query.filter(Faculty.Phone == new_phone, Faculty.ID != faculty_id).first()
            if existing_phone:
                flash('Primary phone number already exists for another faculty.', 'danger')
                return redirect(url_for('faculty'))

        new_phone1 = request.form.get('edit_phone1')
        if new_phone1 and new_phone1 != faculty_member.Phone1:
            existing_phone1 = Faculty.query.filter(Faculty.Phone1 == new_phone1, Faculty.ID != faculty_id).first()
            if existing_phone1:
                flash('Secondary phone number already exists for another faculty.', 'danger')
                return redirect(url_for('faculty'))

        faculty_member.FirstName = request.form.get('edit_first_name')
        faculty_member.LastName = request.form.get('edit_last_name')
        if dob_str: faculty_member.DOB = datetime.strptime(dob_str, '%Y-%m-%d').date()
        faculty_member.Email = new_email
        faculty_member.Phone = new_phone if new_phone else None
        faculty_member.Phone1 = new_phone1 if new_phone1 else None
        faculty_member.Department = request.form.get('edit_department')
        faculty_member.Designation = request.form.get('edit_designation')
        if join_date_str: faculty_member.JoinDate = datetime.strptime(join_date_str, '%Y-%m-%d').date() 
        else: faculty_member.JoinDate = None
        
        db.session.commit()
        flash('Faculty member updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating faculty: {str(e)}', 'danger')
        app.logger.error(f"Error editing faculty {faculty_id}: {e}")
    return redirect(url_for('faculty'))

@app.route('/delete_faculty/<int:faculty_id>', methods=['POST'])
def delete_faculty(faculty_id):
    faculty_member = Faculty.query.get_or_404(faculty_id)
    try:
        # Check if faculty is associated with any subjects or activities
        if faculty_member.subjects_taught.first() or faculty_member.activities.first():
            flash(f'Cannot delete faculty {faculty_member.FirstName} {faculty_member.LastName} as they are associated with subjects or activities. Please reassign or remove these associations first.', 'danger')
            return redirect(url_for('faculty'))

        db.session.delete(faculty_member)
        db.session.commit()
        flash('Faculty member deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting faculty: {str(e)}', 'danger')
        app.logger.error(f"Error deleting faculty {faculty_id}: {e}")
    return redirect(url_for('faculty'))

@app.route('/faculty_detail/<int:faculty_id>')
def view_faculty_detail_page(faculty_id):
    faculty_member = Faculty.query.get_or_404(faculty_id)
    current_year = datetime.now().year
    # This is a placeholder if direct URL access to detail is needed
    # A 'Admin/faculty_detail_placeholder.html' would be required.
    # For modal-only approach, this route might not be used.
    if not os.path.exists(os.path.join(app.root_path, 'templates/Admin/faculty_detail_placeholder.html')):
        with open(os.path.join(app.root_path, 'templates/Admin/faculty_detail_placeholder.html'), 'w') as f:
            f.write("""
            {% extends "Admin/base.html" %}
            {% block title %}Faculty Detail Placeholder{% endblock %}
            {% block content %}
                <h2>Faculty Detail for {{ faculty_member.FirstName }} {{ faculty_member.LastName }}</h2>
                <p>This is a placeholder page for viewing faculty details directly via URL.</p>
                <p>ID: {{ faculty_member.ID }}</p>
                <p>Email: {{ faculty_member.Email }}</p>
                <a href="{{ url_for('faculty') }}">Back to Faculty List</a>
            {% endblock %}
            """)
    return render_template('Admin/faculty_detail_placeholder.html', faculty_member=faculty_member, current_year=current_year)


@app.route('/subjects')
def subjects_view():
    subject_list_query = db.session.query(Subject).options(
        db.joinedload(Subject.assigned_faculty),
        db.joinedload(Subject.academic_year_info)
    ).order_by(Subject.CourseCode).all()

    subject_list_dicts = [s.to_dict() for s in subject_list_query]
    
    faculties = Faculty.query.order_by(Faculty.FirstName).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    current_year = datetime.now().year

    return render_template('Admin/subjects.html',
                           subject_list=subject_list_query,
                           subject_list_json=subject_list_dicts,
                           faculties=faculties,
                           academic_years=academic_years,
                           current_year=current_year)

@app.route('/add_subject', methods=['POST'])
def add_subject():
    try:
        course_code = request.form.get('course_code')
        existing_subject = Subject.query.get(course_code)
        if existing_subject:
            flash(f'Subject with Course Code {course_code} already exists.', 'danger')
            return redirect(url_for('subjects_view'))

        new_subject = Subject(
            CourseCode=course_code,
            SubjectName=request.form.get('subject_name'),
            FacultyID=int(request.form.get('faculty_id')) if request.form.get('faculty_id') and request.form.get('faculty_id').isdigit() else None,
            AcademicYearID=int(request.form.get('academic_year_id')) if request.form.get('academic_year_id') and request.form.get('academic_year_id').isdigit() else None
        )
        db.session.add(new_subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding subject: {str(e)}', 'danger')
        app.logger.error(f"Error adding subject: {e}")
    return redirect(url_for('subjects_view'))

@app.route('/edit_subject/<string:course_code>', methods=['POST'])
def edit_subject(course_code):
    subject = Subject.query.get_or_404(course_code)
    try:
        subject.SubjectName = request.form.get('edit_subject_name')
        
        faculty_id_str = request.form.get('edit_faculty_id')
        subject.FacultyID = int(faculty_id_str) if faculty_id_str and faculty_id_str != "None" and faculty_id_str.isdigit() else None
        
        academic_year_id_str = request.form.get('edit_academic_year_id')
        subject.AcademicYearID = int(academic_year_id_str) if academic_year_id_str and academic_year_id_str != "None" and academic_year_id_str.isdigit() else None
        
        db.session.commit()
        flash(f'Subject {course_code} updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating subject {course_code}: {str(e)}', 'danger')
        app.logger.error(f"Error editing subject {course_code}: {e}")
    return redirect(url_for('subjects_view'))

@app.route('/delete_subject/<string:course_code>', methods=['POST'])
def delete_subject(course_code):
    subject = Subject.query.get_or_404(course_code)
    try:
        # Add checks here if Subject is a foreign key in other tables (e.g., student enrollments)
        # For now, we assume it can be deleted if not directly linked by other critical data.
        db.session.delete(subject)
        db.session.commit()
        flash(f'Subject {course_code} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        if "foreign key constraint fails" in str(e).lower():
             flash(f'Error deleting subject: This subject might be linked to other records and cannot be deleted directly.', 'danger')
        else:
            flash(f'Error deleting subject {course_code}: {str(e)}', 'danger')
        app.logger.error(f"Error deleting subject {course_code}: {e}")
    return redirect(url_for('subjects_view'))


@app.route('/activities')
def activities_view():
    activities_query = db.session.query(Activity).options(
        db.joinedload(Activity.faculty_member),
        db.joinedload(Activity.academic_year_obj),
        db.joinedload(Activity.activity_type_obj)
    ).order_by(Activity.Date.desc()).all()
    
    activities_list_dicts = [act.to_dict() for act in activities_query]
    
    faculties = Faculty.query.order_by(Faculty.FirstName).all()
    activity_types = ActivityType.query.order_by(ActivityType.Name).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    current_year = datetime.now().year
    
    return render_template('Admin/activities.html',
                        activities=activities_query, # For direct Jinja rendering
                        activities_json=activities_list_dicts, # For JavaScript
                        faculties=faculties,
                        activity_types=activity_types,
                        academic_years=academic_years,
                        current_year=current_year,
                        active_page='activities')


@app.route('/add_admin_activity', methods=['POST'])
def add_admin_activity():
    try:
        date_str = request.form.get('date')
        activity_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        if not activity_date:
            flash('Activity date is required.', 'danger')
            return redirect(url_for('activities_view'))

        new_activity = Activity(
            Name=request.form.get('activity_name'),
            Title=request.form.get('title'),
            Date=activity_date,
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
        app.logger.error(f"Error adding admin activity: {e}")
    return redirect(url_for('activities_view'))

@app.route('/edit_admin_activity/<int:id>', methods=['POST'])
def edit_admin_activity(id):
    activity = Activity.query.get_or_404(id)
    try:
        date_str = request.form.get('edit_date') # Ensure form field names match
        
        activity.Name = request.form.get('edit_activity_name')
        activity.Title = request.form.get('edit_title')
        if date_str: activity.Date = datetime.strptime(date_str, '%Y-%m-%d').date()
        activity.Description = request.form.get('edit_description')
        activity.AcademicYearID = request.form.get('edit_academic_year')
        activity.ActivityTypeID = request.form.get('edit_activity_type')
        activity.FacultyID = request.form.get('edit_faculty_id')
        
        db.session.commit()
        flash('Activity updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating activity: {str(e)}', 'danger')
        app.logger.error(f"Error editing admin activity {id}: {e}")
    return redirect(url_for('activities_view'))

@app.route('/delete_admin_activity/<int:id>', methods=['POST'])
def delete_admin_activity(id):
    activity = Activity.query.get_or_404(id)
    try:
        db.session.delete(activity)
        db.session.commit()
        flash('Activity deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting activity: {str(e)}', 'danger')
        app.logger.error(f"Error deleting admin activity {id}: {e}")
    return redirect(url_for('activities_view'))

@app.route('/appraisals')
def appraisals():
    faculties = Faculty.query.order_by(Faculty.FirstName, Faculty.LastName).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()
    current_year = datetime.now().year

    # Placeholder for actual appraisal data fetching logic
    appraisal_list_data = [] 

    return render_template('Admin/appraisals.html',
                           appraisal_list=appraisal_list_data,
                           faculties=faculties,
                           academic_years=academic_years,
                           current_year=current_year)
# ------ End of Admin Views ------
# ------ Start of Faculty Views ------
# Routes -- Faculty Views
@app.route('/facultydashboard')
def facultydashboard():
    # For demonstration, using Faculty ID 2. Replace with actual authentication.
    faculty_id_to_display = 2 
    faculty_member = Faculty.query.get(faculty_id_to_display)

    if not faculty_member:
        flash("Faculty member not found. Please log in or select a valid faculty.", "warning")
        return render_template('Faculty/dashboard.html',
                               faculty=None, subject_count=0, activities_count=0,
                               activity_distribution=[], activities=[])

    subject_count = faculty_member.subjects_taught.count()
    
    # Fetch activities with their type for the specific faculty
    activities_query = db.session.query(
        Activity.Title,
        Activity.Date,
        ActivityType.Name.label('Type') # Use ActivityType.Name for the type
    ).join(ActivityType, Activity.ActivityTypeID == ActivityType.ID)\
     .filter(Activity.FacultyID == faculty_member.ID)\
     .order_by(Activity.Date.desc()).all()

    color_map = {
        'Workshop': 'bg-primary', 'Seminar': 'bg-success',
        'Research': 'bg-warning', 'Other': 'bg-secondary',
        'Conference': 'bg-info', 'FDP': 'bg-danger',
        'Guest Lecture': 'bg-purple', 'Publication': 'bg-teal'
        # Add more types and colors as needed
    }
    faculty_activities = [{
        'Title': a.Title, 
        'Date': a.Date.strftime('%d %b, %Y') if a.Date else 'N/A', 
        'Type': a.Type,
        'color': color_map.get(a.Type, 'bg-secondary') # Default color if type not in map
    } for a in activities_query]

    activities_count = len(faculty_activities)
    
    # Activity distribution for the specific faculty
    activity_type_counts = db.session.query(
        ActivityType.Name, db.func.count(Activity.ID).label('count')
    ).join(Activity, Activity.ActivityTypeID == ActivityType.ID)\
     .filter(Activity.FacultyID == faculty_member.ID)\
     .group_by(ActivityType.Name).all()

    total_faculty_activities = sum(item.count for item in activity_type_counts)
    
    activity_distribution_colors = ['bg-primary', 'bg-success', 'bg-info', 'bg-warning', 'bg-danger', 'bg-secondary', 'bg-purple', 'bg-teal']
    activity_distribution = [{
        'name': item.Name, 
        'count': item.count,
        'percentage': round((item.count / total_faculty_activities) * 100, 1) if total_faculty_activities > 0 else 0,
        'color': activity_distribution_colors[i % len(activity_distribution_colors)]
    } for i, item in enumerate(activity_type_counts)]

    return render_template('Faculty/dashboard.html',
                           faculty=faculty_member,
                           subject_count=subject_count,
                           activities_count=activities_count,
                           activity_distribution=activity_distribution,
                           activities=faculty_activities)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # For demonstration, using Faculty ID 1. Replace with actual authentication.
    faculty_id_to_display = 1
    faculty_member = Faculty.query.get_or_404(faculty_id_to_display)

    if request.method == 'POST':
        try:
            faculty_member.FirstName = request.form['first_name']
            faculty_member.LastName = request.form['last_name']
            dob_str = request.form.get('dob')
            if dob_str: faculty_member.DOB = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
            new_email = request.form['email']
            if new_email != faculty_member.Email:
                existing_email = Faculty.query.filter(Faculty.Email == new_email, Faculty.ID != faculty_id_to_display).first()
                if existing_email:
                    flash('Email address already exists for another faculty.', 'danger')
                    return redirect(url_for('profile')) # Or stay on page with error
            faculty_member.Email = new_email

            new_phone = request.form.get('phone')
            if new_phone and new_phone != faculty_member.Phone:
                existing_phone = Faculty.query.filter(Faculty.Phone == new_phone, Faculty.ID != faculty_id_to_display).first()
                if existing_phone:
                    flash('Primary phone already exists for another faculty.', 'danger')
                    return redirect(url_for('profile'))
            faculty_member.Phone = new_phone if new_phone else None
            
            new_alt_phone = request.form.get('alt_phone')
            if new_alt_phone and new_alt_phone != faculty_member.Phone1:
                existing_alt_phone = Faculty.query.filter(Faculty.Phone1 == new_alt_phone, Faculty.ID != faculty_id_to_display).first()
                if existing_alt_phone:
                    flash('Secondary phone already exists for another faculty.', 'danger')
                    return redirect(url_for('profile'))
            faculty_member.Phone1 = new_alt_phone if new_alt_phone else None # Model uses Phone1

            faculty_member.Department = request.form['department']
            faculty_member.Designation = request.form['designation']
            join_date_str = request.form.get('join_date')
            if join_date_str: faculty_member.JoinDate = datetime.strptime(join_date_str, '%Y-%m-%d').date()
            else: faculty_member.JoinDate = None
            
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "danger")
            app.logger.error(f"Error updating profile for faculty {faculty_member.ID}: {e}")
        return redirect(url_for('profile'))

    return render_template('Faculty/profile.html', faculty=faculty_member)

@app.route('/subject') # This route name might conflict if you have Admin subjects. Consider renaming.
def faculty_subjects_view(): # Renamed function
    # For demonstration, using Faculty ID 1. Replace with actual authentication.
    faculty_id_to_display = 1
    faculty_member = Faculty.query.get_or_404(faculty_id_to_display)
    subjects_with_year = faculty_member.subjects_taught.join(AcademicYear, Subject.AcademicYearID == AcademicYear.ID)\
                                           .add_entity(AcademicYear).all()
    return render_template('Faculty/subjects.html', subjects_data=subjects_with_year, faculty_name=f"{faculty_member.FirstName} {faculty_member.LastName}")


@app.route('/activity') # This route name might conflict. Consider renaming to /faculty/activity
def faculty_activity_view(): # Renamed function
    # For demonstration, using Faculty ID 1. Replace with actual authentication.
    faculty_id_to_display = 1
    faculty_member = Faculty.query.get_or_404(faculty_id_to_display)
    
    # Query for activities specific to this faculty member
    activities_data = db.session.query(
        Activity,
        ActivityType.Name.label('type_name'),
        ActivityType.Category.label('category'),
        AcademicYear.YearStart,
        AcademicYear.YearEnd
    ).filter(Activity.FacultyID == faculty_member.ID)\
     .join(ActivityType, Activity.ActivityTypeID == ActivityType.ID)\
     .join(AcademicYear, Activity.AcademicYearID == AcademicYear.ID)\
     .order_by(Activity.Date.desc())\
     .all()
    
    faculty_activities_detailed = []
    for act_obj, type_name, category, year_start, year_end in activities_data:
        faculty_activities_detailed.append({
            'obj': act_obj, 
            'type_name': type_name,
            'category': category,
            'academic_year_str': f"{year_start}-{year_end}" if year_start and year_end else "N/A"
        })

    # For dropdowns in the "Add/Edit Activity" modal on the faculty page
    activity_types = ActivityType.query.order_by(ActivityType.Name).all()
    academic_years = AcademicYear.query.order_by(AcademicYear.YearStart.desc()).all()

    return render_template('Faculty/activities.html',
                           activities=faculty_activities_detailed,
                           activity_types=activity_types,
                           academic_years=academic_years,
                           faculty_id=faculty_member.ID, 
                           faculty_name=f"{faculty_member.FirstName} {faculty_member.LastName}")

@app.route('/add_activity', methods=['POST']) # Faculty adding their own activity
def add_faculty_activity(): # Renamed function
    # Assume faculty_id is from a hidden form field or session (e.g., current_user.id)
    # For demonstration, hardcoding. Replace with actual faculty ID from session/login.
    current_faculty_id = int(request.form.get('faculty_id_hidden', 1)) 
    
    try:
        date_str = request.form['date']
        activity_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        if not activity_date:
            flash('Activity date is required.', 'danger')
            return redirect(url_for('faculty_activity_view')) # Redirect back to faculty activities page

        new_activity = Activity(
            Name=request.form['activity_name'],
            Title=request.form['title'],
            Date=activity_date,
            Description=request.form.get('description'),
            AcademicYearID=request.form['academic_year'],
            ActivityTypeID=request.form['activity_type'],
            FacultyID=current_faculty_id # Use the ID of the logged-in faculty
        )
        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding activity: {str(e)}', 'danger')
        app.logger.error(f"Error faculty adding activity: {e}")
    return redirect(url_for('faculty_activity_view'))

@app.route('/edit_activity/<int:id>', methods=['POST']) # Faculty editing their own activity
def edit_faculty_activity(id): # Renamed function
    activity_item = Activity.query.get_or_404(id)
    # Authorization: Ensure the logged-in faculty owns this activity
    # current_faculty_id = ... # Get from session
    # if activity_item.FacultyID != current_faculty_id:
    #     flash('You are not authorized to edit this activity.', 'danger')
    #     return redirect(url_for('faculty_activity_view'))
    
    try:
        date_str = request.form['date']
        activity_item.Name = request.form['activity_name']
        activity_item.Title = request.form['title']
        if date_str: activity_item.Date = datetime.strptime(date_str, '%Y-%m-%d').date()
        activity_item.Description = request.form.get('description')
        activity_item.AcademicYearID = request.form['academic_year']
        activity_item.ActivityTypeID = request.form['activity_type']
        # FacultyID should not change here, it's tied to the owner
        db.session.commit()
        flash('Activity updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating activity: {str(e)}', 'danger')
        app.logger.error(f"Error faculty editing activity {id}: {e}")
    return redirect(url_for('faculty_activity_view'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Creates tables if they don't exist
    app.run(debug=True, port=8000)