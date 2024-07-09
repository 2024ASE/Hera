from collections import defaultdict
import json
import graphviz

def visualize_dependency_tree(dependency_tree):
    dot = graphviz.Digraph(comment='Dependency Tree')
    for package, deps in dependency_tree.items():
        dot.node(package, package)
        for dep in deps:
            dot.node(dep, dep)
            dot.edge(package, dep)
    return dot

def process_dependency_file(file_path):
    """
    Process a dependency file to extract dependency relationships.
    """
    with open(file_path, 'r') as file:
        dependencies = []
        for line in file:
            clean_line = line.strip().rstrip(',')
            if clean_line:
                dependencies.append(clean_line)
        return dependencies

def parse_dependencies(dependency_str_list):
    """
    Parse the list of dependency strings into a graph.
    """
    graph = defaultdict(set)
    for dep_str in dependency_str_list:
        package, deps = dep_str.split(':')
        package = "python3-" + package
        deps = deps.split(',') if deps else []
        graph[package].update(deps)
    return graph

def save_simplify_dependencies(simplified_deps):
    json_compatible_dict = {k: list(v) for k, v in simplified_deps.items()}
    json_string = json.dumps(json_compatible_dict, indent=4)
    file_path = 'path_to_file.json'  # Change this path as necessary
    with open(file_path, 'w') as file:
        file.write(json_string)
    print("Dependencies saved successfully")

def simplify_dependencies(dependency_graph):
    """
    Simplify the dependency graph by removing indirect dependencies.
    """
    def remove_indirect_deps(package, seen):
        for dep in list(dependency_graph[package]):
            if dep in seen:
                continue
            seen.add(dep)
            dependency_graph[package] -= dependency_graph[dep]
            remove_indirect_deps(dep, seen)
            seen.remove(dep)

    for package in list(dependency_graph.keys()):
        remove_indirect_deps(package, set())
    return dependency_graph

def get_compatibility_pairs(simplified_graph):
    """
    Generate the pairs of packages that need to be checked for compatibility.
    """
    pairs = []
    for package, deps in simplified_graph.items():
        for dep in deps:
            pairs.append((package, dep))
    return pairs

def analyze_dependencies(dependency_str_list):
    """
    Analyze the given dependencies and return simplified dependencies and compatibility pairs.
    """
    dependency_graph = parse_dependencies(dependency_str_list)
    simplified_graph = simplify_dependencies(dependency_graph)
    compatibility_pairs = get_compatibility_pairs(simplified_graph)
    return simplified_graph, compatibility_pairs

# Example usage
process_dependency = process_dependency_file("path_to_dependency_file.txt")
simplified_deps, compatibility_pairs = analyze_dependencies(process_dependency)

print(simplified_deps, compatibility_pairs)
print(len(compatibility_pairs))
save_simplify_dependencies(simplified_deps)
