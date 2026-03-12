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
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# -------------------------------------------
# 🔧 MODEL D'INTEL·LIGÈNCIA ARTIFICIAL
# -------------------------------------------
#model_name = "tiiuae/falcon-rw-1b"
model_name = "tiiuae/falcon-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype=torch.float16, trust_remote_code=True)

chat_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)

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

# def conversacio_falcon(user_input, max_tokens=100):
#     system_prompt = f"""
# Context:
# - Aquesta aplicació utilitza agents per automatitzar tasques sobre repositoris de programari.
# - L'objectiu és clonar repositoris, analitzar el codi, identificar tecnologies i instal·lar dependències.
  
#   You are an assistant that helps clone, analyze, and manage GitHub repositories, installing relevant technologies based on the languages used in the repository.
#   You can understand both Catalan and English. Users may ask things like 'clone this repository', 'install dependencies', or 'analyze the code', in either language.

#   Examples:
#   Catalan:
#   Usuari: Hola!
#   Assistència: Hola! En què et puc ajudar avui?

#   Usuari: Què pots fer?
#   Assistència: Puc ajudar-te a clonar, analitzar repositoris de GitHub i instal·lar les seves dependències.

#   English:
#   User: Hello!
#   Assistant: Hello! How can I help you today?

#   User: What can you do?
#   Assistant: I can help you clone GitHub repositories, analyze them, and install their dependencies.

#   Ets un assistent tècnic i científic. Respon amb claredat, precisió i to formal. Utilitza un llenguatge professional i evita expressions informals o extravagants, evita repetir el context. No repeteixis exemples anteriors, només respon a la pregunta actual de forma directa.

# Usuari: {user_input}
# Assistència:"""

#     prompt = f"{system_prompt}\nUsuari: {user_input}\nAssistència:"

#     response = chat_pipeline(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.3)
#     generated = response[0]["generated_text"]

#     print("🧠 Resposta completa del model:", generated)

#     match = re.search(r"Assistència:\s*(.*)", generated, re.DOTALL)
#     resposta_neta = match.group(1).strip() if match else generated.strip()

#     if not resposta_neta:
#         return "❓ Comanda no reconeguda. Prova amb 'clona', 'analitza' o 'instal·la'."
#     return resposta_neta

def conversacio_falcon(user_input, max_tokens=100):
    context = (
        "You are a technical assistant that helps clone, analyze, and manage GitHub repositories. "
        "You understand Catalan and English. Respond clearly and professionally, without repeating context or including examples."
    )

    prompt = f"{context}\n\nUser: {user_input}\nAssistant:"
    response = chat_pipeline(
        prompt,
        max_new_tokens=max_tokens,
        do_sample=True,
        temperature=0.3,
        top_p=0.9,
    )

    generated = response[0]["generated_text"]
    print("🧠 Resposta completa del model:", generated)

    resposta_neta = generated.split("Assistant:")[-1].strip()
    return resposta_neta if resposta_neta else "❓ Comanda no reconeguda."

def gestor_chat(user_input):
    comanda = detectar_comanda(user_input)

    if comanda == "clona":
        return clone_repository(user_input)
    elif comanda == "analitza":
        return analyze_repository(user_input)
    elif comanda == "instal·la":
        return install_dependencies(user_input)
    else:
        return conversacio_falcon(user_input)

    
def extract_github_url(text: str) -> str:
    match = re.search(r"https?://github\.com/[^\s/]+/[^\s/]+", text)
    return match.group(0) if match else ""

def detectar_comanda(entrada: str) -> str:
    entrada = entrada.lower()

    ordres_clona = [
        "clona", "clone", "vull clonar", "pots clonar", "fes un clon", "fes un clone",
        "clona aquest repositori", "download repo", "get repository"
    ]
    ordres_analitza = [
        "analitza", "analyze", "pots analitzar", "vull una anàlisi", "analitza el codi",
        "analitza el repositori", "analyze this repo", "review the code"
    ]
    ordres_instal = [
        "instal·la", "instal", "install", "instal·lar", "fes la instal·lació",
        "pots instal·lar", "posa les dependències", "install the dependencies"
    ]

    for frase in ordres_clona:
        if frase in entrada:
            return "clona"
    for frase in ordres_analitza:
        if frase in entrada:
            return "analitza"
    for frase in ordres_instal:
        if frase in entrada:
            return "instal·la"
    return ""


def clone_repository(state: InstallEnvState) -> dict:
    repo_url = state["repo_url"]

    if not repo_url.startswith("https://github.com/"):
        return {"repo_path": "", "error": "❌ URL de repositori no vàlida."}

    if not re.match(r"^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+\.git$", repo_url):
        return {"repo_path": "", "error": "❌ URL del repositori no vàlida o no suportada."}

    repo_name = repo_url.split("/")[-2] + "_" + repo_url.split("/")[-1].replace(".git", "")
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
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Missatge buit"}), 400

    print(f"📩 Rebut: {message}")

    repo_url = extract_github_url(message)

    if not repo_url:
        repo_url = "https://github.com/Josafe/AI.git"

    if not repo_url:
        return jsonify({"error": "❌ No s'ha detectat cap URL del repositori."}), 400

    repo_name = repo_url.split("/")[-2] + "_" + repo_url.split("/")[-1].replace(".git", "")
    repo_path = Path("repos") / repo_name

    state = {
        "repo_url": repo_url,
        "repo_path": str(repo_path),
        "dependencies": {},
    }

    response_parts = []

    if "clona" in message.lower():
        if repo_path.exists() and repo_path.is_dir():
            shutil.rmtree(repo_path)
        result = clone_repository(state)
        if result.get("error"):
            response_parts.append(result["error"])
        else:
            response_parts.append(f"📁 Repositori clonat: {repo_url}")

    elif "analitza" in message.lower():
        if not repo_path.exists():
            response_parts.append("❌ El repositori no està clonat.")
        else:
            state["repo_path"] = str(repo_path)
            output = analyze_repository(state)
            deps = output.get("dependencies", {})
            if deps:
                response_parts.append("🔍 Dependències detectades:")
                for k, v in deps.items():
                    response_parts.append(f"🔹 {k}:\n" + "\n".join(f"• {x}" for x in v))
            else:
                response_parts.append("ℹ️ No s'han trobat dependències.")

    elif "instal·la" in message.lower():
        if not repo_path.exists():
            response_parts.append("❌ El repositori no està clonat.")
        else:
            analyzed = analyze_repository(state)
            state["dependencies"] = analyzed.get("dependencies", {})
            output = install_dependencies(state)
            resultats = output.get("resultats", [])
            response_parts.append("⚙️ Resultats instal·lació:")
            response_parts += resultats

    else:
        resposta = gestor_chat(message)
        response_parts.append(resposta)

    return jsonify({"response": "\n\n".join(response_parts)})


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
