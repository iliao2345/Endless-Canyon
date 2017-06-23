#ENDLESS CANYON Game Code
#Isaac Liao
#version 4
#23-05-2017
import pygame, sys, math, numpy, time, random
from pygame.locals import*
if __name__ == '__main__':
    __file__ = sys.path[0] + '         '
sys.path.append(__file__[:-9] + '\\modules\\mymath')
sys.path.append(__file__[:-9] + '\\modules\\graphics')
sys.path.append(__file__[:-9] + '\\modules\\sounds')
import mymath_v01 as mymath
import graphics_v5_2 as graphics
from math import*
from numpy import*

def player_height(pos): #returns the height of the ground at (x, y), better matches the display
    global world
    corner00 = world.terrain.loaded[world.terrain.distance][world.terrain.distance] #y position of corner00
    corner01 = world.terrain.loaded[world.terrain.distance][world.terrain.distance+1]
    corner10 = world.terrain.loaded[world.terrain.distance+1][world.terrain.distance]
    corner11 = world.terrain.loaded[world.terrain.distance+1][world.terrain.distance+1]
    pos00 = (pos/world.terrain.scale)%1 #xz position of the pos
    if pos00[0][0] > pos00[2][0]: #pos is on one triangle, use corner10
        base = corner10 + (corner00-corner10)*(1-pos00[0][0]) + (corner11-corner10)*(pos00[2][0])
        return world.terrain.scale * base
    else: #pos is on the other triangle, use corner01
        base = corner01 + (corner00-corner01)*(1-pos00[2][0]) + (corner11-corner01)*(pos00[0][0])
        return world.terrain.scale * base
def ground_height(pos): #returns the height of the ground at (x, y), more versatile
    global world
    return graphics.Mountains(pos[0][0]/world.terrain.scale, pos[2][0]/world.terrain.scale, world.terrain.func_state) * world.terrain.scale
def draw_aim(window, craft): #draw the target reticle
    w, h = window.get_width(), window.get_height()#draw the target reticle
    pygame.draw.line(window, (0, 0, 0), (int(w/2-10), int(h/2)), (int(w/2-30), int(h/2)), 2)
    pygame.draw.line(window, (0, 0, 0), (int(w/2+10), int(h/2)), (int(w/2+30), int(h/2)), 2)
    pygame.draw.line(window, (0, 0, 0), (int(w/2), int(h/2-10)), (int(w/2), int(h/2-30)), 2)
    pygame.draw.line(window, (0, 0, 0), (int(w/2), int(h/2+10)), (int(w/2), int(h/2+30)), 2)

#universal aircraft class, can support planes, helicopters, etc.
class Aircraft():
    def __init__(self, linear_drag, angular_drag):
        try: px, pz = player.craft.pos[0][0], player.craft.pos[2][0] #try to spawn at the player
        except NameError: pz, px = 0, 0
        x = random.uniform(-1000+px, 1000+px)
        z = random.uniform(-1000+pz, 1000+pz)
        y = ground_height(array([[x], [0], [z]])) + 100
        self.pos = array([[x], [y], [z]])
        self.theta = eye(3) #theta transforms from the plane's coordinate system to the world's.
        self.omega = zeros([3, 1]) #the angular velocity of the craft, this is in the plane's coordinate system
        self.v = zeros([3, 1]) #the linear velocity of the craft
        self.accelleration = zeros([3, 1]) #this is in the plane's coordinate system
        self.alpha = zeros([3, 1]) #the angular accelleration of the craft
        self.linear_drag = linear_drag
        self.angular_drag = angular_drag
        self.hp = 30
    def move(self): #update the aircraft
        self.v += self.theta.dot(self.accelleration) #accellerate
        self.omega += self.alpha #torque
        self.pos += self.v #move
        self.theta = self.theta.dot(mymath.rot_mat(self.omega, 'rotation vector')) #rotate
        self.v += array([[0], [-0.03], [0]]) #gravity
        self.v -= self.theta.dot(self.theta.T.dot(self.v)*self.linear_drag) #linear drag
        self.omega *= 1-self.angular_drag #angular drag
    def get_altitude(self): #returns the height relative to the ground
        return self.pos[1][0]-ground_height(self.pos)
    def control(self, F, tau, max_a, max_alpha): # F=force, tau=torque. This controls the aircraft.
        self.accelleration = F * max_a
        self.alpha = tau * max_alpha

