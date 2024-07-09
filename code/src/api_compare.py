

import pymongo
import sys
import json
from enum import Enum
import pandas as pd
import openpyxl
import re

# Define API change patterns
class Pattern(Enum):
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

# Global list for tracking API changes
different_apis = []

# Function to connect to MongoDB
def connect(client, package_name, apt_version, pip_version_list):

    log_db = client.get_database("API_compare_new_new_log")
    col = log_db.get_collection("Failure_message")
    col1 = log_db.get_collection("Success_message")
    apt_flag = False
    if apt_version == '':
        log_handle(col, {
            "package": package_name,
            "apt_version": apt_version,
            "status": "failure",
            "message": "message Error"
        })
        return
    try:
        db = client.get_database(str(package_name) + "_API")
        apt_api = client.get_database("APT_API")
        collection_names = db.list_collection_names()
        apt_collections =  apt_api.list_collection_names()
    except Exception as e:
        log_handle(col, {
            "package": package_name,
            "apt_version": apt_version,
            "status": "failure",
            "message": "Database Connect Error"
        })

    try:
        if str(package_name) + "_APIs_" + str(apt_version) in collection_names:
            collection_apt = db[str(package_name) +
                                "_APIs_" + str(apt_version)]
        elif str(package_name) + "_APIs_" + str(apt_version) in apt_collections:
            collection_apt = apt_api[str(package_name) + "_APIs_" + str(apt_version)]
            apt_flag = True
        else:
            print("apt error")
            log_handle(col, {
                "package": package_name,
                "apt_version": apt_version,
                "status": "failure",
                "message": "No Apt Version"
            })
            return

    except Exception as e:
        return

    for pip_version in pip_version_list:
        if apt_version == pip_version:
            continue
        apt_version_data = collection_apt.find()
        try:
            if str(package_name) + "_APIs_" + str(pip_version) in collection_names:
                collection_pip = db[str(package_name) +
                                    "_APIs_" + str(pip_version)]
                pip_version_data = collection_pip.find()
                real_package_name = get_real_package_name(package_name)
                if find_version_order(
                        "F:\\PythonProject\\mongoDB\\versions\\" + str(real_package_name) + ".txt",
                        apt_version, pip_version, apt_flag):
                    message = compare(apt_version_data, pip_version_data)
                    if len(different_apis) > 0:
                        data_output_handler(
                            different_apis, (str(package_name) + str(apt_version) + "VS" + str(pip_version)), db)
                        log_handle(col1, {
                            "package": package_name,
                            "apt_version": apt_version,
                            "pip_version": pip_version,
                            "status": "successful",
                            "compatibility": False,
                            "common": message[0],
                            "difference": message[1],
                            "F_version_api": message[2],
                            "B_version_api": message[3]
                        })
                    else:
                        log_handle(col1, {
                            "package": package_name,
                            "apt_version": apt_version,
                            "pip_version": pip_version,
                            "status": "successful",
                            "compatibility": True,
                            "common": message[0],
                            "difference": message[1],
                            "F_version_api": message[2],
                            "B_version_api": message[3]
                        })
                else:

                    message = compare(pip_version_data, apt_version_data)
                    if len(different_apis) > 0:
                        data_output_handler(different_apis, (str(
                            package_name) + str(pip_version) + "VS" + str(apt_version)), db)
                        log_handle(col1, {
                            "package": package_name,
                            "apt_version": apt_version,
                            "pip_version": pip_version,
                            "status": "successful",
                            "compatibility": False,
                            "common": message[0],
                            "difference": message[1],
                            "F_version_api": message[2],
                            "B_version_api": message[3]
                        })
                    else:
                        log_handle(col1, {
                            "package": package_name,
                            "apt_version": apt_version,
                            "pip_version": pip_version,
                            "status": "successful",
                            "compatibility": True,
                            "common": message[0],
                            "difference": message[1],
                            "F_version_api": message[2],
                            "B_version_api": message[3]
                        })
            else:
                print("pip error")
                log_handle(col, {
                    "package": package_name,
                    "apt_version": apt_version,
                    "pip_version": pip_version,
                    "status": "failure",
                    "message": "No Pip Version"
                })

        except Exception as e:
            print(str(e))
            continue

    # version1_data = collection_apt.find()
    # version2_data = collection_pip.find()

    # return version1_data, version2_data

def log_handle(collection, data):
    # print(data)
    collection.insert_one(data)

