import ctypes
import math
import struct
from pathlib import Path

from OpenGL.GL import *


class Model:
    def __init__(self, vertices, triangles):
        self.vertices = vertices
        self.triangles = triangles

        self.vbo = None
        self.ibo = None
        self.index_count = 0

    @classmethod
    def from_faces(cls, vertices, faces):
        triangles = []

        for face in faces:
            first = face[0]

            for i in range(1, len(face) - 1):
                triangles.append((first, face[i], face[i + 1]))

        return cls(vertices, triangles)

    def upload(self):
        data = []
        for x, y, z in self.vertices:
            data.extend((x, y, z))

        indices = []
        for a, b, c in self.triangles:
            indices.extend((a, b, c))

        self.index_count = len(indices)

        vertices = (ctypes.c_float * len(data))(*data)
        indices = (ctypes.c_uint * len(indices))(*indices)

        self.vbo = glGenBuffers(1)
        self.ibo = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            ctypes.sizeof(vertices),
            vertices,
            GL_STATIC_DRAW,
        )

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            ctypes.sizeof(indices),
            indices,
            GL_STATIC_DRAW,
        )

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def draw(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)

        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, ctypes.c_void_p(0))

        glDrawElements(
            GL_TRIANGLES,
            self.index_count,
            GL_UNSIGNED_INT,
            ctypes.c_void_p(0),
        )

        glDisableClientState(GL_VERTEX_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def destroy(self):
        if self.vbo is not None:
            glDeleteBuffers(1, [self.vbo])
            self.vbo = None

        if self.ibo is not None:
            glDeleteBuffers(1, [self.ibo])
            self.ibo = None

        self.index_count = 0

    def center_and_radius(self):
        xs, ys, zs = zip(*self.vertices)

        center = (
            (min(xs) + max(xs)) / 2.0,
            (min(ys) + max(ys)) / 2.0,
            (min(zs) + max(zs)) / 2.0,
        )

        radius = 0.0

        for vertex in self.vertices:
            radius = max(radius, math.dist(vertex, center))

        return center, max(radius, 1e-6)


def load_model(path):
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".obj":
        return load_obj(path)

    if suffix == ".stl":
        return load_stl(path)

    raise ValueError


def load_obj(path):
    vertices = []
    faces = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.split()

            if not parts or parts[0].startswith("#"):
                continue

            if parts[0] == "v":
                x, y, z = map(float, parts[1:4])
                vertices.append((x, y, z))

            elif parts[0] == "f":
                face = []

                for item in parts[1:]:
                    index = int(item.split("/")[0])

                    if index > 0:
                        index -= 1
                    else:
                        index = len(vertices) + index

                    face.append(index)

                if len(face) >= 3:
                    faces.append(tuple(face))

    if not vertices or not faces:
        raise ValueError

    return Model.from_faces(vertices, faces)


def load_stl(path):
    data = path.read_bytes()

    if is_binary_stl(data):
        return load_binary_stl(data)

    return load_ascii_stl(data.decode("utf-8"))


def is_binary_stl(data):
    if len(data) < 84:
        return False

    n = struct.unpack_from("<I", data, 80)[0]
    size = 84 + n * 50

    return len(data) == size


def load_binary_stl(data):
    vertices = []
    faces = []

    n = struct.unpack_from("<I", data, 80)[0]
    offset = 84

    for _ in range(n):
        offset += 12

        coords = struct.unpack_from("<9f", data, offset)
        offset += 36

        offset += 2

        face = []

        for i in range(0, 9, 3):
            vertex = coords[i], coords[i + 1], coords[i + 2]

            face.append(len(vertices))
            vertices.append(vertex)

        faces.append(tuple(face))

    if not vertices or not faces:
        raise ValueError

    return Model.from_faces(vertices, faces)


def load_ascii_stl(text):
    vertices = []
    faces = []
    face = []

    for line in text.splitlines():
        parts = line.split()

        if len(parts) == 4 and parts[0].lower() == "vertex":
            x, y, z = map(float, parts[1:4])

            face.append(len(vertices))
            vertices.append((x, y, z))

            if len(face) == 3:
                faces.append(tuple(face))
                face = []

    if not vertices or not faces:
        raise ValueError

    return Model.from_faces(vertices, faces)