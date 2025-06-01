# python_backend/app.py
from flask import Flask, request, send_file, jsonify
import matplotlib
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
from flask_cors import CORS
import random
import base64



app = Flask(__name__)
CORS(app)

# Global variables for parsed data
nodes = {}
placements = {}
rows = []
nets = []
nets_file_path = None
last_legality_report = None

@app.route('/process', methods=['POST'])
def process_files():
    global nodes, placements, rows, nets, nets_file_path
    try:
        files = request.files.getlist('files')
        nodes = {}
        placements = {}
        rows = []
        nets = None

        required_found = {
            "nodes": False,
            "pl": False,
            "scl": False,
            "nets": False
        }

        for file in files:
            filename = file.filename

            if filename.startswith("._"):
                continue

            if filename.endswith('.nodes'):
                nodes = parse_nodes(file)
                required_found["nodes"] = True
            elif filename.endswith('.pl'):
                placements = parse_placements(file)
                required_found["pl"] = True
            elif filename.endswith('.scl'):
                rows = parse_scl(file)
                required_found["scl"] = True
            elif filename.endswith('.nets'):
                nets = parse_nets(file)
                required_found["nets"] = True

        missing_files = [ext for ext, found in required_found.items() if not found]
        if missing_files:
            return (
                f"Error: Missing required file(s): {', '.join('.' + ext for ext in missing_files)}",
                400,
            )

        img = visualize_layout(nodes, placements, rows)
        print("Visualization generated successfully.")

        return send_file(img, mimetype='image/png')

    except KeyError as e:
        print(f"KeyError: Missing key {e}")
        return f"Error: Missing key {e}", 500
    except Exception as e:
        print(f"Error occurred during processing: {e}")
        return f"Error occurred during processing: {e}", 500


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def parse_nodes(file):
    nodes = {}

    for line in file:
        line = line.decode('utf-8').strip()
        parts = line.split()

        if len(parts) < 3:
            continue

        try:
            node_id = parts[0].strip().lower()  
            width = float(parts[1])
            height = float(parts[2])
            is_terminal = len(parts) == 4 and parts[3].lower() == 'terminal'
            nodes[node_id] = {'width': width, 'height': height, 'is_terminal': is_terminal}
        except ValueError:
            print(f"Skipping comments: {line}")
            continue

    return nodes


def parse_placements(file):
    placements = {}
    for line in file:
        line = line.decode('utf-8').strip()
        parts = line.split()

        if len(parts) >= 3 and is_float(parts[1]) and is_float(parts[2]):
            node_id = parts[0]
            x = float(parts[1])
            y = float(parts[2])
            placements[node_id] = {'x': x, 'y': y}
    return placements


def parse_scl(file):
    rows = []
    in_row = False
    row = {}

    for line in file:
        line = line.decode('utf-8').strip()
        line = ' '.join(line.split())  
        line = line.replace("NumSites", "Numsites")  

        if 'CoreRow Horizontal' in line:
            in_row = True
            row = {}
            continue
        elif 'End' in line and in_row:
            if 'coordinate' in row and 'height' in row and 'sitewidth' in row and 'subrow_origin' in row and 'numsites' in row:
                rows.append(row)
            else:
                print("Warning: Incomplete row skipped ->", row)
            in_row = False
            continue

        if in_row:
            if 'Coordinate :' in line:
                try:
                    row['coordinate'] = float(line.split(':')[1].strip())
                except ValueError:
                    print("Warning: Invalid coordinate in line:", line)
            elif 'Height :' in line:
                try:
                    row['height'] = float(line.split(':')[1].strip())
                except ValueError:
                    print("Warning: Invalid height in line:", line)
            elif 'Sitewidth :' in line:
                try:
                    row['sitewidth'] = float(line.split(':')[1].strip())
                except ValueError:
                    print("Warning: Invalid sitewidth in line:", line)
            elif 'Sitespacing :' in line:
                try:
                    row['sitespacing'] = float(line.split(':')[1].strip())
                except ValueError:
                    print("Warning: Invalid sitespacing in line:", line)
            elif 'SubrowOrigin :' in line and 'Numsites :' in line:
                try:
                    parts = line.split('SubrowOrigin :')[1].split('Numsites :')
                    row['subrow_origin'] = float(parts[0].strip())
                    row['numsites'] = float(parts[1].strip())
                except (ValueError, IndexError):
                    print("Warning: Could not parse SubrowOrigin or Numsites from line:", line)

    return rows

