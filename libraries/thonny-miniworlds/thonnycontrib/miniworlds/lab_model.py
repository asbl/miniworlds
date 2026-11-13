"""IDE-independent source model and literal argument parsing."""

import ast
import hashlib
import keyword
import os
from pathlib import Path


def classes_in(code):
    tree = ast.parse(code)
    return [
        {
            "name": n.name,
            "line": n.lineno,
            "bases": [ast.unparse(b) for b in n.bases],
            "methods": [
                {"name": m.name, "line": m.lineno}
                for m in n.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            ],
        }
        for n in tree.body
        if isinstance(n, ast.ClassDef)
    ]


def revision(root, filename, source, buffers=None):
    digest = hashlib.sha256()
    buffers = {Path(p).resolve(): text for p, text in (buffers or {}).items()}
    root, filename = Path(root), Path(filename).resolve()
    paths = []
    for folder, directories, files in os.walk(root):
        directories[:] = [
            d
            for d in directories
            if not d.startswith(".")
            and d not in {"venv", "env", "__pycache__", "site-packages"}
            and not (Path(folder) / d).is_symlink()
        ]
        paths.extend(Path(folder) / name for name in files if name.endswith(".py"))
    for path in sorted(paths):
        if path.is_symlink():
            continue
        digest.update(str(path.relative_to(root)).encode())
        digest.update(
            source.encode()
            if path.resolve() == filename
            else buffers[path.resolve()].encode()
            if path.resolve() in buffers
            else path.read_bytes()
        )
    digest.update(source.encode())
    return digest.hexdigest()


def arguments(text, references):
    call = ast.parse("f(" + text + ")", mode="eval").body

    def value(node):
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [value(item) for item in node.elts]
            return tuple(values) if isinstance(node, ast.Tuple) else values
        if isinstance(node, ast.Dict):
            if any(key is None for key in node.keys):
                raise ValueError("**kwargs werden nicht ausgewertet.")
            return {value(k): value(v) for k, v in zip(node.keys, node.values)}
        try:
            return ast.literal_eval(node)
        except (ValueError, TypeError):
            name = ast.unparse(node)
            if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript)) and name in references:
                return references[name]
            raise ValueError(
                "Nutze Zahlen, Texte, Tupel/Listen oder einen Objektnamen aus der Objektbank."
            ) from None

    if any(isinstance(a, ast.Starred) for a in call.args) or any(
        k.arg is None for k in call.keywords
    ):
        raise ValueError("*args und **kwargs werden im Dialog nicht ausgewertet.")
    return [value(a) for a in call.args], {k.arg: value(k.value) for k in call.keywords}


def object_name(name):
    if not name.isidentifier() or keyword.iskeyword(name) or name.startswith("_"):
        raise ValueError(
            "Bitte einen freien Python-Namen ohne führenden Unterstrich wählen."
        )


def export_calls(source, calls):
    tree = ast.parse(source)
    run = next(
        (
            n
            for n in tree.body
            if isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Attribute)
            and n.value.func.attr == "run"
        ),
        None,
    )
    lines = source.splitlines(keepends=True)
    offset = sum(map(len, lines[: run.lineno - 1])) if run else len(source)
    block = "\n# Im Objektlabor ausprobiert\n" + "\n".join(calls) + "\n\n"
    result = source[:offset] + block + source[offset:]
    ast.parse(result)
    return result


def parameter_schema(callback):
    """JSON-safe signature data, without evaluating annotations or defaults."""
    import inspect
    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError):
        return None
    result = []
    for parameter in signature.parameters.values():
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            return None  # Preserve the Python-entry escape hatch for dynamic signatures.
        default = parameter.default
        code = None
        if default is not parameter.empty and type(default) in (str, int, float, bool, type(None), tuple, list, dict):
            try:
                candidate = repr(default)
                if len(candidate) <= 200:
                    ast.literal_eval(candidate)
                    code = candidate
            except (ValueError, TypeError, RecursionError):
                pass
        annotation = parameter.annotation
        hint = 'literal'
        if annotation is str or type(default) is str:
            hint = 'text'
        elif annotation is bool or type(default) is bool:
            hint = 'boolean'
        elif annotation in (int, float) or type(default) in (int, float):
            hint = 'number'
        result.append({'name':parameter.name, 'kind':parameter.kind.name,
                       'required':default is parameter.empty, 'default':code, 'hint':hint})
    return result


def form_arguments(parameters, values, references):
    """Build explicit keywords and validate literal/reference inputs locally."""
    pieces = []
    positional = [p for p in parameters if p['kind']=='POSITIONAL_ONLY']
    last = max((i for i,p in enumerate(positional) if values.get(p['name'],('', 'value'))[0].strip()), default=-1)
    for parameter in parameters:
        name = parameter['name']
        raw, mode = values.get(name, ('', 'value'))
        raw = raw.strip()
        if not raw:
            if parameter['required']:
                raise ValueError(f'Bitte „{name}“ ausfüllen.')
            if parameter['kind']=='POSITIONAL_ONLY' and positional.index(parameter) <= last:
                if parameter['default'] is None:
                    raise ValueError(f'Bitte „{name}“ angeben oder die Python-Eingabe verwenden.')
                raw = parameter['default']
            else:
                continue
        if mode=='object':
            if raw not in references:
                raise ValueError(f'Bitte für „{name}“ ein vorhandenes Objekt wählen.')
        elif parameter['hint']=='text':
            try:
                value = ast.literal_eval(raw)
            except (ValueError, SyntaxError):
                value = raw
            if not isinstance(value,str):
                raise ValueError(f'„{name}“ erwartet einen Text.')
            raw = repr(value)
        else:
            try:
                args, _ = arguments(raw, references)
            except (ValueError, SyntaxError) as error:
                raise ValueError(f'„{name}“: Zahl, True/False, Tupel oder Liste eingeben; Objekte über „Objekt“ auswählen.') from error
            if len(args)!=1:
                raise ValueError(f'Bitte für „{name}“ genau einen Wert angeben.')
            value=args[0]
            if parameter['hint']=='number' and (type(value) not in (int,float)):
                raise ValueError(f'„{name}“ erwartet eine Zahl.')
            if parameter['hint']=='boolean' and type(value) is not bool:
                raise ValueError(f'„{name}“ erwartet True oder False.')
        pieces.append(raw if parameter['kind']=='POSITIONAL_ONLY' else name+'='+raw)
    return ', '.join(pieces)
