# PHASE 0: Tool Selection & POC Validation

**Status**: Awaiting Approval  
**Created**: 2025-11-28  
**Owner**: Technical Product Manager + Engineering Manager  

---

## Executive Summary

This document defines the POC validation process for selecting open-source tools for the CV ranking pipeline. **No production code will be written until all POCs pass acceptance criteria and receive explicit approval.**

---

## 1. OCR & Text Extraction Tools

### Candidates

| Tool | Use Case | Expected Performance | Risk Level |
|------|----------|---------------------|------------|
| **PyMuPDF (fitz)** | Text-based PDFs | <1s per page | Low |
| **PaddleOCR** | Scanned PDFs/Images | 2-5s per page | Medium |
| **Tesseract** | Fallback OCR | 3-8s per page | Low |
| **python-docx** | DOCX files | <0.5s per file | Low |

### POC Plan: OCR Tools

#### Test Dataset Requirements
- 5 text-based PDF CVs (modern format)
- 5 scanned/image-based PDF CVs
- 3 DOCX CVs
- 2 mixed-format CVs (text + images)

#### Acceptance Criteria

**PyMuPDF**:
- ✅ Extract text from 5/5 text-based PDFs
- ✅ Average extraction time <1s per page
- ✅ Preserve structure (sections, bullet points)
- ✅ Handle multi-page CVs correctly
- ❌ Expected to fail on scanned PDFs (acceptable)

**PaddleOCR**:
- ✅ Extract text from 4/5 scanned PDFs (80% success)
- ✅ Average extraction time <5s per page
- ✅ Accuracy: >85% character recognition on clear scans
- ✅ Handle rotated images
- ⚠️ Acceptable: lower accuracy on poor-quality scans

**Tesseract**:
- ✅ Extract text from 3/5 scanned PDFs (60% success - fallback only)
- ✅ Average extraction time <8s per page
- ✅ Baseline accuracy: >70% character recognition
- ⚠️ Used only when PaddleOCR fails

**python-docx**:
- ✅ Extract text from 3/3 DOCX files
- ✅ Average extraction time <0.5s per file
- ✅ Preserve formatting and structure

#### POC Test Script

```python
# File: docs/phase-artifacts/poc_scripts/test_ocr.py

import time
import pymupdf  # PyMuPDF
from docx import Document
from paddleocr import PaddleOCR
import pytesseract
from PIL import Image
import json

def test_pymupdf(pdf_path):
    """Test PyMuPDF on text-based PDF"""
    start = time.time()
    try:
        doc = pymupdf.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        duration = time.time() - start
        
        return {
            "success": len(text) > 100,
            "duration": duration,
            "text_length": len(text),
            "pages": len(doc),
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_paddleocr(image_path):
    """Test PaddleOCR on scanned PDF/image"""
    start = time.time()
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        result = ocr.ocr(image_path, cls=True)
        
        text = "\n".join([line[1][0] for line in result[0]])
        duration = time.time() - start
        
        return {
            "success": len(text) > 50,
            "duration": duration,
            "text_length": len(text),
            "confidence": sum([line[1][1] for line in result[0]]) / len(result[0]),
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_tesseract(image_path):
    """Test Tesseract OCR"""
    start = time.time()
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        duration = time.time() - start
        
        return {
            "success": len(text) > 50,
            "duration": duration,
            "text_length": len(text),
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_python_docx(docx_path):
    """Test python-docx"""
    start = time.time()
    try:
        doc = Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        duration = time.time() - start
        
        return {
            "success": len(text) > 100,
            "duration": duration,
            "text_length": len(text),
            "paragraphs": len(doc.paragraphs),
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_ocr_poc():
    """Run all OCR POCs and generate report"""
    results = {
        "pymupdf": [],
        "paddleocr": [],
        "tesseract": [],
        "python_docx": []
    }
    
    # Test PyMuPDF on text PDFs
    text_pdfs = ["sample_cv_1.pdf", "sample_cv_2.pdf", "sample_cv_3.pdf", 
                 "sample_cv_4.pdf", "sample_cv_5.pdf"]
    for pdf in text_pdfs:
        results["pymupdf"].append(test_pymupdf(f"test_data/text_pdfs/{pdf}"))
    
    # Test PaddleOCR on scanned PDFs
    scanned_images = ["scan_cv_1.jpg", "scan_cv_2.jpg", "scan_cv_3.jpg",
                      "scan_cv_4.jpg", "scan_cv_5.jpg"]
    for img in scanned_images:
        results["paddleocr"].append(test_paddleocr(f"test_data/scanned/{img}"))
    
    # Test Tesseract on same scanned images
    for img in scanned_images:
        results["tesseract"].append(test_tesseract(f"test_data/scanned/{img}"))
    
    # Test python-docx
    docx_files = ["cv_1.docx", "cv_2.docx", "cv_3.docx"]
    for docx in docx_files:
        results["python_docx"].append(test_python_docx(f"test_data/docx/{docx}"))
    
    # Generate summary
    summary = {}
    for tool, tests in results.items():
        success_rate = sum(1 for t in tests if t["success"]) / len(tests)
        avg_duration = sum(t.get("duration", 0) for t in tests) / len(tests)
        summary[tool] = {
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "total_tests": len(tests),
            "passed": sum(1 for t in tests if t["success"])
        }
    
    # Save results
    with open("docs/phase-artifacts/poc_results/ocr_results.json", "w") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2)
    
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    run_ocr_poc()
```

