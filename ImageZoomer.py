# Copyright (C) 2023, All rights reserved.

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageTk, Image, ImageDraw
import os, platform
from tkinter import ttk


class ImageZoomApp:
    def __init__(self, root, image_path):
        self.root = root
        self.original_image = Image.open(image_path)
        self.grid_interval_var = tk.StringVar()
        self.grid_interval_var.set("100")  # Default grid interval value
        self.grid_visible = True  # Grid visibility toggle
        self.last_directory = os.path.dirname(image_path)  # Remember last directory

        # Canvas configuration
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down

        # Keyboard bindings for zoom control
        self.root.bind("<Left>", self.zoom_out_keyboard)
        self.root.bind("<Right>", self.zoom_in_keyboard)
        
        # Keyboard bindings for image manipulation
        self.root.bind("<F1>", self.flip_horizontal)
        self.root.bind("<F2>", self.flip_vertical)
        self.root.bind("<F3>", self.rotate_clockwise)
        self.root.bind("<F4>", self.rotate_counterclockwise)
        self.root.bind("<F5>", self.reset_image)
        self.root.bind("<F6>", self.fit_to_window)
        self.root.bind("<F7>", self.toggle_grid)
        self.root.bind("<Escape>", lambda event: self.root.quit())
        
        self.root.focus_set()  # Ensure window can receive keyboard events

        # Create a centered frame for the slider, entry, and image size input
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10, anchor='center')

        # Label for image dimensions
        tk.Label(self.control_frame, text="Image Size (WxH):").pack(side=tk.LEFT, padx=5)

        # Entry for custom image dimensions
        self.true_original_image = Image.open(image_path).copy()  # This will always store the true original image.
        self.original_image = self.true_original_image.copy()
        self.image_size_var = tk.StringVar()
        self.image_size_var.set(f"{self.original_image.size[0]}x{self.original_image.size[1]}")  # Default image size
        self.image_size_entry = tk.Entry(self.control_frame, textvariable=self.image_size_var, width=10)
        self.image_size_entry.pack(side=tk.LEFT, padx=5)
        self.image_size_entry.bind("<Return>", self.set_image_size)

        # Zoom slider with percentage display
        zoom_frame = tk.Frame(self.control_frame)
        zoom_frame.pack(side=tk.LEFT, padx=5)
        
        self.slider = tk.Scale(zoom_frame, from_=0.5, to_=3, orient=tk.HORIZONTAL, resolution=0.006, command=self.update_zoom, length=300)
        self.slider.set(1)  # Set default value to 1 (no zoom)
        self.slider.pack(side=tk.TOP)
        
        self.zoom_percentage_label = tk.Label(zoom_frame, text="100%", font=("Arial", 8))
        self.zoom_percentage_label.pack(side=tk.TOP)

        # Label and Entry for grid interval
        tk.Label(self.control_frame, text="Grid Interval:").pack(side=tk.LEFT, padx=5)
        self.grid_interval_entry = tk.Entry(self.control_frame, textvariable=self.grid_interval_var, width=5)
        self.grid_interval_entry.pack(side=tk.LEFT)
        self.grid_interval_entry.bind("<Return>", lambda event: self.update_displayed_image())

        # Dropdown for predefined sizes
        self.size_options = ["Custom", "7x7 inches (72 dpi)", "Original Size"]
        self.size_combobox = ttk.Combobox(self.control_frame, values=self.size_options, state="readonly")
        self.size_combobox.set(self.size_options[0])  # set default value to "Custom"
        self.size_combobox.pack(side=tk.LEFT, padx=5)
        self.size_combobox.bind("<<ComboboxSelected>>", self.on_size_combobox_change)

        # Control buttons frame
        button_frame = tk.Frame(self.control_frame)
        button_frame.pack(side=tk.LEFT, padx=10)
        
        # Help button
        help_button = tk.Button(button_frame, text="?", width=2, command=self.show_shortcuts)
        help_button.pack(side=tk.LEFT, padx=2)
        
        # Copy zoom button
        self.copy_zoom_button = tk.Button(button_frame, text="Copy Zoom", command=self.copy_zoom_to_clipboard)
        self.copy_zoom_button.pack(side=tk.LEFT, padx=2)

        # Initial display
        self.root.update()
        self.update_zoom(1)

    def zoom_in_keyboard(self, event):
        """Zoom in using keyboard (Right arrow key)"""
        current_zoom = self.slider.get()
        new_zoom = min(current_zoom + 0.02, self.slider['to'])  # Small increment, respect max limit
        self.slider.set(new_zoom)
        self.update_zoom(new_zoom)

    def zoom_out_keyboard(self, event):
        """Zoom out using keyboard (Left arrow key)"""
        current_zoom = self.slider.get()
        new_zoom = max(current_zoom - 0.02, self.slider['from'])  # Small decrement, respect min limit
        self.slider.set(new_zoom)
        self.update_zoom(new_zoom)

    def flip_horizontal(self, event):
        """Flip image horizontally (F1)"""
        self.original_image = self.original_image.transpose(Image.FLIP_LEFT_RIGHT)
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def flip_vertical(self, event):
        """Flip image vertically (F2)"""
        self.original_image = self.original_image.transpose(Image.FLIP_TOP_BOTTOM)
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def rotate_clockwise(self, event):
        """Rotate image 90° clockwise (F3)"""
        self.original_image = self.original_image.transpose(Image.ROTATE_270)
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def rotate_counterclockwise(self, event):
        """Rotate image 90° counterclockwise (F4)"""
        self.original_image = self.original_image.transpose(Image.ROTATE_90)
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def reset_image(self, event):
        """Reset image to original state (F5)"""
        self.original_image = self.true_original_image.copy()
        self.slider.set(1)
        self.image_size_var.set(f"{self.original_image.size[0]}x{self.original_image.size[1]}")
        self.size_combobox.set("Original Size")
        self.update_zoom(1)

    def fit_to_window(self, event):
        """Fit image to window (F6)"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = self.original_image.size
        
        # Calculate zoom level to fit image in canvas
        zoom_x = canvas_width / img_width
        zoom_y = canvas_height / img_height
        zoom_level = min(zoom_x, zoom_y, self.slider['to'])  # Don't exceed max zoom
        zoom_level = max(zoom_level, self.slider['from'])   # Don't go below min zoom
        
        self.slider.set(zoom_level)
        self.update_zoom(zoom_level)

    def toggle_grid(self, event):
        """Toggle grid visibility (F7)"""
        self.grid_visible = not self.grid_visible
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def show_shortcuts(self):
        """Show keyboard shortcuts in a popup"""
        shortcuts = """Keyboard Shortcuts:

