"""
    Parser lib for converting IDL prose into a parsed representation suitable for saving as JSON

    http://common.barrister.bitmechanic.com/

    :copyright: 2012 by James Cooper.
    :license: MIT, see LICENSE for more details.
"""

import os
import os.path
import time
import copy
import operator
import io
# from plex import Scanner, Lexicon, Str, State, IGNORE
# from plex import Begin, Any, AnyBut, AnyChar, Range, Rep
from .cythonplex3 import Scanner, Lexicon, Str, State, IGNORE
from .cythonplex3 import Begin, Any, AnyBut, AnyChar, Range, Rep

import json
import hashlib

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


native_types    = [ "int", "float", "string", "bool" ]
void_func_types = [ "\r\n", "\n" ]
letter          = Range("AZaz")
digit           = Range("09")
under           = Str("_")
period          = Str(".")
plain_ident     = (letter | under) + Rep(letter | digit | under)
ns_ident        = plain_ident + period + plain_ident
ident           = plain_ident | ns_ident
arr_ident       = Str("[]") + ident
space           = Any(" \t\n\r")
space_tab       = Any(" \t")
comment         = Str("// ") | Str("//")
type_opts       = Str("[") + Rep(AnyBut("{}]\n")) + Str("]")
namespace       = Str("namespace") + Rep(space_tab) + plain_ident
import_stmt     = Str("import") + Rep(space_tab) + Str('"') + Rep(AnyBut("\"\r\n")) + Str('"')

def file_paths(fname, search_path=None):
    if not search_path and "BARRISTER_PATH" in os.environ:
        search_path = os.environ["BARRISTER_PATH"]
    paths = []
    paths.append(fname)
    if search_path:
        for directory in search_path.split(os.pathsep):
            paths.append(os.path.join(directory, fname))
    return paths

def parse(idl_text, idlFilename=None, validate=True, add_meta=True):
    if not isinstance(idl_text, str):
        idl_text = idl_text.read()

    scanner = IdlScanner(idl_text, idlFilename)
    scanner.parse(validate=validate)

    if len(scanner.errors) == 0:
        if add_meta:
            scanner.add_meta()
        return scanner.parsed
    else:
        raise IdlParseException(scanner.errors)

# def validate_scanner(scanner):
#     scanner2 = IdlScanner(idl_text, idlFilename)
#     scanner2.parse(scanner)
#     scanner = scanner2

def elem_checksum(elem):
    if elem["type"] == "struct":
        s = ""
        fields = copy.copy(elem["fields"])
        fields.sort(key=operator.itemgetter("name"))
        for f in fields:
            fs = (f["name"], f["type"], f["is_array"], f["optional"])
            s += "\t%s\t%s\t%s\t%s" % fs
        fs = (elem["name"], elem["extends"], s)
        return "struct\t%s\t%s\t%s\n" % fs
    elif elem["type"] == "enum":
        s = "enum\t%s" % elem["name"]
        vals = copy.copy(elem["values"])
        vals.sort(key=operator.itemgetter("value"))
        for v in vals: s += "\t%s" % v["value"]
        s += "\n"
        return s
    elif elem["type"] == "interface":
        s = "interface\t%s" % elem["name"]
        funcs = copy.copy(elem["functions"])
        funcs.sort(key=operator.itemgetter("name"))
        for f in funcs:
            s += "[%s" % f["name"]
            for p in f["params"]:
                s += "\t%s\t%s" % (p["type"], p["is_array"])
            if f.get("returns", None):
                ret = f["returns"]
                fs = (ret["type"], ret["is_array"], ret["optional"])
                s += "(%s\t%s\t%s)]" % fs
        s += "\n"
        return s
    return None

class IdlParseException(Exception):

    def __init__(self, errors):
        Exception.__init__(self)
        self.errors = errors

    def __str__(self):
        s = ""
        for e in self.errors:
            if s != "":
                s += ", "
            s += "line: %d message: %s" % (e["line"], e["message"])
        return s

