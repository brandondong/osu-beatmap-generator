from tkinter import *
from tkinter import ttk

from beatmap import beatmap_generator

BAD_DIFFICULTY_CHARACTERS = re.compile(r"[^\d,\. ]")

def create_input_row(row, text, mainframe):
    ttk.Label(mainframe, text=text, wraplength=100).grid(column=0, row=row, sticky=W)
    string_var = StringVar()
    entry = ttk.Entry(mainframe, textvariable=string_var)
    entry.grid(column=1, row=row, sticky=(W, E))
    return string_var

def restrict_difficulties_characters(*args):
    value = difficulties.get()
    value = BAD_DIFFICULTY_CHARACTERS.sub("", value)
    difficulties.set(value)

def generate(*args):
    beatmap_generator.create_beatmapset("ffmpeg/test5.mp3", [7], "ffmpeg/", title.get(), artist.get())

root = Tk()
root.title("osu beatmap generator")

mainframe = ttk.Frame(root, padding="12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(1, weight=1)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

ttk.Label(mainframe, text="Audio file:").grid(column=0, row=0, sticky=W)

f1 = ttk.Frame(mainframe)
ttk.Button(f1, text="Browse").grid(column=0, row=0, sticky=W)

filename = StringVar()
filename_entry = ttk.Entry(f1, width=20, textvariable=filename)
filename_entry.grid(column=1, row=0, sticky=(W, E))

f1.grid(column=1, row=0, sticky=(W, E))
f1.columnconfigure(1, weight=1)

title = create_input_row(1, "Title:", mainframe)
artist = create_input_row(2, "Artist:", mainframe)
difficulties = create_input_row(3, "Target difficulties: (e.g. 3, 5.4, 7)", mainframe)
difficulties.trace('w', restrict_difficulties_characters)

ttk.Button(mainframe, text="Generate", command=generate).grid(column=1, row=4, sticky=E)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)
root.mainloop()