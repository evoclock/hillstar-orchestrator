"""
Script
------
doc_generator.py

Path
----
python/hillstar/utils/doc_generator.py

Purpose
-------
AST-based User Manual documentation generator for Hillstar.

This module provides comprehensive documentation generation from Python source code
using the ast module. It parses all Python files in a package and generates structured
markdown documentation with full type hints, docstrings, hierarchical organization,
cross-references, module dependencies, and searchable indices for the User Manual.

Features:
- Complete AST-based analysis of all classes, functions, methods, properties
- Cross-references between modules and components
- Module dependency graph and analysis
- Comprehensive class and function indices
- Searchable markdown sections with proper anchor links

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re


@dataclass
class DocParameter:
    """Represents a function/method parameter with type information."""
    name: str
    type_hint: str
    default: Optional[str] = None

    def __str__(self) -> str:
        result = f"{self.name}"
        if self.type_hint:
            result += f": {self.type_hint}"
        if self.default is not None:
            result += f" = {self.default}"
        return result


@dataclass
class DocFunction:
    """Represents a function or method with metadata."""
    name: str
    module: str
    signature: str
    docstring: str
    parameters: List[DocParameter]
    return_type: str
    decorators: List[str]
    is_method: bool = False
    is_private: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False


@dataclass
class DocClass:
    """Represents a class with methods and properties."""
    name: str
    module: str
    docstring: str
    bases: List[str]
    methods: List[DocFunction]
    properties: List[DocFunction]
    decorators: List[str]
    is_abstract: bool = False
    is_private: bool = False


@dataclass
class DocModule:
    """Represents a module with its contents."""
    name: str
    path: str
    docstring: str
    classes: List[DocClass]
    functions: List[DocFunction]
    imports: List[str]
    constants: Dict[str, Any]


class CrossReferenceBuilder:
    """Builds cross-references between modules, classes, and functions."""

    def __init__(self, modules_data: Dict[str, DocModule]):
        self.modules_data = modules_data
        self.class_index: Dict[str, str] = {}  # class_name -> module
        self.function_index: Dict[str, str] = {}  # function_name -> module
        self.imports_graph: Dict[str, Set[str]] = defaultdict(set)  # module -> imported modules
        self._build_indices()

    def _build_indices(self) -> None:
        """Build indices from module data."""
        for module_name, module in self.modules_data.items():
            # Index classes
            for cls in module.classes:
                self.class_index[cls.name] = module_name

            # Index functions
            for func in module.functions:
                self.function_index[func.name] = module_name

            # Build import graph
            for imp in module.imports:
                # Extract module names from import statements
                if imp.startswith("from"):
                    match = re.search(r"from\s+([\w\.]+)", imp)
                    if match:
                        imported = match.group(1)
                        if imported.startswith("hillstar"):
                            self.imports_graph[module_name].add(imported)

    def get_module_dependencies(self, module_name: str) -> List[str]:
        """Get modules that a module depends on."""
        return sorted(self.imports_graph.get(module_name, set()))

    def find_related_types(self, type_name: str) -> List[Tuple[str, str]]:
        """Find modules and items using or returning a type."""
        results = []
        for class_name, module in self.class_index.items():
            if type_name.lower() in class_name.lower():
                results.append((module, class_name))
        return results


class ASTAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST to extract documentation information."""

    def __init__(self, module_name: str, source_path: str):
        self.module_name = module_name
        self.source_path = source_path
        self.current_class: Optional[str] = None
        self.classes: Dict[str, DocClass] = {}
        self.functions: List[DocFunction] = []
        self.imports: List[str] = []
        self.constants: Dict[str, Any] = {}
        self.module_docstring = ""

    def get_decorator_names(self, node: Any) -> List[str]:
        """Extract decorator names from a node."""
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    decorators.append(decorator.func.attr)
        return decorators

    def get_type_annotation(self, annotation: Optional[Any]) -> str:
        """Convert annotation AST node to string."""
        if annotation is None:
            return ""

        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return repr(annotation.value)
        elif isinstance(annotation, ast.Attribute):
            value = self.get_type_annotation(annotation.value)
            return f"{value}.{annotation.attr}" if value else annotation.attr
        elif isinstance(annotation, ast.Subscript):
            value = self.get_type_annotation(annotation.value)
            slice_val = self.get_type_annotation(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Tuple):
            elements = [self.get_type_annotation(e) for e in annotation.elts]
            return f"({', '.join(elements)})"
        elif isinstance(annotation, ast.List):
            elements = [self.get_type_annotation(e) for e in annotation.elts]
            return f"[{', '.join(elements)}]"
        elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = self.get_type_annotation(annotation.left)
            right = self.get_type_annotation(annotation.right)
            return f"{left} | {right}"

        return ast.unparse(annotation) if hasattr(ast, 'unparse') else ""

    def get_default_value(self, default: Optional[Any]) -> Optional[str]:
        """Convert default value AST node to string."""
        if default is None:
            return None

        if isinstance(default, ast.Constant):
            if default.value is None:
                return "None"
            elif isinstance(default.value, str):
                return repr(default.value)
            else:
                return str(default.value)
        elif isinstance(default, ast.List):
            return "[]"
        elif isinstance(default, ast.Dict):
            return "{}"
        elif isinstance(default, ast.Name):
            return default.id

        return ast.unparse(default) if hasattr(ast, 'unparse') else None

    def visit_Module(self, node: ast.Module) -> None:
        """Visit module node."""
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            if isinstance(node.body[0].value.value, str):
                self.module_docstring = node.body[0].value.value
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            self.imports.append(f"import {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statement."""
        module = node.module or ""
        names = ", ".join(alias.name for alias in node.names)
        self.imports.append(f"from {module} import {names}")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        docstring = ast.get_docstring(node) or ""
        bases = [self.get_type_annotation(base) for base in node.bases]
        decorators = self.get_decorator_names(node)
        is_abstract = "abstractmethod" in decorators or any("ABC" in str(b) for b in bases)

        methods = []
        properties = []

        # Save current class name
        old_class = self.current_class
        self.current_class = node.name

        # Process class body
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                func_decorators = self.get_decorator_names(item)
                func_docstring = ast.get_docstring(item) or ""
                params = self._extract_parameters(item)
                return_type = self.get_type_annotation(item.returns)
                signature = self._build_signature(item.name, params, return_type)

                is_property = "property" in func_decorators
                is_classmethod = "classmethod" in func_decorators
                is_staticmethod = "staticmethod" in func_decorators
                is_private = item.name.startswith("_") and not item.name.startswith("__")

                func = DocFunction(
                    name=item.name,
                    module=self.module_name,
                    signature=signature,
                    docstring=func_docstring,
                    parameters=params,
                    return_type=return_type,
                    decorators=func_decorators,
                    is_method=True,
                    is_private=is_private,
                    is_classmethod=is_classmethod,
                    is_staticmethod=is_staticmethod,
                    is_property=is_property
                )

                if is_property:
                    properties.append(func)
                else:
                    methods.append(func)

        self.current_class = old_class

        doc_class = DocClass(
            name=node.name,
            module=self.module_name,
            docstring=docstring,
            bases=bases,
            methods=methods,
            properties=properties,
            decorators=decorators,
            is_abstract=is_abstract,
            is_private=node.name.startswith("_")
        )

        self.classes[node.name] = doc_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        # Skip functions inside classes (handled in visit_ClassDef)
        if self.current_class is None:
            docstring = ast.get_docstring(node) or ""
            params = self._extract_parameters(node)
            return_type = self.get_type_annotation(node.returns)
            decorators = self.get_decorator_names(node)
            signature = self._build_signature(node.name, params, return_type)

            func = DocFunction(
                name=node.name,
                module=self.module_name,
                signature=signature,
                docstring=docstring,
                parameters=params,
                return_type=return_type,
                decorators=decorators,
                is_private=node.name.startswith("_")
            )

            self.functions.append(func)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        if self.current_class is None:
            docstring = ast.get_docstring(node) or ""
            params = self._extract_parameters(node)
            return_type = self.get_type_annotation(node.returns)
            decorators = self.get_decorator_names(node)
            signature = f"async {self._build_signature(node.name, params, return_type)}"

            func = DocFunction(
                name=node.name,
                module=self.module_name,
                signature=signature,
                docstring=docstring,
                parameters=params,
                return_type=return_type,
                decorators=decorators,
                is_private=node.name.startswith("_")
            )

            self.functions.append(func)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment (constants/globals)."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                if isinstance(node.value, ast.Constant):
                    self.constants[target.id] = node.value.value
                elif isinstance(node.value, ast.List):
                    self.constants[target.id] = "[]"
                elif isinstance(node.value, ast.Dict):
                    self.constants[target.id] = "{}"

        self.generic_visit(node)

    def _extract_parameters(self, node: Any) -> List[DocParameter]:
        """Extract function parameters."""
        params = []
        args = node.args

        # Positional arguments
        for i, arg in enumerate(args.args):
            type_hint = self.get_type_annotation(arg.annotation)
            default = None
            # Calculate default value index
            default_offset = len(args.args) - len(args.defaults)
            if i >= default_offset:
                default = self.get_default_value(args.defaults[i - default_offset])

            params.append(DocParameter(name=arg.arg, type_hint=type_hint, default=default))

        # *args
        if args.vararg:
            type_hint = self.get_type_annotation(args.vararg.annotation)
            params.append(DocParameter(name=f"*{args.vararg.arg}", type_hint=type_hint))

        # Keyword-only arguments
        for i, arg in enumerate(args.kwonlyargs):
            type_hint = self.get_type_annotation(arg.annotation)
            default = self.get_default_value(args.kw_defaults[i])
            params.append(DocParameter(name=arg.arg, type_hint=type_hint, default=default))

        # **kwargs
        if args.kwarg:
            type_hint = self.get_type_annotation(args.kwarg.annotation)
            params.append(DocParameter(name=f"**{args.kwarg.arg}", type_hint=type_hint))

        return params

    def _build_signature(self, name: str, params: List[DocParameter], return_type: str) -> str:
        """Build function signature string."""
        param_str = ", ".join(str(p) for p in params)
        sig = f"{name}({param_str})"
        if return_type:
            sig += f" -> {return_type}"
        return sig


class DocumentationGenerator:
    """Generates comprehensive markdown documentation from Python packages."""

    def __init__(self, package_path: str, setup_py_path: str):
        self.package_path = Path(package_path)
        self.setup_py_path = Path(setup_py_path)
        self.modules: Dict[str, DocModule] = {}
        self.module_hierarchy: Dict[str, List[str]] = defaultdict(list)
        self.cross_ref: Optional[CrossReferenceBuilder] = None

    def analyze_package(self) -> None:
        """Analyze all Python files in package."""
        for py_file in sorted(self.package_path.rglob("*.py")):
            # Skip __pycache__ and tests
            if "__pycache__" in str(py_file) or "/tests/" in str(py_file):
                continue

            relative_path = py_file.relative_to(self.package_path.parent)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()

                tree = ast.parse(source)
                analyzer = ASTAnalyzer(module_name, str(py_file))
                analyzer.visit(tree)

                # Extract imports from source
                imports = []
                for line in source.split("\n")[:50]:  # First 50 lines
                    if line.strip().startswith(("import ", "from ")):
                        imports.append(line.strip())

                doc_module = DocModule(
                    name=module_name,
                    path=str(py_file),
                    docstring=analyzer.module_docstring,
                    classes=list(analyzer.classes.values()),
                    functions=analyzer.functions,
                    imports=imports,
                    constants=analyzer.constants
                )

                self.modules[module_name] = doc_module

                # Organize by category
                parts = module_name.split(".")
                if len(parts) >= 2:
                    category = parts[1]
                    self.module_hierarchy[category].append(module_name)

            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")

    def extract_setup_metadata(self) -> Dict[str, Any]:
        """Extract metadata from setup.py."""
        metadata = {
            "name": "",
            "version": "",
            "description": "",
            "author": "",
            "author_email": "",
            "url": "",
            "license": "",
            "dependencies": [],
            "python_requires": ""
        }

        try:
            with open(self.setup_py_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple regex extraction
            patterns = {
                "name": r'name\s*=\s*["\']([^"\']+)["\']',
                "version": r'version\s*=\s*["\']([^"\']+)["\']',
                "description": r'description\s*=\s*["\']([^"\']+)["\']',
                "author": r'author\s*=\s*["\']([^"\']+)["\']',
                "author_email": r'author_email\s*=\s*["\']([^"\']+)["\']',
                "url": r'url\s*=\s*["\']([^"\']+)["\']',
                "license": r'license\s*=\s*["\']([^"\']+)["\']',
                "python_requires": r'python_requires\s*=\s*["\']([^"\']+)["\']',
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    metadata[key] = match.group(1)

            # Extract dependencies
            install_requires_match = re.search(
                r'install_requires\s*=\s*\[(.*?)\]',
                content,
                re.DOTALL
            )
            if install_requires_match:
                deps_str = install_requires_match.group(1)
                deps = re.findall(r'["\']([^"\']+)["\']', deps_str)
                metadata["dependencies"] = deps

        except Exception as e:
            print(f"Error extracting setup metadata: {e}")

        return metadata

    def generate_markdown(self) -> str:
        """Generate comprehensive markdown documentation."""
        # Initialize cross-reference builder
        self.cross_ref = CrossReferenceBuilder(self.modules)

        metadata = self.extract_setup_metadata()
        doc = []

        # Header
        doc.append("# Hillstar API Reference\n")
        doc.append(f"**Package:** {metadata['name']}\n")
        doc.append(f"**Version:** {metadata['version']}\n")
        doc.append(f"**Description:** {metadata['description']}\n")
        doc.append(f"**Author:** {metadata['author']} ({metadata['author_email']})\n")
        doc.append(f"**License:** {metadata['license']}\n")
        doc.append(f"**Repository:** {metadata['url']}\n")
        doc.append(f"**Python:** {metadata['python_requires']}\n\n")

        # Table of Contents
        doc.append("## Table of Contents\n\n")
        doc.append("1. [Overview](#overview)\n")
        doc.append("2. [Installation & Dependencies](#installation--dependencies)\n")
        doc.append("3. [Architecture](#architecture)\n")
        doc.append("4. [Module Structure](#module-structure)\n")
        doc.append("5. [API Reference](#api-reference)\n")
        doc.append("6. [Class Index](#class-index)\n")
        doc.append("7. [Function Index](#function-index)\n")
        doc.append("8. [Module Dependencies](#module-dependencies)\n\n")

        # Overview
        doc.append("## Overview\n\n")
        doc.append("Hillstar is a research-grade workflow orchestration system designed for ")
        doc.append("multi-agent AI pipelines and classification tasks. It provides a modular ")
        doc.append("architecture with support for multiple LLM providers, governance policies, ")
        doc.append("and comprehensive execution tracing.\n\n")

        # Installation & Dependencies
        doc.append("## Installation & Dependencies\n\n")
        doc.append("```bash\n")
        doc.append("pip install hillstar-orchestrator\n")
        doc.append("```\n\n")
        doc.append("### Core Dependencies\n\n")
        for dep in metadata.get("dependencies", []):
            doc.append(f"- `{dep}`\n")
        doc.append("\n")

        # Architecture
        doc.append("## Architecture\n\n")
        doc.append("Hillstar consists of several key components:\n\n")
        doc.append("```text\nhillstar/\n")
        doc.append("├── config/          - Configuration management\n")
        doc.append("├── execution/       - Workflow execution engine\n")
        doc.append("├── governance/      - Compliance and policy enforcement\n")
        doc.append("├── models/          - LLM provider implementations\n")
        doc.append("├── utils/           - Utilities (logging, tracing, redaction)\n")
        doc.append("├── workflows/       - Workflow discovery and validation\n")
        doc.append("└── cli.py           - Command-line interface\n")
        doc.append("```\n\n")

        # Module Structure
        doc.append("## Module Structure\n\n")

        categories = {
            "config": "Configuration & Provider Registry",
            "execution": "Workflow Execution",
            "governance": "Compliance & Governance",
            "models": "LLM Model Providers",
            "utils": "Utilities",
            "workflows": "Workflow Discovery & Validation"
        }

        for category in sorted(categories.keys()):
            if category in self.module_hierarchy:
                doc.append(f"### {categories.get(category, category.title())}\n\n")
                for module_name in sorted(self.module_hierarchy[category]):
                    doc.append(f"- `{module_name}`\n")
                doc.append("\n")

        # Core modules
        if "hillstar" in self.modules:
            doc.append("### Core\n\n")
            doc.append("- `hillstar` (main package)\n")
            doc.append("- `hillstar.cli` (command-line interface)\n\n")

        # API Reference
        doc.append("## API Reference\n\n")

        # Process modules by category for better organization
        for category in sorted(self.module_hierarchy.keys()):
            category_name = categories.get(category, category.title())
            doc.append(f"### {category_name}\n\n")

            for module_name in sorted(self.module_hierarchy[category]):
                if module_name in self.modules:
                    doc.append(self._generate_module_docs(self.modules[module_name]))

        # Main package
        if "hillstar" in self.modules:
            doc.append("### Core\n\n")
            doc.append(self._generate_module_docs(self.modules["hillstar"]))

        if "hillstar.cli" in self.modules:
            doc.append(self._generate_module_docs(self.modules["hillstar.cli"]))

        # Indices
        doc.append(self._generate_class_index())
        doc.append(self._generate_function_index())
        doc.append(self._generate_module_dependencies())

        # Footer
        doc.append("\n---\n\n")
        doc.append("*Generated with AST-based documentation generator*\n")
        doc.append("*Last Updated: 2026*\n")

        return "".join(doc)

    def _generate_module_docs(self, module: DocModule) -> str:
        """Generate documentation for a single module."""
        doc = []

        doc.append(f"#### Module: `{module.name}`\n\n")

        if module.docstring:
            doc.append(f"*{module.docstring}*\n\n")

        # Imports
        if module.imports:
            doc.append("**Imports:**\n\n")
            doc.append("```python\n")
            for imp in module.imports[:10]:  # Limit to first 10
                doc.append(f"{imp}\n")
            if len(module.imports) > 10:
                doc.append(f"# ... and {len(module.imports) - 10} more imports\n")
            doc.append("```\n\n")

        # Constants
        if module.constants:
            doc.append("**Constants:**\n\n")
            for name, value in module.constants.items():
                doc.append(f"- `{name}` = {repr(value)}\n")
            doc.append("\n")

        # Classes
        if module.classes:
            doc.append("**Classes:**\n\n")
            for cls in module.classes:
                if not cls.is_private:
                    doc.append(self._generate_class_docs(cls, module.name))

        # Functions
        if module.functions:
            doc.append("**Functions:**\n\n")
            for func in module.functions:
                if not func.is_private:
                    doc.append(self._generate_function_docs(func))

        doc.append("\n")
        return "".join(doc)

    def _generate_class_docs(self, cls: DocClass, module_name: str = "") -> str:
        """Generate documentation for a class."""
        doc = []

        # Class signature
        sig = f"class {cls.name}"
        if cls.bases:
            sig += f"({', '.join(cls.bases)})"
        # Create explicit anchor for class documentation matching index format
        if module_name:
            anchor = f"{module_name}-{cls.name}".replace(".", "-").lower()
        else:
            anchor = cls.name.lower()
        doc.append(f"##### `{sig}` {{#{anchor}}}\n\n")

        if cls.docstring:
            doc.append(f"{cls.docstring}\n\n")

        # Properties
        if cls.properties:
            doc.append("*Properties:*\n\n")
            for prop in cls.properties:
                if not prop.is_private:
                    doc.append(f"- `{prop.name}` -> {prop.return_type}\n")
                    if prop.docstring:
                        doc.append(f"  {prop.docstring}\n")
            doc.append("\n")

        # Methods
        if cls.methods:
            doc.append("*Methods:*\n\n")
            for method in cls.methods:
                if not method.is_private:
                    doc.append(f"- `{method.signature}`\n")
                    if method.docstring:
                        doc.append(f"  {method.docstring}\n")
            doc.append("\n")

        return "".join(doc)

    def _generate_function_docs(self, func: DocFunction) -> str:
        """Generate documentation for a function."""
        doc = []

        doc.append(f"- `{func.signature}`\n")

        if func.docstring:
            doc.append(f"  {func.docstring}\n")

        return "".join(doc)

    def _generate_class_index(self) -> str:
        """Generate index of all classes."""
        if not self.cross_ref:
            return ""

        doc = ["## Class Index\n\n"]

        classes_by_module = defaultdict(list)
        for class_name, module_name in sorted(self.cross_ref.class_index.items()):
            classes_by_module[module_name].append(class_name)

        for module_name in sorted(classes_by_module.keys()):
            classes = sorted(classes_by_module[module_name])
            doc.append(f"### {module_name}\n\n")
            for cls_name in classes:
                anchor = f"{module_name}-{cls_name}".replace(".", "-").lower()
                doc.append(f"- [{cls_name}](#{anchor})\n")
            doc.append("\n")

        return "".join(doc)

    def _generate_function_index(self) -> str:
        """Generate index of all functions."""
        if not self.cross_ref:
            return ""

        doc = ["## Function Index\n\n"]

        functions_by_module = defaultdict(list)
        for func_name, module_name in sorted(self.cross_ref.function_index.items()):
            functions_by_module[module_name].append(func_name)

        for module_name in sorted(functions_by_module.keys()):
            functions = sorted(functions_by_module[module_name])
            doc.append(f"### {module_name}\n\n")
            for func_name in functions:
                doc.append(f"- `{func_name}()`\n")
            doc.append("\n")

        return "".join(doc)

    def _generate_module_dependencies(self) -> str:
        """Generate module dependency graph."""
        if not self.cross_ref:
            return ""

        doc = ["## Module Dependencies\n\n"]

        for module_name in sorted(self.modules.keys()):
            deps = self.cross_ref.get_module_dependencies(module_name)
            if deps:
                doc.append(f"### {module_name}\n\n")
                doc.append("Depends on:\n\n")
                for dep in deps:
                    doc.append(f"- `{dep}`\n")
                doc.append("\n")

        return "".join(doc)

    def save_documentation(self, output_path: str) -> None:
        """Save generated documentation to file."""
        markdown = self.generate_markdown()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"Documentation saved to {output_path}")


def generate_user_manual(
    package_path: str = "/home/jgamboa/hillstar-orchestrator",
    setup_py_path: str = "/home/jgamboa/agentic-orchestrator/python/setup.py",
    output_path: str = "/home/jgamboa/hillstar-orchestrator/docs/User_Manual.md"
) -> None:
    """Generate User Manual documentation for Hillstar package."""
    generator = DocumentationGenerator(package_path, setup_py_path)
    generator.analyze_package()
    generator.save_documentation(output_path)


if __name__ == "__main__":
    generate_user_manual()
