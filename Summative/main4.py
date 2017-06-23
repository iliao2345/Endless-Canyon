#ENDLESS CANYON Main Code
#Isaac Liao
#version 1
#23-05-2017
import pygame, sys, time, random
from pygame.locals import*
sys.path.append(sys.path[0] + '\\modules')
import game4 as game
from math import*
from numpy import*

#screen class for menu tree
class Game_Screen():
    def __init__(self, buttons, texts):
        self.buttons = buttons
        self.texts = texts
        self.divs = [] # list of sections of screen consisting of 2 parts: colour and rect.
        game.setup(window)
    def display(self):
        global window
        for division in self.divs:
            pygame.draw.rect(window, division[0], division[1])
        for obj in self.buttons+self.texts:
            obj.display()
            
#button class for menu tree
class Button():
    def __init__(self, rect, destination, x=0, y=0, pushed_rect=None): #pushed_rect is the image of the pushed button
        self.rect = rect
        if type(rect) == pygame.Surface: #if the button is an image
            self.x = x
            self.y = y
            self.pushed_rect = pushed_rect
        self.destination = destination # where the button leads
        self.pushed = False
    def press(self, tree, current_screen):
        if self.destination == 'back':
            current_screen = go_back(tree, current_screen)
        elif type(self.destination) == Screen or type(self.destination) == Game_Screen:
            return self.destination
        return current_screen
    def display(self):
        global window
        if type(self.rect) == pygame.Rect:
            pygame.draw.rect(window, (128, 128, 128), self.rect)
        elif type(self.rect) == pygame.Surface:
            w, h = self.rect.get_width(), self.rect.get_height()
            if self.pushed and self.pushed_rect != None: window.blit(self.pushed_rect, (self.x-w/2, self.y-h/2))
            else: window.blit(self.rect, (self.x-w/2, self.y-h/2))
    def check_click(self, x, y):
        if type(self.rect) == pygame.Rect:
            return self.rect.collidepoint(x, y)
        if type(self.rect) == pygame.Surface:
            w, h = self.rect.get_width(), self.rect.get_height()
            return pygame.Rect(self.x-w/2, self.y-h/2, w, h).collidepoint(x, y)

#screen class for menu tree
class Screen():
    def __init__(self, background, buttons, texts, images=[]):
        self.buttons = buttons
        self.texts = texts
        self.background = background
        self.images = images
    def display(self):
        global window
        if type(self.background) == tuple:
            window.fill(self.colour)
        elif type(self.background) == pygame.Surface:
            window.blit(self.background, (0, 0))
        for obj in self.buttons+self.texts+self.images:
            obj.display()

#image class for menu tree
class Image():
    def __init__(self, image, x, y):
        self.image = image
        self.x = x
        self.y = y
    def display(self):
        global window
        w, h = self.image.get_width(), self.image.get_height()
        window.blit(self.image, (self.x - w/2, self.y - h/2))

#text class for menu tree
class Text():
    def __init__(self, string, size, font, colour, x, y, align = 'center'):
        self.string = string
        self.align = align
        self.x = x
        self.y = y
        self.size = size
        self.colour = colour
        self.font = font
        self.update()
    def update(self): #change properties
        lines = self.string.split('\n')
        fontobj = pygame.font.Font(self.font, int(self.size))

        #special calculation must be done because text.render() does not support newline characters
        max_w = 0
        total_h = 0
        for line in lines: #find the maximum width
            w, h = fontobj.size(line)
            max_w = max(max_w, w)
            total_h += h

        self.textobj = pygame.Surface((max_w, total_h), flags=SRCALPHA)
        
        dy = 0 #dy is the vertical displacement
        for line in lines: #add lines vertically
            w, h = fontobj.size(line)
            nextline = fontobj.render(line, False, self.colour) #create a surface with text, blit it below the previous line.
            if self.align == 'left':
                self.textobj.blit(nextline, (0, dy))
            elif self.align == 'center':
                self.textobj.blit(nextline, (max_w/2-w/2, dy))
            dy += h
        if self.align == 'left':
            self.top, self.left = int(self.x), int(self.y-dy/2)
        elif self.align == 'center':
            self.top, self.left = int(self.x-max_w/2), int(self.y-dy/2)
    def display(self):
        global window
        window.blit(self.textobj, (self.top, self.left))
        
#get_all_screens() returns all screens in the menu tree
def get_all_screens(screen):
    screen_list = [screen]
    for button in screen.buttons:
        if button.destination == None:
            continue
        if type(button.destination) == Screen or type(button.destination) == Game_Screen:
            for listed_screen in get_all_screens(button.destination):
                screen_list.append(listed_screen)
    return screen_list

