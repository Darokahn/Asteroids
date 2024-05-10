import math

def subtract_vector2(v1, v2):
    return [val1 - val2 for val1, val2 in zip(v1, v2)]

def add_vector2(v1, v2):
    return [val1 + val2 for val1, val2 in zip(v1, v2)]

def add_angles(a1, a2):
    return (a1 + a2) % (math.pi * 2)

def rotate_point(drotation, x, y):
    rotation, magnitude = get_polar(x, y)
    x, y = get_cart(rotation + drotation, magnitude)
    return (x, y)

def angle_between(point1, point2):
    normal = subtract_vector2(point2, point1)
    return get_angle(*normal)

def get_polar(x, y):
    magnitude = get_magnitude(x, y)
    angle = get_angle(x, y)
    return angle, magnitude

def get_cart(angle, magnitude):
    x = math.cos(angle) * magnitude
    y = math.sin(angle) * magnitude
    return (x, y)

def get_magnitude(x, y):
    return math.sqrt((x**2) + (y**2))

def get_angle(x, y):
    angle = math.atan2(y, x)
    angle = angle % (math.pi * 2)
    return angle

def distance_between(point1, point2):
    x, y = subtract_vector2(point2, point1)
    return get_magnitude(x, y)

def normalize_angles(*angles):
    normal = -angle[0]
    for count, angle in enumerate(angles):
        angles[count] = angle + normal
    return angles

def angle_is_between(angle1, angle2, arg):
    full_rotation = (2 * math.pi)
    angle1, angle2, arg = normalize_angles(angle1, angle2, arg)
    angle1, angle2, arg = [i % full_rotation for i in (angle1, angle2, arg)]
    return angle1 < arg < angle2

def lesser_arc_is_clockwise(angle1, angle2):
    full_rotation = (2 * math.pi)
    angle1, angle2 = normalize_angles(angle1, angle2)
    
    
    

def get_y_intercept(point, slope):
    x, y = point
    return (slope * -x) + y