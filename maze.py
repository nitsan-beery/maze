import global_vars as gv
import random
import tkinter as tk


def my_randint(a, b):
    return random.randint(a, b)


class TrailWall:
    def __init__(self, is_vertical=False, x=0, y=0):
        self.is_vertical = is_vertical
        self.x = x
        self.y = y


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
    def __init__(self, can_go_up=False, can_go_down=False, can_go_left=False, can_go_right=False, is_free=True):
        self.can_go_up = can_go_up
        self.can_go_down = can_go_down
        self.can_go_left = can_go_left
        self.can_go_right = can_go_right
        self.is_free = is_free


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
        if not self.width % 2:
            self.width += 1
        self.height = height
        self.start_col = my_randint(0, self.width-1)
        self.end_col = my_randint(0, self.width-1)
        self.h_lines, self.v_lines, self.cells = self.reset_state()
        self.left_trail_wall = []
        self.right_trail_wall = []
        self.trail = []
        self.decoy_polygons = []

    def set_empty_polygons(self):
        row = 0
        col = 0
        while True:
            row, col = self.get_next_empty_cell(row, col)
            if row is None:
                break
            polygon_cells, pol_trail_wall = self.get_empty_polygon(row, col)
            i = my_randint(0, len(pol_trail_wall)-1)
            line = pol_trail_wall[i]
            if line.is_vertical:
                self.v_lines[line.x][line.y].clear_walls()
            else:
                self.h_lines[line.x][line.y].clear_walls()
            self.decoy_polygons.append((polygon_cells, line))

    def get_empty_polygon(self, start_row, start_col):
        pol_cells = []
        pol_tw = []
        row = start_row
        min_col = start_col
        max_col = self.get_nearest_wall(row, start_col, 'right') - 1
        while row < self.height:
            end_col = self.get_nearest_wall(row, start_col, 'right') - 1
            for col in range(start_col, end_col + 1):
                pol_cells, pol_tw = self.add_cells_and_tw_to_pol(pol_cells, pol_tw, row, col)
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

        return pol_cells, pol_tw

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

    def add_cells_and_tw_to_pol(self, pol_cells, pol_tw, row, col):
        pol_cells.append((row, col))
        self.cells[row][col].is_free = False
        # upper wall
        tw = TrailWall(False, row, col)
        if self.is_line_part_of_trail_wall(tw):
            pol_tw.append(tw)
        # lower wall
        tw = TrailWall(False, row+1, col)
        if self.is_line_part_of_trail_wall(tw):
            pol_tw.append(tw)
        # left wall
        tw = TrailWall(True, col, row)
        if self.is_line_part_of_trail_wall(tw):
            pol_tw.append(tw)
        # right wall
        tw = TrailWall(True, col+1, row)
        if self.is_line_part_of_trail_wall(tw):
            pol_tw.append(tw)
        return pol_cells, pol_tw

    def is_line_part_of_trail_wall(self, tw):
        if tw.is_vertical:
            if self.v_lines[tw.x][tw.y].is_left_trail_wall or self.v_lines[tw.x][tw.y].is_right_trail_wall:
                return True
        else:
            if self.h_lines[tw.x][tw.y].is_left_trail_wall or self.h_lines[tw.x][tw.y].is_right_trail_wall:
                return True
        return False

    # return first empty row, col
    def get_next_empty_cell(self, start_row, start_col):
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

    def set_trail(self):
        cell = (0, self.start_col)
        prev_direction = 'down'
        i = my_randint(0, 1)
        if i:
            side = 'v'
        else:
            side = 'h'
        while cell != (self.height-1, self.end_col):
            self.trail.append(cell)
            self.cells[cell[0]][cell[1]].is_free = False
            side, next_cell = self.choose_next_cell(cell, side)
            # debug
            if gv.DEBUG_MODE:
                print(f'cell: {cell}   next cell: {next_cell}   side: {side}')
            prev_direction = self.add_trail_between_cells(prev_direction, cell, next_cell)
            # debug
            if gv.DEBUG_MODE:
                self.print_trail_walls()
                self.show_maze()
                pass
            cell = next_cell
        self.trail.append((self.height-1, self.end_col))
        self.cells[self.height-1][self.end_col].is_free = False
        # set walls for last cell
        self.set_end_cell(prev_direction)
        # define edge walls as not part of the trail walls
        self.clean_left_and_right_walls()
        self.clean_row_1_temp_line()

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

    def add_trail_between_cells(self, prev_direction, cell1, cell2):
        row1 = cell1[0]
        col1 = cell1[1]
        row2 = cell2[0]
        col2 = cell2[1]

        cell1_up_wall = self.h_lines[row1][col1]
        cell1_down_wall = self.h_lines[row1+1][col1]
        cell1_left_wall = self.v_lines[col1][row1]
        cell1_right_wall = self.v_lines[col1+1][row1]

        direction = None

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
            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for row in range(row1+1, row2):
                self.v_lines[col1][row].is_right_trail_wall = True
                self.v_lines[col1 + 1][row].is_left_trail_wall = True
                self.insert_trail_lines(row, col1, direction, direction)
                self.trail.append((row, col1))
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
            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for row in range(row1-1, row2, -1):
                self.v_lines[col1][row].is_left_trail_wall = True
                self.v_lines[col1 + 1][row].is_right_trail_wall = True
                self.insert_trail_lines(row, col1, direction, direction)
                self.trail.append((row, col1))
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
            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for col in range(col1+1, col2):
                self.h_lines[row1][col].is_left_trail_wall = True
                self.h_lines[row1+1][col].is_right_trail_wall = True
                self.insert_trail_lines(row1, col, direction, direction)
                self.trail.append((row1, col))
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
            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for col in range(col1-1, col2, -1):
                self.h_lines[row1][col].is_right_trail_wall = True
                self.h_lines[row1+1][col].is_left_trail_wall = True
                self.insert_trail_lines(row1, col, direction, direction)
                self.trail.append((row1, col))
                self.cells[row1][col].is_free = False

        return direction
    
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
    
    def choose_next_cell(self, current_cell, side):
        row = current_cell[0]
        col = current_cell[1]
        next_row = row
        next_col = col
        return_side = None
        found_cell = False
        cell = self.cells[row][col]
        lim_left_wall = self.get_nearest_wall(row, col, 'left')
        if row == self.height - 1:
            if lim_left_wall < self.end_col:
                lim_left_wall = self.end_col
        if lim_left_wall == col:
            cell.can_go_left = False
        lim_right_wall = self.get_nearest_wall(row, col, 'right')
        if row == self.height - 1:
            if lim_right_wall > self.end_col + 1:
                lim_right_wall = self.end_col + 1
        if lim_right_wall == col+1:
            cell.can_go_right = False
        lim_up_wall = self.get_nearest_wall(row, col, 'up')
        if lim_up_wall == row:
            cell.can_go_up = False
        lim_down_wall = self.get_nearest_wall(row, col, 'down')
        if lim_down_wall == row+1:
            cell.can_go_down = False

        if side == 'h' and not cell.can_go_left and not cell.can_go_right:
            side = 'v'
        elif side == 'v' and not cell.can_go_up and not cell.can_go_down:
            side = 'h'

        if side == 'h':
            if cell.can_go_left:
                next_col = my_randint(lim_left_wall, col-1)
                return_side = 'v'
                found_cell = True
            elif cell.can_go_right:
                next_col = my_randint(col+1, lim_right_wall-1)
                return_side = 'v'
                found_cell = True
        if not found_cell:
            if cell.can_go_up:
                next_row = my_randint(lim_up_wall, row-1)
                return_side = 'h'
                found_cell = True
            elif cell.can_go_down:
                next_row = my_randint(row+1, lim_down_wall-1)
                return_side = 'h'
                found_cell = True
        # no open side
        if not found_cell:
            # debug
            print(f'cant find next cell,   side: {side}')
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

    # old version - row by row
    def set_trail_old(self):
        upper_col = self.start_col
        for row in range(0, self.height-1):
            lower_col = self.get_next_col(row, upper_col)
            left_col, right_col = self.get_left_right(upper_col, lower_col)
            left_wall_lim = self.get_nearest_wall(row, left_col, 'left')
            right_wall_lim = self.get_nearest_wall(row, right_col, 'right')
            left_wall, right_wall = self.get_left_and_right_walls(left_wall_lim, right_wall_lim, left_col, right_col)
            self.v_lines[left_wall][row].is_wall = True
            self.v_lines[right_wall][row].is_wall = True
            open_part = OpenPart(left_wall, right_wall, upper_col, lower_col, True)
            self.insert_open_part(row, open_part)
            self.h_lines[row + 1][lower_col].is_wall = False
            # debug
            #print(f'row: {row}   left wall: {left_wall}   right wall: {right_wall}   upper col: {upper_col}   lower col: {lower_col}')
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
        self.h_lines[self.height][lower_col].is_wall = False

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

    def get_left_right(self, col_1, col_2):
        left_col = col_1
        right_col = col_2
        if left_col > right_col:
            left_col, right_col = right_col, left_col
        return left_col, right_col

    def is_floor_blocked(self, row, left_wall, right_wall):
        do_blocked = True
        for i in range(left_wall, right_wall):
            if self.h_lines[row+1][i].is_open():
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
                    self.v_lines[i + 1][row].is_wall = True
                if not self.v_lines[i + 1][row].is_open():
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
                    self.h_lines[row + 1][j].is_wall = False
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
        self.v_lines[j][row].is_wall = True

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
        self.v_lines[divider][row].is_wall = True
        left_hole = my_randint(left_hole_lim, divider-1)
        right_hole = my_randint(divider, right_hole_lim)
        self.h_lines[row+1][left_hole].is_wall = False
        self.h_lines[row+1][right_hole].is_wall = False
        
        left_wall_lim = part.left_wall
        right_wall_lim = part.right_wall

        if part.is_col_2_lower:
            if is_upper_col_on_the_right:
                left_wall_lim = part.col_2+1
            else:
                right_wall_lim = part.col_2

        left_wall, right_wall = self.get_left_and_right_walls(left_wall_lim, right_wall_lim, left_hole, right_hole)
        self.v_lines[left_wall][row+1].is_wall = True
        self.v_lines[right_wall][row+1].is_wall = True
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
        is_left_odd = my_randint(0, 1)
        if self.height % 2:
            is_row_before_last_left = is_left_odd
        else:
            is_row_before_last_left = not is_left_odd

        for row in range(self.height):
            current_row = []
            for col in range(self.width):
                c = Cell()
                if (row+is_left_odd)%2:
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
        for col in range(self.width):
            cells[0][col].can_go_up = False
            h_lines[0][col].is_wall = True
        h_lines[0][self.start_col].is_wall = False
        cells[0][self.start_col].is_free = False
        if is_left_odd:
            v_lines[self.start_col+1][0].is_wall = True
            for col in range(self.start_col+1, self.width-1):
                h_lines[1][col].is_wall = True
        else:
            v_lines[self.start_col][0].is_wall = True
            for col in range(1, self.start_col):
                h_lines[1][col].is_wall = True

        # set last row
        for col in range(self.end_col):
            cells[self.height-1][col].can_go_right = True
            cells[self.height-1][col].can_go_left = False
            cells[self.height - 1][col].can_go_down = False
            h_lines[self.height][col].is_wall = True
            if is_row_before_last_left:
                cells[self.height - 1][col].can_go_up = False
        for col in range(self.end_col+1, self.width):
            cells[self.height-1][col].can_go_right = False
            cells[self.height-1][col].can_go_left = True
            cells[self.height - 1][col].can_go_down = False
            h_lines[self.height][col].is_wall = True
            if not is_row_before_last_left:
                cells[self.height - 1][col].can_go_up = False
        cells[self.height-1][self.end_col].can_go_left = False
        cells[self.height-1][self.end_col].can_go_right = False
        cells[self.height-1][self.end_col].can_go_up = False

        # set first and last columns
        for row in range(self.height-1):
            cells[row][0].can_go_up = False
            cells[row][0].can_go_down = True
            cells[row][0].can_go_left = False
            v_lines[0][row].is_wall = True
            cells[row][self.width-1].can_go_up = False
            cells[row][self.width-1].can_go_down = True
            cells[row][self.width-1].can_go_right = False
            v_lines[self.width][row].is_wall = True
        cells[self.height-1][0].can_go_down = False
        cells[self.height-1][0].can_go_up = False
        cells[self.height-1][self.width-1].can_go_down = False
        cells[self.height-1][self.width-1].can_go_up = False
        v_lines[0][self.height-1].is_wall = True
        v_lines[self.width][self.height-1].is_wall = True

        return h_lines, v_lines, cells

    def show_maze(self):
        window = tk.Tk()
        window.title('Maze')
        width = gv.LINE_SIZE * (self.width+2)
        height = gv.LINE_SIZE * (self.height+2)
        frame_1 = tk.Frame(window)
        frame_1.pack(fill='both', side='top', expand=tk.YES)
        board = tk.Canvas(frame_1, width=width, height=height)
        board.pack(expand=tk.YES, fill=tk.BOTH)

        x_00 = gv.X_00
        y_00 = gv.Y_00
        row = 0
        for line in self.h_lines:
            for col in range(len(line)):
                y = y_00 + gv.LINE_SIZE*row
                start_x = x_00 + gv.LINE_SIZE*col
                end_x = start_x + gv.LINE_SIZE
                if not line[col].is_open():
                    board.create_line(start_x, y, end_x, y, fill=self.get_line_color(line[col]))
            row += 1
        col = 0
        for line in self.v_lines:
            for row in range(len(line)):
                x = x_00 + gv.LINE_SIZE*col
                start_y = y_00 + gv.LINE_SIZE * row
                end_y = start_y + gv.LINE_SIZE
                if not line[row].is_open():
                    board.create_line(x, start_y, x, end_y, fill=self.get_line_color(line[row]))
            col += 1
        window.update()
        window.mainloop()

    def get_line_color(self, line):
        color = gv.NO_TRAIL_LINE_COLOR
        if not gv.MARK_TRAIL:
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


