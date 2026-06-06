import tkinter as tk
import random

# Create window
root = tk.Tk()
root.title("Housy Number Caller")
root.geometry("400x500")
root.config(bg="white")

# Global variables
numbers = list(range(1, 91))
called_numbers = []

# Functions
def call_number():
    global numbers, called_numbers

    if len(numbers) == 0:
        display_label.config(text="Game Over!", fg="red")
        return

    num = random.choice(numbers)
    numbers.remove(num)
    called_numbers.append(num)

    display_label.config(text=f"The number is: {num}", fg="blue", font=("Arial", 20, "bold"))

    history_label.config(text="Called: " + ", ".join(map(str, called_numbers)))

def reset_game():
    global numbers, called_numbers
    numbers = list(range(1, 91))
    called_numbers = []
    display_label.config(text="Ready!", fg="black")
    history_label.config(text="Called: ")

# UI Elements
display_label = tk.Label(root, text="Ready!", font=("Arial", 40, "bold"), bg="white", fg="black")
display_label.pack(pady=30)

call_btn = tk.Button(root, text="Call Next Number", font=("Arial", 18), bg="green", fg="white", command=call_number)
call_btn.pack(pady=20)

reset_btn = tk.Button(root, text="Reset Game", font=("Arial", 14), bg="red", fg="white", command=reset_game)
reset_btn.pack(pady=10)

history_label = tk.Label(root, text="Called: ", font=("Arial", 12), bg="white", fg="black", wraplength=350, justify="left")
history_label.pack(pady=20)

root.mainloop()






















































