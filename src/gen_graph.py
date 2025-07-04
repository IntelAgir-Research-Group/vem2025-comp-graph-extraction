import os
import json
import subprocess

input_folder = "./models"    # Folder with your JSON files
output_folder = "./graphs"      # Output folder for .dot and .png
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_path = os.path.join(input_folder, filename)
        with open(input_path, "r") as f:
            data = json.load(f)

        project = data[0]  # assuming only one project per JSON
        topics = project.get("topics", {})

        lines = [
            'digraph ROS2_Computation_Graph {',
            '  rankdir=LR;',
            '  node [shape=box, style=filled, fillcolor=lightgray];'
        ]

        nodes = set()

        for topic_name, info in topics.items():
            lines.append(f'  "{topic_name}" [shape=ellipse, fillcolor=white];')

            for pub in info.get("publishers", []):
                nodes.add(pub)
                lines.append(f'  "{pub}" -> "{topic_name}";')

            for sub in info.get("subscribers", []):
                nodes.add(sub)
                lines.append(f'  "{topic_name}" -> "{sub}";')

        for node in nodes:
            lines.append(f'  "{node}" [shape=box, fillcolor=lightblue];')

        lines.append("}")

        # Write .dot file
        base_name = os.path.splitext(filename)[0]
        dot_path = os.path.join(output_folder, f"{base_name}.dot")
        with open(dot_path, "w") as f:
            f.write("\n".join(lines))

        # Generate .png file
        png_path = os.path.join(output_folder, f"{base_name}.png")
        subprocess.run(["dot", "-Tpng", dot_path, "-o", png_path], check=True)
