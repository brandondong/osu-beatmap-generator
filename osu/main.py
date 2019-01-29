import os
from threading import Thread
from tkinter import *
from tkinter import filedialog, ttk

from beatmap import beatmap_generator

BAD_DIFFICULTY_CHARACTERS = re.compile(r"[^\d,\. ]")
SPACES = re.compile(" ")

class InfoLabel:
    def __init__(self, parent, **grid_args):
        self.var = StringVar()
        self.label = ttk.Label(parent, textvariable=self.var)
        self.label.grid(**grid_args)

    def error(self, text):
        self.var.set(text)
        self.label.config(foreground="red", cursor="")
        self.label.unbind("<Button 1>")
    
    def info(self, text):
        self.var.set(text)
        self.label.config(foreground="black", cursor="")
        self.label.unbind("<Button 1>")

    def link(self, text, on_click):
        self.var.set(text)
        self.label.config(foreground="blue", cursor="hand2")
        self.label.bind("<Button 1>", on_click)

def create_input_row(row, text, mainframe, on_write):
    ttk.Label(mainframe, text=text, wraplength=120).grid(column=0, row=row, sticky=W)
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

def parse_difficulties(values):
    try:
        values = SPACES.sub("", values).split(",")
        return list(map(lambda x: float(x), values))
    except:
        return None

def is_valid_audio_file(filename):
    return os.path.isfile(filename) and os.path.splitext(filename)[1].lower() == ".mp3"

class GenerateBackgroundThread(Thread):
    def __init__(self, src, dst, difficulties, title, artist, callback):
        Thread.__init__(self)
        self.src = src
        self.dst = dst
        self.difficulties = difficulties
        self.title = title
        self.artist = artist
        self.callback = callback
    
    def run(self):
        error = None
        try:
            beatmap_generator.create_beatmapset(self.src, self.dst, self.difficulties, self.title, self.artist)
        except Exception as e:
            error = e
        self.callback(error, self.dst)

def open_folder_func(file):
    dir_path = os.path.dirname(os.path.realpath(file))
    def open_folder(*args):
        os.startfile(dir_path)
    return open_folder

def finish_generating(error, out_file):
    if error:
        info_label.error(str(error))
    else:
        info_label.link("Beatmaps generated successfully. Click here to show in folder.", open_folder_func(out_file))
    global generating
    generating = False
    update_button_enablement()

def generate(*args):
    # Perform some quick initial validation.
    audio_file = filename.get()
    if not is_valid_audio_file(audio_file):
        info_label.error("Invalid input file.")
        return
    difficulty_values = parse_difficulties(difficulties.get())
    if not difficulty_values:
        info_label.error("Invalid star difficulties format.")
        return
    info_label.info("")

    base_filename = os.path.splitext(os.path.basename(audio_file))[0]
    save_to_name = filedialog.asksaveasfilename(initialfile=f"{base_filename}.osz", filetypes=[("Executable beatmap files","*.osz")])
    if not save_to_name:
        return

    info_label.info("Generating beatmaps...")
    global generating
    generating = True
    generate_button.config(state=DISABLED)
    GenerateBackgroundThread(audio_file, save_to_name, difficulty_values, title.get(), artist.get(), finish_generating).start()

root = Tk()
root.title("osu beatmap generator")

mainframe = ttk.Frame(root, padding="12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(1, weight=1)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

ttk.Label(mainframe, text="Audio file (mp3):").grid(column=0, row=0, sticky=W)

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
difficulties = create_input_row(3, "Target star difficulties: (e.g. 3, 5.4, 7)", mainframe, restrict_difficulties_characters)

generate_button = ttk.Button(mainframe, text="Generate", command=generate)
generate_button.grid(column=1, row=4, sticky=E)
generate_button.config(state=DISABLED)
generating = False

info_label = InfoLabel(mainframe, column=0, row=5, columnspan=2, sticky=E)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)
root.mainloop()