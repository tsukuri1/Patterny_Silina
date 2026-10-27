import math
import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt


# ==================== ПАТТЕРН «КОМПОНОВЩИК» ====================

class TrajectoryComponent:
    """Общий интерфейс для листа и контейнера."""

    def points(self):
        raise NotImplementedError

    def total_time(self):
        raise NotImplementedError

    def max_height(self):
        raise NotImplementedError

    def flight_range(self):
        raise NotImplementedError


class SimpleSegment(TrajectoryComponent):
    """Лист — один участок траектории."""

    def __init__(self, v0, angle, model):
        self.v0 = v0
        self.angle = angle
        self.model = model

    def points(self):
        return self.model.trajectory_points(self.v0, self.angle, 50)

    def total_time(self):
        return self.model.flight_time(self.v0, self.angle)

    def max_height(self):
        return self.model.max_height(self.v0, self.angle)

    def flight_range(self):
        return self.model.flight_range(self.v0, self.angle)


class CompositeTrajectory(TrajectoryComponent):
    """Контейнер — объединение нескольких участков."""

    def __init__(self):
        self.children = []

    def add(self, component):
        self.children.append(component)

    def remove(self, component):
        self.children.remove(component)

    def points(self):
        result = []
        offset = 0.0
        for child in self.children:
            for (x, y) in child.points():
                result.append((round(x + offset, 3), y))
            offset += child.flight_range()
        return result

    def total_time(self):
        return sum(child.total_time() for child in self.children)

    def max_height(self):
        return max((child.max_height() for child in self.children), default=0.0)

    def flight_range(self):
        return sum(child.flight_range() for child in self.children)


# ==================== ПАТТЕРН «ДЕКОРАТОР» ====================

class MotionModel:
    def flight_time(self, v0, angle):
        raise NotImplementedError

    def max_height(self, v0, angle):
        raise NotImplementedError

    def flight_range(self, v0, angle):
        raise NotImplementedError

    def trajectory_points(self, v0, angle, steps):
        raise NotImplementedError


class IdealModel(MotionModel):
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


class BasicDragModel(MotionModel):
    def __init__(self, g=9.81, k=0.05):
        self.g = g
        self.k = k

    def flight_time(self, v0, angle):
        a = math.radians(angle)
        return 2 * v0 * math.sin(a) / (self.g * (1 + self.k))

    def max_height(self, v0, angle):
        a = math.radians(angle)
        return (v0 ** 2) * (math.sin(a) ** 2) / (2 * self.g * (1 + self.k))

    def flight_range(self, v0, angle):
        a = math.radians(angle)
        return (v0 ** 2) * math.sin(2 * a) / (self.g * (1 + self.k))

    def trajectory_points(self, v0, angle, steps):
        T = self.flight_time(v0, angle)
        a = math.radians(angle)
        pts = []
        for i in range(steps + 1):
            t = T * i / steps
            x = v0 * math.cos(a) * t / (1 + self.k * t)
            y = v0 * math.sin(a) * t - 0.5 * self.g * t ** 2
            pts.append((round(x, 3), round(max(y, 0), 3)))
        return pts


class MotionDecorator(MotionModel):
    """Абстрактный декоратор."""

    def __init__(self, wrapped: MotionModel):
        self.wrapped = wrapped

    def flight_time(self, v0, angle):
        return self.wrapped.flight_time(v0, angle)

    def max_height(self, v0, angle):
        return self.wrapped.max_height(v0, angle)

    def flight_range(self, v0, angle):
        return self.wrapped.flight_range(v0, angle)

    def trajectory_points(self, v0, angle, steps):
        return self.wrapped.trajectory_points(v0, angle, steps)


class DragDecorator(MotionDecorator):
    """Декоратор: добавляет учёт сопротивления воздуха."""

    def __init__(self, wrapped: MotionModel, k=0.1):
        super().__init__(wrapped)
        self.k = k

    def flight_time(self, v0, angle):
        return self.wrapped.flight_time(v0, angle) / (1 + self.k)

    def max_height(self, v0, angle):
        return self.wrapped.max_height(v0, angle) / (1 + self.k)

    def flight_range(self, v0, angle):
        return self.wrapped.flight_range(v0, angle) / (1 + self.k)


