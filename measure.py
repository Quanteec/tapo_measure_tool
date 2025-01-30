import asyncio
import os
import csv
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime
from tapo import ApiClient

def load_config():
    CONFIG_FILE = "config.json"
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "username": "",
            "password": "",
            "ip_addresses": [],
            "measure_interval": 0.5,
            "measure_duration": 360,
            "results_folder": "./results"
        }
        save_config(default_config)
        return default_config
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def save_config(config):
    with open("config.json", "w") as file:
        json.dump(config, file, indent=4)

tapo_config = load_config()

# Disable/enable all widgets function
def set_all_widgets_state(state):
    # Disable or enable buttons and entry fields during the measurement process
    for widget in root.winfo_children():
        if isinstance(widget, (tk.Button, tk.Entry, ttk.Combobox)):
            widget.config(state=state)

def add_ip():
    new_ip = simpledialog.askstring("Add IP Address", "Enter new IP address:")
    if new_ip and new_ip not in tapo_config["ip_addresses"]:
        tapo_config["ip_addresses"].append(new_ip)
        save_config(tapo_config)
        ip_dropdown["values"] = tapo_config["ip_addresses"]

def ping_ip_threadsafe():
    threading.Thread(target=asyncio.run, args=(ping_ip_async(),)).start()

async def ping_ip_async():
    ip = ip_var.get()
    if not ip:
        messagebox.showerror("Error", "No IP address selected.")
        return
    client = ApiClient(username_var.get(), password_var.get())
    try:
        device = await asyncio.wait_for(client.p110(ip), timeout=5)
        response = await asyncio.wait_for(device.get_device_info_json(), timeout=5)
        messagebox.showinfo("Success", f"IP {ip} is reachable.\nDevice Info: {response}")
        measure_button.config(state="normal")
    except asyncio.TimeoutError:
        messagebox.showerror("Error", f"Timeout: IP {ip} is unreachable.")
    except Exception as e:
        messagebox.showerror("Error", f"An exception occurred: {e}")

def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def start_measurement_threadsafe():
    threading.Thread(target=asyncio.run, args=(measure_power_async(),)).start()

# Global task reference
measurement_task = None

# Global reference to the event loop
loop = asyncio.get_event_loop()


async def measure_power_async():
    global measurement_task
    root.after(0, set_all_widgets_state, "disabled")
    
    tapo_config["username"] = username_var.get()
    tapo_config["password"] = password_var.get()
    tapo_config["measure_interval"] = float(interval_var.get())
    tapo_config["measure_duration"] = int(duration_var.get())
    save_config(tapo_config)

    ip = ip_var.get()
    filename = filename_var.get()
    folder = folder_var.get()
    if not ip or not filename:
        messagebox.showerror("Error", "IP address and filename are required.")
        root.after(0, set_all_widgets_state, "normal")  # Re-enable all widgets safely in the main thread
        return
    csv_path = os.path.join(folder, f"{filename}.csv")

    # Set up the task and monitor it
    measurement_task = asyncio.ensure_future(measure_power(ip, tapo_config["measure_interval"], tapo_config["measure_duration"], csv_path))
    
    await measurement_task

async def measure_power(tapo_ip, measure_interval, measure_duration, csv_name):
    client = ApiClient(tapo_config["username"], tapo_config["password"])
    device = await asyncio.wait_for(client.p110(tapo_ip), timeout=5)
    end_time = asyncio.get_event_loop().time() + measure_duration
    measurements = []
    start_time = datetime.now()
    measure_interrupt = False
    while asyncio.get_event_loop().time() < end_time:
        try:
            energy_data = await asyncio.wait_for(device.get_energy_usage(), timeout=5)
            current_power = energy_data.current_power
        except:
            print("Error retrieving data, using previous value.")
        timestamp = datetime.now()
        measurements.append({"timestamp": timestamp, "power": current_power})

        # Mise à jour de la barre de progression et du temps restant
        elapsed_time = (datetime.now() - start_time).total_seconds()
        progress = elapsed_time / measure_duration
        progress_bar["value"] = progress * 100
        remaining_time = int(measure_duration - elapsed_time)
        remaining_time_label.config(text=f"Time Remaining: {remaining_time}s")
        
        # Affichage dans le terminal-like widget
        terminal_output.insert(tk.END, f"{timestamp} - Power: {current_power}mW\n")
        terminal_output.yview(tk.END)  # Scroll to the latest entry

        try:
            await asyncio.sleep(measure_interval)  # Handle sleep cancellation
        except asyncio.CancelledError:
            print("Measurement task was cancelled.")
            measure_interrupt = True
            break  # Exit the loop if the task is cancelled    

    if not measure_interrupt:
        with open(csv_name, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["timestamp", "power"])
            writer.writeheader()
            writer.writerows(measurements)
        messagebox.showinfo("Success", f"Data saved to {csv_name}")
        set_all_widgets_state("normal")  # Re-enable all widgets after measurement is done