def find_version_order(txt_file_path, apt_version, pip_version, apt_flag=False):
    if apt_flag:
        return True

    with open(txt_file_path, 'r') as file:
        lines = file.readlines()
    line_numbers = {}
    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if line == apt_version or line == pip_version:
            line_numbers[line] = idx

    if apt_version in line_numbers and pip_version in line_numbers:
        if line_numbers[apt_version] < line_numbers[pip_version]:
            # print(f"{apt_version} comes before {pip_version}")
            return True
        else:
            # print(f"{pip_version} comes before {apt_version}")
            return False
    else:

        return "One or both of the provided data not found in the file."


def get_apt_version(package_name):
    package_name = get_real_package_name(package_name)

    df = pd.read_excel("package_info_new_all.xlsx")

    package_version_dict = dict(zip(df["Package Name"], df["Version"]))
    if package_name in package_version_dict:
        version = package_version_dict[package_name]
        # print(f"Package Name: {package_name}, Version: {version}")
        return version
    else:
        print(f"Package '{package_name}' not found in the dictionary.")
        return ""

def save_parameter_changes(parameter_changes):
    for element in parameter_changes:
        different_apis.append(element)

def get_params_type(params):
    ne_params = {}
    op_params = {}
    for param_name, param in params.items():
        if not param.get('is_optional',False):
            ne_params[param_name] = param
        else:
            op_params[param_name] = param
    return ne_params,op_params

def compare_keys_order(dict1, dict2):

    keys_list1 = list(dict1.keys())
    keys_list2 = list(dict2.keys())
    

    set_equal = set(keys_list1) == set(keys_list2)
    

    list_equal = keys_list1 == keys_list2
    

    return set_equal and not list_equal

def data_output_handler(api_changes, collection_name, db):
    collection = db[collection_name]
    # collection.drop()
    collection.insert_many(api_changes)
    different_apis.clear()
    # with open(filename, 'w') as file:
    #     json.dump(parameter_changes, file, indent=4)


def compare(F_version_data, B_version_data):

    version1_apis = {api['_id']: api for api in F_version_data}
    version2_apis = {api['_id']: api for api in B_version_data}


    common_apis = set(version1_apis.keys()).intersection(
        set(version2_apis.keys()))



    version1_only_apis = []
    version2_only_apis = []


    for api_id in common_apis:
        api1 = version1_apis[api_id]
        api2 = version2_apis[api_id]



        if (api1['type'] == 'member_function' or api1['type'] == 'function') and (api2['type'] == 'member_function' or api2['type'] == 'function'):
            params1 = api1.get('parameters', {})
            params2 = api2.get('parameters', {})
            if ('args' in params1.keys() or 'kwargs' in params1.keys()) and ('args' in params2.keys() or 'kwargs' in params2.keys()):

                continue
            if not compare_parameter_lists(params1, params2, api_id):
                # different_apis.append(api_id)
                pass

    for api_id in version1_apis.keys():
        if api_id not in common_apis:
            version1_only_apis.append(api_id)
            different_apis.append(
                {
                    "old_api": api_id,
                    "new_api": "",
                    "old_parameter": version1_apis[api_id].get('parameters', {}),
                    "new_parameter": {},
                    "old_type": version1_apis[api_id]['type'],
                    "new_type": "",
                    "change_type": Pattern.API_REMOVAL.value,
                    "IC":"FIC"
                })


    for api_id in version2_apis.keys():
        if api_id not in common_apis:
            version2_only_apis.append(api_id)
            different_apis.append(
                {
                    "old_api": "",
                    "new_api": api_id,
                    "old_parameter": {},
                    "new_parameter": version2_apis[api_id].get('parameters', {}),
                    "old_type": "",
                    "new_type": version2_apis[api_id]['type'],
                    "change_type": Pattern.API_ADDITION.value,
                    "IC":"BIC"
                })

    return [len(common_apis), len(different_apis), len(version1_only_apis), len(version2_only_apis)]


