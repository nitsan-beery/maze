from maze import *

class ChooseMaze:
    def __init__(self):
        self.window_main = tk.Tk(className=' Choose maze')
        self.window_main.geometry('250x120')
        self.window_main.resizable(0, 0)

        self.frame_1 = tk.Frame(self.window_main)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH)
        self.frame_2 = tk.Frame(self.window_main)
        self.frame_2.pack(side=tk.TOP, fill=tk.BOTH, ipady=6)
        self.frame_3 = tk.Frame(self.window_main)
        self.frame_3.pack(side=tk.BOTTOM, fill=tk.BOTH, pady=5)

        self.label_empty_11 = tk.Label(self.frame_1, text='')
        self.label_size = tk.Label(self.frame_1, text='size', padx=5, pady=10)
        self.label_empty_11.grid(row=0, column=0, padx=55)
        self.label_size.grid(row=0, column=1)

        self.label_empty_21 = tk.Label(self.frame_2, text='')
        self.entry_width = tk.Entry(self.frame_2, width=4, justify=tk.CENTER)
        self.label_x = tk.Label(self.frame_2, text='x', padx=1)
        self.entry_height = tk.Entry(self.frame_2, width=4, justify=tk.CENTER)
        self.label_empty_21.grid(row=0, column=0, padx=44)
        self.entry_width.grid(row=0, column=1, padx=1, sticky='E')
        self.label_x.grid(row=0, column=2, padx=2, sticky='W')
        self.entry_height.grid(row=0, column=3)

        self.button_show = tk.Button(self.frame_3, text='Show maze', bg='#DDF2FF', command=lambda: self.show_maze())
        self.button_load = tk.Button(self.frame_3, text='Load maze', command=lambda: self.load_maze())
        self.button_show.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_load.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)

        self.entry_width.insert(0, gv.MAZE_WIDTH)
        self.entry_height.insert(0, gv.MAZE_HEIGHT)
        self.entry_width.focus_set()
        self.window_main.bind('<Key>', self.key)

    def show_maze(self):
        is_valid_size = True
        try:
            width = int(self.entry_width.get())
        except ValueError:
            is_valid_size = False
        try:
            height = int(self.entry_height.get())
        except ValueError:
            is_valid_size = False
        if is_valid_size:
            if width < 2 or height < 2:
                is_valid_size = False
        if is_valid_size:
            m = Maze(width, height)
            m.set_maze()
            #debug
            print(f'length: {m.info.trail_length}   decoy polygons: {m.info.num_of_decoy_polygons}')
            m.show_maze()
        else:
            print(f'Invalid size (width x height)')

    def load_maze(self):
        pass

    def key(self, event):
        if event.keycode == 13:
            self.show_maze()

