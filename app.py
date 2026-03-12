from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from config import Config
from utils.pdf_processor import extract_text_from_file
from utils.pii_remover import remove_pii
from utils.skill_extractor import extract_skills
from utils.ranking import compute_tfidf_similarity
from datetime import datetime
import uuid

# Initialize Flask app
db = SQLAlchemy()
login_manager = LoginManager()

# User model (moved up for app context)
class Recruiter(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255))
    resumes = db.relationship('Resume', backref='recruiter', lazy=True, cascade='all, delete-orphan')

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_text = db.Column(db.Text)
    cleaned_text = db.Column(db.Text)
    extracted_skills = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter.id'), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    cutoff_score = db.Column(db.Float, default=70.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RankingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ranking_id = db.Column(db.Integer, db.ForeignKey('ranking.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'), nullable=False)
    score = db.Column(db.Float)
    rank = db.Column(db.Integer)
    status = db.Column(db.String(20), default='Discarded')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Login required!'
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('dashboard.html')
    
    # Auth routes
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            company = request.form.get('company', '')
            
            # Check if user exists
            existing_user = Recruiter.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered!', 'error')
                return render_template('register.html')
            
            # Create new recruiter
            recruiter = Recruiter(
                email=email,
                password_hash=generate_password_hash(password),
                company_name=company
            )
            db.session.add(recruiter)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            recruiter = Recruiter.query.filter_by(email=email).first()
            if recruiter and check_password_hash(recruiter.password_hash, password):
                login_user(recruiter)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials!', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', recruiter=current_user)
    
    # Upload resumes
    @app.route('/upload_resumes', methods=['POST'])
    @login_required
    def upload_resumes():
        files = request.files.getlist('resumes')
        uploaded_files = []
        
        for file in files:
            if file and file.filename:
                # Secure filename and save
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                # Reset file pointer for processing
                file.seek(0)
                
                # Process resume
                text = extract_text_from_file(file)
                cleaned_text = remove_pii(text)
                skills = extract_skills(cleaned_text)
                
                # Save to database
                resume = Resume(
                    recruiter_id=current_user.id,
                    filename=filename,
                    original_text=text,
                    cleaned_text=cleaned_text,
                    extracted_skills=','.join(skills),
                    file_path=unique_filename
                )
                db.session.add(resume)
                uploaded_files.append({
                    'filename': filename,
                    'skills': skills[:5]
                })
        
        db.session.commit()
        return jsonify({'success': True, 'files': uploaded_files})
    
    # Ranking endpoint
    @app.route('/rank_resumes', methods=['POST'])
    @login_required
    def rank_resumes():
        data = request.json
        job_description = data['job_description']
        cutoff_score = float(data.get('cutoff_score', 70.0))
        
        # Get recruiter's resumes
        resumes = Resume.query.filter_by(recruiter_id=current_user.id).all()
        
        if not resumes:
            return jsonify({'error': 'No resumes uploaded'})
        
        # Create ranking record
        ranking = Ranking(
            recruiter_id=current_user.id,
            job_description=job_description,
            cutoff_score=cutoff_score
        )
        db.session.add(ranking)
        db.session.flush()
        
        results = []
        for i, resume in enumerate(resumes):
            score = compute_tfidf_similarity(job_description, resume.cleaned_text or "")
            
            status = 'Shortlisted' if score >= cutoff_score/100 else 'Discarded'
            
            result = RankingResult(
                ranking_id=ranking.id,
                resume_id=resume.id,
                score=round(score * 100, 2),
                rank=i + 1,
                status=status
            )
            db.session.add(result)
            results.append({
                'rank': i + 1,
                'filename': resume.filename,
                'score': round(score * 100, 2),
                'status': status,
                'skills': resume.extracted_skills.split(',')[:5] if resume.extracted_skills else []
            })
        
        db.session.commit()
        return jsonify({'results': results})
    
    # Serve uploaded files
    @app.route('/uploads/<filename>')
    @login_required
    def uploaded_file(filename):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Recruiter, int(user_id))

if __name__ == '__main__':
    app = create_app()
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created!")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
