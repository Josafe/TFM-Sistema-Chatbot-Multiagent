from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import os
from pathlib import Path
from langgraph.graph import StateGraph
from typing import List, TypedDict
from collections import defaultdict
import shutil
import re

# -------------------------------
# 🔧 CONFIGURACIÓ DEL GRAF
# -------------------------------
class InstallEnvState(TypedDict):
    repo_url: str
    repo_path: str
    dependencies: dict

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
        return "✅ Comanda executada correctament."
    except subprocess.CalledProcessError as e:
        return f"❌ Error executant la comanda: {e}"

def clone_repository(state: InstallEnvState) -> dict:
    allowed_repo = "https://github.com/Josafe/AI.git"
    repo_url = state["repo_url"]

    if repo_url != allowed_repo:
        return {"repo_path": "", "error": "❌ No tens permís per clonar aquest repositori."}

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    target_path = os.path.join("repos", repo_name)
    os.makedirs("repos", exist_ok=True)

    if os.path.exists(target_path):
        return {"repo_path": target_path}

    run_command(f"git clone {repo_url} {target_path}")
    return {"repo_path": target_path}

def analyze_repository(state: InstallEnvState) -> dict:
    repo_path = state["repo_path"]
    if not repo_path or not os.path.exists(repo_path):
        return {"dependencies": {"Errors": ["❌ Repositori no trobat."]}}

    language_patterns = {
        "Python": [r"\.py$", r"import\s", r"from\s.*\simport"],
        "JavaScript": [r"\.js$", r"require\(", r"import\s"],
        "TypeScript": [r"\.ts$", r"import\s"],
        "HTML": [r"\.html?$"],
        "CSS": [r"\.css$"],
        "PHP": [r"\.php$", r"<\?php"],
        "Rust": [r"\.rs$", r"extern\scrate"],
        "Ruby": [r"\.rb$", r"require\s", r"class\s"],
        "Go": [r"\.go$", r"package\s"],
        "Docker": [r"Dockerfile"],
        "Dart": [r"\.dart$"],
        "Jupyter": [r"\.ipynb$"],
    }

    tech_signatures = {
        "Vue.js": [r"vue", r"import\s+Vue"],
        "React": [r"react", r"import\s+React"],
        "Next.js": [r"next", r"getServerSideProps"],
        "Nuxt.js": [r"nuxt", r"@nuxtjs"],
        "Angular": [r"@angular"],
        "Svelte": [r"svelte"],
        "TailwindCSS": [r"tailwind", r"@tailwind"],
        "Bootstrap": [r"bootstrap"],
        "Torch": [r"import\s+torch"],
        "TensorFlow": [r"import\s+tensorflow"],
        "Scikit-learn": [r"import\s+sklearn"],
        "Flask": [r"from\s+flask\s+import", r"import\s+flask"],
        "Django": [r"from\s+django", r"import\s+django"],
        "FastAPI": [r"from\s+fastapi", r"import\s+FastAPI"],
        "Flutter": [r"flutter", r"import\s+'package:flutter"],
    }

    detected = defaultdict(set)

    for root, _, files in os.walk(repo_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    for lang, patterns in language_patterns.items():
                        if any(re.search(pat, file_name) or re.search(pat, content) for pat in patterns):
                            detected["Languages"].add(lang)

                    for tech, patterns in tech_signatures.items():
                        if any(re.search(pat, content) for pat in patterns):
                            detected["Technologies"].add(tech)

            except Exception as e:
                detected["Errors"].add(f"Error llegint {file_name}: {e}")

    return {"dependencies": {k: list(v) for k, v in detected.items()}}

def install_dependencies(state: InstallEnvState) -> dict:
    dependencies = state.get("dependencies", {})
    resultats = []

    langs = dependencies.get("Languages", [])
    techs = dependencies.get("Technologies", [])

    for lang in langs:
        if lang == "Python":
            resultats.append(run_command("pip install -r requirements.txt"))
        elif lang in ["JavaScript", "TypeScript"]:
            resultats.append(run_command("npm install"))
        elif lang == "Docker":
            resultats.append(run_command("sudo apt-get install -y docker.io"))
        elif lang == "PHP":
            resultats.append(run_command("composer install"))
        elif lang == "Ruby":
            resultats.append(run_command("bundle install"))
        elif lang == "Rust":
            resultats.append(run_command("cargo build"))
        elif lang == "Go":
            resultats.append(run_command("go mod tidy && go build"))
        elif lang == "Dart":
            resultats.append(run_command("flutter pub get"))

    for tech in techs:
        if tech in ["Vue.js", "React", "Next.js", "Nuxt.js"]:
            resultats.append(run_command("npm run build"))
        elif tech in ["TailwindCSS", "Bootstrap"]:
            resultats.append("ℹ️ Detectada llibreria CSS: No cal instal·lació específica.")
        elif tech == "Torch":
            resultats.append(run_command("pip install torch"))
        elif tech == "TensorFlow":
            resultats.append(run_command("pip install tensorflow"))
        elif tech == "Scikit-learn":
            resultats.append(run_command("pip install scikit-learn"))
        elif tech == "Flask":
            resultats.append(run_command("pip install flask"))
        elif tech == "Django":
            resultats.append(run_command("pip install django"))
        elif tech == "FastAPI":
            resultats.append(run_command("pip install fastapi uvicorn"))
        elif tech == "Flutter":
            resultats.append(run_command("flutter pub get"))

    return {"resultats": resultats}

# -------------------------------
# 🔄 GRAF DE LLANGCHAIN
# -------------------------------
builder = StateGraph(InstallEnvState)

builder.add_node("Clone Repository", clone_repository)
builder.add_node("Analyze Repository", analyze_repository)
builder.add_node("Install Dependencies", install_dependencies)
builder.add_node("Final", lambda state: state)  # 🔚

builder.set_entry_point("Clone Repository")
builder.add_edge("Clone Repository", "Analyze Repository")
builder.add_edge("Analyze Repository", "Install Dependencies")
builder.add_edge("Install Dependencies", "Final")

graph = builder.compile()

# -------------------------------
# 🌐 API FLASK
# -------------------------------
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "http://localhost:5173"}})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip().lower()

    if not message:
        return jsonify({"error": "Missatge buit"}), 400

    print(f"📩 Rebut: {message}")

    repo_url = "https://github.com/Josafe/AI.git"
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = Path("repos") / repo_name

    state = {
        "repo_url": repo_url,
        "repo_path": str(repo_path),
        "dependencies": {},
    }

    response_parts = []

    # Cas: CLONA
    if "clona" in message:
        if repo_path.exists():
            shutil.rmtree(repo_path)
        graph.invoke(state, config={"recursion_limit": 10})
        response_parts.append("📁 Repositori clonat correctament.")

    # Cas: ANALITZA
    elif "analitza" in message:
        if not repo_path.exists():
            response_parts.append("❌ El repositori no està clonat. Escriu 'clona' primer.")
        else:
            output = graph.invoke(state, config={"recursion_limit": 10})
            deps_dict = output.get("dependencies", {})
            if deps_dict:
                formatted = ""
                for section, items in deps_dict.items():
                    formatted += f"\n🔹 {section}:\n" + "\n".join([f"• {item}" for item in items]) + "\n"
                response_parts.append(f"🔍 Dependències detectades:{formatted.strip()}")
            else:
                response_parts.append("ℹ️ No s'han detectat dependències.")

    # Cas: INSTAL·LA
    elif "instal·la" in message:
        if not repo_path.exists():
            response_parts.append("❌ El repositori no està clonat.")
        else:
            output = graph.invoke(state, config={"recursion_limit": 10})
            results = output.get("resultats", [])
            if results:
                response_parts.append(f"⚙️ Resultats instal·lació:\n" + "\n".join(results))
            else:
                response_parts.append("ℹ️ No hi ha dependències a instal·lar.")

    else:
        response_parts.append("❓ Comanda no reconeguda. Prova amb 'clona', 'analitza' o 'instal·la'.")

    return jsonify({"response": "\n\n".join(response_parts)})

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
