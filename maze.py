from tkinter import filedialog
import json
import global_vars as gv
from print_canvas import *
import random
import win32api


class SubMazeRow:
    def __init__(self, row=0, left_col=0, right_col=0):
        self.row = row
        self.left_col = left_col
        self.right_col = right_col
    
    
class TrailWall:
    def __init__(self, is_vertical=False, x=0, y=0):
        self.is_vertical = is_vertical
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.is_vertical == other.is_vertical and self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return not self.__eq__(other)


class Line:
    def __init__(self, is_wall=False, is_left_trail_wall=False, is_right_trail_wall=False):
        self.is_wall = is_wall
        self.is_left_trail_wall = is_left_trail_wall
        self.is_right_trail_wall = is_right_trail_wall
        
    def is_open(self):
        return not (self.is_wall or self.is_left_trail_wall or self.is_right_trail_wall)

    def clear_walls(self):
        self.is_wall = False
        self.is_left_trail_wall = False
        self.is_right_trail_wall = False


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

    def set_maze(self):
        sm = self.get_empty_sub_maze(0, 0)
        self.fill_sub_maze_with_trails(sm)
        self.h_lines[self.height][self.end_col].clear_walls()

    def fill_sub_maze_with_trails_new(self, sm):
        self.set_trail_in_sub_maze(sm)
        row, col = self.get_next_empty_cell_in_sub_maze(sm)
        while row is not None:
            new_sm = self.get_empty_sub_maze(row, col)
            tw = self.get_sub_maze_inner_border(new_sm)
            # debug
            self.clean_tw()
            self.mark_tw(tw)
            self.show_maze()
            i = random.randint(0, len(tw) - 1)
            self.open_trail_wall(tw[i])
            self.set_trail_in_sub_maze(new_sm)
            row, col = self.get_next_empty_cell_in_sub_maze(sm)

    # debug
    def mark_tw(self, tw):
        for t in tw:
            if t.is_vertical:
                self.v_lines[t.x][t.y].is_right_trail_wall = True
            else:
                self.h_lines[t.x][t.y].is_right_trail_wall = True

    # debug
    def clean_tw(self):
        for row in self.h_lines:
            for l in row:
                l.is_right_trail_wall = False
                l.is_left_trail_wall = False
        for col in self.v_lines:
            for l in col:
                l.is_right_trail_wall = False
                l.is_left_trail_wall = False

    def fill_sub_maze_with_trails(self, sm):
        self.set_trail_in_sub_maze(sm)
        row, col = self.get_next_empty_cell_in_sub_maze(sm)
        while row is not None:
            new_sm = self.get_empty_sub_maze(row, col)
            tw = self.get_sub_maze_trail_walls(new_sm)
            i = random.randint(0, len(tw) - 1)
            self.open_trail_wall(tw[i])
            self.set_trail_in_sub_maze(new_sm)
            row, col = self.get_next_empty_cell_in_sub_maze(sm)

    def set_trail_in_sub_maze(self, sm):
        entry_side, cell = self.get_entrance_cell_to_sub_maze(sm)
        row = cell[0]
        col = cell[1]
        if entry_side == 'up':
            self.cells[row][col].can_go_down = False
        elif entry_side == 'down':
            self.cells[row][col].can_go_up = False
        elif entry_side == 'left':
            self.cells[row][col].can_go_right = False
        elif entry_side == 'right':
            self.cells[row][col].can_go_left = False
        trail = self.set_trail(first_cell=cell, prev_dir=entry_side)
        for cell in trail:
            row = cell[0]
            col = cell[1]
            self.cells[row][col].is_free = False

    # return list of TrailWalls = inner border of the sub maze (one and only one of them should be opened)
    def get_sub_maze_inner_border(self, sm):
        inner_border = []
        rows = self.get_sub_maze_rows(sm)
        # first row
        row = rows[0].row
        # if first row == 0 upper border is outer maze border and can't be opened
        if row > 0:
            for col in range(rows[0].left_col, rows[0].right_col+1):
                tw = TrailWall(is_vertical=False, x=row, y=col)
                inner_border.append(tw)
        prev_left = rows[0].left_col
        prev_right = rows[0].right_col
        # left and right columns
        for i in range(len(rows)):
            row = rows[i].row
            # left wall
            col_l = rows[i].left_col
            col_r = rows[i].right_col
            if col_l > 0:
                tw = TrailWall(is_vertical=True, x=col_l, y=row)
                inner_border.append(tw)
            if col_r+1 < self.width:
                tw = TrailWall(is_vertical=True, x=col_r+1, y=row)
                inner_border.append(tw)
            start_col = col_l
            end_col = prev_left
            if prev_left < col_l:
                start_col, end_col = end_col, start_col
            for c in range(start_col, end_col):
                tw = TrailWall(is_vertical=False, x=row, y=c)
                inner_border.append(tw)
            start_col = col_r+1
            end_col = prev_right+1
            if prev_right < col_r:
                start_col, end_col = end_col, start_col
            for c in range(start_col, end_col):
                tw = TrailWall(is_vertical=False, x=row, y=c)
                inner_border.append(tw)
            prev_left = col_l
            prev_right = col_r
        # last row
        row = rows[-1].row
        if row < (self.height-1):
            for col in range(rows[-1].left_col, rows[-1].right_col+1):
                tw = TrailWall(is_vertical=False, x=row+1, y=col)
                inner_border.append(tw)
        return inner_border

    def get_entrance_cell_to_sub_maze(self, sm):
        rows = self.get_sub_maze_rows(sm)
        # first row
        row = rows[0].row
        for col in range(rows[0].left_col, rows[0].right_col+1):
            if self.h_lines[row][col].is_open():
                return 'down', (row, col)
        prev_left = rows[0].left_col
        prev_right = rows[0].right_col
        # left and right columns
        for i in range(len(rows)):
            row = rows[i].row
            # left wall
            col_l = rows[i].left_col
            col_r = rows[i].right_col
            if self.v_lines[col_l][row].is_open():
                return 'right', (row, col_l)
            if col_l < prev_left:
                for c in range(col_l, prev_left):
                    if self.h_lines[row][c].is_open():
                        return 'down', (row, c)
            if col_l > prev_left:
                for c in range(prev_left, col_l):
                    if self.h_lines[row][c].is_open():
                        return 'up', (row-1, c)
            prev_left = col_l
            if self.v_lines[col_r+1][row].is_open():
                return 'left', (row, col_r)
            if col_r < prev_right:
                for c in range(col_r+1, prev_right+1):
                    if self.h_lines[row][c].is_open():
                        return 'up', (row-1, c)
            if col_r > prev_right:
                for c in range(prev_right+1, col_r+1):
                    if self.h_lines[row][c].is_open():
                        return 'down', (row, c)
            prev_right = col_r
        # last row
        row = rows[-1].row
        for col in range(rows[-1].left_col, rows[-1].right_col+1):
            if self.h_lines[row+1][col].is_open():
                return 'up', (row, col)
        return None, None

    def open_trail_wall(self, tw):
        if tw.is_vertical:
            self.v_lines[tw.x][tw.y].clear_walls()
        else:
            self.h_lines[tw.x][tw.y].clear_walls()

    def get_sub_maze_trail_walls(self, sm):
        sm_tw = []
        for i in range(0, len(sm)):
            row = sm[i][0]
            col = sm[i][1]
            # upper wall
            tw = TrailWall(False, row, col)
            if self.is_line_part_of_trail_wall(tw):
                sm_tw.append(tw)
            # left wall
            tw = TrailWall(True, col, row)
            if self.is_line_part_of_trail_wall(tw):
                sm_tw.append(tw)
            # right wall
            tw = TrailWall(True, col+1, row)
            if self.is_line_part_of_trail_wall(tw):
                sm_tw.append(tw)
            # lower wall
            tw = TrailWall(False, row + 1, col)
            if self.is_line_part_of_trail_wall(tw):
                sm_tw.append(tw)
            i += 1
        return sm_tw
    
    def get_sub_maze_rows(self, sm):
        rows = []
        i = 0
        while i < len(sm):
            pr = SubMazeRow()
            pr.row = sm[i][0]
            pr.left_col = sm[i][1]
            i = self.get_sm_index_of_next_row(sm, i)
            pr.right_col = sm[i-1][1]
            rows.append(pr)
        return rows
    
    def get_sm_index_of_next_row(self, sm, i):
        current_row = sm[i][0]
        while i < len(sm):
            if sm[i][0] == current_row:
                i += 1
            else:
                return i
        return i
    
    def get_empty_sub_maze(self, start_row, start_col):
        sm_cells = []
        row = start_row
        min_col = start_col
        max_col = self.get_nearest_wall(row, start_col, 'right') - 1
        while row < self.height:
            end_col = self.get_nearest_wall(row, start_col, 'right') - 1
            for col in range(start_col, end_col + 1):
                sm_cells.append((row, col))
            if end_col > max_col:
                self.set_ceiling(row, max_col+1, end_col)
                max_col = end_col
            elif end_col < max_col:
                self.set_floor(row-1, end_col+1, max_col)
                max_col = end_col
            start_col = self.get_first_free_cell_under_row(row, start_col, end_col)
            if start_col is None:
                break
            if start_col < min_col:
                self.set_ceiling(row+1, start_col, min_col-1)
                min_col = start_col
            elif start_col > min_col:
                self.set_floor(row, min_col, start_col-1)
                min_col = start_col
            row += 1

        return sm_cells

    def set_ceiling(self, row, left_col, right_col):
        for col in range(left_col, right_col+1):
            self.h_lines[row][col].is_wall = True

    def set_floor(self, row, left_col, right_col):
        for col in range(left_col, right_col+1):
            self.h_lines[row+1][col].is_wall = True

    def get_first_free_cell_under_row(self, row, start_col, end_col):
        if self.is_floor_blocked(row, start_col, end_col+1):
            return None
        for col in range(end_col, start_col-1, -1):
            if self.h_lines[row+1][col].is_open():
                break
        return self.get_nearest_wall(row+1, col, 'left')

    def is_line_part_of_trail_wall(self, tw):
        if tw.is_vertical:
            if self.v_lines[tw.x][tw.y].is_left_trail_wall or self.v_lines[tw.x][tw.y].is_right_trail_wall:
                return True
        else:
            if self.h_lines[tw.x][tw.y].is_left_trail_wall or self.h_lines[tw.x][tw.y].is_right_trail_wall:
                return True
        return False

    def get_next_empty_cell_in_sub_maze(self, sm):
        for cell in sm:
            row = cell[0]
            col = cell[1]
            if self.cells[row][col].is_free:
                return row, col
        return None, None

    # return first empty row, col
    def get_next_empty_cell_in_maze(self, start_row, start_col):
        row = start_row
        col = start_col
        while row < self.height:
            while col < self.width:
                if self.cells[row][col].is_free:
                    return row, col
                col += 1
            col = 0
            row += 1
        return None, None

    def set_trail(self, first_cell=(0, 0), prev_dir='down'):
        trail = []
        cell = first_cell
        prev_direction = prev_dir
        i = random.randint(0, 1)
        if i:
            side = 'v'
        else:
            side = 'h'
        while cell is not None:
            trail.append(cell)
            self.cells[cell[0]][cell[1]].is_free = False
            side, next_cell = self.choose_next_cell(cell, side)
            if next_cell is not None:
                prev_direction, trail = self.add_trail_between_cells(prev_direction, cell, next_cell, trail)
            cell = next_cell
        return trail

    def clean_row_1_temp_line(self):
        for col in range(0, self.width):
            if not self.h_lines[1][col].is_left_trail_wall and not self.h_lines[1][col].is_right_trail_wall:
                self.h_lines[1][col].is_wall = False

    def set_end_cell(self, prev_direction):
        end_cell_up_wall = self.h_lines[self.height-1][self.end_col]
        end_cell_left_wall = self.v_lines[self.end_col][self.height-1]
        end_cell_right_wall = self.v_lines[self.end_col+1][self.height-1]
        if prev_direction == 'down':
            end_cell_left_wall.is_right_trail_wall = True
            end_cell_right_wall.is_left_trail_wall = True
        elif prev_direction == 'left':
            end_cell_up_wall.is_right_trail_wall = True
            end_cell_left_wall.is_right_trail_wall = True
        # right
        else:
            end_cell_up_wall.is_left_trail_wall = True
            end_cell_right_wall.is_left_trail_wall = True
        self.insert_trail_lines(self.height-1, self.end_col, prev_direction, 'down')

    def add_trail_between_cells(self, prev_direction, cell1, cell2, trail):
        row1 = cell1[0]
        col1 = cell1[1]
        row2 = cell2[0]
        col2 = cell2[1]

        cell1_up_wall = self.h_lines[row1][col1]
        cell1_down_wall = self.h_lines[row1+1][col1]
        cell1_left_wall = self.v_lines[col1][row1]
        cell1_right_wall = self.v_lines[col1+1][row1]

        # down
        if row1 < row2:
            direction = 'down'
            if prev_direction == 'left':
                cell1_up_wall.is_right_trail_wall = True
                cell1_left_wall.is_right_trail_wall = True
            elif prev_direction == 'right':
                cell1_up_wall.is_left_trail_wall = True
                cell1_right_wall.is_left_trail_wall = True
            elif prev_direction == 'down':
                cell1_left_wall.is_right_trail_wall = True
                cell1_right_wall.is_left_trail_wall = True
