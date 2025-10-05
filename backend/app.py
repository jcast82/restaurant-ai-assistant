from flask import Flask, request, jsonify
import ollama
from jinja2 import Template
import json
from datetime import datetime

app = Flask(__name__)

# Utility to load and render prompt templates
def render_prompt(template_path, variables):
    with open(template_path, 'r') as file:
        template = Template(file.read())
    return template.render(**variables)

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
    return jsonify({'caption': response['message']['content']})

    save_history({
    'type': 'social_post',
    'input': data,
    'output': response['message']['content']
    })

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
    return jsonify({'reply': response['message']['content']})

if __name__ == '__main__':
    app.run(debug=True)