import os
import json
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import asyncio
import argparse
import warnings
import threading
import tkinter as tk
from ble.ble_utils import *
from game_generation.generate_jeopardy_games import get_unique_filename, select_questions, generate_formatted_questions

#+              UUIDS              +#
BUZZ_UUID = 0x0003
SCORE_UUID = 0x0004
SERVICE_UUID = 0x1111


#+              GLOBALS              +#
BUZZED = ['']


#+             SOUND              +#
# Initialize pygame mixer
pygame.mixer.init()
# Load the sound file
sound_file = "sounds/jeopardy-theme-song.mp3"  # Replace with your sound file path
pygame.mixer.music.load(sound_file)

# sound functions
def play_sound():
    pygame.mixer.music.play()
def stop_sound():
    pygame.mixer.music.stop()

#+              MISC FUNCTIONS              +#
def whitespace(b=True, a=True):
    ws = ""
    if b:
        ws += "\n"
    ws += "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    if a:
        ws += "\n"
    print(ws)


#+              QUESTION GENERATION              +#
# define the jeopardy file to use
jeopardy_file = "jeopardy_games/jeopardy_game_3.json"

parser = argparse.ArgumentParser(description='Generate a Jeopardy board with buttons displaying categories and questions with point values')
parser.add_argument('-n', '--new', action='store_true', help='Set this flag to generate a new jeopardy game file')
parser.add_argument('-f', '--file', type=int, help="The positive nonzero integer number of the file you'd like to play with")

args = parser.parse_args()

if args.new:
    output_file = "jeopardy_games/jeopardy_game_1.json"
    unique_output_file = get_unique_filename(output_file)
    select_questions('other_jsons/show_order_wround.json', unique_output_file)
    jeopardy_file = unique_output_file
if args.file:
    if args.file <= 0:
        print("Please enter a positive nonzero integer")
        exit()
    else:
        jeopardy_file = f"jeopardy_games/jeopardy_game_{args.file}.json"

# Generate the jeopardy questions to be used
categories = generate_formatted_questions(jeopardy_file)


#+          ASYNC AND ASSOCIATED FUNCTIONS        +#
async def buzzer_listener(clients, uuid, queue, labels, buttons):
    """Create a buzzer listener with conditional logic to open/close stream"""

    # open listener
    await start_multiple_indication_listener(clients, uuid, queue, False, handle_indication_single)
    
    # close listener after receiving indication
    for client in clients:
        if clients[client]['buzzed'] == False:
            await clients[client]['client'].stop_notify(uuid)

    # get the player number who buzzed in
    buzzed_in = await queue.get()  # Get the value from the queue
    BUZZED[0] = buzzed_in
    buzz_num = int(buzzed_in[-1]) - 1

    # stop the jeopardy music
    stop_sound()
    
    # change the color of the buzzer button and disable the other buttons
    labels[buzz_num].config(bg="red", fg="white", bd=2, relief="solid")
    buttons[0].config(state="normal",bg='blue', fg='white', bd=1, relief="raised")
    buttons[1].config(state="disabled", bg="#FFD700", fg="blue", bd=2, relief="solid") 
    buttons[2].config(state="normal", bg='blue', fg='white', bd=1, relief="raised")
    
def buzzer_listener_thread(clients, uuid, queue, labels, buttons):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(buzzer_listener(clients, uuid, queue, labels, buttons))

def start_buzzer_listener(clients, uuid, queue, labels, buttons):
    """Start a buzzer listener in a new thread"""
    thread = threading.Thread(target=buzzer_listener_thread, args=(clients, uuid, queue, labels, buttons))
    thread.start()
    return thread


#+                      POPUPS                    +#

def display_correct_answer(answer):
    """Display the correct answer in a popup window"""
    top_correct = tk.Toplevel() # Create a popup window
    top_correct.title("Correct Answer") # Set the title
    top_correct.attributes('-fullscreen', True) # Fullscreen
    
    # Display the correct answer
    label_correct = tk.Label(top_correct, text=f"Correct answer: {answer}", font=("Impact", 54), padx=20, pady=20, wraplength=600, fg='white', bg='blue')
    label_correct.pack(fill='both', expand=True)

    # Create an OK button to close the popup window
    ok_button = tk.Button(top_correct, text="OK", command=top_correct.destroy, font=("Impact", 12))
    ok_button.pack(pady=5)

