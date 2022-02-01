# Simple 3d engine made using the https://www.youtube.com/c/javidx9 tutorial series
# Author: Eric Alfaro

import tkinter
from Math3D import *

class Triangle:
    def __init__(self, points):
        self.points = points
        self.base_color = [0] * 3
        self.lit_color = [0] * 3
        self.distance_from_camera = 0

    def get_normal(self):
        line1 = subtract_vector3d(self.points[1], self.points[0])
        line2 = subtract_vector3d(self.points[2], self.points[0])
        normal = normalize_vector3d(cross_product_vector3d(line1, line2))
        return normal

    def get_center(self):
        average = divide_vector3d(add_vector3d(add_vector3d(self.points[0], self.points[1]), self.points[2]), 3)
        return average

class Mesh:
    def __init__(self, triangles): self.triangles = triangles

class Camera:
    def __init__(self, position = None):
        if position == None: self.position = Vector3d()
        else: self.position = position
        self.look_direction = Vector3d(0, 0, 1)
        self.up_direction = Vector3d(0, 1, 0)
        self.yaw = 0
        self.pitch = 0
        self.roll = 0

class Light:
    def __init__(self, direction, color):
        self.direction = direction
        self.color = color

camera = Camera()
current_lights = []

#Input
def w_key(event):
    global camera
    camera.position = add_vector3d(camera.position, multiply_vector3d(camera.look_direction, .2))
def s_key(event):
    global camera
    camera.position = subtract_vector3d(camera.position, multiply_vector3d(camera.look_direction, .2))
def d_key(event):
    global camera
    camera.position = subtract_vector3d(camera.position, multiply_vector3d(cross_product_vector3d(camera.look_direction, camera.up_direction), .2))
def a_key(event):
    global camera
    camera.position = add_vector3d(camera.position, multiply_vector3d(cross_product_vector3d(camera.look_direction, camera.up_direction), .2))
def right_key(event):
    global camera
    camera.yaw -= .05
def left_key(event):
    global camera
    camera.yaw += .05
def space_key(event):
    global camera
    camera.position = subtract_vector3d(camera.position, multiply_vector3d(camera.up_direction, .2))
def ctrl_key(event):
    global camera
    camera.position = add_vector3d(camera.position, multiply_vector3d(camera.up_direction, .2))

#Creates empty window and binds input

window = tkinter.Tk()
window.geometry("600x400")

window.bind("<w>", w_key)
window.bind("<s>", s_key)
window.bind("<d>", d_key)
window.bind("<a>", a_key)
window.bind("<Right>", right_key)
window.bind("<Left>", left_key)
window.bind("<space>", space_key)
window.bind("<Control-Key>", ctrl_key)

canvas = tkinter.Canvas(window)
canvas.config(bg = "white")
canvas.config(width = 600, height= 400)

#Create projection matrix
aspect_ratio = canvas.winfo_reqheight()/canvas.winfo_reqwidth()
z_near = 0.1
z_far = 1000.0
fov = 90.0
projection_matrix = create_projection_matrix(aspect_ratio, fov, z_far, z_near)

#Loads .obj file and returns a Mesh
#.obj files need to be triangulated and with normals removed
def obj_to_triangles(file_path):
    points = []
    triangles = []
    for line in open(file_path, "r").readlines():
        line = line.split()
        if not line: continue
        elif line[0] == "v": points.append(Vector3d(float(line[1]), float(line[2]), float(line[3])))
        elif line[0] == "f":
            new_triangle = Triangle([points[int(line[1])-1], points[int(line[2])-1], points[int(line[3])-1]])
            new_triangle.normal = new_triangle.get_normal()
            triangles.append(new_triangle)
    return triangles

def clip_triangle_plane(plane_point, plane_normal, triangle):
    #Sorts points of triangle into lists depending on whether they are on the inside or outside of the plane
    inside_points = []
    outside_points = []
    for point in triangle.points:
        distance = dot_product_vector3d(plane_normal, point) - dot_product_vector3d(plane_normal, plane_point)
        if distance >= 0.0: inside_points.append(point)
        else: outside_points.append(point)

    #Clips triangles into smaller triangles
    clipped_triangles = []
    #The triangle is completely clipped
    if not len(inside_points): pass
    #The triangle is not clipped
    elif len(inside_points) == 3: clipped_triangles.append(triangle)
    #One smaller triangled is formed
    elif len(inside_points) == 1: clipped_triangles.append(Triangle([inside_points[0],
                                                                     intersect_plane_vector3d(plane_point, plane_normal, inside_points[0], outside_points[0]),
                                                                     intersect_plane_vector3d(plane_point, plane_normal, inside_points[0], outside_points[1])]))
    #Two new triangles are formed to give the illusion of a quadrilateral
    elif len(inside_points) == 2:
        clipped_triangles.append(Triangle([inside_points[0],
                                          inside_points[1],
                                          intersect_plane_vector3d(plane_point, plane_normal, inside_points[0], outside_points[0])]))
        clipped_triangles.append(Triangle([inside_points[1],
                                          clipped_triangles[0].points[2],
                                          intersect_plane_vector3d(plane_point, plane_normal, inside_points[1], outside_points[0])]))
    return clipped_triangles

