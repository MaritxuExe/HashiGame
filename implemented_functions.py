"""
Funciones ya implementadas
"""

def formated_sol(dimensions, nodes, edges, solution, variables):
    width, height = dimensions
    solution_edges = []
    for e in range(len(edges)):
        i, j = edges[e]
        b1, b2 = variables.id(('b1', e)), variables.id(('b2', e))
        num = 0
        if b2 in solution:
            num = num + 2
        elif b1 in solution:
            num = num + 1
        if num > 0:
            solution_edges.append([nodes[i][0], nodes[i][1], nodes[j][0], nodes[j][1], num])
    formatted = {
        "width": width,
        "height": height,
        "islands": nodes,
        "solution": [{"x1":edge[0],"y1":edge[1],
                      "x2":edge[2],"y2":edge[3],
                      "bridges":edge[4]} for edge in solution_edges]
    }
    return formatted


def add_connectivity_constraints(nodes, edges, clauses, variables):
    """
    Conectividad por capas (basado en BFS)
    - r(v,t) = isla v alcanzable en <= t pasos
    - x(e,t) = (b1_e AND r(u,t-1)) donde u es la otra isla en e relativa a v
    Se fuerza r(root,0)=True y r(v,0)=False para v != root.
    Finalmente se exige r(v,T) True para todo v (T = n-1).
    """
    n = len(nodes)
    
    T = n - 1  # número máximo de pasos para conectar n nodos
    root = 0

    # variables: r(v,t) y x(e,v,t) (x depende de la dirección "hacia v")
    def r_var(v, t):
        return variables.id(('r', v, t))

    def x_var(e, v, t):  # x_e_v_t representa (b1_e AND r(other,t-1)) con other la otra isla de e
        return variables.id(('x', e, v, t))

    # 1) r(root,0) = True
    clauses.append([r_var(root, 0)])
    # 2) r(v,0) = False para v != root
    for v in range(n):
        if v != root:
            clauses.append([-r_var(v, 0)])

    # 3) para t = 1..T construimos la relación
    for t in range(1, T + 1):
        for v in range(n):
            # Recolectar todas las aristas incidentes a v
            incident_edges = []
            for e_idx, (a, b) in enumerate(edges):
                if v == a or v == b:
                    incident_edges.append((e_idx, a, b))

            # Para cada arista incidente definimos x(e,v,t) que equivale a (b1_e AND r(other, t-1))
            x_list = []
            for (e_idx, a, b) in incident_edges:
                other = b if v == a else a
                x = x_var(e_idx, v, t)
                b1e = variables.id(('b1', e_idx))
                r_other_prev = r_var(other, t - 1)

                # x -> b1e
                clauses.append([-x, b1e])
                # x -> r_other_prev
                clauses.append([-x, r_other_prev])
                # (b1e AND r_other_prev) -> x  
                clauses.append([-b1e, -r_other_prev, x])

                x_list.append(x)

            # Ahora las cláusulas que construyen r(v,t):
            # r(v, t-1) -> r(v,t)  
            clauses.append([-r_var(v, t-1), r_var(v, t)])

            # Para cada x en x_list: x -> r(v,t)
            for x in x_list:
                clauses.append([-x, r_var(v, t)])

            # r(v,t) -> ( r(v,t-1) OR x1 OR x2 OR ... )
            # esto es (-r(v,t) OR r(v,t-1) OR x1 OR x2 ...)
            if x_list:
                clause = [-r_var(v, t), r_var(v, t-1)] + x_list
                clauses.append(clause)
            else:
                # Si no hay aristas incidentes, r(v,t) -> r(v,t-1)
                clauses.append([-r_var(v, t), r_var(v, t-1)])

    # exigir que r(v, T) sea True para todas las islas
    for v in range(n):
        clauses.append([r_var(v, T)])

    return clauses