#### How to Run POC

```bash
# 1. Install dependencies
pip install pymupdf python-docx paddleocr pytesseract pillow

# 2. Prepare test data (create sample CVs or use provided)
mkdir -p test_data/{text_pdfs,scanned,docx}

# 3. Run POC script
python docs/phase-artifacts/poc_scripts/test_ocr.py

# 4. Review results
cat docs/phase-artifacts/poc_results/ocr_results.json
```

#### Expected Output Format

```json
{
  "pymupdf": {
    "success_rate": 1.0,
    "avg_duration": 0.45,
    "total_tests": 5,
    "passed": 5
  },
  "paddleocr": {
    "success_rate": 0.8,
    "avg_duration": 3.2,
    "total_tests": 5,
    "passed": 4
  },
  "tesseract": {
    "success_rate": 0.6,
    "avg_duration": 5.8,
    "total_tests": 5,
    "passed": 3
  },
  "python_docx": {
    "success_rate": 1.0,
    "avg_duration": 0.3,
    "total_tests": 3,
    "passed": 3
  }
}
```

#### Decision Matrix

| Metric | PyMuPDF | PaddleOCR | Tesseract | python-docx |
|--------|---------|-----------|-----------|-------------|
| Success Rate | ≥90% | ≥80% | ≥60% | ≥90% |
| Avg Duration | <1s | <5s | <8s | <0.5s |
| **Adopt?** | ✅ Primary | ✅ Primary | ✅ Fallback | ✅ Primary |

---

## 2. Resume Parsing Tools

### Candidates

| Tool | Approach | Expected Accuracy | Complexity |
|------|----------|------------------|------------|
| **spaCy NER** | Pre-trained NER | 70-80% | Low |
| **pyresparser** | spaCy + Regex | 60-70% | Low |
| **Custom Regex** | Pattern matching | 50-60% | Very Low |

### POC Plan: Resume Parsers

#### Test Dataset Requirements
- 10 diverse CVs with known ground truth for:
  - Name
  - Email
  - Phone
  - Skills (at least 5 skills per CV)
  - Education
  - Experience years

#### Acceptance Criteria

**spaCy NER**:
- ✅ Name extraction: ≥80% accuracy
- ✅ Email extraction: ≥95% accuracy (regex-assisted)
- ✅ Phone extraction: ≥90% accuracy (regex-assisted)
- ✅ Organization extraction: ≥60% accuracy
- ✅ Processing time: <0.5s per CV

**pyresparser**:
- ✅ Name extraction: ≥70% accuracy
- ✅ Email extraction: ≥90% accuracy
- ✅ Skills extraction: ≥50% accuracy
- ✅ Processing time: <1s per CV

**Custom Regex**:
- ✅ Email extraction: ≥95% accuracy
- ✅ Phone extraction: ≥85% accuracy
- ✅ Processing time: <0.1s per CV
- ⚠️ Expected: Low accuracy for unstructured fields

#### POC Test Script

