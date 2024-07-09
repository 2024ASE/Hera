from pymongo import MongoClient
import json
import pickle
import pandas as pd

def find_version_order(package_name, apt_version, pip_version):
    real_package_name = get_real_package_name(package_name)
    txt_file_path = "~/versions/" + str(real_package_name)+".txt"
    with open(txt_file_path, 'r') as file:
        lines = file.readlines()
    line_numbers = {}
    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if line == apt_version or line == pip_version:
            line_numbers[line] = idx

    if apt_version in line_numbers and pip_version in line_numbers:
        if line_numbers[apt_version] < line_numbers[pip_version]:
            #print(f"{apt_version} comes before {pip_version}")
            return True
        else:
            #print(f"{pip_version} comes before {apt_version}")
            return False
    else:
        print("One or both of the provided data not found in the file.")
        return True

def create_dotless_dict():
    lst = pd.read_excel("~/package_info_new_all.xlsx")["Package Name"]
    dotless_dict = {}
    for s in lst:
        s_str = str(s)
        if '.' in s_str:
            dotless_key = s_str.replace('.', '')
            dotless_dict[dotless_key] = s_str
    return dotless_dict

def get_real_package_name(target):
    global dotless_dict
    target = target.replace("_", "-")
    if target in dotless_dict:
        matching_string = dotless_dict.get(target, None)
        # print(f"Package Name: {package_name}, Version: {version}")
        return matching_string
    else:
        return target
    
def get_apt_version(package_name):
    package_name = get_real_package_name(package_name)
    # 读取Excel文件
    df = pd.read_excel("~/package_info_new_all.xlsx")

    package_version_dict = dict(zip(df["Package Name"], df["Version"]))
    if package_name in package_version_dict:
        version = package_version_dict[package_name]
        # print(f"Package Name: {package_name}, Version: {version}")
        return version
    else:
        print(f"Package '{package_name}' not found in the dictionary.")
        return ""


def get_col_name(dep,dep_info):
    col_name = ''
    apt_version = get_apt_version(dep.replace('python3-', ''))
    pip_version = dep_info.get('pip_versions')[-1]
    if find_version_order(str(dep.replace('python3-', '').replace('.', '')), apt_version, pip_version):
        col_name = (str(dep.replace('python3-', '').replace('.', '').replace('-', '_')) + str(apt_version) + "VS" + str(pip_version))
    else:
        col_name = (str(dep.replace('python3-', '').replace('.', '').replace('-', '_')) + str(pip_version) + "VS" + str(apt_version))
    return col_name

def construct_combination():
    with open("~/dependency_graph_new_new.pkl", "rb") as file:
        dependency_graph = pickle.load(file)
    '''
    for name in dependency_graph.nodes():
        node =  dependency_graph.nodes[name]
        if node.get("pip_info") and len(node.get("pip_versions")) == 0:
            print(name)
    return 
    '''
    count = 0 
    dep_set = set()
    data_set = set()
    with open("~/all.txt", "r") as file:
        for line in file:
            line = str(line.strip())
            direct_dependencies = list(dependency_graph.successors(str(line)))
            if len(direct_dependencies) > 0 and direct_dependencies[0] != '':
                dep_count = 0
                for dep in dependency_graph.successors(line):
                    if dep != '':
                        if dep in dep_set:
                            continue
                        dep_info = dependency_graph.nodes[dep]
                        if dep_info.get('pip_info', False):
                            dep_set.add(dep)
                            dep_count += 1
                            count += 1
                            col_name = get_col_name(dep,dep_info)
                            # print((dep,col_name))
                            data_set.add((dep,col_name))                       
    print(count)
    print(len(data_set))
    print(len(dep_set))
    with open("~/need_json.txt", 'w') as file:
        for item in data_set:
            file.write(f"{item}\n")
    return data_set

def copy_collection_to_new_db(client, target_client, source_db_name, source_collection_name, target_db_name):

    try:
        if source_db_name not in client.list_database_names():
            raise ValueError(source_db_name,source_collection_name)
        source_db = client[source_db_name]

        if source_collection_name not in source_db.list_collection_names():
            raise ValueError(source_db_name,source_collection_name)
        source_collection = source_db[source_collection_name]

        with open('~/success.txt', 'a') as success_file:
            success_file.write(f"{str((source_db_name,source_collection_name))}\n")

        target_db = target_client[target_db_name]
        target_collection = target_db[source_collection_name]
        for document in source_collection.find():
            target_collection.insert_one(document)

    except ValueError as e:
        with open('~/error.txt', 'a') as error_file:
            error_file.write(f"{str(e)}\n")

def export_collections_to_json(client, db_name, export_path):
    db = client[db_name]

    collection_names = db.list_collection_names()
    
    for collection_name in collection_names:

        collection = db[collection_name]
        documents = list(collection.find())

        json_data = json.dumps(documents, default=str)  # default=str
        with open(f"{export_path}/{collection_name}.json", "w") as file:
            file.write(json_data)

# 使用示例
mongo_uri = 'mongodb://192.168.3.1:27017'
target_mongo_url = 'mongodb://localhost:27017'
client = MongoClient(mongo_uri)
target_client = MongoClient(target_mongo_url)
target_db_name = 'need_json'
dotless_dict = {}
dotless_dict = create_dotless_dict()
data_set = construct_combination()
for data in data_set:
    source_db_name = data[0].replace('python3-', '').replace('.', '').replace('-', '_')+"_API"
    source_collection_name = data[1]
    copy_collection_to_new_db(client, target_client, source_db_name, source_collection_name, target_db_name)
construct_combination()
