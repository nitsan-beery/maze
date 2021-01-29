from coose_maze_window import *
import atexit
import os
import sys

# needed due to a BUG in win32ui
def taskkill_this():
    # kill this process
    current_pid = os.getpid()
    os.system("taskkill /pid %s /f" % current_pid)


def main():
    atexit.register(taskkill_this)
    sys.setrecursionlimit((gv.MAX_SIZE+1) ** 2)
    m = Maze()
    m.set_maze()
    m.show_maze()

main()

