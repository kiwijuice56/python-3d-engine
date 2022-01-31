#Holds functions for vector math, matrix math, and some functions from the built-in math module
from math import sqrt, tan, cos, sin

class Vector2d:
    def __init__(self, u = None, v = None):
        if u == None: self.u = 0.0
        else: self.u = u
        if v == None: self.v = 0.0
        else: self.v = v

class Vector3d:
    def __init__(self, x = None, y = None, z = None, w = None):
        if x == None: self.x = 0.0
        else: self.x = x
        if y == None: self.y = 0.0
        else: self.y = y
        if z == None: self.z = 0.0
        else: self.z = z
        if w == None: self.w = 1.0
        else: self.w = w
        #Triangles hold references to points(Vector3ds)
        #Because of this, triangles may share the same point in memory
        #Transformations on triangles are done by iterating through every point of a triangle and transforming it
        #This means shared points can be transformed many times, destroying the model
        #This boolean is toggled during transformations to prevent this
    transformed = False

def add_vector3d(vector, addend):
    output_vector = Vector3d()
    if type(addend) is Vector3d:
        output_vector.x = vector.x + addend.x
        output_vector.y = vector.y + addend.y
        output_vector.z = vector.z + addend.z
    elif type(addend) is int or type(addend) is float:
        output_vector.x = vector.x + addend
        output_vector.y = vector.y + addend
        output_vector.z = vector.z + addend
    return output_vector

def subtract_vector3d(vector, subtrahend):
    output_vector = Vector3d()
    if type(subtrahend) is Vector3d:
        output_vector.x = vector.x - subtrahend.x
        output_vector.y = vector.y - subtrahend.y
        output_vector.z = vector.z - subtrahend.z
    elif type(subtrahend) is int or type(subtrahend) is float:
        output_vector.x = vector.x - subtrahend
        output_vector.y = vector.y - subtrahend
        output_vector.z = vector.z - subtrahend
    return output_vector

def divide_vector3d(vector, divisor):
    output_vector = Vector3d()
    if type(divisor) is Vector3d:
        if not divisor.x == 0: output_vector.x = vector.x/divisor.x
        if not divisor.y == 0: output_vector.y = vector.y/divisor.y
        if not divisor.z == 0: output_vector.z = vector.z/divisor.z
    elif type(divisor) is int or type(divisor) is float:
        if not divisor == 0:
            output_vector.x = vector.x/divisor
            output_vector.y = vector.y/divisor
            output_vector.z = vector.z/divisor
    return output_vector

def multiply_vector3d(vector, multiplier):
    output_vector = Vector3d()
    if type(multiplier) is Vector3d:
        output_vector.x = vector.x * multiplier.x
        output_vector.y = vector.y * multiplier.y
        output_vector.z = vector.z * multiplier.z
    elif type(multiplier) is int or type(multiplier) is float:
        output_vector.x = vector.x * multiplier
        output_vector.y = vector.y * multiplier
        output_vector.z = vector.z * multiplier
    return output_vector

def normalize_vector3d(vector):
    vector_length = sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z)
    output_vector = divide_vector3d(vector, Vector3d(vector_length, vector_length, vector_length))
    return output_vector

def cross_product_vector3d(vector1, vector2):
    output_vector = Vector3d()
    output_vector.x = vector1.y * vector2.z - vector1.z * vector2.y
    output_vector.y = vector1.z * vector2.x - vector1.x * vector2.z
    output_vector.z = vector1.x * vector2.y - vector1.y * vector2.x
    return output_vector

def dot_product_vector3d(vector1, vector2):
    return vector1.x * vector2.x + vector1.y * vector2.y + vector1.z * vector2.z

def intersect_plane_vector3d(plane_point, plane_normal, line_start, line_end):
    plane_d = dot_product_vector3d(plane_normal, plane_point)
    ad = dot_product_vector3d(line_start, plane_normal)
    bd = dot_product_vector3d(line_end, plane_normal)
    t = (plane_d - ad) / (bd - ad)
    line = subtract_vector3d(line_end, line_start)
    line_to_intersection = multiply_vector3d(line, t)
    return add_vector3d(line_start, line_to_intersection)

class Matrix4x4:
    def __init__(self, data): self.data = data

def multiply_matrix_by_vector3d(matrix, vector):
    output_vector = Vector3d(vector.x * matrix.data[0][0] + vector.y * matrix.data[1][0] + vector.z * matrix.data[2][0] + vector.w * matrix.data[3][0],
                             vector.x * matrix.data[0][1] + vector.y * matrix.data[1][1] + vector.z * matrix.data[2][1] + vector.w * matrix.data[3][1],
                             vector.x * matrix.data[0][2] + vector.y * matrix.data[1][2] + vector.z * matrix.data[2][2] + vector.w * matrix.data[3][2],
                             vector.x * matrix.data[0][3] + vector.y * matrix.data[1][3] + vector.z * matrix.data[2][3] + vector.w * matrix.data[3][3])
    return output_vector


def create_y_rotation_matrix(radians):
    output_matrix = Matrix4x4([[cos(radians), 0, sin(radians), 0],
                               [0, 1, 0, 0],
                               [-1 * sin(radians), 0, cos(radians), 0],
                               [0, 0, 0, 1]])
    return output_matrix

def create_projection_matrix(aspect_ratio, fov, z_far, z_near):
    fov_scaling = 1.0/tan(fov * 0.5 / 180.0 * 3.14159)
    projection_matrix = Matrix4x4([[aspect_ratio * fov_scaling, 0, 0, 0],
                                   [0, fov_scaling, 0, 0],
                                   [0, 0, z_far / (z_far - z_near), 1.0],
                                   [0, 0, (-z_far * z_near) / (z_far - z_near), 0]])
    return projection_matrix

def create_point_at_matrix(position, target, up):
    new_forward = normalize_vector3d(subtract_vector3d(target, position))
    up_projection_on_new_forward = multiply_vector3d(new_forward, dot_product_vector3d(up, new_forward))
    new_up = normalize_vector3d(subtract_vector3d(up, up_projection_on_new_forward))
    new_right = cross_product_vector3d(new_up, new_forward)
    output_matrix = Matrix4x4([[new_right.x, new_right.y, new_right.z, 0],
                               [new_up.x, new_up.y, new_up.z, 0],
                               [new_forward.x, new_forward.y, new_forward.z, 0],
                               [position.x, position.y, position.z, 1]])
    return output_matrix

def create_look_at_matrix(matrix):
    output_matrix = Matrix4x4([[matrix.data[0][0], matrix.data[1][0], matrix.data[2][0], 0],
                               [matrix.data[0][1], matrix.data[1][1], matrix.data[2][1], 0],
                               [matrix.data[0][2], matrix.data[1][2], matrix.data[2][2], 0],
                               [0, 0, 0, 0]])
    output_matrix.data[3][0] = -(matrix.data[3][0] * output_matrix.data[0][0] + matrix.data[3][1] * output_matrix.data[1][0] + matrix.data[3][2] * output_matrix.data[2][0])
    output_matrix.data[3][1] = -(matrix.data[3][0] * output_matrix.data[0][1] + matrix.data[3][1] * output_matrix.data[1][1] + matrix.data[3][2] * output_matrix.data[2][1])
    output_matrix.data[3][2] = -(matrix.data[3][0] * output_matrix.data[0][2] + matrix.data[3][1] * output_matrix.data[1][2] + matrix.data[3][2] * output_matrix.data[2][2])
    return output_matrix

