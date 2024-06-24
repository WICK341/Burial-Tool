import tkinter as tk
from tkinter import ttk, filedialog, Canvas
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.image as mpimg
from PIL import Image, ImageTk
from flask import Flask

class XYValueApp:
    def __init__(self, master):
        self.master = master

        # Initialize x and y values
        self.x_values = []
        self.y_values = []

        # Initialize the tree attribute
        self.tree = ttk.Treeview(master, columns=("X", "Y"), show="headings", selectmode="browse")
        self.tree.heading("X", text="Distance from BMH Value (M)")
        self.tree.heading("Y", text="Burial Depth Value (CM)")
        self.tree.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

        # Check if there are any previously saved files, and if so, load the data
        self.load_saved_data()

        # Configure resizing behavior
        master.columnconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)

        # Styling
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#f0f0f0", foreground="#333333", font=("Arial", 10, "bold"))
        self.style.configure("TButton", background="#4CAF50", foreground="white", font=("Arial", 10, "bold"))
        self.style.map("TButton", background=[("active", "#45a049")])
        self.style.configure("Treeview", background="#f0f0f0", foreground="#333333", font=("Arial", 10))
        self.style.map("Treeview", background=[("selected", "#4CAF50")])
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        # Apply alternating row colors
        self.style.configure("Treeview.Heading", background="#f0f0f0")
        self.tree.tag_configure("oddrow", background="#f9f9f9")
        self.tree.tag_configure("evenrow", background="#e0e0e0")

        # Upload button
        self.upload_button = ttk.Button(master, text="Upload Excel", command=self.upload_excel)
        self.upload_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Search bar
        self.search_label = ttk.Label(master, text="Search X Value:")
        self.search_label.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(master, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=2, padx=5, pady=5, sticky="we")
        self.search_entry.bind("<Return>", self.search_value)

        # Save button
        self.save_button = ttk.Button(master, text="Save", command=self.save_data)
        self.save_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

    def upload_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            df = pd.read_excel(file_path)
            x_values = df.iloc[:, 0].tolist()
            y_values = df.iloc[:, 1].tolist()
            # Convert y values to integers
            y_values = [int(y) for y in y_values]
            self.populate_table(x_values, y_values)

    def populate_table(self, x_values, y_values):
        # Clear existing items
        self.tree.delete(*self.tree.get_children())

        # Initialize lists to store filled x and y values
        filled_x_values = []
        filled_y_values = []

        # Ensure x_values and y_values are sorted
        sorted_indices = sorted(range(len(x_values)), key=lambda i: x_values[i])
        x_values = [x_values[i] for i in sorted_indices]
        y_values = [y_values[i] for i in sorted_indices]

        # Fill in missing x values and maintain corresponding y values
        prev_y = None
        for i in range(len(x_values)):
            x = x_values[i]
            y = y_values[i]

            filled_x_values.append(x)
            filled_y_values.append(prev_y if prev_y is not None else y)

            if i < len(x_values) - 1:
                next_x = x_values[i + 1]
                # Fill in missing x values
                for missing_x in range(int(x) + 1, int(next_x)):
                    filled_x_values.append(missing_x)
                    filled_y_values.append(prev_y if prev_y is not None else y)

            prev_y = y

        # Insert filled x and y values into the table with alternating row colors
        for i, (x, y) in enumerate(zip(filled_x_values, filled_y_values), start=1):
            x_formatted = int(x)
            y_formatted = int(y)
            self.tree.insert("", "end", values=(x_formatted, y_formatted))
            # Apply alternating row colors
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.item(self.tree.get_children()[-1], tags=(tag,))

        # Update x_values and y_values
        self.x_values = filled_x_values
        self.y_values = filled_y_values

    def search_value(self, event):
        search_text = self.search_var.get().strip().lower()

        # Clear all tags and reset background color to white
        for item in self.tree.get_children():
            self.tree.item(item, tags=())

        # Search for x values containing the search text
        for item in self.tree.get_children():
            x_value = str(self.tree.item(item, "values")[0]).strip().lower()
            if search_text and search_text in x_value:
                # Scroll to the item and select it
                self.tree.see(item)
                self.tree.selection_set(item)
                break

    def save_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            df = pd.DataFrame({"X": self.x_values, "Y": self.y_values})
            df.to_excel(file_path, index=False)

            # Optionally, save the file path for future use
            with open("last_saved_file.txt", "w") as f:
                f.write(file_path)

    def load_saved_data(self):
        # Check if there is a previously saved file path
        if os.path.exists("last_saved_file.txt"):
            with open("last_saved_file.txt", "r") as f:
                last_saved_file = f.read().strip()
                if os.path.exists(last_saved_file):
                    # Load data from the last saved file
                    df = pd.read_excel(last_saved_file)
                    x_values = df["X"].tolist()
                    y_values = df["Y"].tolist()
                    self.populate_table(x_values, y_values)

