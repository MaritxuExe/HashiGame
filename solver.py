"""
==================================================
Hashi Puzzle Solver 
===================================================

INSTRUCCIONES:

Implementa la función "solve_hashi_true_sat()", que aparece a continuación 
para resolver puzles Hashi, utilizando programación por 
restricciones con OR-Tools.

La función debe:

    Recibir como entrada las dimensiones del puzle y los datos de las islas.

    Usar CP-SAT para codificar y resolver las restricciones del puzle.

    Devolver un diccionario con la solución.

    NO modificar otros archivos.
"""

from implemented_functions import add_connectivity_constraints, formated_sol


from pysat.solvers import Glucose3 # type: ignore
from pysat.formula import CNF, IDPool # type: ignore
from pysat.card import CardEnc # pyright: ignore[reportMissingImports]

# IDPool global para todas las variables
variables = IDPool()


"""
===================================================================
Las funciones que tienes que implementar.
===================================================================
"""

def vertical_bridges(i, j, nodes):
    xi, yi = nodes[i]
    xj, yj = nodes[j]
    
    if xi != xj:
        return False
    
    for k in nodes:
        xk, yk = k
        
        if k == nodes[i] or k == nodes[j]:
            continue
        
        left = min(yi, yj)
        right = max(yi, yj)
        
        #xi == xj
        if xk == xi and (left < yk < right):
            return False
        
    return True
        
def horizontal_bridges(i, j, nodes):
    xi, yi = nodes[i]
    xj, yj = nodes[j]
    
    if yi != yj:
        return False
    
    for k in nodes:
        xk, yk = k
        
        if k == nodes[i] or k == nodes[j]:
            continue
        
        left = min(xi, xj)
        right = max(xi, xj)
        
        #xi == xj
        if yk == yi and (left < xk < right):
            return False
        
    return True                    

def construct_edges(nodes):
    """
    Construir la lista de aristas posibles (puentes válidos). SE DEBE
    LLAMAR "edges". Las aristas van del índice i de una isla nodes[i] al
    índice j de otra nodes[j]. Siguiendo el Ejemplo 1, debes devolver la lista  
    edges =  [[0, 1], [0, 2], [1, 4], [2, 3], [3, 4], [3, 5], [4, 6], [5, 6]].
    """    
  
    edges = []
    n = len(nodes)

    for i in range(n):
        for j in range(i + 1, n):
            if horizontal_bridges(i, j, nodes) or vertical_bridges(i, j, nodes):
                edges.append([i, j])

    return edges

def add_bridge_2_implise_bridg_1(edges, cnf):
    """
    Añadir la restricción (a), que debe añadir, para cada 
    arista e de edges, la clausula [-b2_e, b1_e] a cnf.  
    """
    
    for e in range(len(edges)):
        
        b1 = variables.id(('b1', e))
        b2 = variables.id(('b2', e))
        
        clausula = [-b2, b1]
        
        cnf.append(clausula)
    
    return cnf
    
def add_crossing_constraints(nodes, edges, cnf):
    """
    Añadir la restricción (c), que debe identificar todas las aristas
    de edges que se cruzan. Por cada par de aristas e y e' que se
    crucen hay que añadir la cláusula [-b1e, -b1e'].
    """
       
    for e1 in range(len(edges)):
        e1i, e1j = edges[e1]
        e1_x1, e1_y1 = nodes[e1i]
        e1_x2, e1_y2 = nodes[e1j]
        
        for e2 in range(len(edges)):
            e2i, e2j = edges[e2]
            e2_x1, e2_y1 = nodes[e2i]
            e2_x2, e2_y2 = nodes[e2j]
            
            cruza = False
            
            if e1_y1 == e1_y2 and e2_x1 == e2_x2:
                
                x_top = min(e1_x1, e2_x1)
                x_bottom = max(e1_x1, e2_x1)
                
                y_left = min(e1_y2, e2_y2)
                y_right = max(e1_y2, e2_y2)
                
                if (x_top < e1_x1 < x_bottom) and (y_left < e2_y1 < y_right):
                    cruza = True
            
            elif e2_y1 == e2_y2 and e1_x1 == e1_x2:
                
                x_top = min(e2_x1, e2_x2)
                x_bottom = max(e2_x1, e2_x2)
                
                y_left = min(e1_y1, e1_y2)
                y_right = max(e1_y1, e1_y2)
                
                if (x_top < e1_x1 < x_bottom) and (y_left < e2_y1 < y_right):
                    cruza = True
                
            if cruza:
                b1_e1 = variables.id(('b1', e1))
                b1_e2 = variables.id(('b1', e2))
                
                clausula = [-b1_e1, -b1_e2]
                
                cnf.append(clausula) 
    return cnf

