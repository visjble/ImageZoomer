

# Copyright (C) 2023, All rights reserved.


import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageDraw
import os, platform

class ImageZoomApp:
    def __init__(self, root, image_path):
        self.root = root
        self.original_image = Image.open(image_path)
        self.grid_interval_var = tk.StringVar()
        self.grid_interval_var.set("100")  # Default grid interval value

        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        # Bind the events for dragging / zooming the image
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down


        
        # Create a centered frame for the slider and entry
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10, anchor='center')
        
        self.slider = tk.Scale(self.control_frame, from_=0.5, to_=3, orient=tk.HORIZONTAL, resolution=0.006, command=self.update_zoom, length=300)
        self.slider.set(1)  # Set default value to 1 (no zoom)
        self.slider.pack(side=tk.LEFT)

        tk.Label(self.control_frame, text="Grid Interval:").pack(side=tk.LEFT, padx=5)

        self.grid_interval_entry = tk.Entry(self.control_frame, textvariable=self.grid_interval_var, width=5)
        self.grid_interval_entry.pack(side=tk.LEFT)
        self.grid_interval_entry.bind("<Return>", self.update_grid_interval)

        self.root.update()  # Update to calculate correct dimensions
        self.update_zoom(1)  # Initial display



    def draw_grid(self, image, grid_interval):
        draw = ImageDraw.Draw(image)
        width, height = image.size

        for i in range(0, width, grid_interval):
            draw.line([(i, 0), (i, height)], fill="black")  # Vertical lines
        for j in range(0, height, grid_interval):
            draw.line([(0, j), (width, j)], fill="black")  # Horizontal lines

        return image

    def update_zoom(self, zoom_level):
        zoom_level = float(zoom_level)
        grid_interval = int(self.grid_interval_var.get())
        width, height = self.original_image.size
        zoomed_image = self.original_image.resize((int(width * zoom_level), int(height * zoom_level)), Image.BICUBIC)

        # Draw grid on zoomed image
        zoomed_image = self.draw_grid(zoomed_image, grid_interval)

        self.imgtk = ImageTk.PhotoImage(zoomed_image)
        self.canvas.delete(tk.ALL)
        
        # Calculate centering offsets
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = zoomed_image.width
        img_height = zoomed_image.height
        x_offset = max((canvas_width - img_width) / 2, 0)
        y_offset = max((canvas_height - img_height) / 2, 0)
        
        self.image_on_canvas = self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.imgtk)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def update_grid_interval(self, event):
        self.update_zoom(self.slider.get())
    
    def start_drag(self, event):
        # Record the initial mouse click position.
        self.canvas.scan_mark(event.x, event.y)

    def do_drag(self, event):
        # Drag (move) the image to the new position.
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_mouse_wheel(self, event):
    # Linux: Check event.num to determine the direction of the scroll
        if platform.system() == "Windows":
            direction = event.delta
        else:
            direction = 1 if event.num == 4 else -1

        if direction > 0:
            self.slider.set(self.slider.get() + 0.1)
        else:
            self.slider.set(self.slider.get() - 0.1)
        self.update_zoom(self.slider.get())




if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='gray')


    # Determine desktop path based on OS
    if platform.system() == "Windows":
        desktop = os.path.join(os.path.expanduser("~"), 'Desktop')
    else:  # This should cover Linux and MacOS
        desktop = os.path.expanduser("~/Desktop")

    image_path = filedialog.askopenfilename(initialdir=desktop, filetypes=[("PNG files", "*.png")])

    if image_path:
        # Get the image dimensions
        image = Image.open(image_path)
        width, height = image.size

        # Set window geometry to image dimensions
        root.geometry(f"{width}x{height+50}")  # +50 to account for slider and other widgets
        root.title("Image Zoomer")

        app = ImageZoomApp(root, image_path)
        
        root.mainloop()

