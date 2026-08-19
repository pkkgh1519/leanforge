from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, deque
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, Mapping


BEHAVIOR_ORIGIN_COMMIT = "fb252b4236cc607002e131210f6161db72f6841e"
BYTE_BASELINE_COMMIT = "6f28b044cb2eeee2e1eac94c495450ee8542862b"
SURFACES = ("src/skills", "claude/skills", "codex/plugin/skills")
GRAPH_RELATIVE_PATH = "run/references/load-graph.json"
CONTRACT_RELATIVE_PATH = "run/references/semantic-contract.json"
FIXTURE_RELATIVE_PATH = "tests/fixtures/forced_load_baseline_v1_9_0.json"
MEASUREMENT_DECLARATION = {
    "raw_bytes": (
        "exact Git blob bytes; no newline or frontmatter normalization"
    ),
    "words": (
        "UTF-8 decode followed by Python str.split() "
        "Unicode whitespace counting"
    ),
    "identity": (
        "surface plus surface-relative POSIX path; "
        "no content or path dedupe"
    ),
    "route_union": (
        "forced-load projection from one recursive activation traversal"
    ),
}

TOP_LEVEL_KEYS = {
    "schema_version", "graph_id", "nodes", "edges", "named_roots", "profiles"
}
NODE_KEYS = {"path"}
EDGE_KEYS = {
    "from", "to", "kind", "phase", "activation_contract_id", "optional"
}
ROOT_KEYS = {"name", "path"}
PROFILE_KEYS = {"name", "optional_edges"}
OPTIONAL_SELECTOR_KEYS = {"from", "to", "phase"}
EDGE_KINDS = {"force_load", "prompt_load", "optional_load"}
PHASES = {
    "startup", "preflight", "graph_preflight", "dispatch",
    "conditional_review", "harness", "final_review", "review",
}
ALLOWED_PHASES_BY_INVARIANT_KIND = {
    "route_topology": {"startup", "graph_preflight"},
    "lifecycle_ownership": {"preflight", "harness"},
    "failure_overlay": {"dispatch"},
    "review_topology": {"conditional_review", "final_review", "review"},
}
EXACT_PHASES_BY_EDGE_BINDING = {
    (
        "run/SKILL.md",
        "run/references/orchestration.md",
        "force_load",
        "RUN-ROUTE-TOPOLOGY",
        False,
    ): {"startup"},
    (
        "run/SKILL.md",
        "run/references/harness-lifecycle.md",
        "force_load",
        "RUN-LIFECYCLE-OWNERSHIP",
        False,
    ): {"preflight"},
    (
        "run/SKILL.md",
        "run/references/graph-contract.md",
        "force_load",
        "RUN-ROUTE-TOPOLOGY",
        False,
    ): {"graph_preflight"},
    (
        "run/references/harness-lifecycle.md",
        "run/references/harness-format.md",
        "force_load",
        "RUN-LIFECYCLE-OWNERSHIP",
        False,
    ): {"harness"},
    (
        "run/references/orchestration.md",
        "run/references/implementer-prompt.md",
        "prompt_load",
        "RUN-FAIL-CLOSED",
        False,
    ): {"dispatch"},
    (
        "run/references/orchestration.md",
        "run/references/spec-review-prompt.md",
        "prompt_load",
        "RUN-REVIEW-TOPOLOGY",
        False,
    ): {"conditional_review"},
    (
        "run/references/orchestration.md",
        "run/references/reviewer-prompt.md",
        "prompt_load",
        "RUN-REVIEW-TOPOLOGY",
        False,
    ): {"conditional_review", "final_review"},
    (
        "run/SKILL.md",
        "run/references/harness-review.md",
        "optional_load",
        "RUN-REVIEW-TOPOLOGY",
        True,
    ): {"review"},
    (
        "run/SKILL.md",
        "run/references/repo-lens-routing.md",
        "optional_load",
        "RUN-REVIEW-TOPOLOGY",
        True,
    ): {"review"},
}
CONTEXT_PHASES = {
    "entry_execution": {"startup", "preflight", "graph_preflight", "dispatch"},
    "conditional_review": {
        "startup", "preflight", "graph_preflight", "dispatch", "conditional_review",
    },
    "route_union": {
        "startup", "preflight", "graph_preflight", "dispatch",
        "harness", "final_review", "review",
    },
    "failure_route_union": {
        "startup", "preflight", "graph_preflight", "dispatch",
        "harness", "final_review", "review",
    },
}
MARKER_PREFIX = "leanforge:run-load"
MARKER_RE = re.compile(
    r"<!--\s*leanforge:run-load\s+(\{.*?\})\s*-->", re.DOTALL
)
PLAIN_LOAD_RE = re.compile(
    r"\b(?:force[- ]load|preload|load)\b(?!-)"
    r"(?:(?!\r?\n[ \t]*\r?\n).){0,160}?"
    r"`?((?:references/)?[A-Za-z0-9._/-]+\.md)`?",
    re.IGNORECASE | re.DOTALL,
)
LEGACY_COMPATIBILITY_LITERAL = (
    "Compatibility-only (non-operative legacy assertion): "
    "~~Force-load `references/harness-lifecycle.md` before any state-directory~~"
)
LEGACY_COMPATIBILITY_EDGE = {
    "from": "run/SKILL.md",
    "to": "run/references/harness-lifecycle.md",
    "kind": "force_load",
    "phase": "preflight",
    "activation_contract_id": "RUN-LIFECYCLE-OWNERSHIP",
    "optional": False,
}