def parse_nets(file):
    nets = []
    current_net = None
    net_counter = 0

    for line in file:
        line = line.decode('utf-8').strip()
        parts = line.split()

        if "NetDegree" in line:
            if current_net:
                nets.append(current_net)
            net_id = f"n{net_counter}" 
            net_counter += 1
            current_net = {"net_id": net_id, "nodes": []}
        elif parts:
            node_id = parts[0].strip().lower() 
            if current_net:
                current_net["nodes"].append(node_id)

    if current_net:
        nets.append(current_net)

    return nets


def visualize_layout(nodes, placements, rows):
    plt.figure(figsize=(10, 10))
    ax = plt.gca()
    x_mins, x_maxs, y_mins, y_maxs = [], [], [], []

    for row in rows:
        if all(k in row for k in ('subrow_origin', 'coordinate', 'height', 'numsites', 'sitewidth')):
            y = row['coordinate']
            height = row['height']
            subrow_origin = row['subrow_origin']
            width = row['numsites'] * row['sitewidth']
            ax.add_patch(Rectangle((subrow_origin, y), width, height, edgecolor='grey', facecolor='lightgrey', alpha=0.3))

    regular_patches = []
    terminal_patches = []
    min_terminal_size = 1.0

    for node_id, placement in placements.items():
        if node_id not in nodes:
            continue
        x, y = placement.get('x'), placement.get('y')
        if x is None or y is None:
            continue

        node = nodes[node_id]
        width = abs(node.get('width', 1))
        height = abs(node.get('height', 1))
        is_terminal = node.get("is_terminal", False)

        if is_terminal:
            width = max(width, min_terminal_size)
            height = max(height, min_terminal_size)
            terminal_patches.append(Rectangle((x, y), width, height))
        else:
            regular_patches.append(Rectangle((x, y), width, height))

        x_mins.append(x)
        x_maxs.append(x + width)
        y_mins.append(y)
        y_maxs.append(y + height)

    ax.add_collection(PatchCollection(regular_patches, facecolor='skyblue', edgecolor='blue', alpha=0.7))
    ax.add_collection(PatchCollection(terminal_patches, facecolor='red', edgecolor='red', alpha=0.8))

    if x_mins and x_maxs and y_mins and y_maxs:
        plt.xlim(min(x_mins) - 10, max(x_maxs) + 10)
        plt.ylim(min(y_mins) - 10, max(y_maxs) + 10)

    ax.set_aspect('equal', 'box')
    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.title('Bookshelf Layout Visualization')

    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=300)
    plt.close()
    img.seek(0)
    return img


def calculate_total_wire_length(nets, placements):
    total_length = 0

    for net in nets:
        valid_nodes = [node for node in net["nodes"] if node in placements]
        if len(valid_nodes) < 2:
            continue  

        min_x = min(placements[node]['x'] for node in valid_nodes)
        max_x = max(placements[node]['x'] for node in valid_nodes)
        min_y = min(placements[node]['y'] for node in valid_nodes)
        max_y = max(placements[node]['y'] for node in valid_nodes)

        wire_length = (max_x - min_x) + (max_y - min_y)
        total_length += wire_length

    return total_length



