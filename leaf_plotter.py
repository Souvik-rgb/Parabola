import serial
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
from PIL import Image, ImageTk

# === CONFIGURATION ===
PORT = 'COM3'  # Change to your ESP32 port
BAUD = 115200

# === Globals ===
data = []
running = True
ser = None

def read_serial():
    global data, ser
    while running:
        if ser and ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                x, y = map(float, line.split(','))
                data.append((x, y))
                update_plot()
                update_table()
                led_indicator.config(bg='green')
            except:
                led_indicator.config(bg='red')
        time.sleep(0.01)

def update_plot():
    if data:
        xs, ys = zip(*data)
        ax.clear()
        ax.plot(xs, ys, 'b.-')
        ax.set_title("Parabolic Leaf Profile")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        canvas.draw()

def update_table():
    for row in tree.get_children():
        tree.delete(row)
    for i, (x, y) in enumerate(data):
        tree.insert('', 'end', values=(i+1, x, y))

def save_data():
    if not data:
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    if file:
        df = pd.DataFrame(data, columns=["X", "Y"])
        df.to_csv(file, index=False)
        messagebox.showinfo("Saved", "Data saved successfully.")

def load_data():
    global data
    file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file:
        df = pd.read_csv(file)
        data = list(zip(df["X"], df["Y"]))
        update_plot()
        update_table()
        led_indicator.config(bg='blue')

def on_close():
    global running
    running = False
    if ser:
        ser.close()
    root.destroy()

# === GUI Setup ===
root = tk.Tk()
root.title("Leaf Profile Analyzer")

# --- Logo and Brand Name ---
header_frame = tk.Frame(root)
header_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

try:
    logo_img = Image.open("logo.png")
    logo_img = logo_img.resize((80, 80), Image.ANTIALIAS)
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(header_frame, image=logo_photo)
    logo_label.image = logo_photo
    logo_label.pack(side=tk.LEFT, padx=10)
except:
    print("Logo not found or error loading image.")

brand_label = tk.Label(header_frame, text="Leaf Profile Analyzer", font=("Arial", 20, "bold"))
brand_label.pack(side=tk.LEFT)

# --- Plot ---
fig, ax = plt.subplots(figsize=(5, 3))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# --- Table ---
tree = ttk.Treeview(root, columns=('Index', 'X', 'Y'), show='headings', height=10)
tree.heading('Index', text='Index')
tree.heading('X', text='X')
tree.heading('Y', text='Y')
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.LEFT, fill='y')

# --- Controls ---
control_frame = tk.Frame(root)
control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

tk.Button(control_frame, text="Save Data", command=save_data).pack(pady=5)
tk.Button(control_frame, text="Load Data", command=load_data).pack(pady=5)

led_indicator = tk.Label(control_frame, text="Status", bg='gray', width=15)
led_indicator.pack(pady=20)

# --- Start Serial ---
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    threading.Thread(target=read_serial, daemon=True).start()
except:
    messagebox.showerror("Error", f"Could not open serial port {PORT}")
    root.quit()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
