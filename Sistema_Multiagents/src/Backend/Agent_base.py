import os
import subprocess
from typing import TypedDict, List
from langgraph.graph import StateGraph

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login

# --- Autenticació amb Hugging Face ---
HUGGINGFACE_API_KEY = "KEY PRIVADA ES VISUALITZARÀ A L'ARXIU ORIGINAL"
login(HUGGINGFACE_API_KEY)

# --- Carreguem el model de llenguatge ---
model_name = "tiiuae/falcon-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

chatbot = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device_map="auto",
    pad_token_id=tokenizer.eos_token_id
)

# -------------------------------
# 🔹 DEFINICIÓ DEL GRAF
# -------------------------------
class InstallEnvState(TypedDict):
    repo_url: str
    repo_path: str
    dependencies: List[str]

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
    if not os.path.exists(repo_path):
        return {"dependencies": ["❌ Repositori no trobat."]}

    dependencies = []
    for root, _, files in os.walk(repo_path):
        for file_name in files:
            if file_name == "package.json":
                dependencies.append("Node.js")
            elif file_name == "requirements.txt":
                dependencies.append("Python")
            elif file_name == "Dockerfile":
                dependencies.append("Docker")
    return {"dependencies": dependencies}

def install_dependencies(state: InstallEnvState) -> dict:
    dependencies = state["dependencies"]
    resultats = []

    for dep in dependencies:
        if "Node.js" in dep:
            resultats.append(run_command("sudo apt-get install -y nodejs npm"))
        elif "Python" in dep:
            resultats.append(run_command("pip install -r requirements.txt"))
        elif "Docker" in dep:
            resultats.append(run_command("sudo apt-get install -y docker.io"))

    return {}

builder = StateGraph(InstallEnvState)
builder.add_node("Clone Repository", clone_repository)
builder.add_node("Analyze Repository", analyze_repository)
builder.add_node("Install Dependencies", install_dependencies)
builder.set_entry_point("Clone Repository")
builder.add_edge("Clone Repository", "Analyze Repository")
builder.add_edge("Analyze Repository", "Install Dependencies")
graph = builder.compile()

# -------------------------------
# 🧠 FUNCIONS DE CHATBOT
# -------------------------------
def handle_action(user_input):
    if user_input.startswith("instalar "):
        programa = user_input.split(" ", 1)[1]
        return run_command(f"sudo apt-get install -y {programa}")
    elif user_input.startswith("clonar "):
        url = user_input.split(" ", 1)[1]
        result = graph.invoke({
            "repo_url": url,
            "repo_path": "",
            "dependencies": []
        })
        return f"📦 Instal·lació completa. Resultat: {result}"
    else:
        return None

def get_huggingface_response(user_input):
    print(f"🗣️ Enviant al model: {user_input}")
    resposta = chatbot(user_input, max_length=200, do_sample=True, temperature=0.2, truncation=True)
    return resposta[0]['generated_text']

# -------------------------------
# 🧪 LOOP PRINCIPAL
# -------------------------------
if __name__ == "__main__":
    print("🤖 Agent orquestrador amb suport de llenguatge natural.\nEscriu 'sortir' per acabar.\n")

    while True:
        user_input = input("TU > ").strip()
        if user_input.lower() == "sortir":
            print("AGENT > Fins aviat 👋")
            break

        action_result = handle_action(user_input)
        if action_result:
            print(f"AGENT (acció) > {action_result}")
        else:
            response = get_huggingface_response(user_input)
            print(f"AGENT (LLM) > {response[len(user_input):].strip()}")


# import os
# import subprocess
# from typing import TypedDict, List
# from langgraph.graph import StateGraph

# # 🧾 Estat tipat per a LangGraph
# class InstallEnvState(TypedDict):
#     repo_url: str
#     repo_path: str
#     dependencies: List[str]

# # 🔧 Execució de comandes del sistema
# def run_command(command):
#     try:
#         subprocess.run(command, check=True, shell=True)
#         return "✅ Comanda executada correctament."
#     except subprocess.CalledProcessError as e:
#         return f"❌ Error executant la comanda: {e}"

# # 🔹 Node 1: Clonar repositori
# def clone_repository(state: InstallEnvState) -> dict:
#     allowed_repo = "https://github.com/Josafe/AI.git"
#     repo_url = state["repo_url"]

#     if repo_url != allowed_repo:
#         return {"repo_path": "", "error": "❌ No tens permís per clonar aquest repositori."}

