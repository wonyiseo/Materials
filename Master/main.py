import os
import pickle
import sys
from tkinter.messagebox import showwarning

import numpy as np
import pygame
import pygame_gui as pygui
from scipy.ndimage import zoom
from thermal_base import ThermalImage
from thermal_base import utils as ThermalImageHelpers

from QueueServer.redisqueue import RedisQueueWorker
from utils import WindowHandler

pygame.init()
WINDOW_SIZE = (1020 , 590)
NEW_FILE = False


class Manager(pygui.UIManager):

    def __init__(self , buttons , textbox=None , fields=None):
        super().__init__(WINDOW_SIZE)
        self.buttons = [
            (
                pygui.elements.UIButton(
                    relative_rect=pygame.Rect(pos , size) , text=text , manager=self
                ) ,
                func ,
            )
            for pos , size , text , func in buttons
        ]
        if textbox:
            self.textbox = pygui.elements.ui_text_box.UITextBox(
                html_text=textbox[2] ,
                relative_rect=pygame.Rect(textbox[:2]) ,
                manager=self ,
            )
        if fields:
            self.fields = [
                (
                    pygui.elements.ui_text_entry_line.UITextEntryLine(
                        relative_rect=pygame.Rect((pos[0] , pos[1] + 40) , size) ,
                        manager=self ,
                    ) ,
                    pygui.elements.ui_text_box.UITextBox(
                        html_text=text ,
                        relative_rect=pygame.Rect(pos , (-1 , -1)) ,
                        manager=self ,
                    ) ,
                )
                for pos , size , text in fields
            ]

    def process_events(self , event):
        """Process button presses."""
        if event.type == pygame.USEREVENT:
            if event.user_type == pygui.UI_BUTTON_PRESSED:
                for button , func in self.buttons:
                    if event.ui_element == button:
                        func()

        super().process_events(event)