def on_close():
    global measurement_task
    if measurement_task:
        # Cancel the ongoing task
        measurement_task.cancel()

        # Check if the task has been canceled or completed before accessing the result
        try:
            measurement_task.result()  # This will raise a CancelledError if the task was cancelled
        except asyncio.CancelledError:
            pass  # Ignore cancellation error
        except asyncio.InvalidStateError:
            pass  # Ignore InvalidStateError if the task has already finished

    root.quit()  # Quit Tkinter main loop
    root.destroy()  # Destroy the Tkinter root window

root = tk.Tk()
root.title("Tapo Measurement Tool")
root.geometry("600x600")
root.columnconfigure(1, weight=1)
root.rowconfigure(6, weight=1)

# Adding the close event handler
root.protocol("WM_DELETE_WINDOW", on_close)

# Variables
username_var = tk.StringVar(value=tapo_config.get("username", ""))
password_var = tk.StringVar(value=tapo_config.get("password", ""))
filename_var = tk.StringVar()
folder_var = tk.StringVar(value=tapo_config.get("results_folder", "./results"))
ip_var = tk.StringVar()
interval_var = tk.StringVar(value=str(tapo_config.get("measure_interval", "0.5")))
duration_var = tk.StringVar(value=str(tapo_config.get("measure_duration", "360")))

# Widgets (same as before, but the button and entries are disabled during measurement)
tk.Label(root, text="Username:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=username_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

tk.Label(root, text="Password:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=password_var, show="*").grid(row=1, column=1, sticky="ew", padx=5, pady=5)

tk.Label(root, text="CSV Filename:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=filename_var).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

tk.Label(root, text="Save Folder:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=folder_var, state="readonly").grid(row=3, column=1, sticky="ew", padx=5, pady=5)
tk.Button(root, text="Browse", command=select_folder).grid(row=3, column=2, padx=5, pady=5)

tk.Label(root, text="Select IP Address:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
ip_dropdown = ttk.Combobox(root, textvariable=ip_var, values=tapo_config["ip_addresses"])
ip_dropdown.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

tk.Button(root, text="Add IP", command=add_ip).grid(row=4, column=2, padx=5, pady=5)
tk.Button(root, text="Ping", command=ping_ip_threadsafe).grid(row=4, column=3, padx=5, pady=5)

tk.Label(root, text="Measure Interval (s):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=interval_var).grid(row=5, column=1, sticky="ew", padx=5, pady=5)

tk.Label(root, text="Measure Duration (s):").grid(row=6, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=duration_var).grid(row=6, column=1, sticky="ew", padx=5, pady=5)

measure_button = tk.Button(root, text="Start Measurement", command=start_measurement_threadsafe, state="disabled")
measure_button.grid(row=7, column=1, pady=10)

# Barre de progression
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=8, column=0, columnspan=3, padx=5, pady=5)

# Label de temps restant
remaining_time_label = tk.Label(root, text="Time Remaining: 0s")
remaining_time_label.grid(row=9, column=0, columnspan=3, padx=5, pady=5)

# Terminal-like output
terminal_frame = tk.Frame(root)
terminal_frame.grid(row=10, column=0, columnspan=3, padx=5, pady=5)

terminal_output = tk.Text(terminal_frame, height=10, width=50, wrap="word", bg="black", fg="white", font=("Courier", 10))
terminal_output.pack(side="left", fill="both", expand=True)
terminal_output_scroll = tk.Scrollbar(terminal_frame, command=terminal_output.yview)
terminal_output_scroll.pack(side="right", fill="y")
terminal_output.config(yscrollcommand=terminal_output_scroll.set)

root.mainloop()
