import math
import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt


# ==================== ПАТТЕРН «ФАСАД» ====================

class Validator:
    def validate(self, v0, angle):
        if v0 <= 0:
            raise ValueError("Скорость должна быть > 0")
        if not (0 < angle < 90):
            raise ValueError("Угол должен быть в диапазоне (0; 90)")
        return True


class ModelCalculator:
    def __init__(self, g=9.81):
        self.g = g

    def flight_time(self, v0, angle):
        a = math.radians(angle)
        return 2 * v0 * math.sin(a) / self.g

    def max_height(self, v0, angle):
        a = math.radians(angle)
        return (v0 ** 2) * (math.sin(a) ** 2) / (2 * self.g)

    def flight_range(self, v0, angle):
        a = math.radians(angle)
        return (v0 ** 2) * math.sin(2 * a) / self.g

    def trajectory_points(self, v0, angle, steps):
        T = self.flight_time(v0, angle)
        a = math.radians(angle)
        pts = []
        for i in range(steps + 1):
            t = T * i / steps
            x = v0 * math.cos(a) * t
            y = v0 * math.sin(a) * t - 0.5 * self.g * t ** 2
            pts.append((round(x, 3), round(y, 3)))
        return pts


class PlotBuilder:
    def build(self, points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        plt.plot(xs, ys, marker='o', markersize=3)
        plt.title("Траектория движения")
        plt.xlabel("X, м")
        plt.ylabel("Y, м")
        plt.grid(True)
        plt.axis('equal')
        plt.show()


class TrajectoryFacade:
    """Фасад: простой интерфейс к подсистеме расчёта."""

    def __init__(self):
        self.validator = Validator()
        self.calculator = ModelCalculator()
        self.plot = PlotBuilder()

    def calculate_and_show(self, v0, angle):
        self.validator.validate(v0, angle)
        T = self.calculator.flight_time(v0, angle)
        H = self.calculator.max_height(v0, angle)
        L = self.calculator.flight_range(v0, angle)
        pts = self.calculator.trajectory_points(v0, angle, 50)
        self.plot.build(pts)
        return {"time": T, "height": H, "range": L, "points": pts}


# ==================== ПАТТЕРН «ПРИСПОСОБЛЕНЕЦ» ====================

class PointStyle:
    """Внутреннее состояние: общее для всех точек."""

    def __init__(self, g, k, step):
        self.g = g
        self.k = k
        self.step = step

    def get_g(self):
        return self.g

    def get_k(self):
        return self.k


class TrajectoryPoint:
    """Точка траектории: внешнее состояние + ссылка на общий стиль."""

    def __init__(self, x, y, style: PointStyle):
        self.x = x
        self.y = y
        self.style = style

    def coords(self):
        return (self.x, self.y)

    def style_info(self):
        return f"g={self.style.get_g()}, k={self.style.get_k()}"


class PointFactory:
    """Фабрика и кэш общих стилей (Flyweight)."""

    _cache = {}

    @staticmethod
    def get_style(g, k, step):
        key = (g, k, step)
        if key not in PointFactory._cache:
            PointFactory._cache[key] = PointStyle(g, k, step)
        return PointFactory._cache[key]

    @staticmethod
    def cache_size():
        return len(PointFactory._cache)


# ==================== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ====================

class TrajectoryApp:
    def __init__(self, root):
        self.root = root
        root.title("Траектория движения")

        self.facade = TrajectoryFacade()

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

        tk.Button(root, text="Рассчитать", command=self.calculate).grid(
            row=2, column=0, columnspan=2, pady=5
        )
        tk.Button(
            root, text="Показать кэш приспособленцев", command=self.show_cache
        ).grid(row=3, column=0, columnspan=2)

        self.result = tk.Text(root, width=50, height=12)
        self.result.grid(row=4, column=0, columnspan=2)

    def _read_inputs(self):
        v0 = float(self.v0_entry.get())
        angle = float(self.angle_entry.get())
        return v0, angle

    def calculate(self):
        try:
            v0, angle = self._read_inputs()
            res = self.facade.calculate_and_show(v0, angle)

            # Демонстрация приспособленца: точки используют общий стиль
            style = PointFactory.get_style(9.81, 0.0, 50)
            points = [TrajectoryPoint(x, y, style) for (x, y) in res["points"]]

            self.result.delete("1.0", tk.END)
            self.result.insert(
                tk.END,
                f"Время полёта: {res['time']:.3f} с\n"
                f"Макс. высота: {res['height']:.3f} м\n"
                f"Дальность: {res['range']:.3f} м\n"
                f"Точек траектории: {len(points)}\n"
                f"Стиль точки (пример): {points[0].style_info()}\n"
                f"Размер кэша стилей: {PointFactory.cache_size()}",
            )
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_cache(self):
        messagebox.showinfo(
            "Приспособленец",
            f"В кэше {PointFactory.cache_size()} общих стилей.\n"
            f"Все точки траектории используют один и тот же объект PointStyle.",
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = TrajectoryApp(root)
    root.mainloop()