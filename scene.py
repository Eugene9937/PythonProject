import math

from OpenGL.GL import *
from OpenGL.GLU import *


class Scene:
    def __init__(self):
        self.model = None
        self.reset_view()

    def set_model(self, model):
        self.model = model
        self.reset_view()

    def reset_view(self):
        self.yaw = 35.0
        self.pitch = 25.0
        self.zoom = 1.0

    def rotate(self, dx, dy):
        self.yaw -= dx * 0.5
        self.pitch += dy * 0.5
        self.pitch = max(-85.0, min(85.0, self.pitch))

    def change_zoom(self, delta):
        if delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1

        self.zoom = max(0.05, min(20.0, self.zoom))

    def initialize_gl(self):
        glEnable(GL_DEPTH_TEST)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def draw(self, width, height):
        glViewport(0, 0, width, height)

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.01, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.apply_transform()

        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(1.5)

        self.model.draw()

    def apply_transform(self):
        center, radius = self.model.center_and_radius()

        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)

        distance = 4.0 / self.zoom

        x = distance * math.cos(pitch) * math.sin(yaw)
        y = -distance * math.cos(pitch) * math.cos(yaw)
        z = distance * math.sin(pitch)

        gluLookAt(
            x, y, z,
            0.0, 0.0, 0.0,
            0.0, 0.0, 1.0,
        )

        glScalef(1.0 / radius, 1.0 / radius, 1.0 / radius)
        glTranslatef(-center[0], -center[1], -center[2])