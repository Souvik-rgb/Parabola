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

# === Serial Helpers ===
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

# === Reading Thread ===
def read_serial():
    global data, reading
    while reading:
        if ser and ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                if "," in line:
                    x, y = map(float, line.split(','))
                    data.append((x, y))
                    update_plot()
                    update_table()
                    led_indicator.config(bg='green')
            except:
                led_indicator.config(bg='red')
        time.sleep(0.01)

# === Start/Stop Read ===
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

# === Plot and Table ===
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

# === Save/Load ===
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

# === AI Log Analysis ===
def analyze_serial_logs(log_data):
    issues = []
    if "Guru Meditation Error" in log_data:
        issues.append("Guru Meditation Error: Possible crash due to memory access or pointer issue.")
    if "WDT reset" in log_data or "watchdog" in log_data.lower():
        issues.append("Watchdog timer reset detected. Avoid blocking loops or long delays.")
    if "Brownout detector" in log_data:
        issues.append("Brownout detected: Power supply may be unstable.")
    if log_data.lower().count("rebooting") > 2:
        issues.append("Frequent reboots detected. Possible crash loop.")
    if all(f"P{i}=LOW" in log_data for i in range(5)):
        issues.append("All I/O pins are LOW — check wiring, boot mode, or firmware state.")
    return issues

def extract_crash_timeline(log_data):
    lines = log_data.splitlines()
    crash_lines = [l for l in lines if "Guru Meditation" in l or "Backtrace" in l or "rebooting" in l or "Brownout" in l]
    timeline = [f"{time.strftime('%H:%M:%S')} - {line}" for line in crash_lines]
    return timeline

def suggest_fixes(issues):
    fixes = []
    for issue in issues:
        if "Guru Meditation" in issue:
            fixes.append("// Check for pointer misuse or null access")
        if "Watchdog" in issue:
            fixes.append("if (millis() - lastAction > timeout) yield(); // replace long delay")
        if "Brownout" in issue:
            fixes.append("// Use stable power source: >500mA 3.3V")
        if "GPIO34" in issue:
            fixes.append("// Avoid using GPIO34–39 as outputs")
        if "pinMode" in issue:
            fixes.append("pinMode(PIN_X, OUTPUT); // Add correct pinMode for each pin")
        if "Serial used without initialization" in issue:
            fixes.append("Serial.begin(115200); // Add to setup()")
    return list(set(fixes))  # Remove duplicates

def run_ai_diagnosis():
    log_data = log_text.get("1.0", tk.END)
    issues = analyze_serial_logs(log_data)
    timeline = extract_crash_timeline(log_data)
    fixes = suggest_fixes(issues)

    response = ""
    if issues:
        response += "Detected Issues:\n" + "\n".join(issues) + "\n\n"
    if fixes:
        response += "Suggested Fixes:\n" + "\n".join(fixes) + "\n\n"
    if timeline:
        response += "Crash Timeline:\n" + "\n".join(timeline)
    if not response:
        response = "No known issues or crash patterns found."
    messagebox.showinfo("AI Diagnosis Report", response)

    # Append suggested fixes to the log for review/export
    if fixes:
        log_text.insert(tk.END, "\n\n// === AI SUGGESTED FIXES ===\n")
        for fix in fixes:
            log_text.insert(tk.END, fix + "\n")