@app.route('/calculate_wire_length', methods=['GET'])
def calculate_wire_length():
    global nets, placements

    if not nets:
        print("Error: nets data is empty or not parsed.")
        return jsonify({"error": "No .nets file parsed"}), 400
    if not placements:
        print("Error: placements data is empty or not parsed.")
        return jsonify({"error": "No .pl file parsed"}), 400
    
    try:
        total_length = calculate_total_wire_length(nets, placements)
        print(f"Total wire length: {total_length}")
        return jsonify({"total_length": total_length})
    except Exception as e:
        print(f"Error calculating wire length: {e}")
        return jsonify({"error": f"Error calculating wire length: {e}"}), 500



@app.route('/calculate_net_length/<net_id>', methods=['GET'])
def calculate_net_length_hpwl(net_id):
    global nets, placements

    net = next((n for n in nets if n['net_id'] == net_id), None)
    if not net:
        return jsonify({"error": f"Net {net_id} not found"}), 404

    valid_nodes = [node for node in net['nodes'] if node in placements]
    if len(valid_nodes) < 2:
        return jsonify({"error": f"Not enough valid nodes in net {net_id} to calculate wire length"}), 400

    min_x = min(placements[node]['x'] for node in valid_nodes)
    max_x = max(placements[node]['x'] for node in valid_nodes)
    min_y = min(placements[node]['y'] for node in valid_nodes)
    max_y = max(placements[node]['y'] for node in valid_nodes)

    wire_length = (max_x - min_x) + (max_y - min_y)

    return jsonify({"wire_length": wire_length})


@app.route('/get_node_coordinates/<node_id>', methods=['GET'])
def get_node_coordinates(node_id):
    global placements

    if node_id not in placements:
        print(f"Node {node_id} not found in placements.")
        return jsonify({"error": f"Node {node_id} not found"}), 404

    coordinates = placements[node_id]
    return jsonify({"coordinates": coordinates})


@app.route('/node_size_statistics', methods=['GET'])
def node_size_statistics():
    global nodes

    node_sizes = [
        {"node_id": node_id, "area": node["width"] * node["height"]}
        for node_id, node in nodes.items()
    ]
    sorted_node_sizes = sorted(node_sizes, key=lambda x: x["area"], reverse=True)

    return jsonify(sorted_node_sizes)



@app.route('/sorted_nets', methods=['GET'])
def sorted_nets_by_wirelength():
    global nets, placements

    if not nets or not placements:
        return jsonify({"error": "No nets or placements available"}), 400

    def calculate_net_hpwl(net):
        valid_nodes = [node for node in net['nodes'] if node in placements]
        if len(valid_nodes) < 2:
            return 0 

        min_x = min(placements[node]['x'] for node in valid_nodes)
        max_x = max(placements[node]['x'] for node in valid_nodes)
        min_y = min(placements[node]['y'] for node in valid_nodes)
        max_y = max(placements[node]['y'] for node in valid_nodes)

        return (max_x - min_x) + (max_y - min_y)

    sorted_nets = sorted(
        [
            {
                "net_id": net["net_id"],
                "hpwl": calculate_net_hpwl(net),
                "nodes": net["nodes"]
            }
            for net in nets
        ],
        key=lambda n: n["hpwl"],
        reverse=True
    )

    return jsonify(sorted_nets)



random_placements = {}

@app.route('/random_placement', methods=['POST'])
def random_placement():
    global nodes, rows, random_placements
    random_placements = {}  

    max_width = max(row['subrow_origin'] + row['numsites'] * row['sitewidth'] for row in rows)
    max_height = max(row['coordinate'] + row['height'] for row in rows)

    for node_id, node in nodes.items():
        is_terminal = node.get('is_terminal', False)
        node_width = abs(node.get('width', 1))
        node_height = abs(node.get('height', 1))

        if is_terminal:
            random_placements[node_id] = placements[node_id]
        else:
            random_x = random.uniform(0, max_width - node_width)
            random_y = random.uniform(0, max_height - node_height)

            random_placements[node_id] = {'x': random_x, 'y': random_y}
    return jsonify({"success": True})



