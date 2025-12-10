# Phase 0 POC - Test Data Generation Plan

## Test Data Requirements

### 1. Text-Based PDF CVs (5 files)

**cv_text_1.pdf** - Modern single-column CV
- Clean, modern format
- 2 pages
- Standard sections (Summary, Experience, Education, Skills)
- Source: Generate using LaTeX template

**cv_text_2.pdf** - Two-column layout
- Professional template with sidebar
- Skills in left column, experience in right
- 1 page
- Source: Canva/Overleaf template

**cv_text_3.pdf** - Naukri.com format
- Typical Indian job portal format
- Multiple sections with tables
- 3 pages
- Source: Naukri resume builder export

**cv_text_4.pdf** - LinkedIn export format
- LinkedIn PDF export style
- Includes recommendations section
- 2 pages
- Source: LinkedIn profile export

**cv_text_5.pdf** - Complex formatting
- Mix of tables, bullet points, and text
- Graphical elements (skill bars, charts)
- 2 pages
- Source: Modern template with infographics

### 2. Scanned/Image-Based CVs (5 files)

**cv_scan_1.jpg** - High-quality scan (300 DPI)
- Clear, well-lit scan
- Standard CV format
- Expected: 95%+ OCR accuracy

**cv_scan_2.jpg** - Medium-quality scan (150 DPI)
- Slightly blurry
- Some shadows
- Expected: 80-90% OCR accuracy

**cv_scan_3.jpg** - Low-resolution scan (72 DPI)
- Poor quality, pixelated
- Edge case for OCR
- Expected: 60-70% OCR accuracy

**cv_scan_4.jpg** - Rotated/skewed scan
- 5-10 degree rotation
- Tests angle correction
- Expected: 75-85% OCR accuracy

**cv_scan_5.jpg** - Screenshot converted to PDF
- Mobile screenshot of CV
- Low contrast
- Expected: 70-80% OCR accuracy

### 3. DOCX CVs (3 files)

**cv_docx_1.docx** - Standard Word template
- Microsoft Word built-in template
- Clean formatting
- Expected: 100% extraction

**cv_docx_2.docx** - Naukri DOCX export
- Downloaded from Naukri.com
- May have embedded styles
- Expected: 95%+ extraction

**cv_docx_3.docx** - Complex DOCX
- Tables, text boxes, headers/footers
- Multiple columns
- Expected: 90%+ extraction

### 4. Job Descriptions (5 files)

**jd_1.pdf** - Simple JD
- Clean text format
- Clear sections (Role, Requirements, Responsibilities)
- 1 page

**jd_2.pdf** - Complex JD with tables
- Salary table, benefits table
- Multi-column layout
- 2 pages

**jd_3.docx** - DOCX format JD
- Standard Word document
- Bullet points and formatting
- 1 page

**jd_4.pdf** - LinkedIn job posting format
- Exported from LinkedIn
- Includes company info, culture section
- 2 pages

**jd_5.pdf** - Naukri job posting
- Indian job portal format
- Multiple sections with icons
- 1 page

### 5. Ground Truth Data

**parser_ground_truth.json** - For 10 CVs
```json
[
  {
    "file": "cv_text_1.pdf",
    "ground_truth": {
      "name": "Rajesh Kumar",
      "email": "rajesh.kumar@email.com",
      "phone": "9876543210",
      "skills": ["Python", "Java", "SQL", "AWS", "Docker"],
      "experience_years": 5,
      "education": "B.Tech Computer Science"
    }
  },
  // ... 9 more entries
]
```

**embedding_test_data.json** - For 5 JDs with 5 CVs each
```json
[
  {
    "jd_id": "jd_1",
    "jd_text": "Full job description text...",
    "cvs": [
      {
        "cv_id": "cv_1",
        "cv_text": "Full CV text...",
        "relevance_score": 5  // 1-5 scale (5 = perfect match)
      },
      // ... 4 more CVs
    ]
  },
  // ... 4 more JDs
]
```

## Edge Cases to Cover

### OCR Edge Cases
1. ✅ Low-resolution scans (72 DPI)
2. ✅ Rotated/skewed documents
3. ✅ Poor lighting/shadows
4. ✅ Screenshots converted to PDF
5. ✅ Multi-page documents
6. ✅ Mixed text + images

### Layout Edge Cases
1. ✅ Two-column layouts
2. ✅ Tables and grids
3. ✅ Text boxes and sidebars
4. ✅ Headers and footers
5. ✅ Graphical elements (charts, skill bars)
6. ✅ Different fonts and sizes

### Format Edge Cases
1. ✅ Naukri.com exports
2. ✅ LinkedIn exports
3. ✅ Modern infographic CVs
4. ✅ Traditional text-heavy CVs
5. ✅ Academic CVs (publications, research)

### Content Edge Cases
1. ✅ Indian names and addresses
2. ✅ International phone formats
3. ✅ Multiple email addresses
4. ✅ Special characters in skills (C++, .NET)
5. ✅ Abbreviations and acronyms

## Test Data Sources

### Option 1: Generate Synthetic CVs
- Use Python libraries (reportlab, python-docx)
- Create realistic but fake data
- Full control over content and format
- **Pros**: Privacy-safe, customizable
- **Cons**: May not match real-world variety

### Option 2: Use Public CV Datasets
- Kaggle CV datasets
- GitHub resume repositories
- Academic datasets (with permission)
- **Pros**: Real-world formats
- **Cons**: Privacy concerns, limited control

### Option 3: Hybrid Approach (RECOMMENDED)
- Generate 60% synthetic CVs with realistic data
- Source 40% from public datasets (anonymized)
- Ensures both control and realism

## Implementation Plan

1. **Generate synthetic CVs** (2-3 hours)
   - Create Python script to generate PDFs/DOCX
   - Use faker library for realistic names/data
   - Apply different templates and layouts

2. **Source public samples** (1-2 hours)
   - Download from Kaggle/GitHub
   - Anonymize personal information
   - Convert to required formats

3. **Create ground truth** (1-2 hours)
   - Manually extract name/email/phone from each CV
   - Assign relevance scores for JD-CV pairs
   - Save as JSON files

4. **Validate test data** (1 hour)
   - Ensure all formats are readable
   - Verify ground truth accuracy
   - Check file sizes and quality

**Total Estimated Time**: 5-8 hours
