import os
import sys
import matplotlib
import yaml
import imageio

from search_methods.solver import Solver

src_path = os.path.join(os.path.dirname(__file__), 'search_methods')
sys.path.append(src_path)
from sokoban import (
    Box,
    DOWN,
    Map,
    Player
)

if __name__ == '__main__':
    # Argument parsing
    if len(sys.argv) < 3:
        print("Usage: python3 main.py [simulated_annealing|lrta] [map_filename fara .yaml la final]")
        sys.exit(1)

    method = sys.argv[1].lower()
    map_file = sys.argv[2]  # map_file e numele testului YAML (ex: easy_map1.yaml)
    # Creez Solver cu numele fișierului YAML
    solver = Solver(map_file)
    # Apelez solve
    solver.solve(method)