@app.route('/random_visualize_layout', methods=['GET'])
def random_visualize_layout():
    global nodes, random_placements, rows
    img = visualize_layout(nodes, random_placements, rows) 
    return send_file(img, mimetype='image/png')


@app.route('/random_calculate_wire_length', methods=['GET'])
def random_calculate_wire_length():
    total_length = calculate_total_wire_length(nets, random_placements)
    return jsonify({"total_length": total_length})


@app.route('/random_calculate_net_length/<net_id>', methods=['GET'])
def random_calculate_net_length(net_id):
    global nets, random_placements

    net = next((n for n in nets if n['net_id'] == net_id), None)
    if not net:
        return jsonify({"error": f"Net {net_id} not found"}), 404

    valid_nodes = [node for node in net['nodes'] if node in random_placements]
    if len(valid_nodes) < 2:
        return jsonify({"error": f"Not enough valid nodes in net {net_id} to calculate wire length"}), 400

    min_x = min(random_placements[node]['x'] for node in valid_nodes)
    max_x = max(random_placements[node]['x'] for node in valid_nodes)
    min_y = min(random_placements[node]['y'] for node in valid_nodes)
    max_y = max(random_placements[node]['y'] for node in valid_nodes)

    wire_length = (max_x - min_x) + (max_y - min_y)
    return jsonify({"wire_length": wire_length})


@app.route('/random_node_coordinates', methods=['GET'])
def random_node_coordinates():
    node_id = request.args.get('node_id')
    if not node_id:
        return jsonify({"error": "Node ID is required"}), 400

    if node_id in random_placements:
        coordinates = random_placements[node_id]
        return jsonify({"x": coordinates['x'], "y": coordinates['y']})
    else:
        return jsonify({"error": f"Node {node_id} not found in random placements"}), 404


def calculate_net_hpwl(net, placements):
    
    valid_nodes = [node for node in net['nodes'] if node in placements]

    if len(valid_nodes) < 2:
        return 0

    min_x = min(placements[node]['x'] for node in valid_nodes)
    max_x = max(placements[node]['x'] for node in valid_nodes)
    min_y = min(placements[node]['y'] for node in valid_nodes)
    max_y = max(placements[node]['y'] for node in valid_nodes)

    hpwl = (max_x - min_x) + (max_y - min_y)
    return hpwl


@app.route('/largest_smallest_nets_hpwl', methods=['GET'])
def largest_smallest_nets_hpwl_combined():
    global nets, placements
    if not nets or not placements:
        return jsonify({"error": "Nets or placements data is not available"}), 400

    placements = {key.strip().lower(): value for key, value in placements.items()}

    for net in nets:
        net['nodes'] = [node.strip().lower() for node in net['nodes']]

    net_hpwl_data = []

    for net in nets:
        hpwl = calculate_net_hpwl(net, placements)
        net_hpwl_data.append({
            "net_id": net['net_id'],
            "hpwl": hpwl,
            "nodes": net['nodes']
        })

    largest_net = max(net_hpwl_data, key=lambda n: n["hpwl"], default=None)
    smallest_net = min(net_hpwl_data, key=lambda n: n["hpwl"], default=None)

    return jsonify({
        "largest_net": largest_net,
        "smallest_net": smallest_net
    })

@app.route('/random_largest_smallest_nets_hpwl', methods=['GET'])
def random_largest_smallest_nets_hpwl():
    global nets, random_placements
    if not nets or not random_placements:
        return jsonify({"error": "Nets or placements data is not available"}), 400

    random_placements = {key.strip().lower(): value for key, value in random_placements.items()}

    for net in nets:
        net['nodes'] = [node.strip().lower() for node in net['nodes']]

    net_hpwl_data = []

    for net in nets:
        hpwl = calculate_net_hpwl(net, random_placements)
        net_hpwl_data.append({
            "net_id": net['net_id'],
            "hpwl": hpwl,
            "nodes": net['nodes']
        })

    largest_net = max(net_hpwl_data, key=lambda n: n["hpwl"], default=None)
    smallest_net = min(net_hpwl_data, key=lambda n: n["hpwl"], default=None)

    return jsonify({
        "largest_net": largest_net,
        "smallest_net": smallest_net
    })