class LoadContractError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise LoadContractError(reason)


def _edge_signature(edge: Mapping[str, object]) -> tuple[object, ...]:
    return tuple(edge[key] for key in sorted(EDGE_KEYS))


def _optional_signature(edge: Mapping[str, object]) -> tuple[object, ...]:
    return (edge["from"], edge["to"], edge["phase"])


def _validate_logical_path(path: object) -> str:
    _require(isinstance(path, str) and path, "logical path must be a non-empty string")
    _require("\\" not in path, f"logical path must use POSIX separators: {path}")
    _require(
        not re.match(r"^[A-Za-z]:", path),
        f"absolute logical path is forbidden: {path}",
    )
    logical = PurePosixPath(path)
    _require(not logical.is_absolute(), f"absolute logical path is forbidden: {path}")
    _require(".." not in logical.parts, f"path traversal is forbidden: {path}")
    _require("." not in logical.parts, f"dot path segments are forbidden: {path}")
    _require(
        logical.as_posix() == path,
        f"logical path is not canonical POSIX: {path}",
    )
    _require(
        path.startswith("run/"),
        f"logical path must be relative to the skill surface: {path}",
    )
    return path


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LoadContractError(f"cannot read JSON {path}: {exc}") from exc
    _require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def _is_closed_legacy_compatibility_literal(
    document_path: str,
    text: str,
    match: re.Match,
) -> bool:
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    if text[line_start:line_end] != LEGACY_COMPATIBILITY_LITERAL:
        return False
    if document_path != LEGACY_COMPATIBILITY_EDGE["from"]:
        return False
    previous_end = line_start - 1
    previous_start = text.rfind("\n", 0, previous_end) + 1
    previous_line = text[previous_start:previous_end]
    marker = MARKER_RE.fullmatch(previous_line)
    if marker is None:
        return False
    try:
        edge = json.loads(marker.group(1))
    except json.JSONDecodeError:
        return False
    return edge == LEGACY_COMPATIBILITY_EDGE


def discover_directives_from_documents(
    documents: Mapping[str, str], graph_node_paths: Iterable[str]
) -> list[dict]:
    node_paths = set(graph_node_paths)
    node_basenames = {
        PurePosixPath(path).name: path
        for path in node_paths
        if PurePosixPath(path).name != "SKILL.md"
    }
    directives: list[dict] = []
    for document_path, text in sorted(documents.items()):
        matches = list(MARKER_RE.finditer(text))
        _require(
            text.count(MARKER_PREFIX) == len(matches),
            f"malformed structured load marker in {document_path}",
        )
        for match in matches:
            try:
                directive = json.loads(match.group(1))
            except json.JSONDecodeError as exc:
                raise LoadContractError(
                    f"invalid structured load marker JSON in {document_path}: {exc}"
                ) from exc
            _require(
                isinstance(directive, dict),
                "structured load marker must be an object",
            )
            _require(
                set(directive) == EDGE_KEYS,
                f"structured load marker has unknown or missing keys in {document_path}",
            )
            _require(
                directive["from"] == document_path,
                f"structured load marker source mismatch in {document_path}",
            )
            directives.append(directive)

        for match in PLAIN_LOAD_RE.finditer(text):
            if _is_closed_legacy_compatibility_literal(
                document_path, text, match
            ):
                continue
            named_path = match.group(1)
            logical_path = None
            if named_path.startswith("references/"):
                logical_path = f"run/{named_path}"
            elif named_path in node_basenames:
                logical_path = node_basenames[named_path]
            if logical_path in node_paths:
                raise LoadContractError(
                    f"plain imperative preload is forbidden in {document_path}: "
                    f"{named_path}"
                )
    return directives


def _surface_documents(root: Path, surface: str) -> dict[str, str]:
    surface_root = root / surface
    documents: dict[str, str] = {}
    for path in sorted((surface_root / "run").rglob("*.md")):
        relative = path.relative_to(surface_root).as_posix()
        try:
            documents[relative] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise LoadContractError(f"cannot read Markdown {path}: {exc}") from exc
    return documents


