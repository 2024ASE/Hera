# import networkx as nx
import os

# utils.py
from collections import deque
from parso.python.tree import TryStmt, ExprStmt, ImportFrom, Name, ImportName, IfStmt
import jedi

def find_nodes(node, pred=lambda x: True):
    """
    Traverse and find nodes that satisfy a specific condition.

    Args:
    node: The starting node, usually the root of a syntax tree.
    pred: A function to determine if a node meets the condition, default is a lambda function that returns True.

    Returns:
    result: List containing all nodes that meet the condition.
    """
    que = deque() # Using a queue for breadth-first search
    que.append(node)
    result = [] # Store nodes that meet the condition
    if pred(node):
        result.append(node)
    while que:
        n = que.popleft() # Remove a node from the queue
        if not hasattr(n, "children"):
            continue # Skip if the node has no children
        for ch in n.children: # Traverse child nodes
            if pred(ch): # Check if the child node meets the condition
                result.append(ch)
            que.append(ch) # Add child nodes to the queue
    return result

def extract_clauses_try(stmt):
    """
    Extract try and except blocks from a try statement.

    Args:
    stmt: A TryStmt object, representing a try statement.

    Returns:
    tuple: Contains the code for try and except blocks.
    """
    assert isinstance(stmt, TryStmt) # Ensure the input is a TryStmt object
    if len(stmt.children) == 6:
        return stmt.children[2], stmt.children[5] # Return try and except blocks
    else:
        return stmt.children[2], None # Only a try block, no except block

def extract_clauses_if(stmt):
    """
    Extract if and else blocks from an if statement.

    Args:
    stmt: An IfStmt object, representing an if statement.

    Returns:
    tuple: Contains the code for if and else blocks.
    """
    assert isinstance(stmt, IfStmt) # Ensure the input is an IfStmt object
    if len(stmt.children) < 7:
        # When the if statement does not have an else block
        return stmt.children[3], None # Only an if block, no else block
    else:
        # When the if statement has an else block
        return stmt.children[3], stmt.children[6] # Return if and else blocks

def variables_out(suite):
    """
    Extract variable names used in a code block.

    Args:
    suite: A code block, usually the content of if or try blocks.

    Returns:
    set: A set containing all variable names.
    """
    return {
        d.name for d in jedi.names(suite.get_code()) 
    } if suite else set() # Use the Jedi library to analyze the code block and extract variable names


def file_deduplication(file_in, file_out):
    data_set = set()  # Create a set

    # Read each line from the file and insert it into the set
    with open(file_in, 'r') as file:
        for line in file:
            line = line.strip()  # Remove leading and trailing whitespace
            data_set.add(line)

    sorted_list = sorted(data_set)

    # Write the elements of the set to another file
    with open(file_out, 'w') as file:
        for item in sorted_list:
            file.write(item + '\n')




def dependency_graph(file_name):
    dependency_graph = nx.DiGraph()
    with open(file_name, "r") as file:
        lines = file.readlines()
    for line in lines:
        line = line.strip()  
        if line:
            parts = line.split(":")  
            package = str("python3-" + str(parts[0]))
            dependencies = parts[1].split(",") if len(parts) > 1 else []


            dependency_graph.add_node(
                package, extra_info="your_extra_info_here")


            for dependency in dependencies:
                dependency_graph.add_edge(package, dependency)
    return dependency_graph



def read_directory_list(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
        directory_list = [line.strip() for line in lines]
        return directory_list


def check_directory():

    parent_directory = "~/wheels"


    txt_file_path = "~/all_framework3.txt"
    target_directories = read_directory_list(txt_file_path)


    for target_directory in target_directories:
        directory_path = os.path.join(parent_directory, target_directory)
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            print(
                f"Directory '{target_directory}' exists at '{directory_path}'")
        else:
            print(f"Directory '{target_directory}' does not exist")


if __name__ == '__main__':
    check_directory()