# @app.route('/legality_check', methods=['GET'])
# def legality_check():
#     global nodes, placements, rows

#     issues = {"overlaps": [], "misaligned": [], "out_of_bounds": []}

#     checked_nodes = []
#     for node_id, placement in placements.items():
#         if nodes.get(node_id, {}).get("is_terminal", False):
#             continue  

#         node_width = abs(nodes[node_id].get("width", 1))
#         node_height = abs(nodes[node_id].get("height", 1))

#         node_rect = {
#             "x_min": placement["x"],
#             "x_max": placement["x"] + node_width,
#             "y_min": placement["y"],
#             "y_max": placement["y"] + node_height
#         }

#         for checked_node in checked_nodes:
#             checked_rect = checked_node["rect"]

#             if not (
#                 node_rect["x_max"] <= checked_rect["x_min"] or  
#                 node_rect["x_min"] >= checked_rect["x_max"] or  
#                 node_rect["y_max"] <= checked_rect["y_min"] or  
#                 node_rect["y_min"] >= checked_rect["y_max"]    
#             ):
#                 issues["overlaps"].append({
#                     "node1": node_id,
#                     "node2": checked_node["id"]
#                 })

#         checked_nodes.append({"id": node_id, "rect": node_rect})

#     for node_id, placement in placements.items():
#         if nodes.get(node_id, {}).get("is_terminal", False):
#             continue  

#         node_width = abs(nodes[node_id].get("width", 1))
#         node_height = abs(nodes[node_id].get("height", 1))

#         aligned = False
#         for row in rows:
#             row_min_x = row["subrow_origin"]
#             row_max_x = row["subrow_origin"] + row["numsites"] * row["sitewidth"]
#             row_y = row["coordinate"]

#             if (
#                 row_min_x <= placement["x"] and
#                 (placement["x"] + node_width) <= row_max_x and
#                 row_y <= placement["y"] and
#                 (placement["y"] + node_height) <= (row_y + row["height"])
#             ):
#                 aligned = True
#                 break

#         if not aligned:
#             issues["misaligned"].append({
#                 "node": node_id,
#                 "x_min": placement["x"],
#                 "x_max": placement["x"] + node_width,
#                 "y_min": placement["y"],
#                 "y_max": placement["y"] + node_height
#             })

#     max_width = max(row["subrow_origin"] + row["numsites"] * row["sitewidth"] for row in rows)
#     max_height = max(row["coordinate"] + row["height"] for row in rows)

#     for node_id, placement in placements.items():
#         if nodes.get(node_id, {}).get("is_terminal", False):
#             continue  

#         node_width = abs(nodes[node_id].get("width", 1))
#         node_height = abs(nodes[node_id].get("height", 1))

#         if not (
#             0 <= placement["x"] and
#             (placement["x"] + node_width) <= max_width and
#             0 <= placement["y"] and
#             (placement["y"] + node_height) <= max_height
#         ):
#             issues["out_of_bounds"].append({
#                 "node": node_id,
#                 "x_min": placement["x"],
#                 "x_max": placement["x"] + node_width,
#                 "y_min": placement["y"],
#                 "y_max": placement["y"] + node_height
#             })

#     if not issues["overlaps"] and not issues["misaligned"] and not issues["out_of_bounds"]:
#         return jsonify({"message": "The design is legal!"})

#     return jsonify(issues)

