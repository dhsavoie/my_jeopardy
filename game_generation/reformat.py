import json

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

# Replace 'input_file.json' with your file name
formatted_categories = generate_formatted_questions('jeopardy_game.json')

# Print the formatted categories (for verification)
print(formatted_categories)
