import sys
import os
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from src.document_processor import load_and_split_pdf
from src.vector_store import create_parent_retriever
from src.qa_chain import build_qa_chain, ask_question
from src.logger import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

ALLOWED_EXTENSIONS = {'pdf'}
qa_chain = {}
vectorstore = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global qa_chain, vectorstore
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files allowed'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        logging.info(f'Processing: {filename}')
        chunks     = load_and_split_pdf(filepath)
        retriever = create_parent_retriever(chunks, filename)
        qa = build_qa_chain(retriever)
        qa_chain[filename] = qa

        return jsonify({
            'message': f'Document processed successfully',
            'chunks':  len(chunks),
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    global qa_chains
    try:
        data     = request.get_json()
        question = data.get('question', '').strip()
        filename = data.get('filename', None)

        if not question:
            return jsonify({'error': 'No question provided'}), 400
        if not filename or filename not in qa_chain:
            return jsonify({'error': 'No document selected.'}), 400

        result = ask_question(qa_chain[filename], question)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    global qa_chain, vectorstores
    qa_chain = {}
    vectorstores = {}
    return jsonify({'message': 'Session reset'})

if __name__ == '__main__':
    os.makedirs('data/uploads', exist_ok=True)
    if os.path.exists('vectorstore'):
        shutil.rmtree('vectorstore')
    os.makedirs('vectorstore', exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)