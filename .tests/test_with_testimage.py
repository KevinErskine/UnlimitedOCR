#!/usr/bin/env python3
"""Test UnlimitedOCR with Test_File.jpg"""

import sys
from pathlib import Path
import time

# Setup logging to both stdout and file
log_file = Path(__file__).parent / "test_with_testimage.log"
log_handle = open(log_file, "w", encoding="utf-8")

def log_print(*args, **kwargs):
    """Print to both stdout and log file"""
    print(*args, **kwargs)
    print(*args, file=log_handle, **kwargs)
    log_handle.flush()

log_print("=" * 70)
log_print("Testing UnlimitedOCR with Test_File.jpg")
log_print("=" * 70)

# Import and initialize
from unlimited_ocr import UnlimitedOCR

ocr = UnlimitedOCR()
log_print(f"\n✓ Initialized: {ocr.get_name()}")
log_print(f"  Device: {ocr._device}")
log_print(f"  GPU Memory: {ocr._gpu_memory:.1f}GB")

# Test image path
test_image = Path(__file__).parent / "Test_File.jpg"
if not test_image.exists():
    log_print(f"\n❌ Test image not found: {test_image}")
    log_handle.close()
    sys.exit(1)

log_print(f"\nProcessing: {test_image.name} ({test_image.stat().st_size / (1024*1024):.2f}MB)")
log_print("-" * 70)

try:
    start = time.time()
    text, details = ocr.process_image(str(test_image))
    elapsed = time.time() - start

    log_print("-" * 70)
    log_print(f"\n✓ OCR completed in {elapsed:.2f}s\n")

    log_print("EXTRACTED TEXT:")
    log_print("=" * 70)
    if text:
        log_print(text)
    else:
        log_print("[NO TEXT EXTRACTED]")
    log_print("=" * 70)

    if details:
        log_print(f"\nCharacter details: {len(details)} chars")
        log_print("First 20 characters:")
        for i, detail in enumerate(details[:20]):
            char = detail.get('char', '?')
            conf = detail.get('confidence', 0)
            log_print(f"  {i+1:2d}. '{char}' confidence: {conf:.2%}")
    else:
        log_print("\n[NO CHARACTER DETAILS]")

except Exception as e:
    log_print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc(file=log_handle)
    log_handle.close()
    sys.exit(1)

log_handle.close()
