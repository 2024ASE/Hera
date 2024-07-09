# coding: utf-8

# ## API_Extractor
# #### This is used to extract all API usage from all files under a directory.

import re
import parso
import os
import json
import collections
import logging

class API_Extractor:
    # Initialize the API_Extractor class
    def __init__(self, framework, fileName, repo_url):
        self.framework = framework
        self.module = self.parse_module(fileName)
        self.iR = self.get_import_name()
        self.fileName = fileName
        self.repo_url = repo_url

        if not self.framework_imported():
            # If the specified framework is not imported, do not proceed.
            return
        
    def get_iR(self):
        return self.iR

    def framework_imported(self):
        """
        Check if the specified framework has been imported.

        Returns:
        bool: Returns True if the specified framework has been imported, otherwise False.
        """
        for import_name in self.iR.values():
            if self.framework in import_name:
                return True
        return False
    
    # Check if the API call belongs to our framework
    def check(self, value, iR):
        if value in list(iR.keys()):
            return iR[value]
        return None

    # Handle parameters
    def __handle_param__(self, param):
        p = []
        if param.children[1].type == 'name':
            p = [param.children[1].value]
        else:
            if param.children[1].type == 'atom_expr':
                p = [param.children[1].get_code().replace(' ', '').replace('\n', '')]
            elif param.children[1].type == 'arglist':
                for child in param.children[1].children:
                    if child.type != 'operator':
                        p.append(child.get_code().replace(' ', '').replace('\n', ''))
            elif len(param.children) == 2:
                p = []
        return p

    # Extract call chain and parameter chain
    def __extract_call_param__(self, expr):
        allChildren = expr.children
        callChain = [allChildren[0].value]
        paramChain = [None]
        for i, leaf in enumerate(allChildren):
            if leaf.get_first_leaf() == '.':
                callChain.append(leaf.get_last_leaf().value)
                paramChain.append(None)
            elif leaf.get_first_leaf() == '(':
                param = self.__handle_param__(leaf)
                if paramChain[-1] is None:
                    paramChain[-1] = param
        return callChain, paramChain

    # Find each atom expression for API call
    def find_atom_expr(self, module, iR):
        allapi = []
        temp_iR = iR.copy()
        for node in module.children:
            if node.type == 'funcdef':
                if hasattr(node, 'children'):
                    allapi += self.find_atom_expr(node, temp_iR)
            else:
                if type(node) == parso.python.tree.PythonNode and node.type == 'atom_expr':
                    checkResult = self.check(node.get_first_leaf().value, iR)
                    if checkResult is not None:
                        allapi.append({node: checkResult})
                elif type(node) == parso.python.tree.PythonNode and node.type == 'argument':
                    for child in node.children:
                        if child.type == 'name':
                            checkResult = self.check(child.value, iR)
                            if checkResult is not None:
                                allapi.append({node: checkResult})
                if hasattr(node, 'children'):
                    allapi += self.find_atom_expr(node, iR)
        return allapi

    # Transform API
    def transform_api(self, aE):
        atomExpr = list(aE.keys())[0]
        lineNum, colNum = atomExpr.start_pos
        path = aE[atomExpr]
        call_chain, param_chain = self.__extract_call_param__(atomExpr)
        de_call_chain = path + call_chain[1:]
        api_name = ".".join(de_call_chain)

        return dict([
            ("framework", self.framework),
            ("repo_url", self.repo_url),
            ("api_name", api_name),
            ("line_num", lineNum),
            ("file_name", self.fileName),
            ('call_chain', call_chain),
            ('param_chain', param_chain)
        ])

    # Parse module
    def parse_module(self, fileName: str):
        return parso.parse(open(fileName, "r").read())

    # Get all imports
    def get_import_name(self):
        import_results = {}
        for imports in self.module.iter_imports():
            paths = imports.get_paths()
            names = imports.get_defined_names()
            for t, p in enumerate(paths):
                if len(p) > 0 and p[0].value == (self.framework):
                    call_path = list(map(lambda x: x.value, p))
                    try:
                        import_results[names[t].value] = call_path
                    except IndexError:
                        pass
        self.find_imports(self.module, import_results)
        return import_results

    def find_imports(self, node, import_results):
        if hasattr(node, 'children'):
            for child in node.children:
                if child.type == 'try_stmt':
                    for part in child.children:
                        if part.type == 'suite':
                            self.find_imports(part, import_results)
                elif child.type in ['import_name', 'import_from']:
                    paths = child.get_paths()
                    names = child.get_defined_names()
                    for t, p in enumerate(paths):
                        if len(p) > 0 and p[0].value == (self.framework):
                            call_path = list(map(lambda x: x.value, p))
                            try:
                                import_results[names[t].value] = call_path
                            except IndexError:
                                pass
                else:
                    self.find_imports(child, import_results)
    
    # Get all API call sites
    def get_api(self):
        exprs = self.find_atom_expr(self.module, self.iR)
        transformedApi = list(map(self.transform_api, exprs))
        return transformedApi

def extract_files(path):
    allFile = []
    for i in os.listdir(path):
        if os.path.isdir(path + '/' + i):
            allFile += extract_files(path + '/' + i)
        else:
            if i.endswith('.py'):
                allFile.append(path + '/' + i)
    return allFile