#            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for row in range(row1+1, row2):
                self.v_lines[col1][row].is_right_trail_wall = True
                self.v_lines[col1 + 1][row].is_left_trail_wall = True
#                self.insert_trail_lines(row, col1, direction, direction)
                trail.append((row, col1))
                self.cells[row][col1].is_free = False
        # up
        elif row2 < row1:
            direction = 'up'
            if prev_direction == 'left':
                cell1_down_wall.is_left_trail_wall = True
                cell1_left_wall.is_left_trail_wall = True
            elif prev_direction == 'right':
                cell1_down_wall.is_right_trail_wall = True
                cell1_right_wall.is_right_trail_wall = True
            elif prev_direction == 'up':
                cell1_left_wall.is_left_trail_wall = True
                cell1_right_wall.is_right_trail_wall = True
#            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for row in range(row1-1, row2, -1):
                self.v_lines[col1][row].is_left_trail_wall = True
                self.v_lines[col1 + 1][row].is_right_trail_wall = True
#                self.insert_trail_lines(row, col1, direction, direction)
                trail.append((row, col1))
                self.cells[row][col1].is_free = False
        # right
        elif col1 < col2:
            direction = 'right'
            if prev_direction == 'up':
                cell1_left_wall.is_left_trail_wall = True
                cell1_up_wall.is_left_trail_wall = True
            elif prev_direction == 'down':
                cell1_down_wall.is_right_trail_wall = True
                cell1_left_wall.is_right_trail_wall = True
            elif prev_direction == 'right':
                cell1_down_wall.is_right_trail_wall = True
                cell1_up_wall.is_left_trail_wall = True
