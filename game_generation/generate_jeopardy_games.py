import os
import re
import json
import random

def get_unique_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1

    # Check if the filename exists
    while os.path.exists(filename):
        match = re.search(r'_(\d+)', base)
        if match:
            counter = int(match.group(1)) + 1
            base = re.sub(r'_(\d+)', '', base)
        filename = f"{base}_{counter}{ext}"
        counter += 1  # Increment counter for the next check
    return filename

def contains_image(question_data):
    for question in question_data:
        question_text = question['question']
        if '<img' in question_text or '<a href=' in question_text:
            return True
    return False

def select_questions(input_file, output_file, num_categories=6, questions_per_category=5):
    with open(input_file, 'r') as f:
        data = json.load(f)

    selected_categories = []
    while len(selected_categories) < num_categories:
        show_number = random.choice(list(data.keys()))
        categories = data[show_number]

        jeopardy_categories = [category for category, questions in categories.items() if any(q['round'] == 'Jeopardy!' for q in questions)]
        
        if not jeopardy_categories:
            continue

        category = random.choice(jeopardy_categories)
        category_questions = categories[category]

        # Filter questions with the specified values
        filtered_questions = [q for q in category_questions if int(q['value'].replace('$', '').replace(',', '')) in [200, 400, 600, 800, 1000]]

        if len(filtered_questions) >= questions_per_category:
            # Check if any selected question contains image tags or links
            if not contains_image(filtered_questions[:questions_per_category]):
                selected_categories.append({category: filtered_questions[:questions_per_category]})

    with open(output_file, 'w') as out_file:
        json.dump(selected_categories, out_file, indent=4)

def generate_formatted_questions(input_file):
    formatted_questions = {}
    
    with open(input_file, 'r') as f:
        data = json.load(f)

    for category_data in data:
        category_name = list(category_data.keys())[0]
        questions = category_data[category_name]
        
        formatted_questions[category_name] = []
        
        for q in questions:
            question_text = q['question']
            # Replace <br /> with newline character
            question_text = question_text.replace('<br />', '\n')
            # Replace escaped quotation marks with actual quotation marks
            question_text = question_text.replace('\\"', '"')
            answer = q['answer']
            value = int(q['value'].replace('$', '').replace(',', ''))
            
            formatted_questions[category_name].append({
                question_text: {
                    "answer": answer,
                    "points": value
                }
            })

    return formatted_questions
