import math
import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt

G = 9.81


class TrajectoryCalculator:
    """Класс для расчёта траектории. Реализует паттерн Singleton."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def validate_input(self, v0, angle_deg):
        """Проверка корректности входных данных."""
        if v0 <= 0:
            raise ValueError("Начальная скорость должна быть > 0")
        if not (0 < angle_deg < 90):
            raise ValueError("Угол должен быть в диапазоне (0; 90)")
        return True

    def flight_time(self, v0, angle_deg):
        """Время полёта тела."""
        self.validate_input(v0, angle_deg)
        angle_rad = math.radians(angle_deg)
        return 2 * v0 * math.sin(angle_rad) / G

    def max_height(self, v0, angle_deg):
        """Максимальная высота подъёма."""
        self.validate_input(v0, angle_deg)
        angle_rad = math.radians(angle_deg)
        return (v0 ** 2) * (math.sin(angle_rad) ** 2) / (2 * G)

    def flight_range(self, v0, angle_deg):
        """Дальность полёта."""
        self.validate_input(v0, angle_deg)
        angle_rad = math.radians(angle_deg)
        return (v0 ** 2) * math.sin(2 * angle_rad) / G

    def trajectory_point(self, v0, angle_deg, t):
        """Координаты точки траектории в момент времени t."""
        self.validate_input(v0, angle_deg)
        if t < 0 or t > self.flight_time(v0, angle_deg):
            raise ValueError("Время вне интервала полёта")
        angle_rad = math.radians(angle_deg)
        x = v0 * math.cos(angle_rad) * t
        y = v0 * math.sin(angle_rad) * t - 0.5 * G * t ** 2
        return round(x, 3), round(y, 3)

    def build_trajectory(self, v0, angle_deg, steps=20):
        """Список точек траектории."""
        T = self.flight_time(v0, angle_deg)
        return [
            self.trajectory_point(v0, angle_deg, T * i / steps)
            for i in range(steps + 1)
        ]

    def plot_trajectory(self, v0, angle_deg, steps=50):
        """Построение графика траектории."""
        pts = self.build_trajectory(v0, angle_deg, steps)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        plt.plot(xs, ys, marker='o', markersize=3)
        plt.title(f"Траектория: v0={v0} м/с, угол={angle_deg}°")
        plt.xlabel("X, м")
        plt.ylabel("Y, м")
        plt.grid(True)
        plt.axis('equal')
        plt.show()


class TrajectoryApp:
    """Класс графического интерфейса."""

    def __init__(self, root):
        self.root = root
        self.calculator = TrajectoryCalculator()

        root.title("Траектория движения")

        tk.Label(root, text="Начальная скорость (м/с):").grid(
            row=0, column=0, sticky="w")
        self.v0_entry = tk.Entry(root)
        self.v0_entry.grid(row=0, column=1)

        tk.Label(root, text="Угол броска (°):").grid(
            row=1, column=0, sticky="w")
        self.angle_entry = tk.Entry(root)
        self.angle_entry.grid(row=1, column=1)

        tk.Button(root, text="Рассчитать", command=self.calculate).grid(
            row=2, column=0, columnspan=2, pady=5)

        self.result = tk.Text(root, width=40, height=10)
        self.result.grid(row=3, column=0, columnspan=2)

    def calculate(self):
        try:
            v0 = float(self.v0_entry.get())
            angle = float(self.angle_entry.get())

            self.calculator.validate_input(v0, angle)
            T = self.calculator.flight_time(v0, angle)
            H = self.calculator.max_height(v0, angle)
            L = self.calculator.flight_range(v0, angle)

            self.result.delete("1.0", tk.END)
            self.result.insert(
                tk.END,
                f"Время полёта: {T:.3f} c\n"
                f"Макс. высота: {H:.3f} м\n"
                f"Дальность: {L:.3f} м\n",
            )
            self.calculator.plot_trajectory(v0, angle)
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception:
            messagebox.showerror("Ошибка", "Некорректные данные")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrajectoryApp(root)
    root.mainloop()