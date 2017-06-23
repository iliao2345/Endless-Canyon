#ENDLESS CANYON 3D Graphics Code
#Isaac Liao
#version 5.2
#23-05-2017
import math, pygame, numpy, sys, time
sys.path.append(__file__[:len(__file__) - 24] + '\\mymath')
from pygame.locals import*
from math import*
from numpy import*
import mymath_v01 as mymath

white = (255, 255, 255)

def combined_colour(colours): #multiplication of colours
    r = 1
    g = 1
    b = 1
    for colour in colours:
        r *= colour[0]
        g *= colour[1]
        b *= colour[2]
    return (r, g, b)

class Face(): #face class to display triangles
    def __init__(self, colour, indices, vertices=None):
        self.natural_colour = colour #reflectance
        self.colour = (0, 0, 0) #display colour with lights accounted for
        self.indices = indices #the index of the vertices within the model
        self.unrolled_indices = indices #the index of the unrolled vertices within the world model
        if vertices!=None:
            self.vertices = list(map(lambda i: vertices.T[i], indices))
        self.projected = [0, 0, 0]
    def get_colour(self, ambient, lights): #calculate the colour of the face
        self.colour = combined_colour([self.natural_colour, ambient]) #calculate ambient colour
        for light in lights: #calculate diffuse reflection
            diffuse = light.dir.T.dot(expand_dims(mymath.unit(cross(self.vertices[1] - self.vertices[0], self.vertices[1] - self.vertices[2])), axis=1)) #calculate the percent of light
            diffuse *= float(diffuse) * (diffuse > 0)
            addition = combined_colour([(diffuse, diffuse, diffuse), self.natural_colour, light.colour])
            self.colour = (self.colour[0] + addition[0], self.colour[1] + addition[1], self.colour[2] + addition[2])

#3D model class
class Model():
    def __init__(self, ambient, lights, filename=None, static=True):
        self.static = static #defines whether the model can move
        self.v = array([[], [], []], dtype=float) #vertices
        self.f = [] #faces, only triangles allowed
        self.e = [] #edges
        self.c = [] #colours
        #file read section
        if filename != None:
            with open(filename + '.txt', 'r', 1) as f:
                for line in f.readlines():
                    nums = line.split()
                    if nums[0] == 'v': #array of vertices
                        self.v = hstack([self.v, array([[float(nums[2])], [float(nums[3])], [float(nums[4])]]) ]) #index, x, y, z
                    if nums[0] == 'f': #list of faces
                        self.f.append(Face( self.c[int(nums[1])], [int(nums[2]),int(nums[3]),int(nums[4])], self.v )) #colour, v1, v2, v3
                    if nums[0] == 'c': #list of colours
                        self.c.append((float(nums[2]), float(nums[3]), float(nums[4]))) #index, r, g, b
            #read files here
            f.close()
        if static:
            for face in self.f:
                face.get_colour(ambient, lights)
        else:
            self.original_v = self.v
            self.theta = eye(3)
            self.pos = zeros([3, 1])
class Light(): #light class for lighting
    def __init__(self, direction=array([[0], [-1], [0]], dtype=float), colour=(1, 1, 1)):
        self.dir = direction
        self.colour = colour
class Camera(): #camera to display the world from
    def __init__(self):
        self.pos = array([[0], [0], [0]], dtype=float)
        self.theta = mymath.rot_mat(array([[0], [0], [0]], dtype=float), 'euler')
    def move(self, dx): #move relative to the camera
        self.pos += self.theta.dot(dx)
    def turn(self, theta):
        self.theta = self.theta.dot(theta)
