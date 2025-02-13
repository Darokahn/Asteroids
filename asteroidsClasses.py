import random
import pygame
from side_angle_side import magnitude_at_angle
from trig import *
from dataclasses import dataclass
from globalmessage import GLOBAL

GLOBAL.add_channel("ship-moved")
GLOBAL.add_channel("ship-warped")

class Init:
    def __init__(self, args, nonmembers=None, func=lambda x, y: None):
        if not nonmembers:
            nonmembers = []
        nonmembers.append("self")
        for key, value in args.items():
            if not key in nonmembers:
                setattr(self, key, value)

        func(self, args)


class Movable:
    def __init__(self, x, y, dx, dy, worldwidth, worldheight, frictionval = 0, distance = 0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.worldwidth = worldwidth
        self.worldheight = worldheight
        self.radius = 0
        self.active = True
        self.frictionval = frictionval
        self.distance = distance
    
    def move_parallax(self):
        for vector in GLOBAL.get_messages("ship-moved", self):
            angle, magnitude = vector
            try:
                magnitude /= self.distance ** 2
            except ZeroDivisionError:
                magnitude = magnitude
            magnitude *= -1
            cart_vector = get_cart(angle, magnitude)
            self.move_absolute(*cart_vector) 
        
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
        diameter = self.radius * 2
        if self.x < -self.radius:
            self.x += self.worldwidth + diameter
        elif self.x > self.worldwidth + self.radius:
            self.x -= self.worldwidth + diameter
        if self.y < -self.radius:
            self.y += self.worldheight + diameter
        elif self.y > self.worldheight + self.radius:
            self.y -= self.worldheight + diameter
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
    def __init__(self, x, y, dx, dy, rotation, worldwidth, worldheight, frictionval = 0, distance = 0):
        super().__init__(x, y, dx, dy, worldwidth, worldheight, frictionval, distance)
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
    def __init__(self, x, y, dx, dy, rotation, world_width, world_height, original_polygon, color, frictionval = 0, distance = 0):
        super().__init__(x, y, dx, dy, rotation, world_width, world_height, frictionval, distance)
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
    def __init__(self, x, y, dx, dy, rotation, world_width, world_height, color = "red"):
        polygon = self.gen_shape(1)
        super().__init__(x, y, dx, dy, rotation, world_width, world_height, polygon, color, 0.005)

    def evolve(self, dt):
        self.move(dt)

    def move(self, dt, magnitude = None):
        self.apply_friction()
        direction, mag = get_polar(self.dx, self.dy)
        GLOBAL.broadcast("ship-moved", (direction, mag), 1)

    def gen_shape(self, scale):
        shape = [[10, 0], [-5, -5], [-1, 0], [-5, 5], [10, 0]]
        return [[x * scale, y * scale] for x, y in shape]

    def __repr__(self):
        return str(vars(self))

    def __str__(self):
        return f"{type(self)} " + str(vars(self))
    
    
class Enemy(Ship):
    def __init__(self, x, y, dx, dy, rotation, world_width, world_height, target, view_range, view_distance, color = "green"):
        super().__init__(x, y, dx, dy, rotation, world_width, world_height, color)
        self.view_range = view_range
        self.view_distance = view_distance
        self.seen = []
        
    def sees(asteroids):
        seen = []
        half_range = self.view_range / 2
        low_angle = self.rotation - half_range
        high_angle = self.rotation + half_range
        for asteroid in asteroids:
            angle = angle_between(self.get_pos(), asteroid.get_pos())
            distance = distance_between(asteroid.get_pos(), self.get_pos())
            if not distance < self.view_distance:
                continue
            if not angle_is_between(low_angle, high_angle, angle):
                continue
            seen.append(angle, distance)
        return seen
    
    def move(self, dt):
        direction, magnitude = total_vector_proximity_bias(self, self.seen)
        if self.rotation != direction:
            self.rotate(1)
        self.accelerate_polar(direction, magnitude)
        super().move(self, dt)
    
    def total_vector_proximity_bias(self, vecs):
        angle, mag = [0, 0]
        for vector in vecs:
            n_angle, n_mag = vec
            n_mag = (1/n_mag)
            angle += n_angle
            mag += n_mag
        return angle, mag
    
    def set_seen(self, seen):
        self.seen = seen


class Rock(Polygon):
    color = "brown"
    def __init__(self, x, y, dx, dy, rotation, world_width, world_height, spin_rate, radius, pointcount):
        polygon = Rock.gen_shape(radius, pointcount)
        color = Rock.color
        super().__init__(x, y, dx, dy, rotation, world_width, world_height, polygon, color)
        self.spin_rate = spin_rate
        GLOBAL.add_listener(self, "ship-moved")

    def evolve(self, dt):
        self.move(dt)
        self.move_parallax()
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
            many_star_chance = random.randint(0, 100)
            if many_star_chance == 1:
                star_amount = round(self.radius)
            else:
                star_amount = round(self.radius/5)
            return [Star(self.x, self.y, random.randint(-10, 10), random.randint(-10, 10), self.worldwidth, self.worldheight, 0, random.randint(1, 10)) for i in range(star_amount)]
        newrocks = []
        children_count = random.randint(1, 4)
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
    def __init__(self, x, y, dx, dy, rotation, worldwidth, worldheight, radius, color, frictionval = 0, distance = 0):
        super().__init__(x, y, dx, dy, rotation, worldwidth, worldheight, frictionval, distance)
        self.radius = radius
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.get_pos(), self.radius)


