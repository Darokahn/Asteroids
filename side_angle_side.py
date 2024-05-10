import math
import pygame
from trig import *
from dataclasses import dataclass

@dataclass
class Line:
    slope: float
    intercept: float
    
    def intercepts(self, other):
        line1 = (self.slope, self.intercept)
        line2 = (other.slope, other.intercept)
        m1, b1 = line1
        m2, b2 = line2
        
        try:
            x = (b2 - b1) / (m1 - m2)
        except ZeroDivisionError:
            return False
        
        y = m1 * x + b1
        
        return x, y
    
    def __str__(self):
        return f'y = {self.slope}x + {self.intercept}'


def magnitude_at_angle(total_angle, magnitude1, magnitude2, angle):
    remainder = (math.pi - total_angle) / 2
    
    line1 = side_angle_side_equation(total_angle, magnitude1, magnitude2)
    
    line2 = Line(math.tan(total_angle - angle + remainder), 0)
    
    interception = line1.intercepts(line2)
    
    return get_magnitude(*interception)
    
def side_angle_side_equation(total_angle, magnitude1, magnitude2):
    flat = math.pi
    remainder = (flat - total_angle) / 2
    
    x1, y1 = get_cart(remainder, magnitude1)
    x1 *= -1
    x2, y2 = get_cart(remainder, magnitude2)
    
    rise = y2 - y1
    run = abs(x1) + x2
    
    slope = rise/run
    
    y_intercept = get_y_intercept((x1, y1), slope)
    
    return Line(slope, y_intercept)