class Terrain(): #terrain class
    def __init__(self, func, func_state, colour, scale, distance, ambient, lights, mode='land'): #special function for creating height given an xy coord.
        if mode == 'land': #land means a heightmap
            self.func = func #this is the height function of the terrain
        self.func_state = func_state #func_state is the details of the terrain
        if mode == 'land':
            self.pos = array([[0], [0]]) #center of loaded area
        self.distance = distance #the maximum distance at which chunks load
        self.mode = mode
        self.colour = colour
        self.faces = zeros([self.distance*2, self.distance*2], dtype=object)
        self.unrolled_faces = [] #this is faces but in a list
        self.vertices = array([[], [], []], dtype=float)
        self.scale = scale
        self.initial_load(ambient, lights)
        self.get_unrolled_faces()

    def get_unrolled_faces(self): #unroll the faces
        unrolled_faces = []
        for pair in list(self.faces):
            unrolled_faces.append(pair[0])
            unrolled_faces.append(pair[1])
        
    def initial_load(self, ambient, lights): #load surrounding terrain
        self.faces = zeros([self.distance*2, self.distance*2], dtype=object)
        self.unrolled_faces = []
        self.verticies = array([[], [], []], dtype=float)
        if self.mode == 'land':
            self.loaded = zeros([2*self.distance+1, 2*self.distance+1])
            L = 2*self.distance+1
            for x in range(L):
                for z in range(L):
                    self.loaded[x][z] = self.func(x-self.distance, z-self.distance, self.func_state)
                    
                    self.vertices = hstack([self.vertices, self.scale*array([[self.pos[0][0] - self.distance + x], #get the vertex coordinate
                                          [self.loaded[x][z]],
                                          [self.pos[1][0] - self.distance + z]], dtype=float) ])
                    if x > 0 and z > 0: #create the faces
                        face = Face(self.colour, [z + x*L, z-1 + x*L, z-1+(x-1)*L], self.vertices)
                        face.get_colour(ambient, lights)
                        self.faces[x-1][z-1] = [face]
                        self.unrolled_faces.append(face)
                        face = Face(self.colour, [z + x*L, z-1+(x-1)*L, z + (x-1)*L], self.vertices)
                        face.get_colour(ambient, lights)
                        self.faces[x-1][z-1].append(face)
                        self.unrolled_faces.append(face)
    def generate(self, pos, ambient, lights): #generate new terrain around pos, the new center
        diff = (pos/self.scale).astype(int) - self.pos
        if (diff == 0).all():
            pass
        elif (abs(diff > self.distance)).all(): #totally different area
            self.initial_load(ambient, lights)
        else: #move the faces and vertices
            if self.mode == 'land':
                L = self.distance*2+1
                dx = diff[0][0]
                dz = diff[1][0]
                
                if dx > 0: # delete faces which were moved away from
                    for x in range(dx):
                        for z in range(L-1):
                            self.faces[x][z] = []
                            self.loaded[x][z] = 0
                if dx < 0:
                    for x in range(dx):
                        for z in range(L-1):
                            self.faces[L-2-x][z] = []
                            self.loaded[L-1-x][z] = 0
                if dz > 0:
                    for x in range(L-1):
                        for z in range(dz):
                            self.faces[x][z] = []
                            self.loaded[x][z] = 0
                if dz < 0:
                    for x in range(L-1):
                        for z in range(dz):
                            self.faces[x][L-2-z] = []
                            self.loaded[x][L-1-z] = 0
                
                self.faces = roll(roll(self.faces, -dx, 0), -dz, 1)
                self.loaded = roll(roll(self.loaded, -dx, 0), -dz, 1)
                self.unrolled_faces = []
                for x in range(L): #generate new faces
                    for z in range(L):
                        if self.loaded[x][z] == 0:
                            self.loaded[x][z] = self.func(x-self.distance + int(pos[0]/self.scale), z-self.distance + int(pos[1]/self.scale), self.func_state)
                        self.vertices[0][z + x*L] = (int(pos[0][0]/self.scale)+x-self.distance)*self.scale
                        self.vertices[1][z + x*L] = self.loaded[x][z]*self.scale
                        self.vertices[2][z + x*L] = (int(pos[1][0]/self.scale)+z-self.distance)*self.scale
                        if x > 0 and z > 0: #create the faces
                            face = Face(self.colour, [z + x*L, z-1 + x*L, z-1+(x-1)*L], self.vertices)
                            face.get_colour(ambient, lights)
                            self.faces[x-1][z-1] = [face]
                            self.unrolled_faces.append(face)
                            face = Face(self.colour, [z + x*L, z-1+(x-1)*L, z + (x-1)*L], self.vertices)
                            face.get_colour(ambient, lights)
                            self.faces[x-1][z-1].append(face)
                            self.unrolled_faces.append(face)
                self.get_unrolled_faces()
        self.pos = (pos/self.scale).astype(int)

#this is a height function whose graph appears mountainous
def Mountains(x, y, state): #land type terrain function
    detail = state['detail'] #the level of detail used
    max_dist = state['max_dist'] #the maximum distance 2 points can affect each other from
    smoothness = state['smoothness'] # the rate at which features shrink with each halving of width, must be higher than 2
    max_height = state['max_height'] # the maximum allowable mountain height
    seed = state['seed'] #the world seed
    first_height = max_height * (1 - 1/smoothness)
    
    total = 0
    for accuracy in range(detail): #accuracy is the iteration while making mountains
        dist = max_dist / 2 ** accuracy
        height = first_height / smoothness ** accuracy
        
        pos = array([[x], [y]])

        bot_left = pos // dist * dist#positions
        bot_right = pos // dist * dist + array([[dist], [0]])
        top_left = pos // dist * dist + array([[0], [dist]])
        top_right = pos // dist * dist + array([[dist], [dist]])

        bot_left = mymath.randomize([bot_left, accuracy, seed]) #heights (0 to 1)
        bot_right = mymath.randomize([bot_right, accuracy, seed])
        top_left = mymath.randomize([top_left, accuracy, seed])
        top_right = mymath.randomize([top_right, accuracy, seed])
        
        bot = mymath.interpolate(pos[0][0]%dist, 0, dist, bot_left, bot_right)
        top = mymath.interpolate(pos[0][0]%dist, 0, dist, top_left, top_right)
        total += mymath.interpolate(pos[1][0]%dist, 0, dist, bot, top) * height
    return total