class Bullet(Circle):
    def __init__(self, x, y, dx, dy, worldwidth, worldheight, lifetime, parent):
        super().__init__(x, y, dx, dy, 0, worldwidth, worldheight, 3, "green")
        self.lifetime = lifetime
        self.parent = parent

    def explode(self):
        self.active = False

    def evolve(self, dt):
        if self.lifetime <= 0:
            self.explode()
        self.lifetime -= 1
        self.move(dt)

class Star(Circle):
    def __init__(self, x, y, dx, dy, worldwidth, worldheight, lifetime, distance):
        color = pygame.Color(255 - random.randrange(100), 255 - random.randrange(100), 255 - random.randrange(100))
        super().__init__(x, y, dx, dy, 0, worldwidth, worldheight, 1, color, 0.05, distance)
        self.lifetime = lifetime
        self.warp = False
        self.previous_position = self.get_pos()
        GLOBAL.add_listener(self, "ship-moved")
    
    def move_parallax(self):
        for vector in GLOBAL.get_messages("ship-moved", self):
            angle, magnitude = vector
            try:
                magnitude /= self.distance ** 2
            except ZeroDivisionError:
                magnitude = magnitude
            minimum_speed_for_trail = 10
            self.warp = magnitude > minimum_speed_for_trail
            self.previous_position = add_vector2(get_cart(angle, magnitude-minimum_speed_for_trail), self.get_pos())
            magnitude *= -1
            cart_vector = get_cart(angle, magnitude)
            self.move_absolute(*cart_vector) 

    def evolve(self, dt):
        self.move(dt)
        sparkle = random.randint(0, 100) / 1000
        self.lifetime += sparkle * dt
        self.move_parallax()
        self.apply_friction()
    
    def add_position(self):
        self.previous_position = self.get_pos()

    def draw(self, surface):
        brightness = (math.sin(self.lifetime) + 1) / 2
        extra_sparkle = brightness
        color = [int(brightness * colorComponent)  for colorComponent in self.color[0:3]]
        radius = self.radius + (extra_sparkle * 2)
        
        if self.warp:
            pygame.draw.line(surface, color, self.get_pos(), self.previous_position, int(radius*2))
        else:
            pygame.draw.circle(surface, color, self.get_pos(), radius)
            
