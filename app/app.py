import sys
import os
import shutil

print("=== APP STARTING ===", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"Working dir: {os.getcwd()}", flush=True)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from flask import Flask, request, jsonify, render_template
    from werkzeug.utils import secure_filename
    print("=== Flask imported ===", flush=True)
except Exception as e:
    print(f"=== Flask import error: {e} ===", flush=True)
    sys.exit(1)

try:
    from src.document_processor import load_and_split_pdf
    from src.vector_store import create_parent_retriever
    from src.qa_chain import build_qa_chain, ask_question
    from src.logger import logging
    print("=== src imports OK ===", flush=True)
except Exception as e:
    print(f"=== src import error: {e} ===", flush=True)
    sys.exit(1)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf'}
qa_chain = {}

os.makedirs('data/uploads', exist_ok=True)
os.makedirs('vectorstore', exist_ok=True)

print("=== Flask app created ===", flush=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global qa_chain
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
        chunks = load_and_split_pdf(filepath)
        retriever = create_parent_retriever(chunks, filename)
        qa = build_qa_chain(retriever)
        qa_chain[filename] = qa
        return jsonify({
            'message': 'Document processed successfully',
            'chunks': len(chunks),
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
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
    global qa_chain
    qa_chain = {}
    return jsonify({'message': 'Session reset'})

@app.route('/remove', methods=['POST'])
def remove():
    global qa_chain
    try:
        data = request.get_json()
        filename = data.get('filename')
        if filename in qa_chain:
            del qa_chain[filename]
        persist_dir = os.path.join('vectorstore', filename.replace('.pdf', ''))
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'message': f'{filename} removed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)