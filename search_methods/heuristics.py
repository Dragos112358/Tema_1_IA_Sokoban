#lrta
import heapq
from collections import deque, defaultdict

from sokoban import Map

cell_penalty_map = defaultdict(int)
#functie de cost bfs care imi spune distanta de la cutie la target
def bfs_distance(start, targets, state: Map):
    visited = set()
    queue = deque([(start, 0)]) #coada
    walls = {(wall[0], wall[1]) for wall in state.get_walls()}
    while queue:
        (x, y), dist = queue.popleft()
        if (x, y) in targets: #am ajuns la target => dist
            return dist
        if (x, y) in visited:
            continue
        visited.add((x, y))
        #explorez vecinii
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited and (nx, ny) not in walls:
                queue.append(((nx, ny), dist + 1))
    return float('inf')  # daca nu poate ajunge la nicio tinta

def manhattan_distance(start, targets,state:Map):
    #manhattan clasic
    return min(abs(start[0] - t[0]) + abs(start[1] - t[1]) for t in targets)

def smart_manhattan_distance(start, targets, state: Map):
    #manhattan care tine cont si de obstacole
    x1, y1 = start
    x2, y2 = targets[0]

    manhattan_dist = abs(x1 - x2) + abs(y1 - y2)

    # Verificam daca startul este blocat aproape complet (e un semn ca va dura mai mult)
    walls = {(wall[0], wall[1]) for wall in state.get_walls()}
    boxes = {(box.x, box.y) for box in state.get_box_positions()}

    neighbors = [(x1+1, y1), (x1-1, y1), (x1, y1+1), (x1, y1-1)]
    blocked = sum(1 for n in neighbors if n in walls or n in boxes)

    if blocked > 0:
        manhattan_dist += 1  # Admisibil: +1 e ok (nu supraestimeaza cu mai mult)
    #adaug 1 daca am obstacole in cale
    return manhattan_dist

#bfs real tine cont si de cutii
def bfs_real(start, targets, state: Map, max_iterations=10000):
    visited = set()
    queue = deque([(start, 0)])  # stocam coordonatele și distanta
    walls = {(wall[0], wall[1]) for wall in state.get_walls()}
    boxes = {(box.x, box.y) for box in state.get_box_positions()}
    height = state.get_height()
    width = state.get_width()
    iterations = 0  # contor pentru iteratii
    while queue:
        if iterations >= max_iterations:
            return float('inf')  # Daca am depașit limita de iteratii
        (x, y), dist = queue.popleft()
        iterations += 1
        # Daca am ajuns la o tinta, returnam distanta
        if (x, y) in targets:
            return dist

        # Daca este deja vizitat, trec la urmatorul element
        if (x, y) in visited:
            continue
        visited.add((x, y))

        # Verific vecinii (directiile: sus, jos, stanga, dreapta)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= height or ny >= width:
                continue
            if (nx, ny) not in visited and (nx, ny) not in walls and (nx, ny) not in boxes:
                queue.append(((nx, ny), dist + 1))

    return float('inf')  # Daca nu gasește nicio tinta dupa max_iteratii

def penalty(pos,state):
    # penalizare daca e langa cutii
    penalty_score = 0
    posbox = state.get_box_positions()
    posbox = [(box.x, box.y) for box in posbox]
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        neighbor = (pos[0] + dx, pos[1] + dy)
        if neighbor in posbox:
            #print("Trece")
            penalty_score += 3
    return penalty_score

def astar_distance(start, targets, state: Map):
    #estimare distanta folosind astar pentru lrta
    height = state.get_height()
    width = state.get_width()
    def heuristic2(a, b): #astar cu manhattan
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    walls = {(wall[0], wall[1]) for wall in state.get_walls()}
    open_set = []
    heapq.heappush(open_set, (0 + min(heuristic2(start, t) for t in targets), 0, start))
    g_score = {start: 0}
    visited = set()
    in_open_set = {start}
    while open_set:
        _, current_cost, current = heapq.heappop(open_set)
        in_open_set.remove(current)
        if current in visited:
            continue
        visited.add(current)
        if current in targets:
            return g_score[current]  # returnez doar distanta
        # Iterez asupra vecinilor
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor[0] < 0 or neighbor[1] < 0 or neighbor[0] >= height or neighbor[1] >= width:
                continue  # Daca vecinul este în afara hartii, îl ignor
            # Verific daca vecinul este valid
            if neighbor in visited or neighbor in walls:
                continue
            tentative_g_score = g_score[current] + 1
            # Daca g_score este mai bun, il actualizez
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                g_score[neighbor] = tentative_g_score
                f_score = tentative_g_score + min(heuristic2(neighbor, t) for t in targets)\
                          +penalty(neighbor,state)
                # Daca vecinul nu este deja în open_set, îl adaug
                if neighbor not in in_open_set:
                    heapq.heappush(open_set, (f_score, tentative_g_score, neighbor))
                    in_open_set.add(neighbor)
                # Daca este deja în open_set și are un f_score mai mic, il actualizez
                else:
                    # Caut si actualizez starea existenta
                    for i, (f, g, n) in enumerate(open_set):
                        if n == neighbor and f > f_score:
                            open_set[i] = (f_score, tentative_g_score, neighbor)
                            heapq.heapify(open_set) #transform open_setul din lista in heap
                            break
    return float('inf')  # Nu exista drum
#simulated_annealing
def manhattan_dist(x1, y1, x2, y2):
    """Calculam distanta Manhattan dintre doua puncte (x1, y1) si (x2, y2)."""
    return abs(x1 - x2) + abs(y1 - y2)