def validate_graph(
    graph: dict,
    semantic_contract: dict,
    *,
    available_paths: Iterable[str],
    directives: Iterable[dict] | None = None,
) -> None:
    _require(
        set(graph) == TOP_LEVEL_KEYS,
        "load graph top-level envelope is not closed",
    )
    _require(
        type(graph["schema_version"]) is int
        and graph["schema_version"] == 1,
        "load graph schema_version must be integer 1",
    )
    _require(
        graph["graph_id"] == "leanforge.run.instruction-loads",
        "load graph identity is invalid",
    )

    nodes = graph["nodes"]
    _require(isinstance(nodes, list) and nodes, "nodes must be a non-empty list")
    node_paths: list[str] = []
    for node in nodes:
        _require(
            isinstance(node, dict) and set(node) == NODE_KEYS,
            "node envelope is not closed",
        )
        node_paths.append(_validate_logical_path(node["path"]))
    _require(
        len(node_paths) == len(set(node_paths)),
        "duplicate logical node identity",
    )
    available = set(available_paths)
    for path in node_paths:
        _require(path in available, f"unknown logical node path: {path}")

    invariants = semantic_contract.get("invariants")
    _require(isinstance(invariants, list), "semantic invariants are missing")
    invariant_by_id = {
        invariant.get("id"): invariant
        for invariant in invariants
        if isinstance(invariant, dict)
    }
    _require(
        len(invariant_by_id) == len(invariants),
        "duplicate or missing semantic invariant id",
    )

    edges = graph["edges"]
    _require(isinstance(edges, list) and edges, "edges must be a non-empty list")
    edge_signatures: list[tuple[object, ...]] = []
    incoming = Counter()
    optional_edges: set[tuple[object, ...]] = set()
    for edge in edges:
        _require(
            isinstance(edge, dict) and set(edge) == EDGE_KEYS,
            "edge envelope is not closed",
        )
        source = _validate_logical_path(edge["from"])
        target = _validate_logical_path(edge["to"])
        _require(
            source in node_paths,
            f"edge source is not a declared node: {source}",
        )
        _require(
            target in node_paths,
            f"edge target is not a declared node: {target}",
        )
        _require(source != target, f"self load edge is forbidden: {source}")
        _require(
            edge["kind"] in EDGE_KINDS,
            f"unknown load edge kind: {edge['kind']}",
        )
        _require(
            isinstance(edge["optional"], bool),
            "edge optional must be boolean",
        )
        _require(
            edge["optional"] == (edge["kind"] == "optional_load"),
            "optional flag and optional_load kind must agree",
        )
        _require(
            edge["phase"] in PHASES,
            f"unknown load phase: {edge['phase']}",
        )
        activation_id = edge["activation_contract_id"]
        _require(
            activation_id in invariant_by_id,
            f"orphan activation contract id: {activation_id}",
        )
        invariant_kind = invariant_by_id[activation_id].get("kind")
        _require(
            edge["phase"]
            in ALLOWED_PHASES_BY_INVARIANT_KIND.get(invariant_kind, set()),
            f"wrong phase {edge['phase']} for activation invariant {activation_id}",
        )
        binding = (
            source,
            target,
            edge["kind"],
            activation_id,
            edge["optional"],
        )
        allowed_binding_phases = EXACT_PHASES_BY_EDGE_BINDING.get(binding)
        _require(
            allowed_binding_phases is not None,
            f"unsupported load edge binding: {source} -> {target}",
        )
        _require(
            edge["phase"] in allowed_binding_phases,
            f"wrong phase {edge['phase']} for load edge {source} -> {target}",
        )
        signature = _edge_signature(edge)
        edge_signatures.append(signature)
        incoming[target] += 1
        if edge["optional"]:
            optional_edges.add(_optional_signature(edge))
    _require(
        len(edge_signatures) == len(set(edge_signatures)),
        "duplicate load edge identity",
    )

    roots = graph["named_roots"]
    _require(
        isinstance(roots, list) and roots,
        "named_roots must be a non-empty list",
    )
    root_names: list[str] = []
    root_paths: list[str] = []
    for root in roots:
        _require(
            isinstance(root, dict) and set(root) == ROOT_KEYS,
            "named root envelope is not closed",
        )
        _require(
            isinstance(root["name"], str) and root["name"],
            "named root name is invalid",
        )
        path = _validate_logical_path(root["path"])
        _require(
            path in node_paths,
            f"named root is not a declared node: {path}",
        )
        root_names.append(root["name"])
        root_paths.append(path)
    _require(len(root_names) == len(set(root_names)), "duplicate named root")
    _require(
        len(root_paths) == len(set(root_paths)),
        "duplicate named root path",
    )
    for path in node_paths:
        _require(
            path in root_paths or incoming[path] > 0,
            f"orphan load graph node: {path}",
        )

    profiles = graph["profiles"]
    _require(
        isinstance(profiles, list) and profiles,
        "profiles must be a non-empty list",
    )
    profile_names: list[str] = []
    for profile in profiles:
        _require(
            isinstance(profile, dict) and set(profile) == PROFILE_KEYS,
            "profile envelope is not closed",
        )
        _require(
            isinstance(profile["name"], str) and profile["name"],
            "profile name is invalid",
        )
        selectors = profile["optional_edges"]
        _require(
            isinstance(selectors, list),
            "profile optional_edges must be a list",
        )
        selector_signatures: list[tuple[object, ...]] = []
        for selector in selectors:
            _require(
                isinstance(selector, dict)
                and set(selector) == OPTIONAL_SELECTOR_KEYS,
                "optional edge selector envelope is not closed",
            )
            signature = _optional_signature(selector)
            _require(
                signature in optional_edges,
                f"profile selects undeclared optional edge: {signature}",
            )
            selector_signatures.append(signature)
        _require(
            len(selector_signatures) == len(set(selector_signatures)),
            f"profile {profile['name']} repeats an optional edge",
        )
        profile_names.append(profile["name"])
    _require(
        len(profile_names) == len(set(profile_names)),
        "duplicate profile name",
    )
    _require("default" in profile_names, "default profile is missing")
    default_profile = next(
        profile for profile in profiles if profile["name"] == "default"
    )
    _require(
        default_profile["optional_edges"] == [],
        "default profile must exclude optional loads",
    )

    if directives is not None:
        graph_counter = Counter(edge_signatures)
        marker_counter = Counter(
            _edge_signature(marker) for marker in directives
        )
        missing = graph_counter - marker_counter
        undeclared = marker_counter - graph_counter
        _require(
            not missing,
            f"graph edge is missing its structured marker: "
            f"{list(missing.elements())}",
        )
        _require(
            not undeclared,
            f"structured marker declares an undeclared edge: "
            f"{list(undeclared.elements())}",
        )


