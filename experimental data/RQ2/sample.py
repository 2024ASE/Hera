from pymongo import MongoClient
from collections import Counter
import random
import json

def sample_incompatible_changes(mongo_uri, type_counts,total_sample_size=384, min_samples_per_type=10):
    client = MongoClient(mongo_uri)

    change_types = [
        "api_addition", "api_removal", "param_addition",
        "param_removal", "optional_param_addition",
        "optional_param_removal", "param_reordering"
    ]

    # type_counts = Counter()
    # total_count = 0


    # for db_name in filter(lambda name: '_API' in name, client.list_database_names()):
    #     db = client[db_name]
    #     for collection_name in filter(lambda name: 'VS' in name, db.list_collection_names()):
    #         collection = db[collection_name]
    #         for change_type in change_types:
    #             count = collection.count_documents({"change_type": change_type})
    #             type_counts[change_type] += count
    #             total_count += count
    #     print(type_counts)
    
    # print(total_count)

    samples = {change_type: [] for change_type in type_counts.keys()}


    # total_count = sum(type_counts.values())

    # sample_sizes = {
    #     change_type: max(round((count / total_count) * total_sample_size), min_samples_per_type)
    #     for change_type, count in type_counts.items()
    # }
    # sample_sizes = {
    #     'api_addition': 259, 
    #     'api_removal': 75, 
    #     'param_addition': 10, 
    #     'param_removal': 10, 
    #     'optional_param_addition': 10,
    #     'optional_param_removal': 10,
    #     'param_reordering': 10
    # }

    print(sample_sizes)
    db_names = [name for name in client.list_database_names() if '_API' in name]

    for change_type in type_counts.keys():
        count = 0
        while count < sample_sizes[change_type]:
            db_name = random.choice(db_names)
            db = client[db_name]
            collection_names = [name for name in db.list_collection_names() if 'VS' in name]
            if not collection_names:
                continue
            collection_name = random.choice(collection_names)
            collection = db[collection_name]
            doc_ids = collection.find({"change_type": change_type}, {"_id": 1})
            doc_ids = [doc['_id'] for doc in doc_ids]
            if not doc_ids:
                continue
            if doc_ids:
                doc_id = random.choice(doc_ids)
                doc = collection.find_one({"_id": doc_id})
                doc['database'] = db_name
                doc['collection'] = collection_name
                print(doc)
                samples[change_type].append(doc)
                count = count + 1
    return samples

# 使用示例
mongo_uri ='mongodb://localhost:27017'
type_counts = {
    'api_addition': 32674616, 
    'api_removal': 8831893
    # 'optional_param_addition': 328988, 
    # 'param_addition': 102490, 
    # 'param_removal': 71221,
    # 'optional_param_removal': 46275,
    # 'param_reordering': 3973
}
# type_counts = Counter()
samples = sample_incompatible_changes(mongo_uri,type_counts)

with open(r'~\expr2\sample.json', 'w') as file:
    json.dump(samples, file, indent=4, default=str)
