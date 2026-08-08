# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Unit tests for execution/seat_resolver.py

Covers the resolution chain that makes a seat-based workflow portable: the same
workflow JSON must run under Vogelkop (router injected), standalone with a
router the user runs themselves, and standalone with only local models — or
fail with a typed error, never a silent escalation to a paid API.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.seat_resolver import (  # noqa: E402
	SEATS,
	Capability,
	SeatResolutionError,
	is_seat,
	resolve_seat,
	seat_capability,
)


def _no_models():
	return []


def _models(*names):
	return lambda: list(names)


class TestSeatVocabulary:
	"""Seats are a short, stable vocabulary of roles, not models."""

	def test_known_seats_declare_a_capability(self):
		for name, seat in SEATS.items():
			assert seat.name == name
			assert isinstance(seat.capability, Capability)

	def test_embedding_seat_is_not_chat(self):
		assert seat_capability("router-embedding") is Capability.EMBEDDING
		assert seat_capability("router-planner") is Capability.CHAT

	def test_is_seat_discriminates(self):
		assert is_seat("router-planner") is True
		assert is_seat("glm-5.2:cloud") is False

	def test_a_seat_nothing_can_serve_says_how_to_serve_it(self):
		"""A seat name is valid; being unservable is a deployment fact.

		The failure names the seat and the three ways to satisfy it, rather
		than listing the seats this build happens to enumerate: a deployment
		defines its own, so that list would be wrong as often as right.
		"""
		with pytest.raises(SeatResolutionError) as exc:
			resolve_seat("router-nope", installed_models=_no_models, env={})
		assert "router-nope" in str(exc.value)
		assert "custom_providers" in str(exc.value)
		assert "HILLSTAR_ROUTER_URL" in str(exc.value)


class TestChainPrecedence:
	"""Most specific step wins; each step is exercised in isolation below."""

	def test_workflow_pin_beats_everything(self):
		"""An explicit pin is a deliberate act and outranks the environment."""
		res = resolve_seat(
			"router-planner",
			custom_providers={
				"router-planner": {
					"endpoint": "http://pinned:9000",
					"model_name": "pinned-model",
					"type": "llamacpp",
				}
			},
			env={"HILLSTAR_ROUTER_URL": "http://router:18100"},
			installed_models=_models("jan-code-4b:latest"),
		)
		assert res.source == "workflow-pin"
		assert res.endpoint == "http://pinned:9000"
		assert res.model_name == "pinned-model"

	def test_host_router_beats_local_discovery(self):
		res = resolve_seat(
			"router-planner",
			env={"HILLSTAR_ROUTER_URL": "http://127.0.0.1:18100"},
			installed_models=_models("jan-code-4b:latest"),
		)
		assert res.source == "host-config"
		assert res.endpoint == "http://127.0.0.1:18100"
		# The seat name passes through: the router resolves seats itself and
		# substitutes the backend's real model.
		assert res.model_name == "router-planner"

	def test_local_discovery_when_no_router(self):
		res = resolve_seat(
			"router-planner", env={}, installed_models=_models("jan-code-4b:latest")
		)
		assert res.source == "local-discovery"
		assert res.provider == "ollama"
		assert res.model_name == "jan-code-4b:latest"
		assert res.endpoint is None

	def test_router_required_does_not_fall_back_to_local_discovery(self):
		with pytest.raises(SeatResolutionError, match="router required"):
			resolve_seat(
				"router-reviewer-cloud",
				require_router=True,
				env={},
				installed_models=_models("jan-code-4b:latest"),
			)

	def test_router_required_still_accepts_a_host_router(self):
		res = resolve_seat(
			"router-reviewer-cloud",
			require_router=True,
			env={"HILLSTAR_ROUTER_URL": "http://127.0.0.1:18100"},
			installed_models=_models("jan-code-4b:latest"),
		)
		assert res.source == "host-config"
		assert res.endpoint == "http://127.0.0.1:18100"


class TestWorkflowPin:
	def test_generic_router_key_also_matches(self):
		"""A single `router` entry covers every seat, so workflows need not
		repeat an endpoint per seat."""
		res = resolve_seat(
			"router-reviewer",
			custom_providers={"router": {"endpoint": "http://x:1", "type": "custom"}},
			env={},
			installed_models=_no_models,
		)
		assert res.source == "workflow-pin"
		assert res.model_name == "router-reviewer"

	def test_pin_without_endpoint_is_ignored(self):
		"""A malformed pin must not shadow a working step below it."""
		res = resolve_seat(
			"router-planner",
			custom_providers={"router-planner": {"model_name": "x"}},
			env={"HILLSTAR_ROUTER_URL": "http://router:18100"},
			installed_models=_no_models,
		)
		assert res.source == "host-config"

	def test_trailing_slash_normalised(self):
		res = resolve_seat(
			"router-planner",
			custom_providers={"router": {"endpoint": "http://x:1/"}},
			env={},
			installed_models=_no_models,
		)
		assert res.endpoint == "http://x:1"