def add_required_bridges_contraints(nodes, edges, cnf, required_bridges):
    """
    añadir la restricción (d) para asegurar que cada isla tiene exactamente 
    el número de puentes requerido. 
    """
    
    n = len(nodes)
    
    for i in range(n):
        lits = []
        for e in range(len(edges)):
            if i in edges[e]:
                lits.append(variables.id(('b1', e)))
                lits.append(variables.id(('b2', e)))

        cnf_arit = CardEnc.equals(lits, required_bridges[i], vpool=variables)
        cnf.extend(cnf_arit)

    return cnf
    
    
def solve_hashi_true_sat(dimensions, islands_data):
    """
    Resolver un puzle Hashi utilizando programación por restricciones.

    Argumentos:
    ===========
        dimensions (list): [coordenada x, coordenada y] de 
                           la cuadrícula del puzle.
        islands_data (list): Lista de islas, donde cada isla es:
            [x, y, required_bridges]
               x, y: coordenadas (empezando en 0)
               required_bridges: número de puentes necesarios (de 1 a 8).

    Devuelve:
    =========    
        dict: Solución con el formato:
            {
                "width": int,
                "height": int,
                "islands": original islands_data,
                "solution": [
                    {
                        "x1": int, "y1": int,
                        "x2": int, "y2": int,
                        "bridges": int (1 o 2)
                    },
                    ...
                ]
            }


        None: Si no existe solución.

    Restricciones a codificar:
    =========================    
        - Los puentes solo pueden conectar islas en la misma fila o columna.
        - Los puentes no pueden cruzar otras islas.
        - Los puentes no pueden cruzarse entre sí.
        - Cada par de islas puede tener 0, 1 o 2 puentes.
        - Cada isla debe tener exactamente el número de puentes indicado en 
          required_bridges.
        - Todas las islas deben estar conectadas (conectividad del grafo).

    Ejemplo1:
    ========    
    dimensions = [4, 4]
    islands_data = [[0,0,4],[0,2,2],[1,0,3],[1,1,4],[1,2,1],[3,1,3],[3,2,1]]
   
    4 - 2 -                 
    3 4 1 -           
    - - - -            
    - 3 1 -

    Una solución válida conectaría:
    [0,0] a [0,2] con 2 puentes
    [0,0] a [1,0] con 2 puentes
    [1,0] a [1,1] con 1 puente
    [1,1] a [1,2] con 1 puente
    [1,1] a [3,1] con 2 puentes
    [3,1] a [3,2] con 1 puente. 
    """
    
    nodes = [[isle[0], isle[1]] for isle in islands_data]
    required_bridges = [isle[2] for isle in islands_data]
    
    cnf = CNF()
    
    edges = construct_edges(nodes)  #TODO
    cnf = add_bridge_2_implise_bridg_1(edges, cnf)  #TODO
    cnf = add_crossing_constraints(nodes, edges, cnf)   #TODO
    cnf = add_required_bridges_contraints(nodes, edges, cnf, required_bridges)  #TODO
    cnf = add_connectivity_constraints(nodes, edges, cnf, variables)    # Hecha en implemented_functions
           
    # Se inicializa el solver, y se devuelve la solución.
    print(f"Starting SAT solver with {len(edges)} potential edges")
    with Glucose3(bootstrap_with=cnf) as sat:
        if sat.solve():
            print("✓ Solution found")
            solution = sat.get_model()
            return formated_sol(dimensions, nodes, edges, solution, variables)  # Hecha en implemented_functions
        else:
            print("✗ Solution not found")
            return None