```python
# File: docs/phase-artifacts/poc_scripts/test_parsers.py

import spacy
import re
import time
import json
from typing import Dict, List

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_with_spacy(text: str) -> Dict:
    """Extract entities using spaCy NER"""
    start = time.time()
    doc = nlp(text)
    
    # Extract entities
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    
    # Regex for email and phone
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phones = re.findall(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b', text)
    
    duration = time.time() - start
    
    return {
        "name": names[0] if names else None,
        "emails": emails,
        "phones": [f"{p[0]}-{p[1]}-{p[2]}" for p in phones],
        "organizations": orgs,
        "duration": duration
    }

def extract_with_regex(text: str) -> Dict:
    """Extract using pure regex patterns"""
    start = time.time()
    
    # Email regex
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    
    # Phone regex
    phones = re.findall(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b', text)
    
    # Name regex (first line heuristic - very basic)
    lines = text.split('\n')
    name = lines[0].strip() if lines else None
    
    duration = time.time() - start
    
    return {
        "name": name,
        "emails": emails,
        "phones": [f"{p[0]}-{p[1]}-{p[2]}" for p in phones],
        "duration": duration
    }

def calculate_accuracy(extracted: Dict, ground_truth: Dict) -> Dict:
    """Calculate extraction accuracy"""
    metrics = {}
    
    # Name accuracy (exact match or substring)
    if ground_truth.get("name"):
        name_match = (
            extracted.get("name") == ground_truth["name"] or
            (extracted.get("name") and ground_truth["name"].lower() in extracted["name"].lower())
        )
        metrics["name_accuracy"] = 1.0 if name_match else 0.0
    
    # Email accuracy
    if ground_truth.get("email"):
        email_match = ground_truth["email"] in extracted.get("emails", [])
        metrics["email_accuracy"] = 1.0 if email_match else 0.0
    
    # Phone accuracy
    if ground_truth.get("phone"):
        phone_match = any(ground_truth["phone"] in p for p in extracted.get("phones", []))
        metrics["phone_accuracy"] = 1.0 if phone_match else 0.0
    
    return metrics

def run_parser_poc():
    """Run parser POC tests"""
    # Load ground truth
    with open("test_data/parser_ground_truth.json", "r") as f:
        ground_truth_data = json.load(f)
    
    results = {
        "spacy": [],
        "regex": []
    }
    
    for cv_data in ground_truth_data:
        cv_text = cv_data["text"]
        ground_truth = cv_data["ground_truth"]
        
        # Test spaCy
        spacy_result = extract_with_spacy(cv_text)
        spacy_accuracy = calculate_accuracy(spacy_result, ground_truth)
        results["spacy"].append({
            "extracted": spacy_result,
            "accuracy": spacy_accuracy,
            "duration": spacy_result["duration"]
        })
        
        # Test Regex
        regex_result = extract_with_regex(cv_text)
        regex_accuracy = calculate_accuracy(regex_result, ground_truth)
        results["regex"].append({
            "extracted": regex_result,
            "accuracy": regex_accuracy,
            "duration": regex_result["duration"]
        })
    
    # Calculate summary
    summary = {}
    for tool, tests in results.items():
        summary[tool] = {
            "avg_name_accuracy": sum(t["accuracy"].get("name_accuracy", 0) for t in tests) / len(tests),
            "avg_email_accuracy": sum(t["accuracy"].get("email_accuracy", 0) for t in tests) / len(tests),
            "avg_phone_accuracy": sum(t["accuracy"].get("phone_accuracy", 0) for t in tests) / len(tests),
            "avg_duration": sum(t["duration"] for t in tests) / len(tests),
            "total_tests": len(tests)
        }
    
    # Save results
    with open("docs/phase-artifacts/poc_results/parser_results.json", "w") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2)
    
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    run_parser_poc()
```

#### How to Run POC

```bash
# 1. Install dependencies
pip install spacy
python -m spacy download en_core_web_sm

# 2. Prepare ground truth data
# Create test_data/parser_ground_truth.json with format:
# [
#   {
#     "text": "CV text content...",
#     "ground_truth": {
#       "name": "John Doe",
#       "email": "john@example.com",
#       "phone": "123-456-7890"
#     }
#   }
# ]

# 3. Run POC
python docs/phase-artifacts/poc_scripts/test_parsers.py

# 4. Review results
cat docs/phase-artifacts/poc_results/parser_results.json
```

#### Decision Matrix

