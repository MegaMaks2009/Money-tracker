import tkinter as tk
import json
import math
from datetime import date, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

root = tk.Tk()
root.title("Money tracker")
root.geometry("900x500")
root.configure(bg="#202020")

data = json.load(open("data.json", encoding="utf-8"))

fig = Figure(facecolor="#202020")
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, root)
canvas.get_tk_widget().pack(fill="both", expand=True)

money = [0]
point_x = [0]
point_text = [""]
points = None
text = None
drag = None

def update_points():
    if len(point_x) < 2:
        points.set_visible(True)
        return

    positions = ax.transData.transform([(point_x[i], money[i]) for i in range(len(point_x))])

    for i in range(1, len(positions)):
        x = positions[i][0] - positions[i - 1][0]
        y = positions[i][1] - positions[i - 1][1]

        if (x * x + y * y) ** 0.5 < 30:
            points.set_visible(False)
            text.set_visible(False)
            return

    points.set_visible(True)

def zoom(event):
    if event.inaxes != ax:
        return

    scale = 0.8 if event.button == "up" else 1.25
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()

    ax.set_xlim(event.xdata + (x1 - event.xdata) * scale, event.xdata + (x2 - event.xdata) * scale)
    ax.set_ylim(event.ydata + (y1 - event.ydata) * scale, event.ydata + (y2 - event.ydata) * scale)
    update_points()
    canvas.draw_idle()

def pan_start(event):
    global drag

    if event.button == 1 and event.inaxes == ax:
        drag = (event.x, event.y, ax.get_xlim(), ax.get_ylim())
        text.set_visible(False)

def pan(event):
    if not drag or event.inaxes != ax:
        return

    x1, x2 = drag[2]
    y1, y2 = drag[3]
    dx = (event.x - drag[0]) * (x2 - x1) / ax.bbox.width
    dy = (event.y - drag[1]) * (y2 - y1) / ax.bbox.height

    ax.set_xlim(x1 - dx, x2 - dx)
    ax.set_ylim(y1 - dy, y2 - dy)
    canvas.draw_idle()

def pan_end(event):
    global drag
    drag = None

def draw():
    global money, point_x, point_text, points, text

    ax.clear()
    ax.set_facecolor("#252525")
    ax.tick_params(colors="#bdbdbd")
    ax.grid(color="#444444", alpha=0.3)
    ax.axhline(0, color="#666666", linewidth=1)

    days = []

    if data:
        day = date.fromisoformat(min(item["date"] for item in data))

        while day <= date.today():
            days.append(day.isoformat())
            day += timedelta(days=1)

    money = [0]
    point_x = [0]
    point_text = [""]

    for i, day in enumerate(days):
        items = [item for item in data if item["date"] == day]

        if items:
            for j, item in enumerate(items):
                x = i + (j + 1) / len(items)
                y = money[-1] + item["amount"]

                ax.plot([point_x[-1], x], [money[-1], y], color="#6fa879" if item["amount"] >= 0 else "#b26767", linewidth=2)

                point_x.append(x)
                money.append(y)
                point_text.append(item.get("text", ""))
        else:
            ax.plot([point_x[-1], i + 1], [money[-1], money[-1]], color="#666666", linewidth=2)
            point_x.append(i + 1)
            money.append(money[-1])
            point_text.append("")

    points = ax.scatter(point_x, money, color="#bdbdbd", s=30, zorder=3)

    text = ax.annotate("", xy=(0, 0), xytext=(12, 12), textcoords="offset points", color="#d0d0d0", fontsize=11, bbox=dict(boxstyle="round", fc="#303030", ec="#555555"))
    text.set_visible(False)

    ax.set_xticks(range(len(days)))
    ax.set_xticklabels([day[8:] for day in days], ha="left")
    ax.set_xlabel("Day", color="#bdbdbd")
    ax.set_ylabel("Money", color="#bdbdbd")

    for side in ax.spines.values():
        side.set_color("#444444")

    update_points()
    canvas.draw()

