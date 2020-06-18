import global_vars as gv
import random
import tkinter as tk


def my_randint(a, b):
    return random.randint(a, b)
#    f = random.random()
#    return a+int(f*(b-a+1))


class PolRow:
    def __init__(self, row=0, left_col=0, right_col=0):
        self.row = row
        self.left_col = left_col
        self.right_col = right_col
    
    
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


class MazeInfo:
    def __init__(self):
        self.num_of_decoy_polygons = 0
        self.trail_length = 0


class Cell:
    def __init__(self, can_go_up=False, can_go_down=False, can_go_left=False, can_go_right=False, is_free=True, show_cell=False):
        self.can_go_up = can_go_up
        self.can_go_down = can_go_down
        self.can_go_left = can_go_left
        self.can_go_right = can_go_right
        self.is_free = is_free
        self.show_cell = show_cell


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
        self.info = MazeInfo()

    def set_maze(self):
        self.set_trail()
        self.set_decoy_polygons()
        #debug
        #self.show_maze()
        for pol in self.decoy_polygons:
            tw = self.get_polygon_trail_walls(pol)
            i = my_randint(0, len(tw)-1)
            self.open_trail_wall(tw[i])
        # debug
        print(f'{len(self.decoy_polygons)} decoy polygons')
        for pol in self.decoy_polygons:
            self.fill_decoy_polygon_with_trails(pol)
            # debug
            #print('after fill pol')
            #self.show_maze(True)
        self.info.num_of_decoy_polygons = len(self.decoy_polygons)
        self.info.trail_length = len(self.trail)

    def clean_polygon_cells(self, pol):
        for cell in pol:
            row = cell[0]
            col = cell[1]
            self.cells[row][col].is_free = True
            self.cells[row][col].can_go_up = True
            self.cells[row][col].can_go_down = True
            self.cells[row][col].can_go_left = True
            self.cells[row][col].can_go_right = True

    def fill_decoy_polygon_with_trails(self, pol):
        row = 1
        col = 1
        self.set_trail_in_polygon(pol)
        row, col = self.get_next_empty_cell_in_polygon(pol)
        while row is not None:
            new_pol = self.get_empty_polygon(row, col)
            tw = self.get_polygon_trail_walls(new_pol)
            i = my_randint(0, len(tw) - 1)
            self.open_trail_wall(tw[i])
            self.set_trail_in_polygon(new_pol)
            row, col = self.get_next_empty_cell_in_polygon(pol)

    def set_trail_in_polygon(self, pol):
        self.clean_polygon_cells(pol)
        entry_side, cell = self.get_entrance_cell_to_decoy_polygon(pol)
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
        trail = self.set_trail(is_main_trail=False, first_cell=cell, prev_dir=entry_side)
        for cell in trail:
            row = cell[0]
            col = cell[1]
            self.cells[row][col].is_free = False

    def split_polygon(self, pol):
        rows = self.get_pol_rows(pol)
        if len(rows) < gv.MIN_ROWS_TO_SPLIT_POLYGON:
            return None, None
        split_cell = len(pol)/2-(len(pol)/len(rows))
        mid_row = 0
        counter = 0
        while counter < split_cell and mid_row < len(rows)-1:
            counter += rows[mid_row].right_col-rows[mid_row].left_col+1
            mid_row += 1
        #debug
        #print(f'pol size: {len(pol)}   rows: {len(rows)}    counter: {counter}   mid row: {mid_row}')
        self.set_ceiling(rows[mid_row].row, rows[mid_row].left_col, rows[mid_row].right_col)
        pol1 = []
        pol2 = []
        pol2_start_cell = 0
        for n in range(0, mid_row):
            pol2_start_cell += (rows[n].right_col - rows[n].left_col + 1)
        for i in range(0, pol2_start_cell):
            pol1.append(pol[i])
        for i in range(pol2_start_cell, len(pol)):
            pol2.append(pol[i])
        return pol1, pol2

    def set_decoy_polygons(self):
        row = 0
        col = 0
        while True:
            row, col = self.get_next_empty_cell_in_maze(row, col)
            if row is None:
                break
            polygon_cells = self.get_empty_polygon(row, col)
            self.decoy_polygons.append(polygon_cells)
        maze_size = self.height * self.width
        i = len(self.decoy_polygons)-1
        while i >= 0:
            pol = self.decoy_polygons[i]
            if len(pol) > maze_size * gv.MAX_POLYGON_PERCENTAGE_AREA:
                pol1, pol2 = self.split_polygon(pol)
                if pol1 is not None:
                    self.decoy_polygons[i] = pol1
                    self.decoy_polygons.insert(i+1, pol2)
            i -= 1

    def get_entrance_cell_to_decoy_polygon(self, pol):
        rows = self.get_pol_rows(pol)
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

    def get_polygon_trail_walls(self, pol):
        pol_tw = []
        for i in range(0, len(pol)):
            row = pol[i][0]
            col = pol[i][1]
            # upper wall
            tw = TrailWall(False, row, col)
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
            # lower wall
            tw = TrailWall(False, row + 1, col)
            if self.is_line_part_of_trail_wall(tw):
                pol_tw.append(tw)
            i += 1
        return pol_tw
    
    def get_pol_rows(self, pol):
        rows = []
        i = 0
        while i < len(pol):
            pr = PolRow()
            pr.row = pol[i][0]
            pr.left_col = pol[i][1]
            i = self.get_pol_index_of_next_row(pol, i)
            pr.right_col = pol[i-1][1]
            rows.append(pr)
        return rows
    
    def get_pol_index_of_next_row(self, pol, i):
        current_row = pol[i][0]
        while i < len(pol):
            if pol[i][0] == current_row:
                i += 1
            else:
                return i
        return i
    
    def get_empty_polygon(self, start_row, start_col):
        pol_cells = []
        row = start_row
        min_col = start_col
        max_col = self.get_nearest_wall(row, start_col, 'right') - 1
        while row < self.height:
            end_col = self.get_nearest_wall(row, start_col, 'right') - 1
            for col in range(start_col, end_col + 1):
                pol_cells = self.add_cells_to_pol(pol_cells, row, col)
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

        return pol_cells

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

    def add_cells_to_pol(self, pol_cells, row, col):
        pol_cells.append((row, col))
        self.cells[row][col].is_free = False
        return pol_cells

    def is_line_part_of_trail_wall(self, tw):
        if tw.is_vertical:
            if self.v_lines[tw.x][tw.y].is_left_trail_wall or self.v_lines[tw.x][tw.y].is_right_trail_wall:
                return True
        else:
            if self.h_lines[tw.x][tw.y].is_left_trail_wall or self.h_lines[tw.x][tw.y].is_right_trail_wall:
                return True
        return False

    def get_next_empty_cell_in_polygon(self, pol):
        for cell in pol:
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

    def set_trail(self, is_main_trail=True, first_cell=(0, 0), prev_dir='down'):
        trail = []
        last_cell = (self.height - 1, self.end_col)
        if is_main_trail:
            cell = (0, self.start_col)
        else:
            cell = first_cell
        prev_direction = prev_dir
        i = my_randint(0, 1)
        if i:
            side = 'v'
        else:
            side = 'h'
        while cell != last_cell:
            trail.append(cell)
            self.cells[cell[0]][cell[1]].is_free = False
            side, next_cell = self.choose_next_cell(cell, side, is_main_trail)
            if next_cell is None:
                break
            # debug
            if gv.DEBUG_MODE:
                print(f'cell: {cell}   next cell: {next_cell}   side: {side}')
            prev_direction, trail = self.add_trail_between_cells(prev_direction, cell, next_cell, trail)
            cell = next_cell
            #debug
