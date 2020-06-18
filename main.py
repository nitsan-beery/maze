from maze import *


def main():
    for i in range(1):
        m = Maze()
        if gv.DEBUG_MODE:
            m.print_cells()
            print(f'start: (0, {m.start_col})   end: ({m.height-1}, {m.end_col})')
            m.show_maze()
        m.set_maze()
        print(f'{i}: sucsess\n{m.info.num_of_decoy_polygons} Decoy poygons,   trail length: {m.info.trail_length}')
    m.show_maze(False)
    m.show_maze(True)

main()

