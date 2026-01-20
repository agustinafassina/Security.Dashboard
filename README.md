# Security dashboard
This repository contains a security dashboard built with Plotly, Dash, and Python. It visualizes the results from scan reports, reading multiple CSV files that include data on IP addresses, domains, open ports, and other security metrics to facilitate monitoring and analysis.

### What are the steps we follow to collect information on this control panel?
<img src="stages.png" alt="Logo del proyecto" width="750" height="400">

### Setup
1. Create and activate virtual environment (recommendation)
```bash
# Create virtual environment
python -m venv venv

# Active virtual environment
venv\Scripts\activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

or by package
```bash
pip install dash
pip install pandas
pip install plotly
```

## Run project

```bash
py app.py

# or
python app.py
```