#            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for col in range(col1+1, col2):
                self.h_lines[row1][col].is_left_trail_wall = True
                self.h_lines[row1+1][col].is_right_trail_wall = True
#                self.insert_trail_lines(row1, col, direction, direction)
                trail.append((row1, col))
                self.cells[row1][col].is_free = False
        # left
        else:
            direction = 'left'
            if prev_direction == 'up':
                cell1_up_wall.is_right_trail_wall = True
                cell1_right_wall.is_right_trail_wall = True
            elif prev_direction == 'down':
                cell1_down_wall.is_left_trail_wall = True
                cell1_right_wall.is_left_trail_wall = True
            elif prev_direction == 'left':
                cell1_down_wall.is_left_trail_wall = True
                cell1_up_wall.is_right_trail_wall = True
#            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for col in range(col1-1, col2, -1):
                self.h_lines[row1][col].is_right_trail_wall = True
                self.h_lines[row1+1][col].is_left_trail_wall = True
#                self.insert_trail_lines(row1, col, direction, direction)
                trail.append((row1, col))
                self.cells[row1][col].is_free = False

        return direction, trail
    '''
    def insert_trail_lines(self, row, col, prev_direction, direction):
        if prev_direction == 'down':
            if direction == 'left':
                tw = TrailWall(is_vertical=True, x=col+1, y=row)
                self.left_trail_wall.append(tw)
                tw = TrailWall(is_vertical=False, x=row+1, y=col)
                self.left_trail_wall.append(tw)
            elif direction == 'right':
                tw = TrailWall(is_vertical=True, x=col, y=row)
                self.right_trail_wall.append(tw)
                tw = TrailWall(is_vertical=False, x=row + 1, y=col)
                self.right_trail_wall.append(tw)
            elif direction == 'down':
                tw = TrailWall(is_vertical=True, x=col, y=row)
                self.right_trail_wall.append(tw)
                tw = TrailWall(is_vertical=True, x=col+1, y=row)
                self.left_trail_wall.append(tw)

        elif prev_direction == 'up':
            if direction == 'left':
                tw = TrailWall(is_vertical=True, x=col+1, y=row)
                self.right_trail_wall.append(tw)
                tw = TrailWall(is_vertical=False, x=row, y=col)
                self.right_trail_wall.append(tw)
            elif direction == 'right':
                tw = TrailWall(is_vertical=True, x=col, y=row)
                self.left_trail_wall.append(tw)
                tw = TrailWall(is_vertical=False, x=row, y=col)
                self.left_trail_wall.append(tw)
            elif direction == 'up':
                tw = TrailWall(is_vertical=True, x=col, y=row)
                self.left_trail_wall.append(tw)
                tw = TrailWall(is_vertical=True, x=col+1, y=row)
                self.right_trail_wall.append(tw)
        
        elif prev_direction == 'right':
            if direction == 'up':
                tw = TrailWall(is_vertical=False, x=row+1, y=col)
                self.right_trail_wall.append(tw)
                tw = TrailWall(is_vertical=True, x=col+1, y=row)
                self.right_trail_wall.append(tw)
            elif direction == 'down':
                tw = TrailWall(is_vertical=False, x=row, y=col)
                self.left_trail_wall.append(tw)
                tw = TrailWall(is_vertical=True, x=col+1, y=row)
                self.left_trail_wall.append(tw)
            elif direction == 'right':
                tw = TrailWall(is_vertical=False, x=row+1, y=col)
                self.right_trail_wall.append(tw)
                tw = TrailWall(is_vertical=False, x=row, y=col)
                self.left_trail_wall.append(tw)

        # prev_direction = left
        else:
            if direction == 'up':
                tw = TrailWall(is_vertical=False, x=row+1, y=col)
                self.left_trail_wall.append(tw)
                tw = TrailWall(is_vertical=True, x=col, y=row)
                self.left_trail_wall.append(tw)
            elif direction == 'down':
                tw = TrailWall(is_vertical=False, x=row, y=col)
                self.right_trail_wall.append(tw)
                tw = TrailWall(is_vertical=True, x=col, y=row)
                self.right_trail_wall.append(tw)
            if direction == 'left':
                tw = TrailWall(is_vertical=False, x=row+1, y=col)
                self.left_trail_wall.append(tw)
                tw = TrailWall(is_vertical=False, x=row, y=col)
                self.right_trail_wall.append(tw)
    '''
    def choose_next_cell(self, current_cell, side):
        row = current_cell[0]
        col = current_cell[1]
        next_row = row
        next_col = col
        return_side = None
        found_cell = False
        cell = self.cells[row][col]
        lim_left_wall = self.get_nearest_wall(row, col, 'left')
        if lim_left_wall == col:
            cell.can_go_left = False
        elif col > 0:
            if not self.cells[row][col-1].is_free:
                cell.can_go_left = False
        lim_right_wall = self.get_nearest_wall(row, col, 'right')
        if lim_right_wall == col+1:
            cell.can_go_right = False
        elif col < self.width-1:
            if not self.cells[row][col+1].is_free:
                cell.can_go_right = False
        lim_up_wall = self.get_nearest_wall(row, col, 'up')
        if lim_up_wall == row:
            cell.can_go_up = False
        elif row > 0:
            if not self.cells[row-1][col].is_free:
                cell.can_go_up = False
        lim_down_wall = self.get_nearest_wall(row, col, 'down')
        if lim_down_wall == row+1:
            cell.can_go_down = False
        elif row < self.height-1:
            if not self.cells[row+1][col].is_free:
                cell.can_go_down = False

        if side == 'h' and not cell.can_go_left and not cell.can_go_right:
            side = 'v'
        elif side == 'v' and not cell.can_go_up and not cell.can_go_down:
            side = 'h'

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

        if side == 'h':
            if cell.can_go_left:
                if col - lim_left_wall > gv.MAX_STRAIT_LINE:
                    lim_left_wall = col - gv.MAX_STRAIT_LINE
                next_col = random.randint(lim_left_wall, col-1)
                return_side = 'v'
                found_cell = True
            elif cell.can_go_right:
                if (lim_right_wall-1) - col > gv.MAX_STRAIT_LINE:
                    lim_right_wall = col + gv.MAX_STRAIT_LINE + 1
                next_col = random.randint(col+1, lim_right_wall-1)
                return_side = 'v'
                found_cell = True
        if not found_cell:
            if cell.can_go_up:
                if (row-1) - lim_up_wall > gv.MAX_STRAIT_LINE:
                    lim_up_wall = (row - 1) - gv.MAX_STRAIT_LINE
                next_row = random.randint(lim_up_wall, row-1)
                return_side = 'h'
                found_cell = True
            elif cell.can_go_down:
                if (lim_down_wall-1) - (row+1) > gv.MAX_STRAIT_LINE:
                    lim_down_wall = row + gv.MAX_STRAIT_LINE
                next_row = random.randint(row+1, lim_down_wall-1)
                return_side = 'h'
                found_cell = True
        # no open side
        if not found_cell:
            return None, None
        
        return return_side, (next_row, next_col)

    def trail_wall_is_edge_line(self, tw):
        if tw.x == 0:
            return True
        if tw.is_vertical:
            if tw.x == self.width:
                return True
        else:
            if tw.x == self.height:
                return True
        return False

    def clean_left_and_right_walls(self):
        # remove edge lines from trail wall lists
        i = 0
        while i < len(self.left_trail_wall):
            line = self.left_trail_wall[i]
            if self.trail_wall_is_edge_line(line):
                self.left_trail_wall.pop(i)
            else:
                i += 1
        i = 0
        while i < len(self.right_trail_wall):
            line = self.right_trail_wall[i]
            if self.trail_wall_is_edge_line(line):
                self.right_trail_wall.pop(i)
            else:
                i += 1
        # define edge lines as not part of the trail walls
        for col in range(0, self.width):
            self.h_lines[0][col].is_left_trail_wall = False
            self.h_lines[0][col].is_right_trail_wall = False
            self.h_lines[self.height][col].is_left_trail_wall = False
            self.h_lines[self.height][col].is_right_trail_wall = False
        for row in range(0, self.height):
            self.v_lines[0][row].is_left_trail_wall = False
            self.v_lines[0][row].is_right_trail_wall = False
            self.v_lines[self.width][row].is_left_trail_wall = False
            self.v_lines[self.width][row].is_right_trail_wall = False

    def get_nearest_wall(self, row, col, side):
        if side == 'left' or side == 'right':
            wall = col
            i = -1
            if side == 'right':
                wall += 1
                i = 1
            while self.v_lines[wall][row].is_open():
                wall += i
        else:
            if side == 'up':
                wall = row
                while self.h_lines[wall][col].is_open() and wall > 0:
                    wall -= 1
            # side = down
            else:
                wall = row+1
                while self.h_lines[wall][col].is_open() and wall < self.height:
                    wall += 1

        return wall

    def is_floor_blocked(self, row, left_wall, right_wall):
        do_blocked = True
        for i in range(left_wall, right_wall):
            if self.h_lines[row+1][i].is_open():
                do_blocked = False
                break
        return do_blocked

    def reset_state(self):
        # set all horizontal lines to default = open, no part of the trail
        h_lines = []
        for row in range(self.height+1):
            current_row = []
            for col in range(self.width):
                l = Line()
                current_row.append(l)
            h_lines.append(current_row)

        # set all vertical lines to default = open no part of the trail
        v_lines = []
        for col in range(self.width+1):
            current_col = []
            for row in range(self.height):
                l = Line()
                current_col.append(l)
            v_lines.append(current_col)

        cells = []
        for row in range(self.height):
            current_row = []
            for col in range(self.width):
                current_row.append(Cell())
            cells.append(current_row)

        # set first and last row
        for col in range(self.width):
            cells[0][col].can_go_up = False
            cells[self.height - 1][col].can_go_down = False
            h_lines[0][col].is_wall = True
            h_lines[self.height][col].is_wall = True
        h_lines[0][self.start_col].is_wall = False

        # set first and last columns
        for row in range(self.height):
            cells[row][0].can_go_left = False
            v_lines[0][row].is_wall = True
            cells[row][self.width-1].can_go_right = False
            v_lines[self.width][row].is_wall = True

        return h_lines, v_lines, cells

    def show_maze(self, show_marked_cells=False, mark_trail_lines=True, pause=0):
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
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)
        x += gv.LINE_SIZE
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)

        for line in self.h_lines:
            for col in range(len(line)):
                y = y_00 + gv.LINE_SIZE*row
                start_x = x_00 + gv.LINE_SIZE*col
                end_x = start_x + gv.LINE_SIZE
                if not line[col].is_open():
                    board.create_line(start_x, y, end_x, y, fill=self.get_line_color(line[col], mark_trail_lines))
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
                    board.create_line(x, start_y, x, end_y, fill=self.get_line_color(line[row], mark_trail_lines))
                    if pause:
                        window.update()
            col += 1

        # exit
        x = x_00 + gv.LINE_SIZE * self.end_col
        start_y = y_00 + self.height * gv.LINE_SIZE
        end_y = start_y + gv.LINE_SIZE/2
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)
        x += gv.LINE_SIZE
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)
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

    def get_line_color(self, line, mark_trail_lines=False):
        color = gv.NO_TRAIL_LINE_COLOR
        if not mark_trail_lines:
            return color
        if line.is_left_trail_wall and line.is_right_trail_wall:
            color = gv.BOTH_SIDES_TRAIL_LINE_COLOR
        elif line.is_left_trail_wall:
            color = gv.LEFT_TRAIL_LINE_COLOR
        elif line.is_right_trail_wall:
            color = gv.RIGHT_TRAIL_LINE_COLOR
        return color

    #debug
    def print_cells(self):
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

    #debug
    def print_trail(self):
        t = []
        for cell in self.trail:
            t.append(cell)
        print(f'trail: {t}')

    #debug
    def print_trail_walls(self):
        l = []
        for line in self.left_trail_wall:
            d = 'h'
            if line.is_vertical:
                d = 'v'
            l.append(f'{d}({line.x}, {line.y}) ')
        r = []
        for line in self.right_trail_wall:
            d = 'h'
            if line.is_vertical:
                d = 'v'
            r.append(f'{d}({line.x}, {line.y}) ')
        print(f'left trail: {l}')
        print(f'right trail: {r}')


