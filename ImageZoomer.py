# Copyright visjble (C) 2023, All rights reserved.

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageTk, Image, ImageDraw
import os, platform
from tkinter import ttk
import math


class ImageZoomApp:
    def __init__(self, root, image_path):
        self.root = root
        self.original_image = Image.open(image_path)
        self.overlay_image = None  # Second layer image
        self.original_overlay_image = None  # Keep original for aspect ratio
        self.overlay_scale = 1.0  # Scale factor for overlay
        self.overlay_offset_x = 0  # Overlay position offset
        self.overlay_offset_y = 0
        self.base_offset_x = 0  # Base image position offset
        self.base_offset_y = 0
        self.edit_overlay_mode = False  # Combined overlay edit mode
        self.move_base_mode = False  # Toggle for moving base layer
        self.dragging_what = None  # What is being dragged: None, "overlay", "base"
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.grid_interval_var = tk.StringVar()
        self.grid_interval_var.set("100")  # Default grid interval value
        self.grid_visible = True  # Grid visibility toggle
        self.last_directory = os.path.dirname(image_path)  # Remember last directory
        
        # Initialize image variables early
        self.true_original_image = Image.open(image_path).copy()  # This will always store the true original image.
        self.original_image = self.true_original_image.copy()
        # Initialize rotation center to image center
        self.grid_rotation_center_x = self.original_image.size[0] // 2
        self.grid_rotation_center_y = self.original_image.size[1] // 2
        
        # Initialize image size variable
        self.image_size_var = tk.StringVar()
        self.image_size_var.set(f"{self.original_image.size[0]}x{self.original_image.size[1]}")  # Default image size

        # Dropdown for predefined sizes
        self.size_options = ["Custom", "7x7 inches (72 dpi)", "Original Size"]
        
        # Create menu bar
        self.create_menu()
        
        # Grid positioning variables
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.grid_rotation = 0  # Grid rotation in degrees
        self.grid_rotation_center_x = 0  # Rotation center X (relative to image)
        self.grid_rotation_center_y = 0  # Rotation center Y (relative to image)
        self.grid_move_mode = False  # Toggle for grid move mode
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        # Canvas configuration
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
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
        self.root.bind("<F8>", self.toggle_grid_move_mode)
        self.root.bind("<F9>", self.reset_grid_position)
        self.root.bind("<o>", self.toggle_edit_overlay_mode)  # Combined overlay edit mode
        self.root.bind("<b>", self.toggle_move_base_mode)  # 'b' for base move
        
        # Keyboard bindings for overlay resizing
        self.root.bind("<Control-Shift-plus>", self.increase_overlay_size)
        self.root.bind("<Control-Shift-equal>", self.increase_overlay_size)  # For keyboards where + requires shift
        self.root.bind("<Control-Shift-minus>", self.decrease_overlay_size)
        self.root.bind("<Control-Shift-underscore>", self.decrease_overlay_size)  # Alternative binding for -
        self.root.bind("<Control-Shift-Key-minus>", self.decrease_overlay_size)  # Another alternative
        
        # Keyboard bindings for grid movement (when in grid move mode)
        self.root.bind("<Up>", self.move_grid_up)
        self.root.bind("<Down>", self.move_grid_down)
        self.root.bind("<Shift-Left>", self.move_grid_left)
        self.root.bind("<Shift-Right>", self.move_grid_right)
        self.root.bind("<Shift-Up>", self.rotate_grid_ccw)
        self.root.bind("<Shift-Down>", self.rotate_grid_cw)
        
        self.root.bind("<Escape>", lambda event: self.root.quit())
        
        self.root.focus_set()  # Ensure window can receive keyboard events

        # Create a simplified control frame with only essential controls
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=5, anchor='center')

        # Zoom slider with percentage display
        zoom_frame = tk.Frame(self.control_frame)
        zoom_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(zoom_frame, text="Zoom:", font=("Arial", 8)).pack(side=tk.TOP)
        self.slider = tk.Scale(zoom_frame, from_=0.5, to_=3, orient=tk.HORIZONTAL, resolution=0.006, command=self.update_zoom, length=200)
        self.slider.set(1)  # Set default value to 1 (no zoom)
        self.slider.pack(side=tk.TOP)
        
        self.zoom_percentage_label = tk.Label(zoom_frame, text="100%", font=("Arial", 8))
        self.zoom_percentage_label.pack(side=tk.TOP)

        # Grid interval control
        grid_frame = tk.Frame(self.control_frame)
        grid_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(grid_frame, text="Grid Interval:", font=("Arial", 8)).pack(side=tk.TOP)
        self.grid_interval_entry = tk.Entry(grid_frame, textvariable=self.grid_interval_var, width=8)
        self.grid_interval_entry.pack(side=tk.TOP)
        self.grid_interval_entry.bind("<Return>", lambda event: self.update_displayed_image())

        # Transparency slider for overlay
        transparency_frame = tk.Frame(self.control_frame)
        transparency_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(transparency_frame, text="Overlay Opacity:", font=("Arial", 8)).pack(side=tk.TOP)
        self.transparency_slider = tk.Scale(transparency_frame, from_=0, to_=255, orient=tk.HORIZONTAL, 
                                          command=self.update_transparency, length=100)
        self.transparency_slider.set(255)  # Fully opaque by default
        self.transparency_slider.pack(side=tk.TOP)

        # Image size control
        size_frame = tk.Frame(self.control_frame)
        size_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(size_frame, text="Image Size:", font=("Arial", 8)).pack(side=tk.TOP)
        self.image_size_entry = tk.Entry(size_frame, textvariable=self.image_size_var, width=10)
        self.image_size_entry.pack(side=tk.TOP)
        self.image_size_entry.bind("<Return>", self.set_image_size)

        # Size preset dropdown
        preset_frame = tk.Frame(self.control_frame)
        preset_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(preset_frame, text="Presets:", font=("Arial", 8)).pack(side=tk.TOP)
        self.size_combobox = ttk.Combobox(preset_frame, values=self.size_options, state="readonly", width=12)
        self.size_combobox.set(self.size_options[0])  # set default value to "Custom"
        self.size_combobox.pack(side=tk.TOP)
        self.size_combobox.bind("<<ComboboxSelected>>", self.on_size_combobox_change)

        # Status bar at bottom
        self.status_frame = tk.Frame(root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        # Grid position display
        self.grid_position_label = tk.Label(self.status_frame, text="Grid: (0,0,0°)", font=("Arial", 8), relief=tk.SUNKEN, anchor="w")
        self.grid_position_label.pack(side=tk.LEFT, padx=2)

        # Mode indicators
        self.grid_mode_label = tk.Label(self.status_frame, text="Grid Move: OFF", font=("Arial", 8), fg="red", relief=tk.SUNKEN, anchor="w")
        self.grid_mode_label.pack(side=tk.LEFT, padx=2)

        self.edit_overlay_label = tk.Label(self.status_frame, text="Edit Overlay: OFF", font=("Arial", 8), fg="red", relief=tk.SUNKEN, anchor="w")
        self.edit_overlay_label.pack(side=tk.LEFT, padx=2)
        
        self.move_base_label = tk.Label(self.status_frame, text="Move Base: OFF", font=("Arial", 8), fg="red", relief=tk.SUNKEN, anchor="w")
        self.move_base_label.pack(side=tk.LEFT, padx=2)

        # Initial display
        self.root.update()
        self.update_zoom(1)

    def update_status_menu(self):
        """Update the status menu items to reflect current mode states"""
        try:
            # Update grid move status
            grid_text = "Grid Move: ON" if self.grid_move_mode else "Grid Move: OFF"
            self.grid_move_status_menu.entryconfig(self.status_menu_items['grid_move'], label=grid_text)
            
            # Update edit overlay status  
            overlay_text = "Edit Overlay: ON" if self.edit_overlay_mode else "Edit Overlay: OFF"
            self.grid_move_status_menu.entryconfig(self.status_menu_items['edit_overlay'], label=overlay_text)
            
            # Update move base status
            base_text = "Move Base: ON" if self.move_base_mode else "Move Base: OFF"  
            self.grid_move_status_menu.entryconfig(self.status_menu_items['move_base'], label=base_text)
        except:
            pass  # Ignore menu update errors

    def create_menu(self):
        """Create a comprehensive menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Base Image...", command=self.open_new_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Load Overlay Image...", command=self.load_overlay_image, accelerator="Ctrl+L")
        file_menu.add_separator()
        file_menu.add_command(label="Remove Overlay", command=self.remove_overlay)
        file_menu.add_command(label="Reset Overlay Size/Position", command=self.reset_overlay)
        file_menu.add_command(label="Reset Base Position", command=self.reset_base_position)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Esc")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Fit to Window", command=lambda: self.fit_to_window(None), accelerator="F6")
        view_menu.add_command(label="Reset Image", command=lambda: self.reset_image(None), accelerator="F5")
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Grid", command=lambda: self.toggle_grid(None), accelerator="F7")
        view_menu.add_command(label="Toggle Grid Move Rotate Mode", command=lambda: self.toggle_grid_move_mode(None), accelerator="F8")
        view_menu.add_command(label="Reset Grid Position", command=lambda: self.reset_grid_position(None), accelerator="F9")
        
        # Transform menu
        transform_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transform", menu=transform_menu)
        transform_menu.add_command(label="Flip Horizontal", command=lambda: self.flip_horizontal(None), accelerator="F1")
        transform_menu.add_command(label="Flip Vertical", command=lambda: self.flip_vertical(None), accelerator="F2")
        transform_menu.add_command(label="Rotate Clockwise 90°", command=lambda: self.rotate_clockwise(None), accelerator="F3")
        transform_menu.add_command(label="Rotate Counter-clockwise 90°", command=lambda: self.rotate_counterclockwise(None), accelerator="F4")
        
        # Mode menu
        mode_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Mode", menu=mode_menu)
        mode_menu.add_command(label="Toggle Overlay Edit Mode", command=lambda: self.toggle_edit_overlay_mode(None), accelerator="O")
        mode_menu.add_command(label="Toggle Base Move Mode", command=lambda: self.toggle_move_base_mode(None), accelerator="B")
        mode_menu.add_command(label="Toggle Grid Move Rotate Mode", command=lambda: self.toggle_grid_move_mode(None), accelerator="F8")
        
        # Overlay menu
        overlay_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Overlay", menu=overlay_menu)
        overlay_menu.add_command(label="Load Overlay Image...", command=self.load_overlay_image, accelerator="Ctrl+L")
        overlay_menu.add_command(label="Remove Overlay", command=self.remove_overlay)
        overlay_menu.add_separator()
        overlay_menu.add_command(label="Increase Size (+2px)", command=lambda: self.increase_overlay_size(None), accelerator="Ctrl+Shift++")
        overlay_menu.add_command(label="Decrease Size (-2px)", command=lambda: self.decrease_overlay_size(None), accelerator="Ctrl+Shift+-")
        overlay_menu.add_separator()
        overlay_menu.add_command(label="Reset Size/Position", command=self.reset_overlay)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Copy Zoom Level", command=self.copy_zoom_to_clipboard)
        tools_menu.add_separator()
        tools_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        
        # Status indicators in menu (these will show current mode status)
        status_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Status", menu=status_menu)
        
        # We'll update these menu items to show current status
        self.grid_move_status_menu = status_menu
        self.edit_overlay_status_menu = status_menu  
        self.move_base_status_menu = status_menu
        
        # Add initial status items
        status_menu.add_command(label="Grid Move: OFF", state="disabled")
        status_menu.add_command(label="Edit Overlay: OFF", state="disabled") 
        status_menu.add_command(label="Move Base: OFF", state="disabled")
        
        # Store menu items for updates
        self.status_menu_items = {
            'grid_move': 0,
            'edit_overlay': 1, 
            'move_base': 2
        }
        
        # Bind keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.open_new_image())
        self.root.bind("<Control-l>", lambda e: self.load_overlay_image())

    def load_overlay_image(self):
        """Load an overlay image"""
        image_path = filedialog.askopenfilename(
            initialdir=self.last_directory,
            title="Select Overlay Image",
            filetypes=[
                ("All Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.tif *.webp"),
                ("PNG files", "*.png"), 
                ("JPEG files", "*.jpg *.jpeg"), 
                ("GIF files", "*.gif"),
                ("BMP files", "*.bmp"),
                ("TIFF files", "*.tiff *.tif"),
                ("WebP files", "*.webp"),
                ("All files", "*.*")
            ]
        )
        
        if image_path:
            try:
                self.original_overlay_image = Image.open(image_path)
                self.overlay_image = self.original_overlay_image.copy()
                self.overlay_scale = 1.0
                self.overlay_offset_x = 0
                self.overlay_offset_y = 0
                self.last_directory = os.path.dirname(image_path)
                
                # Refresh display to show overlay
                self.update_zoom(self.slider.get())
                
                messagebox.showinfo("Overlay Loaded", f"Overlay image loaded: {os.path.basename(image_path)}\nPress 'O' to edit overlay (move)\nCtrl+Shift+Plus/Minus to resize")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open overlay image:\n{str(e)}")

    def remove_overlay(self):
        """Remove the overlay image"""
        self.overlay_image = None
        self.original_overlay_image = None
        self.overlay_scale = 1.0
        self.overlay_offset_x = 0
        self.overlay_offset_y = 0
        self.edit_overlay_mode = False
        self.edit_overlay_label.config(text="Edit Overlay: OFF", fg="red")
        self.canvas.config(cursor="")
        self.update_zoom(self.slider.get())

    def reset_overlay(self):
        """Reset overlay size and position"""
        if self.original_overlay_image:
            self.overlay_scale = 1.0
            self.overlay_offset_x = 0
            self.overlay_offset_y = 0
            self.overlay_image = self.original_overlay_image.copy()
            self.update_zoom(self.slider.get())

    def reset_base_position(self):
        """Reset base image position"""
        self.base_offset_x = 0
        self.base_offset_y = 0
        self.update_zoom(self.slider.get())

    def toggle_edit_overlay_mode(self, event):
        """Toggle overlay edit mode (O key) - for moving overlay"""
        if not self.overlay_image:
            return
            
        self.edit_overlay_mode = not self.edit_overlay_mode
        if self.edit_overlay_mode:
            self.edit_overlay_label.config(text="Edit Overlay: ON", fg="green")
            self.canvas.config(cursor="hand2")
            # Turn off other modes
            self.move_base_mode = False
            self.grid_move_mode = False
            self.move_base_label.config(text="Move Base: OFF", fg="red")
            self.grid_mode_label.config(text="Grid Move: OFF", fg="red")
        else:
            self.edit_overlay_label.config(text="Edit Overlay: OFF", fg="red")
            self.canvas.config(cursor="")
        
        self.update_status_menu()
        self.update_zoom(self.slider.get())

    def toggle_move_base_mode(self, event):
        """Toggle base image move mode (B key)"""
        self.move_base_mode = not self.move_base_mode
        if self.move_base_mode:
            self.move_base_label.config(text="Move Base: ON", fg="green")
            self.canvas.config(cursor="fleur")
            # Turn off other modes
            self.edit_overlay_mode = False
            self.grid_move_mode = False
            self.edit_overlay_label.config(text="Edit Overlay: OFF", fg="red")
            self.grid_mode_label.config(text="Grid Move: OFF", fg="red")
        else:
            self.move_base_label.config(text="Move Base: OFF", fg="red")
            self.canvas.config(cursor="")
        
        self.update_status_menu()

    def increase_overlay_size(self, event):
        """Increase overlay size by 2 pixels (Ctrl+Shift++)"""
        if self.overlay_image and self.original_overlay_image:
            # Increase the scale to add ~2 pixels to width
            current_width = self.original_overlay_image.size[0] * self.overlay_scale
            new_width = current_width + 2
            self.overlay_scale = new_width / self.original_overlay_image.size[0]
            self.overlay_scale = max(0.1, self.overlay_scale)  # Minimum scale limit
            self.update_zoom(self.slider.get())

    def decrease_overlay_size(self, event):
        """Decrease overlay size by 2 pixels (Ctrl+Shift+-)"""
        if self.overlay_image and self.original_overlay_image:
            # Decrease the scale to remove ~2 pixels from width
            current_width = self.original_overlay_image.size[0] * self.overlay_scale
            new_width = max(10, current_width - 2)  # Minimum 10 pixels width
            self.overlay_scale = new_width / self.original_overlay_image.size[0]
            self.overlay_scale = max(0.1, self.overlay_scale)  # Minimum scale limit
            self.update_zoom(self.slider.get())

    def update_transparency(self, value):
        """Update overlay transparency"""
        if self.overlay_image:
            self.update_zoom(self.slider.get())

    def get_overlay_bounds_on_canvas(self, zoom_level):
        """Get overlay bounds in canvas coordinates"""
        if not self.overlay_image:
            return None
            
        # Calculate canvas layout
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        base_width = int(self.original_image.size[0] * zoom_level)
        base_height = int(self.original_image.size[1] * zoom_level)
        
        # Base image position on canvas (centered)
        base_x = max((canvas_width - base_width) // 2, 0)
        base_y = max((canvas_height - base_height) // 2, 0)
        
        # Overlay size and position
        overlay_width = int(self.original_overlay_image.size[0] * self.overlay_scale * zoom_level)
        overlay_height = int(self.original_overlay_image.size[1] * self.overlay_scale * zoom_level)
        
        # Overlay position relative to base image center, then to canvas
        overlay_x = base_x + (base_width - overlay_width) // 2 + int(self.overlay_offset_x * zoom_level) + int(self.base_offset_x * zoom_level)
        overlay_y = base_y + (base_height - overlay_height) // 2 + int(self.overlay_offset_y * zoom_level) + int(self.base_offset_y * zoom_level)
        
        return {
            'x': overlay_x,
            'y': overlay_y,
            'width': overlay_width,
            'height': overlay_height,
            'right': overlay_x + overlay_width,
            'bottom': overlay_y + overlay_height,
            'base_x': base_x,
            'base_y': base_y,
            'base_width': base_width,
            'base_height': base_height
        }

    def get_what_to_drag(self, canvas_x, canvas_y, zoom_level):
        if self.edit_overlay_mode and self.overlay_image:
            bounds = self.get_overlay_bounds_on_canvas(zoom_level)
            if bounds:
                # Only check for overlay move - no more corner handles
                if (bounds['x'] <= canvas_x <= bounds['right'] and 
                    bounds['y'] <= canvas_y <= bounds['bottom']):
                    return "overlay"
        
        if self.move_base_mode:
            return "base"
        
        if self.grid_move_mode:
            return "grid"
            
        return "pan"

    def composite_images(self, base_image, zoom_level):
        """Composite the base image with overlay if present"""
        # Store original base image for later use
        original_base = base_image.copy()
        
        # Apply base image offset by creating a larger canvas if needed
        if self.base_offset_x != 0 or self.base_offset_y != 0:
            # Calculate new canvas size to accommodate offset
            base_w, base_h = base_image.size
            new_w = base_w + abs(self.base_offset_x) * 2
            new_h = base_h + abs(self.base_offset_y) * 2
            
            # Create larger canvas
            offset_base = Image.new('RGB', (new_w, new_h), 'white')
            
            # Calculate paste position (center the original, then apply offset)
            paste_x = (new_w - base_w) // 2 + self.base_offset_x
            paste_y = (new_h - base_h) // 2 + self.base_offset_y
            
            try:
                offset_base.paste(base_image, (paste_x, paste_y))
                base_image = offset_base
            except:
                pass  # If paste fails, use original base
        
        if not self.overlay_image:
            return base_image
        
        # Calculate scaled overlay size
        orig_w, orig_h = self.original_overlay_image.size
        scaled_w = int(orig_w * self.overlay_scale)
        scaled_h = int(orig_h * self.overlay_scale)
        
        # Resize overlay with current scale
        overlay_resized = self.original_overlay_image.resize((scaled_w, scaled_h), Image.BICUBIC)
        
        # Get transparency value
        alpha = int(self.transparency_slider.get())
        
        # Convert to RGBA if needed
        if base_image.mode != 'RGBA':
            base_image = base_image.convert('RGBA')
        if overlay_resized.mode != 'RGBA':
            overlay_resized = overlay_resized.convert('RGBA')
        
        # Apply transparency to overlay
        overlay_with_alpha = overlay_resized.copy()
        overlay_with_alpha.putalpha(alpha)
        
        # Create a new image same size as base for compositing
        composite_base = base_image.copy()
        
        # Calculate position to paste overlay (centered by default, plus offset)
        base_w, base_h = base_image.size
        paste_x = (base_w - scaled_w) // 2 + self.overlay_offset_x
        paste_y = (base_h - scaled_h) // 2 + self.overlay_offset_y
        
        # Paste overlay onto base image
        try:
            composite_base.paste(overlay_with_alpha, (paste_x, paste_y), overlay_with_alpha)
        except:
            # If paste fails (overlay outside bounds), try alpha_composite
            overlay_positioned = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
            if 0 <= paste_x < base_w and 0 <= paste_y < base_h:
                overlay_positioned.paste(overlay_with_alpha, (paste_x, paste_y))
            composite_base = Image.alpha_composite(composite_base, overlay_positioned)
        
        # Convert back to RGB for display
        result = composite_base.convert('RGB')
        
        # Draw overlay border if overlay exists and edit mode is on
        if self.overlay_image and self.edit_overlay_mode:
            result = self.draw_overlay_border(result, zoom_level)
        
        return result

    def draw_overlay_border(self, image, zoom_level):
        """Draw border on the overlay (no more resize handles)"""
        image_with_border = image.copy()
        draw = ImageDraw.Draw(image_with_border)
        
        # Calculate overlay bounds in the current image coordinate space
        orig_w, orig_h = self.original_overlay_image.size
        scaled_w = int(orig_w * self.overlay_scale)
        scaled_h = int(orig_h * self.overlay_scale)
        
        base_w, base_h = image.size
        overlay_x = (base_w - scaled_w) // 2 + self.overlay_offset_x + self.base_offset_x
        overlay_y = (base_h - scaled_h) // 2 + self.overlay_offset_y + self.base_offset_y
        overlay_right = overlay_x + scaled_w
        overlay_bottom = overlay_y + scaled_h
        
        # Draw overlay border only
        if overlay_x < base_w and overlay_y < base_h and overlay_right > 0 and overlay_bottom > 0:
            # Clamp border to image bounds for drawing
            border_left = max(0, overlay_x)
            border_top = max(0, overlay_y)
            border_right = min(base_w - 1, overlay_right)
            border_bottom = min(base_h - 1, overlay_bottom)
            
            if border_right > border_left and border_bottom > border_top:
                draw.rectangle([border_left, border_top, border_right, border_bottom], 
                              outline="red", width=2)
        
        return image_with_border

    def open_new_image(self):
        """Open a new image file"""
        image_path = filedialog.askopenfilename(
            initialdir=self.last_directory,
            title="Select Base Image",
            filetypes=[
                ("All Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.tif *.webp"),
                ("PNG files", "*.png"), 
                ("JPEG files", "*.jpg *.jpeg"), 
                ("GIF files", "*.gif"),
                ("BMP files", "*.bmp"),
                ("TIFF files", "*.tiff *.tif"),
                ("WebP files", "*.webp"),
                ("All files", "*.*")
            ]
        )
        
        if image_path:
            try:
                # Load new image
                self.original_image = Image.open(image_path)
                self.true_original_image = self.original_image.copy()
                self.last_directory = os.path.dirname(image_path)
                
                # Reset all transformations
                self.slider.set(1)
                self.grid_offset_x = 0
                self.grid_offset_y = 0
                self.grid_rotation = 0
                self.grid_rotation_center_x = self.original_image.size[0] // 2
                self.grid_rotation_center_y = self.original_image.size[1] // 2
                self.size_combobox.set("Original Size")
                self.image_size_var.set(f"{self.original_image.size[0]}x{self.original_image.size[1]}")
                
                # Update window title
                filename = os.path.basename(image_path)
                self.root.title(f"Image Zoomer - {filename}")
                
                # Refresh display
                self.update_grid_position_display()
                self.update_zoom(1)
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image:\n{str(e)}")

    def toggle_grid_move_mode(self, event):
        """Toggle grid move mode (F8)"""
        self.grid_move_mode = not self.grid_move_mode
        if self.grid_move_mode:
            self.grid_mode_label.config(text="Grid Move: ON", fg="green")
            self.canvas.config(cursor="crosshair")
            # Turn off other modes
            self.edit_overlay_mode = False
            self.move_base_mode = False
            self.edit_overlay_label.config(text="Edit Overlay: OFF", fg="red")
            self.move_base_label.config(text="Move Base: OFF", fg="red")
        else:
            self.grid_mode_label.config(text="Grid Move: OFF", fg="red")
            self.canvas.config(cursor="")
        
        self.update_status_menu()

    def reset_grid_position(self, event):
        """Reset grid position and rotation to (0,0,0°) (F9)"""
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.grid_rotation = 0
        # Reset rotation center to image center
        self.grid_rotation_center_x = self.original_image.size[0] // 2
        self.grid_rotation_center_y = self.original_image.size[1] // 2
        self.update_grid_position_display()
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def move_grid_up(self, event):
        """Move grid up (Up arrow when in grid move mode)"""
        if self.grid_move_mode:
            self.grid_offset_y -= 1
            self.update_grid_position_display()
            current_zoom = self.slider.get()
            self.update_zoom(current_zoom)

    def move_grid_down(self, event):
        """Move grid down (Down arrow when in grid move mode)"""
        if self.grid_move_mode:
            self.grid_offset_y += 1
            self.update_grid_position_display()
            current_zoom = self.slider.get()
            self.update_zoom(current_zoom)

    def move_grid_left(self, event):
        """Move grid left (Shift+Left arrow)"""
        self.grid_offset_x -= 1
        self.update_grid_position_display()
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def move_grid_right(self, event):
        """Move grid right (Shift+Right arrow)"""
        self.grid_offset_x += 1
        self.update_grid_position_display()
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def rotate_grid_ccw(self, event):
        """Rotate grid counter-clockwise (Shift+Up arrow)"""
        self.grid_rotation = (self.grid_rotation - 3) % 360
        self.update_grid_position_display()
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def rotate_grid_cw(self, event):
        """Rotate grid clockwise (Shift+Down arrow)"""
        self.grid_rotation = (self.grid_rotation + 3) % 360
        self.update_grid_position_display()
        current_zoom = self.slider.get()
        self.update_zoom(current_zoom)

    def update_grid_position_display(self):
        """Update the grid position display label"""
        self.grid_position_label.config(text=f"Grid: ({self.grid_offset_x},{self.grid_offset_y},{self.grid_rotation}°)")

    def zoom_in_keyboard(self, event):
        """Zoom in using keyboard (Right arrow key)"""
        if not self.grid_move_mode:  # Only zoom if not in grid move mode
            current_zoom = self.slider.get()
            new_zoom = min(current_zoom + 0.02, self.slider['to'])  # Small increment, respect max limit
            
            # If we have an overlay, scale it proportionally with the zoom change
            if self.overlay_image and self.original_overlay_image and current_zoom > 0:
                zoom_ratio = new_zoom / current_zoom
                self.overlay_scale *= zoom_ratio
                self.overlay_scale = max(0.1, self.overlay_scale)  # Minimum scale limit
            
            self.slider.set(new_zoom)
            self.update_zoom(new_zoom)

    def zoom_out_keyboard(self, event):
        """Zoom out using keyboard (Left arrow key)"""
        if not self.grid_move_mode:  # Only zoom if not in grid move mode
            current_zoom = self.slider.get()
            new_zoom = max(current_zoom - 0.02, self.slider['from'])  # Small decrement, respect min limit
            
            # If we have an overlay, scale it proportionally with the zoom change
            if self.overlay_image and self.original_overlay_image and current_zoom > 0:
                zoom_ratio = new_zoom / current_zoom
                self.overlay_scale *= zoom_ratio
                self.overlay_scale = max(0.1, self.overlay_scale)  # Minimum scale limit
            
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
        # Also reset grid position and rotation center
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.grid_rotation = 0
        self.grid_rotation_center_x = self.original_image.size[0] // 2
        self.grid_rotation_center_y = self.original_image.size[1] // 2
        self.update_grid_position_display()
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

Left/Right Arrows: Zoom out/in (when grid move OFF)
Up/Down Arrows: Move grid up/down (when grid move ON)
Shift+Left/Right: Move grid left/right
Shift+Up/Down: Rotate grid CCW/CW (3° increments)
F1: Flip horizontal
F2: Flip vertical  
F3: Rotate clockwise 90°
F4: Rotate counterclockwise 90°
F5: Reset to original image + grid position/rotation
F6: Fit image to window
F7: Toggle grid on/off
F8: Toggle grid move mode on/off
F9: Reset grid position and rotation to (0,0,0°)
O: Toggle overlay edit mode (move only)
B: Toggle base image move mode on/off
Ctrl+Shift++: Increase overlay size by 2 pixels (independent of zoom)
Ctrl+Shift+-: Decrease overlay size by 2 pixels (independent of zoom)
Ctrl+O: Open base image
Ctrl+L: Load overlay image
Escape: Close application

Mouse:
Click anywhere: Set rotation center for grid
Scroll wheel: Zoom in/out (overlay scales proportionally with base)
Click + drag: Pan image (when no special mode active)
Click + drag: Move grid (when grid move ON)
Click + drag overlay: Move overlay (when edit overlay ON)
Click + drag base: Move base image (when base move ON)

Overlay transparency slider adjusts overlay visibility.
In edit overlay mode:
- Click and drag the overlay to move it
- Use Ctrl+Shift+Plus/Minus to resize overlay by 2 pixels (independent of zoom)
- Mouse wheel zoom scales both base and overlay proportionally"""
        
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
            
        # Create a copy to avoid modifying the original
        image_with_grid = image.copy()
        width, height = image.size
        
        # If no rotation, use the simple method
        if self.grid_rotation == 0:
            draw = ImageDraw.Draw(image_with_grid)
            
            # Apply grid offset
            start_x = self.grid_offset_x % grid_interval
            start_y = self.grid_offset_y % grid_interval

            # Draw vertical lines
            for i in range(start_x, width, grid_interval):
                draw.line([(i, 0), (i, height)], fill="black")
                
            # Draw horizontal lines
            for j in range(start_y, height, grid_interval):
                draw.line([(0, j), (width, j)], fill="black")
        else:
            # For rotated grid, draw a proper rotated square grid
            draw = ImageDraw.Draw(image_with_grid)
            
            # Convert rotation to radians
            angle_rad = math.radians(self.grid_rotation)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            # Use the clicked point as rotation center (accounting for offset)
            cx = self.grid_rotation_center_x + self.grid_offset_x
            cy = self.grid_rotation_center_y + self.grid_offset_y
            
            # Calculate the maximum distance from center to cover the entire image
            max_dist = int(math.sqrt(width**2 + height**2)) + grid_interval
            
            # Two perpendicular directions for the grid
            # Direction 1: original vertical direction rotated
            dir1_x = -sin_a  # perpendicular to angle
            dir1_y = cos_a
            
            # Direction 2: original horizontal direction rotated  
            dir2_x = cos_a
            dir2_y = sin_a
            
            # Draw grid lines in both directions
            for i in range(-max_dist // grid_interval, max_dist // grid_interval + 1):
                offset = i * grid_interval
                
                # Lines in direction 1 (rotated vertical lines)
                # Start point: center + offset in direction 2, extended backwards in direction 1
                start_x = cx + offset * dir2_x - max_dist * dir1_x
                start_y = cy + offset * dir2_y - max_dist * dir1_y
                # End point: center + offset in direction 2, extended forwards in direction 1  
                end_x = cx + offset * dir2_x + max_dist * dir1_x
                end_y = cy + offset * dir2_y + max_dist * dir1_y
                
                if self._line_intersects_image(start_x, start_y, end_x, end_y, width, height):
                    draw.line([(start_x, start_y), (end_x, end_y)], fill="black")
                
                # Lines in direction 2 (rotated horizontal lines)
                # Start point: center + offset in direction 1, extended backwards in direction 2
                start_x = cx + offset * dir1_x - max_dist * dir2_x
                start_y = cy + offset * dir1_y - max_dist * dir2_y
                # End point: center + offset in direction 1, extended forwards in direction 2
                end_x = cx + offset * dir1_x + max_dist * dir2_x
                end_y = cy + offset * dir1_y + max_dist * dir2_y
                
                if self._line_intersects_image(start_x, start_y, end_x, end_y, width, height):
                    draw.line([(start_x, start_y), (end_x, end_y)], fill="black")

        return image_with_grid
    
    def _line_intersects_image(self, x1, y1, x2, y2, width, height):
        """Check if a line intersects with the image bounds"""
        # Simple bounding box check
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        return not (max_x < 0 or min_x > width or max_y < 0 or min_y > height)

    def update_zoom(self, zoom_level):
        zoom_level = float(zoom_level)
        
        # Update zoom percentage display
        self.zoom_percentage_label.config(text=f"{int(zoom_level * 100)}%")
        
        grid_interval = int(self.grid_interval_var.get())
        width, height = self.original_image.size
        zoomed_image = self.original_image.resize((int(width * zoom_level), int(height * zoom_level)), Image.BICUBIC)

        # Composite with overlay if present
        zoomed_image = self.composite_images(zoomed_image, zoom_level)

        # Draw grid on zoomed image with proper scaling
        scaled_grid_interval = int(grid_interval * zoom_level)
        scaled_offset_x = int(self.grid_offset_x * zoom_level)
        scaled_offset_y = int(self.grid_offset_y * zoom_level)
        
        # Temporarily store original offsets and apply scaled ones
        orig_offset_x, orig_offset_y = self.grid_offset_x, self.grid_offset_y
        self.grid_offset_x, self.grid_offset_y = scaled_offset_x, scaled_offset_y
        zoomed_image = self.draw_grid(zoomed_image, scaled_grid_interval)
        self.grid_offset_x, self.grid_offset_y = orig_offset_x, orig_offset_y

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
        self.update_zoom(zoom_level)
        
    def on_mouse_click(self, event):
        """Handle mouse click - determine what to drag and start dragging"""
        zoom_level = float(self.slider.get())
        
        # Determine what should be dragged
        self.dragging_what = self.get_what_to_drag(event.x, event.y, zoom_level)
        
        # Store initial drag position
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # For grid rotation center setting
        if not any([self.edit_overlay_mode, self.move_base_mode, self.grid_move_mode]):
            # Convert canvas coordinates to image coordinates for grid rotation center
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_width = int(self.original_image.size[0] * zoom_level)
            img_height = int(self.original_image.size[1] * zoom_level)
            
            # Calculate image position on canvas (centered)
            x_offset = max((canvas_width - img_width) / 2, 0)
            y_offset = max((canvas_height - img_height) / 2, 0)
            
            # Convert canvas click to image coordinates
            image_x = (event.x - x_offset) / zoom_level
            image_y = (event.y - y_offset) / zoom_level
            
            # Store rotation center (clamped to image bounds)
            self.grid_rotation_center_x = max(0, min(image_x, self.original_image.size[0]))
            self.grid_rotation_center_y = max(0, min(image_y, self.original_image.size[1]))

        # Set up canvas scanning for pan mode
        if self.dragging_what == "pan":
            self.canvas.scan_mark(event.x, event.y)

    def do_drag(self, event):
        """Handle mouse drag based on what's being dragged"""
        if not self.dragging_what:
            return
            
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        zoom_level = float(self.slider.get())
        
        if self.dragging_what == "overlay":
            # Move overlay only - no more resizing
            self.overlay_offset_x += int(dx / zoom_level)
            self.overlay_offset_y += int(dy / zoom_level)
            self.update_zoom(zoom_level)
            
        elif self.dragging_what == "base":
            # Move base image
            self.base_offset_x += int(dx / zoom_level)
            self.base_offset_y += int(dy / zoom_level)
            self.update_zoom(zoom_level)
            
        elif self.dragging_what == "grid":
            # Move grid
            self.grid_offset_x += int(dx / zoom_level)
            self.grid_offset_y += int(dy / zoom_level)
            self.update_grid_position_display()
            self.update_zoom(zoom_level)
            
        elif self.dragging_what == "pan":
            # Pan the canvas
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            return  # Don't update drag_start for panning
        
        # Update drag start position for next frame
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def end_drag(self, event):
        """Clean up after dragging ends"""
        self.dragging_what = None

    def on_mouse_wheel(self, event):
        # Linux: Check event.num to determine the direction of the scroll
        if platform.system() == "Windows":
            direction = event.delta
        else:
            direction = 1 if event.num == 4 else -1

        # Determine zoom change
        zoom_change = 0.1 if direction > 0 else -0.1
        new_zoom = self.slider.get() + zoom_change
        
        # Clamp to slider bounds
        new_zoom = max(self.slider['from'], min(new_zoom, self.slider['to']))
        
        # If we have an overlay, scale it proportionally with the zoom change
        if self.overlay_image and self.original_overlay_image:
            # Calculate the zoom ratio change
            old_zoom = self.slider.get()
            if old_zoom > 0:  # Avoid division by zero
                zoom_ratio = new_zoom / old_zoom
                # Apply the same zoom ratio to overlay scale
                self.overlay_scale *= zoom_ratio
                self.overlay_scale = max(0.1, self.overlay_scale)  # Minimum scale limit
        
        self.slider.set(new_zoom)
        self.update_zoom(new_zoom)

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

    image_path = filedialog.askopenfilename(
        initialdir=desktop, 
        title="Select Image to Open",
        filetypes=[
            ("All Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.tif *.webp"),
            ("PNG files", "*.png"), 
            ("JPEG files", "*.jpg *.jpeg"), 
            ("GIF files", "*.gif"),
            ("BMP files", "*.bmp"),
            ("TIFF files", "*.tiff *.tif"),
            ("WebP files", "*.webp"),
            ("All files", "*.*")
        ]
    )

    if image_path:
        # Get the image dimensions
        image = Image.open(image_path)
        width, height = image.size

        # Set window geometry to image dimensions
        root.geometry(f"{width}x{height+50}")  # +50 to account for controls
        root.title(f"Image Zoomer - {os.path.basename(image_path)}")

        app = ImageZoomApp(root, image_path)
        
        root.mainloop()
