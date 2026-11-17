import csv
import numpy as np
from config import PATTERNS


class CyberGameOfLife:
    def __init__(self, size=50, p=0.25, seed=42):
        self.size = size
        self.p = p
        self.seed = seed
        self.rule_name = "Conway (B3/S23)"
        self.boundary = "Тор"
        self.preset_name = "Випадково"
        self.brush_mode = "1 Кубик"
        self.paused = False
        self.stabilized_at = None

        self.apply_preset("Випадково")

    def apply_preset(self, preset_name):
        self.preset_name = preset_name
        self.generation = 0
        self.stabilized_at = None
        self.history = []
        self.gens = []
        self.alives = []
        self.changes = []

        if preset_name == "Випадково":
            rng = np.random.default_rng(self.seed)
            self.grid = rng.choice([0, 1], size=(self.size, self.size), p=[1 - self.p, self.p])
        elif preset_name == "Порожнє поле":
            self.grid = np.zeros((self.size, self.size), dtype=int)
        else:
            self.grid = np.zeros((self.size, self.size), dtype=int)
            for r, c in PATTERNS[preset_name]:
                if r < self.size and c < self.size:
                    self.grid[r, c] = 1

        self.age_grid = self.grid.copy().astype(int)
        self.trail_grid = self.grid.astype(float)
        self._record_metrics(born=int(np.sum(self.grid)), died=0)

    def _record_metrics(self, born, died):
        alive = int(np.sum(self.grid))
        density = round(alive / (self.size * self.size), 4)
        self.history.append((self.generation, alive, born, died, density))
        self.gens.append(self.generation)
        self.alives.append(alive)
        self.changes.append(born + died)

    def count_neighbors(self):
        pad_mode = "wrap" if self.boundary == "Тор" else "constant"
        padded = np.pad(self.grid, pad_width=1, mode=pad_mode)
        return (
            padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
            padded[1:-1, :-2]                    + padded[1:-1, 2:] +
            padded[2:, :-2]  + padded[2:, 1:-1]  + padded[2:, 2:]
        )

    def step(self):
        neighbors = self.count_neighbors()
        alive_mask = self.grid == 1

        if self.rule_name == "Conway (B3/S23)":
            birth = (~alive_mask) & (neighbors == 3)
            survival = alive_mask & ((neighbors == 2) | (neighbors == 3))
        elif self.rule_name == "HighLife (B36/S23)":
            birth = (~alive_mask) & ((neighbors == 3) | (neighbors == 6))
            survival = alive_mask & ((neighbors == 2) | (neighbors == 3))
        else:  # "Seeds (B2/S)"
            birth = (~alive_mask) & (neighbors == 2)
            survival = np.zeros_like(alive_mask, dtype=bool)

        new_grid = (birth | survival).astype(int)

        new_age = np.zeros_like(self.age_grid)
        new_age[survival] = self.age_grid[survival] + 1
        new_age[birth] = 1
        self.age_grid = new_age

        self.trail_grid = np.maximum(new_grid.astype(float), self.trail_grid * 0.55)

        born_count = int(np.sum((self.grid == 0) & (new_grid == 1)))
        died_count = int(np.sum((self.grid == 1) & (new_grid == 0)))

        self.grid = new_grid
        self.generation += 1
        self._record_metrics(born_count, died_count)

        if born_count == 0 and died_count == 0 and self.stabilized_at is None:
            self.stabilized_at = self.generation

    def apply_brush(self, row, col, erase=False):
        if erase:
            r0, r1 = max(0, row - 1), min(self.size, row + 2)
            c0, c1 = max(0, col - 1), min(self.size, col + 2)
            self.grid[r0:r1, c0:c1] = 0
            self.age_grid[r0:r1, c0:c1] = 0
            self.trail_grid[r0:r1, c0:c1] = 0
            return

        if self.brush_mode == "1 Кубик":
            self.grid[row, col] = 1
            self.age_grid[row, col] = 1
            self.trail_grid[row, col] = 1.0
        elif self.brush_mode == "Глайдер":
            for dr, dc in ((0, 1), (1, 2), (2, 0), (2, 1), (2, 2)):
                rr, cc = (row + dr) % self.size, (col + dc) % self.size
                self.grid[rr, cc] = 1
                self.age_grid[rr, cc] = 1
                self.trail_grid[rr, cc] = 1.0
        elif self.brush_mode == "Хаос-бомба":
            rng = np.random.default_rng()
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    if rng.random() > 0.45:
                        rr, cc = (row + dr) % self.size, (col + dc) % self.size
                        self.grid[rr, cc] = 1
                        self.age_grid[rr, cc] = 1
                        self.trail_grid[rr, cc] = 1.0

    def export_csv(self, filename="simulation_history.csv"):
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Generation", "Alive_A(t)", "Born", "Died", "Density"])
            writer.writerows(self.history)
        print(f"[OK] Збережено {len(self.history)} кроків у '{filename}'")