@app.route('/legality_check', methods=['GET'])
def legality_check():
    global nodes, placements, rows

    issues = {
        "overlaps": 0,
        "misaligned": 0,
        "out_of_bounds": 0
    }

    # --- Overlap check ---
    node_rects = []
    for node_id, placement in placements.items():
        if nodes.get(node_id, {}).get("is_terminal", False):
            continue

        width = abs(nodes[node_id].get("width", 1))
        height = abs(nodes[node_id].get("height", 1))
        rect = {
            "id": node_id,
            "x_min": placement["x"],
            "x_max": placement["x"] + width,
            "y_min": placement["y"],
            "y_max": placement["y"] + height
        }

        for prev in node_rects:
            if not (
                rect["x_max"] <= prev["x_min"] or
                rect["x_min"] >= prev["x_max"] or
                rect["y_max"] <= prev["y_min"] or
                rect["y_min"] >= prev["y_max"]
            ):
                issues["overlaps"] += 1

        node_rects.append(rect)

    # --- Misalignment check ---
    for node_id, placement in placements.items():
        if nodes.get(node_id, {}).get("is_terminal", False):
            continue

        width = abs(nodes[node_id].get("width", 1))
        height = abs(nodes[node_id].get("height", 1))
        aligned = False

        for row in rows:
            x0 = row["subrow_origin"]
            x1 = x0 + row["numsites"] * row["sitewidth"]
            y0 = row["coordinate"]
            y1 = y0 + row["height"]

            if (
                x0 <= placement["x"] and (placement["x"] + width) <= x1 and
                y0 <= placement["y"] and (placement["y"] + height) <= y1
            ):
                aligned = True
                break

        if not aligned:
            issues["misaligned"] += 1

    # --- Out of bounds check ---
    max_x = max(r["subrow_origin"] + r["numsites"] * r["sitewidth"] for r in rows)
    max_y = max(r["coordinate"] + r["height"] for r in rows)

    for node_id, placement in placements.items():
        if nodes.get(node_id, {}).get("is_terminal", False):
            continue

        width = abs(nodes[node_id].get("width", 1))
        height = abs(nodes[node_id].get("height", 1))

        if not (
            0 <= placement["x"] <= max_x - width and
            0 <= placement["y"] <= max_y - height
        ):
            issues["out_of_bounds"] += 1

    # --- Return counts only ---
    return jsonify({
        "message": "Legality check completed",
        "summary": issues
    })
    

@app.route('/random_legality_check', methods=['GET'])
def random_legality_check():
    global nodes, random_placements, rows

    issues = {
        "overlaps": 0,
        "misaligned": 0,
        "out_of_bounds": 0
    }

    node_rects = []

    # Overlap check
    for node_id, placement in random_placements.items():
        if nodes.get(node_id, {}).get("is_terminal", False):
            continue

        width = abs(nodes[node_id].get("width", 1))
        height = abs(nodes[node_id].get("height", 1))
        rect = {
            "id": node_id,
            "x_min": placement["x"],
            "x_max": placement["x"] + width,
            "y_min": placement["y"],
            "y_max": placement["y"] + height
        }

        for other in node_rects:
            if not (
                rect["x_max"] <= other["x_min"] or
                rect["x_min"] >= other["x_max"] or
                rect["y_max"] <= other["y_min"] or
                rect["y_min"] >= other["y_max"]
            ):
                issues["overlaps"] += 1
        node_rects.append(rect)

    # Misalignment check
    for node_id, placement in random_placements.items():
        if nodes.get(node_id, {}).get("is_terminal", False):
            continue

        width = abs(nodes[node_id].get("width", 1))
        height = abs(nodes[node_id].get("height", 1))
        aligned = False

        for row in rows:
            x0 = row["subrow_origin"]
            x1 = x0 + row["numsites"] * row["sitewidth"]
            y0 = row["coordinate"]
            y1 = y0 + row["height"]

            if (
                x0 <= placement["x"] and (placement["x"] + width) <= x1 and
                y0 <= placement["y"] and (placement["y"] + height) <= y1
            ):
                aligned = True
                break

        if not aligned:
            issues["misaligned"] += 1

    # Out-of-bounds check
    max_x = max(r["subrow_origin"] + r["numsites"] * r["sitewidth"] for r in rows)
    max_y = max(r["coordinate"] + r["height"] for r in rows)

    for node_id, placement in random_placements.items():
        if nodes.get(node_id, {}).get("is_terminal", False):
            continue

        width = abs(nodes[node_id].get("width", 1))
        height = abs(nodes[node_id].get("height", 1))

        if not (
            0 <= placement["x"] <= max_x - width and
            0 <= placement["y"] <= max_y - height
        ):
            issues["out_of_bounds"] += 1

    # Return compact summary
    return jsonify({
        "message": "Random legality check completed",
        "summary": issues
    })