def draw_triangles(triangles, normal_culling):
    global camera
    #Find look_direction, a unit vector that represents camera rotation, and offset it by the camera position to find the camera's target
    target = Vector3d(0, 0, 1)
    camera_rotation_matrix = create_y_rotation_matrix(camera.yaw)
    camera.look_direction = multiply_matrix_by_vector3d(camera_rotation_matrix, target)
    target = add_vector3d(camera.position, camera.look_direction)

    #Create a matrix that would point the camera at a target, and then invert it to create the view matrix
    #Multiplying every point by the view matrix rotates and translates the world in the way a camera being multiplied by the camera matrix would be expected to see
    camera_matrix = create_point_at_matrix(camera.position, target, camera.up_direction)
    view_matrix = create_look_at_matrix(camera_matrix)

    #Determine if triangle normal is facing camera and add it to a list to be sorted and drawn
    visible_triangles = []
    if not normal_culling:
        visible_triangles = [tri for tri in triangles]
    else:
        visible_triangles = [tri for tri in triangles if dot_product_vector3d(tri.normal, subtract_vector3d(tri.points[0], camera.position)) < 0]

    #Sort visible triangles by distance from camera
    for tri in visible_triangles:
        camera_to_point = subtract_vector3d(tri.get_center(), camera.position)
        tri.distance_from_camera = sqrt(dot_product_vector3d(camera_to_point, camera_to_point))
    visible_triangles.sort(key = lambda x: x.distance_from_camera, reverse = True)

    #Rasterize the triangles
    for tri in visible_triangles:
        #Light triangle
        fill_color = [0, 0, 0]
        for light in current_lights:
            #Find dot product between light ray and normal and ensures it doesn't subtract color from the fill_color
            light_strength = dot_product_vector3d(tri.normal, light.direction)
            if light_strength < 0: light_strength = 0

            #Averages base color and light color for the r, g, and b values of the fill_color
            #Checks for under and overflow
            for value in range(3):
                fill_color[value] = int(light.color[value] * light_strength/2 + tri.base_color[value] * light_strength/2)
                if fill_color[value] > 255: fill_color[value] = 255
                elif fill_color[value] < 0: fill_color[value] = 0

        #Convert from world space into view space
        viewed_triangle = Triangle([multiply_matrix_by_vector3d(view_matrix, tri.points[0]),
                                    multiply_matrix_by_vector3d(view_matrix, tri.points[1]),
                                    multiply_matrix_by_vector3d(view_matrix, tri.points[2])])

        #Clip triangles against the near plane
        clipped_triangles = clip_triangle_plane(Vector3d(0, 0, z_near), Vector3d(0, 0, 1), viewed_triangle)
        for tri in clipped_triangles:
            #Project triangle from 3d to 2d and give it the illusion of depth
            projected_triangle = Triangle([(multiply_matrix_by_vector3d(projection_matrix, tri.points[0])),
                                           (multiply_matrix_by_vector3d(projection_matrix, tri.points[1])),
                                           (multiply_matrix_by_vector3d(projection_matrix, tri.points[2]))])

            #Normalize into cartesian space and offset into screen
            for i in range(3):
                projected_triangle.points[i] = divide_vector3d(projected_triangle.points[i], Vector3d(projected_triangle.points[i].w,
                                                                                                      projected_triangle.points[i].w,
                                                                                                     projected_triangle.points[i].w))
                projected_triangle.points[i].x += 1.0
                projected_triangle.points[i].y += 1.0
                projected_triangle.points[i].x *= 0.5 * canvas.winfo_reqwidth()
                projected_triangle.points[i].y *= 0.5 * canvas.winfo_reqheight()

            #Clips triangles by edges of the screen
            triangles_to_clip = [projected_triangle]
            planes_checked = 0
            plane_points = [Vector3d(), Vector3d(0, canvas.winfo_reqheight(), 0), Vector3d(), Vector3d(canvas.winfo_reqwidth(), 0, 0)]
            plane_normals = [Vector3d(0, 1, 0), Vector3d(0, -1, 0), Vector3d(1, 0, 0), Vector3d(-1, 0, 0)]
            for i in range(4):
                new_triangles = []
                for triangle in triangles_to_clip:
                    triangles = clip_triangle_plane(plane_points[i], plane_normals[i], triangle)
                    if triangles: new_triangles += triangles
                    else: new_triangles.append(triangle)
                triangles_to_clip = new_triangles
            triangles_to_draw = triangles_to_clip

            #Put all x and y coordinates into a list and draw a triangle
            for tri in triangles_to_draw:
                polygon_coordinates = []
                for point in tri.points:
                    polygon_coordinates.append(point.x)
                    polygon_coordinates.append(point.y)
                if len(polygon_coordinates) > 6: print(1)
                canvas.create_polygon(polygon_coordinates, fill = ("#%02x%02x%02x" % tuple(fill_color)))
                #Uncomment for triangle outlines
                #canvas.create_line(polygon_coordinates, fill = "White")

#Test scene
my_mesh = Mesh(obj_to_triangles("../models/item.obj"))
for triangle in my_mesh.triangles:
    for i in range(3):
        if not triangle.points[i].transformed:
             triangle.points[i].transformed = True
             triangle.points[i].z += 3
main_light = Light(normalize_vector3d(Vector3d(.3, -1, -.3)), (255,255,255))
current_lights.append(main_light)

canvas.pack()

def main():
    while True:
        canvas.delete("all")
        draw_triangles(my_mesh.triangles, True)
        window.update()

if __name__ == "__main__":
    main()
