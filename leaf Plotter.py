import serial
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
from PIL import Image, ImageTk
from io import StringIO

# === CONFIGURATION ===
PORT = 'COM3'  # Change this to match your ESP32
BAUD = 115200

# === Globals ===
data = []
ser = None
read_thread = None
reading = False

def read_serial():
    global data, reading
    while reading:
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

def start_reading():
    global reading, read_thread
    if not reading:
        reading = True
        read_thread = threading.Thread(target=read_serial, daemon=True)
        read_thread.start()
        start_btn.config(state='disabled')
        stop_btn.config(state='normal')

def stop_reading():
    global reading
    reading = False
    led_indicator.config(bg='gray')
    start_btn.config(state='normal')
    stop_btn.config(state='disabled')

def update_plot():
    if data:
        xs, ys = zip(*data)
        ax.clear()
        ax.plot(xs, ys, 'b.-')
        ax.set_title("Parabolic Leaf Profile")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        canvas.draw()
        update_background_color()  # Update background color based on result

def update_background_color():
    if not data:
        root.config(bg="white")
        return

    _, ys = zip(*data)
    max_y = max(ys)

    # Change background color based on the maximum Y value (example rule)
    if max_y < 10:
        root.config(bg="lightgray")  # Flat profile
    elif max_y < 100:
        root.config(bg="lightblue")  # Mild curve
    else:
        root.config(bg="lightgreen")  # Strong curve

def update_table():
    for row in tree.get_children():
        tree.delete(row)
    for i, (x, y) in enumerate(data):
        tree.insert('', 'end', values=(i + 1, x, y))

def save_data():
    if not data:
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    if file:
        model_text = model_label.cget("text").replace("Model: ", "")
        with open(file, 'w') as f:
            f.write("# Brand: Leaf Profile Analyzer\n")
            f.write(f"# Model: {model_text}\n")
            f.write("X,Y\n")
            for x, y in data:
                f.write(f"{x},{y}\n")
        messagebox.showinfo("Saved", "Data saved successfully.")

def load_data():
    global data
    file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file:
        with open(file, 'r') as f:
            lines = f.readlines()

        model_id = "Unknown"
        data_lines = []

        for line in lines:
            if line.startswith("# Model:"):
                model_id = line.strip().split(":")[1].strip()
            elif not line.startswith("#") and "," in line:
                data_lines.append(line)

        try:
            df = pd.read_csv(StringIO("".join(data_lines)))
            data = list(zip(df["X"], df["Y"]))
            update_plot()
            update_table()
            led_indicator.config(bg='blue')
            model_label.config(text=f"Model: {model_id}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load data.\n\n{str(e)}")

def on_close():
    stop_reading()
    if ser:
        ser.close()
    root.destroy()

# === GUI Setup ===
root = tk.Tk()
root.title("Leaf Profile Analyzer")

# --- Header with Logo and Brand Info ---
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

brand_text_frame = tk.Frame(header_frame)
brand_text_frame.pack(side=tk.LEFT)

brand_label = tk.Label(brand_text_frame, text="Leaf Profile Analyzer", font=("Arial", 20, "bold"))
brand_label.pack(anchor="w")

model_label = tk.Label(brand_text_frame, text="Model: Unknown", font=("Arial", 12))
model_label.pack(anchor="w")

# --- Plot ---
fig, ax = plt.subplots(figsize=(5, 3))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# --- Data Table ---
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

start_btn = tk.Button(control_frame, text="Start", command=start_reading)
start_btn.pack(pady=5)

stop_btn = tk.Button(control_frame, text="Stop", command=stop_reading, state='disabled')
stop_btn.pack(pady=5)

tk.Button(control_frame, text="Save Data", command=save_data).pack(pady=5)
tk.Button(control_frame, text="Load Data", command=load_data).pack(pady=5)

led_indicator = tk.Label(control_frame, text="Status", bg='gray', width=15)
led_indicator.pack(pady=20)

# --- Serial Init ---
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
except:
    messagebox.showerror("Error", f"Could not open serial port {PORT}")
    root.quit()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()