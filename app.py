from flask import Flask, request, render_template, jsonify
import os
import google.generativeai as genai

app = Flask(__name__)

# Configure your Gemini API key
genai.configure(api_key=os.environ["GEMINI_KEY_PERSONAL"])
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    input_text = request.json.get('text', '')
    response = model.generate_content(
    f'''Generate five multiple choice questions with their answers based on the following paragraph. Please format them in the following way:

Heading (e.g., "Multiple Choice Questions")
(empty line)

Question Number: question. Options must start immediately in the next line
Option a
Option b
Option c
Option d
(empty line)
Answer: answer with the entire option
(empty line)

Here is the paragraph:
'{input_text}'
'''
    )
    
    parts = response.text.split("\n\n")
    questions = []
    question = None
    options = []
    correct_answer = ""
    
    for part in parts:
        lines = [line.strip() for line in part.split("\n") if line.strip()]

        if len(lines) > 1 and lines[0].startswith("**"):
            question = lines[0].replace("**", "").strip()
            options = [line.strip() for line in lines[1:] if line.startswith(('a', 'b', 'c', 'd'))]

        elif len(lines) == 1 and lines[0].startswith("**Answer:"):
            correct_answer = lines[0].replace("**Answer:", "").strip()
            # Remove the "**" prefix, if any
            correct_answer = correct_answer.lstrip("**").strip()
            if question and options:
                questions.append({
                    "question": question,
                    "options": options,
                    "answer": correct_answer  # Store answer without "**"
                })
            question, options, correct_answer = None, [], ""
    
    return jsonify(questions)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    user_answers = data.get("userAnswers", {})
    correct_answers = data.get("correctAnswers", {})

    score = 0
    total = len(correct_answers)
    results = []

    for q_id, correct in correct_answers.items():
        user_ans = user_answers.get(q_id, "").strip().lower()
        correct = correct.strip().lower()

        # Normalize the format by removing any common suffix/prefix differences
        user_ans = user_ans.replace("**", "").strip()
        correct = correct.replace("**", "").strip()

        # Correct comparison logic
        is_correct = (user_ans == correct)
        if is_correct:
            score += 1
        
        results.append({
            "question_id": q_id,
            "user_answer": user_ans,
            "correct_answer": correct,
            "is_correct": is_correct
        })

    return jsonify({"score": score, "total": total, "results": results})

if __name__ == '__main__':
    app.run(debug=True)