# === Diagnostics Window ===
def open_diagnostics_window():
    diag_win = tk.Toplevel(root)
    diag_win.title("I/O Pin Status & Troubleshooting")
    diag_win.geometry("500x800")

    tk.Label(diag_win, text="I/O Pin States (ESP32 - 38 pins)", font=("Arial", 14, "bold")).pack(pady=5)
    io_frame = tk.Frame(diag_win)
    io_frame.pack()

    pin_indicators = {}
    for i in range(38):
        row = i // 4
        col = i % 4
        pin_name = f"P{i}"
        frame = tk.Frame(io_frame, bd=1, relief=tk.RIDGE, padx=5, pady=5)
        frame.grid(row=row, column=col, padx=5, pady=5)
        lbl = tk.Label(frame, text=pin_name, width=6)
        lbl.pack()
        ind = tk.Label(frame, text="LOW", bg="red", fg="white", width=6)
        ind.pack()
        pin_indicators[pin_name] = ind

    tk.Label(diag_win, text="Send Serial Command:").pack(pady=5)
    command_entry = tk.Entry(diag_win, width=30)
    command_entry.pack()

    def send_command():
        cmd = command_entry.get().strip()
        if ser and ser.is_open and cmd:
            try:
                ser.write((cmd + '\n').encode())
                log_text.insert(tk.END, f"> Sent: {cmd}\n")
            except Exception as e:
                log_text.insert(tk.END, f"! Error: {e}\n")

    tk.Button(diag_win, text="Send", command=send_command).pack(pady=5)

    tk.Label(diag_win, text="Diagnostics Log:").pack(pady=5)
    global log_text
    log_text = tk.Text(diag_win, height=10, width=60)
    log_text.pack()

    tk.Button(diag_win, text="Run AI Diagnosis", command=run_ai_diagnosis).pack(pady=10)

    def update_pin_states():
        if ser and ser.is_open:
            try:
                ser.write(b'IOSTATUS\n')
                time.sleep(0.1)
                buffer = ""
                while ser.in_waiting:
                    buffer += ser.readline().decode(errors='ignore')
                if "IO:" in buffer:
                    lines = [l.strip() for l in buffer.splitlines() if l.startswith("IO:")]
                    for line in lines:
                        items = line.replace("IO:", "").split(",")
                        for item in items:
                            if '=' in item:
                                pin, val = item.split("=")
                                pin = pin.strip().upper()
                                val = val.strip().upper()
                                if pin in pin_indicators:
                                    ind = pin_indicators[pin]
                                    ind.config(text=val)
                                    if val == "HIGH":
                                        ind.config(bg="green", fg="white")
                                    else:
                                        ind.config(bg="red", fg="white")
                    log_text.insert(tk.END, f"[I/O Refresh] {time.strftime('%H:%M:%S')}\n")
                    log_text.see(tk.END)
            except Exception as e:
                log_text.insert(tk.END, f"! Error: {e}\n")
        diag_win.after(2000, update_pin_states)

    update_pin_states()

# === GUI ===
root = tk.Tk()
root.title("Leaf Profile Analyzer")

# Header with Logo and Brand Info
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

# Plot
fig, ax = plt.subplots(figsize=(5, 3))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Data Table
tree = ttk.Treeview(root, columns=('Index', 'X', 'Y'), show='headings', height=10)
tree.heading('Index', text='Index')
tree.heading('X', text='X')
tree.heading('Y', text='Y')
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.LEFT, fill='y')

# Controls
control_frame = tk.Frame(root)
control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

tk.Label(control_frame, text="Select COM Port:").pack()
port_combo = ttk.Combobox(control_frame, state='readonly')
port_combo.pack(pady=5)

def refresh_ports():
    ports = list_serial_ports()
    port_combo['values'] = ports
    if ports:
        port_combo.current(0)

refresh_ports()

tk.Button(control_frame, text="Refresh Ports", command=refresh_ports).pack(pady=5)
start_btn = tk.Button(control_frame, text="Start", command=start_reading)
start_btn.pack(pady=5)
stop_btn = tk.Button(control_frame, text="Stop", command=stop_reading, state='disabled')
stop_btn.pack(pady=5)
tk.Button(control_frame, text="Save Data", command=save_data).pack(pady=5)
tk.Button(control_frame, text="Load Data", command=load_data).pack(pady=5)
tk.Button(control_frame, text="Diagnostics", command=lambda: open_diagnostics_window()).pack(pady=10)

led_indicator = tk.Label(control_frame, text="Status", bg='gray', width=15)
led_indicator.pack(pady=10)
status_label = tk.Label(control_frame, text="Not connected", fg="red")
status_label.pack()

def on_close():
    stop_reading()
    if ser and ser.is_open:
        ser.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
