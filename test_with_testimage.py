#!/usr/bin/env python3
"""Test UnlimitedOCR with TestImage.jpg"""

import sys
from pathlib import Path
import time

print("=" * 70)
print("Testing UnlimitedOCR with TestImage.jpg")
print("=" * 70)

# Import and initialize
from unlimited_ocr import UnlimitedOCR

ocr = UnlimitedOCR()
print(f"\n✓ Initialized: {ocr.get_name()}")
print(f"  Device: {ocr._device}")
print(f"  GPU Memory: {ocr._gpu_memory:.1f}GB")

# Test image path
test_image = Path(__file__).parent / "TestImage.jpg"
if not test_image.exists():
    print(f"\n❌ Test image not found: {test_image}")
    sys.exit(1)

print(f"\nProcessing: {test_image.name} ({test_image.stat().st_size / (1024*1024):.2f}MB)")
print("-" * 70)

try:
    start = time.time()
    text, details = ocr.process_image(str(test_image))
    elapsed = time.time() - start

    print("-" * 70)
    print(f"\n✓ OCR completed in {elapsed:.2f}s\n")

    print("EXTRACTED TEXT:")
    print("=" * 70)
    if text:
        print(text)
    else:
        print("[NO TEXT EXTRACTED]")
    print("=" * 70)

    if details:
        print(f"\nCharacter details: {len(details)} chars")
        print("First 20 characters:")
        for i, detail in enumerate(details[:20]):
            char = detail.get('char', '?')
            conf = detail.get('confidence', 0)
            print(f"  {i+1:2d}. '{char}' confidence: {conf:.2%}")
    else:
        print("\n[NO CHARACTER DETAILS]")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
