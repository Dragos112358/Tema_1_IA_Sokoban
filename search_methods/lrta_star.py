import itertools
import sys
import time
from search_methods import heuristics #de aici folosesc manhattan_distance, bfs_distance, astar_distance si smart_manhattan_distance
from sokoban import Map, create_gif
from collections import deque
import random
import itertools
import pandas as pd
initial_box_target_mapping = {}
nume_test = ' ' #numele testului
perm=0
def bfs_simple2(map_obj, start, goal):
    directions = [(-1,0), (1,0), (0,-1), (0,1)] #bfs clasic, in care returnez calea
    queue = deque([start])
    visited = {start: None}
    posBox = map_obj.get_box_positions()
    posBox = [(box.x, box.y) for box in posBox]
    while queue: #folosesc o coada
        x, y = queue.popleft()
        if (x, y) == goal: #gasesc calea la goal, salvez pathul
            path = []
            current = (x, y)
            while current is not None:
                path.append(current)
                current = visited[current]
            return len(path), path[::-1] #intorc lungimea caii si calea inversata
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            #verific ca ceea ce vizitez sa fie pe harta, nu perete si nu cutie
            if (0 <= nx < map_obj.get_height() and 0 <= ny < map_obj.get_width()
                and (nx, ny) not in visited
                and map_obj.get_positions(nx, ny) !=-1
                and (nx, ny) not in posBox):
                visited[(nx, ny)] = (x, y)
                queue.append((nx, ny))
    return float('inf'), []
def is_obstacle_between(x1, y1, x2, y2, map):
    """
    Verific daca exista obstacole între doua puncte (x1, y1) si (x2, y2)
    pe o harta, folosind verificarea directa a peretelui.
    """
    if x1 == x2:  # Daca sunt pe aceeasi coloana
        for y in range(min(y1, y2) + 1, max(y1, y2)):  # Verific între y1 si y2
            if (x1, y) in map.get_walls() or (x1, y) in map.get_box_positions():
                return True  # Daca gasesc un obstacol, returnez True
    elif y1 == y2:  # Daca sunt pe aceeasi linie
        for x in range(min(x1, x2) + 1, max(x1, x2)):  # Verific între x1 si x2
            if (x, y1) in map.get_walls() or (x, y1) in map.get_box_positions():
                return True  # Daca gaseste un obstacol, returneaza True

    return False  # Nu exista obstacole între cele doua puncte


def is_deadlocked_box(map: Map) -> bool:
    """
    Verifica daca vreo cutie este blocata complet (nu poate fi mutata în nicio directie)
    si daca jucatorul nu poate ajunge la ea.
    """
    boxes = map.get_box_positions()
    player_pos = map.get_player_position()

    def is_valid_position(x, y):
        """Verifica daca pozitia este valida pe harta."""
        return 0 <= x < map.get_height() and 0 <= y < map.get_width() and map.get_positions(x, y) != -1

    def can_player_reach_box(box_x, box_y):
        """Verific daca jucatorul poate ajunge la cutie (box_x, box_y)."""
        visited = set()
        queue = deque([player_pos])  # incepem cautarea de la pozitia jucatorului
        while queue:
            x, y = queue.popleft()
            if (x, y) == (box_x, box_y):  # Daca jucatorul ajunge la cutie
                return True
            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Adaug vecinii jucatorului la coada (directii: stanga, dreapta, sus, jos)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if is_valid_position(nx, ny) and (nx, ny) not in visited:
                    queue.append((nx, ny))
                    queue.append((nx, ny))
        return False  # Daca jucatorul nu ajunge la cutie

    # Verific fiecare cutie
    for i, box in enumerate(boxes):
        target = initial_box_target_mapping[i]
        x, y = box.x, box.y
        # Vecinii cutiei
        left = map.get_positions(x, y-1)
        right = map.get_positions(x, y+1)
        up = map.get_positions(x+1, y)
        down = map.get_positions(x-1, y)
        # Cutia e prinsa între doua obstacole sau alte cutii (blocata la colt)
        if ((left == -1 and up == -1) or (left == -1 and down == -1) or \
           (right == -1 and up == -1) or (right == -1 and down == -1))\
                and (x,y) != target:
            return True
            # Daca jucatorul nu poate ajunge la cutie si cutia nu este pe o tinta
        if (x, y) not in map.get_target_positions() and not can_player_reach_box(x, y):
            return True  # Cutia este blocata
        is_on_edge = (x == 0 or x == map.get_height() - 1 or y == 0 or y == map.get_width() - 1)
        if is_on_edge: #ma_aflu pe margine
            target_x, target_y = target[0], target[1]
            # Verificam daca tinta este pe aceeasi margine
            target_on_edge = (
                        target_x == 0 or target_x == map.get_height() - 1 or target_y == 0 or target_y == map.get_width() - 1)
            if not target_on_edge:
                return True
            else:
                if is_obstacle_between(x, y, target_x, target_y, map):
                    return True

    return False  # Nu sunt cutii blocata complet



