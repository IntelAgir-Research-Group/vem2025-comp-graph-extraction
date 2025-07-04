import os
import subprocess
import ast
import json
from collections import defaultdict

PROJECTS_FILE = r"./crawling/links.csv"
RESULTS_FILE = r"./crawling/scripts/topicpubsubpycaminho.txt"
CLONE_DIR = "repos/"
JSON_DIR = r"./crawling/scripts/models"

os.makedirs(CLONE_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

def clone_repo(repo_url):
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(CLONE_DIR, repo_name)
    if not os.path.exists(repo_path):
        try:
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)
            print(f"Repository cloned: {repo_url}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {repo_url}: {e}")
            return None
    return repo_path

def extract_topics(file_path):
    topics = defaultdict(lambda: {"publishers": [], "subscribers": []})
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            tree = ast.parse(file.read(), filename=file_path)

            class_def_nodes = {
                node.name: node for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            }

            node_name_map = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    call = node.value
                    if (isinstance(call.func, ast.Attribute)
                            and isinstance(call.func.value, ast.Name)
                            and call.func.value.id == "rclpy"
                            and call.func.attr == "create_node"):
                        if len(call.args) >= 1 and isinstance(call.args[0], ast.Str):
                            node_var = node.targets[0].id
                            node_name_map[node_var] = call.args[0].s

            func_node_names = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    call = node.value
                    if isinstance(call.func, ast.Name) and call.func.id == "Node":
                        if len(call.args) >= 1:
                            if isinstance(call.args[0], ast.Str):
                                func_node_names[node.targets[0].id] = call.args[0].s
                            else:
                                func_node_names[node.targets[0].id] = "unknown (variable or dynamic)"

            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    topic_type = "publishers" if node.func.attr == "create_publisher" else (
                        "subscribers" if node.func.attr == "create_subscription" else None
                    )
                    if topic_type and len(node.args) > 1 and isinstance(node.args[1], ast.Str):
                        topic_name = node.args[1].s
                        node_name = "unknown"
                        detection_type = ""

                        for class_name, class_node in class_def_nodes.items():
                            if node in ast.walk(class_node):
                                node_name = class_name
                                detection_type = "(class-based)"
                                break

                        if node_name == "unknown":
                            if isinstance(node.func.value, ast.Name):
                                node_var = node.func.value.id
                                if node_var in node_name_map:
                                    node_name = node_name_map[node_var]
                                    detection_type = "(via rclpy.create_node)"
                                elif node_var in func_node_names:
                                    node_name = func_node_names[node_var]
                                    detection_type = "(variable-based)"

                        topics[topic_name][topic_type].append((file_path, node.lineno, node_name, detection_type))
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    return topics

def process_repos():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f, open(RESULTS_FILE, "w", encoding="utf-8") as results_file:
        for repo_url in f:
            repo_url = repo_url.strip()
            if not repo_url:
                continue

            print(f"Processing repository: {repo_url}...")
            repo_path = clone_repo(repo_url)
            if not repo_path:
                continue

            repo_topics = defaultdict(lambda: {"publishers": [], "subscribers": []})
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        file_topics = extract_topics(file_path)
                        for topic, data in file_topics.items():
                            repo_topics[topic]["publishers"].extend(data["publishers"])
                            repo_topics[topic]["subscribers"].extend(data["subscribers"])

            if repo_topics:
                results_file.write(f"Repository: {repo_url}\n")
                for topic, data in repo_topics.items():
                    results_file.write(f"  Topic: {topic}\n")
                    for pub in data["publishers"]:
                        file_link = f"file:///{os.path.abspath(pub[0]).replace(os.sep, '/')}"
                        results_file.write(
                            f"    [Publisher] Node: {pub[2]} {pub[3]} | File: {file_link} | Line: {pub[1]}\n"
                        )
                    for sub in data["subscribers"]:
                        file_link = f"file:///{os.path.abspath(sub[0]).replace(os.sep, '/')}"
                        results_file.write(
                            f"    [Subscriber] Node: {sub[2]} {sub[3]} | File: {file_link} | Line: {sub[1]}\n"
                        )
                results_file.write("\n")

               
                json_data = {
                    "repository": repo_url,
                    "topics": {}
                }

                for topic, data in repo_topics.items():
                    json_data["topics"][topic] = {}
                    if data["publishers"]:
                        json_data["topics"][topic]["publishers"] = sorted(set([p[2] for p in data["publishers"]]))
                    if data["subscribers"]:
                        json_data["topics"][topic]["subscribers"] = sorted(set([s[2] for s in data["subscribers"]]))

                repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
                json_file_path = os.path.join(JSON_DIR, f"{repo_name}.json")
                with open(json_file_path, "w", encoding="utf-8") as jf:
                    json.dump([json_data], jf, indent=2, ensure_ascii=False)

            print(f"Finished: {repo_url}")

    print(f"Search completed! Results saved to: {RESULTS_FILE}")

if __name__ == "__main__":
    process_repos()