def show_question(question_dict, button, clients, num_players=1):
    """Show the current question in a popup window"""

    # Get the question text, point value, and answer from the question dictionary
    question_text = list(question_dict.keys())[0]
    question_info = question_dict[question_text]
    point_value = question_info["points"]
    answer = question_info["answer"]

    # print the answer to the terminal for the host
    print(f"The answer to '{question_text}' is: {answer}\n")

    # play jeopardy music
    play_sound()

    def on_close():
        # Stop the sound when the popup is closed
        stop_sound()
        top.destroy()

    top = tk.Toplevel() # Create a popup window
    top.title(f"Question ({point_value} points)") # Set the title
    top.configure(bg='blue')  # Blue background
    top.attributes('-fullscreen', True)  # Fullscreen
    top.protocol("WM_DELETE_WINDOW", on_close) # Stop the sound when the popup is closed

    label = tk.Label(top, text=question_text, font=("Impact", 48), padx=20, pady=20, wraplength=600, fg='white', bg='blue')  # White text, Blue background
    label.pack(fill='both', expand=True)

    #TODO: try to get the formatting so that players are on one row and buttons are on the next row
    
    # Create player indicators
    player_labels = []
    for i in range(num_players):
        label = tk.Button(top, text=f"Player {i+1}", font=("Impact", 12), bg='blue', fg='white', bd=2, relief="solid")
        player_labels.append(label)
        label.pack(side=tk.LEFT, padx=5, pady=5, fill='x', expand=True)

    # Create buttons
    correct_button = tk.Button(top, text="Correct", command=lambda: process_correct_answer(point_value, top, answer), font=("Impact", 12), bg='blue', fg='white')
    correct_button.pack(side=tk.LEFT, padx=5, pady=5, fill='x', expand=True)

    give_up_button = tk.Button(top, text="Give Up", command=lambda: process_give_up(top, answer), font=("Impact", 12), bg='blue', fg='white')
    give_up_button.pack(side=tk.LEFT, padx=5, pady=5, fill='x', expand=True)

    incorrect_button = tk.Button(top, text="Incorrect", command=lambda: process_incorrect_answer(point_value, buttons, clients, queue, player_labels), font=("Impact", 12), bg='blue', fg='white')
    incorrect_button.pack(side=tk.LEFT, padx=5, pady=5, fill='x', expand=True)

    # disable the 'correct' and 'incorrect' buttons
    correct_button.config(state="disabled", bg="#FFD700", fg="blue", bd=2, relief="solid") 
    incorrect_button.config(state="disabled", bg="#FFD700", fg="blue", bd=2, relief="solid")

    buttons = [correct_button, give_up_button, incorrect_button]

    queue = asyncio.Queue() # Create a queue to store the value of the client who buzzed in

    # Start a buzzer listener in a new thread
    buzzed_thread = start_buzzer_listener(clients, uuid16_to_uuid(BUZZ_UUID), queue, player_labels, buttons)
    
    # disable the question's button after it has been used
    button.config(state="disabled", bg="#FFD700", fg="blue", bd=2, relief="solid") 

    # play the jeopardy music
    play_sound()

#TODO: add a popup for the end of the game that shows the winner
def display_winner():
    pass


#+                      BUTTON PRESS HANDLING                    +#
def process_correct_answer(points, top, correct_answer):
    """handle when the 'correct' button is pressed"""
    player_num = int(BUZZED[0][-1])-1 # get the player number for who buzzed in
    score_vars[player_num].set(score_vars[player_num].get() + points) # add the points to the player's score
    display_correct_answer(correct_answer) # display the correct answer
    stop_sound() # stop sound
    top.destroy() # close the popup window
    #TODO: send a message to the peripheral to indicate that the answer was correct

