import pygame
import time

SCREENSIZE = (800, 800)

class Frog:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.surface = self.load_surface("frog.png")
        
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
    
    def load_surface(self, path):
        return pygame.image.load(path)
    
    def get_surface(self):
        return self.surface
    
    def handle_inputs(self, inputs):
        keys, mousepos, mousebuttons = inputs
        movement = [0, 0]
        for key in keys:
            
            if key == pygame.K_UP:
                movement[1] += -1
            elif key == pygame.K_DOWN:
                movement[1] += 1
        
        self.move(*movement)
    
    def draw(self, surface):
        position = (self.x, self.y)
        
        new_surface = self.get_surface()
        
        surface.blit(new_surface, position)
        
d = pygame.display.set_mode(SCREENSIZE)

f = Frog(20, 20)

def get_inputs():
    keys = []
    mousepos = pygame.mouse.get_pos()
    mousebuttons = []
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            keys.append(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousebuttons.append(event.button)
            
    return (keys, mousepos, mousebuttons)

while True:
    inputs = get_inputs()
    f.handle_inputs(inputs)
    d.fill("black")
    f.draw(d)
    
    pygame.display.update()
    
    time.sleep(0.1)
