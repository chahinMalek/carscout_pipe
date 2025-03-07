import pandas as pd
import os
from ast import literal_eval


run_id = "562c1e7a-b489-432a-84f8-ff1c0b39f29c"
dir = f"../../data/output/{run_id}/"
data = []

for file in os.listdir(dir):
    if file.startswith("part") and file.endswith(".csv"):
        data.append(pd.read_csv(os.path.join(dir, file)))

data = pd.concat(data, ignore_index=True)
data["specs"] = data["specs"].apply(lambda s: literal_eval(s))
data["published_at"] = data["specs"].apply(lambda s: s.get("Datum objave"))
data["specs"] = data["specs"].apply(lambda s: {k: v for k, v in s.items() if k != "Datum objave"})
data["published_at"] = pd.to_datetime(data["published_at"], format="%d.%m.%Y")
data["scraped_at"] = pd.to_datetime(data["scraped_at"])

data.to_csv(f"../../data/output/{run_id}.csv", index=False)
