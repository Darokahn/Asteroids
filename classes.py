import random
import pygame
from side_angle_side import magnitude_at_angle
from trig import *
from dataclasses import dataclass
from globalmessage import GLOBAL

GLOBAL.add_channel("ship-moved")

class Movable:
    def __init__(self, x, y, dx, dy, worldwidth, worldheight):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.worldwidth = worldwidth
        self.worldheight = worldheight
        self.radius = 0
        self.active = True
        
    def accelerate_cart(self, dx, dy):
        self.x += dx
        self.y += dy
        
    def accelerate_polar(self, angle, magnitude):
        dx, dy = get_cart(angle, magnitude)
        self.accelerate_cart(dx, dy)

    def move(self, dt, mag_modifier=1):
        direction, mag = get_polar(self.dx, self.dy)
        mag *= dt * mag_modifier
        x, y = get_cart(direction, mag)
        self.x += x
        self.y += y
        if self.x < -self.radius:
            self.x = self.worldwidth + self.radius
        elif self.x > self.worldwidth + self.radius:
            self.x = -self.radius
        if self.y < -self.radius:
            self.y = self.worldheight + self.radius
        if self.y > self.worldheight + self.radius:
            self.y = -self.radius
        return direction, mag
    
    def move_absolute(self, x, y):
        self.x += x
        self.y += y

    def apply_friction(self):
        friction = (1 - self.frictionval)
        self.dx *= friction
        self.dy *= friction

    def angle_to_object(self, other):
        normal = self.get_pos()
        otherpos = other.get_pos()
        return self.angle_to_point(otherpos)

    def angle_to_point(self, point):
        normal = self.get_pos()
        otherpos = point
        vector = [val1 - val2 for val1, val2 in zip(normal, otherpos)]
        x, y = vector
        angle = math.atan2(y, x)
        angle = angle % (2 * math.pi)
        return angle

    def get_pos(self):
        return (self.x, self.y)

    def accelerate(self, velocity):
        raise NotImplementedError

    def evolve(self, dt):
        raise NotImplementedError

    def draw(self, surface):
        raise NotImplementedError

    def explode(self):
        raise NotImplementedError


class Rotatable(Movable):
    def __init__(self, x, y, dx, dy, rotation, worldwidth, worldheight):
        super().__init__(x, y, dx, dy, worldwidth, worldheight)
        self.rotation = rotation

    def rotate(self, drotation):
        self.rotation += drotation
        self.rotation = self.rotation % 360

    def rotate_point(self, x, y):
        angle, mag = get_polar(x, y)
        angle = add_angles(self.get_rotation(), angle)
        return get_cart(angle, mag)

    def get_rotation(self):
        return math.radians(self.rotation)

    def accelerate(self, velocity):
        rotation = self.get_rotation()
        xmag, ymag = get_cart(rotation, velocity)
        self.dx += xmag
        self.dy += ymag
        return rotation, velocity

    def translate_point(self, x, y):
        x += self.x
        y += self.y
        return (x, y)

    def rotate_and_translate(self, x, y):
        x, y = self.rotate_point(x, y)
        x, y = self.translate_point(x, y)
        return x, y

    def rotate_translate_list(self, points):
        newpoints = []
        for point in points:
            newpoints.append(self.rotate_and_translate(*point))
        return newpoints


class Polygon(Rotatable):
    def __init__(self, x, y, dx, dy, rotation, world_width, world_height, original_polygon, color):
        super().__init__(x, y, dx, dy, rotation, world_width, world_height)
        self.original_polygon = original_polygon
        self.color = color
        self.angle_data = self.gen_angle_data()
        self.radius = self.get_max_point_distance()

    def get_max_point_distance(self):
        distances = []
        for point in self.original_polygon:
            distances.append(get_magnitude(*point))
        return max(distances)

    def set_polygon(self, p):
        self.original_polygon = p

    def gen_angle_data(self):
        ranges = {}
        points = self.original_polygon
        for count, val in enumerate(points):
            point2count = (count + 1) % len(points)
            point1 = val
            point2 = points[point2count]
            angle1, mag1 = get_polar(*point1)
            angle2, mag2 = get_polar(*point2)
            if angle2 == 0.0:
                angle2 = math.pi * 2
            anglerange = angle2 - angle1
            ranges.update({(angle1, angle2): (mag1, mag2)})
        return ranges

    def hash_ranges(self, angle):
        for key, value in self.angle_data.items():
            low, high = key
            if low <= angle <= high:
                relative_angle = angle - low
                total_angle = high - low
                magnitudes = value
                return (relative_angle, total_angle, magnitudes)
        return None

    def set_color(self, c):
        self.color = c

    def __contains__(self, other):
        if isinstance(other, (tuple, list)):
            if not len(other) == 2:
                Exception("position must be 2-long tuple")
            position = other
        elif isinstance(other, Movable):
            position = other.get_pos()
        else:
            Exception(f'invalid type {type(other)} for \'in\' operation')
        distance = distance_between(self.get_pos(), position)
        if distance > self.radius:
            return False
        angle = angle_between(self.get_pos(), position)
        angle = add_angles(angle, -self.get_rotation())
        relative, total, mags = self.hash_ranges(angle)
        mag = magnitude_at_angle(total, *mags, relative)
        return distance < mag

    def draw(self, surface):
        points = self.original_polygon
        points = self.rotate_translate_list(points)
        pygame.draw.polygon(surface, self.color, points)