def initialize_box_target_mapping(state: Map, target_permutation=None):
    """
    Initializeaza mapping-ul între cutii si targeturi.
    """
    box_positions = [(box.x, box.y) for box in state.get_box_positions()]
    target_positions = [(t[0], t[1]) for t in state.get_target_positions()]
    if target_permutation is None:
        # Daca nu este data o permutare, o generez aleator
        target_permutation = random.sample(target_positions, len(target_positions))
    if len(box_positions) != len(target_positions):
        raise ValueError("Numarul de cutii nu se potriveste cu numarul de tinte.")
    # Construiesc o lista de targeturi asociata fiecarei cutii în ordinea permutarii
    mapping = []
    for i, box in enumerate(box_positions):
        # Asociez fiecare cutie unui target din permutare
        target = target_positions[target_permutation[i]]  # targetul asociat cutiei
        mapping.append(target)  # Adaug coordonatele targetului în lista
    return mapping
def get_general_direction(box, target):
    (x, y) = box
    (x1, y1) = target

    if x == x1:
        if y1 > y:
            return (0,-1)
        elif y1 < y:
            return (0,1)
    elif y == y1:
        if x1 > x:
            return (-1,0)
        elif x1 < x:
            return (1,0)
    else:
        return None  # nu sunt pe aceeasi linie/coloana
def no_boxes_around(pos, box_positions):
    #functie care imi verifica ca in jurul unei cutii nu am alte cutii
    x, y = pos
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # dreapta, stanga, jos, sus

    for dx, dy in directions:
        neighbor = (x + dx, y + dy)
        if neighbor in box_positions:
            return False  # exista o cutie în jur
    return True  # niciuna în jur

def heuristic(state: Map,target_permutation):
    global initial_box_target_mapping
    box_positions = [(box.x, box.y) for box in state.get_box_positions()] #pozitii cutii
    initial_box_target_mapping = initialize_box_target_mapping(state, target_permutation)
    if is_deadlocked_box(state):
        #daca cutia este blocata, scor mare, nu o iau pe acolo
        return float('inf')
    total = 0
    for i, box in enumerate(box_positions):
        target = initial_box_target_mapping[i]
        #dist=heuristics.manhattan_distance(box,[target],state)
        dist = heuristics.astar_distance(box, [target], state)
        #dist=heuristics.bfs_distance(box,[target],state)
        (x1,y1)=Map.get_player_position(state)
        rez= None
        if box not in target: #daca cutia nu este in target, iau directia generala
            rez=get_general_direction(box,target)
        dist2=0
        x2,y2=box
        if rez !=None and rez[0]==1:
            x3,y3=rez
            #pentru fiecare cutie, aplic bfs pentru a vedea ca am acces la ea
            dist2 = heuristics.bfs_real((x1, y1), [(x2+x3,y2+y3)], state)
        if dist2 > 10000 and no_boxes_around(box,box_positions): #nu am acces la cutie
            return float('inf')
        if dist == 0: #distanta 0 => ma aflu pe target
            total -= 1
        total += 3.1 ** dist
    #energia totala a unei stari
    return total

