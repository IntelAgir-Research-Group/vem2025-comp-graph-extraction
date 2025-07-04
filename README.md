# Replication Package - VEM 2025

*Title: Static Extraction of ROS 2 Computation Graphs for Visualizing and Understanding Robotics Software Architecture*

## Repository Organization

```
crawling/               - Folder with files used for crawling the repositories.
graphs/                 - Folder with computation graphs (PNG).
models/                 - Folder with JSON files.
src/                    - Folder with Extractor.
.extractor_python.log   - Log of Python extraction.
```

## Create a Virtual Environment for Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Clone Repositories and Generate JSON with Computation Models

```bash
python3 src/extractpr_python.py
```

## Generate Computation Graphs

```bash
python3 src/gen_graph.py
```

