from tools.history_tool import load_history
from datetime import datetime, timedelta

def refill_agent():
    df = load_history()
    alerts = []
    now = datetime.now()

    for _, row in df.iterrows():
        freq = str(row["Dosage Frequency"]).lower()
        qty = float(row["Quantity"])
        last_date = row["Purchase Date"]

        if "once" in freq:
            per_day = 1
        elif "twice" in freq:
            per_day = 2
        elif "three" in freq:
            per_day = 3
        else:
            per_day = 1

        days_supply = qty / per_day if per_day else qty
        finish_date = last_date + timedelta(days=days_supply)
        if 0 <= (finish_date - now).days <= 2:
            alerts.append(row["Patient ID"])
    return alerts
