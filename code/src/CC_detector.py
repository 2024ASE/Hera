from construct_PDG import construct_PDG, merge_graphs, load_graph_from_gpickle
from pymongo import MongoClient
import json

API_ADDITION = "api_addition"
API_REMOVAL = "api_removal"
PARAM_ADDITION = "param_addition"
PARAM_REMOVAL = "param_removal"
OPTIONAL_PARAM_ADDITION = "optional_param_addition"
OPTIONAL_PARAM_REMOVAL = "optional_param_removal"
PARAM_REORDEING = "param_reordering"
TYPE_MODIFIED = "type_modified"
PARAM_MODIFIED = "param_modified"
PARAM_OPTIONAL_MODIFIED = "param_optional_modified"


def check_PRN(api_usage, api_trans):
    return ((api_usage['api_name'] == api_trans['old_api']) and
            (api_usage['api_name'] == api_trans['new_api']) and
            ((api_trans['change_type'] == PARAM_ADDITION) or 
             (api_trans['change_type'] == PARAM_REMOVAL) or
             (api_trans['change_type'] == OPTIONAL_PARAM_REMOVAL) or
             (api_trans['change_type'] == PARAM_REORDEING)))


def check_ARR(api_usage, api_trans):
    return ((api_usage['api_name'] == api_trans['old_api']) or
            (api_usage['api_name'] == api_trans['new_api'])) and (api_trans['change_type'] == API_REMOVAL)

def check_ATR(api_usage, api_trans):
     return ((api_usage['api_name'] == api_trans['old_api']) and
            (api_usage['api_name'] == api_trans['new_api']) and 
            (api_trans['change_type'] == TYPE_MODIFIED)) 

def check_api_usage(api_usage, api_db):
    for api_trans in api_db:
        # TODO: change to DSL
        if check_ARR(api_usage, api_trans):
            return True
        if check_PRN(api_usage, api_trans):
            return True
        # if check_ATR(api_usage, api_trans):
        #     return True
    return False

def fetch_ic_api(covered_edges):
    
    client = MongoClient('localhost', 27017)  
    results = {}
    
    for edge in covered_edges:
        package = edge['package']
        pip_version = edge['pip_version']
        apt_version = edge['apt_version']
        db_name =f"{package}_API"
        collection_name = f"{package}{apt_version}VS{pip_version}"

        db = client[db_name] 
        collection = db[collection_name]
        incompatibilities = list(collection.find({}))

        if incompatibilities:
            results[package] = {
                'pip_version': pip_version,
                'apt_version': apt_version,
                'incompatibilities': incompatibilities
            }
        else:
            results[package] = f"{pip_version} and {apt_version} versions are compatible."

    return results

def fetch_api_usage(dependencies, db_name):
    
    client = MongoClient('localhost', 27017) 
    db = client[db_name]  

    api_usage_data = {}

    for dependency in dependencies:
        api_usage_data[dependency.key()] = []
        for pair in dependency.value():
            collection_name = f"{pair}USE{dependency.key()}"
            collection = db[collection_name]
            
            api_usages = list(collection.find({}))

            if api_usages:
                api_usage_data[dependency.key()].append({
                    "depended": pair,
                    "api_usage":api_usages}
                )
            else:
                print("No API usage data found")

    return api_usage_data

def find_dependencies_for_covered_edges(graph, covered_edges):
    dependencies_dict = {}

    for edge in covered_edges:
        package = edge['package']

        dependencies_dict[package] = []

        for u, v in graph.in_edges(package):
            dependencies_dict[package].append(u)

    return dependencies_dict

def generate_report(incompatible_api_usage, output_dir):
    with open(output_dir, 'w') as report_file:
        incompatible_api_usage = [x for x in incompatible_api_usage if x != []]
        json.dump(incompatible_api_usage, report_file)

if __name__ == '__main__':
    # pip_graph_path = '~/Desktop/online/Pip_PDG.gpickle'
    # apt_graph_path = '~/Desktop/online/Apt_PDG.gpickle'
    # pip_graph = load_graph_from_gpickle(pip_graph_path)
    # apt_graph = load_graph_from_gpickle(apt_graph_path)
    pip_graph, apt_graph = construct_PDG()
    merged_graph, covered_edges = merge_graphs(pip_graph, apt_graph)
    print(covered_edges)

    dependencies = find_dependencies_for_covered_edges(apt_graph,covered_edges)
    api_usage = fetch_api_usage(dependencies, "aptPackages")
    ic_api = fetch_ic_api(covered_edges)

    for package in api_usage.keys():
        for pair in api_usage[package]:
            incompatible_api_usage = list(
            filter(lambda api: check_api_usage(api, ic_api[package]), api_usage[package]["api_usage"]))
            generate_report(incompatible_api_usage, f"./CC_issue_{package}_with_{api_usage[package]["depended"]}")

    print("successfully detecting")

