"""
Приложение для работы с графами.
Формат ввода: id:метка@x,y > id:метка@x,y > ...
|    — перенос строки в метке
_lt_ — <
_gt_ — >
_    — пробел
"""
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import tkinter as tk
from tkinter import font as tkfont, messagebox
import math


# Граф
DEFAULT_INPUT = (
    "1:начало@500,100\n"
    "1 >2:ValueError?@500,380\n"
    "2 >3:return None@200,520\n"
    "2 >4:value _lt_ min?@800,520\n"
    "4 >5:return None@500,660\n"
    "4 >6:value _gt_ max?@1100,660\n"
    "6 >7:return None@800,800\n"
    "6 >8:return value@1400,800"
)


class Vertex:
    """Описание вершины графа."""
    def __init__(self, name, label, x=0, y=0, r=30):
        self.name = name
        self.label = label
        self.x = x
        self.y = y
        self.r = r
        self.links = set()


class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Граф функции validate()")
        self.root.geometry("1200x850")
        self.root.configure(bg="#f4f6f8")

        self.vertices = {}
        self.link_count = 0
        self._font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        self._build_ui()
        self.draw_from_input()

    def _build_ui(self):
        # Верхняя панель: поле ввода + кнопка
        top = tk.Frame(self.root, bg="#ffffff", bd=1, relief=tk.SOLID)
        top.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(
            top,
            text="Граф:\n"
                 "id:метка@x,y\n"
                 "id > id:метка@x,y\n"
                 "(перенос в метке — |, < и > — _lt_/_gt_, пробел — _)",
            bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 10, "bold"),
            justify="left"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.input_field = tk.Text(
            top, height=8, bg="#f9f9f9", fg="#2c3e50",
            insertbackground="#2c3e50", font=("Consolas", 11),
            bd=1, relief=tk.SOLID
        )
        self.input_field.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.input_field.insert("1.0", DEFAULT_INPUT)

        # Выделение всего текста по Ctrl+A
        self.input_field.bind("<Control-a>", lambda e: self.input_field.tag_add("sel", "1.0", "end"))

        tk.Button(
            top, text="Отрисовать", command=self.draw_from_input,
            bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, padx=20, pady=6, cursor="hand2"
        ).pack(pady=(0, 8))

        # Метрики
        metrics = tk.Frame(self.root, bg="#f4f6f8")
        metrics.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_v = tk.Label(metrics, text="Вершин: 0", bg="#f4f6f8",
                              fg="#27ae60", font=("Segoe UI", 11, "bold"))
        self.lbl_v.pack(side=tk.LEFT, padx=(0, 30))

        self.lbl_e = tk.Label(metrics, text="Рёбер: 0", bg="#f4f6f8",
                              fg="#27ae60", font=("Segoe UI", 11, "bold"))
        self.lbl_e.pack(side=tk.LEFT, padx=(0, 30))

        # Холст для графа
        canvas_frame = tk.Frame(self.root, bg="#ffffff", bd=1, relief=tk.SOLID)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="#fafafa", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Привязка событий для перетаскивания
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._do_pan)
        self.canvas.bind("<ButtonRelease-1>", lambda e: self.canvas.config(cursor=""))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

    # --- Обработчики перетаскивания и зума ---
    def _start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.config(cursor="fleur")

    def _do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_mousewheel(self, event):
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", x, y, factor, factor)

    # --- Парсинг и отрисовка ---
    def _pretty(self, label):
        label = label.replace("|", "\n")
        label = label.replace("_lt_", " < ")
        label = label.replace("_gt_", " > ")
        label = label.replace("_", " ")
        return label

    def _token_info(self, tok):
        coords = None
        if "@" in tok:
            tok, coord_str = tok.rsplit("@", 1)
            try:
                xs, ys = coord_str.split(",")
                coords = (float(xs), float(ys))
            except ValueError:
                coords = None
        if ":" in tok:
            vid, label = tok.split(":", 1)
            return vid.strip(), self._pretty(label.strip()), coords
        return tok.strip(), None, coords

    def _parse(self, text):
        ids = set()
        labels = {}
        positions = {}
        links = {}
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            tokens = [t.strip() for t in line.split(">") if t.strip()]
            for i, tok in enumerate(tokens):
                vid, label, coords = self._token_info(tok)
                if not vid:
                    continue
                ids.add(vid)
                links.setdefault(vid, set())
                if label is not None:
                    labels[vid] = label
                if coords is not None:
                    positions[vid] = coords
                if i < len(tokens) - 1:
                    nxt, _, _ = self._token_info(tokens[i + 1])
                    if nxt:
                        links[vid].add(nxt)
        return ids, labels, positions, links

    def _radius_for(self, label):
        lines = label.split("\n")
        w = max(self._font.measure(line) for line in lines)
        h = self._font.metrics("linespace") * len(lines)
        return max(w, h) / 2 + 20

    def _color_for(self, v):
        low = v.label.lower()
        has_incoming = any(v.name in other.links for other in self.vertices.values())
        if not has_incoming:
            return "#8e44ad"  # Фиолетовый (старт)
        if "?" in low:
            return "#3498db"  # Синий (условия)
        if not v.links:
            if "none" in low or "ошибка" in low or "error" in low:
                return "#e74c3c"  # Красный (ошибки)
            if "value" in low or "успех" in low or "success" in low:
                return "#2ecc71"  # Зеленый (успех)
            return "#95a5a6"  # Серый (конец)
        return "#5dade2"  # Голубой (действия)

    def draw_from_input(self):
        text = self.input_field.get("1.0", tk.END)
        ids, labels, positions, links = self._parse(text)
        if not ids:
            messagebox.showwarning("Пусто", "Введите хотя бы одну вершину.")
            return

        self.canvas.delete("all")
        self.vertices = {}
        self.link_count = sum(len(v) for v in links.values())

        for n in ids:
            x, y = positions.get(n, (500, 100))
            label = labels.get(n, n)
            r = self._radius_for(label)
            self.vertices[n] = Vertex(n, label, x, y, r)

        for src, dests in links.items():
            for d in dests:
                if src in self.vertices and d in self.vertices:
                    self.vertices[src].links.add(d)

        self._paint()
        self._refresh_metrics()

    def _paint(self):
        self.canvas.delete("all")
        # Сначала рисуем стрелки
        for v in self.vertices.values():
            for target in v.links:
                if target in self.vertices:
                    self._arrow(v, self.vertices[target])
        # Потом кружки и метки
        for v in self.vertices.values():
            fill = self._color_for(v)
            self.canvas.create_oval(v.x - v.r, v.y - v.r,
                                    v.x + v.r, v.y + v.r,
                                    fill=fill, outline="#2c3e50", width=2)
            # Метка по центру
            self.canvas.create_text(v.x, v.y, text=v.label,
                                    font=("Segoe UI", 10, "bold"),
                                    fill="#ffffff", justify="center")
            # Номер вершины в маленьком кружке-бейдже (контрастный цвет)
            badge_r = 12
            badge_x = v.x - v.r + 15
            badge_y = v.y - v.r + 15
            self.canvas.create_oval(badge_x - badge_r, badge_y - badge_r,
                                    badge_x + badge_r, badge_y + badge_r,
                                    fill="#2c3e50", outline="#ffffff", width=1)
            self.canvas.create_text(badge_x, badge_y, text=str(v.name),
                                    font=("Segoe UI", 9, "bold"),
                                    fill="#ffffff")

    def _arrow(self, src, dst):
        dx, dy = dst.x - src.x, dst.y - src.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ux, uy = dx / dist, dy / dist
        x1 = src.x + ux * src.r
        y1 = src.y + uy * src.r
        x2 = dst.x - ux * dst.r
        y2 = dst.y - uy * dst.r
        self.canvas.create_line(x1, y1, x2, y2, fill="#7f8c8d", width=2,
                                arrow=tk.LAST, arrowshape=(10, 12, 4))

    def _refresh_metrics(self):
        v = len(self.vertices)
        e = self.link_count
        self.lbl_v.config(text=f"Вершин: {v}")
        self.lbl_e.config(text=f"Рёбер: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()