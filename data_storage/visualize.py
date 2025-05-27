# visualize_cohort_activity.py
import os, json, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
from datetime import datetime
from data_storage.read import read_all_edges     # API TGDB

DATE_FMT = "%Y-%m-%d"
DAYOFWEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

records = []
for edge in read_all_edges():
    ts   = edge["timestamp_start"]
    user = edge["from_name"]
    dt   = datetime.utcfromtimestamp(ts)
    records.append((
        user,
        dt.strftime(DATE_FMT),      # дневная гранулярность
        dt.hour,
        dt.weekday()                # 0-понедельник … 6-воскресенье
    ))

df = pd.DataFrame(records, columns=["user", "day", "hour", "dow"])

# ------------------------------------------------------------------ 1
daily = df.groupby("day").size()
plt.figure(figsize=(10,3))
daily.plot(color="steelblue")
plt.title("Суммарная дневная активность (все студенты)")
plt.xlabel("Дата")
plt.ylabel("Количество действий")
plt.tight_layout()
plt.show()

# ------------------------------------------------------------------ 2
per_user = df.groupby("user").size()
plt.figure(figsize=(6,4))
plt.hist(per_user, bins=30, color="salmon", edgecolor="k")
plt.title("Распределение числа действий на студента")
plt.xlabel("Действий за курс")
plt.ylabel("Число студентов")
plt.tight_layout()
plt.show()

# ------------------------------------------------------------------ 3
heat = (
    df.groupby(["dow","hour"])
      .size()
      .unstack(fill_value=0)
      .reindex(index=range(7), columns=range(24))        # полный каркас
)
plt.figure(figsize=(10,4))
sns.heatmap(heat, cmap="YlGnBu", annot=False,
            xticklabels=range(24),
            yticklabels=[DAYOFWEEK[d] for d in heat.index])
plt.title("Среднее число действий по дню недели и часу (все студенты)")
plt.xlabel("Час UTC")
plt.ylabel("День недели")
plt.tight_layout()
plt.show()
