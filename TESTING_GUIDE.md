# Quick Test Guide - CV/JD Extraction Validation

## 🚀 Quick Start

### 1. Upload Your Test Files

```bash
# Create test directory in your project
mkdir -p /Users/saswatray/AntiGravity/saswat-ctrl/SaarNews/test_documents

# Copy your CV and JD files there
# (Use Finder or command line)
```

### 2. Run Extraction Test

```bash
# Navigate to project
cd /Users/saswatray/AntiGravity/saswat-ctrl/SaarNews

# Test a single CV
docker exec -it saarnews-backend-1 python test_extraction.py \
  --file /app/test_documents/your_cv.pdf

# Test a JD
docker exec -it saarnews-backend-1 python test_extraction.py \
  --file /app/test_documents/your_jd.docx --type jd

# Test all files in folder
docker exec -it saarnews-backend-1 python test_extraction.py \
  --dir /app/test_documents --type cv
```

### 3. Check Results

Results are saved in the backend container. Copy them out:

```bash
# Copy extracted text
docker cp saarnews-backend-1:/app/your_cv_extracted.txt ./

# Copy parsed JSON
docker cp saarnews-backend-1:/app/your_cv_parsed.json ./
```

---

## 📋 Supported File Types

- ✅ PDF (text-based)
- ✅ PDF (scanned/image-based)
- ✅ DOCX
- ✅ JPG/JPEG
- ✅ PNG

---

## 🎯 What to Validate

### For CVs:
- [ ] Name correctly extracted?
- [ ] Email(s) found?
- [ ] Phone number(s) found?
- [ ] Skills identified (check JSON file)?
- [ ] Experience years detected?

### For JDs:
- [ ] Full text extracted?
- [ ] Job title visible?
- [ ] Requirements section clear?
- [ ] Skills/technologies mentioned?

---

## 🐛 If Something Fails

1. **Check file format**: Is it a supported type?
2. **Check file size**: Is it under 5MB?
3. **Check quality**: For scanned docs, is resolution decent?
4. **Check logs**: Look at the error message in output

---

## 📊 Example Commands

```bash
# Test your actual CV
docker exec -it saarnews-backend-1 python test_extraction.py \
  --file /app/test_documents/saswat_cv.pdf

# Test a job posting
docker exec -it saarnews-backend-1 python test_extraction.py \
  --file /app/test_documents/senior_engineer_jd.pdf --type jd

# Batch test 5 CVs
docker exec -it saarnews-backend-1 python test_extraction.py \
  --dir /app/test_documents --type cv
```

---

## 💡 Tips

- **For best results**: Use clear, well-formatted documents
- **For scanned docs**: Ensure good lighting and resolution (300+ DPI)
- **For skills**: Check if your specific tech stack is in the skills database
- **For names**: Works best when name is at the top of CV

---

## ✅ After Validation

Once you're satisfied with extraction accuracy, let me know and I'll proceed with:

1. **API endpoint updates** (synchronous extraction)
2. **Frontend UI** (upload + display parsed data)
3. **End-to-end testing**

**Estimated time to complete simplified MVP**: 24-32 hours (3-4 days)
