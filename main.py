import os
import sys

if sys.platform == "linux":
    os.environ.setdefault("PYOPENGL_PLATFORM", "glx")

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from canvas import Canvas
from model import load_model
from test_models import make_cube, make_octahedron, make_pyramid


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

    def close(self):
        self.canvas.clear_model()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()