#player class, similar to enemy class
class Player():
    def __init__(self, specs): #specs means specifications, a dictionary of the aircraft's drag and thrust
        global world
        self.camera = graphics.Camera()
        self.model = graphics.Model(world.ambient, world.lights, __file__[:-9]+'\\3D models\\jet', False)
        world.models.append(self.model)
        self.craft = Aircraft(specs['linear drag'], specs['angular drag'])
        self.max_a = specs['linear accelleration']
        self.max_alpha = specs['angular accelleration']
    def update(self): #update the player
        self.craft.move()
        offset = array([[-40], [6], [0]], dtype=float) #camera offset
        self.camera.pos = self.craft.pos + self.craft.theta.dot(offset) #move camera
        self.camera.theta = self.craft.theta #rotate camera
        self.model.pos = self.craft.pos #move model
        self.model.theta = self.craft.theta #rotate model
        if random.uniform() < 0.03*(30-self.craft.hp): #emit flames from damage
            global fragments
            fragments.append(Fragment('flames', self.craft.pos+(numpy.random.rand(3, 1)-0.5)*10, copy(self.craft.v / 2)))
    def shoot(self, mode='bullet'): #shoot either a missile or bullet
        if mode == 'bullet': #shoot a bullet
            global bullets
            bullet = Bullet(copy(self.craft.pos+140*mymath.unit(self.craft.v)), copy(self.craft.theta.dot(array([[100], [0], [0]], dtype=float))))
            bullets.append(bullet)
        elif mode == 'missile': #shoot a missile
            global missiles
            closest_aim = -1 #closest_aim tracks the distance from the target reticle to the enemy
            target=None
            for enemy in enemies+[player]: #find the aircraft which is the closest to the target reticle
                if enemy != self:
                    aim = self.craft.theta[:,0].dot(mymath.unit(enemy.craft.pos-self.craft.pos))
                    if closest_aim < aim and aim > 0.8:
                        target = enemy
                        closest_aim = aim
            missile = Missile(self.craft.pos+60*mymath.unit(self.craft.v), self.craft.v+5*mymath.unit(self.craft.v), target)
            missiles.append(missile)
    def crashtest(self): #test for ground collision and bullet/missile collision
        h = ground_height(self.craft.pos)
        altitude = self.craft.pos[1][0]-h
        if altitude < 0: #test for ground collision
            self.crash()
            return True
        for obj in bullets+missiles: #test for bullet/missile collision
            closest_point = mymath.closestpoint(self.craft.pos, obj.pos, obj.pos - obj.v)
            if mymath.norm(self.craft.pos - closest_point)<20:
                obj.pos = closest_point
                obj.hit(mymath.unit(obj.pos-self.craft.pos))
                if type(obj) == Bullet:
                    self.craft.hp -= 1
                    sounds['hit'+str(random.randint(1, 5))].play()
                elif type(obj) == Missile:
                    self.craft.hp -= 20
                    sounds['explosion'].play()
                if self.craft.hp <= 0:
                    self.crash()
                    return True
        return False
    def crash(self): #crash and explode
        global world, fragments
        world.models.remove(self.model)
        sounds['explosion'].play()
        for i in range(10):
            fragments.append(Fragment('plane frag', copy(self.craft.pos), (numpy.random.rand(3, 1)-0.5)*mymath.norm(self.craft.v)*10))

