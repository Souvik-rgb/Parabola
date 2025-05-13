import serial
import serial.tools.list_ports
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
from PIL import Image, ImageTk
from io import StringIO

# === Globals ===
data = []
ser = None
read_thread = None
reading = False

def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def connect_serial(port):
    global ser
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        status_label.config(text=f"Connected: {port}", fg="green")
        return True
    except Exception as e:
        messagebox.showerror("Serial Error", f"Could not open serial port {port}:\n{e}")
        status_label.config(text="Not connected", fg="red")
        return False

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
    selected_port = port_combo.get()
    if not selected_port:
        messagebox.showwarning("Port not selected", "Please select a COM port.")
        return
    if not ser or not ser.is_open:
        if not connect_serial(selected_port):
            return
    if not reading:
        try:
            ser.write(b'START\n')
        except Exception as e:
            messagebox.showerror("Serial Error", f"Failed to send START:\n{e}")
            return
        reading = True
        read_thread = threading.Thread(target=read_serial, daemon=True)
        read_thread.start()
        start_btn.config(state='disabled')
        stop_btn.config(state='normal')

def stop_reading():
    global reading
    if ser and ser.is_open:
        try:
            ser.write(b'STOP\n')
        except Exception as e:
            messagebox.showerror("Serial Error", f"Failed to send STOP:\n{e}")
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
        update_background_color()

def update_background_color():
    if not data:
        root.config(bg="white")
        return

    _, ys = zip(*data)
    max_y = max(ys)

    if max_y < 10:
        root.config(bg="lightgray")
    elif max_y < 100:
        root.config(bg="lightblue")
    else:
        root.config(bg="lightgreen")

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

def refresh_ports():
    ports = list_serial_ports()
    port_combo['values'] = ports
    if ports:
        port_combo.current(0)

def on_close():
    stop_reading()
    if ser and ser.is_open:
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
    logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
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

tk.Label(control_frame, text="Select COM Port:").pack()
port_combo = ttk.Combobox(control_frame, state='readonly')
port_combo.pack(pady=5)
refresh_ports()

tk.Button(control_frame, text="Refresh Ports", command=refresh_ports).pack(pady=5)

start_btn = tk.Button(control_frame, text="Start", command=start_reading)
start_btn.pack(pady=5)

stop_btn = tk.Button(control_frame, text="Stop", command=stop_reading, state='disabled')
stop_btn.pack(pady=5)

tk.Button(control_frame, text="Save Data", command=save_data).pack(pady=5)
tk.Button(control_frame, text="Load Data", command=load_data).pack(pady=5)

led_indicator = tk.Label(control_frame, text="Status", bg='gray', width=15)
led_indicator.pack(pady=10)

status_label = tk.Label(control_frame, text="Not connected", fg="red")
status_label.pack()

# === Start App ===
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()