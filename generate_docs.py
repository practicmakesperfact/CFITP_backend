import os
import subprocess
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs" / "diagrams"
APPS_DIR = BASE_DIR / "apps"

# Create output folder if it doesn't exist
DOCS_DIR.mkdir(parents=True, exist_ok=True)

print(" Generating project diagrams for CFITP...\n")

# Ensure every app has __init__.py so pyreverse recognizes it
for app in APPS_DIR.iterdir():
    if app.is_dir() and not (app / "__init__.py").exists():
        (app / "__init__.py").touch()
        print(f" Added __init__.py to: {app.name}")

# Generate ER Diagram using django-extensions
print("\n🧩 Generating ER Diagram...")
subprocess.run([
    "python", "manage.py", "graph_models", "apps", "-a", "-g", "-o",
    str(DOCS_DIR / "cfitp_models.png")
])

# Generate Class & Package Diagrams using pyreverse
print("\n Generating Class and Package Diagrams...")
subprocess.run(["pyreverse", "-o", "dot", "-p", "CFITP", "apps"])

# Convert .dot to .png using Graphviz
if Path("classes_CFITP.dot").exists():
    subprocess.run(["dot", "-Tpng", "classes_CFITP.dot", "-o", str(DOCS_DIR / "classes_CFITP.png")])
if Path("packages_CFITP.dot").exists():
    subprocess.run(["dot", "-Tpng", "packages_CFITP.dot", "-o", str(DOCS_DIR / "packages_CFITP.png")])

# Clean up .dot files
for file in BASE_DIR.glob("*.dot"):
    file.unlink()

print("\n All diagrams generated and saved in docs/diagrams/")
print(" You can now commit them to GitHub!")