def validate_repository_surface(
    root: Path, surface: str
) -> tuple[dict, dict]:
    graph = load_json(root / surface / GRAPH_RELATIVE_PATH)
    semantic_contract = load_json(root / surface / CONTRACT_RELATIVE_PATH)
    surface_root = root / surface
    available_paths = {
        path.relative_to(surface_root).as_posix()
        for path in (surface_root / "run").rglob("*")
        if path.is_file()
    }
    node_paths = [
        node.get("path")
        for node in graph.get("nodes", [])
        if isinstance(node, dict)
    ]
    directives = discover_directives_from_documents(
        _surface_documents(root, surface), node_paths
    )
    validate_graph(
        graph,
        semantic_contract,
        available_paths=available_paths,
        directives=directives,
    )
    return graph, semantic_contract


def validate_repository(
    root: Path, surfaces: Iterable[str] = SURFACES
) -> tuple[dict, dict]:
    canonical_graph = None
    canonical_contract = None
    for surface in surfaces:
        graph, contract = validate_repository_surface(root, surface)
        if canonical_graph is None:
            canonical_graph = graph
            canonical_contract = contract
        else:
            _require(
                graph == canonical_graph,
                f"generated load graph drift on {surface}",
            )
            _require(
                contract == canonical_contract,
                f"generated semantic contract drift on {surface}",
            )
    assert canonical_graph is not None and canonical_contract is not None
    return canonical_graph, canonical_contract



def _root_path(graph: dict, name: str) -> str:
    matches = [
        root["path"]
        for root in graph["named_roots"]
        if root["name"] == name
    ]
    _require(
        len(matches) == 1,
        f"unknown or duplicate named root: {name}",
    )
    return matches[0]


def _profile_optional_edges(
    graph: dict, name: str
) -> set[tuple[object, ...]]:
    matches = [
        profile
        for profile in graph["profiles"]
        if profile["name"] == name
    ]
    _require(
        len(matches) == 1,
        f"unknown or duplicate profile: {name}",
    )
    return {
        _optional_signature(selector)
        for selector in matches[0]["optional_edges"]
    }


def activation_is_active(
    edge: dict,
    *,
    route: str,
    overlay: str | None,
    phase: str,
    profile: str,
    invariant: dict,
    graph: dict,
    semantic_contract: dict,
) -> bool:
    routes = semantic_contract["vocabulary"]["route"]
    overlays = semantic_contract["vocabulary"]["overlay"]
    _require(route in routes, f"unknown activation route: {route}")
    _require(
        overlay is None or overlay in overlays,
        f"unknown activation overlay: {overlay}",
    )
    _require(
        phase in CONTEXT_PHASES,
        f"unknown activation phase context: {phase}",
    )
    _require(
        invariant.get("id") == edge["activation_contract_id"],
        "activation invariant does not match edge binding",
    )
    if edge["phase"] not in CONTEXT_PHASES[phase]:
        return False

    selected = _profile_optional_edges(graph, profile)
    if edge["optional"] and _optional_signature(edge) not in selected:
        return False

    invariant_kind = invariant.get("kind")
    if invariant_kind in {"route_topology", "lifecycle_ownership"}:
        return True
    if invariant_kind == "failure_overlay":
        return route != "direct" or overlay == "failure"
    if invariant_kind == "review_topology":
        return True
    raise LoadContractError(
        f"unsupported activation invariant kind: {invariant_kind}"
    )


