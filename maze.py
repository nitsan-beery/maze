from tkinter import filedialog
import json
import global_vars as gv
from print_canvas import *
import random
import win32api


class TrailWall:
    def __init__(self, is_vertical=False, x=0, y=0):
        self.is_vertical = is_vertical
        self.x = x
        self.y = y


class Line:
    def __init__(self, is_wall=True):
        self.is_wall = is_wall

    def is_open(self):
        return not self.is_wall

    def open(self):
        self.is_wall = False


class Cell:
    def __init__(self, can_go_up=True, can_go_down=True, can_go_left=True, can_go_right=True, is_free=True, show_cell=False):
        self.can_go_up = can_go_up
        self.can_go_down = can_go_down
        self.can_go_left = can_go_left
        self.can_go_right = can_go_right
        self.is_free = is_free
        self.show_cell = show_cell


class Maze:
    def __init__(self, width=gv.MAZE_WIDTH, height=gv.MAZE_HEIGHT):
        self.width = width
        self.height = height
        self.board_width = max(gv.LINE_SIZE * (self.width+2) + 2 * gv.h_gap, gv.min_win_width)
        self.board_height = gv.LINE_SIZE * (self.height+2) + gv.v_gap
        self.x_pos = int((win32api.GetSystemMetrics(0) - self.board_width) * gv.win_x_pos) - gv.win_border
        self.y_pos = int((win32api.GetSystemMetrics(1) - self.board_height) * gv.win_y_pos) - gv.win_border
        self.start_col = random.randint(0, self.width-1)
        self.end_col = random.randint(0, self.width-1)
        self.h_lines, self.v_lines, self.cells = self.reset_state()
        self.left_trail_wall = []
        self.right_trail_wall = []
        self.trail = []
        self.marked_cells = []
        self.sub_mazes = []

    def reset(self, width=gv.MAZE_WIDTH, height=gv.MAZE_HEIGHT):
        self.width = width
        self.height = height
        self.board_width = max(gv.LINE_SIZE * (self.width+2) + 2 * gv.h_gap, gv.min_win_width)
        self.board_height = gv.LINE_SIZE * (self.height+2) + gv.v_gap
        self.start_col = random.randint(0, self.width-1)
        self.end_col = random.randint(0, self.width-1)
        self.h_lines, self.v_lines, self.cells = self.reset_state()
        self.left_trail_wall = []
        self.right_trail_wall = []
        self.trail = []
        self.marked_cells = []
        self.sub_mazes = []

    def set_maze(self, solve=True):
        sm = self.get_sub_maze((0, 0))
        self.fill_sub_maze_with_trails(sm)
        self.h_lines[self.height][self.end_col].open()
        if solve:
            self.solve_maze()

    def fill_sub_maze_with_trails(self, sm):
        self.set_trail((0, self.start_col))
        row, col = self.get_next_empty_cell_in_sub_maze(sm)
        while row is not None:
            new_sm = self.get_sub_maze((row, col))
            tw = self.get_sub_maze_inner_border(new_sm)
            i = random.randint(0, len(tw) - 1)
            self.open_trail_wall(tw[i])
            cell = self.get_entrance_cell_to_sub_maze(new_sm)
            self.set_trail(cell)
            row, col = self.get_next_empty_cell_in_sub_maze(sm)

    # return list of TrailWalls = inner border of the sub maze (one and only one of them should be opened)
    def get_sub_maze_inner_border(self, sm):
        inner_border = []
        for cell in sm:
            row = cell[0]
            col = cell[1]
            # upper wall
            if row > 0 and not self.cells[row-1][col].is_free:
                tw = TrailWall(is_vertical=False, x=row, y=col)
                inner_border.append(tw)
            # lower wall
            if row < self.height - 1 and not self.cells[row+1][col].is_free:
                tw = TrailWall(is_vertical=False, x=row+1, y=col)
                inner_border.append(tw)
            # left wall
            if col > 0 and not self.cells[row][col-1].is_free:
                tw = TrailWall(is_vertical=True, x=col, y=row)
                inner_border.append(tw)
            # right wall
            if col < self.width-1 and not self.cells[row][col+1].is_free:
                tw = TrailWall(is_vertical=True, x=col+1, y=row)
                inner_border.append(tw)
        return inner_border

    def get_entrance_cell_to_sub_maze(self, sm):
        for cell in sm:
            row = cell[0]
            col = cell[1]
            right_wall = self.v_lines[col][row]
            left_wall = self.v_lines[col+1][row]
            ceiling = self.h_lines[row][col]
            floor = self.h_lines[row+1][col]
            if left_wall.is_open() or right_wall.is_open() or ceiling.is_open() or floor.is_open():
                return cell
        return None

    def open_trail_wall(self, tw):
        if tw.is_vertical:
            self.v_lines[tw.x][tw.y].open()
        else:
            self.h_lines[tw.x][tw.y].open()

    def get_sub_maze(self, first_cell):
        cells = self.copy_cells(self.cells)
        return self.get_free_neighbours(first_cell, cells)

    def get_free_neighbours(self, first_cell, cells):
        row = first_cell[0]
        col = first_cell[1]
        if row < 0 or row >= self.height:
            return []
        if col < 0 or col >= self.width:
            return []
        if not cells[row][col].is_free:
            return []
        cells[row][col].is_free = False
        free_cells = [first_cell]
        free_cells += self.get_free_neighbours((row, col-1), cells)
        free_cells += self.get_free_neighbours((row, col+1), cells)
        free_cells += self.get_free_neighbours((row-1, col), cells)
        free_cells += self.get_free_neighbours((row+1, col), cells)
        return free_cells

    def copy_cells(self, cells):
        cs = []
        for row in range(self.height):
            cs_row = []
            for col in range(self.width):
                c = Cell()
                c.is_free = cells[row][col].is_free
                cs_row.append(c)
            cs.append(cs_row)
        return cs

    def get_next_empty_cell_in_sub_maze(self, sm):
        for row in range(self.height):
            for col in range(self.width):
                if self.cells[row][col].is_free:
                    return row, col
        return None, None

    def set_trail(self, first_cell=(0, 0)):
        self.cells[first_cell[0]][first_cell[1]].is_free = False
        cell = first_cell
        i = random.randint(0, 1)
        if i:
            side = 'v'
        else:
            side = 'h'
        while cell is not None:
            next_cell, direction = self.choose_next_cell(cell, side)
            if next_cell is not None:
                self.add_trail_between_cells(direction, cell, next_cell)
                if direction == 'left' or direction == 'right':
                    side = 'v'
                else:
                    side = 'h'
            cell = next_cell

    def add_trail_between_cells(self, direction, cell1, cell2):
        row1 = cell1[0]
        col1 = cell1[1]
        row2 = cell2[0]
        col2 = cell2[1]

        if direction == 'right':
            row = row1
            for col in range(col1, col2):
                self.cells[row][col].is_free = False
                self.v_lines[col+1][row].is_wall = False
        elif direction == 'left':
            row = row1
            for col in range(col1, col2, -1):
                self.cells[row][col].is_free = False
                self.v_lines[col][row].is_wall = False
        elif direction == 'down':
            col = col1
            for row in range(row1, row2):
                self.cells[row][col].is_free = False
                self.h_lines[row+1][col].is_wall = False
        else:   # up
            col = col1
            for row in range(row1, row2, -1):
                self.cells[row][col].is_free = False
                self.h_lines[row][col].is_wall = False

        self.cells[row2][col2].is_free = False

    # return next cell in trail and direction towards it
    def choose_next_cell(self, current_cell, side):
        row = current_cell[0]
        col = current_cell[1]
        next_row = row
        next_col = col
        return_side = None
        cell = self.cells[row][col]
        lim_left_col = self.get_lim_col(row, col, 'left')
        if lim_left_col == col:
            cell.can_go_left = False
        elif col - lim_left_col > gv.MAX_STRAIT_LINE:
            lim_left_col = col - gv.MAX_STRAIT_LINE
        lim_right_col = self.get_lim_col(row, col, 'right')
        if lim_right_col == col:
            cell.can_go_right = False
        elif lim_right_col - col > gv.MAX_STRAIT_LINE:
            lim_right_col = col + gv.MAX_STRAIT_LINE
        lim_up_row = self.get_lim_row(col, row, 'up')
        if lim_up_row == row:
            cell.can_go_up = False
        elif row - lim_up_row > gv.MAX_STRAIT_LINE:
            lim_up_row = row - gv.MAX_STRAIT_LINE
        lim_down_row = self.get_lim_row(col, row, 'down')
        if lim_down_row == row:
            cell.can_go_down = False
        elif lim_down_row - row > gv.MAX_STRAIT_LINE:
            lim_down_row = row + gv.MAX_STRAIT_LINE

        # leave only one side available
        if cell.can_go_right and cell.can_go_left:
            i = random.randint(0, 1)
            if i:
                cell.can_go_left = False
            else:
                cell.can_go_right = False
        if cell.can_go_up and cell.can_go_down:
            i = random.randint(0, 1)
            if i:
                cell.can_go_down = False
            else:
                cell.can_go_up = False

        # nowhere to go
        if not (cell.can_go_left or cell.can_go_right or cell.can_go_up or cell.can_go_down):
            return None, None

        if side == 'h' and (cell.can_go_left or cell.can_go_right):
            cell.can_go_down = False
            cell.can_go_up = False
        elif side == 'v' and (cell.can_go_up or cell.can_go_down):
            cell.can_go_left = False
            cell.can_go_right = False

        # only one side available
        if cell.can_go_left:
            next_col = random.randint(lim_left_col, col-1)
            return_side = 'left'
        elif cell.can_go_right:
            next_col = random.randint(col+1, lim_right_col)
            return_side = 'right'
        elif cell.can_go_up:
            next_row = random.randint(lim_up_row, row-1)
            return_side = 'up'
        elif cell.can_go_down:
            next_row = random.randint(row+1, lim_down_row)
            return_side = 'down'

        return (next_row, next_col), return_side

    # return last free cell in row from start_col towards 'left' or 'right'
    def get_lim_col(self, row, start_col, side):
        if side == 'right':
            i = 1
        else:
            i = -1
        col = start_col + i
        while 0 <= col < self.width:
            if self.cells[row][col].is_free:
                col += i
            else:
                break
        return col - i

    # return last free cell in col from start_row towards 'down' or 'up'
    def get_lim_row(self, col, start_row, side):
        if side == 'down':
            i = 1
        else:
            i = -1
        row = start_row + i
        while 0 <= row < self.height:
            if self.cells[row][col].is_free:
                row += i
            else:
                break
        return row - i

    def solve_maze(self):
        pass

    def reset_state(self):
        # set all lines to default = closed, no part of the trail
        h_lines = []
        for row in range(self.height+1):
            current_row = []
            for col in range(self.width):
                l = Line()
                current_row.append(l)
            h_lines.append(current_row)

        v_lines = []
        for col in range(self.width+1):
            current_col = []
            for row in range(self.height):
                l = Line()
                current_col.append(l)
            v_lines.append(current_col)

        # set all cells to default = free, can go all directions
        cells = []
        for row in range(self.height):
            current_row = []
            for col in range(self.width):
                current_row.append(Cell())
            cells.append(current_row)

        # open upper entrance
        h_lines[0][self.start_col].is_wall = False

        return h_lines, v_lines, cells

    def show_maze(self, show_marked_cells=False, pause=0):
        window = tk.Tk()
        window.title('Maze')
        window.geometry(f'{self.board_width}x{self.board_height+80}+{self.x_pos}+{self.y_pos}')

        frame_1 = tk.Frame(window)
        frame_1.pack(fill='both', side='top', expand=tk.YES)
        frame_2 = tk.Frame(window)
        frame_2.pack(fill='both', side='bottom', expand=tk.YES)
        frame_3 = tk.Frame(window)
        frame_3.pack(fill='both', side='bottom', expand=tk.YES)
        board = tk.Canvas(frame_1, width=self.board_width, height=self.board_height)
        board.pack(expand=tk.YES, fill=tk.BOTH)

        button_show_trail = tk.Button(frame_2, text="Show trail", command=lambda: self.toggle_trail(window, board, button_show_trail))
        button_print_maze = tk.Button(frame_2, text="Print maze", command=lambda: print_canvas(window, board))
        button_save = tk.Button(frame_2, text="Save maze", command=lambda: self.save_maze(window))
        button_load = tk.Button(frame_2, text='Load maze', command=lambda: self.load_maze(window))

        button_show_trail.pack(side=tk.LEFT, padx=5, pady=5)
        button_print_maze.pack(side=tk.LEFT, padx=5)
        button_save.pack(side=tk.LEFT, padx=5)
        button_load.pack(side=tk.LEFT, padx=5)

        entry_width = tk.Entry(frame_3, width=4, justify=tk.CENTER)
        label_x = tk.Label(frame_3, text='x', padx=1)
        entry_height = tk.Entry(frame_3, width=4, justify=tk.CENTER)
        button_new = tk.Button(frame_3, text='New maze', command=lambda: self.select_new_maze(window, entry_width, entry_height))

        button_new.pack(side=tk.LEFT, padx=5)
        entry_width.pack(side=tk.LEFT, padx=5)
        label_x.pack(side=tk.LEFT)
        entry_height.pack(side=tk.LEFT, padx=5)

        entry_width.delete(0, tk.END)
        entry_width.insert(0, self.width)
        entry_height.delete(0, tk.END)
        entry_height.insert(0, self.height)

        x_00 = gv.X_00
        y_00 = gv.Y_00
        row = 0
        trail_cells = None

        # entrance
        x = x_00 + gv.LINE_SIZE * self.start_col
        start_y = y_00
        end_y = start_y - gv.LINE_SIZE/2
        board.create_line(x, start_y, x, end_y, fill=gv.WALL_LINE_COLOR)
        x += gv.LINE_SIZE
        board.create_line(x, start_y, x, end_y, fill=gv.WALL_LINE_COLOR)

        for line in self.h_lines:
            for col in range(len(line)):
                y = y_00 + gv.LINE_SIZE*row
                start_x = x_00 + gv.LINE_SIZE*col
                end_x = start_x + gv.LINE_SIZE
                if not line[col].is_open():
                    board.create_line(start_x, y, end_x, y, fill=gv.WALL_LINE_COLOR)
                if pause:
                    window.update()
            row += 1
        col = 0
        for line in self.v_lines:
            for row in range(len(line)):
                x = x_00 + gv.LINE_SIZE*col
                start_y = y_00 + gv.LINE_SIZE * row
                end_y = start_y + gv.LINE_SIZE
                if not line[row].is_open():
                    board.create_line(x, start_y, x, end_y, fill=gv.WALL_LINE_COLOR)
                    if pause:
                        window.update()
            col += 1

        # exit
        x = x_00 + gv.LINE_SIZE * self.end_col
        start_y = y_00 + self.height * gv.LINE_SIZE
        end_y = start_y + gv.LINE_SIZE/2
        board.create_line(x, start_y, x, end_y, fill=gv.WALL_LINE_COLOR)
        x += gv.LINE_SIZE
        board.create_line(x, start_y, x, end_y, fill=gv.WALL_LINE_COLOR)
        # trail
        if show_marked_cells:
            self.get_and_show_marked_cells(window, board)

        window.update()
        window.mainloop()

    def set_maze_data(self, json_data):
        self.width = json_data.get("width")
        self.height = json_data.get("height")
        self.board_width = max(gv.LINE_SIZE * (self.width+2), gv.min_win_width)
        self.board_height = gv.LINE_SIZE * (self.height+2)
        self.start_col = json_data.get("start_col")
        self.end_col = json_data.get("end_col")
        self.h_lines, self.v_lines, self.cells = self.reset_state()
        self.trail = json_data.get("trail")
        for cell in self.trail:
            self.cells[cell[0]][cell[1]].show_cell = True

        h_lines = json_data.get("h_lines")
        v_lines = json_data.get("v_lines")

        for row in range(self.height+1):
            for col in range(self.width):
                line = h_lines[row][col]
                self.h_lines[row][col].is_wall = line

        for col in range(self.width+1):
            for row in range(self.height):
                line = v_lines[col][row]
                self.v_lines[col][row].is_wall = line

    def get_maze_data(self):
        h_lines = []
        v_lines = []
        for row in range(self.height+1):
            strip = []
            for col in range(self.width):
                line = self.h_lines[row][col]
                strip.append(not line.is_open())
            h_lines.append(strip)

        for col in range(self.width+1):
            strip = []
            for row in range(self.height):
                line = self.v_lines[col][row]
                strip.append(not line.is_open())
            v_lines.append(strip)

        md = {
            "width": self.width,
            "height": self.height,
            "start_col": self.start_col,
            "end_col": self.end_col,
            "h_lines": h_lines,
            "v_lines": v_lines,
            "trail": self.trail
        }

        return md

    def save_maze(self, root):
        default_file_name = f'maze-{self.width}x{self.height} trail_length-{len(self.trail)}'
        filename = filedialog.asksaveasfilename(parent=root, initialdir="./saved_mazes/", title="Select file",
                                                initialfile=default_file_name, defaultextension=".json",
                                                filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if filename == '':
            return
        maze_data = self.get_maze_data()
        with open(filename, "w") as json_file:
            json.dump(maze_data, json_file)

    def select_new_maze(self, root, entry_width, entry_height):
        is_valid_size = True
        width = 0
        height = 0
        try:
            width = int(entry_width.get())
            height = int(entry_height.get())
        except ValueError:
            is_valid_size = False
        if is_valid_size:
            if width < 2 or height < 2:
                is_valid_size = False
        if is_valid_size:
            self.x_pos = root.winfo_x()
            self.y_pos = root.winfo_y()
            root.destroy()
            self.reset(width, height)
            self.set_maze()
            self.show_maze()

        else:
            print(f'Invalid size (width x height)')

    def load_maze(self, root):
        filename = filedialog.askopenfilename(parent=root, initialdir="./saved_mazes/", title="Select file",
                                                   filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if filename == '':
            return
        self.x_pos = root.winfo_x()
        self.y_pos = root.winfo_y()
        root.destroy()
        with open(filename, "r") as json_file:
            maze_data = json.load(json_file)
        self.set_maze_data(maze_data)
        self.show_maze()

    def delete_marked_cells(self, window, board):
        for c in self.marked_cells:
            board.delete(c)
        window.update()

    def get_and_show_marked_cells(self, window, board):
        x_00 = gv.X_00
        y_00 = gv.Y_00
        self.marked_cells = []

        x_00 += gv.LINE_SIZE/3
        y_00 += gv.LINE_SIZE/3
        top_x = x_00 + gv.LINE_SIZE * self.start_col
        bottom_x = top_x + gv.LINE_SIZE / 3
        top_y = y_00 - gv.LINE_SIZE
        bottom_y = top_y + gv.LINE_SIZE / 3
        self.marked_cells.append(board.create_oval(top_x, top_y, bottom_x, bottom_y, fill=gv.SHOW_CELL_COLOR, outline=gv.SHOW_CELL_COLOR))
        for row in range(self.height):
            for col in range(self.width):
                if self.cells[row][col].show_cell:
                    top_x = x_00 + gv.LINE_SIZE*col
                    bottom_x = top_x + gv.LINE_SIZE/3
                    top_y = y_00 + gv.LINE_SIZE*row
                    bottom_y = top_y + gv.LINE_SIZE/3
                    self.marked_cells.append(board.create_oval(top_x, top_y, bottom_x, bottom_y, fill=gv.SHOW_CELL_COLOR, outline=gv.SHOW_CELL_COLOR))
        top_x = x_00 + gv.LINE_SIZE * self.end_col
        bottom_x = top_x + gv.LINE_SIZE / 3
        top_y = y_00 + (row+1)*gv.LINE_SIZE
        bottom_y = top_y + gv.LINE_SIZE / 3
        self.marked_cells.append(board.create_oval(top_x, top_y, bottom_x, bottom_y, fill=gv.SHOW_CELL_COLOR, outline=gv.SHOW_CELL_COLOR))
        window.update()

    def toggle(self, b):
        if b.config('relief')[-1] == 'sunken':
            b.config(relief="raised")
            return 'off'
        else:
            b.config(relief="sunken")
            return 'on'

    def toggle_trail(self, window, board, button_show_trail):
        if self.toggle(button_show_trail) == 'on':
            self.get_and_show_marked_cells(window, board)
        else:
            self.delete_marked_cells(window, board)
        window.update()

    #debug
    def print_cells(self):
        print('--------------------------------')
        for row in range(self.height):
            line = ''
            for col in range(self.width):
                cell = self.cells[row][col]
                s = ''
                if cell.is_free:
                    s += 'O'
                else:
                    s += '@'
                if cell.can_go_up:
                    s += '^'
                else:
                    s += ' '
                if cell.can_go_down:
                    s += '!'
                else:
                    s += ' '
                if cell.can_go_left:
                    s += '<'
                else:
                    s += ' '
                if cell.can_go_right:
                    s += '>    '
                else:
                    s += '     '
                line += s
            print(line)




