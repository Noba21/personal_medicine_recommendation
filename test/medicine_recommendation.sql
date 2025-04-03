-- Create the database
CREATE DATABASE IF NOT EXISTS medicine_recommendation;
USE medicine_recommendation;

-- Users Table (for all actors: admin, user, medical_expert)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role ENUM('admin', 'user', 'medical_expert') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Symptoms Table (user-submitted symptoms)
CREATE TABLE IF NOT EXISTS symptoms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    symptoms_text TEXT NOT NULL,
    severity ENUM('low', 'medium', 'high') DEFAULT 'medium',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'reviewed', 'treated') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Medicine Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symptom_id INT NOT NULL,
    medicine_name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50) NOT NULL,
    instructions TEXT,
    expert_notes TEXT,
    recommended_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symptom_id) REFERENCES symptoms(id) ON DELETE CASCADE,
    FOREIGN KEY (recommended_by) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Chat Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_status BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX (sender_id, receiver_id),
    INDEX (receiver_id, read_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Audit Log Table (optional for tracking activities)
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Initial Admin User (change password after first login)
INSERT INTO users (username, password, email, role) VALUES (
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- bcrypt hash for 'secret'
    'admin@medirec.com',
    'admin'
);

-- Sample Medical Expert
INSERT INTO users (username, password, email, role) VALUES (
    'dr_smith',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'dr.smith@medirec.com',
    'medical_expert'
);

-- Sample Patient User
INSERT INTO users (username, password, email, role) VALUES (
    'patient1',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'patient1@example.com',
    'user'
);

-- Sample Symptoms Data
INSERT INTO symptoms (user_id, symptoms_text, severity) VALUES (
    3, -- patient1
    'Headache, fever, and sore throat for 3 days',
    'medium'
);

-- Sample Recommendation
INSERT INTO recommendations (
    symptom_id,
    medicine_name,
    dosage,
    instructions,
    expert_notes,
    recommended_by
) VALUES (
    1, -- symptom ID
    'Paracetamol',
    '500mg every 6 hours',
    'Take with food. Avoid alcohol.',
    'Patient should rest and drink plenty of fluids.',
    2  -- dr_smith
);

-- Sample Chat Messages
INSERT INTO messages (sender_id, receiver_id, message) VALUES
(3, 2, 'Doctor, I have a terrible headache and fever'),
(2, 3, 'How long have you had these symptoms?'),
(3, 2, 'About 3 days now'),
(2, 3, 'I recommend paracetamol and rest. See full recommendation in your dashboard.');

-- Create indexes for better performance
CREATE INDEX idx_symptoms_user ON symptoms(user_id);
CREATE INDEX idx_symptoms_status ON symptoms(status);
CREATE INDEX idx_recommendations_symptom ON recommendations(symptom_id);
CREATE INDEX idx_messages_conversation ON messages(sender_id, receiver_id, sent_at);