class Ship(Polygon):
    color = "red"
    def __init__(self, x, y, dx, dy, rotation, world_width, world_height):
        polygon = self.gen_shape()
        color = Ship.color
        self.frictionval = 0.01
        super().__init__(x, y, dx, dy, rotation, world_width, world_height, polygon, color)

    def evolve(self, dt):
        self.move(dt)

    def move(self, dt, magnitude = None):
        self.apply_friction()
        vector = Movable.move(self, dt)
        GLOBAL.refresh()
        GLOBAL.broadcast("ship-moved", vector, 100)

    def gen_shape(self):
        return [[10, 0], [-5, -5], [-1, 0], [-5, 5], [10, 0]]

    def __repr__(self):
        return str(vars(self))

    def __str__(self):
        return f"{type(self)} " + str(vars(self))


class Rock(Polygon):
    color = "gray"
    def __init__(self, x, y, dx, dy, rotation, world_width, world_height, spin_rate, radius, pointcount):
        polygon = Rock.gen_shape(radius, pointcount)
        color = Rock.color
        super().__init__(x, y, dx, dy, rotation, world_width, world_height, polygon, color)
        self.spin_rate = spin_rate

    def evolve(self, dt):
        self.move(dt)
        self.rotate(self.spin_rate * dt)

    def gen_shape(radius, pointcount):
        points = []
        increment = 2 * math.pi / pointcount
        angle = 0
        for count in range(pointcount):
            angle = increment * count
            magnitudeMod = random.randint(70, 130)
            radius *= magnitudeMod / 100
            point = get_cart(angle, radius)
            points.append(point)
        return points

    def explode(self, killer):
        self.active = False
        if self.radius < 25:
            return [Star(self.x, self.y, random.randint(-10, 10), random.randint(-10, 10), self.worldwidth, self.worldheight, 0, random.randint(10, 100)) for i in range(3)]
        newrocks = []
        children_count = 3
        children_count = random.randrange(1, 4)
        for i in range(children_count):
            new_radius = min(20, self.radius / children_count)
            angle = i * (2 * math.pi) / 3
            new_magnitude = random.randint(1, 3)
            newpoint = get_cart(angle, new_magnitude / 3)
            newpoint = add_vector2(newpoint, self.get_pos())
            x, y = newpoint
            dx, dy = get_cart(angle, new_magnitude)
            spin_rate = random.randint(0, 100) / 100
            newrocks.append(Rock(x, y, dx, dy, 0, self.worldwidth, self.worldheight, spin_rate, new_radius, 10))
        return newrocks


class Circle(Rotatable):
    def __init__(self, x, y, dx, dy, rotation, worldwidth, worldheight, radius, color):
        super().__init__(x, y, dx, dy, rotation, worldwidth, worldheight)
        self.radius = radius
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.get_pos(), self.radius)


class Bullet(Circle):
    def __init__(self, x, y, dx, dy, worldwidth, worldheight, lifetime, parent):
        super().__init__(x, y, dx, dy, 0, worldwidth, worldheight, 3, "green")
        self.lifetime = lifetime
        self.time_spent = 0
        self.parent = parent

    def explode(self):
        self.active = False

    def evolve(self, dt):
        if self.time_spent >= self.lifetime:
            self.explode()
        self.time_spent += 1
        self.move(dt)

class Star(Circle):
    def __init__(self, x, y, dx, dy, worldwidth, worldheight, lifetime, distance):
        super().__init__(x, y, dx, dy, 0, worldwidth, worldheight, 1, "white")
        self.lifetime = lifetime
        self.distance = distance
        self.frictionval = 0.05

    def evolve(self, dt):
        self.move(dt)
        sparkle = random.randint(0, 100) / 1000
        self.lifetime += sparkle * dt
        self.move_parallax()
        self.apply_friction()
        
    def move_parallax(self):
        for vector in GLOBAL.get_messages("ship-moved", self):
            angle, magnitude = vector
            magnitude /= self.distance
            magnitude *= -1
            cart_vector = get_cart(angle, magnitude)
            self.move_absolute(*cart_vector) 

    def draw(self, surface):
        amplitude = 255
        half_amplitude = amplitude / 2
        brightness = (math.sin(self.lifetime) + 1) * half_amplitude
        extra_sparkle = brightness * 0.01
        color = [brightness for i in range(3)]
        radius = self.radius + extra_sparkle
        pygame.draw.circle(surface, color, self.get_pos(), radius)