#go_back() returns to the parent screen for any screen, quits if at the main menu
def go_back(tree, current_screen):
    if current_screen == tree:
        pygame.quit()
        sys.exit()
    for possible_parent in get_all_screens(tree):
        for button in possible_parent.buttons:
            if button.destination == current_screen:
                return possible_parent

#window setup
pygame.init()
width = 1000
height = 1000
background_colour = (100, 150, 255)
window = pygame.display.set_mode((width, height))

#edit the button images to remove unwanted corners
back_button = pygame.image.load('images\\back icon.jpg')
back_button.set_colorkey((255, 255, 255))
pygame.draw.polygon(back_button, (255, 255, 255), [(164, 108), (148, 108), (164, 92)]) #get rid of the white triangle in the corner
back_button.convert_alpha()
back_button_pushed = pygame.image.load('images\\back icon pushed.jpg')
back_button_pushed.set_colorkey((255, 255, 255))
pygame.draw.polygon(back_button_pushed, (255, 255, 255), [(164, 108), (148, 108), (164, 92)]) #get rid of the white triangle in the corner
back_button_pushed.convert_alpha()

other_buttons = []
for button in [pygame.image.load('images\\play icon.jpg'), pygame.image.load('images\\play icon pushed.jpg'), pygame.image.load('images\\instructions icon.jpg'), pygame.image.load('images\\instructions icon pushed.jpg')]:
    button.set_colorkey((255, 255, 255))
    pygame.draw.polygon(button, (255, 255, 255), [(327, 186), (311, 186), (327, 170)])
    pygame.draw.polygon(button, (255, 255, 255), [(0, 0), (16, 0), (0, 16)])
    pygame.draw.polygon(button, (255, 255, 255), [(327, 0), (311, 0), (327, 16)])
    pygame.draw.polygon(button, (255, 255, 255), [(0, 186), (16, 186), (0, 170)])
    button.convert_alpha()
    other_buttons.append(button)

#create the menu system
tree = Screen(pygame.image.load('images\\canyon background.jpg'),
              [Button(back_button, 'back', 82, 55, back_button_pushed), #exit button
               Button(other_buttons[0], #game
                      Game_Screen(
                          [Button(back_button, 'back', 82, 55, back_button_pushed)], []), 
                      width/2-300, height/2+200, other_buttons[1]), 
               Button(other_buttons[2], #instructions
                      Screen(pygame.image.load('images\\canyon background.jpg'),
                              [Button(back_button, 'back', 82, 55, back_button_pushed)], 
                              [],
                              [Image(pygame.image.load('images\\instructions.jpg'), width/2, height/2)]
                             ),
                      width/2+300, height/2+200, other_buttons[3]), 
               Button(pygame.Rect(0, 0, 0, 0), #score screen
                      Screen(pygame.image.load('images\\canyon background for score screen.jpg'),
                              [Button(back_button, 'back', 82, 55, back_button_pushed)], 
                              [Text('x', 200, None, (0, 0, 0), width/2, height/2-200)],
                              []
                             )
                      ),
               ],
              [], [Text('ENDLESS\nCANYON', 200, None, (190, 200, 210), 500, 270)]) #title


current_screen = tree
while True: #game loop
    events = pygame.event.get() #get events
    for event in events:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYUP:
            if event.key == K_ESCAPE: #escape key triggers go_back()
                current_screen = go_back(tree, current_screen)
                if type(current_screen) == Game_Screen: pygame.mouse.set_visible(False)
                else: pygame.mouse.set_visible(True)
        if event.type == MOUSEBUTTONUP: #check for button clicks
            for button in current_screen.buttons:
                x, y = pygame.mouse.get_pos()
                if button.check_click(x, y):
                    button.pushed = False
                    current_screen = button.press(tree, current_screen)
                    if type(current_screen) == Game_Screen: pygame.mouse.set_visible(False)
                    else: pygame.mouse.set_visible(True)
        if event.type == MOUSEBUTTONDOWN:
            for button in current_screen.buttons:
                x, y = pygame.mouse.get_pos()
                if button.check_click(x, y):
                    button.pushed = True
    if type(current_screen) == Game_Screen: #run one iteration of the game loop if that is the current screen
        score = game.loop(window, events) #pass events into the game loop
        if score != None: #the game has finished
            game.setup(window) #reset the game
            tree.buttons[3].destination.texts[0].string = str(score)+'x' #update the score screen
            tree.buttons[3].destination.texts[0].update()
            current_screen = tree.buttons[3].destination #go to the score screen
            pygame.mouse.set_visible(True)
    current_screen.display()
    pygame.display.update()

