import math
import tkinter as tk
from tkinter import messagebox


# ==================== ПАТТЕРН «КОМАНДА» ====================

class TrajectoryService:
    """Получатель команды."""

    def calculate(self, v0, angle):
        raise NotImplementedError

    def points(self, v0, angle, steps):
        raise NotImplementedError


class RealTrajectoryService(TrajectoryService):
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


class Command:
    """Общий интерфейс команды."""

    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    def description(self):
        raise NotImplementedError


class CalculateTrajectoryCommand(Command):
    """Команда расчёта траектории."""

    def __init__(self, service: TrajectoryService, v0, angle, steps):
        self.service = service
        self.v0 = v0
        self.angle = angle
        self.steps = steps
        self.result = None

    def execute(self):
        self.result = self.service.calculate(self.v0, self.angle)
        return self.result

    def undo(self):
        self.result = None

    def description(self):
        return f"Расчёт: v0={self.v0}, angle={self.angle}, steps={self.steps}"


class CommandHistory:
    """История выполненных команд."""

    def __init__(self):
        self.history = []

    def execute(self, command: Command):
        result = command.execute()
        self.history.append(command)
        return result

    def undo_last(self):
        if self.history:
            command = self.history.pop()
            command.undo()
            return command
        return None

    def get_history(self):
        return [cmd.description() for cmd in self.history]

    def clear(self):
        self.history.clear()


# ==================== ПАТТЕРН «ИТЕРАТОР» ====================

class TrajectoryIterator:
    """Итератор для обхода точек траектории."""

    def __init__(self, items):
        self.items = items
        self.index = 0

    def has_next(self):
        return self.index < len(self.items)

    def next(self):
        if not self.has_next():
            raise StopIteration("Точек больше нет")
        item = self.items[self.index]
        self.index += 1
        return item

    def reset(self):
        self.index = 0


class TrajectoryCollection:
    """Коллекция точек траектории."""

    def __init__(self):
        self.items = []

    def add(self, point):
        self.items.append(point)

    def __iter__(self):
        return TrajectoryIterator(self.items)

    def size(self):
        return len(self.items)


# ==================== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ====================

class TrajectoryApp:
    def __init__(self, root):
        self.root = root
        root.title("Траектория движения")

        self.service = RealTrajectoryService()
        self.history = CommandHistory()
        self.collection = TrajectoryCollection()
        self.last_result = None

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
        self.steps_entry.insert(0, "10")
        self.steps_entry.grid(row=2, column=1)

        tk.Button(
            root, text="Выполнить расчёт (команда)", command=self.execute_command
        ).grid(row=3, column=0, columnspan=2, pady=3)
        tk.Button(
            root, text="Отменить последнюю команду", command=self.undo_command
        ).grid(row=4, column=0, columnspan=2)
        tk.Button(
            root, text="Показать историю команд", command=self.show_history
        ).grid(row=5, column=0, columnspan=2)
        tk.Button(
            root, text="Обойти точки (итератор)", command=self.iterate_points
        ).grid(row=6, column=0, columnspan=2)

        self.result = tk.Text(root, width=55, height=14)
        self.result.grid(row=7, column=0, columnspan=2)

    def _read_inputs(self):
        v0 = float(self.v0_entry.get())
        angle = float(self.angle_entry.get())
        steps = int(self.steps_entry.get())
        return v0, angle, steps

    def execute_command(self):
        try:
            v0, angle, steps = self._read_inputs()
            command = CalculateTrajectoryCommand(self.service, v0, angle, steps)
            res = self.history.execute(command)
            self.last_result = res

            # Заполняем коллекцию точек траектории
            self.collection = TrajectoryCollection()
            pts = self.service.points(v0, angle, steps)
            for p in pts:
                self.collection.add(p)

            self.result.delete("1.0", tk.END)
            self.result.insert(
                tk.END,
                f"Команда выполнена:\n{command.description()}\n\n"
                f"Время полёта: {res['time']:.3f} с\n"
                f"Макс. высота: {res['height']:.3f} м\n"
                f"Дальность: {res['range']:.3f} м\n"
                f"Точек в коллекции: {self.collection.size()}\n",
            )
            self.root.update_idletasks()
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def undo_command(self):
        cmd = self.history.undo_last()
        if cmd:
            self.last_result = None
            messagebox.showinfo("Отмена", f"Отменена команда:\n{cmd.description()}")
        else:
            messagebox.showinfo("Отмена", "История команд пуста.")

    def show_history(self):
        log = self.history.get_history()
        text = "\n".join(log) if log else "(история пуста)"
        messagebox.showinfo("История команд", text)

    def iterate_points(self):
        """Демонстрация паттерна Итератор."""
        if self.collection.size() == 0:
            messagebox.showinfo("Итератор", "Коллекция пуста. Сначала выполните расчёт.")
            return

        iterator = self.collection.__iter__()
        self.result.delete("1.0", tk.END)
        self.result.insert(tk.END, "Обход точек через итератор:\n")
        i = 0
        while iterator.has_next():
            x, y = iterator.next()
            self.result.insert(tk.END, f"  {i}: x={x}, y={y}\n")
            i += 1
        self.result.insert(tk.END, f"\nВсего пройдено точек: {i}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrajectoryApp(root)
    root.mainloop()