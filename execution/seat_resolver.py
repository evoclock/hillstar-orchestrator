# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Seat resolution.

Purpose: turn a SEAT named by a workflow into a concrete provider, model and
	endpoint, using whatever inference the running machine actually has.

	A workflow names a seat and its capability and nothing else — no endpoint,
	no host, no model id, no credentials — so the same bytes run under
	Vogelkop, standalone, and on someone else's machine. Everything
	deployment-specific is resolved here, at run time.

	Why seats rather than models: models churn. A workflow pinned to
	`glm-5.2:cloud` may be unreproducible in a year unless that model is local.
	Reproducibility is served by *recording* what ran (the execution receipt),
	not by pinning what will run.

Inputs: a seat name, the workflow's `custom_providers` block, the process
	environment, and two discovery callables (installed ollama models, and a
	PATH lookup). Discovery is injected rather than performed here so this
	module stays pure and testable without ollama running.

Outputs: a `Resolution` naming provider / model / endpoint plus the chain step
	that produced it, or `SeatResolutionError`.

Assumptions: seat names are a small, stable vocabulary (they change when the
	kind of work changes, not when a vendor ships a model). Capability is the
	only thing a seat declares beyond its name.

Parameters: none (library module).

Failure Modes: no backend for a seat raises `SeatResolutionError` — never a
	silent fallback, and in particular never an escalation to a metered API
	because nothing local was found. Unbounded cost must be an explicit act.

Author: Julen Gamboa

Created: 2026-08-03

Last Edited: 2026-08-03 by Julen Gamboa
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Iterable, Mapping

from utils.exceptions import HillstarException


class Capability(StrEnum):
	"""What a seat is FOR.

	The only thing a seat declares beyond its name. Capability catches the
	category errors that produce silent nonsense — an embedding request served
	by a chat model returns plausible numbers, not an error — without
	recreating per-model metadata, which is the thing that rots.
	"""

	CHAT = "chat"
	EMBEDDING = "embedding"
	OCR = "ocr"
	SEQUENCE = "sequence"


@dataclass(frozen=True)
class Seat:
	"""A role in the workforce. Which model serves it is a deployment fact."""

	name: str
	capability: Capability


# Seats whose CAPABILITY hillstar must know without asking anyone: an embedding
# seat must never be served by a chat model. This is not the list of valid
# seats. A deployment adds seats (a US-origin reviewer, a second implementer)
# in the router's configuration, and a copy of that list here would go stale
# the moment it did — which is exactly what happened.
SEAT_PREFIX = "router-"

SEATS: Mapping[str, Seat] = {
	"router-planner": Seat("router-planner", Capability.CHAT),
	"router-reviewer": Seat("router-reviewer", Capability.CHAT),
	"router-implementer": Seat("router-implementer", Capability.CHAT),
	"router-implementer-reasoning": Seat("router-implementer-reasoning", Capability.CHAT),
	"router-embedding": Seat("router-embedding", Capability.EMBEDDING),
}


class SeatResolutionError(HillstarException):
	"""Raised when no backend on this machine can serve a seat."""

	pass


@dataclass(frozen=True)
class Resolution:
	"""How a seat was resolved, and by which step of the chain.

	`source` is recorded so a trace can answer "why did this run reach that
	model", which portability otherwise makes unanswerable.
	"""

	provider: str
	model_name: str
	endpoint: str | None
	source: str


def is_seat(name: str) -> bool:
	"""True for any name in the seat namespace.

	Deliberately permissive. Hillstar cannot know which seats a deployment has
	configured, so treating an unknown `router-*` name as a typo would reject
	valid workflows. An unservable seat fails at resolution with a typed error
	naming what the router does offer, which is the honest place for it.
	"""
	return name in SEATS or name.startswith(SEAT_PREFIX)


def seat_capability(name: str) -> Capability | None:
	seat = SEATS.get(name)
	return seat.capability if seat else None


def _pinned(seat_name: str, custom_providers: Mapping | None) -> Resolution | None:
	"""Step 1: an explicit `custom_providers` entry in the workflow.

	Highest precedence precisely because it is deliberate: someone pinned this
	run for reproducibility, and that intent outranks anything the environment
	offers.
	"""
	if not isinstance(custom_providers, Mapping):
		return None
	entry = custom_providers.get(seat_name) or custom_providers.get("router")
	if not isinstance(entry, Mapping):
		return None
	endpoint = entry.get("endpoint")
	if not isinstance(endpoint, str) or not endpoint.strip():
		return None
	return Resolution(
		provider=str(entry.get("type") or "custom"),
		model_name=str(entry.get("model_name") or seat_name),
		endpoint=endpoint.strip().rstrip("/"),
		source="workflow-pin",
	)


