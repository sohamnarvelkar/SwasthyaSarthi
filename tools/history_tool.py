# tools/history_tool.py
import pandas as pd

def load_history():
    df = pd.read_excel("data/Consumer Order History 1.xlsx", skiprows=4)
    df.columns = [
        "Patient ID", "Patient Age", "Patient Gender",
        "Purchase Date", "Product Name", "Quantity",
        "Total Price (EUR)", "Dosage Frequency", "Prescription Required"
    ]
    df["Purchase Date"] = pd.to_datetime(df["Purchase Date"])
    return df