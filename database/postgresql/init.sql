-- Create doctors table
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    designation TEXT,
    speciality TEXT NOT NULL,
    location TEXT,
    fee INTEGER,
    keywords TEXT,
    symptom_to_speciality TEXT,
    disease_examples TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
