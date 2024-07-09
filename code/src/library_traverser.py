#! /usr/bin/python3

import queue
import inspect
import sys
import re
import parso

# Base class for extracting member information
class MemberInfoExtractor:
    # Extract argument documentation
    def extract_args_doc(self, doc):
        return {}

    # Extract return value documentation
    def extract_returns_doc(self, doc):
        return None

    # Extract exception documentation
    def extract_raise_doc(self, doc):
        return None

    # Check if a member is deprecated
    def is_deprecated(self, name, member):
        return False

# Convert values to a usable code form
def conver_to_code(value):
    if value is None:
        return "None"
    supported_types = (int, float, bool, str)
    if type(value) in supported_types:
        return repr(value)
    elif type(value) in (list, tuple) and all(element is None or type(element) in supported_types for element in value):
        return repr(value)
    else:
        return "___complex_type___"

# Class for visiting members
class MemberVisitor:
    def __init__(self, data_output_handler, inspector=inspect, extractor=MemberInfoExtractor()):
        self._yield_item = data_output_handler
        self._is_deprecated = extractor.is_deprecated
        self._extract_args_doc = extractor.extract_args_doc
        self._extract_returns_doc = extractor.extract_returns_doc
        self._extract_raise_doc = extractor.extract_raise_doc
        self._inspect = inspector

    # Parse basic information
    def _parse_basic_info(self, name, member):
        return {
            "_id": name,
            "doc": self._inspect.getdoc(member),
            "is_deprecated": self._is_deprecated(name, member)
        }

    # Try to get the definition of a function
    def _try_get_func_def(self, func):
        if not self._inspect.getsourcefile(func):
            return None
        else:
            source = self._inspect.getsource(func)
            tree = parso.parse(source)
            return next(tree.iter_funcdefs(), None)

    # Get the signature string of a function
    def _get_sig_string(self, func):
        func_def = self._try_get_func_def(func)
        if func_def:
            return "(%s)" % "".join(p.get_code() for p in func_def.get_params())
        else:
            sig = self._inspect.signature(func)
            return "(%s)" % ", ".join(
                name if p.default is inspect.Parameter.empty else "%s=%s" % (
                    name, conver_to_code(p.default))
                for name, p in sig.parameters.items()
            )

    # Parse function members
    def _parse_function(self, name, member):
        doc = self._inspect.getdoc(member)
        arg_doc = self._extract_args_doc(doc)
        sig_str = self._get_sig_string(member)

        return {
            **self._parse_basic_info(name, member),
            "signature": sig_str,
            "parameters": {
                name: {
                    "description": arg_doc[name] if name in arg_doc else None,
                    "is_optional": p.default is not inspect.Parameter.empty,
                }
                for name, p in self._inspect.signature(member).parameters.items()
            },
            "returns_doc": self._extract_returns_doc(doc),
            "raise_doc": self._extract_raise_doc(doc)
        }

    # Parse attribute members
    def _parse_attribute(self, name, member, class_member):
        return {
            **self._parse_basic_info(name, member),
        }

    # Visit module members
    def _visit_module(self, name, member):
        self._yield_item({
            **self._parse_basic_info(name, member),
            "type": "module"
        })

    # Visit class members
    def _visit_class(self, name, member):
        member_functions = (
            {
                **self._parse_function(".".join([name, func_name]), func),
                "type": "member_function",
                "class": name
            }
            for func_name, func in inspect.getmembers(member, self._inspect.isfunction)if (
                not func_name.startswith("_") or re.match(
                    r"__.*__$", func_name)
            )
        )
        attributes = (
            {
                **self._parse_attribute(".".join([name, attr_name]), attr, member),
                "type": "field",
                "class": name,
            }
            for attr_name, attr in inspect.getmembers(member) if (isinstance(attr, property) and not attr_name.startswith("_"))
        )
        mf_name_list = {}
        attr_name_list = {}
        for mf in member_functions:
            mf_name_list[mf["_id"]] = mf["signature"]
            self._yield_item(mf)
        for attr in attributes:
            attr_name_list[attr["_id"]] = attr["doc"]
            self._yield_item(attr)

        self._yield_item({
            **self._parse_basic_info(name, member),
            "member_functions": mf_name_list,
            "attributes": attr_name_list,
            "type": "class"
        })

    # Visit function members
    def _visit_function(self, name, member):
        try:
            self._yield_item({
                **self._parse_function(name, member),
                "type": "function"
            })
        except:
            pass

    # Visit module field members
    def _visit_module_field(self, name, member):
        self._yield_item({
            "_id": name,
            "doc": self._inspect.getdoc(member),
            "is_deprecated": self._is_deprecated(name, member),
            "type": "module_field",
            "module": name[:name.rfind(".")]
        })

    # Invoke the visitor to access members
    def __call__(self, name, member):
        try:
            if inspect.isfunction(member):
                self._visit_function(name, member)
            elif inspect.isclass(member):
                self._visit_class(name, member)
            elif not inspect.ismodule(member):
                d_name = name.split(".")[-1]
                if (not d_name.startswith("_")):
                    self._visit_module_field(name, member)
        except OSError:
            pass

# Utility functions to check if a name is private or if a member should be visited or skipped

def is_private_name(name):
    return name.startswith("_") and (not re.match(r"__.*__$", name))

def should_visit(prefix=""):
    def predicate(member):
        if inspect.ismodule(member):
            return member.__name__.startswith(prefix)
        elif inspect.isclass(member) and hasattr(member, "__module__"):
            return member.__module__.startswith(prefix)
        elif inspect.isfunction(member):
            return True
        return True

    return predicate

def should_skip_child(name, child):
    return is_private_name(name) or name in {"__base__", "__class__", "__builtins__"} or (
        inspect.ismodule(child) and child.__name__ in sys.builtin_module_names
    )

# Traverse through the members of a module
def traverse_module(root, visit, module_prefix=None, prefix_black_list=set(), error_handle=print()):
    members = queue.deque()
    members.append(root)
    visited = []
    lossed_amount = 0
    while members:
        member_name, member = members.popleft()
        if member_name in prefix_black_list:
            continue
        try:
            visited.append(str(member))
        except Exception as any_exp:
            pass

        try:
            visit(member_name, member)
        except Exception as any_exp:
            lossed_amount += 1
            error_handle({
                "id": member_name,
                "lossed_amount": lossed_amount,
                "error_message": str(any_exp),
                "member": str(member),
                "type": str(type(member))
            })

        if not inspect.ismodule(member):
            continue
        try:
            children = sorted(
                inspect.getmembers(member, should_visit(prefix=module_prefix))
            )
            for name, child in children:
                if should_skip_child(name, child):
                    continue
                try:
                    if str(child) not in visited:
                        members.append((".".join([member_name, name]), child))
                except Exception as any_exp:
                    lossed_amount += 1
                    error_handle({
                        "id": name,
                        "lossed_amount": lossed_amount,
                        "error_message": str(any_exp),
                        "member": str(child),
                        "type": str(type(child)),
                        "child": True,
                        "father": member_name,
                    })

        except ImportError as err:
            sys.stderr.write(
                "Error expanding %s due to an import error\n" % member_name
            )
            sys.stderr.write(err.msg)
    return lossed_amount
