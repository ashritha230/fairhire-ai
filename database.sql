CREATE DATABASE IF NOT EXISTS fairhire_ai;
USE fairhire_ai;

-- Recruiters table
CREATE TABLE recruiters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resumes table
CREATE TABLE resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recruiter_id INT,
    filename VARCHAR(255) NOT NULL,
    original_text LONGTEXT,
    cleaned_text LONGTEXT,
    extracted_skills TEXT,
    file_path VARCHAR(500),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recruiter_id) REFERENCES recruiters(id) ON DELETE CASCADE
);

-- Rankings table
CREATE TABLE rankings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recruiter_id INT,
    job_description LONGTEXT NOT NULL,
    cutoff_score DECIMAL(5,2) DEFAULT 70.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recruiter_id) REFERENCES recruiters(id) ON DELETE CASCADE
);

-- Ranking results
CREATE TABLE ranking_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ranking_id INT,
    resume_id INT,
    score DECIMAL(5,2),
    rank INT,
    status ENUM('Shortlisted', 'Discarded') DEFAULT 'Discarded',
    FOREIGN KEY (ranking_id) REFERENCES rankings(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);
