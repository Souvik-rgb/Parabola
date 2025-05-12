
import tkinter as tk
from tkinter import filedialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import time
from PIL import Image, ImageTk

class LeafProfileApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parabolic Leaf Profile Viewer")
        self.root.configure(bg="#1e1e2e")
        self.data = []

        # --- Top Brand Area ---
        self.top_frame = tk.Frame(root, bg="#1e1e2e")
        self.top_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        try:
            logo_img = Image.open("logo.png").resize((50, 50))
            self.logo = ImageTk.PhotoImage(logo_img)
            self.logo_label = tk.Label(self.top_frame, image=self.logo, bg="#1e1e2e")
            self.logo_label.pack(side=tk.LEFT, padx=10)
        except FileNotFoundError:
            print("logo.png not found. Skipping logo display.")

        self.brand_label = tk.Label(self.top_frame, text="THYNK TECH", font=("Arial", 20, "bold"),
                                    fg="#00bfff", bg="#1e1e2e")
        self.brand_label.pack(side=tk.LEFT)

        self.slogan_label = tk.Label(self.top_frame, text="Evolve Yourself With Technology", font=("Arial", 10),
                                     fg="lightgray", bg="#1e1e2e")
        self.slogan_label.pack(side=tk.LEFT, padx=10)

        # --- Graph and Table ---
        self.display_frame = tk.Frame(root, bg="#1e1e2e")
        self.display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Graph Panel
        graph_frame = tk.Frame(self.display_frame, bg="#1e1e2e")
        graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(facecolor="#1e1e2e")
        self.ax.set_facecolor("#2e2e3e")
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Table Panel
        table_frame = tk.Frame(self.display_frame, bg="#1e1e2e")
        table_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.table = ttk.Treeview(table_frame, columns=("X", "Y"), show="headings", height=15)
        self.table.heading("X", text="X")
        self.table.heading("Y", text="Y")
        self.table.column("X", width=80)
        self.table.column("Y", width=80)
        self.table.pack(side=tk.TOP, fill=tk.Y, padx=5, pady=5)

        # --- Controls ---
        self.control_frame = tk.Frame(root, bg="#1e1e2e")
        self.control_frame.pack(fill=tk.X, pady=10)

        self.load_button = tk.Button(self.control_frame, text="Load Data", command=self.load_data,
                                     bg="#333", fg="white", activebackground="#444", activeforeground="cyan")
        self.load_button.pack(side=tk.LEFT, padx=10)

        self.save_button = tk.Button(self.control_frame, text="Save Data", command=self.save_data,
                                     bg="#333", fg="white", activebackground="#444", activeforeground="cyan")
        self.save_button.pack(side=tk.LEFT, padx=10)

        self.start_button = tk.Button(self.control_frame, text="Start", command=self.plot_data,
                                      bg="#007acc", fg="white", activebackground="#005f99", activeforeground="white")
        self.start_button.pack(side=tk.LEFT, padx=10)

        # LED Indicator
        self.status_led = tk.Canvas(self.control_frame, width=20, height=20, bg="#1e1e2e", highlightthickness=0)
        self.led = self.status_led.create_oval(2, 2, 18, 18, fill="red")
        self.status_led.pack(side=tk.LEFT, padx=10)

    def load_data(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        self.data = []
        with open(filepath, newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    try:
                        x = float(row[0])
                        y = float(row[1])
                        self.data.append((x, y))
                    except ValueError:
                        pass

    def save_data(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv")
        if not filepath:
            return
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(self.data)

    def plot_data(self):
        self.ax.clear()
        self.table.delete(*self.table.get_children())
        self.status_led.itemconfig(self.led, fill="green")

        if self.data:
            x_vals, y_vals = zip(*self.data)
            plotted_x = []
            plotted_y = []
            for x, y in zip(x_vals, y_vals):
                plotted_x.append(x)
                plotted_y.append(y)
                self.ax.plot(plotted_x, plotted_y, 'b-')
                self.ax.set_title("Parabolic Leaf Profile")
                self.ax.set_xlabel("X-axis")
                self.ax.set_ylabel("Y-axis")
                self.table.insert("", "end", values=(round(x, 3), round(y, 3)))
                self.canvas.draw()
                self.root.update()
                time.sleep(0.05)  # delay for real-time feel

        self.status_led.itemconfig(self.led, fill="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = LeafProfileApp(root)
    root.mainloop()
