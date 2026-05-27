import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

INK = "#0b0f1a"; CARD = "#121826"; LINE = "#2a3550"
MINT = "#34e5a1"; GOLD = "#e8b66a"; RED = "#ff6b6b"
TEXT = "#e9eef7"; MUTED = "#8893a7"

plt.rcParams["font.family"] = "DejaVu Sans"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.4))
fig.patch.set_facecolor(INK)
for ax in (ax1, ax2):
    ax.set_facecolor(CARD)
    ax.tick_params(colors=MUTED)
    for s in ax.spines.values():
        s.set_color(LINE)
    ax.grid(axis="y", color=LINE, linewidth=0.6, alpha=0.5)
    ax.set_axisbelow(True)

# --- Panel 1: connect-latency p95 @ 6,000 concurrent, by optimization stage ---
stages = ["Original\n(1 worker)", "+ pgbouncer\n+ Varnish\n+ tuning", "+ 3 replicas\n+ ws-direct"]
p95 = [7799, 1430, 254]
colors = [RED, GOLD, MINT]
bars = ax1.bar(stages, p95, color=colors, width=0.62, edgecolor=INK)
labels = ["7.80 s", "1.43 s", "254 ms"]
for b, lab in zip(bars, labels):
    ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 150, lab,
             ha="center", va="bottom", color=TEXT, fontweight="bold", fontsize=11)
ax1.set_title("Connect latency p95 @ 6,000 concurrent users", color=TEXT, fontsize=12, pad=12)
ax1.set_ylabel("milliseconds  (lower is better)", color=MUTED)
ax1.set_ylim(0, 9000)

# --- Panel 2: final config — connections established vs attempted ---
targets =   [3000, 6000, 12000, 18000, 24000]
connected = [3000, 6000, 12000, 17379, 17546]
ax2.plot(targets, targets, "--", color=MUTED, linewidth=1.4, label="ideal (100%)")
ax2.plot(targets, connected, "-o", color=MINT, linewidth=2.6, markersize=7,
         markerfacecolor=MINT, markeredgecolor=INK, label="achieved")
ax2.axvspan(0, 12000, color=MINT, alpha=0.07)
ax2.text(6000, 22500, "100% delivery\nto ~12,000", color=MINT, ha="center", fontsize=10, fontweight="bold")
ax2.annotate("client-bound\n~17,500 (server has headroom)", xy=(18000, 17379),
             xytext=(13500, 8500), color=MUTED, fontsize=9,
             arrowprops=dict(arrowstyle="->", color=MUTED))
ax2.set_title("Final config: concurrent WebSocket connections", color=TEXT, fontsize=12, pad=12)
ax2.set_xlabel("attempted", color=MUTED)
ax2.set_ylabel("established", color=MUTED)
fmt = FuncFormatter(lambda v, _: f"{int(v/1000)}k" if v else "0")
ax2.xaxis.set_major_formatter(fmt); ax2.yaxis.set_major_formatter(fmt)
ax2.set_xlim(0, 25000); ax2.set_ylim(0, 25000)
leg = ax2.legend(facecolor=CARD, edgecolor=LINE, labelcolor=TEXT, loc="lower right")

fig.suptitle("Meridian FX — WebSocket Load Test (single host: 3 backend replicas)",
             color=TEXT, fontsize=15, fontweight="bold", y=0.99)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig("/out/load-test-results.png", dpi=150, facecolor=INK)
print("wrote load-test-results.png")
