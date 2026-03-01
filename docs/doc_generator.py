"""
Script
------
doc_generator.py

Path
----
docs/doc_generator.py

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
		self.imported_names: Dict[str, Set[str]] = defaultdict(set)  # name -> modules that import it
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

			# Build import graph and track imported names
			for imp in module.imports:
				if imp.startswith("from"):
					match = re.search(r"from\s+([\w\.]+)\s+import\s+(.*)", imp)
					if match:
						imported_module = match.group(1)
						imported_names = [n.strip() for n in match.group(2).split(",")]
						if imported_module.startswith(("hillstar", ".")):
							self.imports_graph[module_name].add(imported_module)
							for name in imported_names:
								clean = name.strip()
								if clean:
									self.imported_names[clean].add(module_name)

	def get_module_dependencies(self, module_name: str) -> List[str]:
		"""Get modules that a module depends on."""
		return sorted(self.imports_graph.get(module_name, set()))

	def get_importers(self, name: str) -> List[str]:
		"""Get modules that import a given class or function name."""
		return sorted(self.imported_names.get(name, set()))

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

	# Module categories to exclude from generated documentation entirely
	EXCLUDED_CATEGORIES = {"deprecated", "dev", "docs"}

	# Categories handled separately (not in the main category loop)
	SPECIAL_CATEGORIES = {"__init__", "cli"}

	# Category display names
	CATEGORY_NAMES = {
		"config": "Configuration & Provider Registry",
		"execution": "Workflow Execution",
		"governance": "Compliance & Governance",
		"models": "LLM Model Providers",
		"utils": "Utilities",
		"workflows": "Workflow Discovery & Validation",
		"mcp-server": "MCP Servers",
	}

	def __init__(self, package_path: str, setup_py_path: str):
		self.package_path = Path(package_path)
		self.setup_py_path = Path(setup_py_path)
		self.modules: Dict[str, DocModule] = {}
		self.module_hierarchy: Dict[str, List[str]] = defaultdict(list)
		self.cross_ref: Optional[CrossReferenceBuilder] = None

	def _should_include_module(self, module_name: str) -> bool:
		"""Check if a module should be included in documentation."""
		parts = module_name.split(".")
		if len(parts) >= 2:
			category = parts[1]
			if category in self.EXCLUDED_CATEGORIES:
				return False
		# Also skip tmp_test and __pycache__ directories
		if "tmp_test" in module_name or "__pycache__" in module_name:
			return False
		return True

	@staticmethod
	def _clean_docstring(docstring: str) -> str:
		"""Clean a docstring for markdown output.

		Strips RST-style headers, wraps >>> examples in code blocks,
		fixes markdown heading conflicts, and ensures markdownlint compliance.
		"""
		if not docstring:
			return ""

		lines = docstring.split("\n")
		cleaned = []
		i = 0
		in_example_block = False

		while i < len(lines):
			line = lines[i]

			# Detect RST-style underline headers (e.g., "Script\n------\n")
			if (i + 1 < len(lines)
					and lines[i + 1].strip()
					and all(c in "-=~" for c in lines[i + 1].strip())
					and len(lines[i + 1].strip()) >= 3):
				# Convert RST header to bold text
				cleaned.append(f"**{line.strip()}**")
				i += 2  # Skip the underline
				continue

			# Wrap >>> examples in code blocks
			stripped = line.strip()
			if stripped.startswith(">>>"):
				if not in_example_block:
					cleaned.append("")
					cleaned.append("```python")
					in_example_block = True
				cleaned.append(stripped)
			elif in_example_block:
				if stripped and not stripped.startswith(">>>"):
					# Output line (result of example)
					cleaned.append(stripped)
				else:
					# End of example block
					cleaned.append("```")
					cleaned.append("")
					in_example_block = False
					if stripped:
						cleaned.append(stripped)
			else:
				# MD025: Prevent markdown headings from docstrings
				# (# at start of line becomes a heading in markdown)
				if stripped.startswith("#") and not stripped.startswith("#!"):
					line = line.replace("#", "\\#", 1)

				# MD050: Convert underscore bold to asterisk bold
				line = re.sub(r'__(\w+)__', r'**\1**', line)

				cleaned.append(line)

			i += 1

		# Close any open example block
		if in_example_block:
			cleaned.append("```")

		return "\n".join(cleaned)

	def analyze_package(self) -> None:
		"""Analyze all Python files in package."""
		for py_file in sorted(self.package_path.rglob("*.py")):
			# Skip __pycache__ and tests
			if "__pycache__" in str(py_file) or "/tests/" in str(py_file):
				continue

			relative_path = py_file.relative_to(self.package_path.parent)
			module_name = str(relative_path.with_suffix("")).replace("/", ".")

			# Skip excluded modules
			if not self._should_include_module(module_name):
				continue

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
					# Skip special categories (handled separately in Core section)
					if category not in self.SPECIAL_CATEGORIES:
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
		doc.append("# Hillstar API Reference & User Manual\n\n")
		doc.append("| | |\n")
		doc.append("|---|---|\n")
		doc.append(f"| **Package** | {metadata['name']} |\n")
		doc.append(f"| **Version** | {metadata['version']} |\n")
		doc.append(f"| **Description** | {metadata['description']} |\n")
		doc.append(f"| **Author** | {metadata['author']} |\n")
		doc.append(f"| **License** | {metadata['license']} |\n")
		doc.append(f"| **Repository** | <{metadata['url']}> |\n")
		doc.append(f"| **Python** | {metadata['python_requires']} |\n\n")

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
		doc.append("├── config/       - Configuration management\n")
		doc.append("├── execution/    - Workflow execution engine\n")
		doc.append("├── governance/   - Compliance and policy enforcement\n")
		doc.append("├── models/       - LLM provider implementations\n")
		doc.append("├── utils/        - Utilities (logging, tracing, redaction)\n")
		doc.append("├── workflows/    - Workflow discovery and validation\n")
		doc.append("└── cli.py        - Command-line interface\n")
		doc.append("```\n\n")

		# Module Structure
		doc.append("## Module Structure\n\n")

		for category in sorted(self.CATEGORY_NAMES.keys()):
			if category in self.module_hierarchy:
				doc.append(f"### {self.CATEGORY_NAMES[category]}\n\n")
				for module_name in sorted(self.module_hierarchy[category]):
					doc.append(f"- `{module_name}`\n")
				doc.append("\n")

		# API Reference
		doc.append("## API Reference\n\n")

		# Core package first (__init__ and cli modules)
		package_name = self.package_path.name
		init_key = f"{package_name}.__init__"
		cli_key = f"{package_name}.cli"
		has_core = init_key in self.modules or cli_key in self.modules
		if has_core:
			doc.append("### Core\n\n")
			if init_key in self.modules:
				doc.append(self._generate_module_docs(self.modules[init_key]))
			if cli_key in self.modules:
				doc.append(self._generate_module_docs(self.modules[cli_key]))

		# Process modules by category for better organization
		for category in sorted(self.CATEGORY_NAMES.keys()):
			if category not in self.module_hierarchy:
				continue
			doc.append(f"### {self.CATEGORY_NAMES[category]}\n\n")

			for module_name in sorted(self.module_hierarchy[category]):
				# Skip cli (already in Core section)
				if module_name.endswith(".cli"):
					continue
				if module_name in self.modules:
					doc.append(self._generate_module_docs(self.modules[module_name]))

		# Indices
		doc.append(self._generate_class_index())
		doc.append(self._generate_function_index())
		doc.append(self._generate_module_dependencies())

		# Footer
		doc.append("\n---\n\n")
		doc.append("Generated with AST-based documentation generator.\n")
		doc.append("Last Updated: 2026\n")

		raw = "".join(doc)
		return self._markdownlint_clean(raw)

	@staticmethod
	def _markdownlint_clean(markdown: str) -> str:
		"""Post-process markdown to ensure markdownlint compliance.

		Fixes:
		- MD012: No multiple consecutive blank lines
		- MD028: No blank line inside blockquote
		- MD031: Fenced code blocks surrounded by blank lines
		- MD047: Files should end with a single newline
		"""
		# MD012: Collapse multiple consecutive blank lines to one
		while "\n\n\n" in markdown:
			markdown = markdown.replace("\n\n\n", "\n\n")

		lines = markdown.split("\n")
		cleaned = []
		in_fence = False
		i = 0
		while i < len(lines):
			line = lines[i]

			# MD028: Skip blank lines between blockquote lines
			if (i + 2 < len(lines)
					and line.strip().startswith(">")
					and lines[i + 1].strip() == ""
					and lines[i + 2].strip().startswith(">")):
				cleaned.append(line)
				i += 1  # Skip the blank line
				i += 1
				continue

			is_fence = line.strip().startswith("```")

			if is_fence and not in_fence:
				# Opening fence - ensure blank line before it
				if cleaned:
					prev = cleaned[-1].strip() if cleaned else ""
					if prev:
						cleaned.append("")
				in_fence = True
			elif is_fence and in_fence:
				# Closing fence - ensure blank line after it
				in_fence = False

			cleaned.append(line)

			# MD031: Ensure blank line after closing fenced code block
			if (is_fence and not in_fence
					and i + 1 < len(lines)
					and lines[i + 1].strip()):
				cleaned.append("")

			i += 1

		result = "\n".join(cleaned)

		# Clean up any triple blank lines introduced by MD031 fix
		while "\n\n\n" in result:
			result = result.replace("\n\n\n", "\n\n")

		# MD032: Ensure blank lines around lists
		lines2 = result.split("\n")
		result_lines = []
		for line in lines2:
			stripped = line.strip()
			# If this is a list item and prev line is non-empty non-list text
			if (stripped.startswith("- ") or stripped.startswith("* ")
					or re.match(r'^\d+\.\s', stripped)):
				if (result_lines
						and result_lines[-1].strip()
						and not result_lines[-1].strip().startswith("- ")
						and not result_lines[-1].strip().startswith("* ")
						and not re.match(r'^\d+\.\s', result_lines[-1].strip())):
					result_lines.append("")
			result_lines.append(line)
		result = "\n".join(result_lines)

		# Clean up any triple blank lines introduced
		while "\n\n\n" in result:
			result = result.replace("\n\n\n", "\n\n")

		# MD047: Ensure file ends with a single newline
		result = result.rstrip("\n") + "\n"

		return result

	def _format_module_name(self, module_name: str) -> str:
		"""Format module name for display, handling __init__ modules."""
		if module_name.endswith(".__init__"):
			# Show as package name
			package = module_name.rsplit(".__init__", 1)[0]
			return f"{package} (package)"
		return module_name

	def _extract_purpose(self, docstring: str) -> str:
		"""Extract a short purpose line from a docstring.

		Looks for a 'Purpose' RST header section or uses the first
		non-header line.
		"""
		if not docstring:
			return ""

		lines = docstring.strip().split("\n")
		# Look for Purpose section
		for i, line in enumerate(lines):
			if line.strip() == "Purpose" and i + 1 < len(lines) and lines[i + 1].strip().startswith("---"):
				# Return lines after the underline until next section
				purpose_lines = []
				for j in range(i + 2, len(lines)):
					if lines[j].strip() and not (
						j + 1 < len(lines)
						and lines[j + 1].strip()
						and all(c in "-=~" for c in lines[j + 1].strip())
					):
						purpose_lines.append(lines[j].strip())
					else:
						break
				if purpose_lines:
					return " ".join(purpose_lines)

		# Fallback: first non-empty, non-header line
		for i, line in enumerate(lines):
			stripped = line.strip()
			if not stripped:
				continue
			# Skip if next line is an RST underline
			if (i + 1 < len(lines)
					and lines[i + 1].strip()
					and all(c in "-=~" for c in lines[i + 1].strip())):
				continue
			return stripped

		return ""

	@staticmethod
	def _parse_google_docstring(docstring: str) -> Dict[str, str]:
		"""Parse Google-style docstring into structured sections.

		Recognizes: Args, Returns, Raises, Examples, Notes, Yields,
		Attributes, References, See Also.

		Returns a dict with keys like 'summary', 'args', 'returns', etc.
		Each value is the raw text of that section.
		"""
		if not docstring:
			return {"summary": ""}

		sections: Dict[str, str] = {}
		known_headers = {
			"args", "arguments", "parameters", "params",
			"returns", "return",
			"raises", "raise", "except", "exceptions",
			"examples", "example",
			"notes", "note",
			"yields", "yield",
			"attributes", "attrs",
			"references", "see also",
			"warning", "warnings",
			"todo",
		}
		# Normalize header aliases
		header_map = {
			"arguments": "args", "parameters": "args", "params": "args",
			"return": "returns",
			"raise": "raises", "except": "raises", "exceptions": "raises",
			"example": "examples",
			"note": "notes",
			"yield": "yields",
			"attrs": "attributes",
			"warnings": "warning",
		}

		lines = docstring.strip().split("\n")
		# Extract summary (everything before the first section header)
		summary_lines = []
		current_section = None
		current_lines: List[str] = []
		for line in lines:
			stripped = line.strip()
			# Check if this line is a section header (e.g., "Args:" or "Returns:")
			lower = stripped.lower().rstrip(":")
			if lower in known_headers and stripped.endswith(":"):
				if current_section is None:
					sections["summary"] = "\n".join(summary_lines).strip()
				else:
					key = header_map.get(current_section, current_section)
					sections[key] = "\n".join(current_lines).strip()
				current_section = lower
				current_lines = []
			elif current_section is None:
				summary_lines.append(line)
			else:
				current_lines.append(line)

		# Save the last section
		if current_section is not None:
			key = header_map.get(current_section, current_section)
			sections[key] = "\n".join(current_lines).strip()
		elif "summary" not in sections:
			sections["summary"] = "\n".join(summary_lines).strip()

		return sections

	def _build_arg_table(self, func: DocFunction, docstring_sections: Dict[str, str]) -> str:
		"""Build a markdown arguments table merging AST params with docstring descriptions.

		AST provides authoritative types and defaults. Docstring provides
		human-written descriptions for each parameter.
		"""
		params = [p for p in func.parameters if p.name != "self"]
		if not params:
			return ""

		# Parse docstring args section for descriptions
		arg_descriptions: Dict[str, str] = {}
		args_text = docstring_sections.get("args", "")
		if args_text:
			current_arg = None
			current_desc_lines: List[str] = []
			for line in args_text.split("\n"):
				stripped = line.strip()
				# Match "param_name (type): description" or "param_name: description"
				match = re.match(r'^(\w+)\s*(?:\([^)]*\))?\s*:\s*(.*)', stripped)
				if match:
					if current_arg:
						arg_descriptions[current_arg] = " ".join(current_desc_lines).strip()
					current_arg = match.group(1)
					current_desc_lines = [match.group(2)] if match.group(2) else []
				elif current_arg and stripped:
					current_desc_lines.append(stripped)
			if current_arg:
				arg_descriptions[current_arg] = " ".join(current_desc_lines).strip()

		# Build table (escape | in type hints and defaults to avoid breaking table)
		lines = ["| Parameter | Type | Default | Description |",
				 "|-----------|------|---------|-------------|"]
		for p in params:
			name = f"`{p.name}`"
			# Escape pipe characters inside type hints (e.g., "str | None")
			hint_text = p.type_hint.replace("|", "\\|") if p.type_hint else ""
			type_hint = f"`{hint_text}`" if hint_text else "-"
			default_text = p.default.replace("|", "\\|") if p.default else ""
			default = f"`{default_text}`" if default_text else "-"
			# Clean param name for lookup (strip * prefixes)
			clean_name = p.name.lstrip("*")
			desc = arg_descriptions.get(clean_name, "-")
			# Escape pipes in descriptions too
			desc = desc.replace("|", "\\|")
			lines.append(f"| {name} | {type_hint} | {default} | {desc} |")

		return "\n".join(lines) + "\n"

	def _generate_module_docs(self, module: DocModule) -> str:
		"""Generate documentation for a single module."""
		doc = []

		display_name = self._format_module_name(module.name)
		doc.append(f"#### Module: `{display_name}`\n\n")

		if module.docstring:
			purpose = self._extract_purpose(module.docstring)
			if purpose:
				doc.append(f"{purpose}\n\n")

		# Constants
		if module.constants:
			doc.append("**Constants:**\n\n")
			for name, value in module.constants.items():
				doc.append(f"- `{name}` = {repr(value)}\n")
			doc.append("\n")

		# Classes
		for cls in module.classes:
			if not cls.is_private:
				doc.append(self._generate_class_docs(cls, module.name))

		# Functions (each gets its own structured section)
		public_funcs = [f for f in module.functions if not f.is_private]
		if public_funcs:
			for func in public_funcs:
				doc.append(self._generate_function_docs(func))

		doc.append("\n---\n\n")
		return "".join(doc)

	@staticmethod
	def _gfm_anchor(heading_text: str) -> str:
		"""Generate a GitHub Flavored Markdown compatible anchor from heading text.

		GitHub's algorithm: lowercase, spaces to hyphens, strip non-alphanumeric
		characters except hyphens.
		"""
		anchor = heading_text.lower()
		anchor = anchor.replace(" ", "-")
		anchor = re.sub(r'[^a-z0-9\-]', '', anchor)
		# Collapse multiple hyphens
		anchor = re.sub(r'-+', '-', anchor)
		return anchor.strip("-")

	def _generate_class_docs(self, cls: DocClass, _module_name: str = "") -> str:
		"""Generate structured documentation for a class.

		Gives __init__ constructor full structured treatment (signature,
		args table). Other methods stay compact as bullet list.
		"""
		doc = []

		# Class heading uses just the name for predictable GFM anchors
		doc.append(f"##### class {cls.name}\n\n")

		# Show inheritance in body if applicable
		if cls.bases:
			doc.append(f"Extends: `{', '.join(cls.bases)}`\n\n")

		if cls.docstring:
			cleaned = self._clean_docstring(cls.docstring)
			purpose = self._extract_purpose(cls.docstring)
			if purpose and len(purpose) < 200:
				doc.append(f"{purpose}\n\n")
			elif cleaned:
				first_para = cleaned.split("\n\n")[0]
				doc.append(f"{first_para}\n\n")

		# Constructor (__init__) gets structured treatment
		init_method = None
		for m in cls.methods:
			if m.name == "__init__":
				init_method = m
				break

		if init_method:
			non_self_params = [p for p in init_method.parameters if p.name != "self"]
			if non_self_params:
				doc.append("**Constructor:**\n\n")
				doc.append(f"```python\n{init_method.signature}\n```\n\n")
				sections = self._parse_google_docstring(init_method.docstring)
				doc.append(self._build_arg_table(init_method, sections))
				doc.append("\n")

		# Properties
		public_props = [p for p in cls.properties if not p.is_private]
		if public_props:
			doc.append("**Properties:**\n\n")
			for prop in public_props:
				doc.append(f"- `{prop.name}`")
				if prop.return_type:
					doc.append(f" -> `{prop.return_type}`")
				doc.append("\n")
				if prop.docstring:
					cleaned = self._clean_docstring(prop.docstring)
					first_line = cleaned.split("\n")[0].strip()
					if first_line:
						doc.append(f"  {first_line}\n")
			doc.append("\n")

		# Methods (excluding __init__ and private)
		public_methods = [m for m in cls.methods
						  if not m.is_private and m.name != "__init__"]
		if public_methods:
			doc.append("**Methods:**\n\n")
			for method in public_methods:
				# Compact format: signature + first-line description
				doc.append(f"- `{method.signature}`\n")
				if method.docstring:
					sections = self._parse_google_docstring(method.docstring)
					summary = sections.get("summary", "")
					if summary:
						first_line = summary.split("\n")[0].strip()
						if first_line:
							doc.append(f"  {first_line}\n")
			doc.append("\n")

		# Cross-references (used in)
		if self.cross_ref:
			importers = self.cross_ref.get_importers(cls.name)
			if importers:
				doc.append(f"**Used in:** {', '.join(f'`{m}`' for m in importers)}\n\n")

		return "".join(doc)

	def _generate_function_docs(self, func: DocFunction) -> str:
		"""Generate structured documentation for a module-level function.

		Produces: heading, signature code block, description, arguments table,
		returns section, and cross-references.
		"""
		doc = []

		# Function heading
		doc.append(f"##### {func.name}\n\n")

		# Signature code block
		doc.append(f"```python\n{func.signature}\n```\n\n")

		# Parse docstring sections
		sections = self._parse_google_docstring(func.docstring)

		# Description
		summary = sections.get("summary", "")
		if summary:
			cleaned = self._clean_docstring(summary)
			doc.append(f"{cleaned}\n\n")

		# Arguments table
		non_self_params = [p for p in func.parameters if p.name != "self"]
		if non_self_params:
			doc.append("**Arguments:**\n\n")
			doc.append(self._build_arg_table(func, sections))
			doc.append("\n")

		# Returns
		returns_text = sections.get("returns", "")
		if returns_text or func.return_type:
			doc.append("**Returns:**\n\n")
			if func.return_type:
				desc = self._clean_docstring(returns_text) if returns_text else ""
				if desc:
					doc.append(f"`{func.return_type}` - {desc}\n\n")
				else:
					doc.append(f"`{func.return_type}`\n\n")
			elif returns_text:
				doc.append(f"{self._clean_docstring(returns_text)}\n\n")

		# Raises
		raises_text = sections.get("raises", "")
		if raises_text:
			doc.append("**Raises:**\n\n")
			for line in raises_text.split("\n"):
				stripped = line.strip()
				if stripped:
					doc.append(f"- {stripped}\n")
			doc.append("\n")

		# Examples
		examples_text = sections.get("examples", "")
		if examples_text:
			doc.append("**Examples:**\n\n")
			cleaned = self._clean_docstring(examples_text)
			doc.append(f"{cleaned}\n\n")

		# Cross-references (used in)
		if self.cross_ref:
			importers = self.cross_ref.get_importers(func.name)
			if importers:
				doc.append(f"**Used in:** {', '.join(f'`{m}`' for m in importers)}\n\n")

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
				# Build heading text that matches _generate_class_docs output
				heading = f"class {cls_name}"
				anchor = self._gfm_anchor(heading)
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
				# Escape __init__ in headings to prevent MD050 (underscore bold)
				display = module_name.replace("__", r"\_\_")
				doc.append(f"### {display}\n\n")
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
