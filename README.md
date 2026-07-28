# Unlimited-OCR Backend

Baidu Unlimited-OCR backend for local, private OCR processing using vision-language models.

- **Zero API costs** — runs locally on GPU
- **Private** — no cloud submission
- **Optimized for RTX 4060** (8GB VRAM) using native bfloat16
- **Handles handwritten & printed text** with high accuracy

## Quick Start

### 1. Install Dependencies

**For GPU (RTX 4060 with CUDA 12.1) — RECOMMENDED:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install --upgrade pip
# Install torch with CUDA 12.1 support (required for GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# Install remaining dependencies
pip install -r requirements.txt
```

**For CPU only (slow, not recommended):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt  # Gets CPU-only torch
```

**Verify installation:**
```powershell
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### 2. Use Directly

```python
from unlimited_ocr import UnlimitedOCR

ocr = UnlimitedOCR()
text, details = ocr.process_image("path/to/image.jpg")
print(text)
```

### 3. Use via JournalOCR Registry

```python
from ocr_backend import OCRRegistry

ocr = OCRRegistry.get("unlimited-ocr")
text, details = ocr.process_image("path/to/image.jpg")
```

## Hardware Requirements

- **GPU**: RTX 4060 or better (8GB VRAM minimum)
- **CUDA**: 12.1 or compatible
- **Torch**: 2.0+
- **Python**: 3.11+

## Environment Setup

Create a `.env` file if you need custom model paths:

```bash
# Optional: custom model cache location
UNLIMITED_OCR_CACHE=/path/to/cache

# Optional: custom Unlimited-OCR repo location (for vendored updates)
UNLIMITED_OCR_REPO=/path/to/Unlimited-OCR
```

## Architecture

```
UnlimitedOCR (this package)
├── ocr_unlimited.py          # Main class (no deps on JournalOCR)
├── Unlimited-OCR/            # Vendored copy of Baidu's repo (static)
├── requirements.txt          # ML stack only
└── pyproject.toml           # Package metadata
```

**Design**: UnlimitedOCR is **independent** of JournalOCR. JournalOCR imports it via registry.

## Updating Vendored Unlimited-OCR

The `./Unlimited-OCR/` folder is a static snapshot of https://github.com/baidu/Unlimited-OCR.

To update:
1. Test new Baidu release in isolation
2. Back up current `./Unlimited-OCR/`
3. Copy new version
4. Verify `ocr_unlimited.py` still works
5. Commit with message: `chore: Update vendored Unlimited-OCR to <commit-hash>`

## Known Quirks

- **First run is slow** — downloads model (~8GB) from Hugging Face
- **Model inference takes ~30-60s** per image (GPU-dependent)
- **Falls back to CPU** if CUDA unavailable (very slow, not recommended)
- **Requires 8GB+ VRAM** — bfloat16 is efficient but still memory-intensive

## Troubleshooting

### CUDA Not Found
```bash
# Verify CUDA installation
python -c "import torch; print(torch.cuda.is_available())"
```

### Out of Memory
- Reduce batch size (set in model inference call)
- Check other GPU processes (`nvidia-smi`)
- Consider CPU mode (not recommended for production)

### Model Download Hangs
- Check internet connection
- Verify HuggingFace is accessible
- Set custom cache location in `.env`

## Integration with JournalOCR

When used via JournalOCR:
1. Set `UNLIMITED_OCR_PATH` env var to this directory
2. JournalOCR's `ocr_backend.py` auto-registers UnlimitedOCR
3. Use registry: `OCRRegistry.get("unlimited-ocr")`

## References

- [Baidu Unlimited-OCR](https://github.com/baidu/Unlimited-OCR)
- [PyTorch](https://pytorch.org/)
- [HuggingFace Transformers](https://huggingface.co/transformers/)
