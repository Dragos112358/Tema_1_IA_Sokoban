
import sys
import time
from collections import defaultdict
from copy import deepcopy
from search_methods import heuristics
from sokoban import Map, save_images, create_gif
from itertools import permutations
import numpy as np
import random
import math
import pandas as pd
val_mare = 10000000000000000 #daca blochez cutia
a  = []
def remove_duplicates(states): #folosit la final, cand returnez starile din annealing
    seen = set()
    unique_states = []
    for s in states:
        if str(s) not in seen:
            unique_states.append(s) #adaug stari unice
            seen.add(str(s))
    return unique_states

def is_box_stuck(map: Map) -> bool:
    """
    Verifica daca vreo cutie este blocata complet (nu poate fi mutata in nicio directie).
    """
    boxes = map.get_box_positions()
    for box in boxes:
        x, y = box.x, box.y
        # Vecinii cutiei in forma de cruce
        left = map.get_positions(x - 1, y)
        right = map.get_positions(x + 1, y)
        up = map.get_positions(x, y - 1)
        down = map.get_positions(x, y + 1)

        # Cutia e prinsa intre doua obstacole pe parti opuse
        if (left == -1 and right == -1) or (up == -1 and down == -1):
            return True

        # Cutia e prinsa la colt si nu e pe o tinta
        if (left == -1 and up == -1) or (left == -1 and down == -1) or \
                (right == -1 and up == -1) or (right == -1 and down == -1):
            if (x, y) not in map.get_target_positions():
                return True
    return False


def este_push_valid(test_map, start_box, end_box):
    dx = end_box[0] - start_box[0]
    dy = end_box[1] - start_box[1]
    # Pozitia unde ar trebui sa fie jucatorul pentru a impinge cutia
    player_pos = (start_box[0] - dx, start_box[1] - dy)
    # Verificam daca jucatorul poate sta acolo (nu e perete sau in afara hartii)
    if 0 <= player_pos[0] < test_map.get_height() and 0 <= player_pos[1] < test_map.get_width():
        # Verific ca jucatorul nu este pe perete
        if test_map.get_positions2(player_pos[0], player_pos[1]) != -1:  # presupunem ca `-1` e perete
            return True #este push valid daca nu e pe perete
    return False

def este_cale_push_only(test_map, cale):
    # functie in care primesc o cale si verific ca pe toata lungimea caii pot impinge cutia
    for i in range(len(cale) - 1):
        if not este_push_valid(test_map, cale[i], cale[i + 1]):
            #daca nu este push_valid pe o sectiune, calea devine invalida folosind doar pushuri
            print(f"Se blocheaza intre {cale[i]} si {cale[i + 1]}")
            return False
    return True

def manhattan_distance(x1, y1, x2, y2):
    """Calculez distanta Manhattan dintre doua puncte (x1, y1) si (x2, y2)."""
    return abs(x1 - x2) + abs(y1 - y2)

cell_penalty_map = defaultdict(int) #zone de pe harta penalizate pentru suprapuneri
def clone_state_with_boxes(state,cai,poz):
    """ Ideea din spate este sa generez pe rand, un numar de harti egal cu numarul de targeturi
    Fiecare harta are toate cutiile pe targeturi, mai putin cutia de la poz
    Scopul este sa vad daca am toate cutiile pe targeturi, in afara de una, daca mai pot ajunge
    la cutie
    """
    new_state = deepcopy(state)
    (x,y)=poz
    for cale in cai:
        #setez fiecare cutie, in afara de poz, pe targetul aferent
        start = cale[0]
        end = cale[-1]
        if start != (x,y): #daca nu e in pozitie, folosesc functia set_box_position
            new_state.set_box_position(start[0], start[1], end[0], end[1])
    return new_state

def este_cutie_blocata(pos, state,cale,cai):
    """
    Verific daca o cutie este blocata (nu pot sa o imping din nicio directie valida).
    """
    x, y = pos
    walls = {(wall[0], wall[1]) for wall in test_map.get_walls()}
    boxes =state.get_box_positions()
    boxes = [(box.x, box.y) for box in boxes]
    player_pos = state.get_player_position() #salvez pozitia playerului, cutiile si tintele

    # (dx, dy) reprezinta directia in care imping cutia
    (x1,y1) = cale[1] #prima mutare a cutiei curente
    dx=x1-x
    dy=y1-y
    behind_box=(x-dx,y-dy)  #pozitia din spatele cutiei
    if behind_box not in walls and behind_box not in boxes:
        new_state = clone_state_with_boxes(state,cai,(x,y))
        #aplic bfs_simple sa vad daca pot ajunge in pozitie
        d, _ = heuristics.bfs_simple2(new_state, player_pos, behind_box)
        if d> val_mare:
            return True #cutie blocata
        return False  # nu e blocata, exista o cale
    return True

