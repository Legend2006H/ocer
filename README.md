# PDF Text Lens

A small, local Flask app for extracting text from PDF files.

- Extracts native/selectable text directly from digital PDFs.
- Uses Tesseract OCR for pages that have little or no embedded text (scans, images, handwriting).
- Shows the source used per page and lets you download a `.txt` file.

## Run it

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

For scanned and handwritten PDFs, also install the Windows build of Tesseract and ensure `tesseract` is on your `PATH`:
https://github.com/UB-Mannheim/tesseract/wiki

Tesseract recognizes clear block handwriting only imperfectly. For difficult cursive handwriting, replace the OCR stage with a handwriting-specific cloud model (for example Azure AI Vision Read, Google Cloud Vision, or a specialized transformer) if the documents may be sent to an external service.
