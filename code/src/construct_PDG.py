import sys
import subprocess
import re
import networkx as nx
import matplotlib.pyplot as plt
import pickle
import json
import pkg_resources
import os
import pandas as pd

def get_python_import_path():
    import_path = sys.path
    return import_path


def get_apt_installed_packages():
    apt_packages = subprocess.check_output(
        ['dpkg', '-l', 'python3-*']).decode('utf-8')
    package_lines = apt_packages.strip().split('\n')[5:]  
    package_info = []
    print(len(package_lines))
    for line in package_lines:
        package_details = line.split()
        package_name = package_details[1]
        package_version = package_details[2]
        package_info.append((package_name, package_version))

    return package_info

def list_installed_python_packages(output_file):
    #command = ['dpkg-query', '-W', '-f=${binary:Package} ${Version}\n', 'python3-*']
    command = ['dpkg-query', '-W', '-f=${binary:Package}\n', 'python3-*']
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print("An error occurred while querying installed packages.")
        return
    
    with open(output_file, 'w') as file:
        for line in result.stdout.splitlines():
            package_name = line.replace('python3-', '')  # Remove the 'python3-' prefix
            file.write(package_name + '\n')
        
        #file.write(result.stdout)


def get_pip_installed_packages():
    pip_packages = subprocess.check_output(['pip', 'list']).decode('utf-8')
    package_lines = pip_packages.strip().split('\n')[2:]  
    package_info = []
    print(len(package_lines))
    for line in package_lines:
        package_name, package_version = re.findall(
            r'([\w.-]+)\s+([\w.-]+)', line)[0]
        package_info.append((package_name, package_version))

    return package_info

#pkg_resources
def get_packages_and_versions(directory):

    os.chdir(directory)
    
    distributions = pkg_resources.find_distributions(directory)
    
    packages_and_versions = {}
    
    for distribution in distributions:
        packages_and_versions[distribution.project_name] = distribution.version
    
    packages_and_versions = {k: packages_and_versions[k] for k in sorted(packages_and_versions)}
    return packages_and_versions


def get_common_package(apt_warehouse, pip_warehouse):
    common_packages = set(apt_warehouse) & set(pip_warehouse)
    return common_packages


def load_dependency_graph(file_name):
    with open(file_name, "rb") as file:
        loaded_graph = pickle.load(file)
    return loaded_graph


def construct_PDG():
    print(sys.path)
    
    pipDir = '~/.local/lib/python3.8/site-packages'
    aptDir = "/usr/lib/python3/dist-packages"
    pip_PDG = PipDependencyGraph(pipDir)
    pip_PDG.save_graph("gpickle","Pip_PDG")
    apt_PDG = AptDependencyGraph(aptDir,"~/Desktop/online/apt_intra_dependency_graph.pkl")
    apt_PDG.save_graph("gpickle","Apt_PDG")
    print("ok")
    return pip_PDG.get_PDG(), apt_PDG.get_PDG()  


def get_dependencies():
    try:
        # Run pipdeptree and get the output
        result = subprocess.run(["pipdeptree", "--json"], capture_output=True, text=True, check=True)
        # Parse the JSON output
        dependencies = json.loads(result.stdout)    # if dependencies is not None:
        for element in dependencies:
            package = element['package']
            package_name = package['key']
            package_dependencies = [dep['key'] for dep in element['dependencies']]
            if len(package_dependencies) == 0:
                continue
            print(f"{package_name} depends on: {', '.join(package_dependencies) if package_dependencies else 'None'}")
        return dependencies
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None

#

class DependencyGraph:
    def __init__(self, directory):
        self.directory = directory
        self.graph = nx.DiGraph()
        self.packages_and_versions = self.get_packages_and_versions()
        self.packages = self.get_packages()
        self.build_graph()
    
    def get_packages_and_versions(self):

        os.chdir(self.directory)
        
        distributions = pkg_resources.find_distributions(self.directory)

        packages_and_versions = {}
        
        for distribution in distributions:
            packages_and_versions[distribution.project_name] = distribution.version
        
        packages_and_versions = {k: packages_and_versions[k] for k in sorted(packages_and_versions)}
        return packages_and_versions

    def get_packages(self):

        packages = []
        flag = 0
        for package, version in self.packages_and_versions.items():
            # print(f'{package}: {version}')
            flag = flag + 1
            packages.append(package)
        print(flag)
        return packages

    def build_graph(self):

        raise NotImplementedError("This method should be overridden by subclasses.")
    
    def get_PDG(self):
        return self.graph

    def save_graph(self, format='graphml', filename='dependency_graph'):
        """
        Save the graph in various formats in the current directory.
        Available formats: graphml, json, gpickle, png
        """
        filepath = f"~/Desktop/online/{filename}"  # Prepends "./" to ensure it's in the current directory
        if format == 'graphml':
            nx.write_graphml(self.graph, f"{filepath}.graphml")
        elif format == 'json':
            data = nx.node_link_data(self.graph)
            with open(f"{filepath}.json", "w") as f:
                json.dump(data, f)
        elif format == 'gpickle':
            nx.write_gpickle(self.graph, f"{filepath}.gpickle")
        elif format == 'png':
            plt.figure(figsize=(12, 12))
            pos = nx.spring_layout(self.graph)
            nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', edge_color='#909090', node_size=500, font_size=10)
            plt.savefig(f"{filepath}.png")
            plt.show()
        else:
            print("Unsupported format")

