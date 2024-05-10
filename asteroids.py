from asteroidsClasses  import *

class Asteroids:
    def __init__(self, worldwidth, worldheight, rock_amount):
        self.worldwidth = worldwidth
        self.worldheight = worldheight
        self.rocks = self.new_rocks(rock_amount)
        self.ship = [self.new_ship()]
        self.bullets = []
        self.stars = []
        self.enemies = []
        
    def get_ship(self):
        return self.ship[0]
        
    def get_objects(self):
        return self.stars + self.rocks + self.ship + self.enemies + self.bullets
    
    def add_bullet(self):
        ship = self.get_ship()
        rotation = ship.get_rotation()
        x, y = ship.get_pos()
        dx, dy = get_cart(rotation, 10)
        self.bullets.append(Bullet(x, y, dx, dy, self.worldwidth, self.worldheight, 60, ship))
    
    def add_objects(self, objects):
        types = {Bullet: self.bullets,
                 Rock: self.rocks,
                 Star: self.stars}
                 
        for obj in objects:
            t = type(obj)
            array = types[t]
            array.append(obj)
            
    def get_inputs(self, keys = []):
        newkeys = []
        for event in pygame.event.get(exclude=None):
            if event.type == pygame.KEYDOWN:
                keys.append(event.key)
                newkeys.append(event.key)
            elif event.type == pygame.KEYUP:
                keys.remove(event.key)
            elif event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
        mousepos = pygame.mouse.get_pos()
        return keys, mousepos, newkeys
    
    def use_inputs(self, inputs, dt):
        turnspeed = 4
        movespeed = 0.1
        accelerated = False
        keys, mousepos, newkeys = inputs
        if pygame.K_LSHIFT in keys:
            self.get_ship().frictionval = 0
            movespeed = 1.5
        else:
            self.get_ship().frictionval = 0.01
        for key in keys:
            if key in (pygame.K_UP, pygame.K_w) and not accelerated:
                self.accelerate_ship(movespeed * dt)
                accelerated = True
            elif key in (pygame.K_LEFT, pygame.K_a):
                self.turn_ship_left(turnspeed * dt)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.turn_ship_right(turnspeed * dt)
        for key in newkeys:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.add_bullet()
                
    
    def new_rocks(self, rock_amount):
        rocks = []
        for _ in range(rock_amount):
            x = random.randint(0, self.worldwidth)
            y = random.randint(0, self.worldheight)
            dx = random.randint(0, 100)/50
            dy = random.randint(0, 100)/50
            spin_rate = random.randint(0, 100)/100
            rock = Rock(x, y, dx, dy, 0, self.worldwidth, self.worldheight, spin_rate, 40, 15)
            rocks.append(rock)
        return rocks
    
#     def new_rocks(self, rock_amount):
#         return []
    
    def new_stars(self, star_amount):
        stars = []
        for _ in range(star_amount):
            x, y = (random.randint(0, self.worldwidth), random.randint(0, self.worldheight))
            dx, dy = (0, 0)
            worldwidth = self.worldwidth
            worldheight = self.worldheight
            lifetime = random.randint(0, 20)
            distance = random.randint(1, 10)
            star = Star(x, y, dx, dy, worldwidth, worldheight, lifetime, distance)
            stars.append(star)
        return stars
    
    def set_ship_dest(self, point):
        ship = self.get_ship()
        x, y = ship.get_pos()
        dx, dy = point
        
        ship.dx = x - dx
        ship.dy = y - dy
    
    def new_ship(self):
        return Ship(self.worldwidth/2, self.worldheight/2, 0, 0, 0, self.worldwidth, self.worldheight)
    
    def turn_ship_left(self, amount):
        self.get_ship().rotate(-amount)
            
    def turn_ship_right(self, amount):
        self.get_ship().rotate(amount)
        
    def accelerate_ship(self, amount):
        self.get_ship().accelerate(amount)
    
    def evolve(self, dt):
        for rock in self.rocks:
            if self.get_ship() in rock:
                self.get_ship().active = False
                self.__init__(self.worldwidth, self.worldheight, 10)
            for bullet in self.bullets[:]:
                if bullet in rock:
                    self.add_objects(rock.explode(bullet.parent))
                    bullet.explode()
            for enemy in self.enemies:
                seen = enemy.sees(self.rocks)
                
        for obj in self.get_objects():
            obj.evolve(dt)
        self.clear_inactives()
        GLOBAL.refresh()
                    
    def clear_inactives(self):
        is_active = lambda obj: obj.active
        types = (self.rocks, self.ship, self.bullets, self.stars)
        for t in types:
            t[:] = list(filter(is_active, t))
    
    def draw(self, surface):
        for obj in self.get_objects():
            obj.draw(surface)

if __name__ == '__main__':
    a = Asteroids(800, 800, 10)
    s = pygame.display.set_mode((800, 800))
    keys = []
    clock = pygame.time.Clock()
    FPS = 60
    while True:
        dt = 1
        s.fill((0, 0, 0))
        keys, mousepos, newkeys = a.get_inputs()
        a.use_inputs((keys, mousepos, newkeys), dt)
        a.evolve(dt)
        a.draw(s)
        pygame.display.update()
        clock.tick(FPS)

