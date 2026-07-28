#!/usr/bin/env python3
"""Baidu Unlimited-OCR backend for local, private OCR processing (vision-language model)"""
"""Reference: https://github.com/baidu/Unlimited-OCR"""
"""Optimized for RTX 4060 (8GB VRAM) using 4-bit quantization"""

import os
import json
import re
import time
import threading
from pathlib import Path
from typing import Tuple, List, Dict

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
except ImportError:
    raise ImportError(
        "torch and transformers not installed. Run:\n"
        "  pip install torch transformers pillow"
    )


class UnlimitedOCR:
    """Baidu Unlimited-OCR backend for handwritten and printed text OCR (RTX 4060 optimized)

    Implements the OCR backend interface:
    - process_image(image_path: str) -> Tuple[str, List[Dict]]
    - get_name() -> str
    """

    _model = None
    _tokenizer = None

    def __init__(self):
        """Initialize Unlimited-OCR model (lazy load on first use)"""
        self.output_folder = None
        self.last_token_count = 0
        self.last_token_cost = 0.0
        self.model_name = 'baidu/Unlimited-OCR'
        self.model_revision = '2a06ebf2d6f600f95fd2b99f6ccdee18a52e3b8f'
        self._device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._gpu_memory = self._get_gpu_memory()
        # Diagnostic tracking
        self.last_error = None
        self.last_model_output = None
        self.last_inference_time = 0

    @staticmethod
    def _get_gpu_memory() -> int:
        """Get available GPU VRAM in GB"""
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        return 0

    def _ensure_model_loaded(self):
        """Load model and tokenizer on first use (cached across instances, native bfloat16)"""
        if UnlimitedOCR._model is None:
            print(f"      [Unlimited-OCR] Loading model from {self.model_name}...")
            print(f"      [Unlimited-OCR] Device: {self._device}")
            print(f"      [Unlimited-OCR] GPU Memory: {self._gpu_memory:.1f}GB")

            if self._device == 'cuda':
                print(f"      [Unlimited-OCR] Using native bfloat16 (hardware-optimized for RTX 4060)")

            UnlimitedOCR._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                revision=self.model_revision,
                trust_remote_code=True
            )

            # Load with native bfloat16 (efficient, faster than 4-bit, fits in 8GB)
            UnlimitedOCR._model = AutoModel.from_pretrained(
                self.model_name,
                revision=self.model_revision,
                trust_remote_code=True,
                dtype=torch.bfloat16,
                device_map="auto"
            ).eval()

            print(f"      [Unlimited-OCR] Model loaded successfully")

    def set_output_folder(self, output_folder: str):
        """Set output folder for saving responses"""
        self.output_folder = output_folder

    def get_name(self) -> str:
        return "Baidu Unlimited-OCR (Local VLM - Private, Zero-Cost)"

    def process_image(self, image_path: str) -> Tuple[str, List[Dict]]:
        """
        Run Unlimited-OCR on image using model.infer() custom method.

        Args:
            image_path: Path to JPG/PNG image

        Returns:
            Tuple of (ocr_text, ocr_details) where:
            - ocr_text: Full extracted text
            - ocr_details: List of {'char': str, 'confidence': float}
        """
        try:
            # Ensure model is loaded
            self._ensure_model_loaded()

            p = Path(image_path)
            if not p.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            start_time = time.time()

            # Create temp output directory for model inference
            import tempfile
            temp_output_dir = tempfile.mkdtemp(prefix="unlimited_ocr_")

            # Prompt MUST start with <image> flag (Baidu's custom requirement)
            prompt_text = (
                "<image>Transcribe this document, which is completely handwritten using "
                "a mix of hand-printed block text and connected cursive script. "
                "Transcribe the paragraphs verbatim into Markdown, maintaining the natural reading order. "
                "Separate distinct blocks of text with double line breaks. "
                "Replace any word that is completely illegible or obscured with '[unclear]'. "
                "Use plain text for ordinal suffixes (st, nd, rd, th) rather than LaTeX notation."
            )

            # Run OCR using model.infer() custom method with timeout protection
            inference_timeout = 120  # 2 minutes max
            inference_completed = False

            def run_inference():
                nonlocal inference_completed
                # Suppress model's raw inference output (detection tags, intermediate results)
                import os, sys
                with open(os.devnull, 'w') as devnull:
                    old_stdout, old_stderr = sys.stdout, sys.stderr
                    try:
                        sys.stdout = sys.stderr = devnull
                        with torch.no_grad():
                            UnlimitedOCR._model.infer(
                                tokenizer=UnlimitedOCR._tokenizer,
                                prompt=prompt_text,
                                image_file=str(image_path),
                                output_path=temp_output_dir,
                                base_size=1024,        # Optimal canvas sizing
                                image_size=640,        # Crop processing resolution
                                crop_mode=True,        # "gundam" mode for detailed text lines
                                max_length=16384,      # Balanced: high enough for Image019, guards against Image090 hallucination
                                save_results=True      # Auto-save to output folder
                            )
                    finally:
                        sys.stdout, sys.stderr = old_stdout, old_stderr
                inference_completed = True

            # Run in thread so we can timeout
            inference_thread = threading.Thread(target=run_inference)
            inference_thread.daemon = True
            inference_thread.start()
            inference_thread.join(timeout=inference_timeout)

            if inference_thread.is_alive():
                print(f"      [Unlimited-OCR] WARNING: Inference timeout after {inference_timeout}s, using partial output")
                elapsed = inference_timeout
            else:
                elapsed = time.time() - start_time

            self.last_inference_time = elapsed

            # Diagnostic: List all files created by model.infer()
            self._log_output_directory_structure(temp_output_dir, p.stem)

            # Extract text from output directory (model saves as .txt or .md)
            ocr_text = self._extract_text_from_output(temp_output_dir, p.stem)
            self.last_model_output = ocr_text  # Track for diagnostics
            self.last_error = None  # Clear any previous errors

            # For local inference, confidence is uniform (high) since it's deterministic
            self.last_token_count = 0  # Local inference, no token counting
            self.last_token_cost = 0.0  # Free local processing

            print(f"      [Unlimited-OCR] Extracted {len(ocr_text)} chars in {elapsed:.1f}s")

            # Save response for debugging
            if self.output_folder:
                self._save_response(image_path, ocr_text)

            # Convert to per-character confidence
            ocr_details = self._convert_to_char_confidence(ocr_text)

            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_output_dir, ignore_errors=True)

            return ocr_text, ocr_details

        except Exception as e:
            error_msg = f"Unlimited-OCR Error: {e}"
            self.last_error = error_msg  # Track error for diagnostics
            print(f"      [Unlimited-OCR] ERROR: {error_msg}")
            if self.output_folder:
                self._save_response(image_path, str(e), error=True)
            raise RuntimeError(f"Unlimited-OCR OCR failed: {e}")

    def _log_output_directory_structure(self, output_dir: str, base_name: str):
        """Log all files created by model.infer() for diagnostics"""
        try:
            output_path = Path(output_dir)
            print(f"      [Unlimited-OCR] Output directory structure for {base_name}:")

            if not output_path.exists():
                print(f"      [Unlimited-OCR]   WARNING: Output directory does not exist: {output_dir}")
                return

            # List all files recursively
            all_files = list(output_path.rglob("*"))
            if not all_files:
                print(f"      [Unlimited-OCR]   (empty directory)")
                return

            # Separate files and directories
            files = [f for f in all_files if f.is_file()]
            dirs = [f for f in all_files if f.is_dir()]

            # Log directories
            for d in sorted(dirs):
                rel_path = d.relative_to(output_path)
                print(f"      [Unlimited-OCR]   📁 {rel_path}/")

            # Log files with sizes
            for f in sorted(files):
                rel_path = f.relative_to(output_path)
                size_kb = f.stat().st_size / 1024
                print(f"      [Unlimited-OCR]   📄 {rel_path} ({size_kb:.1f} KB)")

            # Specifically check for images directory
            images_dir = output_path / "images"
            if images_dir.exists():
                image_files = list(images_dir.glob("*"))
                print(f"      [Unlimited-OCR]   Found {len(image_files)} images in images/ directory")

        except Exception as e:
            print(f"      [Unlimited-OCR] Error listing output directory: {e}")

    def _extract_text_from_output(self, output_dir: str, base_name: str) -> str:
        """
        Extract text from model output files saved to disk.

        The model.infer() method saves results to:
        - result.md (OCR text with image references)
        - images/ (extracted images)

        Also copies images directory to persistent output folder for embedding in DOCX.
        """
        from pathlib import Path
        import shutil

        output_path = Path(output_dir)

        # Unlimited-OCR saves as result.md specifically
        text = ""
        result_md_path = output_path / "result.md"
        if result_md_path.exists():
            try:
                text = result_md_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"      [Unlimited-OCR] Warning: Could not read {result_md_path}: {e}")

        # If result.md not found, fallback to generic patterns
        if not text:
            patterns = [
                f"{base_name}.txt",
                f"{base_name}.md",
                f"{base_name}.markdown",
            ]
            for pattern in patterns:
                file_path = output_path / pattern
                if file_path.exists():
                    try:
                        text = file_path.read_text(encoding="utf-8")
                        break
                    except Exception as e:
                        print(f"      [Unlimited-OCR] Warning: Could not read {file_path}: {e}")

        if not text:
            for file_path in output_path.glob("*.txt"):
                try:
                    text = file_path.read_text(encoding="utf-8")
                    break
                except Exception:
                    continue

        if not text:
            for file_path in output_path.glob("*.md"):
                try:
                    text = file_path.read_text(encoding="utf-8")
                    break
                except Exception:
                    continue

        # Copy images directory to persistent output folder if it exists
        if self.output_folder:
            images_src = output_path / "images"
            if images_src.exists():
                images_dst = Path(self.output_folder) / "images"
                try:
                    # List source before copy for debugging
                    src_files = list(images_src.glob("*"))
                    print(f"      [Unlimited-OCR] Source images ({len(src_files)} files): {images_src}")

                    if images_dst.exists():
                        shutil.rmtree(images_dst)
                    shutil.copytree(images_src, images_dst)

                    # Verify copy
                    dst_files = list(images_dst.glob("*"))
                    print(f"      [Unlimited-OCR] Copied {len(dst_files)} images to: {images_dst}")
                    for f in dst_files:
                        print(f"      [Unlimited-OCR]   - {f.name} ({f.stat().st_size/1024:.1f} KB)")
                except Exception as e:
                    print(f"      [Unlimited-OCR] ERROR copying images: {type(e).__name__}: {e}")
            else:
                print(f"      [Unlimited-OCR] Note: No images/ directory found in temp output")

        # Remove model self-critique metadata warnings from leading lines only
        # Stop filtering as soon as we hit actual document content
        lines = text.splitlines()
        filtered_lines = []
        found_content = False

        for line in lines:
            # Once we find actual content, keep everything else (even if it matches patterns)
            if found_content:
                filtered_lines.append(line)
            # Skip leading meta message lines only
            elif not (
                line.startswith('The OCR should not have output') or
                line.startswith('The output is correct') or
                line.startswith('The output must reflect') or
                line.startswith('The output punctuation') or
                line.startswith('The output') or
                line.startswith('Treat all') or
                line.startswith('Inline') or
                line.startswith('Ground Truth')
            ):
                # This is the first non-meta line - actual content starts here
                found_content = True
                filtered_lines.append(line)

        text = '\n'.join(filtered_lines)

        # Convert LaTeX superscript ordinals to plain text
        text = re.sub(r'\\\(\s*\^\{st\}\s*\\\)', 'st', text)
        text = re.sub(r'\\\(\s*\^\{nd\}\s*\\\)', 'nd', text)
        text = re.sub(r'\\\(\s*\^\{rd\}\s*\\\)', 'rd', text)
        text = re.sub(r'\\\(\s*\^\{th\}\s*\\\)', 'th', text)

        # Detect and truncate obvious runaway token generation (20+ identical tokens)
        text = self._detect_and_fix_repetitions(text)

        return text

    def _detect_and_fix_repetitions(self, text: str) -> str:
        """
        Detect semantic hallucination loops (Unlimited-OCR failure mode).
        When handwriting is too noisy, model gets stuck generating sequences.
        """
        # Check for hallucination loop signatures
        if self._is_hallucination_loop(text):
            print(f"      [Unlimited-OCR] WARNING: Detected hallucination loop, truncating")
            # Return only the first reasonable portion
            return text[:1500] if len(text) > 1500 else text

        return text

    def _is_hallucination_loop(self, text: str) -> bool:
        """
        Detect if text contains semantic hallucination loop patterns.
        These are reliable signatures of when the model gets stuck.
        """
        # 1. Excessive length (normal OCR rarely exceeds 2000 chars per image)
        if len(text) > 2000:
            # print(f"      [Unlimited-OCR] DEBUG: Rule #1 triggered - excessive length: {len(text)} chars > 2000")
            return True

        # 2. Repetitive date-like patterns (9/10, 9/11, 9/12... 10/40, 10/80...)
        date_matches = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", text)
        if len(date_matches) >= 10:
            # print(f"      [Unlimited-OCR] DEBUG: Rule #2 triggered - repetitive dates: {len(date_matches)} >= 10")
            return True

        # 3. Monotonic numeric sequences (1, 2, 3, 4, 5... = textbook hallucination)
        nums = [int(n) for n in re.findall(r"\b\d+\b", text)]
        if len(nums) > 10:
            # Check if numbers increment by 1 consecutively
            consecutive_increments = sum(
                1 for i in range(len(nums) - 1)
                if nums[i+1] - nums[i] == 1
            )
            if consecutive_increments > 10:
                # print(f"      [Unlimited-OCR] DEBUG: Rule #3 triggered - monotonic sequence: {consecutive_increments} increments > 10")
                return True

        # 4. Repeated phrases (same word appears 5+ times = stuck loop)
        words = text.split()
        if len(words) > 50:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            max_freq = max(word_freq.values()) if word_freq else 0
            unique_words = len(word_freq)
            # If any word appears too frequently, likely hallucination
            if max_freq >= 5 and unique_words < len(words) / 2:
                most_freq_word = max(word_freq, key=word_freq.get)
                # print(f"      [Unlimited-OCR] DEBUG: Rule #4 triggered - word repetition: '{most_freq_word}' appears {max_freq}x in {len(words)} words ({unique_words} unique)")
                return True

        return False

    def _extract_text(self, result) -> str:
        """
        Extract text from Unlimited-OCR model output (legacy).

        The model returns structured text (typically markdown or JSON format).
        """
        if isinstance(result, dict):
            # If result is a dict, try common keys
            return result.get('text', result.get('content', str(result)))
        elif isinstance(result, str):
            return result
        else:
            return str(result)

    def _convert_to_char_confidence(self, text: str) -> List[Dict]:
        """
        Convert text to per-character confidence.

        For local inference, all characters get uniform confidence (0.95).
        The model is deterministic, so all outputs are equally confident.
        """
        return [{"char": char, "confidence": 0.95} for char in text]

    def _save_response(self, image_path: str, response_text, error: bool = False):
        """Save model output to file for debugging"""
        try:
            p = Path(image_path)
            base_name = p.stem
            txt_filename = f"{base_name}-response-error.txt" if error else f"{base_name}-response.txt"
            summary_folder = Path(self.output_folder) / "summary"
            summary_folder.mkdir(parents=True, exist_ok=True)
            txt_path = summary_folder / txt_filename

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("===== UNLIMITED-OCR RESPONSE =====\n\n")
                if error:
                    f.write(f"ERROR: {response_text}\n")
                else:
                    f.write("[RESPONSE TEXT - RAW]\n")
                    f.write(str(response_text) + "\n\n")
                    f.write("[RESPONSE TEXT - PRETTY PRINTED]\n")
                    if isinstance(response_text, dict):
                        f.write(json.dumps(response_text, indent=2) + "\n")
                    else:
                        f.write(str(response_text) + "\n")

            print(f"      [Unlimited-OCR] Saved: {txt_filename}")
        except Exception as e:
            print(f"      [Unlimited-OCR] Warning: Failed to save response: {e}")