class Window:
    """Class that handles the main window."""
    fonts = [
        pygame.font.SysFont("monospace" , 20) ,
        pygame.font.SysFont("monospace" , 24) ,
        pygame.font.SysFont("arial" , 18) ,
    ]

    cursors = [
        pygame.image.load("./assets/cursors/pointer.png") ,
        pygame.image.load("./assets/cursors/crosshair.png") ,
    ]
    clip = lambda x , a , b: a if x < a else b if x > b else x

    @staticmethod
    def renderText(surface , text , location):
        """Render text at a given location."""
        whitetext = Window.fonts[2].render(text , 1 , (255 , 255 , 255))
        Window.fonts[0].set_bold(True)
        blacktext = Window.fonts[2].render(text , 1 , (0 , 0 , 0))
        Window.fonts[0].set_bold(False)

        textrect = whitetext.get_rect()
        for i in range(-3 , 4):
            for j in range(-3 , 4):
                textrect.center = [a + b for a , b in zip(location , (i , j))]
                surface.blit(blacktext , textrect)
        textrect.center = location
        surface.blit(whitetext , textrect)

    def __init__(self , thermal_image=None , filename=None):
        self.exthandler = WindowHandler()
        if thermal_image is not None:
            mat = thermal_image.thermal_np.astype(np.float32)

            if mat.shape != (512 , 640):
                y0 , x0 = mat.shape
                mat = zoom(mat , [512 / y0 , 640 / x0])

            self.mat = mat
            self.mat_orig = mat.copy()
            self.mat_emm = mat.copy()
            self.raw = thermal_image.raw_sensor_np
            self.meta = thermal_image.meta
            self.overlays = pygame.Surface((640 , 512) , pygame.SRCALPHA)
        else:
            with open(filename , "rb") as f:
                data = pickle.load(f)
            self.mat = data.mat
            self.mat_orig = data.mat_orig
            self.mat_emm = data.mat_emm
            self.raw = data.raw
            self.meta = data.meta
            self.overlays = pygame.image.fromstring(data.overlays , (640 , 512) , "RGBA")

            for entry in data.tableEntries:
                self.exthandler.addToTable(entry)
            self.exthandler.loadGraph(data.plots)
            self.exthandler.addRects(data.rects)

        self.colorMap = "jet"
        self.lineNum = 0
        self.boxNum = 0
        self.spotNum = 0
        self.areaMode = "poly"
        self.selectionComplete = False

        self.mode = "main"
        self.managers = {}
        self.managers["main"] = Manager(
            buttons=[((15 , 15) , (215 , 45) , "Area marking" , lambda: self.changeMode("area"))]
        )
        self.managers["area"] = Manager(
            buttons=[
                ((15 , 470) , (215 , 45) , "Continue" , lambda: self.work("area")) ,
                ((15 , 530) , (215 , 45) , "Back" , lambda: self.changeMode("main")) ,
            ] ,
            textbox=(
                (15 , 15) ,
                (215 , -1) ,
                "Click and drag to draw selection. Select continue to mark" ,
            ) ,
        )
        self.linePoints = []

        self.cursor_rect = self.cursors[0].get_rect()
        self.background = pygame.Surface(WINDOW_SIZE)
        self.background.fill((170 , 170 , 170))

    def changeMode(self , mode):
        if self.mode == "line":
            if mode in ("main" , "line"):
                self.linePoints = []

        if self.mode in ("scale" , "area" , "emissivity"):
            if mode in ("main" , "scale" , "area"):
                self.selectionComplete = False
                self.linePoints = []

        self.mode = mode

    def work(self , mode , *args):
        if mode == "area":
            if self.selectionComplete:
                points = [(a - 245 , b - 15) for a , b in self.linePoints]
                x_coords , y_coords = zip(*points)
                xmin = min(x_coords)
                xmax = max(x_coords)
                ymin = min(y_coords)
                ymax = max(y_coords)
                if xmin == xmax or ymin == ymax:
                    return
                self.boxNum += 1
                chunk = self.mat_emm[ymin:ymax , xmin:xmax]
                self.exthandler.addToTable(
                    [f"a{self.boxNum}" , np.min(chunk) , np.max(chunk) , np.mean(chunk)]
                )
                self.exthandler.addRects([[xmin , xmax , ymin , ymax]])
                pygame.draw.lines(self.overlays , (255 , 255 , 255) , True , points , 3)
                self.renderText(
                    self.overlays , f"a{self.boxNum}" , (xmin + 12 , ymin + 10)
                )

    def process(self , event):
        """Process input event."""
        self.mx , self.my = self.cursor_rect.center = pygame.mouse.get_pos()
        self.cx = Window.clip(self.mx , 245 , 884)
        self.cy = Window.clip(self.my , 15 , 526)
        self.cursor_in = (245 < self.mx < 885) and (15 < self.my < 527)
        self.managers[self.mode].process_events(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.cursor_in:
                if self.mode == "line":
                    if len(self.linePoints) < 2:
                        self.linePoints.append((self.mx , self.my))
                if (
                        self.mode == "scale" and self.areaMode == "poly"
                )
                if (
                        self.mode == "scale" and self.areaMode == "rect"
                ) or self.mode == "area":
                    self.changeMode(self.mode)
                    self.linePoints.append((self.mx , self.my))


        if event.type == pygame.MOUSEBUTTONUP:
            if (
                    self.mode == "scale" and self.areaMode == "rect"
            ) or self.mode == "area":
                if len(self.linePoints) == 1:
                    self.linePoints.append((self.cx , self.linePoints[0][1]))
                    self.linePoints.append((self.cx , self.cy))
                    self.linePoints.append((self.linePoints[0][0] , self.cy))
                    self.selectionComplete = True

    def update(self , time_del):
        self.managers[self.mode].update(time_del)

    def draw(self , surface):
        """Draw contents on screen."""
        surface.blit(self.background , (0 , 0))
        surface.blit(self.imsurf , (245 , 15))
        surface.blit(self.overlays , (245 , 15))

        pygame.draw.rect(surface , (255 , 255 , 255) , (245 , 540 , 760 , 35) , 1)
        self.managers[self.mode].draw_ui(surface)
        surface.blit(
            self.fonts[1].render(
                f"x:{self.cx - 245:03}   y:{self.cy - 15:03}   temp:{self.mat_emm[self.cy - 15 , self.cx - 245]:.4f}" ,
                1 ,
                (255 , 255 , 255) ,
            ) ,
            (253 , 544) ,
        )

        if (
                self.mode == "scale" and self.areaMode == "poly"
        ) 
        if (self.mode == "scale" and self.areaMode == "rect") or self.mode == "area":
            if not self.selectionComplete:
                if len(self.linePoints) > 0:
                    pygame.draw.lines(
                        surface ,
                        (255 , 255 , 255) ,
                        True ,
                        self.linePoints
                        + [
                            (self.cx , self.linePoints[0][1]) ,
                            (self.cx , self.cy) ,
                            (self.linePoints[0][0] , self.cy) ,
                        ] ,
                        3 ,
                    )
            else:
                pygame.draw.lines(surface , (255 , 255 , 255) , True , self.linePoints , 3)

        surface.blit(self.cursors[self.cursor_in] , self.cursor_rect)


if __name__ == "__main__":
    pygame.mouse.set_visible(False)

    pygame.display.set_caption("")
    pygame.display.set_icon(pygame.image.load("./assets/visible.png"))
    surface = pygame.display.set_mode(WINDOW_SIZE)
    surface.blit(Window.fonts[2].render("Loading..." , 1 , (255 , 255 , 255)) , (460 , 275))
    pygame.display.update()

    clock = pygame.time.Clock()

    done = False
    NEW_FILE = True
    window = None

    QUEUE_NAME = "queue1"
    WORKER_NAME = "queue1"
    QUEUE_PASS = "queue1234"
    SERVER_IP = "54.180.86.235"
    SERVER_PORT = 8588
    DB = 0
    q = RedisQueueWorker(event_q_name="queue1" , worker_q_name="queue11" , host=SERVER_IP , port=SERVER_PORT , db=DB)

    while not done:

        if NEW_FILE:
            msg = q.get_msg(isBlocking=True)
            q.done_msg(msg)

            # filename = openImage()
            if msg:
                filename = "./result.jpg"
                with open(filename , "wb") as fp:
                    fp.write(msg)

                surface.fill((0 , 0 , 0))
                surface.blit(
                    Window.fonts[2].render("Loading..." , 1 , (255 , 255 , 255)) , (460 , 275)
                )
                pygame.display.update()
                newwindow = None
                try:
                    # if filename.split(".")[-1] == "pkl":
                    #     newwindow = Window(filename=filename)
                    # else:
                    try:
                        image = ThermalImage(filename , camera_manufacturer="FLIR")
                    except Exception:
                        image = ThermalImage(filename , camera_manufacturer="DJI")

                    newwindow = Window(thermal_image=image)

                except Exception as err:
                    print(f"Exception: {err}")
                    showwarning(title="Error" , message="Please upload a jpg file that can be analyzed")

                if newwindow is not None:
                    if window is not None:
                        window.exthandler.killThreads()
                    window = newwindow

            if not window:
                sys.exit(0)
            NEW_FILE = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == ord("s"):
                    index = 0
                    while os.path.isfile(f"{index}.png"):
                        index += 1
                    pygame.image.save(surface , f"{index}.png")
                    print(f"Saved {index}.png")

            window.process(event)

        window.update(clock.tick(60) / 1000.0)
        window.draw(surface)

        pygame.display.update()

    # For the threads to close before end of program
    window.exthandler.killThreads()