#the world class holds all 3D information about the world
class WorldModel():
    def __init__(self):
        self.models = []
        self.terrain = None
        self.lights = []
        self.ambient = (0.5, 0.5, 0.5)
        
    def plot(self, pos, theta, fov): #this projects the points from 3D to 2D
        rotated = theta.T.dot(pos)
        try:
            projection = vstack([vstack([rotated[2], rotated[1]]) / rotated[0] / fov, rotated[0]])
            return projection #x, y, depth
        except AttributeError:
            return 'error' #this happens if the depth after projection is 0
    
    def display(self, window, camera, fov=1): #display the world
        
        #process models/terrain
        form_sum = 0 #models
        model_faces = []
        terrain_faces = []
        model_vertices = []
        terrain_vertices = []
        for model in self.models: #indices must be adjusted
            if not model.static: #recalculate colour of moveable faces
                model.v = model.pos + model.theta.dot(model.original_v) #calculate vertices
                for face in model.f: face.vertices = list(map(lambda index: model.v.T[index], face.indices)); #roll vertices
                for face in model.f: face.get_colour(self.ambient, self.lights); #calculate colour
            model_vertices.append(model.v) #unroll vertices
            for face in model.f:
                face.unrolled_indices = list(map(lambda i: i+form_sum, face.indices))
            model_faces += model.f
            form_sum += model.v.shape[1]
        if self.terrain != None:
            for face in self.terrain.unrolled_faces:
                #print(self.terrain.faces)
                face.unrolled_indices = list(map(lambda i: i+form_sum, face.indices))
            terrain_faces = self.terrain.unrolled_faces
            terrain_vertices = self.terrain.vertices
        
        #project points onto plane
        proj = self.plot(hstack(model_vertices+[terrain_vertices]) - camera.pos, camera.theta, fov)
        if proj == 'error':
            return

        #screen fit
        screen_fit_matrix = array([[window.get_width() / 2, window.get_height() / 2, 0, 0], [window.get_height() / 2, 0, -window.get_height() / 2, 0], [0, 0, 0, 1]])
        try:
            screen_fitted = screen_fit_matrix.dot(mymath.add_bias(proj))
        except AttributeError:
            return #this error is caused by unknown reasons; it doesn't seem to damage the functionality of the module.

        #delete faces facing away from the camera, where points are listed in clockwise order
        all_faces = [face for face in model_faces+terrain_faces if expand_dims(cross(face.vertices[0]-face.vertices[1], face.vertices[1]-face.vertices[2]), axis=0).dot(expand_dims(face.vertices[0], axis=1)-camera.pos) < 0]

        #roll vertices into faces by replacing indices with their respective values
        try:
            for face in all_faces:
                face.projected = list(map(lambda i: screen_fitted[:,i], face.unrolled_indices))
        except AttributeError: ###########################fix this################################
            return
        
        #sort from far to close
        all_faces.sort(key = lambda face: -sum(list(map(lambda vertex: vertex[2], face.projected))))

        #draw faces
        for face in all_faces:
            colour = combined_colour([face.colour, white])
            colour = tuple(map(lambda component: component*(component<=255)+255*(component>255), colour)) #cap colour components at 255
            if face.projected[0][2] > 0 or face.projected[1][2] > 0 or face.projected[2][2] > 0: #if some of the triangle is on the screen
                polygon = [] #list of vertices defining the polygon to be used
                for (v1, v2) in [(0, 1), (1, 2), (2, 0)]: #iterate through the edges
                    if face.projected[v1][2] > 0 and face.projected[v2][2] > 0: #both are in front
                        polygon.append(tuple(face.projected[v1][:2])) #the point
                    elif face.projected[v1][2] >= 0 and face.projected[v2][2] <= 0: #front to behind
                        polygon.append(tuple(face.projected[v1][:2])) #the point
                        shortened = mymath.unit(face.projected[v1][:2]-face.projected[v2][:2])*window.get_width()+face.projected[v1][:2] #add this point to compensate for points behind the camera
                        polygon.append(tuple(shortened))
                    elif face.projected[v1][2] <= 0 and face.projected[v2][2] >= 0: #behind to front
                        shortened = mymath.unit(face.projected[v2][:2]-face.projected[v1][:2])*window.get_width()+face.projected[v2][:2] #add this point to compensate for points behind the camera
                        polygon.append(tuple(shortened))
                try:
                    if max(map(lambda coord: hypot(coord[0]-window.get_width()/2, coord[1]-window.get_height()/2), polygon)) < window.get_width()*300:
                        pygame.draw.polygon(window, (int(colour[0]), int(colour[1]), int(colour[2])), polygon)
                except TypeError:
                    pass
