import ctypes
import logging
import math
import struct
from pathlib import Path

from PIL import Image
from OpenGL.GL import *


logger = logging.getLogger(__name__)


class Model:
    def __init__(self, vertices, triangles, texcoords=None, tex_triangles=None, texture_path=None):
        self.vertices = vertices
        self.triangles = triangles
        self.texcoords = texcoords
        self.tex_triangles = tex_triangles
        self.texture_path = texture_path

        self.vbo = None
        self.nbo = None
        self.tbo = None
        self.texture_id = None
        self.vertex_count = 0

    @classmethod
    def from_faces(cls, vertices, faces, texcoords=None, tex_faces=None, texture_path=None):
        triangles = []
        tex_triangles = [] if tex_faces is not None else None

        for face_id, face in enumerate(faces):
            first = face[0]

            for i in range(1, len(face) - 1):
                triangles.append((first, face[i], face[i + 1]))

                if tex_triangles is not None:
                    tex_face = tex_faces[face_id]
                    tex_triangles.append((tex_face[0], tex_face[i], tex_face[i + 1]))

        return cls(vertices, triangles, texcoords, tex_triangles, texture_path)

    def has_texture(self):
        return self.texture_path is not None and self.texcoords is not None and self.tex_triangles is not None

    def upload(self):
        data = []
        normal_data = []
        tex_data = []

        for i, (a, b, c) in enumerate(self.triangles):
            p0 = self.vertices[a]
            p1 = self.vertices[b]
            p2 = self.vertices[c]

            normal = self.triangle_normal(p0, p1, p2)

            for p in (p0, p1, p2):
                data.extend(p)
                normal_data.extend(normal)

            if self.tex_triangles is not None:
                for index in self.tex_triangles[i]:
                    tex_data.extend(self.texcoords[index])

        self.vertex_count = len(data) // 3

        self.vbo = self.create_buffer(data)
        self.nbo = self.create_buffer(normal_data)

        if self.tex_triangles is not None:
            self.tbo = self.create_buffer(tex_data)
            self.texture_id = self.load_texture(self.texture_path)

    def create_buffer(self, data):
        values = (ctypes.c_float * len(data))(*data)
        buffer = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, buffer)
        glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(values), values, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        return buffer

    def draw(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        glBindBuffer(GL_ARRAY_BUFFER, self.nbo)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        if self.tbo is not None:
            glBindBuffer(GL_ARRAY_BUFFER, self.tbo)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)

        if self.tbo is not None:
            glDisableVertexAttribArray(2)

        glDisableVertexAttribArray(1)
        glDisableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def bind_texture(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

    def destroy(self):
        if self.vbo is not None:
            glDeleteBuffers(1, [self.vbo])
            self.vbo = None

        if self.nbo is not None:
            glDeleteBuffers(1, [self.nbo])
            self.nbo = None

        if self.tbo is not None:
            glDeleteBuffers(1, [self.tbo])
            self.tbo = None

        if self.texture_id is not None:
            glDeleteTextures(1, [self.texture_id])
            self.texture_id = None

        self.vertex_count = 0

    def triangle_normal(self, p0, p1, p2):
        ux = p1[0] - p0[0]
        uy = p1[1] - p0[1]
        uz = p1[2] - p0[2]

        vx = p2[0] - p0[0]
        vy = p2[1] - p0[1]
        vz = p2[2] - p0[2]

        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx

        length = math.sqrt(nx * nx + ny * ny + nz * nz)

        if length == 0:
            return 0.0, 0.0, 1.0

        return nx / length, ny / length, nz / length

    def load_texture(self, path):
        image = Image.open(path).convert("RGBA")
        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        width, height = image.size
        data = image.tobytes()

        texture = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, texture)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            data,
        )

        glBindTexture(GL_TEXTURE_2D, 0)

        logger.info("texture: %s (%sx%s)", path, width, height)

        return texture

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

    logger.info("model: %s", path)

    if suffix == ".obj":
        return load_obj(path)

    if suffix == ".stl":
        return load_stl(path)

    raise ValueError


def load_obj(path):
    vertices = []
    texcoords = []
    faces = []
    tex_faces = []

    materials = {}
    texture_path = None
    has_mtl = False

    with open(path, "r", encoding="utf-8-sig") as file:
        for line in file:
            parts = line.split()

            if not parts or parts[0].startswith("#"):
                continue

            if parts[0] == "mtllib":
                has_mtl = True
                for name in parts[1:]:
                    mtl_path = path.parent / name
                    materials.update(load_mtl(mtl_path))
            elif parts[0] == "usemtl":
                if parts[1] in materials and texture_path is None:
                    texture_path = materials[parts[1]]
            elif parts[0] == "v":
                x, y, z = map(float, parts[1:4])
                vertices.append((x, y, z))
            elif parts[0] == "vt":
                u, v = map(float, parts[1:3])
                texcoords.append((u, v))
            elif parts[0] == "f":
                face = []
                tex_face = []

                for item in parts[1:]:
                    values = item.split("/")

                    index = int(values[0])
                    if index > 0:
                        index -= 1
                    else:
                        index = len(vertices) + index

                    face.append(index)

                    if len(values) > 1 and values[1]:
                        tex_index = int(values[1])
                        if tex_index > 0:
                            tex_index -= 1
                        else:
                            tex_index = len(texcoords) + tex_index

                        tex_face.append(tex_index)

                if len(face) >= 3:
                    faces.append(tuple(face))

                    if len(tex_face) == len(face):
                        tex_faces.append(tuple(tex_face))
                    else:
                        tex_faces.append(None)

    if not vertices or not faces:
        raise ValueError

    logger.info(
        "obj: vertices=%s faces=%s texcoords=%s mtl=%s texture=%s",
        len(vertices),
        len(faces),
        len(texcoords),
        "yes" if has_mtl else "no",
        "yes" if texture_path is not None else "no",
    )

    if texture_path is not None and texcoords and None not in tex_faces:
        return Model.from_faces(vertices, faces, texcoords, tex_faces, texture_path)

    return Model.from_faces(vertices, faces)


def load_mtl(path):
    materials = {}
    current = None

    with open(path, "r", encoding="utf-8-sig") as file:
        for line in file:
            parts = line.split()

            if not parts or parts[0].startswith("#"):
                continue

            if parts[0] == "newmtl":
                current = parts[1]
            elif parts[0] == "map_Kd" and current is not None:
                materials[current] = path.parent / parts[-1]

    return materials


def load_stl(path):
    data = path.read_bytes()

    if is_binary_stl(data):
        return load_binary_stl(data)

    return load_ascii_stl(data.decode("utf-8-sig"))


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

    logger.info("stl: binary triangles=%s", len(faces))

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

    logger.info("stl: ascii triangles=%s", len(faces))

    return Model.from_faces(vertices, faces)