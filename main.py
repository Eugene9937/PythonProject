import logging
import os
import sys

if sys.platform == "linux":
    os.environ.setdefault("PYOPENGL_PLATFORM", "glx")

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from canvas import Canvas
from model import load_model
from scene import RenderMode
from test_models import make_cube, make_octahedron, make_pyramid


logging.basicConfig(level=logging.INFO, format="%(message)s")


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("3D Viewer")
        self.geometry("800x600")

        self.create_menu()

        self.canvas = Canvas(self, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        self.load_cube()

        self.protocol("WM_DELETE_WINDOW", self.close)

    def create_menu(self):
        menu = tk.Menu(self)

        menu.add_command(label="Open", command=self.open_file)

        examples = tk.Menu(menu, tearoff=False)
        examples.add_command(label="Cube", command=self.load_cube)
        examples.add_command(label="Pyramid", command=self.load_pyramid)
        examples.add_command(label="Octahedron", command=self.load_octahedron)
        menu.add_cascade(label="Examples", menu=examples)

        view = tk.Menu(menu, tearoff=False)
        view.add_command(label="Wireframe", command=self.show_wireframe)
        view.add_command(label="Solid", command=self.show_solid)
        view.add_command(label="Textured", command=self.show_textured)
        menu.add_cascade(label="View", menu=view)

        self.config(menu=menu)

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("3D models", "*.obj *.stl")]
        )

        if not path:
            return

        try:
            model = load_model(path)
        except Exception:
            logging.exception("could not open file")
            messagebox.showerror("Error", "Could not open file")
            return

        self.canvas.set_model(model)
        self.title(f"3D Viewer — {Path(path).name}")

    def load_cube(self):
        self.canvas.set_model(make_cube())
        self.title("3D Viewer — Cube")

    def load_pyramid(self):
        self.canvas.set_model(make_pyramid())
        self.title("3D Viewer — Pyramid")

    def load_octahedron(self):
        self.canvas.set_model(make_octahedron())
        self.title("3D Viewer — Octahedron")

    def show_wireframe(self):
        self.canvas.set_mode(RenderMode.WIREFRAME)

    def show_solid(self):
        self.canvas.set_mode(RenderMode.SOLID)

    def show_textured(self):
        if not self.canvas.has_texture():
            messagebox.showerror("Error", "No texture")
            return

        self.canvas.set_mode(RenderMode.TEXTURED)

    def close(self):
        self.canvas.clear_model()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()