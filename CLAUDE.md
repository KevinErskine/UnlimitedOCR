# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup & Environment

**Python**: 3.11+ (tested on 3.11, 3.12)

**CUDA is required for GPU inference:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Standard `pip install -r requirements.txt` installs CPU-only torch, which is extremely slow and not production-ready. Always use the CUDA 12.1 index URL above.

**Verify installation:**
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

## Critical Dependencies

- **transformers==4.57.1** — locked version, do NOT upgrade without testing model loading
- **torch>=2.0.0 with CUDA 12.1 support** — version sync with transformers is critical
- **RTX 4060 target** — 8GB VRAM minimum; bfloat16 is hardware-native and efficient

If dependency versions are changed, test by running `test_with_testimage.py` to ensure model loads and inference works.

## Architecture

**UnlimitedOCR** is a standalone Python package wrapping Baidu's Unlimited-OCR vision-language model. It implements the OCR backend interface for integration with JournalOCR via auto-registry:

```python
from unlimited_ocr import UnlimitedOCR
ocr = UnlimitedOCR()
text, char_details = ocr.process_image("path/to/image.jpg")
```

**Key design decisions:**
- **Class-level model caching** (`_model`, `_tokenizer` static) — shared across all instances to avoid redundant loads
- **Lazy loading** — model downloads from Hugging Face on first `process_image()` call (~8GB, can take minutes)
- **Inference timeout** — 120-second default; logs warning if exceeded (daemon thread + `join(timeout)`)
- **Vendored dependency** — `Unlimited-OCR/` is a static snapshot of https://github.com/baidu/Unlimited-OCR; manual updates only after testing

## Inference Behavior

- **Inference time** — 30–60s per image on RTX 4060 (GPU-dependent)
- **Prompt format** — must start with `<image>` tag (Baidu-specific requirement)
- **Max tokens** — 16384 (balanced to avoid hallucination)
- **Confidence** — per-character confidence is uniform/synthetic (deterministic local inference, not ML confidence)
- **Output** — Markdown format with image references; model stdout/stderr is suppressed during inference
- **Cost** — zero (local inference, no API calls or token counting)

## Testing

Test changes with real images to verify OCR quality. A `tests/` folder holds test inputs and scripts:

- `tests/test_with_testimage.py` — validates basic OCR on `.jpg` files
- `tests/test_with_pdf.py` — validates PDF → image conversion and OCR
- Test data: `TestImage.jpg`, `TestDocument.pdf` (at project root)

Run tests from project root:
```powershell
python tests/test_with_testimage.py
python tests/test_with_pdf.py
```

All test output should show extracted character count > 0 and confidence ≥ 95%.

## Integration with JournalOCR

UnlimitedOCR is auto-discovered by JournalOCR's `OCRRegistry` when:
1. The `unlimited_ocr` package is importable
2. `UNLIMITED_OCR_PATH` env var points to this directory (optional, for external repos)

JournalOCR calls: `OCRRegistry.get("unlimited-ocr")` → returns UnlimitedOCR instance implementing `process_image()` and `get_name()`.

**Do NOT add JournalOCR dependencies to UnlimitedOCR.** It must remain independent and reusable.

## Known Quirks & Limitations

- **First-run latency** — model download (~8GB) can take 5–10 minutes; cache location is `~/.cache/huggingface/`
- **Thread safety** — class-level model caching is not fully thread-safe (GIL helps, but risky under heavy concurrency)
- **Timeout cleanup race** — if inference hangs past 120s timeout, temp directory may be deleted while inference still running; monitor logs
- **GPU memory** — requires 8GB+ VRAM; falls back to CPU if CUDA unavailable (very slow, not recommended)

## Environment Variables

- `UNLIMITED_OCR_CACHE` — custom Hugging Face cache location (default: `~/.cache/huggingface/`)
- `UNLIMITED_OCR_REPO` — override vendored Unlimited-OCR path (default: local `./unlimited_ocr/Unlimited-OCR/`)

## Updating Vendored Unlimited-OCR

The `./unlimited_ocr/Unlimited-OCR/` folder is a static snapshot. To update:
1. Test new Baidu release in isolation
2. Back up current `./unlimited_ocr/Unlimited-OCR/`
3. Replace with new version
4. Run test suite to verify `ocr_unlimited.py` still works
5. Commit: `chore: Update vendored Unlimited-OCR to <commit-hash>`

Do not auto-update; always verify compatibility first.