def test():
    
    """
    ===================================================================
    Seis casos de prueba
    ===================================================================

    Example 1: 
    ============
    4 - 2 -                 
    3 4 1 -           
    - - - -            
    - 3 1 -

    La solucion es
    [0,0] a [0,2] con 2 puentes
    [0,0] a [1,0] con 2 puentes
    [1,0] a [1,1] con 1 puente
    [1,1] a [1,2] con 1 puente
    [1,1] a [3,1] con 2 puentes
    [3,1] a [3,2] con 1 puente
    """    
    dimensions = [4, 4]
    islands_data = [[0,0,4],[0,2,2],[1,0,3],[1,1,4],[1,2,1],[3,1,3],[3,2,1]]
    
    print("\n")
    print("Ejemplo 1")
    print("========")
    print("dimensions: ", dimensions, "islands: ", islands_data, "\n")
    print(solve_hashi_true_sat(dimensions, islands_data))
    print("\n")
    
    
    """
    Example 2:
    ===============    
    - - - - - - -                 
    - 3 - - 2 - -           
    - - - - - - -            
    - - - - - - -
    - 4 - - 3 - -
    - - - - - - -
    - - - - - - -       
    
    La solucion es
    [1,1] a [4,1] con 2 puentes
    [1,1] a [1,4] con 1 puente
    [4,1] a [4,4] con 2 puentes
    [1,4] a [4,4] con 1 puente
    """
   
    dimensions = [7, 7]
    islands_data = [[1, 1, 3], [4, 1, 4], [1, 4, 2], [4, 4, 3]]
    
    print("Ejemplo 2")
    print("========")
    print("dimensions: ", dimensions, "islands: ", islands_data, "\n")
    print(solve_hashi_true_sat(dimensions, islands_data))
    print("\n")
    
    
    """
    Example 3:
    ===============    
    2 2 1                
    1 - -        
    - - -         
     
    La solucion es
    [0,0] a [0,1] con 1 puente
    [0,1] a [0,2] con 1 puente
    [0,0] a [1,0] con 1 puente
    """
    
    dimensions = [3, 3]
    islands_data = [[0,0,2],[0,1,2],[0,2,1],[1,0,1]]
    
    print("Ejemplo 3")
    print("========")
    print("dimensions: ", dimensions, "islands: ", islands_data, "\n")
    print(solve_hashi_true_sat(dimensions, islands_data))
    print("\n")
    
   
    """
    Example 4: 
    ============
    1 - 1 -                 
    - 1 - 1           
    - - - 2            
    - - - 1

    No hay solución porque no es conexo.
    """    
    dimensions = [4, 4]
    islands_data = [[0,0,1],[0,2,1],[1,1,1],[1,3,1],[2,3,2],[3,3,1]]
    
    print("Ejemplo 4")
    print("========")
    print("dimensions: ", dimensions, "islands: ", islands_data, "\n")
    print(solve_hashi_true_sat(dimensions, islands_data))
    print("\n")
    
    
    """
    Example 5:
    ===============    
    1 1 -                 
    2 - 2           
    - 2 2                
    
    No hay solución porque o se cruzan los puentes o no es conexo.
    """
   
    dimensions = [3, 3]
    islands_data = [[0, 0, 1], [0, 1, 1], [1, 0, 2], [1, 2, 2], 
                [2, 1, 2], [2, 2, 2]]
    
    print("Ejemplo 5")
    print("========")
    print("dimensions: ", dimensions, "islands: ", islands_data, "\n")
    print(solve_hashi_true_sat(dimensions, islands_data))
    print("\n")
    
    
    """
    Example 6: 
    ============
    1 - 2 - -                 
    2 - 1 - -           
    - 1 - - -            
    - 2 - - -
    - - - - -

    No hay solución.
    """    
    dimensions = [5, 5]
    islands_data = [[0,0,1],[0,2,2],[1,0,2],[1,2,1],[2,1,1],[3,1,2]]
    
    print("Ejemplo 6")
    print("========")
    print("dimensions: ", dimensions, "islands: ", islands_data, "\n")
    print(solve_hashi_true_sat(dimensions, islands_data))
    
    
#test()


