import math
import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt


# ==================== ПАТТЕРН «ЗАМЕСТИТЕЛЬ» ====================

class TrajectoryService:
    """Общий интерфейс сервиса расчёта."""

    def calculate(self, v0, angle):
        raise NotImplementedError

    def points(self, v0, angle, steps):
        raise NotImplementedError


class RealTrajectoryService(TrajectoryService):
    """Реальный объект — выполняет расчёт."""

    def __init__(self, g=9.81):
        self.g = g

    def calculate(self, v0, angle):
        if v0 <= 0:
            raise ValueError("Скорость должна быть > 0")
        if not (0 < angle < 90):
            raise ValueError("Угол должен быть в диапазоне (0; 90)")
        a = math.radians(angle)
        T = 2 * v0 * math.sin(a) / self.g
        H = (v0 ** 2) * (math.sin(a) ** 2) / (2 * self.g)
        L = (v0 ** 2) * math.sin(2 * a) / self.g
        return {"time": T, "height": H, "range": L}

    def points(self, v0, angle, steps):
        res = self.calculate(v0, angle)
        T = res["time"]
        a = math.radians(angle)
        pts = []
        for i in range(steps + 1):
            t = T * i / steps
            x = v0 * math.cos(a) * t
            y = v0 * math.sin(a) * t - 0.5 * self.g * t ** 2
            pts.append((round(x, 3), round(y, 3)))
        return pts


class TrajectoryProxy(TrajectoryService):
    """Заместитель: кэш, лог, ленивое создание реального объекта."""

    def __init__(self):
        self._real = None
        self._cache = {}
        self._log = []

    def _get_real(self):
        if self._real is None:
            self._real = RealTrajectoryService()
        return self._real

    def calculate(self, v0, angle):
        key = (round(v0, 3), round(angle, 3))
        if key in self._cache:
            self._log.append(f"CACHE HIT calculate({v0}, {angle})")
            return self._cache[key]

        self._log.append(f"REAL CALL calculate({v0}, {angle})")
        result = self._get_real().calculate(v0, angle)
        self._cache[key] = result
        return result

    def points(self, v0, angle, steps):
        key = (round(v0, 3), round(angle, 3), steps)
        if key in self._cache:
            self._log.append(f"CACHE HIT points({v0}, {angle}, {steps})")
            return self._cache[key]

        self._log.append(f"REAL CALL points({v0}, {angle}, {steps})")
        result = self._get_real().points(v0, angle, steps)
        self._cache[key] = result
        return result

    def get_log(self):
        return list(self._log)

    def cache_size(self):
        return len(self._cache)


# ==================== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ====================

class TrajectoryApp:
    def __init__(self, root):
        self.root = root
        root.title("Траектория движения")

        self.proxy = TrajectoryProxy()

        tk.Label(root, text="Начальная скорость (м/с):").grid(
            row=0, column=0, sticky="w"
        )
        self.v0_entry = tk.Entry(root)
        self.v0_entry.insert(0, "20")
        self.v0_entry.grid(row=0, column=1)

        tk.Label(root, text="Угол броска (°):").grid(row=1, column=0, sticky="w")
        self.angle_entry = tk.Entry(root)
        self.angle_entry.insert(0, "45")
        self.angle_entry.grid(row=1, column=1)

        tk.Label(root, text="Шагов траектории:").grid(row=2, column=0, sticky="w")
        self.steps_entry = tk.Entry(root)
        self.steps_entry.insert(0, "50")
        self.steps_entry.grid(row=2, column=1)

        tk.Button(root, text="Рассчитать", command=self.calculate).grid(
            row=3, column=0, columnspan=2, pady=5
        )
        tk.Button(
            root, text="Показать журнал заместителя", command=self.show_log
        ).grid(row=4, column=0, columnspan=2)
        tk.Button(root, text="Очистить кэш", command=self.clear_cache).grid(
            row=5, column=0, columnspan=2
        )

        self.result = tk.Text(root, width=55, height=14)
        self.result.grid(row=6, column=0, columnspan=2)

    def _read_inputs(self):
        v0 = float(self.v0_entry.get())
        angle = float(self.angle_entry.get())
        steps = int(self.steps_entry.get())
        return v0, angle, steps

    def calculate(self):
        try:
            v0, angle, steps = self._read_inputs()
            res = self.proxy.calculate(v0, angle)
            pts = self.proxy.points(v0, angle, steps)

            self.result.delete("1.0", tk.END)
            self.result.insert(
                tk.END,
                f"Время полёта: {res['time']:.3f} с\n"
                f"Макс. высота: {res['height']:.3f} м\n"
                f"Дальность: {res['range']:.3f} м\n"
                f"Точек траектории: {len(pts)}\n"
                f"Размер кэша: {self.proxy.cache_size()}\n\n"
                f"Последние записи журнала:\n",
            )
            for line in self.proxy.get_log()[-4:]:
                self.result.insert(tk.END, "  " + line + "\n")

            self.root.update_idletasks()

            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            plt.plot(xs, ys, marker="o", markersize=3)
            plt.title("Траектория движения")
            plt.xlabel("X, м")
            plt.ylabel("Y, м")
            plt.grid(True)
            plt.axis("equal")
            plt.show()
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_log(self):
        log = self.proxy.get_log()
        text = "\n".join(log) if log else "(журнал пуст)"
        messagebox.showinfo("Журнал заместителя", text)

    def clear_cache(self):
        self.proxy._cache.clear()
        messagebox.showinfo("Кэш", "Кэш заместителя очищен.")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrajectoryApp(root)
    root.mainloop()