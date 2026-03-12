import os
import subprocess
from langgraph.graph import Graph, Node
from langgraph.context import Context

# Función para ejecutar comandos del sistema
def run_command(command):
    """Ejecuta un comando en la terminal y maneja errores."""
    try:
        subprocess.run(command, check=True, shell=True)
        return "Comando ejecutado correctamente."
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando el comando: {e}"

# Nodo para clonar un repositorio de GitHub
def clone_repository(context, repo_url):
    """Clona un repositorio desde GitHub."""
    command = f"git clone {repo_url}"
    result = run_command(command)
    context["repo_path"] = repo_url.split('/')[-1].replace('.git', '')  # Extraer nombre del repo
    return result

# Nodo para analizar un repositorio
def analyze_repository(context):
    """Analiza un repositorio y detecta dependencias."""
    repo_path = context.get("repo_path")
    if not repo_path or not os.path.exists(repo_path):
        return "Repositorio no encontrado. Por favor clona el repositorio primero."

    dependencies = []
    files_to_check = [
        "package.json", "requirements.txt", "Dockerfile",
        "composer.json", "Gemfile", "Cargo.toml", "Makefile"
    ]
    
    # Analizar archivos clave
    for root, _, files in os.walk(repo_path):
        for file_name in files:
            if file_name in files_to_check:
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r') as f:
                    content = f.read()
                    if file_name == "package.json":
                        dependencies.append("Node.js dependencies found in package.json")
                    elif file_name == "requirements.txt":
                        dependencies.append("Python dependencies found in requirements.txt")
                    elif file_name == "Dockerfile":
                        dependencies.append("Docker instructions found in Dockerfile")
    
    context["dependencies"] = dependencies
    return f"Dependencias detectadas: {dependencies}"

# Nodo para instalar dependencias detectadas
def install_dependencies(context):
    """Instala las dependencias detectadas en el análisis del repositorio."""
    dependencies = context.get("dependencies", [])
    results = []
    for dependency in dependencies:
        if "Node.js" in dependency:
            results.append(run_command("sudo apt-get install --assume-yes nodejs npm"))
        elif "Python" in dependency:
            results.append(run_command("pip install -r requirements.txt"))
        elif "Docker" in dependency:
            results.append(run_command("sudo apt-get install --assume-yes docker.io"))
    return results

# Configuración del grafo
graph = Graph()

# Nodos del grafo
clone_node = Node(
    func=clone_repository,
    name="Clone Repository",
    inputs={"repo_url": str},
    outputs=["repo_path"],
    description="Clona un repositorio desde GitHub."
)
analyze_node = Node(
    func=analyze_repository,
    name="Analyze Repository",
    inputs=["repo_path"],
    outputs=["dependencies"],
    description="Analiza el repositorio para detectar dependencias."
)
install_node = Node(
    func=install_dependencies,
    name="Install Dependencies",
    inputs=["dependencies"],
    outputs=[],
    description="Instala las dependencias detectadas."
)

# Conectar nodos
graph.add_node(clone_node)
graph.add_node(analyze_node)
graph.add_node(install_node)

graph.connect(clone_node, analyze_node, {"repo_path": "repo_path"})
graph.connect(analyze_node, install_node, {"dependencies": "dependencies"})

# Ejecución del grafo
if __name__ == "__main__":
    context = Context()
    repo_url = "https://<USERNAME>:<TOKEN>@github.com/<USERNAME>/<REPO>.git"  # URL del repositorio
    context["repo_url"] = repo_url

    # Ejecutar el grafo
    graph.execute(context)

    # Mostrar resultados finales
    print("Resultado final del grafo:", context)