@app.route('/random_sorted_nets', methods=['GET'])
def sorted_nets_by_wirelength_random():
    global nets, random_placements

    if not nets or not random_placements:
        return jsonify({"error": "No nets available"}), 400

    def calculate_net_hpwl(net):
        valid_nodes = [node for node in net['nodes'] if node in random_placements]
        if len(valid_nodes) < 2:
            return 0 

        min_x = min(random_placements[node]['x'] for node in valid_nodes)
        max_x = max(random_placements[node]['x'] for node in valid_nodes)
        min_y = min(random_placements[node]['y'] for node in valid_nodes)
        max_y = max(random_placements[node]['y'] for node in valid_nodes)

        return (max_x - min_x) + (max_y - min_y)

    sorted_nets = sorted(
        [
            {
                "net_id": net["net_id"],
                "hpwl": calculate_net_hpwl(net),
                "nodes": net["nodes"]
            }
            for net in nets
        ],
        key=lambda n: n["hpwl"],
        reverse=True
    )

    return jsonify(sorted_nets)


# @app.route('/modify_node_coordinates', methods=['POST'])
# def modify_node_coordinates():
#     global placements

#     try:
#         data = request.get_json()
#         node_id = data.get('node_id')
#         new_x = float(data.get('x'))
#         new_y = float(data.get('y'))

#         if node_id not in placements:
#             return jsonify({"error": f"Node {node_id} not found"}), 404

#         placements[node_id]['x'] = new_x
#         placements[node_id]['y'] = new_y

#         img = visualize_layout(nodes, placements, rows)
#         img_url = f"data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}"

#         return jsonify({"message": f"Node {node_id} updated successfully", "image_url": img_url})
#     except Exception as e:
#         print(f"Error modifying node coordinates: {e}")
#         return jsonify({"error": str(e)}), 500