def lrta_star(start_state: Map, max_steps: int = 100000):
    explored_states_count = 0 #nr stari explorate
    goals = start_state.get_target_positions()
    goal_positions = [(goal[0], goal[1]) for goal in goals] #salvez tintele
    toate_permutarile = list(itertools.permutations(range(len(goal_positions))))
    for perm in toate_permutarile:
        H = {}  # Euristica învatata
        current_state = start_state.copy()
        path = [current_state]
        boxes = {(box.x, box.y) for box in current_state.get_box_positions()}
        def closest_box_distance(state):
            """Distanta fata de cea mai apropiata cutie (de tip manhattan)
            Functie folosita pentru tiebreaker intre 2 stari cu aceeasi energie
            M-a ajutat pentru hard_map1"""
            state_pos = state.get_player_position()
            #returnez distanta manhattan pana la cea mai apropiata cutie
            return min(abs(state_pos[0] - box[0]) + abs(state_pos[1] - box[1]) for box in boxes)
        for step in range(max_steps):
            explored_states_count += 1
            if current_state.is_solved(): #daca este rezolvat
                explored_states_count += 1
                print(f"Rezolvat cu permutarea {perm} în {step} pasi!")
                #returnez calea, nr_de stari explorate, True (rezolvat) si permutarea buna
                return path, explored_states_count, True, perm
            state_str = str(current_state)
            if state_str not in H:
                #aplic euristica pentru invatare pe starea curenta
                H[state_str] = heuristic(current_state, perm)
            neighbours = current_state.get_neighbours()
            best_cost = float('inf')
            best_neighbour = None
            #iterez in vecini
            for neighbour in neighbours:
                neighbour_str = str(neighbour)
                h = H.get(neighbour_str, heuristic(neighbour, perm))
                cost = 1 + h
                #gasesc valoarea euristicii si costu;
                if cost < best_cost:
                    #salvez costul mai bun
                    best_cost = cost
                    best_neighbour = neighbour
                elif cost == best_cost: #situatie de tiebreaker
                    current_dist = closest_box_distance(current_state)
                    #gasesc distanta minima
                    neighbour_dist = closest_box_distance(neighbour)
                    #daca distanta este mai mica
                    if neighbour_dist < current_dist or (neighbour_dist == current_dist and neighbour < best_neighbour):
                        best_neighbour = neighbour
            H[state_str] = best_cost
            if best_neighbour is None:
                #daca nu gaseste vecin bun, inseamna ca toti au cost +inf => nu gaseste vecini valizi
                print("Blocaj. Nu exista vecini valizi.")
                break
            current_state = best_neighbour
            path.append(current_state) #adaug vecinul cel mai bun
        explored_states_count += 1
    print("Nicio permutare nu a dus la o solutie.")
    return path, explored_states_count, False, perm #returnez False, adica nu este rezolvat

def get_direction(from_pos, to_pos):
    #functie care imi da directia intre 2 puncte vecine
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]
    if dx == -1: return 'd'
    if dx == 1:  return 'u'
    if dy == -1: return 'l'
    if dy == 1:  return 'r'
    return '?'  # pentru cazuri neprevazute
# Codificarea mutarilor
important_states = []
unique_states = []
global move_sequence
global sol
global solution_steps
import tkinter as tk
from PIL import ImageTk
import os
from PIL import Image

