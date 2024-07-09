#! /usr/bin/python3
import sys
from library_traverser import traverse_module, MemberVisitor, MemberInfoExtractor

import re
import inspect
import pymongo
import pkgutil
import importlib
import json
import subprocess


argv = sys.argv[1]
project = argv.split('_')[0].replace("-", "_")
version = argv.split('_')[1]

do_not_descend_map = {
    # 'numpy.lib': [
    #     'index_tricks'
    # #    'lib',
    #     #memory leak
    #     # 'ma',
    #     #memory leak
    # ],
    # 'numpy.ma.extras':[
    #     'mr_class'
    # ]
    # 'numpy.random': [
    #     'SeedSequence'
    # ],
    # 'numpy.random.bit_generator': [
    #     'SeedSequence'
    # ]
}


prefix_black_list = {
    ".".join([prefix, name])
    for prefix in do_not_descend_map
    for name in do_not_descend_map[prefix]
}

# mongn_client = pymongo.MongoClient('mongodb://localhost:27017')
mongo_client = pymongo.MongoClient(
    'mongodb://password@localhost:27017')
log_db = mongo_client.get_database("API_extract_log")
col = log_db.get_collection("Failure_message")
col1 = log_db.get_collection("Success_message")
col2 = log_db.get_collection("Other_message")

max_retries = 20
retry_count = 0
missing_module = []
me = ''
while retry_count < max_retries:
    try:
        module = importlib.import_module(project)
    except ModuleNotFoundError as e:
        error_message = str(e)
        start_index = error_message.find("'") + 1
        end_index = error_message.rfind("'")
        module_name = error_message[start_index:end_index]
        if module_name == project:
            col.insert_one({
                "package": project,
                "version": version,
                "status": "fail",
                "missing_module": missing_module,
                "error_message": "no package wheel",
                "type": "wheel error"
            })
            mongo_client.close()
            sys.exit()
        if module_name not in missing_module:
            missing_module.append(module_name)
        pip_cmd = f"pip install {module_name} -i https://mirrors.tencent.com/pypi/simple"
        try:
            subprocess.run(pip_cmd, shell=True, check=True)
        except Exception as ee:
            col.insert_one({
                "package": project,
                "version": version,
                "status": "fail",
                "missing_module": missing_module,
                "error_message": str(ee),
                "type": "pip install error"
            })
            mongo_client.close()
            sys.exit()
        else:
            pass

            retry_count += 1
            col2.insert_one({
                "package": project,
                "version": version,
                "status": "missing module",
                "missing_module": missing_module,
                "error_message": str(e)
            })
            me = str(e)
    except Exception as any_exp:
        print("Unknown exception occurred:", str(any_exp))
        col.insert_one({
            "package": project,
            "version": version,
            "status": "fail",
            "missing_module": missing_module,
            "error_message": str(any_exp),
            "type": "other exception"
        })
        mongo_client.close()
        sys.exit()
    else:
        break
    retry_count += 1
    if retry_count >= max_retries:
        print("ok")
        col.insert_one({
            "package": project,
            "version": version,
            "status": "fail",
            "missing_module": missing_module,
            "error_message": str(me),
            "type": "ModuleNotFoundError"
        })

try:
    sub_modules = [m for m in pkgutil.iter_modules(module.__path__) if m[2]]
    for m in sub_modules:
        importlib.import_module(str(project) + ".%s" % m[1], m)
except Exception as e:
    print("sub_module import error")
else:
    print("sub_module import successful")


try:
    argv1 = module.__path__
    argv2 = module.__version__
except Exception as e:
    col2.insert_one({
        "package": project,
        "version": version,
        "status": "no path or version",
        "error_message": str(e)
    })



class FlaskMemberInfoExtractor(MemberInfoExtractor):
    _args_doc_regex = re.compile(
        r"((\n:param (\w+): ([\S ]+(\n\ {16}[\S ]+)*))+)")
    _arg_item_doc_regex = re.compile(
        r":param (\w+): ([\S ]+(\n\ {16}[\S ]+)*)")
    _returns_doc_regex = re.compile(r"(Returns:\n)((\ {2}[\S\ ]+\n)+)")
    _raises_doc_regex = re.compile(r"(Raises:\n)((\ {2}[\S\ ]+\n)+)")

    def extract_args_doc(self, doc):
        arg_doc_match = next(self._args_doc_regex.finditer(doc or ""), None)
        if not arg_doc_match:
            return {}
        arg_doc = arg_doc_match.group(1)
        return {
            match.group(1):  match.group(2)
            for match in self._arg_item_doc_regex.finditer(arg_doc)
        }


    def extract_returns_doc(self, doc):
        match = next(self._returns_doc_regex.finditer(doc or ""), None)
        return match.group(2) if match else None


    def extract_raise_doc(self, doc):
        match = next(self._raises_doc_regex.finditer(doc or ""), None)
        return match.group(2) if match else None


    def is_deprecated(self, name, member):
        doc = inspect.getdoc(member)
        return False if not doc else "DEPRECATED" in doc


if "." not in str(project):
    db = mongo_client.get_database(str(project) + "_API")

    collection = db.get_collection(str(project) + "_APIs_%s" % version)
    collection_error = db.get_collection(str(project) + "_Errors_%s" % version)
    collection_log = db.get_collection(str(project) + "_Log")
else:
    project1 = str(project).replace('.', '')
    db = mongo_client.get_database(str(project1) + "_API")

    collection = db.get_collection(str(project1) + "_APIs_%s" % version)
    collection_error = db.get_collection(
        str(project1) + "_Errors_%s" % version)
    collection_log = db.get_collection(str(project1) + "_Log")


collection.drop()
collection_error.drop()



def insert_db(data):
    collection.insert_one(data)
    # print(data)
    # f.write(str(data))
    # f.write("/n")


def error_handle(data):
    # print(data)
    collection_error.insert_one(data)


def log_handle(collection, data):
    # print(data)
    collection.insert_one(data)


extractor = FlaskMemberInfoExtractor()

visitor = MemberVisitor(insert_db, inspect, extractor)

lossed_amount = traverse_module((str(project), module), visitor, str(
    project), prefix_black_list, error_handle)

log_handle(collection_log, {
    "package": project,
    "version": version,
    "status":  "successful",
    "lossed_amount": lossed_amount,
    "missing_module": missing_module
})


log_handle(col1, {
    "package": project,
    "version": version,
    "status":  "successful",
    "lossed_amount": lossed_amount,
    "missing_module": missing_module
})
mongo_client.close()