def compare_parameter_lists(params1, params2, api_id):
    different_params = []

    ne_params1,op_params1 = get_params_type(params1)
    ne_params2,op_params2 = get_params_type(params2)
    if len(ne_params1) != len(ne_params2):
        if len(ne_params1) > len(ne_params2):
            for p in ne_params1.keys():
                if p not in ne_params2.keys():
                    change = p
            different_params.append({
                "old_api": api_id,
                "new_api": api_id,
                "old_parameter": params1,
                "new_parameter": params2,
                "change_type": Pattern.PARAM_REMOVAL.value,
                "IC":"BIC/FIC",
                "change":change
            })
        if len(ne_params1) < len(ne_params2):
            for p in ne_params2.keys():
                if p not in ne_params1.keys():
                    change = p
            different_params.append({
                "old_api": api_id,
                "new_api": api_id,
                "old_parameter": params1,
                "new_parameter": params2,
                "change_type": Pattern.PARAM_ADDITION.value,
                "IC":"BIC/FIC",
                "change":change
            })
    else:
        if len(op_params1) != len(op_params2):
            if len(op_params1) > len(op_params2):
                for op in op_params1.keys():
                    if op not in op_params2.keys():
                        change = op
                different_params.append({
                    "old_api": api_id,
                    "new_api": api_id,
                    "old_parameter": params1,
                    "new_parameter": params2,
                    "change_type": Pattern.OPTIONAL_PARAM_REMOVAL.value,
                    "IC":"FIC",
                    "change":change
            })
            if len(op_params1) < len(op_params2):
                for op in op_params2.keys():
                    if op not in op_params1.keys():
                        change = op
                different_params.append({
                    "old_api": api_id,
                    "new_api": api_id,
                    "old_parameter": params1,
                    "new_parameter": params2,
                    "change_type": Pattern.OPTIONAL_PARAM_ADDITION.value,
                    "IC":"BIC",
                    "change":change
                })
        else:
            if compare_keys_order(params1, params2):
                different_params.append({
                    "old_api": api_id,
                    "new_api": api_id,
                    "old_parameter": params1,
                    "new_parameter": params2,
                    "change_type": Pattern.PARAM_REORDEING.value,
                    "IC":"BIC/FIC"
                })

    if different_params:

        save_parameter_changes(different_params)
        return False

    else:
        return True

def get_pip_version_list(excel_file_path, package):
    df = pd.read_excel(excel_file_path)

    target_row = df[df["database"] == package]
    if not target_row.empty:
        version_list = target_row.iloc[0]["collections"]
        version_list = version_list.split(", ")
        return version_list
    else:
        return []

def get_package_list(excel_file_path):
    df = pd.read_excel(excel_file_path)
    package_list = df["database"].tolist()
    return package_list

def create_dotless_dict():
    lst = pd.read_excel("package_info_new_all.xlsx")["Package Name"]

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

def drop_collections(client, package_name, apt_version, pip_version_list):
    if '$' == apt_version:
        return
    if '#' == apt_version:
        return
    db = client.get_database(str(package_name) + "_API")
    for version in pip_version_list:
        db[str(str(package_name) + str(apt_version) + "VS" + str(version))].drop()
        db[str(str(package_name) + str(version) + "VS" + str(apt_version))].drop()

def main():

    flag = 0
    package_list = get_package_list(
        "collection_stats(6).xlsx")
    print(package_list)
    for package_name in package_list:
        flag = flag + 1
        pip_version_list = get_pip_version_list(
            "collection_stats(6).xlsx", str(package_name))
        # print(pip_version_list)
        print((package_name, flag))
        if len(pip_version_list) == 0:
            continue
        if flag < 0:
            continue
        client = pymongo.MongoClient('mongodb://localhost:27017')
        connect(client, str(package_name).replace("_API", ""), get_apt_version(
            str(package_name).replace("_API", "")), pip_version_list)
        # drop_collections(client, str(package_name).replace("_API", ""),
        #                  get_apt_version(str(package_name).replace("_API", "")), pip_version_list)
        client.close()


def error_analyse():
    pattern = r"(\w+?)(?=\d)([\d\.]+)"


    failed_packages = {}
    flag = 0
    with open('error.txt', 'r', encoding='utf-8') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                package, version = match.groups()
                if package in failed_packages:
                    failed_packages[package].append(version)
                else:
                    failed_packages[package] = [version]

    for package_name, pip_version_list in failed_packages.items():
        flag = flag + 1
        print((package_name, flag))
        if len(pip_version_list) == 0:
            continue
        if flag < 0:
            continue
        client = pymongo.MongoClient('mongodb://localhost:27017')
        connect(client, str(package_name).replace("_API", ""), get_apt_version(
            str(package_name).replace("_API", "")), pip_version_list)
        # drop_collections(client, str(package_name).replace("_API", ""),
        #                  get_apt_version(str(package_name).replace("_API", "")), pip_version_list)
        client.close()


dotless_dict = {}
if __name__ == '__main__':
    dotless_dict = create_dotless_dict()
    main()
    # package_list = get_package_list(
    #     "collection_stats(6).xlsx")
    # with open("./package_list.txt", "w") as file:
    #     for var in package_list:
    #         file.write(f"{get_real_package_name(var.replace('_API', ''))}\n")