@app.route('/modify_node_coordinates', methods=['POST'])
def modify_node_coordinates():
    global placements, nodes, nets, rows

    try:
        data = request.get_json()
        node_id = data.get('node_id')
        new_x = float(data.get('x'))
        new_y = float(data.get('y'))

        if node_id not in placements:
            return jsonify({"error": f"Node {node_id} not found"}), 404

        # Apply change
        placements[node_id]['x'] = new_x
        placements[node_id]['y'] = new_y

        # Identify affected nets
        affected_nets = [net for net in nets if node_id in net["nodes"]]

        # Half-Perimeter Wirelength (HPWL) for a net
        def hpwl(net):
            coords = [(placements[n]["x"], placements[n]["y"]) for n in net["nodes"] if n in placements]
            if not coords:
                return 0
            xs, ys = zip(*coords)
            return (max(xs) - min(xs)) + (max(ys) - min(ys))

        # Total wirelength after the change
        total_wirelength = sum(hpwl(net) for net in nets)

        # Affected net lengths
        affected_info = [{
            "net_id": net["net_id"],
            "length": round(hpwl(net), 2)
        } for net in affected_nets]

        # Redraw
        img = visualize_layout(nodes, placements, rows)
        img_url = f"data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}"

        return jsonify({
            "message": f"Node {node_id} updated successfully.",
            "image_url": img_url,
            "updated_total_wirelength": round(total_wirelength, 2),
            "affected_nets": affected_info
        })

    except Exception as e:
        print(f"Error modifying node coordinates: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/random_modify_node_coordinates', methods=['POST'])
def random_modify_node_coordinates():
    global random_placements

    try:
        data = request.get_json()
        node_id = data.get('node_id')
        new_x = float(data.get('x'))
        new_y = float(data.get('y'))

        if node_id not in random_placements:
            return jsonify({"error": f"Node {node_id} not found in random placements"}), 404

        random_placements[node_id]['x'] = new_x
        random_placements[node_id]['y'] = new_y

        img = visualize_layout(nodes, random_placements, rows)
        img_url = f"data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}"

        return jsonify({"message": f"Node {node_id} updated successfully", "image_url": img_url})
    except Exception as e:
        print(f"Error modifying random node coordinates: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/legalize_placement', methods=['POST'])
def legalize_placement():
    global nodes, placements, rows

    try:
        legalized_placements, skipped = tetris_legalize(nodes, rows, placements)
        img = visualize_layout(nodes, legalized_placements, rows)
        img_url = f"data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}"

        return jsonify({
            "message": "Legalization completed.",
            "image_url": img_url,
            "skipped_nodes": skipped
        })
    except Exception as e:
        print("Error during legalization:", str(e))
        return jsonify({"error": str(e)}), 500
    
def tetris_legalize(nodes, rows, placements):
    legalized = {}
    skipped_nodes = []
    row_x_positions = {i: row['subrow_origin'] for i, row in enumerate(rows)}

    for node_id, node in nodes.items():
        if node.get("is_terminal", False):
            legalized[node_id] = placements[node_id]
            continue

        width = abs(node.get("width", 1))
        height = abs(node.get("height", 1))
        placed = False


        for i, row in enumerate(rows):
            row_y = row['coordinate']
            row_height = row['height']
            start_x = row_x_positions[i]
            end_x = row['subrow_origin'] + row['numsites'] * row['sitewidth']

            if height > row_height:
                continue

            if start_x + width <= end_x:
                legalized[node_id] = {"x": start_x, "y": row_y}
                row_x_positions[i] += width
                placed = True
                break

        if not placed:
            print(f"FAILED to place node {node_id}")
            skipped_nodes.append(node_id)

    return legalized, skipped_nodes

@app.route('/detailed_placement', methods=['POST'])
def detailed_placement():
    global nodes, placements, rows

    legalized = {}
    failed_nodes = []

    row_end_positions = {
        i: row['subrow_origin'] + row['numsites'] * row['sitewidth']
        for i, row in enumerate(rows)
    }

    movable_nodes = [
        (node_id, placements[node_id]['x'])
        for node_id in nodes
        if node_id in placements and not nodes[node_id].get("is_terminal", False)
    ]
    movable_nodes.sort(key=lambda x: -x[1])  

    for node_id, _ in movable_nodes:
        node = nodes[node_id]
        width = abs(node.get("width", 1))
        height = abs(node.get("height", 1))
        placed = False

        for i, row in enumerate(rows):
            row_y = row['coordinate']
            row_height = row['height']
            end_x = row_end_positions[i]
            start_x = end_x - width  

            if height <= row_height and start_x >= row['subrow_origin']:
                legalized[node_id] = {"x": start_x, "y": row_y}
                row_end_positions[i] -= width 
                placed = True
                break

        if not placed:
            failed_nodes.append(node_id)

    for node_id, data in placements.items():
        if nodes.get(node_id, {}).get("is_terminal", False):
            legalized[node_id] = data

    img = visualize_layout(nodes, legalized, rows)
    img_url = f"data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}"

    return jsonify({
        "message": f"Legalization complete. {len(failed_nodes)} nodes failed to place." if failed_nodes else "All nodes placed successfully.",
        "image_url": img_url,
        "failed_nodes": failed_nodes
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))  # required for Render
    app.run(host='0.0.0.0', port=port)