#enemy class, similar to player class
class Enemy():
    def __init__(self, specs): #specs is a dictionary of the aircraft's drag and thrust
        global world
        self.craft = Aircraft(specs['linear drag'], specs['angular drag'])
        self.model = graphics.Model(world.ambient, world.lights, __file__[:-9]+'\\3D models\\jet', False)
        world.models.append(self.model)
        self.max_a = specs['linear accelleration']
        self.max_alpha = specs['angular accelleration']
    def update(self): #update the enemy
        self.craft.move()
        self.model.pos = self.craft.pos #move model
        self.model.theta = self.craft.theta #rotate model
        for obj in bullets+missiles: #test for bullet/missile collision
            closest_point = mymath.closestpoint(self.craft.pos, obj.pos, obj.pos - obj.v)
            if mymath.norm(self.craft.pos-closest_point)<20:
                obj.pos = closest_point
                obj.hit(mymath.unit(closest_point-self.craft.pos))
                if type(obj)==Bullet: self.craft.hp -= 1
                elif type(obj)==Missile: self.craft.hp -= 20
                if self.craft.hp <= 0: self.crash()
        if random.uniform() < 0.03*(30-self.craft.hp): #emit flames from damage
            global fragments
            fragments.append(Fragment('flames', self.craft.pos+(numpy.random.rand(3, 1)-0.5)*10, copy(self.craft.v / 2)))
    def automate(self): #control the enemy aircraft
        F = array([[0.8], [0], [0]]) #continuous thrust
        altitude = self.craft.get_altitude()
        if altitude<100: avoid_crash = 150/altitude #avoid ground collision
        else: avoid_crash = 0
        stay_upright = expand_dims(cross(array([0, 1, 0]), self.model.theta[:,1]), 1) * 0.3 #stay upright
        attack = ((self.craft.theta.T.dot(cross(self.model.theta[:,0], mymath.unit(self.craft.pos - player.craft.pos).T).T)>0)-0.5).astype(float) * 0.5 #attack player
        tau = expand_dims(cross(array([0, avoid_crash, 0]), self.model.theta[:,0]), 1)
        tau += stay_upright
        tau += attack
        self.craft.control(F, tau, self.max_a, self.max_alpha) #control the aircraft
        if self.model.theta[:,0].T.dot(mymath.unit(player.craft.pos - self.craft.pos)) > 0.9: #shoot if player is within 10 degrees of target reticle
            global bullets
            self.shoot()
    def crashtest(self): #test for ground collision
        h = ground_height(self.craft.pos)
        altitude = self.craft.pos[1][0]-h
        if altitude < 0:
            self.crash()
            return
    def crash(self): #crash and explode
        global world, fragments, enemies, kills
        kills += 1
        try:
            enemies.remove(self)
            world.models.remove(self.model)
        except ValueError:
            pass
        sounds['explosion'].play()
        for i in range(10):
            fragments.append(Fragment('plane frag', copy(self.craft.pos), (numpy.random.rand(3, 1)-0.5)*mymath.norm(self.craft.v)*10))
    def shoot(self, mode='bullet'): #shoot
        if mode == 'bullet':
            global bullets
            bullet = Bullet(self.craft.pos+140*mymath.unit(self.craft.v), self.craft.theta.dot(array([[100], [0], [0]], dtype=float)))
            bullets.append(bullet)
        elif mode == 'missile': #enemy AI will not shoot missiles
            global missiles
            closest_aim = -1 #equivalent to the distance from the target reticle to the enemy
            target=None
            for enemy in enemies+[player]:
                if enemy != self:
                    aim = self.craft.theta[0].dot(mymath.unit(enemy.craft.pos-self.craft.pos))
                    if closest_aim < aim and aim > 0.8:
                        target = enemy
                        closest_aim = aim
            missile = Missile(self.pos+60*mymath.unit(self.craft.v), self.craft.v+5*mymath.unit(self.craft.v), target)
            missiles.append(missile)
class Bullet(): #bullet class
    def __init__(self, pos, v):
        global world
        self.model = graphics.Model(world.ambient, world.lights, __file__[:-9]+'\\3D models\\bullet', False)
        world.models.append(self.model)
        self.pos = pos
        self.v = v
    def move(self): #move bullet
        global world
        self.pos += self.v
        self.model.pos = self.pos
        if mymath.norm(player.craft.pos - self.pos) > world.terrain.scale * world.terrain.distance: #despawn if too far
            try:
                bullets.remove(self)
                world.models.remove(self.model)
            except ValueError:
                pass
        elif self.get_altitude()<0: #hit ground
            v1 = ground_height(self.pos)
            v2 = ground_height(self.pos + array([[1], [0], [0]]))
            v3 = ground_height(self.pos + array([[0], [0], [1]]))
            normal = -expand_dims(mymath.unit(cross(array([1, v2-v1, 0]), array([0, v3-v1, 1]))), 1)
            self.hit_ground(normal)
    def get_altitude(self): #get altitude
        return self.pos[1][0]-ground_height(self.pos)
    def hit_ground(self, normal): #hit the ground, do not generate fragments, instead make dirt clumps.
        global world, bullets, fragments
        try:
            bullets.remove(self)
            world.models.remove(self.model)
        except ValueError:
            pass
        for i in range(4):
            fragments.append(Fragment('dirt clump', copy(self.pos), (self.v - 2*normal*normal.T.dot(self.v))*0.3+ (numpy.random.rand(3, 1)-0.5)*mymath.norm(self.v)*0.1))
    def hit(self, normal): #hit something other than the ground, generate fragments
        global world, bullets, fragments
        try:
            bullets.remove(self)
            world.models.remove(self.model)
        except ValueError:
            pass

        #create fragments upon collision
        for i in range(4):
            fragments.append(Fragment('bullet', copy(self.pos), self.v - 2*normal*normal.T.dot(self.v) + (numpy.random.rand(3, 1)-0.5)*mymath.norm(self.v)*0.5))

