from flask import Flask, request, jsonify
from jinja2 import Template
from werkzeug.utils import secure_filename
import ollama
import json
import csv
import os
from datetime import datetime

app = Flask(__name__)

# Setup image upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Utility: Load and render prompt templates
def render_prompt(template_path, variables):
    with open(template_path, 'r') as file:
        template = Template(file.read())
    return template.render(**variables)

# Utility: Save history to JSON file
def save_history(entry, filename='history.json'):
    try:
        with open(filename, 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    entry['timestamp'] = datetime.now().isoformat()
    history.append(entry)

    with open(filename, 'w') as f:
        json.dump(history, f, indent=2)

# Route: Generate Social Post (with optional image)
@app.route('/generate_post', methods=['POST'])
def generate_post():
    dish = request.form['dish_name']
    theme = request.form['theme']
    tone = request.form['tone']
    image_file = request.files.get('image')

    image_path = None
    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

    prompt = render_prompt(
        '../prompts/social_post_template.txt',
        {'dish_name': dish, 'theme': theme, 'tone': tone}
    )
    response = ollama.chat(model='phi', messages=[{'role': 'user', 'content': prompt}])
    result = response['message']['content']

    save_history({
        'type': 'social_post',
        'input': {'dish_name': dish, 'theme': theme, 'tone': tone, 'image': image_path},
        'output': result
    })

    return jsonify({'caption': result})

# Route: Respond to Review
@app.route('/respond_review', methods=['POST'])
def respond_review():
    data = request.json
    prompt = render_prompt(
        '../prompts/review_reply_template.txt',
        {
            'review_text': data['review_text'],
            'sentiment': data['sentiment'],
            'tone': data['tone']
        }
    )
    response = ollama.chat(model='phi', messages=[{'role': 'user', 'content': prompt}])
    result = response['message']['content']

    save_history({
        'type': 'review_reply',
        'input': data,
        'output': result
    })

    return jsonify({'reply': result})

# Route: View Full History
@app.route('/history', methods=['GET'])
def get_history():
    try:
        with open('history.json', 'r') as f:
            history = json.load(f)
        return jsonify(history)
    except FileNotFoundError:
        return jsonify([])

# Route: Filtered History
@app.route('/history/filter', methods=['GET'])
def filter_history():
    entry_type = request.args.get('type')
    try:
        with open('history.json', 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        return jsonify([])

    if entry_type:
        filtered = [h for h in history if h['type'] == entry_type]
        return jsonify(filtered)
    return jsonify(history)

# Route: Export History to CSV
@app.route('/export_csv', methods=['GET'])
def export_csv():
    try:
        with open('history.json', 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        return "No history found", 404

    with open('history.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Type', 'Timestamp', 'Input', 'Output'])
        for entry in history:
            writer.writerow([
                entry['type'],
                entry['timestamp'],
                json.dumps(entry['input'], ensure_ascii=False),
                entry['output']
            ])
    return "CSV exported successfully", 200

if __name__ == '__main__':
    app.run(debug=True)