Left/Right Arrows: Zoom out/in (fine control)
F1: Flip horizontal
F2: Flip vertical  
F3: Rotate clockwise 90°
F4: Rotate counterclockwise 90°
F5: Reset to original image
F6: Fit image to window
F7: Toggle grid on/off
Escape: Close application

Mouse:
Scroll wheel: Zoom in/out
Click + drag: Pan image"""
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def copy_zoom_to_clipboard(self):
        """Copy current zoom level to clipboard"""
        zoom_level = self.slider.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(f"{zoom_level:.3f}")
        # Brief visual feedback
        original_text = self.copy_zoom_button.config('text')[-1]
        self.copy_zoom_button.config(text="Copied!")
        self.root.after(1000, lambda: self.copy_zoom_button.config(text=original_text))

    def on_size_combobox_change(self, event):
        selected_option = self.size_combobox.get()
        if selected_option == "7x7 inches (72 dpi)":
            #compensate for the screen/dpi discrepancy
            discr = 90
            # Resize the image to 7 inches at 96 dpi
            new_width = 7 * 96 - discr # 7 inches * 96 dpi
            new_height = 7 * 96 - discr # 7 inches * 96 dpi
            self.original_image = self.original_image.resize((new_width, new_height), Image.BICUBIC)
            self.image_size_var.set(f"{new_width}x{new_height}")  # Update the entry widget

            # Set the zoom level to 1 (100%)
            self.slider.set(1)
            self.update_displayed_image()
        elif selected_option == "Original Size":
            self.original_image = self.true_original_image.copy()  # Reset to the true original image
            self.slider.set(1)  # Reset zoom to 100%
            self.image_size_var.set(f"{self.original_image.size[0]}x{self.original_image.size[1]}")
            self.update_displayed_image()

        elif selected_option == "Custom":
            self.image_size_entry.focus_set()  # Set focus to the entry widget

    def draw_grid(self, image, grid_interval):
        if not self.grid_visible:
            return image
            
        draw = ImageDraw.Draw(image)
        width, height = image.size

        for i in range(0, width, grid_interval):
            draw.line([(i, 0), (i, height)], fill="black")  # Vertical lines
        for j in range(0, height, grid_interval):
            draw.line([(0, j), (width, j)], fill="black")  # Horizontal lines

        return image

    def update_zoom(self, zoom_level):
        self.update_displayed_image()
        zoom_level = float(zoom_level)
        
        # Update zoom percentage display
        self.zoom_percentage_label.config(text=f"{int(zoom_level * 100)}%")
        
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

    def update_displayed_image(self):
        zoom_level = float(self.slider.get())
        
        # Update zoom percentage display
        self.zoom_percentage_label.config(text=f"{int(zoom_level * 100)}%")
        
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

    def set_image_size(self, event):
        size_str = self.image_size_var.get()
        try:
            width, height = map(int, size_str.split("x"))
            resized_image = self.original_image.resize((width, height), Image.BICUBIC)
            self.original_image = resized_image  # Update the original image reference
            self.update_zoom(self.slider.get())  # Refresh the image
        except ValueError:
            # If the format is wrong, flash the entry in red
            self.image_size_entry.config(bg="red")
            self.root.after(500, lambda: self.image_size_entry.config(bg="white"))  # Reset color after 500ms (0.5 seconds)

            # Set the current size format back into the entry
            self.image_size_var.set(f"{self.original_image.size[0]}x{self.original_image.size[1]}")


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='gray')

    # Determine desktop path based on OS
    if platform.system() == "Windows":
        desktop = os.path.join(os.path.expanduser("~"), 'Desktop')
    else:  # This should cover Linux and MacOS
        desktop = os.path.expanduser("~/Desktop")

    image_path = filedialog.askopenfilename(initialdir=desktop, filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg"), ("All image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])

    if image_path:
        # Get the image dimensions
        image = Image.open(image_path)
        width, height = image.size

        # Set window geometry to image dimensions
        root.geometry(f"{width}x{height+50}")  # +50 to account for controls
        root.title("Image Zoomer")

        app = ImageZoomApp(root, image_path)
        
        root.mainloop()