def instruction_closure(
    graph: dict,
    semantic_contract: dict,
    *,
    root: str,
    route: str,
    overlay: str | None,
    phase: str,
    profile: str,
) -> dict:
    root_path = _root_path(graph, root)
    invariant_by_id = {
        invariant["id"]: invariant
        for invariant in semantic_contract["invariants"]
    }
    outgoing: dict[str, list[dict]] = {}
    for edge in graph["edges"]:
        outgoing.setdefault(edge["from"], []).append(edge)

    instruction_nodes = {root_path}
    forced_load_nodes = {root_path}
    active_edges: set[tuple[object, ...]] = set()
    states_seen: set[tuple[str, bool]] = set()
    queue = deque([(root_path, True)])
    while queue:
        node, forced_chain = queue.popleft()
        state = (node, forced_chain)
        if state in states_seen:
            continue
        states_seen.add(state)
        for edge in sorted(
            outgoing.get(node, []), key=_edge_signature
        ):
            invariant = invariant_by_id[
                edge["activation_contract_id"]
            ]
            if not activation_is_active(
                edge,
                route=route,
                overlay=overlay,
                phase=phase,
                profile=profile,
                invariant=invariant,
                graph=graph,
                semantic_contract=semantic_contract,
            ):
                continue
            active_edges.add(_edge_signature(edge))
            instruction_nodes.add(edge["to"])
            next_forced = (
                forced_chain and edge["kind"] == "force_load"
            )
            if next_forced:
                forced_load_nodes.add(edge["to"])
            queue.append((edge["to"], next_forced))

    return {
        "instruction_nodes": sorted(instruction_nodes),
        "forced_load_nodes": sorted(forced_load_nodes),
        "active_edges": [
            list(signature) for signature in sorted(active_edges)
        ],
    }


def named_contexts() -> list[dict]:
    contexts: list[dict] = []
    for route in (
        "direct", "single_risky", "parallel", "external"
    ):
        contexts.extend(
            [
                {
                    "name": f"entry_execution.{route}",
                    "root": "run",
                    "route": route,
                    "overlay": None,
                    "phase": "entry_execution",
                    "profile": "default",
                },
                {
                    "name": f"route_union.{route}",
                    "root": "run",
                    "route": route,
                    "overlay": None,
                    "phase": "route_union",
                    "profile": "default",
                },
                {
                    "name": f"failure_route_union.{route}",
                    "root": "run",
                    "route": route,
                    "overlay": "failure",
                    "phase": "failure_route_union",
                    "profile": "default",
                },
            ]
        )
    return contexts


def _word_count(raw: bytes) -> int:
    return len(raw.decode("utf-8").split())


def _measure_surface(
    graph: dict,
    semantic_contract: dict,
    read_bytes: Callable[[str], bytes],
    blob_oid: Callable[[str], str] | None,
) -> dict:
    nodes: list[dict] = []
    node_by_path: dict[str, dict] = {}
    for node in sorted(
        graph["nodes"], key=lambda item: item["path"]
    ):
        path = node["path"]
        raw = read_bytes(path)
        record = {
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_bytes": len(raw),
            "words": _word_count(raw),
        }
        if blob_oid is not None:
            record["git_blob_oid"] = blob_oid(path)
        nodes.append(record)
        node_by_path[path] = record

    closures: list[dict] = []
    closure_by_name: dict[str, dict] = {}
    for context in named_contexts():
        closure = instruction_closure(
            graph,
            semantic_contract,
            **{
                key: context[key]
                for key in (
                    "root", "route", "overlay", "phase", "profile"
                )
            },
        )
        forced_paths = closure["forced_load_nodes"]
        record = {
            **context,
            "instruction_nodes": closure["instruction_nodes"],
            "forced_load_nodes": forced_paths,
            "raw_bytes": sum(
                node_by_path[path]["raw_bytes"]
                for path in forced_paths
            ),
            "words": sum(
                node_by_path[path]["words"]
                for path in forced_paths
            ),
        }
        closures.append(record)
        closure_by_name[record["name"]] = record

    for route in (
        "direct", "single_risky", "parallel", "external"
    ):
        happy = closure_by_name[f"route_union.{route}"]
        failed = closure_by_name[
            f"failure_route_union.{route}"
        ]
        instruction_delta = sorted(
            set(failed["instruction_nodes"])
            - set(happy["instruction_nodes"])
        )
        forced_delta = sorted(
            set(failed["forced_load_nodes"])
            - set(happy["forced_load_nodes"])
        )
        closures.append(
            {
                "name": f"failure_overlay_report.{route}",
                "derived_from": [
                    f"route_union.{route}",
                    f"failure_route_union.{route}",
                ],
                "instruction_nodes": instruction_delta,
                "forced_load_nodes": forced_delta,
                "raw_bytes": sum(
                    node_by_path[path]["raw_bytes"]
                    for path in forced_delta
                ),
                "words": sum(
                    node_by_path[path]["words"]
                    for path in forced_delta
                ),
            }
        )
    return {"nodes": nodes, "closures": closures}