class Missile(): #missile class
    def __init__(self, pos, v, target):
        global world
        self.model = graphics.Model(world.ambient, world.lights, __file__[:-9]+'\\3D models\\missile', False)
        world.models.append(self.model)
        self.pos = pos
        self.v = v
        self.target = target
    def move(self): #move the missile
        global world
        if self.target!=None:self.v += mymath.unit(self.target.craft.pos - self.pos)*5 #thrust
        else: self.v += mymath.unit(self.v)*5
        self.v *= 0.9 #drag
        self.pos += self.v
        self.model.pos = self.pos
        side = cross(mymath.unit(self.v).T, array([[0, 1, 0]])).T #a column vector for the side of the missile
        self.model.theta = hstack([mymath.unit(self.v), -side, cross(mymath.unit(self.v).T, side.T).T ]) #rotate model
        if self.get_altitude()<0: #hit ground
            v1 = ground_height(self.pos)
            v2 = ground_height(self.pos + array([[1], [0], [0]]))
            v3 = ground_height(self.pos + array([[0], [0], [1]]))
            normal = -expand_dims(mymath.unit(cross(array([1, v2-v1, 0]), array([0, v3-v1, 1]))), 1)
            self.hit(normal)
        if self.target == None and mymath.norm(player.craft.pos - self.pos) > world.terrain.scale * world.terrain.distance: #despawn if too far
            global missiles
            try:
                missiles.remove(self)
                world.models.remove(self.model)
            except ValueError:
                pass
    def get_altitude(self): #get altitude
        return self.pos[1][0]-ground_height(self.pos)
    def hit(self, normal): #collide and explode
        global world, missiles, fragments
        try:
            missiles.remove(self)
            world.models.remove(self.model)
        except ValueError:
            pass

        sounds['explosion'].play()

        #create flames upon collision
        for i in range(10):
            fragments.append(Fragment('flames', copy(self.pos), self.v - 2*normal*normal.T.dot(self.v) + (numpy.random.rand(3, 1)-0.5)*mymath.norm(self.v)*0.5))

class Fragment(): #fragment class for display effects
    def __init__(self, filename, pos, v):
        global world
        self.model = graphics.Model(world.ambient, world.lights, __file__[:-9]+'\\3D models\\' + filename, False)
        world.models.append(self.model)
        self.pos = pos
        self.v = v
        self.time = 5 #fragments should disappear after 5 frames
    def move(self): #update/move
        self.time -= 1
        self.pos += self.v
        self.model.pos = self.pos
        if self.time < 0:
            global world, fragments
            fragments.remove(self)
            world.models.remove(self.model)

def setup(window): #this runs once, at the beginning of a game
    global jet, helicopter, tester #this game only uses the jet
    jet = {'linear drag':array([[0.01], [0.7], [0.3]]), 'angular drag':array([[0.15], [0.4], [0.6]]), 'linear accelleration':array([[0.2], [0.01], [0.04]]), 'angular accelleration':array([[0.015], [0.02], [0.1]])}
    helicopter = {'linear drag':array([[0.015], [0.04], [0.06]]), 'angular drag':array([[0.4], [0.7], [0.7]]), 'linear accelleration':array([[0], [0.1], [0.01]]), 'angular accelleration':array([[0.007], [0.1], [0.05]])}
    tester = {'linear drag':array([[0.01], [0.01], [0.01]]), 'angular drag':array([[0.4], [0.4], [0.4]]), 'linear accelleration':array([[0.2], [0.2], [0.2]]), 'angular accelleration':array([[0.007], [0.1], [0.1]])}

    global world #the world contains all 3D graphics imformation except for the sky's colour.
    world = graphics.WorldModel()
    world.ambient = (0.1, 0.1, 0.4) #blue ambient light
    world.lights.append(graphics.Light(direction=mymath.unit(array([[3], [-1], [1]])), colour=(1, 1, 1))) #white angled sunlight
    terrain_scale = 300 #set up the terrain
    terrain_state = {'detail':4, 'max_dist':8, 'smoothness':2, 'max_height':30, 'seed':random.randint(1, 1<<15)}
    world.terrain = graphics.Terrain(graphics.Mountains, terrain_state, (0.9, 0.4, 0.2), terrain_scale, 6, world.ambient, world.lights)

    global background_colour, player
    background_colour = (120, 150, 255) #blue sky
    player = Player(jet) #create player

    global enemies, bullets, fragments, missiles #create lists containing other objects
    enemies = []
    bullets = []
    fragments = []
    missiles = []

    global F, tau, mousehold
    F = zeros([3, 1]) #supposed to go from -1 to 1
    tau = zeros([3, 1]) #supposed to go from -1 to 1
    mousehold = True #hold the mouse in the center

    global kills, framecounter, shooting, missiles_left
    kills = 0 #count the kills
    framecounter = 0
    shooting = False
    missiles_left = 5 #the player is given 5 missiles

    global sounds #load all sounds
    sounds = {'shooting':pygame.mixer.Sound(__file__[:-9]+'\\sounds\\shooting.wav'),
              'explosion':pygame.mixer.Sound(__file__[:-9]+'\\sounds\\explosion.wav'),
              'hit1':pygame.mixer.Sound(__file__[:-9]+'\\sounds\\hit1.wav'),
              'hit2':pygame.mixer.Sound(__file__[:-9]+'\\sounds\\hit2.wav'),
              'hit3':pygame.mixer.Sound(__file__[:-9]+'\\sounds\\hit3.wav'),
              'hit4':pygame.mixer.Sound(__file__[:-9]+'\\sounds\\hit4.wav')}

