
import tkinter as tk
from tkinter import ttk, filedialog
import serial
import serial.tools.list_ports
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import csv

# --- GLOBALS ---
running = True
paused = True
data = []
ser = None

def find_esp32_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "ESP32" in p.description or "Silicon" in p.description or "USB" in p.description:
            return p.device
    return None

def read_serial():
    global paused
    last_values = None
    while running and ser:
        try:
            if ser.in_waiting:
                line = ser.readline().decode().strip()
                if ',' in line:
                    x_str, y_str = line.split(',')
                    x, y = int(x_str), int(y_str)
                    if last_values != (x, y):
                        data.append((x, y))
                        last_values = (x, y)
                        paused = False
                    else:
                        paused = True
        except Exception as e:
            print("Serial error:", e)
        time.sleep(0.05)

def update_plot():
    if data:
        xs, ys = zip(*data)
        ax.clear()
        ax.plot(xs, ys, label='Leaf Profile')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.grid(True)
        ax.legend()
        canvas.draw()

    # Update LED status
    led_canvas.itemconfig(led_indicator, fill="red" if paused else "green")
    root.after(100, update_plot)

def reset_plot():
    global data, paused
    data = []
    paused = False

def save_data():
    if not data: return
    filename = filedialog.asksaveasfilename(defaultextension=".csv")
    if filename:
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['X', 'Y'])
            writer.writerows(data)

# --- GUI SETUP ---
root = tk.Tk()
root.title("ESP32 Leaf Profile Plotter")

frame = ttk.Frame(root, padding=10)
frame.pack()

ttk.Button(frame, text="Reset", command=reset_plot).grid(row=0, column=0, padx=5)
ttk.Button(frame, text="Save CSV", command=save_data).grid(row=0, column=1, padx=5)

# LED Status
ttk.Label(frame, text="Status:").grid(row=0, column=2)
led_canvas = tk.Canvas(frame, width=20, height=20)
led_canvas.grid(row=0, column=3)
led_indicator = led_canvas.create_oval(2, 2, 18, 18, fill="gray")

# Plot
fig, ax = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.get_tk_widget().grid(row=1, column=0, columnspan=4)

# --- SERIAL SETUP ---
port = find_esp32_port()
if not port:
    print("ESP32 not found. Connect it and restart.")
    exit()

try:
    ser = serial.Serial(port, 115200, timeout=1)
    print(f"Connected to {port}")
except:
    print(f"Failed to open {port}")
    exit()

# --- START THREAD + PLOT LOOP ---
threading.Thread(target=read_serial, daemon=True).start()
update_plot()

# --- MAINLOOP ---
try:
    root.mainloop()
finally:
    running = False
    if ser:
        ser.close()
