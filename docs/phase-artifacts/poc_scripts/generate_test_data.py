"""
Generate synthetic test data for Phase 0 POCs
Creates CVs and JDs with various formats and edge cases
"""

import os
import json
from faker import Faker
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from docx import Document
from docx.shared import Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont
import random

fake = Faker('en_IN')  # Indian locale for realistic names

# Ensure output directories exist
os.makedirs('test_data/text_pdfs', exist_ok=True)
os.makedirs('test_data/scanned', exist_ok=True)
os.makedirs('test_data/docx', exist_ok=True)
os.makedirs('test_data/jds', exist_ok=True)

# Sample skills database
SKILLS_DB = {
    'programming': ['Python', 'Java', 'JavaScript', 'C++', 'Go', 'Ruby', 'PHP', 'C#', '.NET'],
    'web': ['React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring Boot'],
    'data': ['SQL', 'MongoDB', 'PostgreSQL', 'Redis', 'Elasticsearch', 'Cassandra'],
    'cloud': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform'],
    'tools': ['Git', 'Jenkins', 'JIRA', 'Confluence', 'Postman', 'VS Code'],
    'soft': ['Leadership', 'Communication', 'Problem Solving', 'Team Management']
}

def generate_cv_data():
    """Generate realistic CV data"""
    name = fake.name()
    email = f"{name.lower().replace(' ', '.')}@{fake.free_email_domain()}"
    phone = fake.phone_number()
    
    # Select random skills
    skills = []
    for category in random.sample(list(SKILLS_DB.keys()), 3):
        skills.extend(random.sample(SKILLS_DB[category], random.randint(2, 4)))
    
    experience_years = random.randint(2, 10)
    
    experiences = []
    for i in range(random.randint(2, 4)):
        experiences.append({
            'title': fake.job(),
            'company': fake.company(),
            'duration': f"{random.randint(1, 3)} years",
            'description': fake.text(max_nb_chars=200)
        })
    
    education = {
        'degree': random.choice(['B.Tech', 'M.Tech', 'BCA', 'MCA', 'B.Sc', 'M.Sc']),
        'field': random.choice(['Computer Science', 'Information Technology', 'Software Engineering']),
        'university': fake.company() + ' University',
        'year': random.randint(2010, 2020)
    }
    
    return {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'experience_years': experience_years,
        'experiences': experiences,
        'education': education,
        'summary': fake.text(max_nb_chars=300)
    }

