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

def visualize(timeline, base_time=None):
    # データを3日間に制限
    if base_time is None:
        base_time = datetime.now()
    now = base_time
    end_time = now + timedelta(days=3)
    timeline = [t for t in timeline if now <= t['execution_time'] <= end_time]

    label_time_map = {}
    for row in timeline:
        label = f"{row['system']}: {row['command']}"
        time = row['execution_time']
        if label not in label_time_map or time < label_time_map[label]:
            label_time_map[label] = time

    # 全てのラベルを使用
    unique_labels = sorted(label_time_map.keys(), key=lambda lbl: label_time_map[lbl])
    label_to_y = {label: i for i, label in enumerate(unique_labels)}

    times = [row["execution_time"] for row in timeline]
    labels = [f"{row['system']}: {row['command']}" for row in timeline]
    systems = [row["system"] for row in timeline]

    y_vals = [label_to_y[label] for label in labels]

    system_to_color = {sys: color for sys, color in zip(sorted(set(systems)), sns.color_palette("tab10", len(set(systems))))}
    colors = [system_to_color[sys] for sys in systems]

    # 描画
    plt.figure(figsize=(20, 12))
    scatter = plt.scatter(times, y_vals, c=colors, s=10)

    # プロットの横に時間を表示
    for t, y in zip(times, y_vals):
        plt.text(t, y, t.strftime('%H:%M'), fontsize=6, va='center', ha='left', bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

    plt.yticks(list(label_to_y.values()), list(label_to_y.keys()), fontsize=6)
    plt.gca().invert_yaxis()
    plt.xlabel("実行時刻")
    plt.title("システム別 Cronジョブのタイムライン（3日間）", fontsize=16)
    plt.grid(True, which='both', linestyle=':', linewidth=0.5)

    # 横軸調整（3日間）＋フォーマット
    plt.xlim([now, end_time])
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45, ha='right', fontsize=8)

    # 凡例
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', label=system,
                                  markerfacecolor=color, markersize=6)
                       for system, color in system_to_color.items()]
    plt.legend(handles=legend_elements, title="システム", loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)

    plt.tight_layout()
    output_image = f"cron_timeline_{args.system}.png" if args.system else "cron_timeline.png"
    plt.savefig(output_image, dpi=150, bbox_inches='tight')
    print(f":camera: {output_image} を保存しました")
    plt.show()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cronジョブのタイムラインを解析・可視化します。")
    parser.add_argument("--base-time", type=str, help="基準時刻を指定 (フォーマット: YYYY-MM-DD HH:MM:SS)", default=None)
    parser.add_argument("--system", type=str, help="特定のシステム名を指定してフィルタリングします", default=None)
    args = parser.parse_args()

    base_time = None
    if args.base_time:
        try:
            base_time = datetime.strptime(args.base_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("❌ 基準時刻のフォーマットが正しくありません。YYYY-MM-DD HH:MM:SS の形式で指定してください。")
            exit(1)
    jobs = read_all_crontabs()
    if args.system:
        jobs = [job for job in jobs if job['system'] == args.system]
        timeline = compute_executions(jobs, base_time=base_time)
        export_to_csv(timeline)
        print("✅ cron_output.csv を出力しました")
        visualize(timeline, base_time=base_time)