def gaseste_ultima_cutie_de_mutat(test_map, cai):
    boxes = test_map.get_box_positions()
    box_positions = [(box.x, box.y) for box in boxes]
    blocked_boxes = set()  # Set pentru a pastra cutiile blocate
    if(len(cai)>1): #daca am mai multe cai
        blocked_boxes.add(cai[1][0])
    for idx, (x, y) in enumerate(box_positions):
        cale = cai[idx]
        if not cale:
            continue
        final_pos = cale[-1]  # ultima pozitie din cale este tinta
        cutii_simulate = box_positions.copy() #copiez cutiile
        cutii_simulate[idx] = final_pos
        for j, pos in enumerate(cutii_simulate):
            if j == idx:
                continue
            cale_cutie = cai[j]

            if este_cutie_blocata(pos, test_map, cale_cutie, cai): #cutie blocata
                blocked_boxes.add(cale_cutie[0]) #set pentru a pastra unicitatea cutiilor
    if blocked_boxes:
        return list(blocked_boxes)  # returnez lista de cutii
    else:
        return None  # altfel nimic



def energy(state, cai, explored_states_count):
    """
    Energia sistemului: suma scorurilor cutiilor pe drumul propriu spre tinta.
    Daca mai e o singura cutie de plasat, caut o cale directa sa o pun acolo.
    """
    boxes = state.get_box_positions()
    goals = state.get_target_positions()
    goal_positions = [(goal[0], goal[1]) for goal in goals] #pozitie tinte
    box_positions = [(box.x, box.y) for box in boxes] #pozitie cutii
    scor_total = 0
    relax_factor = max(20 - explored_states_count / 500, 1) #factor de relaxare
    #lista de cutii ramase, daca cutia nu se afla pe tinta, o adaug
    cutii_ramase = [box for box in box_positions if box not in goal_positions]
    scopuri_libere = [goal for goal in goal_positions if goal not in box_positions]
    global a #este setul de cutii
    #folosesc functia gaseste_ultima_cutie_de_mutat
    if  a!=None and len(a) == 1:
        pos=a[0] #salvez pozitia blocata daca este doar o cutie blocata
    #print(pos)
    prioritati = [1.0] * len(boxes)
    #daca am mai mult de o cutie de dus pe target si nu pot ajunge in zona la pos, returnez valoare mare
    if len(boxes) >= 4 and len(cutii_ramase) > 1 and all(math.dist(pos, box) > 0.1 for box in cutii_ramase):
        return val_mare
    #prioritatile sunt folosite pentru a prioritiza anumite cutii (scorul lor conteaza mai mult)
    if len(cutii_ramase) == 1: #daca mai am doar o cutie, reduc prioritatile
        prioritati = [0.1] * len(boxes)
    for idx, (x, y) in enumerate(box_positions):
        cale = cai[idx]
        score = 0
        factor_prioritate = prioritati[idx] if idx < len(prioritati) else 1.0

        # Daca cutia e pe cale catre scopul ei
        if (x, y) in cale:
            index = cale.index((x, y))
            score = 1.1 ** (len(cale) - index - 1) * factor_prioritate
            if len(cale) - index - 1 == 0:
                score = 0.1 #cutia este pe target

        else:
            if len(cutii_ramase) == 1 and (x, y) == cutii_ramase[0]: #daca mai am doar o cutie
                best_path = None #ii caut o noua cale
                prioritati = [1.0] * len(boxes)
                #pot aplica bfs sau astar pentru a determina calea
                #statistic, astar este un pic mai eficienta
                for goal in scopuri_libere:
                    #_, path = bfs_full(state, x, y, goal[0], goal[1])
                    _,path = heuristics.a_star_full(state,x,y,goal[0],goal[1])
                    if path:
                        best_path = path #am gasit o cale de pastrat
                        break
                if best_path: #daca am gasit calea, recalculez noul scor
                    index2 = best_path.index((x, y))
                    score = 1.1 ** (len(best_path) - index2 - 1)
                else:
                    score = 999999 #daca nu exista cale pentru ultima cutie
                    #penalizare foarte mare
            else:
                if is_box_stuck(state): #daca cutia este blocata
                    #nu folosesc pull, deci penalizez rau
                    score = 999999
                else:
                    score = 1.1 ** (len(cale) + relax_factor)
                    #scor final
        scor_total += score
    return scor_total

