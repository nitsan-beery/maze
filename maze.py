import global_vars as gv
import random
import tkinter as tk

def my_randint(a, b):
    return random.randint(a, b)
    
    
class Line:
    def __init__(self, is_open=False, is_left_wall=False, is_right_wall=False):
        self.is_open = is_open
        self.is_left_wall = is_left_wall
        self.is_right_wall = is_right_wall


class Cell:
    def __init__(self, can_go_up=False, can_go_down=False, can_go_left=False, can_go_right=False, is_part_of_trail=False):
        self.can_go_up = can_go_up
        self.can_go_down = can_go_down
        self.can_go_left = can_go_left
        self.can_go_right = can_go_right
        self.is_part_of_trail = is_part_of_trail


# old version row by row
# keep open from left wall to right wall
class OpenPart:
    def __init__(self, left_wall=0, right_wall=0, upper_col=None, col_2=None, is_col_2_lower=True):
        self.left_wall = left_wall
        self.right_wall = right_wall
        self.upper_col = upper_col
        self.col_2 = col_2
        self.is_col_2_lower = is_col_2_lower


class Maze:
    def __init__(self, width=gv.MAZE_WIDTH, height=gv.MAZE_HEIGHT):
        self.width = width
        self.height = height
        self.start_col = my_randint(0, width-1)
        self.end_col = my_randint(0, width-1)
        self.h_lines, self.v_lines, self.keep_open = self.reset_state()

    def set_trail(self):
        pass

    # old version - row by row
    def set_trail_old(self):
        upper_col = self.start_col
        for row in range(0, self.height-1):
            lower_col = self.get_next_col(row, upper_col)
            left_col, right_col = self.get_left_right(upper_col, lower_col)
            left_wall_lim = self.get_nearest_wall(row, left_col, 'left')
            right_wall_lim = self.get_nearest_wall(row, right_col, 'right')
            left_wall, right_wall = self.get_left_and_right_walls(left_wall_lim, right_wall_lim, left_col, right_col)
            self.v_lines[left_wall][row].is_open = False
            self.v_lines[right_wall][row].is_open = False
            open_part = OpenPart(left_wall, right_wall, upper_col, lower_col, True)
            self.insert_open_part(row, open_part)
            self.h_lines[row + 1][lower_col].is_open = True
            # debug
            print(f'row: {row}   left wall: {left_wall}   right wall: {right_wall}   upper col: {upper_col}   lower col: {lower_col}')
            for part in self.keep_open[row]:
                # continue
                # if enough seperation between the columns set tunnel under the part
                if (part.upper_col - part.col_2) * (part.upper_col - part.col_2) > 4:
                    do_tunnel = my_randint(0, 1)
                    if part.is_col_2_lower:
                        # if do_tunnel:
                        left_wall, right_wall = self.set_tunnel(row, part)
            divider_list = self.get_dividers_list(row)
#            self.set_dividers(row, divider_list)
            self.make_holes_under_blocked_part(row, lower_col, divider_list)
            upper_col = lower_col
#            debug
#            self.show_maze()
        # handle last row
        lower_col = self.get_next_col(self.height-1, upper_col)
        self.h_lines[self.height][lower_col].is_open = True

    def get_left_and_right_walls(self, left_lim, right_lim, left_col, right_col):
        if left_col-left_lim > gv.MAX_ADD_TO_PART_SIZE:
            left_lim = left_col-gv.MAX_ADD_TO_PART_SIZE
        if right_lim-(right_col+1) > gv.MAX_ADD_TO_PART_SIZE:
            right_lim = right_col+1+gv.MAX_ADD_TO_PART_SIZE
        left_wall = my_randint(left_lim, left_col)
        right_wall = my_randint(right_col + 1, right_lim)
        return left_wall, right_wall

    # old version - row by row
    def get_next_col(self, row, upper_col):
        if row > self.height-1:
            return
        l_lim_wall = self.get_nearest_wall(row, upper_col, 'left')
        r_lim_wall = self.get_nearest_wall(row, upper_col, 'right')
        side = self.choose_side(upper_col, l_lim_wall, r_lim_wall)
        if side == 'right':
            lower_col = my_randint(upper_col, r_lim_wall-1)
        else:
            lower_col = my_randint(l_lim_wall, upper_col)
        return lower_col

    # old version - row by row
    def insert_open_part(self, row, op):
        self.keep_open[row].append(op)

    def get_nearest_wall(self, row, col, side):
        wall = col
        i = -1
        if side == 'right':
            wall += 1
            i = 1
        while self.v_lines[wall][row].is_open:
            wall += i
        return wall

    def get_left_right(self, col_1, col_2):
        left_col = col_1
        right_col = col_2
        if left_col > right_col:
            left_col, right_col = right_col, left_col
        return left_col, right_col

    def is_floor_blocked(self, row, left_wall, right_wall):
        do_blocked = True
        for i in range(left_wall, right_wall):
            if self.h_lines[row+1][i].is_open:
                do_blocked = False
                break
        return do_blocked

    # old version - row by row
    def get_dividers_list(self, row):
        divider_list = []
        left_lim = 0
        for part in self.keep_open[row]:
            if part.left_wall > left_lim:
                divider_list.append((left_lim, part.left_wall))
            left_lim = part.right_wall
        if left_lim < self.width:
            divider_list.append((left_lim, self.width))
        return divider_list

    # old version - row by row
    def set_dividers(self, row, divider_list):
        for part in divider_list:
            num_dividers = 0
            l_lim = part[0]
            r_lim = part[1]
            i = l_lim + my_randint(0, gv.DIVIDERS_RESOLUTION)
            max_dividers = int((r_lim-l_lim)/gv.DIVIDERS_RESOLUTION)
            while i < r_lim and num_dividers < max_dividers:
                do_block = my_randint(0, 1)
                if do_block:
                    self.v_lines[i + 1][row].is_open = False
                if not self.v_lines[i + 1][row].is_open:
                    num_dividers += 1
                i += gv.DIVIDERS_RESOLUTION
                #debug
