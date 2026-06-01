import os
import csv

BASE_DIR = os.getenv("BASE_DIR", ".")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)

with open(os.path.join(LOG_DIR, "sanitation.log"), "w", encoding="utf-8"):
    pass

with open(
    os.path.join(LOG_DIR, "histories.csv"),
    "w",
    newline="",
    encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "table_id",
            "start_time",
            "clean_time",
            "duration_seconds"
        ]
    )
    writer.writeheader()

# resmon.csv
with open(
    os.path.join(LOG_DIR, "resmon.csv"),
    "w",
    newline=""
) as f:
    writer = csv.writer(f)
    writer.writerow([
        "timestamp",
        "cpu",
        "memory",
        "disk",
        "temperature"
    ])

print("All logs cleared successfully")