from flask import Flask, request, jsonify
from jinja2 import Template
import ollama
import json
import csv
from datetime import datetime

app = Flask(__name__)

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

# Route: Generate Social Post
@app.route('/generate_post', methods=['POST'])
def generate_post():
    data = request.json
    prompt = render_prompt(
        '../prompts/social_post_template.txt',
        {
            'dish_name': data['dish_name'],
            'theme': data['theme'],
            'tone': data['tone']
        }
    )
    response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt}])
    result = response['message']['content']

    save_history({
        'type': 'social_post',
        'input': data,
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
    response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt}])
    result = response['message']['content']

    save_history({
        'type': 'review_reply',
        'input': data,
        'output': result
    })

    return jsonify({'reply': result})

# Route: View History
@app.route('/history', methods=['GET'])
def get_history():
    try:
        with open('history.json', 'r') as f:
            history = json.load(f)
        return jsonify(history)
    except FileNotFoundError:
        return jsonify([])

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