class IdlScanner(Scanner):

    def __init__(self, idl_text, name):
        f = io.StringIO(idl_text)
        Scanner.__init__(self, self.lex, f, name)
        self.parsed = [ ]
        self.errors = [ ]
        self.types = { }
        self.imports = { }
        self.comment = None
        self.cur = None
        self.namespace = None
        self.searchPath = None
        self.idl_text = idl_text
        self.name = name
        if name:
            searchPath = os.path.dirname(os.path.abspath(name))
            if 'BARRISTER_PATH' in os.environ:
                searchPath = searchPath + os.pathsep + os.environ['BARRISTER_PATH']
            self.searchPath = searchPath

    def parse(self, firstPass=None, validate=False):
        self.firstPass = firstPass
        while True:
            (t, name) = self.read()
            if t is None:
                break
            else:
                self.add_error(t)
                break

        if validate:
            scanner2 = IdlScanner(self.idl_text, self.name)
            scanner2.parse(self)
            self.parsed = scanner2.parsed
            self.errors = scanner2.errors
            self.types  = scanner2.types

    def import_file(self, fname):
        path_to_load = None
        for path in file_paths(fname, self.searchPath):
            path = os.path.abspath(path)
            if os.path.exists(path):
                path_to_load = path
                break
        if path_to_load:
            if path_to_load not in self.imports:
                f = open(path_to_load)
                idl_text = f.read()
                f.close()
                scanner = IdlScanner(idl_text, path_to_load)
                self.imports[path_to_load] = scanner
                scanner.parse(validate=True)
                for elem in scanner.parsed:
                    if elem["type"] == "struct" or elem["type"] == "enum":
                        if elem["name"] in self.types:
                            c1 = elem_checksum(self.types[elem["name"]])
                            c2 = elem_checksum(elem)
                            if c1 != c2:
                                self.add_error("Include %s redefined type: %s" % (path_to_load, elem["name"]))
                        else:
                            self.types[elem["name"]] = elem
                            self.parsed.append(elem)
        else:
            self.add_error("Cannot find import file: %s" % fname)

    def eof(self):
        if self.cur:
            self.add_error("Unexpected end of file")

    def add_meta(self):
        from stackhut.common.barrister import __version__
        meta = {
            "type"              : "meta",
            "barrister_version" : __version__,
            "date_generated"    : int(time.time() * 1000),
            "checksum"          : self.get_checksum()
        }
        self.parsed.append(meta)

    def get_checksum(self):
        """
        Returns a checksum based on the IDL that ignores comments and
        ordering, but detects changes to types, parameter order,
        and enum values.
        """
        arr = [ ]
        for elem in self.parsed:
            s = elem_checksum(elem)
            if s:
                arr.append(s)
        arr.sort()
        #print arr
        return md5(json.dumps(arr))

    #####################################################

    def validate_type_vs_first_pass(self, type_str):
        if self.firstPass:
            self.add_error(self.firstPass.validate_type(type_str, [], 0))

    def validate_type(self, cur_type, types, level):
        level += 1

        cur_type = self.strip_array_chars(cur_type)

        if cur_type in native_types or cur_type in types:
            pass
        elif cur_type not in self.types:
            return "undefined type: %s" % cur_type
        else:
            cur = self.types[cur_type]
            types.append(cur_type)
            if cur["type"] == "struct":
                if cur["extends"] != "":
                    self.validate_type(cur["extends"], types, level)
                for f in cur["fields"]:
                    self.validate_type(f["type"], types, level)
            elif cur["type"] == "interface":
                # interface types must be top-level, so if len(types) > 1, we
                # know this interface was used as a type in a function
                # or struct
                return "interface %s cannot be used as a type" % cur["name"]
                if level > 1:
                    return "interface %s cannot be a field type" % cur["name"]
                else:
                    for f in cur["functions"]:
                        types = [ ]
                        for p in f["params"]:
                            self.validate_type(p["type"], types, 1)
                        self.validate_type(f["returns"]["type"], types, 1)

    def validate_struct_extends(self, s):
        if self.firstPass:
            name    = s["name"]
            extends = s["extends"]

            if extends in native_types:
                self.add_error("%s cannot extend %s" % (name, extends))
            elif extends in self.firstPass.types:
                ext_type = self.firstPass.types[extends]
                if ext_type["type"] != "struct":
                    fs = (name, ext_type["type"], extends)
                    self.add_error("%s cannot extend %s %s" % fs)
            else:
                self.add_error("%s extends unknown type %s" % (name, extends))

    def validate_struct_field(self, s):
        if self.firstPass:
            names = self.get_parent_fields(s, [], [])
            for f in s["fields"]:
                if f["name"] in names:
                    errf = (s["name"], f["name"])
                    err  = "%s cannot redefine parent field %s" % errf
                    self.add_error(err)

    def validate_struct_cycles(self, s):
        if self.firstPass:
            all_types = self.firstPass.get_struct_field_types(s, [])
            if s["name"] in all_types:
                self.add_error("cycle detected in struct: %s" % s["name"])

    def get_parent_fields(self, s, names, types):
        if s["extends"] in self.types:
            if s["name"] not in types:
                types.append(s["name"])
                parent = self.types[s["extends"]]
                if parent["type"] == "struct":
                    for f in parent["fields"]:
                        if f["name"] not in names:
                            names.append(f["name"])
                    self.get_parent_fields(parent, names, types)
        return names

    def get_struct_field_types(self, struct, types):
        for f in struct["fields"]:
            type_name = self.strip_array_chars(f["type"])
            if type_name in self.types and not type_name in types:
                t = self.types[type_name]
                if t["type"] == "struct":
                    if not f["is_array"] and not f["optional"]:
                        types.append(type_name)
                        self.get_struct_field_types(t, types)
                else:
                    types.append(type_name)
        if struct["extends"] != "":
            type_name = struct["extends"]
            if type_name in self.types and not type_name in types:
                t = self.types[type_name]
                if t["type"] == "struct":
                    types.append(type_name)
                    self.get_struct_field_types(t, types)
        return types

    def strip_array_chars(self, name):
        if name.find("[]") == 0:
            return name[2:]
        return name

    def add_error(self, message, line=-1):
        if not message: return
        if line < 0:
            (name, line, col) = self.position()
        self.errors.append({"line": line, "message": message})

    def prefix_namespace(self, ident):
        if self.namespace and ident.find(".") < 0 and ident not in native_types:
            return self.namespace + "." + ident
        return ident

    #####################################################

    def begin_struct(self, text):
        self.check_dupe_name(text)
        name = self.prefix_namespace(text)
        self.cur = { "name" : name, "type" : "struct", "extends" : "",
                     "comment" : self.get_comment(), "fields" : [] }
        self.begin('start-block')

    def begin_enum(self, text):
        self.check_dupe_name(text)
        name = self.prefix_namespace(text)
        self.cur = { "name" : name, "type" : "enum",
                     "comment" : self.get_comment(), "values" : [] }
        self.begin('start-block')

    def begin_interface(self, text):
        self.check_dupe_name(text)
        self.cur = { "name" : text, "type" : "interface",
                     "comment" : self.get_comment(), "functions" : [] }
        self.begin('start-block')

    def check_dupe_name(self, name):
        if name in self.types:
            self.add_error("type %s already defined" % name)

    def check_not_empty(self, cur, list_name, printable_name):
        if len(cur[list_name]) == 0:
            flist = (cur["name"], printable_name)
            self.add_error("%s must have at least one %s" % flist)
            return False
        return True

    def set_namespace(self, text):
        if self.namespace:
            self.add_error("Cannot redeclare namespace")
        elif len(self.parsed) > 0:
            self.add_error("namespace must preceed all struct/enum/interface definitions")
        ns = text.strip()[9:].strip()
        self.namespace = ns
        self.begin('end_of_line')

    def add_import(self, text):
        start = text.find('"') + 1
        end   = text[start:].find('"') + start
        fname = text[start:end]
        self.import_file(fname)
        self.begin('end_of_line')

    def end_of_line(self, text):
        self.cur = None
        self.begin('')

    def start_block(self, text):
        t = self.cur["type"]
        if t == "struct":
            self.begin("fields")
        elif t == "enum":
            self.begin("values")
        elif t == "interface":
            if self.namespace:
                self.add_error("namespace cannot be used in files with interfaces")
            self.begin("functions")
        else:
            raise Exception("Invalid type: %s" % t)
        #self.validate_type_vs_first_pass(self.cur["name"])

    def end_block(self, text):
        ok = False
        t = self.cur["type"]
        if t == "struct":
            ok = self.check_not_empty(self.cur, "fields", "field")
            self.validate_struct_cycles(self.cur)
        elif t == "enum":
            ok = self.check_not_empty(self.cur, "values", "value")
        elif t == "interface":
            ok = self.check_not_empty(self.cur, "functions", "function")

        if ok:
            self.parsed.append(self.cur)
            self.types[self.cur["name"]] = self.cur

        self.cur = None
        self.begin('')

    def begin_field(self, text):
        self.field = { "name" : text }
        self.begin("field")

    def end_field(self, text):
        is_array = False
        if text.find("[]") == 0:
            text = text[2:]
            is_array = True
        type_name = self.prefix_namespace(text)
        self.validate_type_vs_first_pass(type_name)
        self.field["type"] = type_name
        self.field["is_array"] = is_array
        self.field["comment"] = self.get_comment()
        self.field["optional"] = False
        self.type = self.field
        self.cur["fields"].append(self.field)
        self.validate_struct_field(self.cur)
        self.field = None
        self.next_state = "fields"
        self.begin("type-opts")

    def begin_function(self, text):
        self.function = {
               "name" : text,
            "comment" : self.get_comment(),
             "params" : [ ] }
        self.begin("function-start")

    def begin_param(self, text):
        self.param = { "name" : text }
        self.begin("param")

    def end_param(self, text):
        is_array = False
        if text.find("[]") == 0:
            text = text[2:]
            is_array = True
        type_name = self.prefix_namespace(text)
        self.validate_type_vs_first_pass(type_name)
        self.param["type"] = type_name
        self.param["is_array"] = is_array
        self.function["params"].append(self.param)
        self.param = None
        self.begin("end-param")

    def end_return(self, text):
        is_array = False
        if text.find("[]") == 0:
            text = text[2:]
            is_array = True
        type_name = self.prefix_namespace(text)
        if type_name in void_func_types:
            self.type = None
            self.next_state = "functions"
            self.cur["functions"].append(self.function)
            self.function = None
            self.begin(self.next_state)
        else:
            self.validate_type_vs_first_pass(type_name)
            self.function["returns"] = {
                    "type" : type_name,
                "is_array" : is_array,
                "optional" : False }
            self.type = self.function["returns"]
            self.next_state = "functions"
            self.cur["functions"].append(self.function)
            self.function = None
            self.begin("type-opts")

    def end_type_opts(self, text):
        text = text.strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1]
        if text != "":
            if text == "optional":
                self.type["optional"] = True
            else:
                raise Exception("Invalid type option: %s" % text)
        self.type = None
        self.begin(self.next_state)
        self.next_state = None

    def end_type_opts_and_block(self, text):
        self.end_type_opts(text)
        self.end_block(text)

    def end_value(self, text):
        if not text in self.cur["values"]:
            val = { "value" : text, "comment" : self.get_comment() }
            self.last_comment = ""
            self.cur["values"].append(val)

    def get_comment(self):
        comment = ""
        if self.comment and len(self.comment) > 0:
            comment = "".join(self.comment)
        self.comment = None
        return comment

    def start_comment(self, text):
        if self.comment:
            self.comment.append("\n")
        else:
            self.comment = []
        self.prev_state = self.state_name
        self.begin("comment")

    def append_comment(self, text):
        self.comment.append(text)

    def append_field_options(self, text):
        self.field_options.append(text)

    def end_comment(self, text):
        self.begin(self.prev_state)
        self.prev_state = None

    def end_extends(self, text):
        if self.cur and self.cur["type"] == "struct":
            self.cur["extends"] = self.prefix_namespace(text)
            self.validate_struct_extends(self.cur)
        else:
            self.add_error("extends is only supported for struct types")

    def add_comment_block(self, text):
        comment = self.get_comment()
        if comment:
            self.parsed.append({"type" : "comment", "value" : comment})

    lex = Lexicon([
            (Str("\n"),  add_comment_block),
            (space,      IGNORE),
            (namespace,   set_namespace),
            (import_stmt, add_import),
            (Str('struct '),   Begin('struct-start')),
            (Str('enum '),   Begin('enum-start')),
            (Str('interface '),   Begin('interface-start')),
            (comment,    start_comment),
            State('end_of_line', [
                    (Str("\r\n"), end_of_line),
                    (Str("\n"), end_of_line),
                    (space, IGNORE),
                    (AnyChar, "Illegal character - expected end of line") ]),
            State('struct-start', [
                    (ident,    begin_struct),
                    (space,    IGNORE),
                    (AnyChar, "Missing identifier") ]),
            State('enum-start', [
                    (ident,    begin_enum),
                    (space,    IGNORE),
                    (AnyChar, "Missing identifier") ]),
            State('interface-start', [
                    (ident,    begin_interface),
                    (space,    IGNORE),
                    (AnyChar, "Missing identifier") ]),
            State('start-block', [
                    (space, IGNORE),
                    (Str("extends"), Begin('extends')),
                    (Str('{'), start_block) ]),
            State('extends', [
                    (space, IGNORE),
                    (ident, end_extends),
                    (Str('{'), start_block) ]),
            State('fields', [
                    (ident,    begin_field),
                    (space,    IGNORE),
                    (comment, start_comment),
                    (Str('{'), 'invalid'),
                    (Str('}'), end_block) ]),
            State('field', [
                    (ident,    end_field),
                    (arr_ident, end_field),
                    (Str("\n"), 'invalid'),
                    (space,    IGNORE),
                    (Str('{'), 'invalid'),
                    (Str('}'), 'invalid') ]),
            State('functions', [
                    (ident,    begin_function),
                    (space,    IGNORE),
                    (comment,  start_comment),
                    (Str('{'), 'invalid'),
                    (Str('}'), end_block) ]),
            State('function-start', [
                    (Str("("), Begin('params')),
                    (Str("\n"), 'invalid'),
                    (space,    IGNORE) ]),
            State('params', [
                    (ident,    begin_param),
                    (space,    IGNORE),
                    (Str(")"), Begin('function-return')) ]),
            State('end-param', [
                    (space, IGNORE),
                    (Str(","), Begin('params')),
                    (Str(")"), Begin('function-return')) ]),
            State('param', [
                    (ident,    end_param),
                    (arr_ident, end_param),
                    (space,    IGNORE) ]),
            State('function-return', [
                    (Str("\r\n"), end_return),
                    (Str("\n"), end_return),
                    (space,    IGNORE),
                    (ident,    end_return),
                    (arr_ident, end_return) ]),
            State('type-opts', [
                    (type_opts, end_type_opts),
                    (Str("\n"), end_type_opts),
                    (Str('}'),  end_block),
                    (space,    IGNORE),
                    (Str('{'),  'invalid') ]),
            State('end-function', [
                    (Str("\n"), Begin('functions')),
                    (space, IGNORE) ]),
            State('values', [
                    (ident,    end_value),
                    (space,    IGNORE),
                    (comment,  start_comment),
                    (Str('{'), 'invalid'),
                    (Str('}'), end_block) ]),
            State('comment', [
                    (Str("\n"),     end_comment),
                    (AnyChar, append_comment) ])
            ])