def loop(window, events): #this runs as long as the game is running
    global world, player, enemies, bullets, fragments, missiles, F, tau, mousehold, framecounter, shooting, kills, sounds, missiles_left
    width = window.get_width()
    height = window.get_height()
    scroll = 0
    for event in events:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN: #record key pressing
            if event.key == K_w:
                F[0][0] = 1 #key pressing is linked to craft linear accelleration
            if event.key == K_s:
                F[0][0] = -2
            if event.key == K_a:
                F[2][0] = -1
            if event.key == K_d:
                F[2][0] = 1
            if event.key == K_LSHIFT:
                F[1][0] = -1
            if event.key == K_SPACE:
                F[1][0] = 1
            if event.key == K_LCTRL:
                mousehold = False
                pygame.mouse.set_visible(True)
        if event.type == KEYUP:
            if event.key == K_w or event.key == K_s:
                F[0][0] = 0
            if event.key == K_a or event.key == K_d:
                F[2][0] = 0
            if event.key == K_LSHIFT or event.key == K_SPACE:
                F[1][0] = 0
            if event.key == K_LCTRL:
                mousehold = True
                pygame.mouse.set_visible(False)
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 4: #scroll position is linked to craft angular velocity
                tau[0][0] += 1
            if event.button == 5:
                tau[0][0] -= 1
            if event.button == 1: #shoot bullet
                shooting = True
            if event.button == 3 and missiles_left > 0: #shoot missile
                missiles_left -= 1
                player.shoot('missile')
        if event.type == MOUSEBUTTONUP: #stop shooting bullets
            if event.button == 1:
                shooting = False
    if mousehold: #mouse position is linked to craft angular velocity
        pygame.mouse.set_pos((width/2, height/2))
        (x, y) = pygame.mouse.get_pos()
        tau[1][0] += (y-width/2)/750
        tau[2][0] -= (x-height/2)/750

    if framecounter >= 300 or len(enemies) == 0: #add an enemy every 300 frames
        enemies.append(Enemy(jet))
        framecounter = 1

    for obj in bullets+missiles+fragments: #update objects
        obj.move()
    for enemy in enemies: #update enemies
        enemy.update()
        enemy.automate()
        enemy.crashtest()
    player.craft.control(F, tau, player.max_a, player.max_alpha) #control the player
    if shooting:
        player.shoot('bullet')
        channel = pygame.mixer.find_channel()
        if channel != None:
            channel.play(sounds['shooting'])
            channel.fadeout(300)
        
    player.update() #update the player
    if player.crashtest(): #show 30 more frames on death
        sounds['explosion'].play()
        for frame in range(30):
            for obj in bullets+fragments+missiles:
                obj.move()
            for enemy in enemies:
                enemy.update()
                enemy.automate()
                enemy.crashtest()
            window.fill(background_colour)
            world.display(window, player.camera)
            pygame.display.update()
        return kills #finish game

    world.terrain.generate(vstack([player.craft.pos[0], player.craft.pos[2]]), world.ambient, world.lights) #generate terrain
    window.fill(background_colour)
    world.display(window, player.camera) #display the world
    draw_aim(window, player.craft) #draw the target reticle
    framecounter += 1
    return None

