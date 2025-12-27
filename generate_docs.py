import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs" / "diagrams"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

CORE_APPS = [
    "users",
    "feedback",
    "issues",
    "notifications",
    "comments",
    "attachments",
]

print("Generating CFITP diagrams...")

# 1. ER / Model Diagram (Django Extensions)
subprocess.run([
    "python", "manage.py", "graph_models",
    *CORE_APPS,
    "--disable-abstract-fields",
    "--hide-edge-labels",
    "-o", str(DOCS_DIR / "cfitp_models.png")
])

# 2. Class Diagram (per app – clean)
for app in CORE_APPS:
    subprocess.run([
        "pyreverse",
        "-o", "png",
        "-p", f"CFITP_{app}",
        f"apps/{app}"
    ])

print("Done! Diagrams saved in docs/diagrams/")