def interfata_grafica(base_name):
    # Directorul în care se afla acest script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construiesc calea corecta catre folderul Images
    save_path = os.path.join(script_dir, "..", "Images", base_name)
    save_path = os.path.normpath(save_path)  # normalizare
    gif_path = os.path.join(save_path, "solution.gif") #calea gif-ului
    if os.path.exists(gif_path):
        gif = Image.open(gif_path)
    gif_path = os.path.join(save_path, "solution.gif")
    # Creare fereastra Tkinter
    root = tk.Tk()
    root.title("Vizualizare Solutie Sokoban")
    # Label pentru afisarea GIF-ului
    img_label = tk.Label(root)
    img_label.pack()
    # incarcare GIF si obtinerea cadrelor
    gif = Image.open(gif_path)
    frames = []
    try:
        while True:
            frames.append(ImageTk.PhotoImage(gif.copy()))
            gif.seek(len(frames))  # Merg la urmatorul frame
    except EOFError:
        pass  # Sfarsitul GIF-ului
    # Index pentru frame-ul curent
    current_frame = 0
    # Functie pentru redarea animatiei
    def update_image(index):
        """Actualizez imaginea afişata."""
        global current_frame
        if 0 <= index < len(frames):
            img_label.config(image=frames[index])
            current_frame = index
    # Functie pentru a merge la imaginea anterioara
    def prev_frame():
        global current_frame
        if current_frame > 0:
            update_image(current_frame - 1)
    # Functie pentru a merge la imaginea urmatoare
    def next_frame():
        global current_frame
        if current_frame < len(frames) - 1: #actualizez frameul curent
            update_image(current_frame + 1)

    # Butoane pentru navigare
    btn_prev = tk.Button(root, text="<< Anterior", command=prev_frame)
    btn_prev.pack(side=tk.LEFT, padx=10)
    btn_next = tk.Button(root, text="Urmator >>", command=next_frame)
    btn_next.pack(side=tk.RIGHT, padx=10)
    # Initializare cu prima imagine
    if frames:
        update_image(current_frame)
    # Start loop Tkinter
    root.mainloop()

def generate_permutations(target_positions):
    #generare lista de permutari
    return list(itertools.permutations(target_positions))