#        if not is_main_trail:
#            for cell in trail:
#                self.cells[cell[0]][cell[1]].show_cell = True
            #self.show_maze(True)
        if is_main_trail:
            self.trail = trail
            self.trail.append((self.height-1, self.end_col))
            self.cells[self.height-1][self.end_col].is_free = False
            # set walls for last cell
            self.set_end_cell(prev_direction)
            # define edge walls as not part of the trail walls
            self.clean_left_and_right_walls()
            self.clean_row_1_temp_line()
            for cell in self.trail:
                self.cells[cell[0]][cell[1]].show_cell = True
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
            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for row in range(row1-1, row2, -1):
                self.v_lines[col1][row].is_left_trail_wall = True
                self.v_lines[col1 + 1][row].is_right_trail_wall = True
                self.insert_trail_lines(row, col1, direction, direction)
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
            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for col in range(col1+1, col2):
                self.h_lines[row1][col].is_left_trail_wall = True
                self.h_lines[row1+1][col].is_right_trail_wall = True
                self.insert_trail_lines(row1, col, direction, direction)
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
            self.insert_trail_lines(row1, col1, prev_direction, direction)
            for col in range(col1-1, col2, -1):
                self.h_lines[row1][col].is_right_trail_wall = True
                self.h_lines[row1+1][col].is_left_trail_wall = True
                self.insert_trail_lines(row1, col, direction, direction)
                trail.append((row1, col))
                self.cells[row1][col].is_free = False

        return direction, trail
    
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
    
    def choose_next_cell(self, current_cell, side, is_main_trail=True):
        row = current_cell[0]
        col = current_cell[1]
        next_row = row
        next_col = col
        return_side = None
        found_cell = False
        cell = self.cells[row][col]
        lim_left_wall = self.get_nearest_wall(row, col, 'left')
        if row == self.height - 1 and is_main_trail:
            if lim_left_wall < self.end_col:
                lim_left_wall = self.end_col
        if lim_left_wall == col:
            cell.can_go_left = False
        elif col > 0:
            if not self.cells[row][col-1].is_free:
                cell.can_go_left = False
        lim_right_wall = self.get_nearest_wall(row, col, 'right')
        if row == self.height - 1 and is_main_trail:
            if lim_right_wall > self.end_col + 1:
                lim_right_wall = self.end_col + 1
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

        # in decoy polygon choose randomly
        if not is_main_trail:
            if cell.can_go_right and cell.can_go_left:
                i = my_randint(0, 1)
                if i:
                    cell.can_go_left = False
                else:
                    cell.can_go_right = False
            if cell.can_go_up and cell.can_go_down:
                i = my_randint(0, 1)
                if i:
                    cell.can_go_down = False
                else:
                    cell.can_go_up = False

        if side == 'h':
            if cell.can_go_left:
                if col - lim_left_wall > gv.MAX_STRAIT_LINE:
                    lim_left_wall = col - gv.MAX_STRAIT_LINE
                #debug
                #print(f'row: {row}   lim_left_wall: {lim_left_wall}   col: {col}')
                next_col = my_randint(lim_left_wall, col-1)
                return_side = 'v'
                found_cell = True
            elif cell.can_go_right:
                if (lim_right_wall-1) - col > gv.MAX_STRAIT_LINE:
                    lim_right_wall = col + gv.MAX_STRAIT_LINE + 1
                #debug
                #print(f'row: {row}   col: {col}   lim_right_wall: {lim_right_wall}')
                next_col = my_randint(col+1, lim_right_wall-1)
                return_side = 'v'
                found_cell = True
        if not found_cell:
            if cell.can_go_up:
                if (row-1) - lim_up_wall > gv.MAX_STRAIT_LINE:
                    lim_up_wall = (row - 1) - gv.MAX_STRAIT_LINE
                next_row = my_randint(lim_up_wall, row-1)
                return_side = 'h'
                found_cell = True
            elif cell.can_go_down:
                if (lim_down_wall-1) - (row+1) > gv.MAX_STRAIT_LINE:
                    lim_down_wall = row + gv.MAX_STRAIT_LINE
                next_row = my_randint(row+1, lim_down_wall-1)
                return_side = 'h'
                found_cell = True
        # no open side
        if not found_cell:
            # debug
            #print(f'cant find next cell,   side: {side}')
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

    def show_maze(self, show_cells=False, mark_trail=False):
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
                    board.create_line(start_x, y, end_x, y, fill=self.get_line_color(line[col], mark_trail))
            row += 1
        col = 0
        for line in self.v_lines:
            for row in range(len(line)):
                x = x_00 + gv.LINE_SIZE*col
                start_y = y_00 + gv.LINE_SIZE * row
                end_y = start_y + gv.LINE_SIZE
                if not line[row].is_open():
                    board.create_line(x, start_y, x, end_y, fill=self.get_line_color(line[row], mark_trail))
            col += 1

        # entrance and exit
        x = x_00 + gv.LINE_SIZE * self.start_col
        start_y = y_00
        end_y = start_y - gv.LINE_SIZE/2
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)
        x += gv.LINE_SIZE
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)
        x = x_00 + gv.LINE_SIZE * self.end_col
        start_y = y_00 + self.height * gv.LINE_SIZE
        end_y = start_y + gv.LINE_SIZE/2
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)
        x += gv.LINE_SIZE
        board.create_line(x, start_y, x, end_y, fill=gv.NO_TRAIL_LINE_COLOR)

        if show_cells:
            x_00 += gv.LINE_SIZE/4
            y_00 += gv.LINE_SIZE/4
            for row in range(self.height):
                for col in range(self.width):
                    if self.cells[row][col].show_cell:
                        hx_left = x_00 + gv.LINE_SIZE*col
                        hx_right = hx_left + gv.LINE_SIZE/2
                        hy = y_00 + gv.LINE_SIZE*row + gv.LINE_SIZE/4
                        vx = hx_left + gv.LINE_SIZE/4
                        vy_up = y_00 + gv.LINE_SIZE*row
                        vy_down = vy_up + gv.LINE_SIZE/2
                        board.create_line(hx_left, hy, hx_right, hy, fill=gv.SHOW_CELL_COLOR)
                        board.create_line(vx, vy_up, vx, vy_down, fill=gv.SHOW_CELL_COLOR)

        window.update()
        window.mainloop()

    def get_line_color(self, line, mark_trail=False):
        color = gv.NO_TRAIL_LINE_COLOR
        if not mark_trail:
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


