"""
Core infrastructure for running Hashi puzzle solvers.
DO NOT MODIFY - This is part of the course infrastructure.

"""

import json
import os
import glob
import copy
import traceback


def load_template():
    """
    Load the HTML template for puzzle visualization.

    Returns:
        str: HTML template content

    Raises:
        FileNotFoundError: If template file is not found
    """
    template_path = os.path.join('templates', 'template.html')
    template_path = os.path.normpath(template_path)

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Template file not found at {template_path}\n"
            f"Make sure 'templates/template.html' exists in the project root."
        )


def create_html_from_json_data(data, output_html):
    """
    Create an HTML visualization from solution or puzzle data.
    PRESERVA todos los campos de cada isla exactamente como vienen.
    Normaliza a un dict con keys: width, height, islands, solution para el template,
    pero no recorta ni elimina elementos dentro de cada isla.
    """
    if isinstance(data, list):
        if len(data) >= 2 and isinstance(data[0], list) and isinstance(data[1], list):
            dims = data[0]
            islands_raw = data[1]
            islands = []
            for isl in islands_raw:
                if isinstance(isl, list):
                    new_isl = []
                    for val in isl:
                        try:
                            new_isl.append(int(val))
                        except Exception:
                            new_isl.append(val)
                    islands.append(new_isl)
                else:
                    islands.append(isl)
            norm = {
                "width": int(dims[0]),
                "height": int(dims[1]),
                "islands": islands,
                "solution": []
            }
        else:
            raise ValueError("Formato de lista inesperado en data")
    elif isinstance(data, dict):
        islands_raw = data.get("islands", [])
        islands = []
        for isl in islands_raw:
            if isinstance(isl, list):
                new_isl = []
                for val in isl:
                    try:
                        new_isl.append(int(val))
                    except Exception:
                        new_isl.append(val)
                islands.append(new_isl)
            else:
                islands.append(isl)
        norm = {
            "width": data.get("width"),
            "height": data.get("height"),
            "islands": islands,
            "solution": data.get("solution", [])
        }
    else:
        raise TypeError("create_html_from_json_data: data debe ser dict o list")

    embedded_json = json.dumps(norm)
    html_content = load_template()
    html_content = html_content.replace("{embedded_json}", embedded_json)

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)


def validate_solution_format(solution_data):
    if solution_data is None:
        return False

    required_keys = ['width', 'height', 'islands', 'solution']
    if not all(key in solution_data for key in required_keys):
        return False

    if not isinstance(solution_data['solution'], list):
        return False

    for bridge in solution_data['solution']:
        if not isinstance(bridge, dict):
            return False
        if 'bridges' not in bridge:
            return False
        has_coords = all(k in bridge for k in ('x1', 'y1', 'x2', 'y2'))
        has_ids = all(k in bridge for k in ('id1', 'id2'))
        if not (has_coords or has_ids):
            return False
    return True


def load_puzzle(filename):
    """
    Load a Hashi puzzle from a JSON file.

    Args:
        filename (str): Path to the puzzle JSON file

    Returns:
        list: [dimensions, islands_data]
            - dimensions: [width, height]
            - islands_data: List of [x, y, required_bridges, island_id] (or whatever fields the file has)
    """
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    dimensions = data[0]
    islands_data = data[1]
    return [dimensions, islands_data]


def run_solver(solver_function, puzzle_pattern='./mypuzzles/*.json', max_puzzles=100):
    """
    Run a solver function on all puzzle files matching the pattern.
    
    """
    os.makedirs('solutions', exist_ok=True)
    puzzle_files = glob.glob(puzzle_pattern)

    stats = {
        'total': 0,
        'solved': 0,
        'unsolved': 0,
        'errors': 0
    }

    for puzzle_file in puzzle_files[:max_puzzles]:
        stats['total'] += 1
        print(f"\n{'='*60}")
        print(f"Processing: {puzzle_file}")
        print(f"{'='*60}")

        try:
            result = load_puzzle(puzzle_file)
            dimensions = result[0]
            islands_data = result[1]  
            orig_islands = copy.deepcopy(islands_data)

            solution_result = solver_function(dimensions, islands_data)


            base_name = os.path.splitext(os.path.basename(puzzle_file))[0]
            solution_json_file = f'./solutions/{base_name}_solution.json'
            output_html_file = f'./solutions/{base_name}.html'

            if solution_result is None:
                final_solution = {
                    "width": dimensions[0],
                    "height": dimensions[1],
                    "islands": orig_islands,
                    "solution": []
                }
                print(f"✗ NO SOLUTION found for {puzzle_file}")
                stats['unsolved'] += 1
            else:
                if isinstance(solution_result, dict) and 'solution' in solution_result:
                    islands_from_solver = solution_result.get("islands")
                    use_solver_islands = False
                    if isinstance(islands_from_solver, list) and len(islands_from_solver) == len(orig_islands):
                        try:
                            if all(isinstance(it, list) and len(it) >= 3 for it in islands_from_solver):
                                use_solver_islands = True
                        except Exception:
                            use_solver_islands = False

                    islands_to_use = islands_from_solver if use_solver_islands else orig_islands

                    final_solution = {
                        "width": solution_result.get("width", dimensions[0]),
                        "height": solution_result.get("height", dimensions[1]),
                        "islands": islands_to_use,
                        "solution": solution_result.get("solution", [])
                    }
                else:
                    final_solution = {
                        "width": dimensions[0],
                        "height": dimensions[1],
                        "islands": orig_islands,
                        "solution": solution_result
                    }

                print(f"✓ SOLVED: {puzzle_file}")
                stats['solved'] += 1

            with open(solution_json_file, 'w', encoding='utf-8') as jf:
                json.dump(final_solution, jf, indent=4, ensure_ascii=False)

            create_html_from_json_data(final_solution, output_html_file)
            print(f"  → JSON: {solution_json_file}")
            print(f"  → HTML: {output_html_file}")

        except Exception as e:
            print(f"✗ ERROR processing {puzzle_file}: {str(e)}")
            traceback.print_exc()
            stats['errors'] += 1

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total puzzles:    {stats['total']}")
    print(f"Solved:           {stats['solved']}")
    print(f"Unsolved:         {stats['unsolved']}")
    print(f"Errors:           {stats['errors']}")
    print(f"{'='*60}")

    return stats