def este_push_valid(test_map, start_box, end_box):
    #verific daca pot face push de la o pozitie la alta
    #(pozitia din spatele cutiei sa fie libera)
    dx = end_box[0] - start_box[0]
    dy = end_box[1] - start_box[1]
    player_pos = (start_box[0] - dx, start_box[1] - dy)
    # Verific daca jucatorul poate sta acolo (nu e perete sau în afara hartii)
    if 0 <= player_pos[0] < test_map.get_height() and 0 <= player_pos[1] < test_map.get_width():
        # Verific ca jucatorul nu este pe perete
        if test_map.get_positions2(player_pos[0], player_pos[1]) != -1:  # presupunem ca `-1` e perete
            return True #push valid
    return False #push invalid

def este_cale_push_only(test_map, cale):
    # Verific fiecare pas din cale ca este pushable
    for i in range(len(cale) - 1):
        if not este_push_valid(test_map, cale[i], cale[i + 1]):
            return False #daca are o zona din drum unde nu poate fi impins, returnez false
    return True

def a_star_full(test_map, start_x, start_y, goal_x, goal_y, cell_penalty_map=None):
    #astar cu determinare de cale pentru simulated_annealing
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if cell_penalty_map is None:
        cell_penalty_map = defaultdict(int)
    open_list = []
    heapq.heappush(open_list, (
        manhattan_dist(start_x, start_y, goal_x, goal_y),  # f = g + h
        0,  # g
        start_x,
        start_y,
        []  # path
    ))
    visited = dict()
    goal_positions = {(goal[0], goal[1]) for goal in test_map.get_target_positions()}
    while open_list:
        f, g, x, y, path = heapq.heappop(open_list)
        if (x, y) in visited and visited[(x, y)] <= g:
            continue #daca este deja vizitat, nu il mai explorez
        visited[(x, y)] = g
        if (x, y) == (goal_x, goal_y): #daca gasesc calea cea buna
            full_path = path + [(x, y)]
            if este_cale_push_only(test_map, full_path): #verific ca este valida
                for px, py in full_path:
                    cell_penalty_map[(px, py)] += 1 #penalizez cu 1
                #nu vreau sa am mai multe cai suprapuse
                return g, full_path
            else:
                continue
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < test_map.get_height() and 0 <= ny < test_map.get_width():
                if test_map.get_positions(nx, ny) != -1:
                    if este_push_valid(test_map, (x, y), (nx, ny)):
                        new_g = g + 1 #daca este pushable, gasesc noul cost
                        heuristic = manhattan_dist(nx, ny, goal_x, goal_y)
                        #penalizare daca calea mea trece prin tinta altei cutii
                        penalty = 5 if (nx, ny) in goal_positions else 0
                        overlap_penalty = cell_penalty_map[(nx, ny)]
                        #cost cu penalitati
                        new_f = new_g + heuristic + overlap_penalty * 5 + penalty
                        heapq.heappush(open_list, (new_f, new_g, nx, ny, path + [(x, y)]))
    return float('inf'), [] #daca nu merge, returnez distanta +inf si o cale goala

def bfs_full(test_map, start_x, start_y, goal_x, goal_y):
    #similar cu astar ca logica
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    open_list = []
    heapq.heappush(open_list, (0 + manhattan_dist(start_x, start_y, goal_x, goal_y), 0, start_x, start_y, []))
    goalBox = test_map.get_target_positions()
    goalBox = [(goal[0], goal[1]) for goal in goalBox]
    visited = dict()

    while open_list:
        f, g, x, y, path = heapq.heappop(open_list)

        if (x, y) in visited and visited[(x, y)] <= g:
            continue
        visited[(x, y)] = g

        if (x, y) == (goal_x, goal_y):
            full_path = path + [(x, y)]
            if este_cale_push_only(test_map, full_path): #daca este cale pushable
                for x, y in full_path:
                    cell_penalty_map[(x, y)] += 1 #penalizare daca trece prin alt target
                return g, full_path
            else:
                continue
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < test_map.get_height() and 0 <= ny < test_map.get_width():
                if test_map.get_positions(nx, ny) != -1:
                    # ✅ verific daca se poate împinge cutia de la (x,y) la (nx,ny)
                    if este_push_valid(test_map, (x, y), (nx, ny)):
                        new_g = g + 1
                        if (nx,ny)in goalBox:
                            penalty = 5
                        else:
                            penalty = 0
                        overlap_penalty = cell_penalty_map[(nx, ny)]
                        #alt calcul pentru costul bfs
                        new_f = new_g + manhattan_dist(nx, ny, goal_x, goal_y) + overlap_penalty * 5
                        heapq.heappush(open_list, (new_f, new_g, nx, ny, path + [(x, y)]))

    return float('inf'), []

def bfs_simple2(map_obj, start, goal): #bfs clasic, in care returnez distanta si calea
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    queue = deque([start])
    visited = {start: None}
    posBox = map_obj.get_box_positions()
    posBox = [(box.x, box.y) for box in posBox]
    while queue:
        x, y = queue.popleft()
        if (x, y) == goal: #daca am ajuns la target, reconstruiesc calea
            path = []
            current = (x, y)
            while current is not None:
                path.append(current)
                current = visited[current]
            return len(path), path[::-1]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (0 <= nx < map_obj.get_height() and 0 <= ny < map_obj.get_width()
                and (nx, ny) not in visited
                and map_obj.get_positions(nx, ny) !=-1
                and (nx, ny) not in posBox):
                visited[(nx, ny)] = (x, y)
                queue.append((nx, ny)) #adaug la coada daca respecta toate conditiile
    return float('inf'), []
