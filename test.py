from side_angle_side import magnitude_at_angle
import math
from classes import Rock
from trig import *
import pygame
import time


s = pygame.display.set_mode((800, 800))

while True:
    obj = Rock(300, 300, 0, 0, 0, 800, 800, 0, 100, 20)
    s.fill("black")
    for angle in range(3600):
        angle /= 10
        angle = math.radians(angle)
        relative, total, magnitudes = obj.hash_ranges(angle)
        magnitude = magnitude_at_angle(total, *magnitudes, relative)
        point = get_cart(angle, magnitude)
        point = add_vector2(point, obj.get_pos())
        pygame.draw.circle(s, "blue", point, 2)
        
    for point in obj.original_polygon:
        point = add_vector2(point, obj.get_pos())
        pygame.draw.circle(s, "red", point, 5)
        
    for angles, magnitudes in obj.angle_data.items():
        for count in range(2):
            angle = angles[count]
            mag = magnitudes[count]
            point = get_cart(angle, mag)
            point = add_vector2(point, obj.get_pos())
            pygame.draw.circle(s, "green", point, 2)
    pygame.display.update()
    pygame.event.get()
