import math
from enum import Enum

import glm
from OpenGL.GL import *

from shaders import make_basic_shader, make_solid_shader, make_texture_shader


class RenderMode(Enum):
    WIREFRAME = 1
    SOLID = 2
    TEXTURED = 3


class Scene:
    def __init__(self):
        self.model = None
        self.mode = RenderMode.SOLID

        self.basic_shader = None
        self.solid_shader = None
        self.texture_shader = None

        self.reset_view()

    def set_model(self, model):
        self.model = model
        self.reset_view()

        if self.mode == RenderMode.TEXTURED and not self.has_texture():
            self.mode = RenderMode.SOLID

    def set_mode(self, mode):
        self.mode = mode

    def has_texture(self):
        return self.model is not None and self.model.has_texture()

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

        self.basic_shader = make_basic_shader()
        self.solid_shader = make_solid_shader()
        self.texture_shader = make_texture_shader()

    def draw(self, width, height):
        glViewport(0, 0, width, height)

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        model, view, projection = self.make_matrices(width, height)

        if self.mode == RenderMode.WIREFRAME:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            shader = self.basic_shader
        elif self.mode == RenderMode.SOLID:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            shader = self.solid_shader
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            shader = self.texture_shader

        shader.use()
        shader.set_mat4("model", model)
        shader.set_mat4("view", view)
        shader.set_mat4("projection", projection)

        if self.mode == RenderMode.SOLID:
            shader.set_vec3("color", glm.vec3(0.7, 0.7, 0.8))
            shader.set_vec3("light_dir", glm.vec3(0.4, 0.6, 1.0))
        elif self.mode == RenderMode.TEXTURED:
            shader.set_vec3("light_dir", glm.vec3(0.4, 0.6, 1.0))
            shader.set_int("texture_image", 0)
            self.model.bind_texture()

        self.model.draw()

    def make_matrices(self, width, height):
        center, radius = self.model.center_and_radius()

        model = glm.mat4(1.0)
        model = glm.scale(model, glm.vec3(1.0 / radius))
        model = glm.translate(model, glm.vec3(-center[0], -center[1], -center[2]))

        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)

        distance = 4.0 / self.zoom

        eye = glm.vec3(
            distance * math.cos(pitch) * math.sin(yaw),
            -distance * math.cos(pitch) * math.cos(yaw),
            distance * math.sin(pitch),
        )

        view = glm.lookAt(
            eye,
            glm.vec3(0.0, 0.0, 0.0),
            glm.vec3(0.0, 0.0, 1.0),
        )

        projection = glm.perspective(
            math.radians(45.0),
            width / height,
            0.01,
            100.0,
        )

        return model, view, projection