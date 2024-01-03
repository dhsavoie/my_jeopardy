import json

def reorder_questions(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    categorized_questions = {}
    for item in data:
        show_number = item['show_number']
        category = item['category']
        question = item['question']
        answer = item['answer']
        value = item['value']
        game_round = item['round']

        if show_number not in categorized_questions:
            categorized_questions[show_number] = {}

        if category not in categorized_questions[show_number]:
            categorized_questions[show_number][category] = []

        categorized_questions[show_number][category].append({
            "round": game_round,
            "question": question,
            "answer": answer,
            "value": value
        })

    with open(output_file, 'w') as out_file:
        json.dump(categorized_questions, out_file, indent=4)

# Replace 'input_file.json' and 'output_file.json' with your file names
reorder_questions('JEOPARDY_QUESTIONS1.json', 'show_order_wround.json')