def softmax(x: np.array) -> float:
    """Functie preluata din laborator pentru annealing"""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum() #returnez probabiltiatile


#la annealing mai merge bine cu tfinal=1., alpha =0.09, initial_temp=700
#tfinal=0.001, alpha=0.01, max_iter=1000000, initial_temp=1, cooling_rate=0.9995)
def simulated_annealing(initial_map, tfinal=1., alpha=0.02, max_iter=1000000, initial_temp=1000, cooling_rate=0.9995):
    current_state = initial_map #starea curenta este harta initiala
    explored_states_count = 0 #0 stari explorate
    boxes = Map.get_box_positions(initial_map)
    goals = Map.get_target_positions(initial_map)
    box_positions = [(box.x, box.y) for box in boxes]
    goal_positions = [(goal[0], goal[1]) for goal in goals]
    cost_matrix = []
    paths_matrix = []
    # Construiesc paths_matrix si cost_matrix
    for box in box_positions:
        row_cost = []
        row_paths = []
        for goal in goal_positions:
            #aici, la generarea cailor initiale, pot alege intre bfs si astar
            _, cale = heuristics.bfs_full(initial_map, box[0], box[1], goal[0], goal[1])
            #_, cale = heuristics.a_star_full(initial_map, box[0], box[1], goal[0], goal[1])
            if cale:
                row_cost.append(len(cale)) #salvez in matrice lungimea caii
            else:
                row_cost.append(9999) #nu gaseste cale
            row_paths.append(cale)
        cost_matrix.append(row_cost)
        paths_matrix.append(row_paths)
    print("Incep permutarile intre box-uri si scopuri...")
    # lista cu toate permutarile box-target
    toate_permutarile = list(permutations(range(len(goal_positions))))

    for perm in toate_permutarile: #for in toate permutarile
        cai_finale = [] #caile precalculate
        valid = True
        for i, box_index in enumerate(range(len(box_positions))):
            goal_index = perm[i] #unde trebuie sa ajunga cutia
            path = paths_matrix[box_index][goal_index] #aleg calea buna
            if path and cost_matrix[box_index][goal_index] < 9999:
                cai_finale.append(path) #cale valida
            else:
                valid = False #cale invalida
                break
        if not valid: #daca nu gaseste cale valida, nu are rost permutarea
            print(perm)
            continue  # Sar peste permutarile invalide
        print(f"\nPermutare valida: {perm}")
        for i, cale in enumerate(cai_finale):
            print(f"Cutia {box_positions[i]} -> Goal {goal_positions[perm[i]]}: {cale}")
        # Resetez variabilele de Simulated Annealing pentru fiecare permutare
        temp = initial_temp  # Resetez temperatura pentru fiecare permutare
        current_state = initial_map
        mutari_bune = [current_state]
        parents = {}
        iters = 0
        explored = 0
        global a
        a = gaseste_ultima_cutie_de_mutat(current_state,cai_finale) #ultima cutie de mutat
        if a!=None:
            a=list(set(box_positions)-set(a)) #lista cu cutiile blocate
        while temp > tfinal and iters < max_iter:
            iters += 1
            if current_state.is_solved(): #daca gaseste solutie
                print(" Solutie gasita!")
                path = []
                state = current_state
                while state in parents:
                    path.append(state) #creez calea de stari returnata
                    state = parents[state]
                path.append(state)
                path.reverse() #dau reverse la cale, fiindca ma intereseaza de la cea initiala la finala
                return current_state, remove_duplicates(mutari_bune), explored_states_count
            neighbors = list(current_state.get_neighbours())
            scores = []
            filtered_neighbors = []
            explored+=1
            explored_states_count += 1 #stari explorate +1

            for n in neighbors:
                filtered_neighbors.append(n)
                scores.append(energy(n, cai_finale,explored))

            if not filtered_neighbors:
                continue
            probabilities = softmax(-np.array(scores)) #aplic softmax pe lista de energii
            #aleg indexul aleator, bazandu-ma pe probabilitatile calculate de softmax
            index = np.random.choice(len(filtered_neighbors), p=probabilities)
            next_state = filtered_neighbors[index] #asa determin starea urmatoare
            parents[next_state] = current_state #vector de parinti pentru a putea reface calea
            next_energy = energy(next_state, cai_finale,explored)
            current_energy = energy(current_state, cai_finale,explored)
            delta_energy = next_energy - current_energy #delta_energy = viitor-curent
            if delta_energy < 0: #daca gasesc ceva de energie mai buna, este o stare mai buna
                mutari_bune.append(current_state)
                mutari_bune.append(next_state)
            if delta_energy < 0 or random.random() < math.exp(-delta_energy / (temp * alpha)):
                current_state = next_state #trec in starea urmatoare
            temp *= cooling_rate  # Reducem temperatura
        print(f" Permutarea {perm} nu a dus la o solutie.")
    print("Nu s-a gasit nicio solutie pentru nicio permutare.")
    return current_state, remove_duplicates(mutari_bune), explored_states_count

