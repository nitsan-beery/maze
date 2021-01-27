from coose_maze_window import *
import atexit, os


# needed due to a BUG in win32ui
def taskkill_this():
    # kill this process
    current_pid = os.getpid()
    os.system("taskkill /pid %s /f" % current_pid)


def main():
    atexit.register(taskkill_this)
    m = Maze()
    m.set_maze()
    m.show_maze()

main()