#     repo_name = repo_url.split("/")[-1].replace(".git", "")
#     target_path = os.path.join("repos", repo_name)
#     os.makedirs("repos", exist_ok=True)

#     if os.path.exists(target_path):
#         return {"repo_path": target_path}

#     run_command(f"git clone {repo_url} {target_path}")
#     return {"repo_path": target_path}

# # 🔹 Node 2: Analitzar dependències
# def analyze_repository(state: InstallEnvState) -> dict:
#     repo_path = state["repo_path"]
#     if not os.path.exists(repo_path):
#         return {"dependencies": ["❌ Repositori no trobat."]}

#     dependencies = []
#     for root, _, files in os.walk(repo_path):
#         for file_name in files:
#             if file_name == "package.json":
#                 dependencies.append("Node.js")
#             elif file_name == "requirements.txt":
#                 dependencies.append("Python")
#             elif file_name == "Dockerfile":
#                 dependencies.append("Docker")
#     return {"dependencies": dependencies}

# # 🔹 Node 3: Instal·lar dependències
# def install_dependencies(state: InstallEnvState) -> dict:
#     dependencies = state["dependencies"]
#     resultats = []

#     for dep in dependencies:
#         if "Node.js" in dep:
#             resultats.append(run_command("sudo apt-get install -y nodejs npm"))
#         elif "Python" in dep:
#             resultats.append(run_command("pip install -r requirements.txt"))
#         elif "Docker" in dep:
#             resultats.append(run_command("sudo apt-get install -y docker.io"))

#     return {}

# # ✅ Construcció del graf
# builder = StateGraph(InstallEnvState)

# # Afegir els nodes de forma explícita
# builder.add_node("Clone Repository", clone_repository)
# builder.add_node("Analyze Repository", analyze_repository)
# builder.add_node("Install Dependencies", install_dependencies)

# # Definir l'ordre dels nodes
# builder.set_entry_point("Clone Repository")
# builder.add_edge("Clone Repository", "Analyze Repository")
# builder.add_edge("Analyze Repository", "Install Dependencies")

# # Compilar el graf
# graph = builder.compile()

# # 🧪 Execució del flux
# if __name__ == "__main__":
#     repo_url = "https://github.com/Josafe/AI.git"  # ⬅️ Substitueix amb un repo real
#     result = graph.invoke({
#         "repo_url": repo_url,
#         "repo_path": "",
#         "dependencies": []
#     })

#     print("\n✅ Resultat final:", result)
# ------------------------------------------------------------------------------------------
# import os
# import subprocess
# from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
# from huggingface_hub import login

# # Iniciar sesión en Hugging Face con tu API Key
# HUGGINGFACE_API_KEY = "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"
# login(HUGGINGFACE_API_KEY)

# # Elegir el modelo que vas a usar
# model_name = "tiiuae/falcon-7b-instruct"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# # Crear el pipeline de generación de texto
# chatbot = pipeline(
#     "text-generation",
#     model=model,
#     tokenizer=tokenizer,
#     device_map="auto",
#     pad_token_id=tokenizer.eos_token_id
# )

# # Ejecutar comandos en el sistema
# def run_command(command):
#     try:
#         subprocess.run(command, check=True, shell=True)
#         return "✅ Comando ejecutado correctamente."
#     except subprocess.CalledProcessError as e:
#         return f"❌ Error ejecutando el comando: {e}"

# # Manejo de acciones específicas
# def handle_action(user_input):
#     if user_input.startswith("instalar "):
#         programa = user_input.split(" ", 1)[1]
#         return run_command(f"sudo apt-get install -y {programa}")
#     elif user_input.startswith("clonar "):
#         url = user_input.split(" ", 1)[1]
#         return run_command(f"git clone {url}")
#     else:
#         return None

# # Obtener respuesta del modelo
# def get_huggingface_response(user_input):
#     print(f"Enviando al modelo: {user_input}")
#     respuesta = chatbot(user_input, max_length=200, do_sample=True, temperature=0.2, truncation=True)
#     return respuesta[0]['generated_text']

# # Main loop
# if __name__ == "__main__":
#     print("🤖 Bienvenido al agente conversacional. Escribe 'salir' para terminar.\n")

#     while True:
#         user_input = input("Tú: ").strip()
#         if user_input.lower() == "salir":
#             print("Agente: ¡Hasta luego!")
#             break

#         action_result = handle_action(user_input)
#         if action_result:
#             print(f"Agente (acción): {action_result}")
#         else:
#             response = get_huggingface_response(user_input)
#             print(f"Agente: {response[len(user_input):].strip()}")
