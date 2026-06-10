"""Generate pytest cases from Python code blocks in the Sphinx docs."""

from __future__ import annotations

import argparse
import ast
import builtins
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs" / "source"
GENERATED_ROOT = REPO_ROOT / "test" / "generated" / "docs_examples"
FENCED_BLOCK_RE = re.compile(
    r"(?P<indent>^[ \t]*)```(?P<info>[^\n`]*)\n(?P<code>.*?)(?P=indent)```",
    re.MULTILINE | re.DOTALL,
)
PYTHON_INFOS = {"python", "py", "python3"}


@dataclass(frozen=True)
class DocExample:
    docs_path: str
    line: int
    block_index: int
    test_file: str


@dataclass(frozen=True)
class SkippedDocExample:
    docs_path: str
    line: int
    block_index: int
    reason: str


class UndefinedNameVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.scopes: list[set[str]] = [set()]
        self.undefined: set[str] = set()
        self.allowed_names = set(dir(builtins)) | {"__name__", "__file__"}

    def _is_defined(self, name: str) -> bool:
        return name in self.allowed_names or any(name in scope for scope in reversed(self.scopes))

    def _define(self, name: str) -> None:
        self.scopes[-1].add(name)

    def _define_target(self, target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            self._define(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._define_target(element)
        elif isinstance(target, ast.Starred):
            self._define_target(target.value)
        elif isinstance(target, ast.Attribute):
            self.visit(target.value)
        elif isinstance(target, ast.Subscript):
            self.visit(target.value)
            self.visit(target.slice)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and not self._is_defined(node.id):
            self.undefined.add(node.id)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._define(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name != "*":
                self._define(alias.asname or alias.name)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            self._define_target(target)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
        self._define_target(node.target)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit(node.target)
        self.visit(node.value)

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._define_target(node.target)
        for statement in node.body + node.orelse:
            self.visit(statement)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._define_target(item.optional_vars)
        for statement in node.body:
            self.visit(statement)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in node.args.defaults + node.args.kw_defaults:
            if default is not None:
                self.visit(default)
        self._define(node.name)
        names = {arg.arg for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs}
        if node.args.vararg is not None:
            names.add(node.args.vararg.arg)
        if node.args.kwarg is not None:
            names.add(node.args.kwarg.arg)
        self.scopes.append(names)
        for statement in node.body:
            self.visit(statement)
        self.scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self._define(node.name)
        self.scopes.append(set())
        for statement in node.body:
            self.visit(statement)
        self.scopes.pop()


def _skip_reason(code: str) -> str | None:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return f"syntax example: {error.msg}"
    if any(
        isinstance(node, ast.While)
        and isinstance(node.test, ast.Constant)
        and node.test.value is True
        for node in ast.walk(tree)
    ):
        return "infinite loop example"
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input" for node in ast.walk(tree)):
        return "interactive input example"
    visitor = UndefinedNameVisitor()
    visitor.visit(tree)
    if visitor.undefined:
        names = ", ".join(sorted(visitor.undefined))
        return f"depends on external names: {names}"
    return None


def _is_python_block(info: str) -> bool:
    info = info.strip()
    if not info:
        return False
    language = info.split()[0]
    return language in PYTHON_INFOS


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _slug_for_path(path: Path) -> str:
    relative = path.relative_to(DOCS_ROOT).with_suffix("")
    return re.sub(r"[^a-zA-Z0-9]+", "_", relative.as_posix()).strip("_").lower()


def _iter_doc_examples() -> tuple[list[tuple[DocExample, str]], list[SkippedDocExample]]:
    examples: list[tuple[DocExample, str]] = []
    skipped: list[SkippedDocExample] = []
    for docs_path in sorted(DOCS_ROOT.rglob("*.md")):
        content = docs_path.read_text(encoding="utf-8")
        block_index = 0
        for match in FENCED_BLOCK_RE.finditer(content):
            if not _is_python_block(match.group("info")):
                continue
            block_index += 1
            code = match.group("code").strip("\n")
            if not code.strip():
                continue
            line = _line_number(content, match.start())
            reason = _skip_reason(code)
            if reason is not None:
                skipped.append(
                    SkippedDocExample(
                        docs_path=docs_path.relative_to(REPO_ROOT).as_posix(),
                        line=line,
                        block_index=block_index,
                        reason=reason,
                    )
                )
                continue
            slug = _slug_for_path(docs_path)
            test_file = f"{slug}__block_{block_index:03d}_line_{line}.py"
            example = DocExample(
                docs_path=docs_path.relative_to(REPO_ROOT).as_posix(),
                line=line,
                block_index=block_index,
                test_file=test_file,
            )
            examples.append((example, code))
    return examples, skipped


def _generated_test_module() -> str:
    return '''"""Generated pytest entry point for documentation examples."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from test.unittests.integration.doc_example_runner import run_doc_example_script


ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


@pytest.mark.unit
@pytest.mark.parametrize("entry", MANIFEST, ids=lambda entry: entry["test_file"])
def test_generated_doc_example(entry):
    run_doc_example_script(ROOT / entry["test_file"], entry)
'''


def generate_doc_example_tests(output_root: Path = GENERATED_ROOT) -> tuple[list[DocExample], list[SkippedDocExample]]:
    examples, skipped = _iter_doc_examples()
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    manifest: list[dict[str, object]] = []
    for example, code in examples:
        target = output_root / example.test_file
        header = (
            f"# Generated from {example.docs_path}:{example.line}\n"
            "# Regenerate with: invoke docs.examples\n\n"
        )
        target.write_text(header + code + "\n", encoding="utf-8")
        manifest.append(asdict(example))

    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "skipped_manifest.json").write_text(
        json.dumps([asdict(example) for example in skipped], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "test_generated_doc_examples.py").write_text(
        _generated_test_module(),
        encoding="utf-8",
    )
    (output_root / "__init__.py").write_text("", encoding="utf-8")
    return [example for example, _code in examples], skipped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        default=GENERATED_ROOT,
        type=Path,
        help="Directory for generated pytest files.",
    )
    args = parser.parse_args()
    examples, skipped = generate_doc_example_tests(args.output_root)
    print(
        f"Generated {len(examples)} documentation example tests in {args.output_root}; "
        f"skipped {len(skipped)} non-standalone snippets"
    )


if __name__ == "__main__":
    main()