import tkinter as tk
from PIL import Image, ImageTk
import os
def interfata_grafica(base_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construiesc calea corecta catre folderul Images
    save_path = os.path.join(script_dir, "..", "Images_Simulated", base_name)
    save_path = os.path.normpath(save_path)
    # Calea catre GIF-ul generat
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
            gif.seek(len(frames))  # Merge la urmatorul frame
    except EOFError:
        pass  # Sfarsitul GIF-ului

    # Index pentru frame-ul curent
    current_frame = 0
    # Functie pentru redarea animatiei
    def update_image(index):
        """Actualizeaza imaginea afisata."""
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
        if current_frame < len(frames) - 1:
            update_image(current_frame + 1)
    # Butoane pentru navigare
    btn_prev = tk.Button(root, text="<< Anterior", command=prev_frame)
    btn_prev.pack(side=tk.LEFT, padx=10)

    btn_next = tk.Button(root, text="Urmator >>", command=next_frame)
    btn_next.pack(side=tk.RIGHT, padx=10)
    # Initializare cu prima imagine
    if frames:
        update_image(current_frame)
    # Loopul pentru animatie
    root.mainloop()

if __name__ == '__main__':
    name_test=''
    if len(sys.argv) > 1: #numele testului
        name_test = sys.argv[1]
        #print(sys.argv[1])
    else:
        print("Argumentul lipseste!")
    if name_test=='':
        name_test='large_map1' #ii dau large_map1 default, daca nu merge altfel
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..'))  # 2 nivele in sus pentru a ajunge in directorul rădăcină al proiectului
    map_path = os.path.join(project_dir,'Tema 1 IA', 'tests', name_test)
    time_start = time.time() #cronometrez algoritmul
    file_name = os.path.basename(map_path)
    # indepartez extensia .yaml din numele fisierului
    base_name = file_name.replace('.yaml', '')
    test_map = Map.from_yaml(map_path + '.yaml') #extrag harta
    solution, path,explored_states_count = simulated_annealing(test_map) #aplic simulated annealing
    if solution:
        print("Solutia finala:")
        print(solution)
    else:
        print("Nu s-a gasit solutia.")
    time_end = time.time()
    sol=[]
    for i in range(len(path) - 1):  # Iau calea spre optimizare
        #bfs_full(state,)
        state=path[i]
        print("Stari:")
        print(state)
        state2=path[i+1]
        x1,y1 = state.get_player_position() #ma uit la deplasare player intre 2 stari
        x2,y2=state2.get_player_position()
        #print(x1, y1, x2, y2)
        _,cale = heuristics.bfs_simple2(state,(x1,y1),(x2,y2))
        #aplic bfs_simple pentru a determina calea.
        posBox = state.get_box_positions()
        posBox = [(box.x, box.y) for box in posBox]
        if (x2, y2) in posBox: #daca playerul este in pozitia anterioara a cutiei
            #impinge cutia
            ok=0
            x1,y1 = state.get_player_position()
            x2,y2 = state2.get_player_position()
            if (x1 == x2 and y2 == y1 + 1):
                #litere mari pentru impingere cutie
                sol.append('R')
                ok=1
            if (x1 == x2 and y1 == y2 + 1):
                sol.append('L')
                ok=1
            if (y1 == y2 and x1 == x2 + 1):
                sol.append('D')
                ok=1
            if (y1 == y2 and x2 == x1 + 1):
                sol.append('U')
                ok=1
            if ok == 0:
                #cazul in care se modifica mai multe pe harta de la o stare la alta
                print("NU FACE NIMIC")
                posBox1 = state.get_box_positions()
                posBox1 = [(box.x, box.y) for box in posBox1]
                posBox2 = state2.get_box_positions()
                posBox2 = [(box.x, box.y) for box in posBox2]
                for i in range(len(posBox1)):
                    if posBox1[i] != posBox2[i]:
                        dx = posBox2[i][0] - posBox1[i][0] #vad modificarea dx si dy
                        dy = posBox2[i][1] - posBox1[i][1]
                        posPlayer_after=(posBox1[i][0]-dx,posBox1[i][1]-dy)
                        x1, y1 = state.get_player_position()
                        _,cale5 = heuristics.bfs_simple2(state,(x1,y1),posPlayer_after)
                        for i in range(len(cale5) - 1):
                            coord1 = cale5[i]
                            coord2 = cale5[i + 1]
                            x1, y1 = coord1
                            x2, y2 = coord2
                            #vad cum se deplaseaza playerul (codificare cu litere mici)
                            if (x1 == x2 and y2 == y1 + 1):
                                sol.append('r')
                            if (x1 == x2 and y1 == y2 + 1):
                                sol.append('l')
                            if (y1 == y2 and x1 == x2 + 1):
                                sol.append('d')
                            if (y1 == y2 and x2 == x1 + 1):
                                sol.append('u')
                if dx==-1 and dy==0:
                    sol.append('D')
                if dx == 1 and dy == 0:
                    sol.append('U')
                if dx == 0 and dy == 1:
                    sol.append('R')
                else:
                    sol.append('L')
        else:
            _, cale2 = heuristics.bfs_simple2(state, (x1, y1), (x2, y2))
            #print(x1,y1,x2,y2)
            #deplasare player de la (x1,y1) la (X2,y2)
            for i in range(len(cale2)-1):
                coord1=cale2[i]
                coord2=cale2[i+1]
                x1,y1=coord1
                x2,y2=coord2
                #vad cum se deplaseaza de-a lungul caii
                if(x1==x2 and y2==y1+1):
                    sol.append('r')
                if(x1 == x2 and y1==y2+1):
                    sol.append('l')
                if(y1==y2 and x1 == x2+1):
                    sol.append('d')
                if(y1==y2 and x2==x1+1):
                    sol.append('u')
                if (x1, y1) in state.positions_of_boxes:
                    box_name = state.positions_of_boxes[(x1, y1)]
                    box = state.boxes[box_name]
    solution_steps = [str(test_map)]
    #print(path[len(path)-1])
    sol_string = ''.join(sol)
    print(solution) #solutia finala
    moves = str(sol_string)
    print(moves)
    print(f" Numar total de stari explorate: {explored_states_count}")
    print('Runtime of simulated annealing: %.2f second.' % (time_end - time_start))
    den_test= sys.argv[1]
    rezultate = {
        'nume_test': [den_test],
        'miscari': ["".join(sol)],
        'numar_stari_explorate': [explored_states_count],
        'runtime_secunde': [round(time_end - time_start, 2)]
    }
    # Îl pun într-un DataFrame
    df = pd.DataFrame(rezultate)
    fisier_csv = 'rezultate_Annealing.csv'
    if not os.path.isfile(fisier_csv):
        # Daca NU exista, scriu cu header
        df.to_csv(fisier_csv, index=False)
    else:
        # Daca exista, adăug (append) fără header
        df.to_csv(fisier_csv, mode='a', header=False, index=False)
    df_total = pd.read_csv(fisier_csv)
    # Sortez după 'nume_test' și 'Tip'
    df_total = df_total.sort_values(by=[ 'nume_test'])
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
    for move in moves:
        if move not in MOVE_MAPPING:  # Verifica daca miscarea este valida
            raise ValueError(f"Invalid move character: {move}")
        numeric_move = MOVE_MAPPING[move]  # Convertesc miscarea in numar
        test_map.apply_move(numeric_move)  # Aplic miscarea pe stare
        solution_steps.append(str(test_map))  # Salvez noua stare
    # Construiesc calea completa de salvare
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construiesc calea corecta catre folderul Images_Simulated
    save_path = os.path.join(script_dir, "..", "Images_Simulated", base_name)
    save_path = os.path.normpath(save_path)
    save_images(solution_steps, save_path)
    create_gif(save_path, "solution.gif", save_path)
    interfata_grafica(base_name) #afisez o fereastra cu jocul si cu mutarile