class LoggingDecorator(MotionDecorator):
    """Декоратор: добавляет логирование расчётов."""

    def __init__(self, wrapped: MotionModel):
        super().__init__(wrapped)
        self.log = []

    def flight_time(self, v0, angle):
        result = self.wrapped.flight_time(v0, angle)
        self.log.append(f"flight_time({v0}, {angle}) = {result:.3f}")
        return result

    def max_height(self, v0, angle):
        result = self.wrapped.max_height(v0, angle)
        self.log.append(f"max_height({v0}, {angle}) = {result:.3f}")
        return result

    def flight_range(self, v0, angle):
        result = self.wrapped.flight_range(v0, angle)
        self.log.append(f"flight_range({v0}, {angle}) = {result:.3f}")
        return result

    def trajectory_points(self, v0, angle, steps):
        pts = self.wrapped.trajectory_points(v0, angle, steps)
        self.log.append(f"trajectory_points({v0}, {angle}, {steps}) = {len(pts)} точек")
        return pts

    def get_log(self):
        return self.log


# ==================== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ====================

class TrajectoryApp:
    def __init__(self, root):
        self.root = root
        root.title("Траектория движения")

        self.model = IdealModel()
        self.logging = None
        self.segments = []

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

        tk.Label(root, text="Модель:").grid(row=2, column=0, sticky="w")
        self.model_var = tk.StringVar(value="ideal")
        tk.Radiobutton(
            root,
            text="Идеальная",
            variable=self.model_var,
            value="ideal",
            command=self.update_model,
        ).grid(row=2, column=1, sticky="w")
        tk.Radiobutton(
            root,
            text="С сопротивлением",
            variable=self.model_var,
            value="drag",
            command=self.update_model,
        ).grid(row=3, column=1, sticky="w")

        self.drag_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            root,
            text="Добавить сопротивление (декоратор)",
            variable=self.drag_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w")

        self.log_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            root,
            text="Включить логирование (декоратор)",
            variable=self.log_var,
        ).grid(row=5, column=0, columnspan=2, sticky="w")

        tk.Button(
            root, text="Добавить участок в компоновщик", command=self.add_segment
        ).grid(row=6, column=0, columnspan=2, pady=3)
        tk.Button(root, text="Рассчитать", command=self.calculate).grid(
            row=7, column=0, columnspan=2, pady=3
        )

        self.result = tk.Text(root, width=55, height=14)
        self.result.grid(row=8, column=0, columnspan=2)

    def update_model(self):
        if self.model_var.get() == "ideal":
            self.model = IdealModel()
        else:
            self.model = BasicDragModel()

    def _build_model(self):
        """Навешиваем декораторы на базовую модель."""
        model = self.model
        if self.drag_var.get():
            model = DragDecorator(model)
        if self.log_var.get():
            self.logging = LoggingDecorator(model)
            model = self.logging
        else:
            self.logging = None
        return model

    def _read_inputs(self):
        v0 = float(self.v0_entry.get())
        angle = float(self.angle_entry.get())
        if v0 <= 0:
            raise ValueError("Скорость должна быть > 0")
        if not (0 < angle < 90):
            raise ValueError("Угол должен быть в диапазоне (0; 90)")
        return v0, angle

    def add_segment(self):
        """Добавляем очередной участок в компоновщик."""
        try:
            v0, angle = self._read_inputs()
            model = self._build_model()
            segment = SimpleSegment(v0, angle, model)
            self.segments.append(segment)
            messagebox.showinfo(
                "Компоновщик",
                f"Участок добавлен. Всего участков: {len(self.segments)}",
            )
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))

    def calculate(self):
        try:
            if not self.segments:
                v0, angle = self._read_inputs()
                model = self._build_model()
                segment = SimpleSegment(v0, angle, model)
                self.segments.append(segment)

            composite = CompositeTrajectory()
            for seg in self.segments:
                composite.add(seg)

            total_time = composite.total_time()
            height = composite.max_height()
            distance = composite.flight_range()
            pts = composite.points()

            self.result.delete("1.0", tk.END)
            self.result.insert(
                tk.END,
                f"Участков: {len(self.segments)}\n"
                f"Суммарное время: {total_time:.3f} с\n"
                f"Макс. высота: {height:.3f} м\n"
                f"Общая дальность: {distance:.3f} м\n",
            )

            if self.logging:
                self.result.insert(tk.END, "\nЛог декоратора:\n")
                for line in self.logging.get_log():
                    self.result.insert(tk.END, "  " + line + "\n")

            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            plt.plot(xs, ys, marker="o", markersize=3)
            plt.title("Составная траектория")
            plt.xlabel("X, м")
            plt.ylabel("Y, м")
            plt.grid(True)
            plt.axis("equal")
            plt.show()
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = TrajectoryApp(root)
    root.mainloop()