def _git(
    root: Path, *args: str, binary: bool = False
) -> str | bytes:
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={root.as_posix()}",
            *args,
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise LoadContractError(
            f"git {' '.join(args)} failed: "
            f"{completed.stderr.decode('utf-8', errors='replace').strip()}"
        )
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8").strip()


def _baseline_surface(
    root: Path,
    graph: dict,
    semantic_contract: dict,
    surface: str,
) -> dict:
    oid_cache: dict[str, str] = {}

    def oid(path: str) -> str:
        if path not in oid_cache:
            oid_cache[path] = str(
                _git(
                    root,
                    "rev-parse",
                    f"{BYTE_BASELINE_COMMIT}:{surface}/{path}",
                )
            )
        return oid_cache[path]

    def read(path: str) -> bytes:
        return bytes(
            _git(root, "cat-file", "blob", oid(path), binary=True)
        )

    return _measure_surface(
        graph, semantic_contract, read, oid
    )


def _build_predecessor_fixture(root: Path) -> dict:
    graph, semantic_contract = validate_repository_surface(
        root, "src/skills"
    )
    return {
        "schema_version": 1,
        "fixture_id": "leanforge.run.forced-load-baseline",
        "behavior_origin_commit": BEHAVIOR_ORIGIN_COMMIT,
        "byte_baseline_commit": BYTE_BASELINE_COMMIT,
        "measurement": dict(MEASUREMENT_DECLARATION),
        "surfaces": {
            surface: _baseline_surface(
                root, graph, semantic_contract, surface
            )
            for surface in SURFACES
        },
    }


def capture_baseline(root: Path) -> dict:
    return _build_predecessor_fixture(root)


