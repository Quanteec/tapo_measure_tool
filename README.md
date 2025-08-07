# Tapo Measurement Tool

A GUI-based tool to measure and log power consumption from **TP-Link Tapo P110** smart plugs. This application retrieves power usage data at set intervals and saves it as a CSV file for analysis.

## Features
- Connects to **Tapo P110** smart plugs via API.
- Allows users to **select an IP address** from a dropdown.
- Provides **configurable measurement intervals and durations**.
- Displays **real-time power consumption in mW** in a terminal-like UI.
- Saves **measurement data to a CSV file**.

## Installation

### **1. Clone the Repository**
```sh
git clone https://github.com/Quanteec/tapo_measure_tool.git
cd tapo-measure-tool
```

### **2. Create a Virtual Environment (Optional but Recommended)**
```sh
python -m venv venv  # Create virtual environment
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### **3. Install Dependencies**
```sh
pip install -r requirements.txt
```

## Usage

### **1. Launch the Application**
```sh
python tapo_measure_tool.py
```

### **2. Configure Your Settings**
- **Enter Tapo login credentials** (Username & Password).
- **Select an IP Address** from the dropdown or add a new one.
- **Set the measurement interval (seconds)**.
- **Set the duration for the measurement (seconds)**.
- **Choose a filename for the CSV output**.
- **Select a folder to save results**.

### **3. Start Measurement**
- Click **"Ping"** to check connectivity.
- Click **"Start Measurement"** to begin.
- View real-time power data in the terminal output area.
- The progress bar updates as the measurement progresses.

### **4. End Measurement**
- The CSV file is saved in the selected folder.
- If the filename already exists, a number (`_1`, `_2`, etc.) is added to the filename automatically.
- The GUI re-enables once measurement completes.

## Configuration File
The tool stores configuration settings in `config.json`, which includes:
```json
{
    "username": "",
    "password": "",
    "ip_addresses": [],
    "selected_ip": "",
    "measure_interval": 0.5,
    "measure_duration": 360,
    "results_folder": "./results"
}
```
These values are updated automatically when changed in the GUI.

## Troubleshooting
### **1. GUI Freezes When Closing the App**
- Use `Ctrl + C` in the terminal to force quit.

### **2. Measurement Doesn't Start**
- Ensure **Tapo P110** is powered on and accessible.
- Verify correct **username and password**.
- Try **pushing "Ping"** to check device availability.

## Contributing
Feel free to submit pull requests or report issues in the **GitHub Issues** section.

## License
This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

## Author
Developed by **Jérémy ALBOUYS PERROIS** for **QUANTEEC**.


