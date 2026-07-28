#!/usr/bin/env python3
"""Test UnlimitedOCR independently on a PDF"""

import sys
from pathlib import Path
import time

# Test 1: Import UnlimitedOCR
print("=" * 60)
print("TEST 1: Import UnlimitedOCR")
print("=" * 60)

try:
    from unlimited_ocr import UnlimitedOCR
    print("✓ Successfully imported UnlimitedOCR")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: Initialize model
print("\n" + "=" * 60)
print("TEST 2: Initialize UnlimitedOCR")
print("=" * 60)

try:
    ocr = UnlimitedOCR()
    print(f"✓ Initialized: {ocr.get_name()}")
    print(f"  Device: {ocr._device}")
    print(f"  GPU Memory: {ocr._gpu_memory:.1f}GB")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test 3: Convert PDF to image
print("\n" + "=" * 60)
print("TEST 3: Convert PDF to Image")
print("=" * 60)

pdf_path = Path(__file__).parent / "TestDocument.pdf"
if not pdf_path.exists():
    print(f"❌ Test PDF not found: {pdf_path}")
    sys.exit(1)

try:
    import fitz  # PyMuPDF
    print(f"✓ PyMuPDF available")

    # Open PDF and convert first page to image
    pdf_doc = fitz.open(str(pdf_path))
    print(f"  PDF has {len(pdf_doc)} pages")

    # Render first page to image
    page = pdf_doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR

    # Save as temp image
    temp_image = Path(__file__).parent / "test_page_0.png"
    pix.save(str(temp_image))
    print(f"✓ Converted page 0 to image: {temp_image.name}")

except ImportError:
    print("⚠️  PyMuPDF not installed. Using a dummy test image instead...")
    # Create a simple test image if PyMuPDF not available
    try:
        from PIL import Image, ImageDraw, ImageFont
        temp_image = Path(__file__).parent / "test_page_0.png"
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Test OCR Document\nUnlimitedOCR Test", fill='black')
        img.save(str(temp_image))
        print(f"✓ Created test image: {temp_image.name}")
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        sys.exit(1)

# Test 4: Run OCR
print("\n" + "=" * 60)
print("TEST 4: Run OCR on Image")
print("=" * 60)

try:
    print(f"Processing: {temp_image.name}")
    start_time = time.time()

    text, details = ocr.process_image(str(temp_image))

    elapsed = time.time() - start_time
    print(f"✓ OCR completed in {elapsed:.2f}s")
    print(f"\n--- Extracted Text ---")
    print(text)
    print(f"\n--- Character Details ---")
    if details:
        print(f"Total characters: {len(details)}")
        print(f"First 10 chars with confidence:")
        for i, detail in enumerate(details[:10]):
            print(f"  {i+1}. '{detail.get('char', '?')}' - confidence: {detail.get('confidence', 0):.2%}")

    # Cleanup
    temp_image.unlink()
    print(f"\n✓ Cleaned up {temp_image.name}")

except Exception as e:
    print(f"❌ OCR failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
