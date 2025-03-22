import os
from datetime import datetime, timedelta
from croniter import croniter
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import seaborn as sns

# 日本語フォント設定（macOS向け）
plt.rcParams['font.family'] = 'Hiragino Sans'

def read_all_crontabs(directory="./crons/"):
    jobs = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            system_name = os.path.splitext(filename)[0]
            with open(os.path.join(directory, filename), "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) < 6:
                        continue
                    schedule = " ".join(parts[:5])
                    command = " ".join(parts[5:])
                    jobs.append({
                        "system": system_name,
                        "schedule": schedule,
                        "command": command
                    })
    return jobs

def compute_executions(jobs, count=72, base_time=None):
    if base_time is None:
        base_time = datetime.now()
    timeline = []
    for job in jobs:
        try:
            itr = croniter(job['schedule'], base_time)
            for _ in range(count):
                exec_time = itr.get_next(datetime)
                timeline.append({
                    "system": job['system'],
                    "schedule": job['schedule'],
                    "command": job['command'],
                    "execution_time": exec_time
                })
        except Exception:
            continue
    return timeline

def export_to_csv(timeline, filename="cron_output.csv"):
    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["System", "Schedule", "Command", "ExecutionTime"])
        for row in timeline:
            writer.writerow([row['system'], row['schedule'], row['command'], row['execution_time']])

def visualize(timeline):
    label_time_map = {}
    for row in timeline:
        label = f"{row['system']}: {row['command']}"
        time = row['execution_time']
        if label not in label_time_map or time < label_time_map[label]:
            label_time_map[label] = time

    # Sort labels by their earliest execution time
    unique_labels = sorted(label_time_map.keys(), key=lambda lbl: label_time_map[lbl])
    
    # 整理
    times = [row["execution_time"] for row in timeline]
    labels = [f"{row['system']}: {row['command']}" for row in timeline]
    systems = [row["system"] for row in timeline]

    # y 軸ラベルをユニーク化
    label_to_y = {label: i for i, label in enumerate(unique_labels)}
    y_vals = [label_to_y[label] for label in labels]

    # カラーマップ（システムごとに色）
    system_to_color = {sys: color for sys, color in zip(sorted(set(systems)), sns.color_palette("tab10", len(set(systems))))}
    colors = [system_to_color[sys] for sys in systems]

    # 描画
    plt.figure(figsize=(14, 8))
    plt.scatter(times, y_vals, c=colors, s=20)
    plt.yticks(list(label_to_y.values()), list(label_to_y.keys()))
    plt.gca().invert_yaxis()
    plt.xlabel("実行時刻")
    plt.title("システム別 Cronジョブのタイムライン（3日分）")
    plt.grid(True)

    # 横軸調整（3日間）＋フォーマット
    now = datetime.now()
    plt.xlim([now, now + timedelta(days=3)])
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)

    # 凡例
    handles = [plt.Line2D([0], [0], marker='o', color='w', label=system,
                          markerfacecolor=color, markersize=8) for system, color in system_to_color.items()]
    plt.legend(handles=handles, title="システム", loc='upper left')

    plt.tight_layout()
    plt.savefig("cron_timeline.png")
    print("📷 cron_timeline.png を保存しました")
    plt.show()

if __name__ == "__main__":
    jobs = read_all_crontabs()
    timeline = compute_executions(jobs)
    export_to_csv(timeline)
    print("✅ cron_output.csv を出力しました")
    visualize(timeline)
