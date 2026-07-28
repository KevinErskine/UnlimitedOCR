#!/usr/bin/env python3
"""Generic OCR test script for UnlimitedOCR

Usage:
  python test_unlimited_ocr.py [image_file]

Examples:
  python test_unlimited_ocr.py Test_File.jpg
  python test_unlimited_ocr.py test_image.png
  python test_unlimited_ocr.py document.jpg  # Default: Test_File.jpg
"""

import sys
from pathlib import Path
import time

# Add parent directory to path so we can import unlimited_ocr
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_ocr_test(image_path):
    """Run OCR test on specified image file"""

    # Setup logging to both stdout and file
    test_dir = Path(__file__).parent
    image_file = Path(image_path)
    log_filename = image_file.name + ".log"
    log_file = test_dir / log_filename

    log_handle = open(log_file, "w", encoding="utf-8")

    def log_print(*args, **kwargs):
        """Print to both stdout and log file"""
        print(*args, **kwargs)
        print(*args, file=log_handle, **kwargs)
        log_handle.flush()

    log_print("=" * 70)
    log_print(f"Testing UnlimitedOCR with {image_file.name}")
    log_print("=" * 70)

    # Import and initialize
    from unlimited_ocr import UnlimitedOCR

    ocr = UnlimitedOCR()
    log_print(f"\n✓ Initialized: {ocr.get_name()}")
    log_print(f"  Device: {ocr._device}")
    log_print(f"  GPU Memory: {ocr._gpu_memory:.1f}GB")

    # Verify image exists
    if not image_file.exists():
        log_print(f"\n❌ Test image not found: {image_file.absolute()}")
        log_handle.close()
        return False

    file_size_mb = image_file.stat().st_size / (1024*1024)
    log_print(f"\nProcessing: {image_file.name} ({file_size_mb:.2f}MB)")
    log_print("-" * 70)

    try:
        start = time.time()
        text, details = ocr.process_image(str(image_file))
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

        log_print(f"\n✓ Log file: {log_file}")
        log_handle.close()
        return True

    except Exception as e:
        log_print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc(file=log_handle)
        log_handle.close()
        return False

if __name__ == "__main__":
    test_dir = Path(__file__).parent

    # Get image file from command line or use default
    if len(sys.argv) > 1:
        image_file = Path(sys.argv[1])
        # If relative path, check if it exists in test directory
        if not image_file.is_absolute() and not image_file.exists():
            test_image = test_dir / image_file.name
            if test_image.exists():
                image_file = test_image
    else:
        # Default to Test_File.jpg if available
        default_file = test_dir / "Test_File.jpg"
        if default_file.exists():
            image_file = default_file
        else:
            print("Usage: python test_unlimited_ocr.py <image_file>")
            print("  No default image found. Please specify an image file.")
            sys.exit(1)

    success = run_ocr_test(str(image_file))
    sys.exit(0 if success else 1)
