from tkinter_gl import GLCanvas

from scene import Scene


class Canvas(GLCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.scene = Scene()
        self.ready = False
        self.last_pos = None

        self.bind("<Map>", self.on_show)
        self.bind("<Configure>", self.on_resize)

        self.bind("<ButtonPress-1>", self.on_mouse_down)
        self.bind("<B1-Motion>", self.on_mouse_drag)

        self.bind("<MouseWheel>", self.on_mouse_wheel)
        self.bind("<Button-4>", self.on_scroll_up)
        self.bind("<Button-5>", self.on_scroll_down)

    def on_show(self, event):
        self.after_idle(self.initialize)

    def on_resize(self, event):
        self.redraw_later()

    def initialize(self):
        if self.ready:
            return

        self.make_current()
        self.ready = True

        self.scene.initialize_gl()

        if self.scene.model is not None:
            self.scene.model.upload()

        self.redraw_later()

    def set_model(self, model):
        if self.ready:
            self.make_current()

            if self.scene.model is not None:
                self.scene.model.destroy()

        self.scene.set_model(model)
        self.last_pos = None

        if self.ready:
            self.scene.model.upload()
            self.redraw_later()

    def clear_model(self):
        if self.scene.model is None:
            return

        if self.ready:
            self.make_current()
            self.scene.model.destroy()

        self.scene.set_model(None)

    def set_mode(self, mode):
        self.scene.set_mode(mode)
        self.redraw_later()

    def has_texture(self):
        return self.scene.has_texture()

    def redraw_later(self):
        if self.ready:
            self.after_idle(self.draw)

    def draw(self):
        self.make_current()

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 0 or height <= 0:
            return

        self.scene.draw(width, height)
        self.swap_buffers()

    def on_mouse_down(self, event):
        self.last_pos = event.x, event.y

    def on_mouse_drag(self, event):
        if self.last_pos is None:
            self.last_pos = event.x, event.y
            return

        last_x, last_y = self.last_pos

        dx = event.x - last_x
        dy = event.y - last_y

        self.scene.rotate(dx, dy)

        self.last_pos = event.x, event.y
        self.redraw_later()

    def on_mouse_wheel(self, event):
        self.scene.change_zoom(event.delta)
        self.redraw_later()

    def on_scroll_up(self, event):
        self.scene.change_zoom(1)
        self.redraw_later()

    def on_scroll_down(self, event):
        self.scene.change_zoom(-1)
        self.redraw_later()