def hover(event):
    if drag or not points.get_visible():
        if text.get_visible():
            text.set_visible(False)
            canvas.draw_idle()
        return

    if event.inaxes == ax:
        hit, info = points.contains(event)

        if hit:
            i = info["ind"][0]
            value = f"{money[i]:.2f}".rstrip("0").rstrip(".")
            note = "\n".join(point_text[i][j:j + 30] for j in range(0, len(point_text[i]), 30))

            text.xy = (point_x[i], money[i])
            text.set_text(value + ("\n" + note if note else ""))

            if event.x > canvas.get_tk_widget().winfo_width() / 2:
                text.set_position((-12, 12))
                text.set_ha("right")
            else:
                text.set_position((12, 12))
                text.set_ha("left")

            text.set_visible(True)
            canvas.draw_idle()
            return

    if text.get_visible():
        text.set_visible(False)
        canvas.draw_idle()

def show_error(window, error, message):
    window.geometry("320x91")
    error.config(text=message)
    error.pack(fill="x", padx=5, pady=5)

def add(window, entry, note, error):
    value = entry.get().strip()

    if not value:
        show_error(window, error, "Enter a value")
        return

    if value[0] not in "+-":
        show_error(window, error, "Use only + or - before the number")
        return

    number = value[1:]

    if not number:
        show_error(window, error, "Enter a number after + or -")
        return

    if not number.replace(".", "", 1).isdigit():
        show_error(window, error, "Enter a valid number")
        return

    if "." in number:
        first, last = number.split(".")
        last = last.rstrip("0")

        if len(last) > 2:
            show_error(window, error, "Maximum 2 digits after the decimal point")
            return

        number = first + ("." + last if last else "")

    amount = float(value[0] + number)

    if not math.isfinite(amount):
        show_error(window, error, "Number is too large")
        return

    if amount == 0:
        show_error(window, error, "Value cannot be 0")
        return

    data.append({"date": date.today().isoformat(), "amount": amount, "text": note.get().strip()})
    json.dump(data, open("data.json", "w", encoding="utf-8"), ensure_ascii=False)
    window.destroy()
    draw()

def menu(event):
    window = tk.Toplevel(root)
    window.overrideredirect(True)
    window.geometry(f"320x69+{event.x_root}+{event.y_root}")
    window.configure(bg="#303030")

    entry = tk.Entry(window, bg="#383838", fg="#d0d0d0", insertbackground="#d0d0d0", relief="flat", font=("Arial", 14))
    entry.pack(fill="x", padx=5, pady=(5, 0))
    entry.insert(0, "-")

    note = tk.Entry(window, bg="#383838", fg="#d0d0d0", insertbackground="#d0d0d0", relief="flat", font=("Arial", 14))
    note.pack(fill="x", padx=5, pady=(5, 0))

    error = tk.Label(window, bg="#303030", fg="#c97a7a", font=("Arial", 9))

    entry.focus()
    entry.bind("<Return>", lambda e: add(window, entry, note, error))
    note.bind("<Return>", lambda e: add(window, entry, note, error))
    entry.bind("<Escape>", lambda e: window.destroy())
    note.bind("<Escape>", lambda e: window.destroy())

def undo(event):
    if event.keycode == 90 and data:
        data.pop()
        json.dump(data, open("data.json", "w", encoding="utf-8"), ensure_ascii=False)
        draw()

canvas.get_tk_widget().bind("<Button-3>", menu)
root.bind_all("<Control-KeyPress>", undo)
canvas.mpl_connect("motion_notify_event", hover)
canvas.mpl_connect("scroll_event", zoom)
canvas.mpl_connect("button_press_event", pan_start)
canvas.mpl_connect("motion_notify_event", pan)
canvas.mpl_connect("button_release_event", pan_end)

draw()
root.mainloop()