#                else:
#                    print(f'last part - l_lim: {l_lim}   r_lim: {r_lim}   last_divider: {last_divider}')

    # old version - row by row
    # make hole under row, where trail_col is the row lower col
    def make_holes_under_blocked_part(self, row, trail_col, divider_list):
        #debug
        s = f'make holes under row: {row}   - '
        for part in divider_list:
            l_lim = part[0]
            r_lim = part[1]
            #debug
            s += f'({l_lim}-{r_lim}) '
            next_wall = l_lim
            while next_wall < r_lim:
                next_wall = self.get_nearest_wall(row, l_lim, 'right')
                if self.is_floor_blocked(row, l_lim, next_wall):
                    j = my_randint(l_lim, next_wall-1)
                    self.h_lines[row + 1][j].is_open = True
                    if row < self.height-2:
                        if j < trail_col:
                            self.set_wall(row+1, j+1, trail_col)
                        else:
                            self.set_wall(row+1, trail_col+1, j)
                    #debug
                    s += f'hole: {j}   '
                l_lim = next_wall
        #debug
        print(s)

    def set_wall(self, row, left_lim, right_lim):
        j = my_randint(left_lim, right_lim)
        self.v_lines[j][row].is_open = False

    # old version - row by row
    # set a tunnel under current row. divider = wall on upper row, wall = wall on lower row
    def set_tunnel(self, row, part):
        is_upper_col_on_the_right = True
        if part.is_col_2_lower:
            if part.upper_col > part.col_2:
                left_hole_lim = part.col_2 + 1
                right_hole_lim = part.right_wall - 1
                left_divider_wall_lim = part.col_2 + 2
                right_divider_wall_lim = part.upper_col
            else:
                is_upper_col_on_the_right = False
                left_hole_lim = part.left_wall
                right_hole_lim = part.col_2 - 1
                left_divider_wall_lim = part.upper_col+1
                right_divider_wall_lim = part.col_2 - 1
        # tunnel with 2 holes on the upper surface
        else:
            left_col, right_col = self.get_left_right(part.upper_col, part.col_2)
            left_hole_lim = part.left_wall
            right_hole_lim = part.right_wall-1
            left_divider_wall_lim = left_col+1
            right_divider_wall_lim = right_col

        # left hole max = divider-1,  right hole min = divider
        divider = my_randint(left_divider_wall_lim, right_divider_wall_lim)
        self.v_lines[divider][row].is_open = False
        left_hole = my_randint(left_hole_lim, divider-1)
        right_hole = my_randint(divider, right_hole_lim)
        self.h_lines[row+1][left_hole].is_open = True
        self.h_lines[row+1][right_hole].is_open = True
        
        left_wall_lim = part.left_wall
        right_wall_lim = part.right_wall

        if part.is_col_2_lower:
            if is_upper_col_on_the_right:
                left_wall_lim = part.col_2+1
            else:
                right_wall_lim = part.col_2

        left_wall, right_wall = self.get_left_and_right_walls(left_wall_lim, right_wall_lim, left_hole, right_hole)
        self.v_lines[left_wall][row+1].is_open = False
        self.v_lines[right_wall][row+1].is_open = False
        open_part = OpenPart(left_wall, right_wall, left_hole, right_hole, False)
        self.insert_open_part(row+1, open_part)

        # debug
        print(f'tunnel under row {row}   left wall: {left_wall}   right wall: {right_wall}   left hole: {left_hole}   right hole: {right_hole}   upper divider: {divider}')
        return left_wall, right_wall

    # old version - row by row
    def choose_side(self, col, l_lim_wall, r_lim_wall):
        if col == l_lim_wall:
            side = 'right'
        elif col == r_lim_wall-1:
            side = 'left'
        else:
            i = my_randint(0, 1)
            if i:
                side = 'right'
            else:
                side = 'left'
        return side

    def reset_state(self):
        # set all horizontal lines to default = close, no part of the trail
        h_lines = []
        for row in range(self.height+1):
            current_row = []
            for col in range(self.width):
                l = Line()
                current_row.append(l)
            h_lines.append(current_row)

        # set all vertical lines to default = close no part of the trail
        v_lines = []
        for col in range(self.width+1):
            current_col = []
            for row in range(self.height):
                l = Line()
                current_col.append(l)
            v_lines.append(current_col)

        # open first and last row
        h_lines[0][self.start_col].is_open = True
        h_lines[self.height][self.end_col].is_open = True

        cells = []
        for row in range(self.height):
            current_row = []
            for col in range(self.width):
                c = Cell()
                if row%2:
                    c.can_go_left = True
                else:
                    c.can_go_right = True
                if col%2:
                    c.can_go_up = True
                else:
                    c.can_go_down = True
                current_row.append(c)
            cells.append(current_row)

        # set first row
        for col in range(self.start_col):
            cells[0][col].can_go_right = False
            cells[0][col].can_go_left = True
        for col in range(self.start_col, self.width):
            cells[0][col].can_go_right = True
            cells[0][col].can_go_left = False
        cells[0][self.start_col].can_go_left = True
        cells[0][self.start_col].can_go_left = True

        # set last row
        for col in range(self.end_col):
            cells[self.height-1][col].can_go_right = True
            cells[self.height-1][col].can_go_left = False
            cells[self.height - 1][col].can_go_down = False
        for col in range(self.end_col, self.width):
            cells[self.height-1][col].can_go_right = False
            cells[self.height-1][col].can_go_left = True
            cells[self.height - 1][col].can_go_down = False
        cells[self.height-1][self.end_col].can_go_left = False
        cells[self.height-1][self.end_col].can_go_right = False
        cells[self.height-1][self.end_col].can_go_up = False

        # set first and last columns
        for row in range(self.height-1):
            cells[row][0].can_go_up = False
            cells[row][0].can_go_down = True
            cells[row][0].can_go_left = False
            cells[row][self.width-1].can_go_up = False
            cells[row][self.width-1].can_go_down = True
            cells[row][self.width-1].can_go_right = False
        cells[self.height-1][0].can_go_down = False
        cells[self.height-1][self.width-1].can_go_down = False

        return h_lines, v_lines, cells

    def show_maze(self):
        window = tk.Tk()
        window.title('Maze')
        frame_1 = tk.Frame(window)
        frame_1.pack(fill='both', side='top', expand=tk.YES)
        board = tk.Canvas(frame_1, width=gv.WINDOW_WIDTH, height=gv.WINDOW_HEIGHT)
        board.pack(expand=tk.YES, fill=tk.BOTH)

        x_00 = gv.X_00
        y_00 = gv.Y_00
        row = 0
        for line in self.h_lines:
            for col in range(len(line)):
                y = y_00 + gv.LINE_SIZE*row
                start_x = x_00 + gv.LINE_SIZE*col
                end_x = start_x + gv.LINE_SIZE
                if not line[col].is_open:
                    board.create_line(start_x, y, end_x, y, fill=self.get_line_color(line[col]))
            row += 1
        col = 0
        for line in self.v_lines:
            for row in range(len(line)):
                x = x_00 + gv.LINE_SIZE*col
                start_y = y_00 + gv.LINE_SIZE * row
                end_y = start_y + gv.LINE_SIZE
                if not line[row].is_open:
                    board.create_line(x, start_y, x, end_y, fill=self.get_line_color(line[row]))
            col += 1
        window.update()
        window.mainloop()

    def get_line_color(self, line):
        color = gv.NO_TRAIL_LINE_COLOR
        if line.is_left_wall and line.is_right_wall:
            color = gv.BOTH_SIDES_TRAIL_LINE_COLOR
        elif line.is_left_wall:
            color = gv.LEFT_TRAIL_LINE_COLOR
        elif line.is_right_wall:
            color = gv.RIGHT_TRAIL_LINE_COLOR
        return color


