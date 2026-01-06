"""
Hashi Puzzle Solver
===========================================

Ejecuta este archivo usando tu implementación para resolver los puzles Hashi.

Configuración:
    – Ubicación de los archivos de los puzles: cambia PUZZLE_PATTERN
    – Número máximo de puzles: cambia MAX_PUZZLES
"""

import infrastructure
import solver

# Configuracion
PUZZLE_PATTERN = './mypuzzles/*.json'  
MAX_PUZZLES = 10                       

def main():
    print("""
===========
HASHI PUZZLE                                
===========
""")
    
    print("Iniciando el programa que resuelve los puzles")
    print("Patrón de puzles: " + str(PUZZLE_PATTERN))
    print("Número máximo de puzles: " + str(MAX_PUZZLES))
        
    stats = infrastructure.run_solver(
        solver_function=solver.solve_hashi_true_sat,
        puzzle_pattern=PUZZLE_PATTERN,
        max_puzzles=MAX_PUZZLES
    )
    
    print("\n¡Terminado! Revisa la carpeta 'solutions/' para ver los resultados.")
    
    return stats

main()