def process_incorrect_answer(points, buttons, clients, queue, player_labels):
    """handle when the 'incorrect' button is pressed"""
    player_num = int(BUZZED[0][-1])-1 # get the player number for who buzzed in
    score_vars[player_num].set(score_vars[player_num].get() - points) # subtract the points from the player's score
    buttons[0].config(state="disabled", bg="#FFD700", fg="blue", bd=2, relief="solid") # re disable the 'correct' button
    buttons[1].config(state="normal", bg='blue', fg='white', bd=1, relief="raised") # re enable the 'give up' button
    buttons[2].config(state="disabled", bg="#FFD700", fg="blue", bd=2, relief="solid") # re disable the 'incorrect' button
    for label in player_labels: # reset the player labels
        label.config(bg='blue', fg='white', bd=2, relief="solid")

    #! may have to reset BUZZED[0]- not sure- will need to test with multiple players
    #TODO: send a message to the peripheral to indicate that the answer was incorrect
    # restart the buzzer listener
    play_sound()
    buzzed_thread = start_buzzer_listener(clients, uuid16_to_uuid(BUZZ_UUID), queue, player_labels, buttons)

def process_give_up(top, correct_answer):
    """handle when the 'give up' button is pressed"""
    display_correct_answer(correct_answer)
    stop_sound() # stop sound
    top.destroy() # close the popup window


#+                     MAIN GUI GENERATION                    +#
def generate_jeopardy_board(categories, clients, num_players=1):
    root = tk.Tk()
    root.title("Jeopardy Board")
    root.configure(bg="blue")  # Set background color to blue

    for idx, category in enumerate(categories.keys()):
        label = tk.Label(root, text=category.upper(), font=("Impact", 16), bg="blue", fg="white", bd=2, relief="solid", wraplength=200)
        label.grid(row=0, column=idx, padx=20, pady=10, sticky="nsew")  # Make category titles the same width as buttons

        for i, question_dict in enumerate(categories[category], start=1):
            question_text = list(question_dict.keys())[0]
            btn = tk.Button(root, text=f"${question_dict[question_text]['points']}", width=10, height=3, font=("Impact", 20))
            btn.grid(row=i, column=idx, padx=10, pady=5, sticky="nsew")
            btn.config(command=lambda q=question_dict, b=btn: show_question(q, b, clients, num_players), bg="blue", fg="#FFD700", bd=2, relief="solid")

            root.grid_columnconfigure(idx, uniform="col")  # Set uniform size for buttons

    global score_vars
    score_vars = []

    # Create player score labels
    for i in range(num_players):
        player_label = tk.Label(root, text=f"Player {i+1}: ", font=("Impact", 14), bg="blue", fg="white")
        player_label.grid(row=max(len(q) for q in categories.values()) + 1, column=i, pady=5, sticky="w")

        score_var = tk.IntVar()
        score_var.set(0)
        score_display = tk.Label(root, textvariable=score_var, font=("Impact", 14), bg="blue", fg="white")
        score_display.grid(row=max(len(q) for q in categories.values()) + 1, column=i, pady=5, sticky="")
        score_vars.append(score_var)


    # Configure grid weights to make cells expandable
    for i in range(len(categories) + 2):
        root.grid_columnconfigure(i, weight=1)
    for i in range(max(len(q) for q in categories.values()) + 1):
        root.grid_rowconfigure(i, weight=1)

    root.mainloop()

    # Disable all buttons after the main loop exits
    for row in range(max(len(q) for q in categories.values())):
        for col in range(len(categories)):
            btn = root.grid_slaves(row=row + 1, column=col)[0]
            btn.config(state="disabled", bg="#9E9E9E", fg="black")

#+                                          MAIN                                          +#
# Generate a Jeopardy board with buttons displaying categories and questions with point values
async def main():
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    mydevice_name = "Player"

    whitespace(False)
    print("--------------------WELCOME TO JEOPARDY--------------------")
    whitespace()

    print("Scanning for players...")
    # Scan for multiple devices with name mydevice_name
    clients = await scan_for_multiple_devices(mydevice_name, 1)

    # the gui (as is) can support up to 6 players
    num_players = len(clients)
    print("Number of players: ", num_players)
    if num_players == 0:
        print("No players found")
        return

    # Connect to all devices
    await connect_multiple(clients)

    try:
        whitespace()
        print("LET THE GAME BEGIN!")
        whitespace()
        generate_jeopardy_board(categories, clients, num_players)
    except tk.TclError:
        print("Jeopardy board closed")

    # Close all connections
    await disconnect_multiple(clients)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