| Metric | spaCy NER | Regex Only |
|--------|-----------|------------|
| Name Accuracy | ≥80% | ≥40% |
| Email Accuracy | ≥95% | ≥95% |
| Phone Accuracy | ≥90% | ≥85% |
| Avg Duration | <0.5s | <0.1s |
| **Adopt?** | ✅ Primary | ✅ For email/phone |

**Recommendation**: Hybrid approach - spaCy for names/orgs, regex for email/phone

---

## 3. Embedding & Similarity Tools

### Candidates

| Tool | Type | Model Size | Expected Quality |
|------|------|------------|------------------|
| **Sentence-BERT (MiniLM)** | Transformer | 80MB | High (semantic) |
| **TF-IDF** | Classical | N/A | Medium (keyword) |
| **Doc2Vec** | Neural | Trainable | Medium |

### POC Plan: Embeddings

#### Test Dataset Requirements
- 5 job descriptions
- 25 CVs (5 per JD: 2 highly relevant, 2 moderately relevant, 1 irrelevant)
- Ground truth relevance scores (1-5 scale)

#### Acceptance Criteria

**Sentence-BERT**:
- ✅ Correlation with human labels: ≥0.75 (Pearson)
- ✅ Embedding time: <0.5s per document
- ✅ Top-2 candidates match human top-2: ≥80% of cases
- ✅ Model loads in <5s

**TF-IDF**:
- ✅ Correlation with human labels: ≥0.60 (Pearson)
- ✅ Embedding time: <0.1s per document
- ✅ Top-2 candidates match human top-2: ≥60% of cases

#### POC Test Script

```python
# File: docs/phase-artifacts/poc_scripts/test_embeddings.py

import time
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import pearsonr
import json

def test_sentence_bert(jd_text: str, cv_texts: List[str]) -> Dict:
    """Test Sentence-BERT embeddings"""
    start = time.time()
    
    # Load model
    model_load_start = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model_load_time = time.time() - model_load_start
    
    # Generate embeddings
    embed_start = time.time()
    jd_embedding = model.encode([jd_text])[0]
    cv_embeddings = model.encode(cv_texts)
    embed_time = time.time() - embed_start
    
    # Calculate similarities
    similarities = cosine_similarity([jd_embedding], cv_embeddings)[0]
    
    total_time = time.time() - start
    
    return {
        "similarities": similarities.tolist(),
        "model_load_time": model_load_time,
        "embed_time": embed_time,
        "total_time": total_time,
        "avg_time_per_doc": embed_time / (len(cv_texts) + 1)
    }

def test_tfidf(jd_text: str, cv_texts: List[str]) -> Dict:
    """Test TF-IDF embeddings"""
    start = time.time()
    
    # Create vectorizer
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    # Fit and transform
    all_texts = [jd_text] + cv_texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Calculate similarities
    jd_vector = tfidf_matrix[0]
    cv_vectors = tfidf_matrix[1:]
    similarities = cosine_similarity(jd_vector, cv_vectors)[0]
    
    total_time = time.time() - start
    
    return {
        "similarities": similarities.tolist(),
        "total_time": total_time,
        "avg_time_per_doc": total_time / len(all_texts)
    }

def evaluate_ranking(predicted_scores: List[float], ground_truth_scores: List[float]) -> Dict:
    """Evaluate ranking quality"""
    # Pearson correlation
    correlation, p_value = pearsonr(predicted_scores, ground_truth_scores)
    
    # Top-2 accuracy
    pred_top2 = set(np.argsort(predicted_scores)[-2:])
    true_top2 = set(np.argsort(ground_truth_scores)[-2:])
    top2_accuracy = len(pred_top2 & true_top2) / 2.0
    
    return {
        "pearson_correlation": correlation,
        "p_value": p_value,
        "top2_accuracy": top2_accuracy
    }

def run_embedding_poc():
    """Run embedding POC tests"""
    # Load test data
    with open("test_data/embedding_test_data.json", "r") as f:
        test_data = json.load(f)
    
    results = {
        "sbert": [],
        "tfidf": []
    }
    
    for test_case in test_data:
        jd_text = test_case["jd_text"]
        cv_texts = test_case["cv_texts"]
        ground_truth = test_case["relevance_scores"]
        
        # Test Sentence-BERT
        sbert_result = test_sentence_bert(jd_text, cv_texts)
        sbert_eval = evaluate_ranking(sbert_result["similarities"], ground_truth)
        results["sbert"].append({
            "performance": sbert_result,
            "evaluation": sbert_eval
        })
        
        # Test TF-IDF
        tfidf_result = test_tfidf(jd_text, cv_texts)
        tfidf_eval = evaluate_ranking(tfidf_result["similarities"], ground_truth)
        results["tfidf"].append({
            "performance": tfidf_result,
            "evaluation": tfidf_eval
        })
    
    # Calculate summary
    summary = {}
    for tool, tests in results.items():
        summary[tool] = {
            "avg_correlation": sum(t["evaluation"]["pearson_correlation"] for t in tests) / len(tests),
            "avg_top2_accuracy": sum(t["evaluation"]["top2_accuracy"] for t in tests) / len(tests),
            "avg_time_per_doc": sum(t["performance"]["avg_time_per_doc"] for t in tests) / len(tests),
            "total_tests": len(tests)
        }
    
    # Save results
    with open("docs/phase-artifacts/poc_results/embedding_results.json", "w") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2)
    
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    run_embedding_poc()
```

