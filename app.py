from flask import Flask, request, jsonify
from transformers import pipeline
import os
import PyPDF2
import docx
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 1. Load summarization pipeline from Hugging Face
#    The first time you run this, it will download the model. This is free, open-source.
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

@app.route('/summarize', methods=['POST'])
def summarize_resume():
    """
    Endpoint to handle file upload, extract text, and summarize it.
    """
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files['resume']
    file_extension = os.path.splitext(uploaded_file.filename)[1].lower()

    # Save the uploaded file to a temporary location
    temp_path = os.path.join("temp_upload" + file_extension)
    uploaded_file.save(temp_path)

    # Extract text based on extension
    if file_extension in ['.pdf']:
        extracted_text = extract_text_from_pdf(temp_path)
    elif file_extension in ['.doc', '.docx']:
        extracted_text = extract_text_from_docx(temp_path)
    else:
        os.remove(temp_path)
        return jsonify({"error": "Unsupported file format"}), 400

    # Remove temporary file
    os.remove(temp_path)

    # If the resume is too short or empty, handle that
    if not extracted_text.strip():
        return jsonify({"error": "Could not extract text from file."}), 400

    # 2. Summarize text
    #    You may want to limit the text length or chunk it if it’s very long.
    #    The BART model handles ~1024 tokens. We'll do a simple approach here:
    #    Summarize in chunks if it's too big. For large resumes, consider chunking.
    max_chunk_size = 1000
    text_chunks = []
    words = extracted_text.split()
    
    chunk = []
    current_length = 0
    for word in words:
        chunk.append(word)
        current_length += 1
        if current_length >= max_chunk_size:
            text_chunks.append(" ".join(chunk))
            chunk = []
            current_length = 0
    # Add the last chunk
    if chunk:
        text_chunks.append(" ".join(chunk))

    summary_result = []
    for chunk_text in text_chunks:
        summary = summarizer(chunk_text, max_length=130, min_length=30, do_sample=False)
        summary_result.append(summary[0]['summary_text'])

    # Join all partial summaries
    final_summary = " ".join(summary_result)

    return jsonify({"summary": final_summary})

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
