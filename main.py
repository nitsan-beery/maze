from maze import *


def main():
    for i in range(1):
        m = Maze()
        if gv.DEBUG_MODE:
            m.print_cells()
            print(f'start: (0, {m.start_col})   end: ({m.height-1}, {m.end_col})')
        m.set_trail()
        print(f'{i}: sucsess')
    m.show_maze()

main()