#### How to Run POC

```bash
# 1. Install dependencies
pip install sentence-transformers scikit-learn scipy numpy

# 2. Prepare test data
# Create test_data/embedding_test_data.json with format:
# [
#   {
#     "jd_text": "Job description text...",
#     "cv_texts": ["CV 1 text...", "CV 2 text...", ...],
#     "relevance_scores": [5, 4, 3, 2, 1]  # Ground truth (1-5 scale)
#   }
# ]

# 3. Run POC
python docs/phase-artifacts/poc_scripts/test_embeddings.py

# 4. Review results
cat docs/phase-artifacts/poc_results/embedding_results.json
```

#### Decision Matrix

| Metric | Sentence-BERT | TF-IDF |
|--------|---------------|--------|
| Correlation | ≥0.75 | ≥0.60 |
| Top-2 Accuracy | ≥80% | ≥60% |
| Avg Time/Doc | <0.5s | <0.1s |
| **Adopt?** | ✅ Primary | ✅ Secondary |

**Recommendation**: Hybrid scoring - 60% SBERT + 40% TF-IDF

---

## 4. Background Task Queue

### Candidates

| Tool | Complexity | Reliability | Resource Usage |
|------|------------|-------------|----------------|
| **Celery + Redis** | High | High | Medium |
| **RQ (Redis Queue)** | Medium | Medium | Low |
| **In-process (threading)** | Low | Low | Very Low |

### POC Plan: Task Queue

#### Test Scenarios
- Queue 10 extraction tasks simultaneously
- Queue 5 ranking tasks (heavier workload)
- Test task failure & retry
- Test task status tracking

#### Acceptance Criteria

**Celery + Redis**:
- ✅ Handle 10 concurrent tasks
- ✅ Task retry on failure
- ✅ Task status tracking
- ✅ Setup time: <30 min
- ⚠️ Adds Redis dependency

**RQ**:
- ✅ Handle 10 concurrent tasks
- ✅ Simple setup (<15 min)
- ✅ Task status tracking
- ⚠️ Adds Redis dependency

**In-process**:
- ✅ No external dependencies
- ✅ Setup time: <5 min
- ❌ No persistence across restarts
- ❌ Limited concurrency

#### POC Test Script

```python
# File: docs/phase-artifacts/poc_scripts/test_queue.py

import time
from concurrent.futures import ThreadPoolExecutor
import json

def simulate_extraction_task(cv_id: int) -> Dict:
    """Simulate CV extraction task"""
    start = time.time()
    time.sleep(2)  # Simulate OCR work
    duration = time.time() - start
    
    return {
        "cv_id": cv_id,
        "status": "completed",
        "duration": duration
    }

def simulate_ranking_task(job_id: int, num_cvs: int) -> Dict:
    """Simulate ranking task"""
    start = time.time()
    time.sleep(5)  # Simulate embedding + scoring
    duration = time.time() - start
    
    return {
        "job_id": job_id,
        "num_cvs": num_cvs,
        "status": "completed",
        "duration": duration
    }

def test_in_process_queue():
    """Test in-process threading"""
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit 10 extraction tasks
        extraction_futures = [executor.submit(simulate_extraction_task, i) for i in range(10)]
        
        # Wait for completion
        extraction_results = [f.result() for f in extraction_futures]
    
    total_time = time.time() - start
    
    return {
        "total_time": total_time,
        "tasks_completed": len(extraction_results),
        "avg_task_time": sum(r["duration"] for r in extraction_results) / len(extraction_results)
    }

def run_queue_poc():
    """Run queue POC"""
    results = {}
    
    # Test in-process
    results["in_process"] = test_in_process_queue()
    
    # Save results
    with open("docs/phase-artifacts/poc_results/queue_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run_queue_poc()
```

