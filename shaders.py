import glm

from OpenGL.GL import *


BASIC_VERTEX = """
#version 120

attribute vec3 position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model * vec4(position, 1.0);
}
"""


BASIC_FRAGMENT = """
#version 120

void main()
{
    gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
"""


SOLID_VERTEX = """
#version 120

attribute vec3 position;
attribute vec3 normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

varying vec3 v_normal;

void main()
{
    mat4 model_view = view * model;

    gl_Position = projection * model_view * vec4(position, 1.0);
    v_normal = normalize(mat3(model_view) * normal);
}
"""


SOLID_FRAGMENT = """
#version 120

uniform vec3 color;
uniform vec3 light_dir;

varying vec3 v_normal;

void main()
{
    vec3 n = normalize(v_normal);
    vec3 l = normalize(light_dir);

    float diffuse = max(dot(n, l), 0.0);
    float light = 0.25 + 0.75 * diffuse;

    gl_FragColor = vec4(color * light, 1.0);
}
"""


TEXTURE_VERTEX = """
#version 120

attribute vec3 position;
attribute vec3 normal;
attribute vec2 texcoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

varying vec3 v_normal;
varying vec2 v_texcoord;

void main()
{
    mat4 model_view = view * model;

    gl_Position = projection * model_view * vec4(position, 1.0);
    v_normal = normalize(mat3(model_view) * normal);
    v_texcoord = texcoord;
}
"""


TEXTURE_FRAGMENT = """
#version 120

uniform sampler2D texture_image;
uniform vec3 light_dir;

varying vec3 v_normal;
varying vec2 v_texcoord;

void main()
{
    vec3 n = normalize(v_normal);
    vec3 l = normalize(light_dir);

    float diffuse = max(dot(n, l), 0.0);
    float light = 0.25 + 0.75 * diffuse;

    vec4 tex = texture2D(texture_image, v_texcoord);

    gl_FragColor = vec4(tex.rgb * light, tex.a);
}
"""


class Shader:
    def __init__(self, vertex_source, fragment_source):
        self.program = glCreateProgram()

        vertex_shader = self.create_shader(GL_VERTEX_SHADER, vertex_source)
        fragment_shader = self.create_shader(GL_FRAGMENT_SHADER, fragment_source)

        glAttachShader(self.program, vertex_shader)
        glAttachShader(self.program, fragment_shader)

        glBindAttribLocation(self.program, 0, "position")
        glBindAttribLocation(self.program, 1, "normal")
        glBindAttribLocation(self.program, 2, "texcoord")

        glLinkProgram(self.program)

        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(self.program).decode())

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def create_shader(self, shader_type, source):
        shader = glCreateShader(shader_type)

        glShaderSource(shader, source)
        glCompileShader(shader)

        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(shader).decode())

        return shader

    def use(self):
        glUseProgram(self.program)

    def set_int(self, name, value):
        location = glGetUniformLocation(self.program, name)
        glUniform1i(location, value)

    def set_mat4(self, name, value):
        location = glGetUniformLocation(self.program, name)
        glUniformMatrix4fv(location, 1, GL_FALSE, glm.value_ptr(value))

    def set_vec3(self, name, value):
        location = glGetUniformLocation(self.program, name)
        glUniform3f(location, value.x, value.y, value.z)

    def destroy(self):
        glDeleteProgram(self.program)


def make_basic_shader():
    return Shader(BASIC_VERTEX, BASIC_FRAGMENT)


def make_solid_shader():
    return Shader(SOLID_VERTEX, SOLID_FRAGMENT)


def make_texture_shader():
    return Shader(TEXTURE_VERTEX, TEXTURE_FRAGMENT)