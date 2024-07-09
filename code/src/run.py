import argparse
import logging
import os
import json
from api_extractor import API_Extractor
from fixing_finder import detect_fixing_ifs, detect_fixing_tries,is_api_in_fixing_try
import json
from os.path import join

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



def check_fixing(danger_api_usage: dict):

    fixing_ifs = detect_fixing_ifs(danger_api_usage)
    fixing_tries = detect_fixing_tries(danger_api_usage)
    if len(fixing_ifs) > 0 or len(fixing_tries) > 0:
        return True
    else:
        return False


def generate_report(all_api, output_dir):
    with open(output_dir, 'w') as report_file:
        all_api = [x for x in all_api if x != []]
        json.dump(all_api, report_file)


def start(args):
    all_api = []
    if os.path.isfile(args.input) and args.input.endswith('.py'):
        all_api.append(process_file(args.input, args))
    elif os.path.isdir(args.input):
        for root, dirs, files in os.walk(args.input):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    all_api.append(process_file(file_path, args))
    else:
        logger.error("Invalid input path: {}".format(os.path.abspath(args.input)))
    

    # Generating report
    generate_report(all_api, args.output)

def process_file(file_path, args):

    # Get all APIs
    api_extractor = API_Extractor(args.framework, file_path, "none")
    all_apis = api_extractor.get_api()

    all_apis = list(
        filter(lambda x: not check_fixing(x), all_apis))

    return all_apis

def set_logger(level):
    FORMAT = '[%(levelname)s][%(filename)s][line:%(lineno)d]%(message)s'
    logging.basicConfig(format=FORMAT, level=level)
    return logging.getLogger("extraction")


if __name__ == "__main__":
    logger = set_logger(logging.DEBUG)

    parser = argparse.ArgumentParser(description='extraction')
    parser.add_argument("input",
                        help='Path for input file')
    parser.add_argument("framework",
                        help='framework name')
    parser.add_argument("output",
                        help='Path for output')
    args = parser.parse_args()

    start(args)
