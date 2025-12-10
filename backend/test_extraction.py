"""
Standalone Test Script for CV/JD Extraction and Parsing
Run this script to test extraction and parsing services with your own files.

Usage:
    python test_extraction.py --file path/to/your/cv.pdf
    python test_extraction.py --file path/to/your/jd.docx --type jd
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add parent directory to path to import services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.extraction_service import extract_text
from app.services.parsing_service import parse_resume


async def test_extraction(file_path: str, doc_type: str = "cv"):
    """
    Test extraction and parsing on a single file.
    
    Args:
        file_path: Path to PDF/DOCX/image file
        doc_type: "cv" or "jd"
    """
    print("=" * 80)
    print(f"TESTING EXTRACTION: {file_path}")
    print("=" * 80)
    
    # Check file exists
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found: {file_path}")
        return
    
    # Detect MIME type
    ext = Path(file_path).suffix.lower()
    mime_type_map = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
    }
    
    mime_type = mime_type_map.get(ext, 'application/octet-stream')
    print(f"\n📄 File: {Path(file_path).name}")
    print(f"📋 Type: {mime_type}")
    print(f"📊 Size: {os.path.getsize(file_path)} bytes")
    
    # Extract text
    print("\n" + "─" * 80)
    print("STEP 1: TEXT EXTRACTION")
    print("─" * 80)
    
    extracted_text, error = await extract_text(file_path, mime_type)
    
    if error:
        print(f"❌ EXTRACTION ERROR: {error}")
        print(f"📝 Partial text extracted: {len(extracted_text)} characters")
    else:
        print(f"✅ EXTRACTION SUCCESS")
        print(f"📝 Extracted: {len(extracted_text)} characters")
    
    # Show preview
    print("\n📖 TEXT PREVIEW (first 500 chars):")
    print("─" * 80)
    print(extracted_text[:500])
    if len(extracted_text) > 500:
        print("...")
    print("─" * 80)
    
    # Parse if it's a CV
    parsed_data = {}
    if doc_type == "cv" and extracted_text:
        print("\n" + "─" * 80)
        print("STEP 2: RESUME PARSING")
        print("─" * 80)
        
        parsed_data = await parse_resume(extracted_text)
        
        print("\n✅ PARSING RESULTS:")
        print("─" * 80)
        print(f"👤 Name:       {parsed_data.get('name') or '❌ Not found'}")
        print(f"📧 Email:      {parsed_data.get('email') or '❌ Not found'}")
        print(f"📱 Phone:      {parsed_data.get('phone') or '❌ Not found'}")
        print(f"💼 Experience: {parsed_data.get('experience_years') or '❌ Not found'} years")
        print(f"🔧 Skills:     {len(parsed_data.get('skills', []))} found")
        
        if parsed_data.get('skills'):
            print("\n🔧 EXTRACTED SKILLS:")
            print("─" * 80)
            skills = parsed_data['skills']
            # Print in columns
            for i in range(0, len(skills), 5):
                print("  " + ", ".join(skills[i:i+5]))
        
        # Save parsed data to JSON
        output_file = f"{Path(file_path).stem}_parsed.json"
        with open(output_file, 'w') as f:
            json.dump({
                'file': file_path,
                'extracted_text': extracted_text,
                'parsed_data': parsed_data,
                'extraction_error': error
            }, f, indent=2)
        
        print(f"\n💾 Full results saved to: {output_file}")
    
    # Save full text
    text_output_file = f"{Path(file_path).stem}_extracted.txt"
    with open(text_output_file, 'w') as f:
        f.write(extracted_text)
    
    print(f"💾 Full extracted text saved to: {text_output_file}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    return {
        'extracted_text': extracted_text,
        'parsed_data': parsed_data if doc_type == "cv" else None,
        'error': error
    }


async def test_batch(directory: str, doc_type: str = "cv"):
    """
    Test extraction on all files in a directory.
    
    Args:
        directory: Path to directory containing files
        doc_type: "cv" or "jd"
    """
    print("=" * 80)
    print(f"BATCH TESTING: {directory}")
    print("=" * 80)
    
    # Find all supported files
    supported_exts = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png']
    files = []
    
    for ext in supported_exts:
        files.extend(Path(directory).glob(f"*{ext}"))
    
    if not files:
        print(f"❌ No supported files found in {directory}")
        return
    
    print(f"\n📁 Found {len(files)} files to process\n")
    
    results = []
    for i, file_path in enumerate(files, 1):
        print(f"\n{'=' * 80}")
        print(f"PROCESSING FILE {i}/{len(files)}")
        print(f"{'=' * 80}")
        
        result = await test_extraction(str(file_path), doc_type)
        results.append({
            'file': str(file_path),
            'success': result['error'] is None,
            'chars_extracted': len(result['extracted_text']),
            'error': result['error']
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("BATCH TEST SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for r in results if r['success'])
    print(f"\n✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    
    print("\n📊 RESULTS:")
    print("─" * 80)
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {Path(r['file']).name}: {r['chars_extracted']} chars")
        if r['error']:
            print(f"   Error: {r['error']}")
    
    print("=" * 80)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test CV/JD extraction and parsing')
    parser.add_argument('--file', help='Path to single file to test')
    parser.add_argument('--dir', help='Path to directory for batch testing')
    parser.add_argument('--type', choices=['cv', 'jd'], default='cv', 
                       help='Document type: cv or jd (default: cv)')
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        print("❌ ERROR: Please specify either --file or --dir")
        print("\nExamples:")
        print("  python test_extraction.py --file my_cv.pdf")
        print("  python test_extraction.py --file job_description.docx --type jd")
        print("  python test_extraction.py --dir ./test_cvs --type cv")
        return
    
    if args.file:
        asyncio.run(test_extraction(args.file, args.type))
    elif args.dir:
        asyncio.run(test_batch(args.dir, args.type))


if __name__ == "__main__":
    main()