class GraphApp:
    def __init__(self, master):
        self.master = master

        # Initialize figure and axes
        self.fig, self.ax = plt.subplots()

        # Set x and y limits for the graph
        self.ax.set_xlim(0, 1000)
        self.ax.set_ylim(0, 225)  # Normal y-axis limits

        # Initialize cursor label
        self.cursor_label = tk.Label(master, text="", font=("Arial", 14))  # Larger font size
        self.cursor_label.pack()

        # Upload button
        self.upload_button = tk.Button(master, text="Upload Image", command=self.upload_image)
        self.upload_button.pack()

        # Canvas for displaying graph
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)

        # Connect the cursor motion event to the function
        self.canvas.mpl_connect('motion_notify_event', self.on_move)

    def upload_image(self):
        # Open file dialog to select image file
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            # Read and display the image
            self.img = mpimg.imread(file_path)
            self.ax.imshow(self.img, extent=[0, 1000, 225, 0])  # Reverse y-axis limits
            self.canvas.draw()

            # Bind escape key to exit full screen mode
            self.master.wm_attributes("-fullscreen", True)
            self.master.bind("<Escape>", self.exit_fullscreen)

    def exit_fullscreen(self, event):
        # Exit full screen mode
        self.master.wm_attributes("-fullscreen", False)

    def on_move(self, event):
        # Get x and y coordinates of the cursor
        x = event.xdata
        y = event.ydata
        if x is not None and y is not None:
            # Adjust y-coordinate for display (flip it)
            y = 225 - y
            # Update cursor label with coordinates
            self.cursor_label.config(text=f"X: {x:.2f}, Y: {y:.2f}")
        else:
            self.cursor_label.config(text="")

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.canvas = Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.upload_button = ttk.Button(root, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(pady=10)

        self.coord_label = ttk.Label(root, text="Coordinates: X=0, Y=0")
        self.coord_label.pack(pady=10)

        self.canvas.bind("<Button-1>", self.get_coordinates)
        self.root.bind('<Configure>', self.resize_image)

        self.image = None
        self.photo = None

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image = Image.open(file_path)
            self.display_image()

    def display_image(self):
        if self.image:
            # Resize the image to fit the canvas while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            self.image.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(canvas_width / 2, canvas_height / 2, anchor=tk.CENTER, image=self.photo)

    def resize_image(self, event):
        if self.image:
            self.display_image()

    def get_coordinates(self, event):
        if self.image:
            width, height = self.image.size
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Adjust coordinates based on the center position
            x_offset = (canvas_width - width) // 2
            y_offset = (canvas_height - height) // 2

            # Calculate the coordinates according to the given scales
            x = (event.x - x_offset) / width * 10000
            y = (event.y - y_offset) / height * 225
            self.coord_label.config(text=f"Coordinates: X={x:.2f}, Y={y:.2f}")
            print(f"Selected Coordinates: X={x}, Y={y}")

def main():
    root = tk.Tk()
    root.geometry("800x600")
    root.title("Cool Burial App")
    root.iconbitmap("C:\cable1.ico")
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    data_graph_tab = ttk.Frame(notebook)
    line_graph_tab = ttk.Frame(notebook)
    click_data_tab = ttk.Frame(notebook)

    notebook.add(data_graph_tab, text="Data Graph")
    notebook.add(line_graph_tab, text="Line Graph")
    notebook.add(click_data_tab, text="Click Data")

    app1 = XYValueApp(data_graph_tab)
    app2 = GraphApp(line_graph_tab)
    app3 = ImageApp(click_data_tab)

    root.mainloop()

if __name__ == "__main__":
    main()
