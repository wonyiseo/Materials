
import pickle
import threading
from tkinter import Tk , filedialog , messagebox , ttk

import numpy as np
import pandas as pd
import pygame
from PIL import Image
from matplotlib import figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg ,
                                               NavigationToolbar2Tk)


class SaveData:

    pass

class TableView(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()
        self.initialized = False
        self.data = []

    def addRow(self , entry):
        """Add row to table."""
        while not self.initialized:
            pass
        entry[1:] = [round(ent , 3) for ent in entry[1:]]
        self.treev.insert("" , "end" , text="L1" , values=entry)
        self.data.append(entry)

    def getDF(self):
        """Get table values as a pandas data frame."""
        data = pd.DataFrame(self.data , columns=["Element" , "Min" , "Max" , "Average"])
        data.set_index("Element" , inplace=True)
        return data

    def killTable(self):
        self.root.quit()
        self.root.update()

    def run(self):
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW" , lambda: None)
        self.root.title("Table")

        self.treev = ttk.Treeview(self.root , selectmode="browse")
        self.treev.pack(side="right")
        self.treev.pack(side="right")

        verscrlbar = ttk.Scrollbar(
            self.root , orient="vertical" , command=self.treev.yview
        )
        verscrlbar.pack(side="right" , fill="x")

        self.treev.configure(xscrollcommand=verscrlbar.set)
        self.treev["columns"] = ("1" , "2" , "3" , "4")
        self.treev["show"] = "headings"

        self.treev.column("1" , width=100 , anchor="c")
        self.treev.column("2" , width=100 , anchor="se")
        self.treev.column("3" , width=100 , anchor="se")
        self.treev.column("4" , width=100 , anchor="se")

        self.treev.heading("1" , text="Element")
        self.treev.heading("2" , text="min")
        self.treev.heading("3" , text="max")
        self.treev.heading("4" , text="average")

        self.initialized = True

        self.root.mainloop()


class Figure(threading.Thread):

    def __init__(self , plots):
        threading.Thread.__init__(self)
        self.plots = plots
        self.start()

    def killFigure(self):
        self.root.quit()
        self.root.update()

    def saveFig(self , filename):
        self.fig.savefig(filename)

    def run(self):
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW" , lambda: None)
        self.root.title("Plot")

        self.fig = figure.Figure()
        plot = self.fig.add_subplot(111)

        for x , y , label in self.plots:
            plot.plot(x , y , label=label)
        plot.legend()

        canvas = FigureCanvasTkAgg(self.fig , master=self.root)
        canvas.draw()
        canvas.get_tk_widget().pack()

        toolbar = NavigationToolbar2Tk(canvas , self.root)
        toolbar.update()

        canvas.get_tk_widget().pack()

        self.root.mainloop()


class WindowHandler:
    """Handles external(graphs/tables) windows."""

    def __init__(self):
        self.mainTable = None
        self.mainFigure = None
        self.plots = []
        self.killed = False
        self.rects = []

    def __del__(self):
        if not self.killed:
            self.killThreads()

    def killThreads(self):
        if self.mainTable:
            self.mainTable.killTable()
            self.mainTable.join()
        if self.mainFigure:
            self.mainFigure.killFigure()
            self.mainFigure.join()
        self.killed = True

    def addRects(self , rects):
        """Add rectangle coordinates."""
        for rect in rects:
            self.rects.append(rect)

    def addToTable(self , entry):
        """Add entry to table."""
        if self.mainTable is None:
            self.mainTable = TableView()
        self.mainTable.addRow(entry)

    def loadGraph(self , plots_in):
        """Load the graph window."""
        self.plots = plots_in
        if self.plots:
            self.mainFigure = Figure(self.plots)