class TestLocalDiscovery:
	def test_prefers_a_known_good_chat_model(self):
		res = resolve_seat(
			"router-planner",
			env={},
			installed_models=_models("llama2:7b", "jan-code-4b:latest"),
		)
		assert res.model_name == "jan-code-4b:latest"

	def test_falls_back_to_any_chat_model(self):
		"""A chat seat can use any chat model; something is better than nothing."""
		res = resolve_seat(
			"router-planner", env={}, installed_models=_models("some-unknown-model:7b")
		)
		assert res.model_name == "some-unknown-model:7b"

	def test_embedding_seat_picks_an_embedding_model(self):
		res = resolve_seat(
			"router-embedding",
			env={},
			installed_models=_models("jan-code-4b:latest", "bge-m3:latest"),
		)
		assert res.model_name == "bge-m3:latest"

	# The category error the capability field exists to prevent: a chat model
	# serving an embedding request returns plausible numbers, not an error.
	def test_embedding_seat_never_falls_back_to_a_chat_model(self):
		with pytest.raises(SeatResolutionError):
			resolve_seat(
				"router-embedding", env={}, installed_models=_models("jan-code-4b:latest")
			)


class TestTypedFailure:
	def test_no_backend_raises_rather_than_escalating(self):
		"""Never reach for a paid API because nothing local was found."""
		with pytest.raises(SeatResolutionError) as exc:
			resolve_seat("router-planner", env={}, installed_models=_no_models)
		msg = str(exc.value)
		assert "no backend for seat" in msg
		# The message must say how to fix it.
		assert "HILLSTAR_ROUTER_URL" in msg or "custom_providers" in msg

	def test_empty_router_url_is_not_a_router(self):
		with pytest.raises(SeatResolutionError):
			resolve_seat(
				"router-planner",
				env={"HILLSTAR_ROUTER_URL": "   "},
				installed_models=_no_models,
			)


class TestProvenance:
	"""Portability makes the model non-deterministic, so the trace must say
	which chain step produced it."""

	def test_every_resolution_names_its_source(self):
		sources = {
			resolve_seat(
				"router-planner",
				custom_providers={"router": {"endpoint": "http://x:1"}},
				env={},
				installed_models=_no_models,
			).source,
			resolve_seat(
				"router-planner", env={"HILLSTAR_ROUTER_URL": "http://y:2"}, installed_models=_no_models
			).source,
			resolve_seat("router-planner", env={}, installed_models=_models("m:1")).source,
		}
		assert sources == {"workflow-pin", "host-config", "local-discovery"}


class TestDeploymentDefinedSeats:
	"""Seats a deployment adds are valid without a hillstar release.

	The seat table lived in two places, hillstar and the Vogelkop router. Adding
	router-reviewer-us and router-reviewer-cloud to the router made every
	workflow using them fail hillstar validation with "Unknown provider
	'router'", because this side had never heard of them.
	"""

	def test_recognises_a_seat_this_build_does_not_enumerate(self):
		assert is_seat("router-reviewer-us")
		assert is_seat("router-reviewer-cloud")
		assert is_seat("router-implementer-reasoning-us")

	def test_rejects_a_name_outside_the_seat_namespace(self):
		assert not is_seat("gpt-5")
		assert not is_seat("deepseek-v4-flash")
		assert not is_seat("")

	def test_resolves_an_unenumerated_seat_through_the_router(self):
		res = resolve_seat(
			"router-reviewer-us",
			env={"HILLSTAR_ROUTER_URL": "http://127.0.0.1:18100"},
		)
		assert res.endpoint.startswith("http://127.0.0.1:18100")
		assert res.model_name == "router-reviewer-us"

	def test_a_pin_still_outranks_the_router_for_a_new_seat(self):
		res = resolve_seat(
			"router-reviewer-us",
			custom_providers={
				"router-reviewer-us": {
					"endpoint": "http://127.0.0.1:18011",
					"model_name": "puzzle-75b",
					"type": "custom",
				}
			},
			env={"HILLSTAR_ROUTER_URL": "http://127.0.0.1:18100"},
		)
		assert res.endpoint == "http://127.0.0.1:18011"

	def test_a_name_outside_the_namespace_still_fails_typed(self):
		with pytest.raises(SeatResolutionError):
			resolve_seat("not-a-seat", env={})
