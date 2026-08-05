# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Bounded iteration, compiled into the DAG before execution.

An implementer-reviewer cycle is the shape most real work takes: write, review,
apply the revisions, review again. Expressed as a back edge it is a cycle, and
the executor rejects cycles for good reason — an unbounded loop in an agent
graph is an unbounded bill.

So iteration is declared, not drawn: a `loop` block names the body, a maximum
number of attempts, and the condition that ends it early. This module expands
that into ordinary nodes and forward edges. Everything downstream — topological
sort, checkpoints, tracing, the DAG pane — keeps working unchanged, because
what it receives is a DAG.

Bounding is the point. `max_attempts` is required and finite, so the worst case
is stated in the workflow rather than discovered from a bill.

    "loops": [
      {
        "id": "fix",
        "body": ["implement", "review"],
        "max_attempts": 3,
        "until": {"node": "review", "contains": "sign-off"},
        "on_exhausted": "escalate"
      }
    ]

Attempt 1 is the nodes as authored. Attempts 2..n are copies suffixed `@2`,
`@3`, each carrying a `skip_if` naming the previous attempt's exit check: if
the loop has already succeeded, the later attempts are skipped at run time
rather than run and discarded.
"""

from __future__ import annotations

import re
from typing import Any, Mapping


class LoopError(ValueError):
	"""A loop declaration that cannot be compiled."""


def _suffixed(node_id: str, attempt: int) -> str:
	return node_id if attempt == 1 else f"{node_id}@{attempt}"


def _rewrite_references(value: Any, body: set[str], attempt: int) -> Any:
	"""Point `{{ node.output }}` at this attempt's copy of a body node.

	`{{ prev.node.output }}` instead names the PREVIOUS attempt. That is what
	carries a review back to the implementer: without it the second attempt
	would reference its own review, which has not run yet, and the implementer
	would simply repeat the first prompt and produce the same defect. On the
	first attempt there is no previous output, so it resolves to nothing.

	References to nodes OUTSIDE the loop body are left alone: they name work
	that happens once, and every attempt should see the same value.
	"""
	if isinstance(value, str):
		out = value
		# Resolve prev-references to a sentinel FIRST. Rewriting them straight to
		# the previous attempt would leave text the same-attempt pass below then
		# rewrites again, moving the reference forward to the attempt that has
		# not run.
		sentinel = {}
		for node_id in body:
			pattern = r"\{\{\s*prev\." + re.escape(node_id) + r"\.([a-zA-Z_]+)\s*\}\}"
			if attempt <= 1:
				# Nothing has been reviewed yet, so the reference resolves to
				# nothing rather than to an unresolved template.
				out = re.sub(pattern, "", out)
			else:
				token = f"\x00PREV{len(sentinel)}\x00"
				target = _suffixed(node_id, attempt - 1)
				out, n = re.subn(pattern, lambda m, t=token: t + m.group(1) + "\x01", out)
				if n:
					sentinel[token] = target

		for node_id in body:
			out = out.replace(f"{{{{ {node_id}.", f"{{{{ {_suffixed(node_id, attempt)}.")
			out = out.replace(f"{{{{{node_id}.", f"{{{{{_suffixed(node_id, attempt)}.")

		for token, target in sentinel.items():
			out = re.sub(re.escape(token) + r"([a-zA-Z_]+)\x01", lambda m, t=target: "{{ " + t + "." + m.group(1) + " }}", out)
		return out
	if isinstance(value, list):
		return [_rewrite_references(v, body, attempt) for v in value]
	if isinstance(value, dict):
		return {k: _rewrite_references(v, body, attempt) for k, v in value.items()}
	return value


def _validate(loop: Mapping[str, Any], nodes: Mapping[str, Any]) -> tuple[list[str], int, dict]:
	body = loop.get("body")
	if not isinstance(body, list) or not body:
		raise LoopError(f"loop {loop.get('id')!r}: body must be a non-empty list of node ids")
	missing = [n for n in body if n not in nodes]
	if missing:
		raise LoopError(f"loop {loop.get('id')!r}: body names nodes that do not exist: {missing}")

	attempts = loop.get("max_attempts")
	if not isinstance(attempts, int) or attempts < 1:
		raise LoopError(
			f"loop {loop.get('id')!r}: max_attempts must be an integer of at least 1. "
			"An unbounded loop is not expressible on purpose."
		)

	until = loop.get("until")
	if not isinstance(until, Mapping) or "node" not in until:
		raise LoopError(f"loop {loop.get('id')!r}: until must name the node whose output ends the loop")
	if until["node"] not in body:
		raise LoopError(f"loop {loop.get('id')!r}: until.node {until['node']!r} is not in the body")
	if not any(k in until for k in ("contains", "not_contains", "equals")):
		raise LoopError(
			f"loop {loop.get('id')!r}: until needs one of contains, not_contains or equals"
		)
	return list(body), attempts, dict(until)


def compile_loops(workflow: Mapping[str, Any]) -> dict:
	"""Return the workflow with every `graph.loops` entry expanded into a DAG.

	A workflow with no loops is returned unchanged, so this is safe to call on
	everything.
	"""
	graph = workflow.get("graph", {})
	loops = graph.get("loops")
	if not loops:
		return dict(workflow)

	nodes = dict(graph.get("nodes", {}))
	edges = [dict(e) for e in graph.get("edges", [])]

	for loop in loops:
		body, attempts, until = _validate(loop, nodes)
		body_set = set(body)
		# Edges wholly inside the body are the ones repeated per attempt.
		inner = [e for e in edges if e["from"] in body_set and e["to"] in body_set]
		# Where the loop hands off to the rest of the graph: rewire from the
		# LAST attempt, so downstream sees the final result.
		exits = [e for e in edges if e["from"] in body_set and e["to"] not in body_set]

		last = _suffixed(until["node"], attempts)
		for e in exits:
			if e["from"] == until["node"]:
				e["from"] = last

		for attempt in range(2, attempts + 1):
			prev_check = _suffixed(until["node"], attempt - 1)
			for node_id in body:
				copy = _rewrite_references(dict(nodes[node_id]), body_set, attempt)
				# The exit condition, carried on every node of the attempt: if
				# the previous attempt already satisfied it, this attempt is
				# skipped rather than run and thrown away.
				copy["skip_if"] = {**until, "node": prev_check}
				copy["loop"] = {"id": loop.get("id"), "attempt": attempt, "of": attempts}
				nodes[_suffixed(node_id, attempt)] = copy

			for e in inner:
				edges.append({
					"from": _suffixed(e["from"], attempt),
					"to": _suffixed(e["to"], attempt),
				})
			# Chain the attempts: this attempt begins after the previous
			# attempt's check, which is what makes the expansion a DAG.
			edges.append({"from": prev_check, "to": _suffixed(body[0], attempt)})

		for node_id in body:
			nodes[node_id] = _rewrite_references(dict(nodes[node_id]), body_set, 1)
			nodes[node_id].setdefault("loop", {"id": loop.get("id"), "attempt": 1, "of": attempts})

	out = dict(workflow)
	out["graph"] = {**graph, "nodes": nodes, "edges": edges}
	out["graph"].pop("loops", None)
	return out


def condition_met(condition: Mapping[str, Any], outputs: Mapping[str, Any]) -> bool:
	"""Evaluate a `skip_if` / `when` condition against the outputs so far.

	A condition on a node that has not produced output is NOT met: an absent
	result is not evidence of success, so the loop continues rather than
	exiting on a node that failed to run.
	"""
	node = condition.get("node")
	if node not in outputs:
		return False
	value = outputs[node]
	if isinstance(value, Mapping):
		# A node is only ever skipped because this same condition was already
		# met, so a skipped predecessor carries the exit forward. Without this
		# the third attempt inspects a skipped second attempt, finds no marker,
		# and runs work the first attempt already finished.
		if value.get("skipped"):
			return True
		value = value.get("output", value)
	text = value if isinstance(value, str) else str(value)

	if "equals" in condition:
		return text.strip() == str(condition["equals"]).strip()
	if "contains" in condition:
		return str(condition["contains"]).lower() in text.lower()
	if "not_contains" in condition:
		return str(condition["not_contains"]).lower() not in text.lower()
	return False
