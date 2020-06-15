from maze import *


def main():
    for i in range(10):
        m = Maze()
        if gv.DEBUG_MODE:
            m.print_cells()
            print(f'start: (0, {m.start_col})   end: ({m.height-1}, {m.end_col})')
            m.show_maze()
        m.set_trail()
#        m.print_cells()
#        m.show_maze()
        m.set_empty_polygons()
#        print('after setting empty polygons')
#        m.print_cells()
        print(f'{i}: sucsess')
    m.show_maze()

main()