class PipDependencyGraph(DependencyGraph):

    def get_package_info(self, package):

        result = subprocess.run(['pip', 'show', package], stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error: Unable to retrieve information for package {package}")
            return None, None

        dependencies = []
        version = None
        location = None
        for line in result.stdout.strip().split('\n'):
            if line.startswith('Requires: '):
                dependencies = [dep.strip() for dep in line[len('Requires: '):].split(',') if dep.strip()]
            if line.startswith('Version: '):
                version = line[len('Version: '):]
            if line.startswith('Location: '):
                location = line[len('Location: '):]

        if location != self.directory:
            return None, None  # Return None if location does not match

        return dependencies, version
    
    def add_nodes(self):

        flag = 0
        for package in self.packages:
            dependencies, version = self.get_package_info(package)
            print(flag)
            flag += 1
            if dependencies is not None:  # Only add node if the location matches
                self.graph.add_node(package, version=version, installation_method='pip', dependencies=dependencies)


    def add_edges(self):

        for node in self.graph.nodes:
            dependencies = self.graph.nodes[node].get('dependencies', [])
            if dependencies:
                for dep in dependencies:
                    if dep in self.graph.nodes:  # Only add edges to dependencies that are also in the packages list
                        self.graph.add_edge(node, dep)

    def build_graph(self):

        self.add_nodes()
        self.add_edges()

class AptDependencyGraph(DependencyGraph):
    def __init__(self, directory, dependency_graph_path='apt_intra_dependency_graph.pkl'):
        self.dependency_graph = self.load_dependency_graph(dependency_graph_path)
        self.normalized_packages = []
        super().__init__(directory)

    def parse_depends(self, depends_str):

        return [re.split(r' \(.*\)', dep)[0].strip() for dep in depends_str.split(', ')]
    
    def load_dependency_graph(self, path):
        """Load the pre-existing dependency graph from a pickle file."""
        with open(path, 'rb') as file:
            return pickle.load(file)
        
    def normalize_names(self, packages):
        """Normalize package names to match those in the dependency graph."""
        # Simple rule: prepend 'python3-' to package names. Adjust this based on actual naming conventions.
        return {pkg: f'python3-{pkg}' for pkg in packages}
    
    def get_apt_version(self,package_name):

        df = pd.read_excel("~/Desktop/online/package_info_new_all.xlsx")

        package_version_dict = dict(zip(df["Package Name"], df["Version"]))
        if package_name in package_version_dict:
            version = package_version_dict[package_name]
            # print(f"Package Name: {package_name}, Version: {version}")
            return version
        else:
            print(f"Package '{package_name}' not found in the dictionary.")
            return ""

    def get_package_info(self, package):
        self.normalized_packages = self.normalize_names(self.packages)
        normalized_package = self.normalized_packages[package]
        if normalized_package not in self.dependency_graph:
            print(f"Warning: Package {normalized_package} not found in the dependency graph.")
            return None, None, None
        intra_dependencies = list(self.dependency_graph.successors(normalized_package))
        dependencies = []
        version = self.get_apt_version(package)
        for dep in intra_dependencies:
            if dep in self.normalized_packages.values():
                dep = dep.replace("python3-",'')
                dependencies.append(dep)
        return dependencies, version, 'apt'
    
    def add_nodes(self):
        flag = 0
        for package in self.packages:
            package_info = self.get_package_info(package)
            flag += 1
            print(flag)
            if package_info:
                dependencies, version, installation_method = package_info
                # Add node with all necessary details
                self.graph.add_node(package, version=version, installation_method=installation_method, dependencies=dependencies)


    def add_edges(self):
        for node in self.graph.nodes:
            dependencies = self.graph.nodes[node].get('dependencies', [])
            if dependencies:
                for dep in dependencies:
                    if dep in self.graph.nodes:  # Only add edges to dependencies that are also in the packages list
                        self.graph.add_edge(node, dep)

    def build_graph(self):
        self.add_nodes()
        self.add_edges()

def merge_graphs(pip_graph, apt_graph):

    merged_graph = nx.compose(pip_graph, apt_graph)
    
    pip_nodes = set(pip_graph.nodes())
    apt_nodes = set(apt_graph.nodes())
    covered_edges = []
    for node in pip_nodes & apt_nodes:  
        if 'installation_method' in pip_graph.nodes[node] and pip_graph.nodes[node]['installation_method'] == 'pip':
            if 'installation_method' in apt_graph.nodes[node] and apt_graph.nodes[node]['installation_method'] == 'apt':
                merged_graph.add_edge(node, node, type='covered-edge')
                covered_edges.append({
                    'package': node,
                    'pip_version': pip_graph.nodes[node].get('version', 'unknown'),
                    'apt_version': apt_graph.nodes[node].get('version', 'unknown')
                })
    
    return merged_graph, covered_edges

def save_covered_edges_to_json(covered_edges, filename="~/Desktop/online/covered_edges.json"):
    with open(filename, 'w') as f:
        json.dump(covered_edges, f, indent=4)

def load_graph_from_gpickle(path):
    return nx.read_gpickle(path)

if __name__ == '__main__':
    pip_graph, apt_graph = construct_PDG()
    # pip_graph_path = '~/Desktop/online/Pip_PDG.gpickle'
    # apt_graph_path = '~/Desktop/online/Apt_PDG.gpickle'
    # pip_graph = load_graph_from_gpickle(pip_graph_path)
    # apt_graph = load_graph_from_gpickle(apt_graph_path)
    merged_graph, covered_edges = merge_graphs(pip_graph, apt_graph)
    save_covered_edges_to_json(covered_edges)
