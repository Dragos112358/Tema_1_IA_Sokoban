import os
import sys
from sokoban.map import Map

class Solver:

    def __init__(self, map_file: str) -> None:
        self.map_file = map_file  # exemplu: 'easy_map1'

    def solve(self, method: str):
        print(f"Solver started with method '{method}'")

        base_dir = os.path.dirname(__file__)

        if method == "simulated_annealing":
            script_path = os.path.join(base_dir, "simulated_annealing.py")
        elif method == "lrta":
            script_path = os.path.join(base_dir, "lrta_star.py")
        else:
            raise ValueError(f"Unknown method '{method}'. Use 'simulated_annealing' or 'lrta'.")

        # citesc scriptul
        with open(script_path, encoding="utf-8") as f:
            code = f.read()

        # setez contextul global pentru exec
        globals()["__file__"] = script_path
        globals()["__name__"] = "__main__"

        # aici setezi ARGUMENTELE exact cum vrei tu:
        sys.argv = [script_path, self.map_file]

        print(f"Executing {script_path} with map {self.map_file}")
        exec(code, globals())