def serialize_fixture(fixture: dict) -> bytes:
    text = json.dumps(
        fixture,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return (text + "\n").encode("utf-8")


def write_captured_baseline(
    root: Path, output: Path
) -> None:
    _require(
        output.is_absolute(),
        "capture output path must be explicit and absolute",
    )
    output.write_bytes(
        serialize_fixture(capture_baseline(root))
    )


def validate_fixture(fixture: dict) -> None:
    _require(
        isinstance(fixture, dict),
        "baseline fixture root must be an object",
    )
    _require(
        set(fixture)
        == {
            "schema_version",
            "fixture_id",
            "behavior_origin_commit",
            "byte_baseline_commit",
            "measurement",
            "surfaces",
        },
        "baseline fixture envelope is not closed",
    )
    _require(
        type(fixture["schema_version"]) is int
        and fixture["schema_version"] == 1,
        "baseline fixture schema version is invalid",
    )
    _require(
        fixture["fixture_id"]
        == "leanforge.run.forced-load-baseline",
        "baseline fixture identity is invalid",
    )
    _require(
        fixture["behavior_origin_commit"]
        == BEHAVIOR_ORIGIN_COMMIT,
        "behavior origin commit is invalid",
    )
    _require(
        fixture["byte_baseline_commit"]
        == BYTE_BASELINE_COMMIT,
        "byte baseline commit is invalid",
    )
    _require(
        fixture["measurement"] == MEASUREMENT_DECLARATION,
        "baseline measurement declaration is invalid",
    )
    _require(
        isinstance(fixture["surfaces"], dict),
        "baseline surfaces must be an object",
    )
    _require(
        set(fixture["surfaces"]) == set(SURFACES),
        "baseline surfaces are incomplete",
    )
    for surface, measurement in fixture["surfaces"].items():
        _require(
            isinstance(measurement, dict)
            and set(measurement) == {"nodes", "closures"},
            f"baseline surface envelope is not closed for {surface}",
        )
        nodes = measurement.get("nodes")
        closures = measurement.get("closures")
        _require(
            isinstance(nodes, list) and nodes,
            f"baseline nodes are missing for {surface}",
        )
        _require(
            all(
                isinstance(node, dict)
                and isinstance(node.get("path"), str)
                for node in nodes
            ),
            f"baseline node entries are invalid for {surface}",
        )
        paths = [node.get("path") for node in nodes]
        _require(
            len(paths) == len(set(paths)),
            f"baseline node identity is duplicated for {surface}",
        )
        for node in nodes:
            _require(
                isinstance(node, dict)
                and set(node)
                == {
                    "path", "git_blob_oid", "sha256",
                    "raw_bytes", "words",
                },
                f"baseline node metadata is incomplete for {surface}",
            )
            _validate_logical_path(node["path"])
            _require(
                isinstance(node["git_blob_oid"], str)
                and re.fullmatch(r"[0-9a-f]{40}", node["git_blob_oid"]),
                "Git blob OID must be lowercase SHA-1 hex",
            )
            _require(
                isinstance(node["sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", node["sha256"]),
                "SHA-256 must be lowercase hex",
            )
            _require(
                type(node["raw_bytes"]) is int
                and node["raw_bytes"] >= 0,
                "raw byte count must be a nonnegative integer",
            )
            _require(
                type(node["words"]) is int and node["words"] >= 0,
                "word count must be a nonnegative integer",
            )
        _require(
            isinstance(closures, list) and closures,
            f"baseline closures are missing for {surface}",
        )
        _require(
            all(isinstance(closure, dict) for closure in closures),
            f"baseline closure entries are invalid for {surface}",
        )
        closure_names = [
            closure.get("name") for closure in closures
        ]
        _require(
            all(isinstance(name, str) for name in closure_names),
            f"baseline closure names are invalid for {surface}",
        )
        _require(
            len(closure_names) == len(set(closure_names)),
            f"duplicate closure for {surface}",
        )
        routes = ("direct", "single_risky", "parallel", "external")
        closure_phases = (
            "entry_execution", "route_union", "failure_route_union"
        )
        expected_closure_names = {
            f"{phase}.{route}"
            for phase in closure_phases
            for route in routes
        } | {f"failure_overlay_report.{route}" for route in routes}
        _require(
            set(closure_names) == expected_closure_names,
            f"baseline closure set is incomplete for {surface}",
        )
        node_paths = set(paths)
        for closure in closures:
            _require(
                isinstance(closure, dict),
                f"baseline closure must be an object for {surface}",
            )
            name = closure.get("name")
            is_report = isinstance(name, str) and name.startswith(
                "failure_overlay_report."
            )
            expected_keys = (
                {
                    "name", "derived_from", "instruction_nodes",
                    "forced_load_nodes", "raw_bytes", "words",
                }
                if is_report
                else {
                    "name", "root", "profile", "route", "overlay",
                    "phase", "instruction_nodes", "forced_load_nodes",
                    "raw_bytes", "words",
                }
            )
            _require(
                set(closure) == expected_keys,
                f"baseline closure envelope is not closed for {surface}/{name}",
            )
            for field in ("instruction_nodes", "forced_load_nodes"):
                paths_value = closure[field]
                _require(
                    isinstance(paths_value, list),
                    f"closure {field} must be a list",
                )
                _require(
                    all(isinstance(path, str) for path in paths_value),
                    f"closure {field} paths must be strings",
                )
                _require(
                    len(paths_value) == len(set(paths_value)),
                    f"closure {field} contains duplicate paths",
                )
                for path in paths_value:
                    _validate_logical_path(path)
                    _require(
                        path in node_paths,
                        f"closure {field} contains an unknown path: {path}",
                    )
            _require(
                type(closure["raw_bytes"]) is int
                and closure["raw_bytes"] >= 0,
                "closure raw byte count must be a nonnegative integer",
            )
            _require(
                type(closure["words"]) is int
                and closure["words"] >= 0,
                "closure word count must be a nonnegative integer",
            )
            if is_report:
                route = name.removeprefix("failure_overlay_report.")
                _require(route in routes, f"unknown overlay route: {route}")
                _require(
                    closure["derived_from"]
                    == [
                        f"route_union.{route}",
                        f"failure_route_union.{route}",
                    ],
                    f"overlay derivation is invalid for {surface}/{route}",
                )
            else:
                phase = closure["phase"]
                route = closure["route"]
                _require(
                    phase in closure_phases and route in routes,
                    f"closure route or phase is invalid for {surface}/{name}",
                )
                _require(
                    name == f"{phase}.{route}",
                    f"closure name is not derived from route and phase: {name}",
                )
                _require(
                    closure["root"] == "run"
                    and closure["profile"] == "default",
                    f"closure root or profile is invalid for {surface}/{name}",
                )
                expected_overlay = (
                    "failure" if phase == "failure_route_union" else None
                )
                _require(
                    closure["overlay"] == expected_overlay,
                    f"closure overlay is invalid for {surface}/{name}",
                )
        for route in (
            "direct", "single_risky", "parallel", "external"
        ):
            name = f"failure_overlay_report.{route}"
            matches = [
                closure
                for closure in closures
                if closure.get("name") == name
            ]
            _require(
                len(matches) == 1,
                f"missing predecessor overlay report "
                f"{surface}/{route}",
            )
            overlay = matches[0]
            _require(
                overlay["forced_load_nodes"] == []
                and overlay["raw_bytes"] == 0
                and overlay["words"] == 0,
                f"predecessor forced-load overlay must be "
                f"empty for {surface}/{route}",
            )


def measure_candidate(
    root: Path,
    graph: dict,
    semantic_contract: dict,
) -> dict:
    result = {}
    for surface in SURFACES:
        surface_root = root / surface

        def read(
            path: str, base: Path = surface_root
        ) -> bytes:
            candidate = base / path
            try:
                return candidate.read_bytes()
            except OSError as exc:
                raise LoadContractError(
                    f"cannot read candidate bytes "
                    f"{candidate}: {exc}"
                ) from exc

        result[surface] = _measure_surface(
            graph, semantic_contract, read, None
        )
    return result


def _closures_by_name(
    measurement: dict,
) -> dict[str, dict]:
    return {
        closure["name"]: closure
        for closure in measurement["closures"]
    }


def _closure_delta(
    fixture: dict, candidate: dict
) -> dict:
    result = {}
    for surface in SURFACES:
        predecessor = _closures_by_name(
            fixture["surfaces"][surface]
        )
        current = _closures_by_name(candidate[surface])
        surface_delta = {}
        for name in sorted(predecessor):
            before = predecessor[name]
            after = current[name]
            surface_delta[name] = {
                "instruction_nodes_added": sorted(
                    set(after["instruction_nodes"])
                    - set(before["instruction_nodes"])
                ),
                "instruction_nodes_removed": sorted(
                    set(before["instruction_nodes"])
                    - set(after["instruction_nodes"])
                ),
                "forced_load_nodes_added": sorted(
                    set(after["forced_load_nodes"])
                    - set(before["forced_load_nodes"])
                ),
                "forced_load_nodes_removed": sorted(
                    set(before["forced_load_nodes"])
                    - set(after["forced_load_nodes"])
                ),
                "raw_bytes_delta": (
                    after["raw_bytes"] - before["raw_bytes"]
                ),
                "words_delta": (
                    after["words"] - before["words"]
                ),
            }
        result[surface] = surface_delta
    return result


def _overlay_reports(
    measurements: Mapping[str, dict]
) -> dict:
    result = {}
    for surface in SURFACES:
        closures = _closures_by_name(
            measurements[surface]
        )
        result[surface] = {
            route: closures[
                f"failure_overlay_report.{route}"
            ]
            for route in (
                "direct",
                "single_risky",
                "parallel",
                "external",
            )
        }
    return result


def scoped_product_hash(root: Path) -> str:
    paths = [root / FIXTURE_RELATIVE_PATH]
    paths.extend(
        path
        for path in (root / "src/skills/run").rglob("*")
        if path.is_file()
    )
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = (
            path.relative_to(root).as_posix().encode("utf-8")
        )
        raw = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def verify_baseline(root: Path) -> dict:
    before_hash = scoped_product_hash(root)
    graph, semantic_contract = validate_repository(root)
    fixture = load_json(root / FIXTURE_RELATIVE_PATH)
    validate_fixture(fixture)
    expected_fixture = _build_predecessor_fixture(root)
    fixture_match = fixture == expected_fixture
    _require(
        fixture_match,
        "predecessor fixture does not match exact "
        "Git blob measurement",
    )

    candidate = measure_candidate(
        root, graph, semantic_contract
    )
    overlay_difference = {
        "predecessor": _overlay_reports(
            fixture["surfaces"]
        ),
        "candidate": _overlay_reports(candidate),
    }
    for view_name, view in overlay_difference.items():
        for surface in SURFACES:
            for route, report in view[surface].items():
                _require(
                    report["forced_load_nodes"] == []
                    and report["raw_bytes"] == 0
                    and report["words"] == 0,
                    f"{view_name} forced-load overlay is "
                    f"not empty for {surface}/{route}",
                )

    after_hash = scoped_product_hash(root)
    _require(
        before_hash == after_hash,
        "read-only verification changed fixture or product tree",
    )
    return {
        "predecessor_fixture_match": {
            "matched": fixture_match,
            "behavior_origin_commit": (
                fixture["behavior_origin_commit"]
            ),
            "byte_baseline_commit": (
                fixture["byte_baseline_commit"]
            ),
        },
        "candidate_measurement": candidate,
        "closure_delta": _closure_delta(
            fixture, candidate
        ),
        "failure_overlay_difference": (
            overlay_difference
        ),
        "read_only": {
            "fixture_and_product_hash_before": before_hash,
            "fixture_and_product_hash_after": after_hash,
            "unchanged": before_hash == after_hash,
        },
    }


def clone_graph(graph: dict) -> dict:
    return deepcopy(graph)
