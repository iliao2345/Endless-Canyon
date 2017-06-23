#ENDLESS CANYON Special Math Code
#Isaac Liao
#version 0.1
#02-05-2017
from math import*
from numpy import*

def add_bias(x): #add 1's to the top row of a matrix
    return vstack([ones([1, x.shape[1]]), x])

def randomize(x): #returns a seemingly random number from 0 to 1 from seed x. x is a number or a tree of numbers.
    a = 479027 #prime
    b = 1438891 #prime
    c = 2**16-1
    if type(x) == list or type(x) == ndarray:
        total = 0
        for i in range(len(x)):
            total += randomize(x[i] + i + e)
        return randomize(total)
    scaled = int(b*x)&c
    return ((scaled<<11|scaled>>5)&c) / c

def interpolate(value, old1, old2, new1, new2): #map value from range1 to range2
    return (value-old1)/(old2-old1)*(new2-new1)+new1

#create a rotation matrix
def rot_mat(theta, mode): #roll, then pitch, then yaw (x, z, y)
    if mode == '2d':
        return array([[cos(theta), -sin(theta)], [sin(theta), cos(theta)]])
    if mode == 'euler':
        roll_mat = array([[1, 0, 0], [0, cos(theta[0][0]), -sin(theta[0][0])], [0, sin(theta[0][0]), cos(theta[0][0])]])
        pitch_mat = array([[cos(theta[1][0]), -sin(theta[1][0]), 0], [sin(theta[1][0]), cos(theta[1][0]), 0], [0, 0, 1]])
        yaw_mat = array([[cos(theta[2][0]), 0, -sin(theta[2][0])], [0, 1, 0], [sin(theta[2][0]), 0, cos(theta[2][0])]])
        return yaw_mat.dot(pitch_mat.dot(roll_mat)) #gives the rotation matrix from the rotation vector
    if mode == 'rotation vector': #axis and angle
        n = norm(theta) #determines angle
        if n == 0:
            return eye(3)
        u = theta / n #determines axis
        c = cos(n) #https://en.wikipedia.org/wiki/Rotation_matrix#Axis_and_angle
        s = sin(n)
        x = u[0][0]
        y = u[1][0]
        z = u[2][0]
        half = u.dot(u.T)*(1-c) #half of the calculations done
        return (half + array([[c, -z*s, y*s], [z*s, c, -x*s], [-y*s, x*s, c]])).T

#create a special skew symmetric matrix
def skew_symmetric(v): # v cross x = output dot x
    x = v[0][0]
    y = v[1][0]
    z = v[2][0]
    return array([[0, -z, y], [z, 0, -x], [-y, x, 0]])

def xnor(a, b):
    return a == b

def xor(a, b):
    return a != b

#vector norm
def norm(a):
    return sqrt(sum(a**2))

#return a unit vector
def unit(a):
    return a / norm(a)

#returns the closest point on line segment bc to a
def closestpoint(a, b, c):
    db = unit(c-b)
    pos = b + (db.T.dot(a)-db.T.dot(b))*db
    if b.T.dot(db) > a.T.dot(db):
        pos = b
    elif c.T.dot(db) < a.T.dot(db):
        pos = c
    return pos

