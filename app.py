from __future__ import annotations

import io
import shutil
from pathlib import Path
import pymupdf
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB


def get_tesseract_command() -> str | None:
    """Find Tesseract, including its usual Windows installation path."""
    command = shutil.which("tesseract")
    if command:
        return command

    windows_default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if windows_default.is_file():
        return str(windows_default)
    return None


def get_dependencies():
    """Report the optional components used for scanned/handwritten pages."""
    try:
        import pymupdf  # noqa: F401
        pdf_engine = True
    except ImportError:
        pdf_engine = False
    try:
        import pytesseract  # noqa: F401
        ocr_library = True
    except ImportError:
        ocr_library = False

    tesseract_command = get_tesseract_command()
    return {
        "pdf_engine": pdf_engine,
        "ocr_library": ocr_library,
        "tesseract": bool(tesseract_command),
        "ocr_ready": pdf_engine and ocr_library and bool(tesseract_command),
    }


def clean_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def extract_pdf(file_bytes: bytes, use_ocr: bool, language: str) -> tuple[str, list[dict], list[str]]:
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is not installed. Run: pip install -r requirements.txt") from exc

    dependencies = get_dependencies()
    document = pymupdf.open(stream=file_bytes, filetype="pdf")
    pages: list[dict] = []
    warnings: list[str] = []
    full_text: list[str] = []

    for index, page in enumerate(document, start=1):
        native_text = clean_text(page.get_text("text"))
        source = "embedded text"
        final_text = native_text

        # A sparse selectable layer may be only a page number, so OCR it too.
        should_ocr = use_ocr and dependencies["ocr_ready"] and len(native_text) < 40
        if should_ocr:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = get_tesseract_command() or "tesseract"
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5), alpha=False)
            from PIL import Image

            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            ocr_text = clean_text(pytesseract.image_to_string(image, lang=language, config="--psm 6"))
            if ocr_text:
                final_text = ocr_text
                source = "OCR"
            else:
                source = "OCR attempted - no text detected"
        elif use_ocr and len(native_text) < 40 and not dependencies["ocr_ready"]:
            warnings.append("OCR was requested, but its local dependencies are not installed. Embedded text was still extracted.")
        elif len(native_text) < 40 and not dependencies["ocr_ready"]:
            source = "Little or no embedded text - OCR unavailable"
            warnings.append("This page has little or no selectable text. Install Tesseract OCR to extract text from scanned or handwritten pages.")

        pages.append({"page": index, "source": source, "characters": len(final_text), "text": final_text})
        full_text.append(f"--- Page {index} ({source}) ---\n{final_text or '[No text detected]'}")

    document.close()
    return "\n\n".join(full_text), pages, list(dict.fromkeys(warnings))


@app.get("/")
def index():
    return render_template("index.html", dependencies=get_dependencies())


@app.post("/extract")
def extract():
    upload = request.files.get("pdf")
    if not upload or not upload.filename:
        return jsonify(error="Choose a PDF first."), 400
    if not upload.filename.lower().endswith(".pdf"):
        return jsonify(error="Only PDF files are supported."), 400

    language = request.form.get("language", "eng").strip() or "eng"
    try:
        text, pages, warnings = extract_pdf(upload.read(), request.form.get("ocr") == "true", language)
        return jsonify(text=text, pages=pages, warnings=warnings, dependencies=get_dependencies())
    except Exception as exc:
        # PDFs with a misleading extension should not expose an internal traceback.
        return jsonify(error=f"Could not read this PDF: {exc}"), 400


@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="The PDF is larger than 50 MB."), 413


if __name__ == "__main__":
    app.run(debug=True, port=5000)