#### Decision Matrix

| Metric | Celery | RQ | In-Process |
|--------|--------|----|-----------| 
| Concurrent Tasks | ✅ | ✅ | ⚠️ |
| Persistence | ✅ | ✅ | ❌ |
| Setup Complexity | High | Medium | Low |
| **Adopt?** | ⚠️ Phase 2+ | ✅ Phase 1 | ❌ |

**Recommendation**: Start with **RQ** for MVP, migrate to Celery if needed

---

## 5. POC Execution Checklist

### Pre-POC Setup

- [ ] Create `docs/phase-artifacts/` directory structure
- [ ] Create `test_data/` directory with subdirectories
- [ ] Prepare sample CVs (5 text PDFs, 5 scanned, 3 DOCX)
- [ ] Create ground truth JSON files for parser and embedding tests
- [ ] Install base dependencies: `pip install -r requirements-poc.txt`

### POC Execution Order

1. **OCR Tools** (Day 1)
   - [ ] Run `test_ocr.py`
   - [ ] Review `ocr_results.json`
   - [ ] Document any failures or edge cases
   - [ ] Make adopt/reject decision

2. **Resume Parsers** (Day 2)
   - [ ] Run `test_parsers.py`
   - [ ] Review `parser_results.json`
   - [ ] Compare accuracy vs ground truth
   - [ ] Make adopt/reject decision

3. **Embeddings** (Day 3)
   - [ ] Run `test_embeddings.py`
   - [ ] Review `embedding_results.json`
   - [ ] Validate correlation with human labels
   - [ ] Make adopt/reject decision

4. **Task Queue** (Day 4)
   - [ ] Run `test_queue.py`
   - [ ] Test RQ setup (if Redis available)
   - [ ] Make adopt/reject decision

### Post-POC Deliverables

- [ ] `docs/phase-artifacts/poc_results/` contains all JSON results
- [ ] `docs/phase-artifacts/POC_SUMMARY.md` with recommendations
- [ ] `docs/phase-artifacts/TOOL_DECISIONS.md` with final stack
- [ ] Update `requirements.txt` with approved tools

---

## 6. Recommendation Table (To Be Filled After POC)

| Component | Tool | Status | Reason |
|-----------|------|--------|--------|
| PDF Text Extraction | PyMuPDF | ⏳ Pending POC | TBD |
| DOCX Extraction | python-docx | ⏳ Pending POC | TBD |
| OCR (Scanned) | PaddleOCR | ⏳ Pending POC | TBD |
| OCR Fallback | Tesseract | ⏳ Pending POC | TBD |
| Name/Org Parsing | spaCy NER | ⏳ Pending POC | TBD |
| Email/Phone Parsing | Regex | ⏳ Pending POC | TBD |
| Semantic Embedding | Sentence-BERT | ⏳ Pending POC | TBD |
| Keyword Matching | TF-IDF | ⏳ Pending POC | TBD |
| Task Queue | RQ | ⏳ Pending POC | TBD |

---

## 7. Next Steps

1. **Review this POC plan** and approve/modify
2. **Prepare test data** (I can help generate sample CVs if needed)
3. **Execute POCs** in order (4 days estimated)
4. **Review POC results** together
5. **Make final tool decisions**
6. **Proceed to Phase 1 planning** only after approval

---

## 8. Rollback Plan

If any POC fails to meet acceptance criteria:

1. **Document failure mode** (what went wrong, why)
2. **Evaluate alternative** from candidate list
3. **Run POC for alternative**
4. **If all alternatives fail**: Escalate for requirements review

---

**Status**: Awaiting approval to execute POCs  
**Estimated POC Duration**: 4 days  
**Estimated POC Effort**: 16-20 hours  

---

**Next Action**: Please approve this POC plan, and I will either:
A) Execute the POCs and present results, OR
B) Provide you with the exact commands/scripts to run POCs yourself
