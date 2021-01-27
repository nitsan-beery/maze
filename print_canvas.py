import tkinter as tk
from tkinter import ttk
import win32print
# importing win32ui causes a BUG - can't exit the program
import win32ui
import win32con


def print_canvas(root, canvas, scale=20):
    coord_list = [(canvas.type(obj), canvas.coords(obj)) for obj in canvas.find_all()]
    '''Print canvas from list of coords for each canvas.object'''
    moves = []
    for obj in coord_list:
        if obj[0] == 'rectangle':
            # moves.append(('rectangle@: ', obj[1]))
            tlc, trc, blc, brc = (obj[1][0], obj[1][1]), (obj[1][2], obj[1][1]), (obj[1][0], obj[1][3]), (
            obj[1][2], obj[1][3])
            moves.append('dc.MoveTo((scale*%d, scale*-%d))' % (int(tlc[0]), int(tlc[1])))
            moves.append('dc.LineTo((scale*%d, scale*-%d))' % (int(blc[0]), int(blc[1])))
            moves.append('dc.LineTo((scale*%d, scale*-%d))' % (int(brc[0]), int(brc[1])))
            moves.append('dc.LineTo((scale*%d, scale*-%d))' % (int(trc[0]), int(trc[1])))
            moves.append('dc.LineTo((scale*%d, scale*-%d))' % (int(tlc[0]), int(tlc[1])))

        elif obj[0] == 'line':
            # moves.append(('line@: ', obj[1]))
            moves.append('dc.MoveTo((scale*%d, scale*-%d))' % (int(obj[1][0]), int(obj[1][1])))
            moves.append('dc.LineTo((scale*%d, scale*-%d))' % (int(obj[1][2]), int(obj[1][3])))

        elif obj[0] == 'polygon':
            # moves.append(('polygon@: ', obj[1]))
            start = 0
            temp = []
            for y in range(1, len(obj[1]) + 1, 2):
                temp.append((obj[1][start], obj[1][y]))
                start += 2
            sc = temp[0]
            ec = temp[1]
            if sc != ec:
                temp.append(sc)  # close the polygon
            moves.append('dc.MoveTo((scale*%d, scale*-%d))' % (int(temp[0][0]), int(temp[0][1])))
            for x in temp[1:]:
                moves.append('dc.LineTo((scale*%d, scale*-%d))' % (int(x[0]), int(x[1])))

        elif obj[0] == 'arc':
            # draw curve to printer ???
            pass
        elif obj[0] == 'oval':
            # draw curve to printer ???
            pass
        else:
            pass
    choice = PrinterChooser(root).show()
    if choice is not None:
        printer = choice.get('printer')
    else:
        return
    try:
        dc = win32ui.CreateDC()
        dc.CreatePrinterDC(printer)
        dc.SetMapMode(win32con.MM_TWIPS)  # 1440 per inch
        dc.StartDoc('draw line')
        pen = win32ui.CreatePen(win32con.PS_SOLID, 0, 0)
        dc.SelectObject(pen)
        for x in moves:
            exec(x)
        dc.EndDoc()
    except:
        print('!!! Print Failed !!!')


class PrinterChooser(object):
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title(' Choose')
        width = 220
        height = 150
        self.window.geometry(f'{width}x{height}')
        self.window.resizable(0, 0)

        p_list = win32print.EnumPrinters(2)
        p0 = None
        p1 = None
        printers = []
        for p in p_list:
            printer = p[1]
            sep = printer.find(",")
            printer = printer[:sep]
            if p0 is None and 'hp' in printer.lower():
                p0 = printer
            if p1 is None and 'pdf' in printer.lower():
                p1 = printer
            printers.append(printer)
        if p1 is not None:
            printers.remove(p1)
            printers.insert(0, p1)
        if p0 is not None:
            printers.remove(p0)
            printers.insert(0, p0)

        self.frame_1 = tk.Frame(self.window)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
        self.frame_2 = tk.Frame(self.window)
        self.frame_2.pack(side=tk.TOP, fill=tk.BOTH, ipady=6)
        self.frame_3 = tk.Frame(self.window)
        self.frame_3.pack(side=tk.BOTTOM, fill=tk.BOTH, ipady=0)

        self.label_printer = tk.Label(self.frame_2, width=5, text='Printer', padx=7)
        self.label_printer.grid(row=0, column=2)

        self.printer_choice_menu = ttk.Combobox(self.frame_2, width=25, values=printers)
        self.printer_choice_menu.grid(row=1, column=2, padx=5, pady=5)

        button_ok = tk.Button(self.frame_3, text="OK", width=5, command=self.get_choice)
        button_cancel = tk.Button(self.frame_3, text="Cancel", width=5, command=self.window.destroy)
        button_ok.pack(side=tk.RIGHT, padx=5, pady=5)
        button_cancel.pack(side=tk.LEFT, padx=5)

        self.window.bind('<Key>', self.key)
        self.window.lift()

        # set default values
        i = printers.index(win32print.GetDefaultPrinter())
        self.printer_choice_menu.current(i)
        self.printer_choice_menu.focus_set()
        self.choice = None

    def get_choice(self):
        printer = self.printer_choice_menu.get()
        self.choice = {
            'printer': printer
        }
        self.window.destroy()

    def show(self):
        self.window.deiconify()
        self.window.wait_window()
        return self.choice

    def key(self, event):
        if event.keycode == 13:
            self.get_choice()
