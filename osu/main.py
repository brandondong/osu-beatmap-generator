import os
from threading import Thread
from tkinter import *
from tkinter import filedialog, ttk

from beatmap import beatmap_generator

BAD_DIFFICULTY_CHARACTERS = re.compile(r"[^\d,\. ]")

def create_input_row(row, text, mainframe, on_write):
    ttk.Label(mainframe, text=text, wraplength=100).grid(column=0, row=row, sticky=W)
    string_var = StringVar()
    entry = ttk.Entry(mainframe, textvariable=string_var)
    entry.grid(column=1, row=row, sticky=(W, E))
    string_var.trace('w', on_write)
    return string_var

def restrict_difficulties_characters(*args):
    value = difficulties.get()
    value = BAD_DIFFICULTY_CHARACTERS.sub("", value)
    difficulties.set(value)
    update_button_enablement()

def update_button_enablement(*args):
    if not generating and len(filename.get()) > 0 and len(title.get()) > 0 and len(artist.get()) > 0 and len(difficulties.get()) > 0:
        generate_button.config(state=NORMAL)
    else:
        generate_button.config(state=DISABLED)

def browse(*args):
    audio_filename = filedialog.askopenfilename(filetypes=[("MP3 files","*.mp3")])
    if not audio_filename:
        return
    filename.set(audio_filename)

class GenerateBackgroundThread(Thread):
    def __init__(self, src, dst, title, artist, callback):
        Thread.__init__(self)
        self.src = src
        self.dst = dst
        self.title = title
        self.artist = artist
        self.callback = callback
    
    def run(self):
        beatmap_generator.create_beatmapset(self.src, [7], self.dst, self.title, self.artist)
        self.callback()

def finish_generating():
    global generating
    generating = False
    update_button_enablement()

def generate(*args):
    base_filename = os.path.splitext(os.path.basename(filename.get()))[0]
    save_to_name = filedialog.asksaveasfilename(initialfile=f"{base_filename}.osz", filetypes=[("Executable beatmap files","*.osz")])
    if not save_to_name:
        return
    global generating
    generating = True
    generate_button.config(state=DISABLED)
    GenerateBackgroundThread(filename.get(), save_to_name, title.get(), artist.get(), finish_generating).start()

root = Tk()
root.title("osu beatmap generator")

mainframe = ttk.Frame(root, padding="12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(1, weight=1)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

ttk.Label(mainframe, text="Audio file:").grid(column=0, row=0, sticky=W)

f1 = ttk.Frame(mainframe)
ttk.Button(f1, text="Browse", command=browse).grid(column=0, row=0, sticky=W)

filename = StringVar()
filename_entry = ttk.Entry(f1, width=20, textvariable=filename)
filename_entry.grid(column=1, row=0, sticky=(W, E))
filename.trace('w', update_button_enablement)

f1.grid(column=1, row=0, sticky=(W, E))
f1.columnconfigure(1, weight=1)

title = create_input_row(1, "Title:", mainframe, update_button_enablement)
artist = create_input_row(2, "Artist:", mainframe, update_button_enablement)
difficulties = create_input_row(3, "Target difficulties: (e.g. 3, 5.4, 7)", mainframe, restrict_difficulties_characters)

generate_button = ttk.Button(mainframe, text="Generate", command=generate)
generate_button.grid(column=1, row=4, sticky=E)
generate_button.config(state=DISABLED)
generating = False

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)
root.mainloop()