def main():
    global base_name
    name_test = ''
    if len(sys.argv) > 1:
        name_test = sys.argv[1] #nume test
    else:
        print("Argumentul lipseste!")
    if name_test == '':
        name_test = 'large_map1' #default large_map1
    name_test += '.yaml'
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                               '..'))
    # 1 nivel în sus pentru a ajunge în directorul radacina al proiectului
    map_path = os.path.join(project_dir, 'Tema 1 IA', 'tests', name_test)
    move_sequence = ""
    solution_steps=[]
    sol=[]
    # Calea catre fisierul YAML
    global nume_test
    nume_test = os.path.basename(map_path)
    # Extrag numele testului din fisier (fara extensia .yaml)
    test_name = os.path.splitext(os.path.basename(map_path))[0]
    base_name = test_name.replace('.yaml', '')
    # incarc harta
    game_map = Map.from_yaml(map_path)
    important_states.append(game_map)
    # Rulez LRTA*
    print("Pornesc algoritmul LRTA*...")
    time_start = time.time()
    goals = game_map.get_target_positions()
    goal_positions = [(goal[0], goal[1]) for goal in goals]
    #aplic lrta pe harta de joc
    path, nr_stari, is_solved,perm = lrta_star(game_map, max_steps=1000)
    time_end=time.time()

    # Creeaza folderul unde se salveaza imaginile
    script_dir = os.path.dirname(os.path.abspath(__file__))  # directorul curent al fisierului .py
    save_folder = os.path.normpath(os.path.join(script_dir, "..", "Images", test_name))
    os.makedirs(save_folder, exist_ok=True)
    # Afisez si salvez fiecare stare
    for i in range(len(path) - 1):
        curr = path[i]
        next_ = path[i + 1]
        player_curr = curr.get_player_position() #pozitie player curenta
        player_next = next_.get_player_position() #pozitie viitoare
        dir_char = get_direction((player_curr[0], player_curr[1]), (player_next[0], player_next[1]))
        # Daca o cutie s-a mutat si e în acea directie => push
        boxes_curr = {(b.x, b.y) for b in curr.get_box_positions()}
        boxes_next = {(b.x, b.y) for b in next_.get_box_positions()}
        # Cutia mutata = diferenta dintre pozitiile cutiilor
        moved_boxes = boxes_next - boxes_curr
        pushed = False
        for box in moved_boxes:
            # daca cutia s-a mutat în directia jucatorului
            expected_new_box_pos = (player_next[0] + (player_next[0] - player_curr[0]),
                                    player_next[1] + (player_next[1] - player_curr[1]))
            if box == expected_new_box_pos:
                pushed = True #daca cutia se muta, am dat push
                break
        if pushed:
            move_sequence += dir_char.upper() #directia mutata cu litera mare
            important_states.append(curr) #adaug ambele stari
            important_states.append(next_)
        else:
            move_sequence += dir_char #altfel, doar playerul se misca (codificare cu litera mica)
    seen = set()
    min=float('inf')
    #in acest for, extrag starile unice
    for state in important_states:
        key = str(state)
        #daca cheia nu exista, o adaug
        if key not in seen and heuristic(state, perm)<=min:
            seen.add(key)
            unique_states.append(state)
    for i in range(len(important_states) - 1):
        state = important_states[i]
        print("Stari:")
        print(state)
        print("Scor stare: " +str(heuristic(state,perm)))
        state2 = important_states[i + 1]
        x1, y1 = state.get_player_position()
        x2, y2 = state2.get_player_position()
        #aplic bfs_simple2 intre cele 2 pozitii ale playerului
        _, cale = bfs_simple2(state, (x1, y1), (x2, y2))
        posBox = state.get_box_positions()
        posBox = [(box.x, box.y) for box in posBox]
        if (x2, y2) in posBox: #inseamna ca am dat push la o cutie
            ok = 0
            x1, y1 = state.get_player_position()
            x2, y2 = state2.get_player_position()
            #push la cutie = codificare cu litera mare
            if (x1 == x2 and y2 == y1 + 1):
                sol.append('R')
                ok = 1
            if (x1 == x2 and y1 == y2 + 1):
                sol.append('L')
                ok = 1
            if (y1 == y2 and x1 == x2 + 1):
                sol.append('D')
                ok = 1
            if (y1 == y2 and x2 == x1 + 1):
                sol.append('U')
                ok = 1
            if ok == 0: #cutia a fost mutata mai mult
                #print("NU FACE NIMIC")
                posBox1 = state.get_box_positions()
                posBox1 = [(box.x, box.y) for box in posBox1]
                posBox2 = state2.get_box_positions()
                posBox2 = [(box.x, box.y) for box in posBox2]
                for i in range(len(posBox1)):
                    if posBox1[i] != posBox2[i]: #cutia s-a mutat
                        #print(f"Cutia {i} s-a mutat de la {posBox1[i]} la {posBox2[i]}")
                        dx = posBox2[i][0] - posBox1[i][0]
                        dy = posBox2[i][1] - posBox1[i][1]
                        posPlayer_after = (posBox1[i][0] - dx, posBox1[i][1] - dy)
                        #print(posPlayer_after)
                        x1, y1 = state.get_player_position()
                        _, cale5 = bfs_simple2(state, (x1, y1), posPlayer_after)
                        #noua cale a playerului
                        for i in range(len(cale5) - 1):
                            coord1 = cale5[i]
                            coord2 = cale5[i + 1]
                            x1, y1 = coord1
                            x2, y2 = coord2
                            #dau append la litere mici (playerul se misca fara cutie)
                            if (x1 == x2 and y2 == y1 + 1):
                                sol.append('r')
                            if (x1 == x2 and y1 == y2 + 1):
                                sol.append('l')
                            if (y1 == y2 and x1 == x2 + 1):
                                sol.append('d')
                            if (y1 == y2 and x2 == x1 + 1):
                                sol.append('u')
                # daca cutia se muta doar cu o pozitie
                #se misca atat playerul, cat si cutia
                if dx == -1 and dy == 0:
                    sol.append('D')
                if dx == 1 and dy == 0:
                    sol.append('U')
                if dx == 0 and dy == 1:
                    sol.append('R')
                else:
                    sol.append('L')
        else:
            _, cale2 = bfs_simple2(state, (x1, y1), (x2, y2))
            #un alt bfs intre player_initial si player_final
            for i in range(len(cale2) - 1):
                coord1 = cale2[i]
                coord2 = cale2[i + 1]
                x1, y1 = coord1
                x2, y2 = coord2
                #in aceste if-uri, doar playerul se deplaseaza
                if (x1 == x2 and y2 == y1 + 1):
                    sol.append('r')
                if (x1 == x2 and y1 == y2 + 1):
                    sol.append('l')
                if (y1 == y2 and x1 == x2 + 1):
                    sol.append('d')
                if (y1 == y2 and x2 == x1 + 1):
                    sol.append('u')
                if (x1, y1) in state.positions_of_boxes:
                    box_name = state.positions_of_boxes[(x1, y1)]
                    box = state.boxes[box_name]
    print("\n🔢 Secventa de miscari (player):")
    print(move_sequence)
    #move_sequence are toate mutarile efectuate de lrta pana la destinatie
    #sol are mutarile optimizate (lrta exploreaza foarte mult si ar fi contraproductiv
    #sa am 952 de gif-uri pentru large_map2
    print("\n🔢 Secventa de miscari usoara:")
    print("".join(sol))

    print(f"Numar total de stari explorate: {nr_stari}")

    print('Runtime of LRTA*: %.2f second.' % (time_end - time_start))
    den_test=sys.argv[1]
    rezultate = {
        'nume_test':[den_test],
        'miscari': ["".join(sol)],
        'numar_stari_explorate': [nr_stari],
        'runtime_secunde': [round(time_end - time_start, 2)]
    }
    #Îl pun într-un DataFrame
    df = pd.DataFrame(rezultate)
    fisier_csv = 'rezultate_LRTA.csv'
    if not os.path.isfile(fisier_csv):
        # Daca NU exista, scriu cu header
        df.to_csv(fisier_csv, index=False)
    else:
        # Daca exista, adăug (append) fără header
        df.to_csv(fisier_csv, mode='a', header=False, index=False)
    df_total = pd.read_csv(fisier_csv)
    # Sortez după 'nume_test' și 'Tip'
    df_total = df_total.sort_values(by=['Tip', 'nume_test'])
    # Salvez sortat înapoi
    df_total.to_csv(fisier_csv, index=False)
    print("Am adaugat in CSV")
    MOVE_MAPPING = {
        'l': 1,  # Stanga
        'r': 2,  # Dreapta
        'u': 3,  # Sus
        'd': 4,  # Jos
        'L': 5,  # Stanga cu cutie
        'R': 6,  # Dreapta cu cutie
        'U': 7,  # Sus cu cutie
        'D': 8
        # Jos cu cutie
    }
    # print(moves)
    test_map = Map.from_yaml(map_path)
    solution_steps.append(test_map.copy())
    for move in sol:
        if move not in MOVE_MAPPING:  # Verific daca miscarea este valida
            raise ValueError(f"Invalid move character: {move}")
        numeric_move = MOVE_MAPPING[move]  # Convertesc miscarea în numar
        test_map.apply_move(numeric_move)  # Aplic miscarea numerica
        solution_steps.append(test_map.copy())  # Salvez noua stare
    # Creez gif animat
    print("\nCream gif-ul animat...")
    for idx, state in enumerate(solution_steps):
        state.save_map(save_folder, f"step_{idx:03d}")
    gif_path = os.path.join(save_folder)
    absolute_gif_path = os.path.abspath(gif_path)
    create_gif(absolute_gif_path, "solution.gif", gif_path)
    print(f"\n✅ Solutia a fost salvata în {absolute_gif_path}")
    interfata_grafica(base_name)
if __name__ == "__main__":
    main()