def create_text_pdf_cv(cv_data, filename, layout='single'):
    """Create text-based PDF CV"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2C3E50'))
    story.append(Paragraph(cv_data['name'], title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Contact info
    contact = f"{cv_data['email']} | {cv_data['phone']}"
    story.append(Paragraph(contact, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    story.append(Paragraph("<b>Professional Summary</b>", styles['Heading2']))
    story.append(Paragraph(cv_data['summary'], styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Skills
    story.append(Paragraph("<b>Skills</b>", styles['Heading2']))
    skills_text = ", ".join(cv_data['skills'])
    story.append(Paragraph(skills_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Experience
    story.append(Paragraph("<b>Work Experience</b>", styles['Heading2']))
    for exp in cv_data['experiences']:
        story.append(Paragraph(f"<b>{exp['title']}</b> at {exp['company']}", styles['Normal']))
        story.append(Paragraph(f"Duration: {exp['duration']}", styles['Normal']))
        story.append(Paragraph(exp['description'], styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # Education
    story.append(Paragraph("<b>Education</b>", styles['Heading2']))
    edu_text = f"{cv_data['education']['degree']} in {cv_data['education']['field']}, {cv_data['education']['university']} ({cv_data['education']['year']})"
    story.append(Paragraph(edu_text, styles['Normal']))
    
    doc.build(story)
    return cv_data

def create_docx_cv(cv_data, filename):
    """Create DOCX CV"""
    doc = Document()
    
    # Title
    title = doc.add_heading(cv_data['name'], 0)
    title.alignment = 1  # Center
    
    # Contact
    contact = doc.add_paragraph(f"{cv_data['email']} | {cv_data['phone']}")
    contact.alignment = 1
    
    # Summary
    doc.add_heading('Professional Summary', 2)
    doc.add_paragraph(cv_data['summary'])
    
    # Skills
    doc.add_heading('Skills', 2)
    doc.add_paragraph(", ".join(cv_data['skills']))
    
    # Experience
    doc.add_heading('Work Experience', 2)
    for exp in cv_data['experiences']:
        doc.add_paragraph(f"{exp['title']} at {exp['company']}", style='List Bullet')
        doc.add_paragraph(f"Duration: {exp['duration']}")
        doc.add_paragraph(exp['description'])
    
    # Education
    doc.add_heading('Education', 2)
    edu_text = f"{cv_data['education']['degree']} in {cv_data['education']['field']}, {cv_data['education']['university']} ({cv_data['education']['year']})"
    doc.add_paragraph(edu_text)
    
    doc.save(filename)
    return cv_data

def create_scanned_cv_image(cv_data, filename, quality='high'):
    """Create scanned CV image with varying quality"""
    # Create a simple text image
    width, height = 800, 1100
    
    if quality == 'low':
        width, height = 400, 550  # Low resolution
    elif quality == 'medium':
        width, height = 600, 825
    
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    y = 50
    
    # Name
    draw.text((50, y), cv_data['name'], fill='black', font=font_large)
    y += 60
    
    # Contact
    draw.text((50, y), f"{cv_data['email']} | {cv_data['phone']}", fill='black', font=font_small)
    y += 40
    
    # Summary
    draw.text((50, y), "PROFESSIONAL SUMMARY", fill='black', font=font_medium)
    y += 30
    summary_lines = [cv_data['summary'][i:i+60] for i in range(0, len(cv_data['summary']), 60)]
    for line in summary_lines[:3]:
        draw.text((50, y), line, fill='black', font=font_small)
        y += 25
    
    y += 20
    
    # Skills
    draw.text((50, y), "SKILLS", fill='black', font=font_medium)
    y += 30
    skills_text = ", ".join(cv_data['skills'][:8])
    draw.text((50, y), skills_text, fill='black', font=font_small)
    
    # Add noise for low quality
    if quality == 'low':
        pixels = img.load()
        for i in range(width):
            for j in range(height):
                if random.random() < 0.02:  # 2% noise
                    pixels[i, j] = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    
    img.save(filename)
    return cv_data

def generate_jd_data():
    """Generate job description data"""
    return {
        'title': fake.job(),
        'company': fake.company(),
        'location': fake.city(),
        'description': fake.text(max_nb_chars=500),
        'requirements': [fake.sentence() for _ in range(5)],
        'responsibilities': [fake.sentence() for _ in range(5)],
        'skills': random.sample([s for cat in SKILLS_DB.values() for s in cat], 8)
    }

def create_jd_pdf(jd_data, filename):
    """Create JD PDF"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(jd_data['title'], styles['Title']))
    story.append(Paragraph(f"{jd_data['company']} - {jd_data['location']}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Description
    story.append(Paragraph("<b>Job Description</b>", styles['Heading2']))
    story.append(Paragraph(jd_data['description'], styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Requirements
    story.append(Paragraph("<b>Requirements</b>", styles['Heading2']))
    for req in jd_data['requirements']:
        story.append(Paragraph(f"• {req}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Responsibilities
    story.append(Paragraph("<b>Responsibilities</b>", styles['Heading2']))
    for resp in jd_data['responsibilities']:
        story.append(Paragraph(f"• {resp}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Skills
    story.append(Paragraph("<b>Required Skills</b>", styles['Heading2']))
    story.append(Paragraph(", ".join(jd_data['skills']), styles['Normal']))
    
    doc.build(story)
    return jd_data

def main():
    """Generate all test data"""
    print("Generating test data for Phase 0 POCs...")
    
    ground_truth = []
    
    # Generate 5 text PDFs
    print("\n1. Generating text-based PDF CVs...")
    for i in range(1, 6):
        cv_data = generate_cv_data()
        filename = f"test_data/text_pdfs/cv_text_{i}.pdf"
        create_text_pdf_cv(cv_data, filename)
        ground_truth.append({
            'file': f"cv_text_{i}.pdf",
            'ground_truth': {
                'name': cv_data['name'],
                'email': cv_data['email'],
                'phone': cv_data['phone'],
                'skills': cv_data['skills'][:5],
                'experience_years': cv_data['experience_years']
            }
        })
        print(f"   Created {filename}")
    
    # Generate 5 scanned images
    print("\n2. Generating scanned CV images...")
    qualities = ['high', 'high', 'medium', 'medium', 'low']
    for i, quality in enumerate(qualities, 1):
        cv_data = generate_cv_data()
        filename = f"test_data/scanned/cv_scan_{i}.jpg"
        create_scanned_cv_image(cv_data, filename, quality=quality)
        ground_truth.append({
            'file': f"cv_scan_{i}.jpg",
            'ground_truth': {
                'name': cv_data['name'],
                'email': cv_data['email'],
                'phone': cv_data['phone']
            }
        })
        print(f"   Created {filename} (quality: {quality})")
    
    # Generate 3 DOCX CVs
    print("\n3. Generating DOCX CVs...")
    for i in range(1, 4):
        cv_data = generate_cv_data()
        filename = f"test_data/docx/cv_docx_{i}.docx"
        create_docx_cv(cv_data, filename)
        print(f"   Created {filename}")
    
    # Generate 5 JDs
    print("\n4. Generating Job Descriptions...")
    jd_data_list = []
    for i in range(1, 6):
        jd_data = generate_jd_data()
        filename = f"test_data/jds/jd_{i}.pdf"
        create_jd_pdf(jd_data, filename)
        jd_data_list.append(jd_data)
        print(f"   Created {filename}")
    
    # Save ground truth
    print("\n5. Saving ground truth data...")
    with open('test_data/parser_ground_truth.json', 'w') as f:
        json.dump(ground_truth, f, indent=2)
    print("   Saved parser_ground_truth.json")
    
    # Generate embedding test data (JD-CV pairs with relevance scores)
    embedding_data = []
    for i, jd_data in enumerate(jd_data_list, 1):
        cv_pairs = []
        # Generate 5 CVs per JD with varying relevance
        relevance_scores = [5, 4, 3, 2, 1]  # High to low relevance
        for score in relevance_scores:
            cv_data = generate_cv_data()
            # Adjust skills to match relevance
            if score >= 4:
                cv_data['skills'] = jd_data['skills'][:6] + random.sample(cv_data['skills'], 2)
            elif score == 3:
                cv_data['skills'] = jd_data['skills'][:3] + random.sample(cv_data['skills'], 5)
            
            cv_pairs.append({
                'cv_text': f"{cv_data['name']}\n{cv_data['summary']}\nSkills: {', '.join(cv_data['skills'])}",
                'relevance_score': score
            })
        
        embedding_data.append({
            'jd_id': f"jd_{i}",
            'jd_text': f"{jd_data['title']}\n{jd_data['description']}\nRequired Skills: {', '.join(jd_data['skills'])}",
            'cvs': cv_pairs
        })
    
    with open('test_data/embedding_test_data.json', 'w') as f:
        json.dump(embedding_data, f, indent=2)
    print("   Saved embedding_test_data.json")
    
    print("\n✅ Test data generation complete!")
    print(f"\nGenerated:")
    print(f"  - 5 text-based PDF CVs")
    print(f"  - 5 scanned CV images (varying quality)")
    print(f"  - 3 DOCX CVs")
    print(f"  - 5 Job Description PDFs")
    print(f"  - Ground truth JSON files")
    print(f"\nTotal files: 18 CVs + 5 JDs + 2 JSON files = 25 files")

if __name__ == "__main__":
    main()
