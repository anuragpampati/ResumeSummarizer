from flask import Flask, request, jsonify, send_from_directory
from transformers import pipeline
import os
import PyPDF2
import docx


app = Flask(__name__, static_folder='static')# Enable cross-origin requests (if needed for external front-ends)

# 1. Initialize the summarizer (download model if not present)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyPDF2."""
    text = ""
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text() + "\n"
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX files using python-docx."""
    doc_file = docx.Document(file_path)
    full_text = []
    for para in doc_file.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


@app.route('/')
def serve_index():
    """Serve the main HTML file."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files like script.js or style.css."""
    return send_from_directory(app.static_folder, path)


@app.route('/summarize', methods=['POST'])
def summarize_resume():
    """Endpoint to handle file upload, extract text, and summarize."""
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['resume']
    file_extension = os.path.splitext(uploaded_file.filename)[1].lower()

    # Save uploaded file to a temporary location
    temp_path = os.path.join("temp_upload" + file_extension)
    uploaded_file.save(temp_path)

    # Extract text based on extension
    if file_extension == '.pdf':
        extracted_text = extract_text_from_pdf(temp_path)
    elif file_extension in ('.doc', '.docx'):
        extracted_text = extract_text_from_docx(temp_path)
    else:
        os.remove(temp_path)
        return jsonify({"error": "Unsupported file format"}), 400

    # Remove the temp file
    os.remove(temp_path)

    if not extracted_text.strip():
        return jsonify({"error": "Could not extract text from file."}), 400

    # For large text, chunk it into segments of ~1000 tokens or words
    max_chunk_size = 1000
    words = extracted_text.split()
    text_chunks = []
    chunk = []
    current_length = 0

    for word in words:
        chunk.append(word)
        current_length += 1
        if current_length >= max_chunk_size:
            text_chunks.append(" ".join(chunk))
            chunk = []
            current_length = 0

    # Add any remaining words as the last chunk
    if chunk:
        text_chunks.append(" ".join(chunk))

    summary_result = []
    for chunk_text in text_chunks:
        # Summarize each chunk
        summary = summarizer(chunk_text, max_length=130, min_length=30, do_sample=False)
        summary_result.append(summary[0]['summary_text'])

    # Join partial summaries
    final_summary = " ".join(summary_result)

    return jsonify({"summary": final_summary})


if __name__ == '__main__':
    # On Render or Heroku, typically you'd use:
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)

    # For local dev, simply:
    app.run(debug=True, host="0.0.0.0", port=5000)