def _host_router(seat_name: str, env: Mapping[str, str]) -> Resolution | None:
	"""Step 2: a router endpoint supplied by the host.

	Vogelkop injects this when it runs a workflow; a standalone user can set
	`HILLSTAR_ROUTER_URL` to reach a router they run themselves. The seat name
	is passed through as the model, because the router resolves seats itself
	and substitutes the backend's real model name.
	"""
	url = env.get("HILLSTAR_ROUTER_URL", "").strip()
	if not url:
		return None
	return Resolution(
		provider="custom",
		model_name=seat_name,
		endpoint=url.rstrip("/"),
		source="host-config",
	)


# Local model preferences per capability, most preferred first. Substring match
# against whatever ollama actually reports, so a tag suffix (":latest",
# ":cloud") does not have to be spelled out.
_LOCAL_PREFERENCES: Mapping[Capability, tuple[str, ...]] = {
	Capability.CHAT: ("jan-code", "qwen", "deepseek", "glm", "minimax", "kimi"),
	Capability.EMBEDDING: ("bge", "embed", "nomic", "minilm"),
}


def _local(
	seat_name: str,
	capability: Capability,
	installed: Iterable[str],
) -> Resolution | None:
	"""Step 3: resolve against models this machine actually has.

	Discovery, not a hand-written list: asking ollama what exists is truthful,
	whereas a catalogue in a file drifts the moment a model is pulled or
	removed. That drift is exactly what happened to the provider registry.
	"""
	models = [m for m in installed if m]
	if not models:
		return None
	for wanted in _LOCAL_PREFERENCES.get(capability, ()):  # preference order
		for model in models:
			if wanted in model.lower():
				return Resolution(
					provider="ollama",
					model_name=model,
					endpoint=None,
					source="local-discovery",
				)
	# A chat seat can use any chat model; an embedding seat cannot fall back to
	# an arbitrary model, because a chat model returns plausible nonsense
	# rather than failing.
	if capability is Capability.CHAT:
		return Resolution(
			provider="ollama",
			model_name=models[0],
			endpoint=None,
			source="local-discovery",
		)
	return None


def _ollama_models() -> list[str]:
	"""Default discovery: models installed in the local ollama."""
	import subprocess

	if not shutil.which("ollama"):
		return []
	try:
		proc = subprocess.run(
			["ollama", "list"], capture_output=True, text=True, timeout=5
		)
	except (OSError, subprocess.SubprocessError):
		return []
	if proc.returncode != 0:
		return []
	out = []
	for line in proc.stdout.splitlines()[1:]:  # skip the header row
		name = line.split()[0] if line.split() else ""
		if name:
			out.append(name)
	return out


def resolve_seat(
	seat_name: str,
	*,
	custom_providers: Mapping | None = None,
	env: Mapping[str, str] | None = None,
	installed_models: Callable[[], Iterable[str]] | None = None,
	which: Callable[[str], str | None] | None = None,
	require_router: bool = False,
) -> Resolution:
	"""Resolve `seat_name` through the chain, most specific step first.

	1. explicit `custom_providers` pin in the workflow
	2. host-supplied router endpoint (Vogelkop injects; or HILLSTAR_ROUTER_URL)
	3. local discovery, unless the caller explicitly requires a router
	4. typed failure

	`require_router` is the transport contract for a node whose provider is
	`router`: a seat must not silently become whichever local chat model happens
	to be installed. Direct-provider and standalone callers leave it false and
	retain the portable local-discovery path.

	Never falls through to a metered API because nothing local was found:
	unbounded cost is an explicit act, not a consolation prize.
	"""
	seat = SEATS.get(seat_name)
	if seat is None:
		if not is_seat(seat_name):
			raise SeatResolutionError(
				f"{seat_name!r} is not a seat; seat names begin {SEAT_PREFIX!r}"
			)
		# A seat this build has no capability entry for. Chat is the safe
		# assumption: every capability-specific seat is named above, and the
		# router rejects a seat it does not serve.
		seat = Seat(seat_name, Capability.CHAT)

	env = os.environ if env is None else env
	installed_models = _ollama_models if installed_models is None else installed_models
	which = shutil.which if which is None else which

	resolutions = [
		_pinned(seat_name, custom_providers),
		_host_router(seat_name, env),
	]
	if not require_router:
		resolutions.append(_local(seat_name, seat.capability, installed_models()))

	for resolution in resolutions:
		if resolution is not None:
			return resolution

	if require_router:
		raise SeatResolutionError(
			f"router required for seat {seat_name!r} (capability {seat.capability}); "
			"provide a router endpoint through HILLSTAR_ROUTER_URL or "
			"custom_providers"
		)

	raise SeatResolutionError(
		f"no backend for seat {seat_name!r} (capability {seat.capability}). "
		"Pin one in the workflow's custom_providers, set HILLSTAR_ROUTER_URL, "
		"or install a suitable local model."
	)
