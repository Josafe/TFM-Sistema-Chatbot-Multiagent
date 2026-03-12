from langgraph import Graph, Node
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import subprocess
import tempfile
import re
import json
from pathlib import Path

# Nodo 1: Clonar repositorio de GitHub
class CloneRepoNode(Node):
    def run(self, repo_url):
        self.log(f"Clonando repositorio: {repo_url}")
        with tempfile.TemporaryDirectory() as temp_dir:
            command = f"git clone {repo_url} {temp_dir}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"Error clonando el repositorio: {result.stderr}")
                return {"success": False, "error": result.stderr}
            self.log(f"Repositorio clonado en: {temp_dir}")
            return {"success": True, "repo_path": temp_dir}

# Nodo 2: Analizar los archivos del repositorio
class AnalyzeRepoNode(Node):
    def run(self, repo_path):
        self.log(f"Analizando el repositorio en: {repo_path}")
        dependencies = []
        files_to_check = [
            "package.json", "requirements.txt", "Dockerfile",
            "composer.json", "Gemfile", "Cargo.toml", "Makefile"
        ]
        
        # Analizar archivos clave
        for file_name in files_to_check:
            file_path = Path(repo_path) / file_name
            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read()
                    if file_name == "package.json":
                        dependencies.extend(self.analyze_package_json(content))
                    elif file_name == "requirements.txt":
                        dependencies.extend(self.analyze_requirements_txt(content))
                    elif file_name == "Dockerfile":
                        dependencies.extend(self.analyze_dockerfile(content))
                    elif file_name == "composer.json":
                        dependencies.extend(self.analyze_composer_json(content))
                    elif file_name == "Gemfile":
                        dependencies.extend(self.analyze_gemfile(content))
                    elif file_name == "Cargo.toml":
                        dependencies.extend(self.analyze_cargo_toml(content))
                    elif file_name == "Makefile":
                        dependencies.extend(self.analyze_makefile(content))
        
        # Analizar archivos de código
        code_files = list(Path(repo_path).rglob("*.*"))
        for file_path in code_files:
            if file_path.suffix in [".py", ".vue", ".js", ".html", ".css", ".java", ".cpp", ".rs"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    dependencies.extend(self.analyze_code_file(file_path.suffix, content))
        
        self.log(f"Dependencias encontradas: {dependencies}")
        return {"dependencies": dependencies}
    
    # Funciones de análisis
    def analyze_package_json(self, content):
        try:
            data = json.loads(content)
            return [f"npm install {dep}" for dep in data.get("dependencies", {})]
        except json.JSONDecodeError:
            return ["Error analizando package.json"]

    def analyze_requirements_txt(self, content):
        return [f"pip install {line.strip()}" for line in content.splitlines() if line.strip()]

    def analyze_dockerfile(self, content):
        return [line.replace("RUN", "").strip() for line in content.splitlines() if line.startswith("RUN")]

    def analyze_composer_json(self, content):
        try:
            data = json.loads(content)
            return [f"composer require {dep}" for dep in data.get("require", {})]
        except json.JSONDecodeError:
            return ["Error analizando composer.json"]

    def analyze_gemfile(self, content):
        return [f"gem install {gem}" for gem in re.findall(r'gem\s+["\'](.*?)["\']', content)]

    def analyze_cargo_toml(self, content):
        return [f"cargo add {dep}" for dep in re.findall(r'^\s*([\w-]+)\s*=', content, re.MULTILINE)]

    def analyze_makefile(self, content):
        return re.findall(r'(install:.*?)\n', content, re.DOTALL)

    def analyze_code_file(self, file_type, content):
        dependencies = []
        if file_type == ".py":
            imports = re.findall(r'(?:import|from)\s+([a-zA-Z0-9_]+)', content)
            dependencies.extend([f"pip install {imp}" for imp in imports])
        elif file_type == ".vue" or file_type == ".js":
            imports = re.findall(r'import\s+.*\s+from\s+[\'"](.*?)[\'"]', content)
            dependencies.extend(imports)
        elif file_type == ".html":
            scripts = re.findall(r'<script\s+.*src=["\'](.*?)["\']', content)
            links = re.findall(r'<link\s+.*href=["\'](.*?)["\']', content)
            dependencies.extend(scripts + links)
        elif file_type == ".css":
            imports = re.findall(r'@import\s+[\'"](.*?)[\'"]', content)
            dependencies.extend(imports)
        return dependencies

# Nodo 3: Generar informe con LangChain LLM
class GenerateReportNode(Node):
    def run(self, dependencies):
        self.log(f"Generando informe para las dependencias: {dependencies}")
        
        llm = OpenAI(model="text-davinci-003", temperature=0.7)
        prompt = PromptTemplate(
            input_variables=["dependencies"],
            template="""
Eres un asistente técnico que genera informes claros y detallados sobre las dependencias de un proyecto.
Aquí tienes la lista de comandos, bibliotecas y herramientas necesarias para configurar el proyecto:

{dependencies}

Genera un informe claro y profesional basado en esta lista.
"""
        )
        chain = LLMChain(prompt=prompt, llm=llm)
        report = chain.run(dependencies="\n".join(dependencies))
        return {"report": report}

# Crear el grafo
graph = Graph([
    CloneRepoNode("Clonar Repositorio"),
    AnalyzeRepoNode("Analizar Repositorio"),
    GenerateReportNode("Generar Informe")
])

# Conectar los nodos
graph.connect("Clonar Repositorio", "Analizar Repositorio", output_key="repo_path")
graph.connect("Analizar Repositorio", "Generar Informe", output_key="dependencies")

# Ejecutar el grafo
if __name__ == "__main__":
    repo_url = "https://github.com/usuario/repo.git"  # Reemplaza con tu URL
    result = graph.run({"repo_url": repo_url})
    print("\n--- Informe del Repositorio ---")
    print(result["Generar Informe"]["report"])

# Nodo 1: Detección de tecnologías y frameworks
class DetectTechnologiesNode(Node):
    def run(self, repo_path):
        self.log(f"Detectando tecnologías en: {repo_path}")
        detected_technologies = []
        
        # Archivos de configuración a analizar
        tech_files = {
            "package.json": "Node.js",
            "requirements.txt": "Python",
            "Dockerfile": "Docker",
            "composer.json": "PHP",
            "Gemfile": "Ruby",
            "Cargo.toml": "Rust",
            "Makefile": "Make",
            "pom.xml": "Java (Maven)",
            "build.gradle": "Java (Gradle)",
            ".env": "Configuraciones de entorno",
            "config.yaml": "Configuración YAML"
        }
        
        for file_name, tech in tech_files.items():
            if Path(repo_path, file_name).exists():
                detected_technologies.append(tech)
                
        # Frameworks populares
        framework_patterns = {
            "django": "Django",
            "flask": "Flask",
            "express": "Express.js",
            "angular": "Angular",
            "react": "React",
            "vue": "Vue.js",
            "spring": "Spring Boot",
            "laravel": "Laravel"
        }
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = Path(root, file)
                if file_path.suffix in [".py", ".js", ".java", ".php"]:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        for pattern, framework in framework_patterns.items():
                            if pattern in content and framework not in detected_technologies:
                                detected_technologies.append(framework)
        
        self.log(f"Tecnologías detectadas: {detected_technologies}")
        return {"technologies": detected_technologies}

# Nodo 2: Análisis del historial del repositorio
def run_git_command(repo_path, command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=repo_path)
    return result.stdout.strip()

class AnalyzeRepoHistoryNode(Node):
    def run(self, repo_path):
        self.log(f"Analizando historial del repositorio en: {repo_path}")
        
        # Obtener los últimos 5 commits
        commits = run_git_command(repo_path, "git log --oneline -n 5").split("\n")
        
        # Obtener autores principales
        authors = run_git_command(repo_path, "git shortlog -sn").split("\n")[:5]
        
        # Verificar ramas huérfanas
        branches = run_git_command(repo_path, "git branch -r").split("\n")
        orphan_branches = [b.strip() for b in branches if "origin/" in b and not b.strip().endswith("master")]
        
        self.log(f"Últimos commits: {commits}")
        self.log(f"Autores principales: {authors}")
        self.log(f"Ramas huérfanas: {orphan_branches}")
        
        return {"commits": commits, "authors": authors, "orphan_branches": orphan_branches}
# Nodo 3: Análisis de arquitectura del proyecto
class AnalyzeArchitectureNode(Node):
    def run(self, repo_path):
        self.log(f"Analizando arquitectura en: {repo_path}")
        architecture_info = {}
        
        # Identificar estructura de carpetas
        folders = [f.name for f in Path(repo_path).iterdir() if f.is_dir()]
        
        # Detectar estructura basada en carpetas comunes
        if "src" in folders or "app" in folders:
            architecture_info["pattern"] = "Posible arquitectura MVC o modular"
        if "services" in folders and "models" in folders:
            architecture_info["pattern"] = "Posible arquitectura basada en servicios"
        
        self.log(f"Estructura de carpetas: {folders}")
        self.log(f"Patrón detectado: {architecture_info.get('pattern', 'Desconocido')}")
        
        return {"architecture": architecture_info}

# Nodo 4: Generación de informe
class GenerateProjectSummaryNode(Node):
    def run(self, technologies, commits, authors, orphan_branches, architecture):
        self.log("Generando informe del proyecto")
        summary = {
            "Technologies": technologies,
            "Last Commits": commits,
            "Top Authors": authors,
            "Orphan Branches": orphan_branches,
            "Architecture": architecture
        }
        
        return {"report": json.dumps(summary, indent=4)}