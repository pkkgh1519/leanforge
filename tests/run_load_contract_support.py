from __future__ import annotations

import hashlib
import html
import json
import posixpath
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
CODEX_PLATFORM_PROMPT_RELATIVE_PATH = (
    "platform/codex/skills/run/agents/openai.yaml"
)
CODEX_GENERATED_PROMPT_RELATIVE_PATH = (
    "codex/plugin/skills/run/agents/openai.yaml"
)
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
    "route_topology": {"startup", "graph_preflight", "dispatch"},
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
        "RUN-ROUTE-TOPOLOGY",
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
PACKAGED_MARKDOWN_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9._-])"
    r"(?P<path>[\\/]*(?:[A-Za-z0-9._-]+[\\/])*[A-Za-z0-9._-]+\.md)"
    r"(?![A-Za-z0-9._/\\-])",
    re.IGNORECASE,
)
CODEX_DEFAULT_PROMPT_KEY_RE = re.compile(
    r"(?m)^[ \t]*default_prompt[ \t]*:"
)
CODEX_DEFAULT_PROMPT_LINE_RE = re.compile(
    r'(?m)^[ \t]+default_prompt:[ \t]*'
    r'(?P<quoted>"(?:[^"\\\r\n]|\\.)*")[ \t]*$'
)
PACKAGED_REFERENCE_NAMESPACE_RE = re.compile(
    r"(?<![A-Za-z0-9._-])(?:run[\\/])?references[\\/]",
    re.IGNORECASE,
)
MARKDOWN_HEADING_RE = re.compile(
    r"(?m)^(?P<marks>#{1,6})[ \t]+(?P<title>[^\r\n]+?)[ \t]*$"
)
INSTRUCTION_VERB_RE = re.compile(
    r"\b(?:force[- ]load|preload|load|read|consult|open|inspect)\b",
    re.IGNORECASE,
)
ALLOWED_VISIBLE_INSTRUCTION_VERB_COUNTS = {
    "run/references/foundation-format.md": 1,
    "run/references/graph-contract.md": 2,
    "run/references/harness-format.md": 10,
    "run/references/harness-lifecycle.md": 6,
    "run/references/harness-review.md": 3,
    "run/references/implementer-prompt.md": 1,
    "run/references/orchestration.md": 12,
    "run/references/repo-lens-routing.md": 3,
    "run/references/reviewer-prompt.md": 1,
    "run/references/spec-review-prompt.md": 1,
    "run/SKILL.md": 10,
}
ALLOWED_TOOLS_LINE = (
    "allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Agent, "
    "SendMessage, AskUserQuestion"
)
MARKDOWN_BACKSLASH_ESCAPE_RE = re.compile(
    r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])"
)
MARKDOWN_SYNTAX_WHITESPACE = " \t\r\n"
MARKDOWN_AUTOLINK_RE = re.compile(
    r"<(?:"
    r"[A-Za-z][A-Za-z0-9.+-]{1,31}:"
    r"[^\x00-\x20<>]*"
    r"|[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9]"
    r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*"
    r")>"
)
ALLOWED_INSTRUCTION_VERB_LINE_HASH_COUNTS = {
    "run/references/foundation-format.md": {
        "abf4801fccf675027a690ddaa4e334637740ce5e0c5dd288417e515ac0e94bdf": 1,
    },
    "run/references/graph-contract.md": {
        "09c066872373fd45163bc038527166fae9414bd4c2c36070786fd602bf90cf13": 1,
        "2356527d26c686fcfdafea146eabb2dc0df1aa1b05ce82a4c3f7cbe34c3720ae": 1,
    },
    "run/references/harness-format.md": {
        "1720b824618398f35004cd133b0e76e42dfbe6c91862ff6ce17cbc5f67b5747e": 1,
        "1b179dab2bba8617a6b2dbd4e5ee5f891c7e111df9db140f2d8e4fd3c431633a": 1,
        "22dc212fbc371f0b944135af30c1c2e39f171b28c31c68d0709c11a0a3698cfe": 1,
        "49ec7e52ee933092950ab44e4dc26a8ff3ba71ee8f8dbc7fdadfecb1c4d751c8": 1,
        "5f83698a1ad245cdd6e875f6e0395b23a9eb97a6e4a48c25cbc581a41b7bc7e2": 1,
        "7eec6aaf4ed959b5952e873bc73700f461560aef13b58bdaf7f2e192e949bb82": 1,
        "95b350893a538e9bdcdf1d4762a81dfbecd1910be466bad27eeba71655f2dcd3": 1,
        "d7230a084854d68b4d1deeb0db2ccbcfa159a43338a2616600605c1c4be00410": 1,
        "f5e7f2a3c58d6c6bb2c54c26ca3e23b064a01e6e6cbf24338b890e852fcd52cb": 1,
    },
    "run/references/harness-lifecycle.md": {
        "3adf22458f856b9d3499f6c9ef0bd8c2310ad8f920c9ad4502281097ac6c1106": 1,
        "3bcdfb9b6d8da041b8390e05af73e4b98a04dbf35f1f0e132a6fc022f01edcd2": 1,
        "484646c89b1e06853e1a8427d4520d0df77abd01b26decc2c0840d3e2bc03396": 1,
        "721717c873b2beb0f76ece3ac7646b62d52269478048314318082a00ad0f66c3": 1,
        "7594ef0b5d52bb27265ca9b2abad7db3d4e345e1cf45c3ae4333c0c5bca0828e": 1,
        "9c93fbf37f79571c05af3b0e36a4e4aec69a814e8d8de035200794abcfb1f9e8": 1,
    },
    "run/references/harness-review.md": {
        "0fdde1cf3cb256be3664c9edf0f46b81628dc95daf8a27e4007269b151547496": 1,
        "2f3501c1639931c0835d6ce2bc22d68c5de5e88801714efb96d940a0cef4abdc": 1,
    },
    "run/references/implementer-prompt.md": {
        "03f22e4c7aaa98a2120581f63127b8056f2bac1a16ef1de8cd42424144a8ccc0": 1,
    },
    "run/references/orchestration.md": {
        "5a34be11bc3164e4f57c68fe63e7d035cd720034f2b032358825de1bd3101b4f": 1,
        "5b909c1fa7ab6e8d702126a8eb3a346f1739600cf4185532ac16d78d3812e829": 1,
        "5d7bf406427511af29205ffed74e109f7347fc77198fe90a85d8796a660fa256": 1,
        "6bc0f6d35ae53de8af70495994c86516592cd6e7ca8f9e09b78acdf537222b74": 1,
        "6dddb79f1eb843cabac81dc931b4935077d9d2a7d7d2a468180adc95e0c5314d": 1,
        "b4b5992cc4bfd0a648c9cea4238b0d6b34c98531a565dbc8faa62a37fa7d47b2": 1,
        "b78186996deae300667f59eb46d3e5d24a238353d3d8e80b726d181f3c3478d0": 1,
        "bdc9d2ecda296bfa746409d1644fb35928c3419fa8d5d4711048fdeada1807f7": 1,
        "c3d08edcb0d7ecfaa4eb3104164ecabd4a13e9b1c506ba64d38fa744afc93209": 1,
        "c815edafce071de8fdfb20966a21dc2e1809a9e90c94ea41661e61eb22bcee29": 1,
        "cef18b9b3378558591faaaa687626828a9ec2e5c79ddf6c9500a81162b886fdf": 1,
        "f794501c1ee0444c40a971bff91fb0bfb6e2bd21f12586429bb88088d670a993": 1,
    },
    "run/references/repo-lens-routing.md": {
        "3624a17406ddfc1f0264b5e5477be522b80439a12339ab447cc9242bf8f438e8": 1,
        "c53d8627667c624c470e9e3dd99f935eb7315775198954833ccf0a48924ca738": 1,
        "e8f031a3594b71409233a9eba19244057a896c4160ad0085ccc12ddbef7ff502": 1,
    },
    "run/references/reviewer-prompt.md": {
        "49d792a1c00fdfbef0a395a00c3eebd6a001c32c5cfc162c161731244906379a": 1,
    },
    "run/references/spec-review-prompt.md": {
        "cd32883f3e90a7449c4d4917f38622cfa3128b799f07f18f4bbd8b2de5fd6133": 1,
    },
    "run/SKILL.md": {
        "0101e024c1acc647300593929492abf5a158c23f36e7806ea2254876e571a5c2": 1,
        "71bb69cb6487b4c80d25c2e7916600e113be33087968a2d5cf41fcf62e27fbc7": 1,
        "7d6225bcd626c33401ae0b81394c0c5db9b2f0dceb6ab32e273d12d486617c7b": 1,
        "8fd43a9adaf04c63d38ae7897bb82f0eeabfc7f99d828a4b9b9f9e421d3b6e04": 1,
        "92ea361e00c850e197964b8ba12617b2bbc492d8fa1acf8026f2efab5c83f550": 1,
        "b8a5e1ea986fe5599d33068abea8a9468f92244b2c3f756a9afbe015451c9643": 1,
        "c013b26f0330ec4faaaf20e839bc144ecf910cce9cca2f2291e70a42e84f5e72": 1,
        "d537e0b4b3a0853040f837f8474663ecbf0eb291ed0b7fbf355cb6eb62c86278": 1,
        "e8a0f1c10e5f89b5ee85034aff46a1242a34cb19b6fbc12cc85c3429418d5b5c": 1,
        "fff9c2af10e57c2572a5f5fc4959b2f06f344fd4af2e4f72aad15566ac06a871": 1,
    },
}
YAML_KEY_TOKEN_RE = re.compile(
    r'(?P<key>"(?:[^"\\\r\n]|\\.)*"|'
    r"'(?:''|[^'\r\n])*'|[A-Za-z_][A-Za-z0-9_-]*)[ \t]*:"
)
YAML_FORBIDDEN_COMPLEX_KEY_RE = re.compile(
    r"(?m)^[ \t]*(?:\?|<<[ \t]*:)"
)
YAML_FORBIDDEN_ANCHOR_ALIAS_RE = re.compile(
    r"(?m)(?:^|[ \t])(?:&|\*)[A-Za-z0-9_-]+(?=[ \t:]|$)"
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

# Closed inventory of accepted non-marker packaged-Markdown occurrences at
# their named Markdown section seam. Structured markers are removed before the
# section hash so discovery remains heading-independent; adjacent prose still
# changes the section hash. Each value is the exact occurrence count.
ALLOWED_REFERENCE_SECTION_CONTEXT_COUNTS = {
    "run/SKILL.md": {
        ("# Leanforge:Run", "78e2201113d621a4f6e2d640343d58facdb8983a0f41e14c4f106901ab302d8e", "legacy"): 1,
        ("## Core principles", "49fa4f2fabfc8c04cb8da3f30c90fffadb57d30f6b5de071a3318f93dd6ce12d", "reference"): 3,
        ("## Flow", "6e4fc763fa1d328683dbc12a9aa1f0d53ecea5743e1973e6d875ae44a3643824", "reference"): 1,
        ("## Graph validation", "c8814c65fc7668994e730a71545df50126ea3a697641aa892f1184cd144671d4", "reference"): 1,
        ("## Input and preconditions", "a11c61bcb25649111b76ac4ab66a06f888a58e275d0b76f3fb275a0c539b0653", "reference"): 1,
    },
    "run/references/foundation-format.md": {
        ("# foundation-format.md — the Project Foundation section (handoff, first cycle only)", "422d82382ac169207b04e1b7beb5f31dcb078e96000954a0210e91ba043720ac", "reference"): 2,
        ("## Content quality", "f5850cae996929a5416c40ecc55618bc5526a730ad1d4025d2a85ce6cd586ffc", "reference"): 1,
        ("## First-cycle precondition (Foundation is always present — no degrade)", "3df2c379f2fd0e66115233eceb5ce38e20382eab13ac1b9f8b8bc960c2847b0a", "reference"): 1,
        ("## How `Run` uses it (dual use)", "6b5c7254892dd45641468b4e3846fadd094e5d1bc1a5c456c8fb21efb70a0d0d", "reference"): 1,
    },
    "run/references/graph-contract.md": {
        ("# graph-contract.md — the Execution Graph, from Run's side (parse contract)", "9bd951ffc25a8231eca06116efb2b7b80ece238d8165277b63dfc2b2c08d78a4", "reference"): 1,
        ("## The graph — the only machine-parsed part of the 3-doc", "233f635dbe6b3fea792c3a902e1b491bae08866745aab9cbdc8f9e70eec1b105", "reference"): 1,
        ("## What is NOT in the graph (do not look for it here)", "be5d4eaeb22ec4a339b0ce03b5fe4314c3b4830dc0d1f8b8ea6c1d3fefad684b", "reference"): 1,
    },
    "run/references/harness-format.md": {
        ("# harness-format.md — the project harness spec (force-load)", "3baadc494409f58d7eff591fe5b8684a8ea4936a154c8f40cb7edffbb3ccc5a8", "reference"): 1,
        ("## Execution discipline (when authoring the harness)", "af9d37d656be94ba8ff9c9b85ae8c0d230650879dad0174724b5e46dbb1877f3", "reference"): 1,
    },
    "run/references/harness-lifecycle.md": {
        ("# harness-lifecycle.md — Run's harness create / update / archive (force-load)", "38464ed56f35f7e8eda628742e97848ec511483392399cb9f43d14b9f5bf4c5b", "reference"): 1,
        ("## Delta — update only the changed scope", "55a0e9b1e420a8c83bc2be91eb6dd1f28e2362b0e9974c99fc6401f86751efbf", "reference"): 1,
        ("## First cycle — create the whole harness", "3d35d5d71ac6ce7ece8d3be8976a67eb37f8f58e20f11778355c16e397e4a9b9", "reference"): 1,
        ("### Idempotent archive retry", "fcc25afa730c0491a394657586b6421a2a9fa98e887d662195e3aaa679932a38", "reference"): 1,
    },
    "run/references/harness-review.md": {
        ("# harness-review.md — verifying a generated/updated harness (force-load)", "a41ee7d60f567dcd1b1cdf7b9f7b46a6da9719c1d98649d6f8443994f24e81de", "reference"): 2,
        ("## Dimension 1 — content (does each file substantively meet its spec?)", "bdf2ac5d30f83799056f33c494926d50b1403e219524f4c32feaa9c5cc6b6b98", "reference"): 1,
        ("## Dimension 3 — completeness (required files present)", "9ef9cb65d0da11dbdfcc5849e1add5411e7796168f8a3d8b38d4906c88b000ec", "reference"): 1,
    },
    "run/references/implementer-prompt.md": {
        ("# implementer-prompt.md — the implementer subagent prompt", "3ef1b8ee8c8a9260a1204dc7749fa590486f163830a824bad00a3df7482c64ea", "reference"): 2,
        ("## Required elements (every implementer prompt must pin)", "3bda3e41c2c47d8dd064446ac12484ec53d01c228f7c61d06bbeaf3c5420fb1d", "reference"): 1,
    },
    "run/references/orchestration.md": {
        ("# orchestration.md — wave lifecycle (force-load)", "bccbabbdfd04e96d05b128098355a211039259ca88fd8d06d05253468409c0b8", "reference"): 1,
        ("## Reporting principle", "a91e2f4ee16d40c544aba7369084b957abfcdff589ab59eea9c3d07bf62d89c6", "reference"): 1,
        ("## Sequential wave — execution", "24638c1e4fa2267165557bb0e2358fae11fbe904ae133109dace05976202c81d", "reference"): 1,
        ("## Wave scheduling", "7f0f739ffb697195f2fea85373f02e400155dc73c57a230776b094908a931859", "reference"): 1,
        ("### Parallel wave (multiple tasks)", "f01a21bdd6883740faa4a37d2eaf58e8dc17bfbc9d4b2652bae210d56a59dcbf", "reference"): 1,
    },
    "run/references/repo-lens-routing.md": {
        ("# repo-lens-routing.md — repo-local review/explore lenses", "160fdcc6d380bf5c5c45a5f0b1b4569448f1913bbd206a86c6e1b9200b8c6183", "reference"): 1,
    },
    "run/references/reviewer-prompt.md": {
        ("# reviewer-prompt.md — final review (spec + code + harness)", "c1048b9d252a184e36bb354e94f18a740be9eef5e1cc0fbc5ac0c07c26a4e279", "reference"): 4,
        ("## Scope — four lenses, one pass", "14baa1ee8025f2e2f4705e5b869225835a0087c9ccba92b6ac5ee10aab79be01", "reference"): 2,
    },
    "run/references/spec-review-prompt.md": {
        ("# spec-review-prompt.md — conditional mid-run spec review", "471f63041ebe01213ecaa8e299c7c8e4f84f8d13cf89434a1e4aac0d379316fd", "reference"): 3,
    },
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


def _is_valid_markdown_link_target(
    value: str,
    *,
    allow_empty_destination: bool = True,
) -> bool:
    if re.search(r"\r?\n[ \t]*\r?\n", value):
        return False

    cursor = 0
    while (
        cursor < len(value)
        and value[cursor] in MARKDOWN_SYNTAX_WHITESPACE
    ):
        cursor += 1
    if cursor == len(value):
        return allow_empty_destination

    has_destination = True
    if value[cursor] == "<":
        cursor += 1
        while cursor < len(value):
            character = value[cursor]
            if (
                character == "\\"
                and cursor + 1 < len(value)
                and MARKDOWN_BACKSLASH_ESCAPE_RE.fullmatch(
                    value[cursor : cursor + 2]
                )
            ):
                cursor += 2
                continue
            if character in "\r\n<":
                return False
            if character == ">":
                cursor += 1
                break
            cursor += 1
        else:
            return False
    else:
        destination_start = cursor
        depth = 0
        while (
            cursor < len(value)
            and value[cursor] not in MARKDOWN_SYNTAX_WHITESPACE
        ):
            character = value[cursor]
            if 0 < ord(character) < 0x20 or ord(character) == 0x7F:
                return False
            if (
                character == "\\"
                and cursor + 1 < len(value)
                and MARKDOWN_BACKSLASH_ESCAPE_RE.fullmatch(
                    value[cursor : cursor + 2]
                )
            ):
                cursor += 2
                continue
            if character in "<>":
                return False
            if character == "(":
                depth += 1
                if depth > 32:
                    return False
            elif character == ")":
                if depth == 0:
                    return False
                depth -= 1
            cursor += 1
        if cursor == destination_start or depth != 0:
            return False

    if cursor == len(value):
        return has_destination or allow_empty_destination

    separator_start = cursor
    while (
        cursor < len(value)
        and value[cursor] in MARKDOWN_SYNTAX_WHITESPACE
    ):
        cursor += 1
    if cursor == len(value):
        return has_destination or allow_empty_destination
    if cursor == separator_start:
        return False

    delimiter = value[cursor]
    if delimiter not in {"\"", "'", "("}:
        return False
    closing_delimiter = ")" if delimiter == "(" else delimiter
    cursor += 1
    while cursor < len(value):
        character = value[cursor]
        if (
            character == "\\"
            and cursor + 1 < len(value)
            and MARKDOWN_BACKSLASH_ESCAPE_RE.fullmatch(
                value[cursor : cursor + 2]
            )
        ):
            cursor += 2
            continue
        if delimiter == "(" and character == "(":
            return False
        if character == closing_delimiter:
            cursor += 1
            break
        cursor += 1
    else:
        return False

    return value[cursor:].strip(MARKDOWN_SYNTAX_WHITESPACE) == ""


def _is_markdown_escaped(value: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and value[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _markdown_autolink_ranges(
    value: str,
    opaque_ranges: tuple[tuple[int, int], ...] = (),
) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    parsed_value = value.replace("\x00", "\uFFFD")
    for match in MARKDOWN_AUTOLINK_RE.finditer(parsed_value):
        if _is_markdown_escaped(value, match.start()):
            continue
        if any(
            range_start <= match.start() < range_end
            for range_start, range_end in opaque_ranges
        ):
            continue
        ranges.append(match.span())
    return tuple(ranges)


def _markdown_code_span_ranges(value: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    index = 0
    while index < len(value):
        if value[index] != "`" or _is_markdown_escaped(value, index):
            index += 1
            continue
        opener_start = index
        while index < len(value) and value[index] == "`":
            index += 1
        opener_size = index - opener_start
        cursor = index
        while cursor < len(value):
            closing_start = value.find("`", cursor)
            if closing_start < 0:
                break
            closing_end = closing_start
            while closing_end < len(value) and value[closing_end] == "`":
                closing_end += 1
            if closing_end - closing_start == opener_size:
                ranges.append((opener_start, closing_end))
                index = closing_end
                break
            cursor = closing_end
        else:
            index = len(value)
            continue
        if cursor >= len(value) or closing_start < 0:
            index = opener_start + opener_size
    return tuple(ranges)


def _split_commonmark_lines(
    value: str,
    *,
    keepends: bool = False,
) -> list[str]:
    lines: list[str] = []
    start = 0
    index = 0
    while index < len(value):
        if value[index] not in "\r\n":
            index += 1
            continue
        end = (
            index + 2
            if value[index] == "\r"
            and index + 1 < len(value)
            and value[index + 1] == "\n"
            else index + 1
        )
        lines.append(
            value[start:end] if keepends else value[start:index]
        )
        start = end
        index = end
    if start < len(value):
        lines.append(value[start:])
    return lines


def _count_commonmark_line_endings(value: str) -> int:
    return len(re.findall(r"\r\n|\r|\n", value))


def _markdown_inline_block_ids(value: str) -> tuple[int, ...]:
    lines = _split_commonmark_lines(value, keepends=True)
    contexts = _markdown_container_contexts(lines)
    fenced_lines = _fenced_code_line_flags(lines, contexts)
    html_block_lines = _html_block_line_flags(lines, contexts)

    def line_is_noninterrupting_list_marker(
        line: str,
        paragraph_key: MarkdownContainerKey,
        current_key: MarkdownContainerKey,
    ) -> bool:
        if (
            len(paragraph_key) >= len(current_key)
            or current_key[: len(paragraph_key)] != paragraph_key
            or current_key[len(paragraph_key)][0] != "list"
        ):
            return False
        parent_body = _markdown_body_at_container_depth(
            line, current_key, len(paragraph_key)
        )
        marker = MARKDOWN_LIST_MARKER_RE.match(parent_body)
        if marker is None:
            return False
        marker_text, _, item_body = _markdown_list_marker_parts(marker)
        if not item_body.strip(" \t"):
            return True
        return marker_text[0].isdigit() and int(marker_text[:-1]) != 1

    block_ids: list[int] = []
    block_id = 0
    previous_key: MarkdownContainerKey | None = None
    previous_blank = True
    previous_structural = True
    for line, (key, body), fenced, html_block in zip(
        lines, contexts, fenced_lines, html_block_lines
    ):
        noninterrupting_list = (
            previous_key is not None
            and not previous_blank
            and not previous_structural
            and line_is_noninterrupting_list_marker(
                line, previous_key, key
            )
        )
        lazy_list_alias = False
        if (
            previous_key is not None
            and not previous_blank
            and not previous_structural
            and len(previous_key) < len(key)
            and key[: len(previous_key)] == previous_key
            and key[len(previous_key)][0] == "list"
        ):
            parent_body = _markdown_body_at_container_depth(
                line, key, len(previous_key)
            )
            lazy_list_alias = (
                MARKDOWN_LIST_MARKER_RE.match(parent_body) is None
            )
        lazy_ancestor_alias = (
            previous_key is not None
            and not previous_blank
            and not previous_structural
            and len(key) < len(previous_key)
            and previous_key[: len(key)] == key
        )
        same_paragraph_container = (
            key == previous_key
            or noninterrupting_list
            or lazy_list_alias
            or lazy_ancestor_alias
        )
        source_blank = not body.strip(" \t")
        blank = source_blank and not noninterrupting_list
        open_paragraph = (
            not previous_blank
            and not previous_structural
            and same_paragraph_container
        )
        setext_body = body
        if (
            previous_key is not None
            and len(previous_key) < len(key)
            and key[: len(previous_key)] == previous_key
        ):
            setext_body = _markdown_body_at_container_depth(
                line, key, len(previous_key)
            )
        setext_underline = (
            open_paragraph
            and MARKDOWN_SETEXT_UNDERLINE_RE.fullmatch(setext_body)
            is not None
        )
        indented_code = (
            _markdown_prefix_columns(body) >= 4 and not open_paragraph
        )
        structural = (
            fenced
            or html_block
            or indented_code
            or MARKDOWN_ATX_HEADING_RE.match(body) is not None
            or MARKDOWN_THEMATIC_BREAK_RE.fullmatch(body) is not None
            or setext_underline
        )
        continues_inline_block = (
            not blank
            and not structural
            and open_paragraph
        )
        if not continues_inline_block:
            block_id += 1
        block_ids.extend(block_id for _ in line)
        if not (
            noninterrupting_list
            or lazy_list_alias
            or lazy_ancestor_alias
        ):
            previous_key = key
        previous_blank = blank
        previous_structural = structural
    return tuple(block_ids)


def _markdown_inline_html_ranges(
    value: str,
    excluded_ranges: tuple[tuple[int, int], ...] = (),
    block_ids: tuple[int, ...] | None = None,
) -> tuple[tuple[int, int], ...]:
    if block_ids is None:
        block_ids = _markdown_inline_block_ids(value)
    tag_re = re.compile(
        r"(?:</[A-Za-z][A-Za-z0-9-]*[ \t\r\n]*>"
        r"|<[A-Za-z][A-Za-z0-9-]*"
        r"(?:[ \t\r\n]+[A-Za-z_:][A-Za-z0-9_.:-]*"
        r"(?:[ \t\r\n]*=[ \t\r\n]*"
        r"(?:[^ \t\r\n\"'=<>`]+|'[^']*'|\"[^\"]*\")"
        r")?)*[ \t\r\n]*/?>)"
    )
    opaque_patterns = (
        re.compile(
            r"<!--(?!>|->)(?:(?!--).)*(?<!-)-->", re.DOTALL
        ),
        re.compile(r"<\?.*?\?>", re.DOTALL),
        re.compile(r"<!\[CDATA\[.*?\]\]>", re.DOTALL),
        re.compile(r"<![A-Z][^>]*>", re.DOTALL),
    )
    ranges: list[tuple[int, int]] = []
    index = 0
    while index < len(value):
        if (
            value[index] != "<"
            or _is_markdown_escaped(value, index)
            or any(start <= index < end for start, end in excluded_ranges)
        ):
            index += 1
            continue
        line_start = value.rfind("\n", 0, index) + 1
        line_prefix = value[line_start:index]
        if (
            not line_prefix.strip(" \t")
            and _markdown_prefix_columns(line_prefix) >= 4
        ):
            index += 1
            continue
        matches = [
            match
            for pattern in (*opaque_patterns, tag_re)
            if (match := pattern.match(value, index)) is not None
            and re.search(
                r"\r?\n[ \t]*\r?\n",
                value[index : match.end()],
            )
            is None
            and not any(
                start < match.end() and index < end
                for start, end in excluded_ranges
            )
            and match.end() > index
            and block_ids[index] == block_ids[match.end() - 1]
        ]
        if not matches:
            index += 1
            continue
        match = min(matches, key=lambda candidate: candidate.end())
        ranges.append((index, match.end()))
        index = match.end()
    return tuple(ranges)



def _markdown_prose_code_ranges(
    value: str,
) -> tuple[tuple[int, int], ...]:
    lines = _split_commonmark_lines(value, keepends=True)
    contexts = _markdown_container_contexts(lines)
    fenced_lines = _fenced_code_line_flags(lines, contexts)
    html_block_lines = _html_block_line_flags(lines, contexts)
    block_ids = _markdown_inline_block_ids(value)
    ranges: list[tuple[int, int]] = []
    offset = 0
    for line, (_, body), fenced, html_block in zip(
        lines, contexts, fenced_lines, html_block_lines
    ):
        line_end = offset + len(line)
        starts_new_inline_block = (
            offset == 0 or block_ids[offset] != block_ids[offset - 1]
        )
        if (
            fenced
            or html_block
            or (
                _markdown_prefix_columns(body) >= 4
                and starts_new_inline_block
            )
        ):
            ranges.append((offset, line_end))
        offset = line_end

    index = 0
    while index < len(value):
        block_id = block_ids[index]
        end = index + 1
        while end < len(value) and block_ids[end] == block_id:
            end += 1
        if not any(start < end and index < stop for start, stop in ranges):
            for start, stop in _markdown_code_span_ranges(value[index:end]):
                ranges.append((index + start, index + stop))
        index = end
    return tuple(sorted(ranges))



def _strip_markdown_link_targets(
    value: str,
    reference_labels: frozenset[str],
    *,
    preserve_line_boundaries: bool = False,
) -> str:
    inline_block_ids = _markdown_inline_block_ids(value)
    inline_lines = _split_commonmark_lines(value, keepends=True)
    inline_contexts = _markdown_container_contexts(inline_lines)
    inline_line_spans: list[tuple[int, int, int, str]] = []
    line_start = 0
    paragraph_key: MarkdownContainerKey | None = None
    for line, (key, body) in zip(inline_lines, inline_contexts):
        line_end = line_start + len(line)
        if line.endswith("\r\n"):
            content_end = line_end - 2
        elif line.endswith(("\r", "\n")):
            content_end = line_end - 1
        else:
            content_end = line_end
        projected_body = body
        same_inline_block = (
            line_start > 0
            and line_start < len(inline_block_ids)
            and inline_block_ids[line_start]
            == inline_block_ids[line_start - 1]
        )
        if not same_inline_block:
            paragraph_key = key
        if (
            same_inline_block
            and paragraph_key is not None
            and len(paragraph_key) < len(key)
            and key[: len(paragraph_key)] == paragraph_key
            and key[len(paragraph_key)][0] == "list"
        ):
            parent_body = _markdown_body_at_container_depth(
                line, key, len(paragraph_key)
            )
            marker = MARKDOWN_LIST_MARKER_RE.match(parent_body)
            if marker is not None:
                marker_text, _, item_body = _markdown_list_marker_parts(
                    marker
                )
                if (
                    not item_body.strip(" \t")
                    or (
                        marker_text[0].isdigit()
                        and int(marker_text[:-1]) != 1
                    )
                ):
                    projected_body = parent_body
        inline_line_spans.append(
            (line_start, content_end, line_end, projected_body)
        )
        line_start = line_end

    def project_inline_span(start: int, end: int) -> str:
        pieces: list[str] = []
        first_line = True
        for line_start, content_end, line_end, body in inline_line_spans:
            if end <= line_start:
                break
            if start >= line_end:
                continue

            if first_line:
                content_start = max(start, line_start)
                pieces.append(value[content_start : min(end, content_end)])
                first_line = False
            else:
                trailing_source = max(0, content_end - end)
                projected_end = max(0, len(body) - trailing_source)
                pieces.append(body[:projected_end])

            newline_start = max(start, content_end)
            newline_end = min(end, line_end)
            if newline_start < newline_end:
                pieces.append(value[newline_start:newline_end])
        return "".join(pieces)

    def link_text_opener(
        output: list[str],
        source_positions: list[int],
        current_source_index: int,
    ) -> int | None:
        bracket_depth = 0
        current_block_id = inline_block_ids[current_source_index]
        for output_index in range(len(output) - 1, -1, -1):
            source_position = source_positions[output_index]
            if inline_block_ids[source_position] != current_block_id:
                break
            if in_code_span(source_position):
                continue
            character = output[output_index]
            if character not in {"[", "]"}:
                continue
            backslashes = 0
            probe = output_index - 1
            while probe >= 0 and output[probe] == "\\":
                backslashes += 1
                probe -= 1
            if backslashes % 2 == 1:
                continue
            if character == "]":
                bracket_depth += 1
                continue
            if bracket_depth:
                bracket_depth -= 1
                continue
            return output_index
        return None

    def is_image_opener(output: list[str], opener: int) -> bool:
        return (
            opener > 0
            and output[opener - 1] == "!"
            and not _is_markdown_escaped("".join(output), opener - 1)
        )

    def label_has_autolink(
        label_text: str, label_image_tokens: list[bool]
    ) -> bool:
        html_ranges = _markdown_inline_html_ranges(label_text)
        visible_label = "".join(
            " "
            if image_token
            or any(start <= index < end for start, end in html_ranges)
            else character
            for index, (character, image_token) in enumerate(
                zip(label_text, label_image_tokens)
            )
        )
        return bool(
            _markdown_autolink_ranges(
                visible_label,
                _markdown_code_span_ranges(visible_label),
            )
        )

    def unwrap_link_text(
        output: list[str],
        link_tokens: list[bool],
        image_tokens: list[bool],
        source_positions: list[int],
        current_source_index: int,
    ) -> bool:
        opener = link_text_opener(
            output, source_positions, current_source_index
        )
        if opener is None:
            return False
        image = is_image_opener(output, opener)
        label_text = "".join(output[opener + 1 :])
        if not image and (
            any(
                link_token and not image_token
                for link_token, image_token in zip(
                    link_tokens[opener + 1 :],
                    image_tokens[opener + 1 :],
                )
            )
            or label_has_autolink(
                label_text, image_tokens[opener + 1 :]
            )
        ):
            return False

        del output[opener]
        del link_tokens[opener]
        del image_tokens[opener]
        del source_positions[opener]
        if image:
            del output[opener - 1]
            del link_tokens[opener - 1]
            del image_tokens[opener - 1]
            del source_positions[opener - 1]
            for token_index in range(opener - 1, len(link_tokens)):
                link_tokens[token_index] = False
                image_tokens[token_index] = True
            return True
        for token_index in range(opener, len(link_tokens)):
            link_tokens[token_index] = True
        return True

    def mark_shortcut_reference(
        output: list[str],
        link_tokens: list[bool],
        image_tokens: list[bool],
        source_positions: list[int],
        current_source_index: int,
    ) -> None:
        opener = link_text_opener(
            output, source_positions, current_source_index
        )
        if opener is None:
            return
        if is_image_opener(output, opener):
            label_text = "".join(output[opener + 1 :])
            label = _normalize_markdown_reference_label(label_text)
            if (
                label not in reference_labels
                or any(link_tokens[opener + 1 :])
            ):
                return
            for token_index in range(opener - 1, len(link_tokens)):
                link_tokens[token_index] = False
                image_tokens[token_index] = True
            return
        label = _normalize_markdown_reference_label(
            "".join(output[opener + 1 :])
        )
        if label not in reference_labels:
            return
        for token_index in range(opener + 1, len(link_tokens)):
            link_tokens[token_index] = True

    code_ranges = list(_markdown_prose_code_ranges(value))
    code_ranges.extend(
        _markdown_inline_html_ranges(
            value, tuple(code_ranges), inline_block_ids
        )
    )
    code_ranges.extend(_markdown_autolink_ranges(value, tuple(code_ranges)))

    def in_code_span(position: int) -> bool:
        return any(start <= position < end for start, end in code_ranges)

    output: list[str] = []
    link_tokens: list[bool] = []
    image_tokens: list[bool] = []
    source_positions: list[int] = []
    index = 0
    while index < len(value):
        if (
            value.startswith("](", index)
            and not _is_markdown_escaped(value, index)
            and not in_code_span(index)
        ):
            depth = 1
            cursor = index + 2
            target_block_id = inline_block_ids[index]
            angle_destination = (
                cursor < len(value) and value[cursor] == "<"
            )
            quote_delimiter: str | None = None
            parenthesized_title = False
            separator_seen = False
            while cursor < len(value):
                if inline_block_ids[cursor] != target_block_id:
                    break
                character = value[cursor]
                if character == "\\" and cursor + 1 < len(value):
                    cursor += 2
                    continue

                if quote_delimiter is not None:
                    if character == quote_delimiter:
                        quote_delimiter = None
                    cursor += 1
                    continue

                if parenthesized_title:
                    if character == ")":
                        parenthesized_title = False
                        depth -= 1
                    cursor += 1
                    continue

                if character in "\r\n":
                    next_cursor = cursor + 1
                    if (
                        character == "\r"
                        and next_cursor < len(value)
                        and value[next_cursor] == "\n"
                    ):
                        next_cursor += 1
                    blank_probe = next_cursor
                    while (
                        blank_probe < len(value)
                        and value[blank_probe] in " \t"
                    ):
                        blank_probe += 1
                    if angle_destination or (
                        blank_probe < len(value)
                        and value[blank_probe] in "\r\n"
                    ):
                        break
                    if depth == 1:
                        separator_seen = True
                    cursor = next_cursor
                    continue

                if angle_destination:
                    if character == ">":
                        angle_destination = False
                    cursor += 1
                    continue

                if character in MARKDOWN_SYNTAX_WHITESPACE:
                    if depth == 1:
                        separator_seen = True
                    cursor += 1
                    continue

                if depth == 1 and separator_seen:
                    if character in {"\"", "'"}:
                        quote_delimiter = character
                        cursor += 1
                        continue
                    if character == "(":
                        parenthesized_title = True
                        depth += 1
                        cursor += 1
                        continue

                if depth == 1:
                    separator_seen = False
                if character == "(":
                    depth += 1
                    if depth > 33:
                        break
                elif character == ")":
                    depth -= 1
                    if depth == 0:
                        break
                cursor += 1
            if depth == 0:
                candidate = project_inline_span(index + 2, cursor)
                if (
                    _is_valid_markdown_link_target(candidate)
                    and unwrap_link_text(
                        output,
                        link_tokens,
                        image_tokens,
                        source_positions,
                        index,
                    )
                    ):
                    if preserve_line_boundaries:
                        preserved_newlines = _count_commonmark_line_endings(
                            value[index : cursor + 1]
                        )
                        output.extend("\n" * preserved_newlines)
                        link_tokens.extend(False for _ in range(preserved_newlines))
                        image_tokens.extend(False for _ in range(preserved_newlines))
                        source_positions.extend(
                            index for _ in range(preserved_newlines)
                        )
                        if cursor + 1 == len(value) and preserved_newlines:
                            output.append(" ")
                            link_tokens.append(False)
                            image_tokens.append(False)
                            source_positions.append(index)
                    index = cursor + 1
                    continue
        elif (
            value.startswith("][", index)
            and not _is_markdown_escaped(value, index)
            and not in_code_span(index)
        ):
            cursor = index + 2
            target_block_id = inline_block_ids[index]
            closed = False
            while cursor < len(value):
                if inline_block_ids[cursor] != target_block_id:
                    break
                character = value[cursor]
                if character in "\r\n":
                    next_cursor = cursor + 1
                    if (
                        character == "\r"
                        and next_cursor < len(value)
                        and value[next_cursor] == "\n"
                    ):
                        next_cursor += 1
                    blank_probe = next_cursor
                    while (
                        blank_probe < len(value)
                        and value[blank_probe] in " \t"
                    ):
                        blank_probe += 1
                    if (
                        blank_probe < len(value)
                        and value[blank_probe] in "\r\n"
                    ):
                        break
                    cursor = next_cursor
                    continue
                if character == "\\" and cursor + 1 < len(value):
                    cursor += 2
                    continue
                if character == "]" and not _is_markdown_escaped(
                    value, cursor
                ):
                    label = _normalize_markdown_reference_label(
                        project_inline_span(index + 2, cursor)
                    )
                    if not label:
                        opener = link_text_opener(
                            output, source_positions, index
                        )
                        if opener is not None:
                            label = _normalize_markdown_reference_label(
                                "".join(output[opener + 1 :])
                            )
                    if (
                        label in reference_labels
                        and unwrap_link_text(
                        output,
                        link_tokens,
                        image_tokens,
                        source_positions,
                        index,
                    )
                    ):
                        if preserve_line_boundaries:
                            preserved_newlines = (
                                _count_commonmark_line_endings(
                                    value[index : cursor + 1]
                                )
                            )
                            output.extend("\n" * preserved_newlines)
                            link_tokens.extend(
                                False for _ in range(preserved_newlines)
                            )
                            image_tokens.extend(
                                False for _ in range(preserved_newlines)
                            )
                            source_positions.extend(
                                index for _ in range(preserved_newlines)
                            )
                            if cursor + 1 == len(value) and preserved_newlines:
                                output.append(" ")
                                link_tokens.append(False)
                                image_tokens.append(False)
                                source_positions.append(index)
                        index = cursor + 1
                        closed = True
                    break
                cursor += 1
            if closed:
                continue
        if (
            value[index] == "]"
            and not _is_markdown_escaped(value, index)
            and not in_code_span(index)
            and (index + 1 >= len(value) or value[index + 1] not in "[(")
        ):
            mark_shortcut_reference(
                output,
                link_tokens,
                image_tokens,
                source_positions,
                index,
            )
        output.append(value[index])
        link_tokens.append(False)
        image_tokens.append(False)
        source_positions.append(index)
        index += 1
    return "".join(output)


def _normalize_markdown_reference_label(value: str) -> str:
    value = re.sub(r"[ \t\r\n]+", " ", value)
    return value.strip(" \t\r\n").casefold()


def _split_blockquote_container(body: str) -> tuple[int, str]:
    depth = 0
    while True:
        match = re.match(r"^ {0,3}>[ \t]?", body)
        if match is None:
            return depth, body
        depth += 1
        body = body[match.end() :]


MarkdownContainerFrame = tuple[str, int, int]
MarkdownContainerKey = tuple[MarkdownContainerFrame, ...]
ROOT_MARKDOWN_CONTAINER: MarkdownContainerKey = ()
MARKDOWN_QUOTE_MARKER_RE = re.compile(r"^ {0,3}>[ \t]?")
MARKDOWN_THEMATIC_BREAK_RE = re.compile(
    r"^ {0,3}(?:"
    r"(?:\*[ \t]*){3,}"
    r"|(?:_[ \t]*){3,}"
    r"|(?:-[ \t]*){3,}"
    r")[ \t]*$"
)
MARKDOWN_ATX_HEADING_RE = re.compile(
    r"^ {0,3}#{1,6}(?:[ \t]+|$)"
)
MARKDOWN_LIST_MARKER_RE = re.compile(
    r"^(?P<indent> {0,3})"
    r"(?P<marker>[-+*]|[0-9]{1,9}[.)])"
    r"(?P<after>[ \t].*|)$"
)


def _markdown_advance_column(column: int, character: str) -> int:
    if character == "\t":
        return column + (4 - column % 4)
    return column + 1


def _markdown_expand_tabs(value: str) -> str:
    return value.expandtabs(4)


def _markdown_prefix_columns(value: str, start_column: int = 0) -> int:
    column = start_column
    for character in value:
        if character not in " \t":
            break
        column = _markdown_advance_column(column, character)
    return column - start_column


def _markdown_consume_indent(
    value: str,
    required_columns: int,
    *,
    start_column: int = 0,
) -> str | None:
    target_column = start_column + required_columns
    column = start_column
    index = 0
    while index < len(value) and value[index] in " \t":
        next_column = _markdown_advance_column(column, value[index])
        index += 1
        if next_column >= target_column:
            column = next_column
            while index < len(value) and value[index] in " \t":
                column = _markdown_advance_column(column, value[index])
                index += 1
            return " " * (column - target_column) + value[index:]
        column = next_column
    return None


def _markdown_consume_quote_marker(value: str) -> str | None:
    marker = re.match(r"^ {0,3}>", value)
    if marker is None:
        return None
    source_column = 0
    for character in value[: marker.end()]:
        source_column = _markdown_advance_column(
            source_column, character
        )
    content_column = source_column
    index = marker.end()
    if index < len(value) and value[index] == " ":
        source_column += 1
        content_column += 1
        index += 1
    elif index < len(value) and value[index] == "\t":
        source_column = _markdown_advance_column(
            source_column, value[index]
        )
        content_column += 1
        index += 1
    while index < len(value) and value[index] in " \t":
        source_column = _markdown_advance_column(
            source_column, value[index]
        )
        index += 1
    return " " * (source_column - content_column) + value[index:]


def _markdown_list_marker_parts(
    marker: re.Match[str],
) -> tuple[str, int, str]:
    marker_text = marker.group("marker")
    after = marker.group("after")
    indent_columns = _markdown_prefix_columns(marker.group("indent"))
    marker_end_column = indent_columns + len(marker_text)
    if not after:
        padding = 1
        item_body = ""
    else:
        whitespace_text = after[: len(after) - len(after.lstrip(" \t"))]
        whitespace_columns = _markdown_prefix_columns(
            whitespace_text, marker_end_column
        )
        has_content = bool(after[len(whitespace_text) :])
        padding = (
            whitespace_columns
            if has_content and whitespace_columns <= 4
            else 1
        )
        item_body = _markdown_consume_indent(
            after, padding, start_column=marker_end_column
        )
        if item_body is None:
            item_body = ""
    content_indent = indent_columns + len(marker_text) + padding
    return marker_text, content_indent, item_body
MARKDOWN_SETEXT_UNDERLINE_RE = re.compile(
    r"^ {0,3}(?:=+|-+)[ \t]*$"
)


def _markdown_container_contexts(
    lines: list[str],
) -> tuple[tuple[MarkdownContainerKey, str], ...]:
    contexts: list[tuple[MarkdownContainerKey, str]] = []
    active_frames: list[MarkdownContainerFrame] = []
    lazy_container: MarkdownContainerKey | None = None
    container_id = 0
    quote_marker_re = re.compile(r"^ {0,3}>[ \t]?")
    for line in lines:
        body = _markdown_expand_tabs(line.rstrip("\r\n"))
        source_body = body
        previous_frames = list(active_frames)
        matched_frames: list[MarkdownContainerFrame] = []

        # Re-enter the previous line's arbitrary quote/list nesting in order.
        # List content indentation is relative to its immediate parent, so
        # alternating paths such as list -> quote -> list remain representable.
        for frame in active_frames:
            kind, frame_id, content_indent = frame
            if kind == "quote":
                continued_body = _markdown_consume_quote_marker(body)
                if continued_body is None:
                    break
                body = continued_body
                matched_frames.append(frame)
                continue

            continued_body = _markdown_consume_indent(
                body, content_indent
            )
            if continued_body is not None:
                body = continued_body
                matched_frames.append(frame)
                continue
            if not body.strip(" \t"):
                # A blank remains in every active list ancestor, but an
                # omitted quote marker closes that quote and its descendants.
                body = ""
                matched_frames.append(frame)
                continue
            break

        if (
            len(matched_frames) < len(previous_frames)
            and source_body.strip(" \t")
            and lazy_container == tuple(previous_frames)
            and MARKDOWN_ATX_HEADING_RE.match(source_body) is None
            and MARKDOWN_THEMATIC_BREAK_RE.fullmatch(source_body) is None
            and re.match(r"^ {0,3}(?:`{3,}|~{3,})", source_body)
            is None
            and MARKDOWN_QUOTE_MARKER_RE.match(source_body) is None
            and MARKDOWN_LIST_MARKER_RE.match(source_body) is None
        ):
            contexts.append((tuple(previous_frames), source_body))
            active_frames = previous_frames
            continue

        active_frames = matched_frames

        # A single source line may open any alternating sequence of blockquote
        # and list containers. Allocate identity per list item/quote block so
        # sibling items cannot lend destinations or titles to each other.
        while body.strip(" \t"):
            if MARKDOWN_THEMATIC_BREAK_RE.fullmatch(body) is not None:
                break
            quote_body = _markdown_consume_quote_marker(body)
            if quote_body is not None:
                container_id += 1
                active_frames.append(("quote", container_id, 0))
                body = quote_body
                continue

            list_marker = MARKDOWN_LIST_MARKER_RE.match(body)
            if list_marker is None:
                break
            container_id += 1
            _, content_indent, item_body = _markdown_list_marker_parts(
                list_marker
            )
            active_frames.append(("list", container_id, content_indent))
            body = item_body

        contexts.append((tuple(active_frames), body))
        if (
            body.strip(" \t")
            and MARKDOWN_ATX_HEADING_RE.match(body) is None
            and MARKDOWN_THEMATIC_BREAK_RE.fullmatch(body) is None
            and re.match(r"^ {0,3}(?:`{3,}|~{3,})", body) is None
            and not body.lstrip(" \t").startswith("<")
        ):
            lazy_container = tuple(active_frames)
        elif not body.strip(" \t"):
            lazy_container = None
        else:
            lazy_container = None
    return tuple(contexts)


def _markdown_body_at_container_depth(
    line: str,
    key: MarkdownContainerKey,
    depth: int,
) -> str:
    body = _markdown_expand_tabs(line.rstrip("\r\n"))
    for kind, _, content_indent in key[:depth]:
        if kind == "quote":
            continued_body = _markdown_consume_quote_marker(body)
            if continued_body is None:
                return body
            body = continued_body
            continue
        continued_body = _markdown_consume_indent(body, content_indent)
        if continued_body is None:
            return body
        body = continued_body
    return body


def _container_continues(
    active_key: MarkdownContainerKey,
    current_key: MarkdownContainerKey,
) -> bool:
    return current_key[: len(active_key)] == active_key


def _fenced_code_line_flags(
    lines: list[str],
    contexts: tuple[tuple[MarkdownContainerKey, str], ...] | None = None,
) -> tuple[bool, ...]:
    if contexts is None:
        contexts = _markdown_container_contexts(lines)
    flags: list[bool] = []
    active_key: MarkdownContainerKey | None = None
    active_character: str | None = None
    active_size = 0
    for line, (key, body) in zip(lines, contexts):
        if active_character is not None:
            if _container_continues(active_key, key):
                active_body = _markdown_body_at_container_depth(
                    line, key, len(active_key)
                )
                flags.append(True)
                closing = re.fullmatch(
                    rf"(?P<indent>[ \t]*)"
                    rf"{re.escape(active_character)}"
                    rf"{{{active_size},}}[ \t]*",
                    active_body,
                )
                if (
                    closing is not None
                    and _markdown_prefix_columns(
                        closing.group("indent")
                    )
                    <= 3
                ):
                    active_key = None
                    active_character = None
                    active_size = 0
                continue
            active_key = None
            active_character = None
            active_size = 0

        opening = re.match(r"^ {0,3}(?P<fence>`{3,}|~{3,})", body)
        if opening is None:
            flags.append(False)
            continue
        fence = opening.group("fence")
        if fence[0] == "`" and "`" in body[opening.end() :]:
            flags.append(False)
            continue
        active_key = key
        active_character = fence[0]
        active_size = len(fence)
        flags.append(True)
    return tuple(flags)


MARKDOWN_REFERENCE_DEFINITION_RE = re.compile(
    r"^ {0,3}\["
    r"(?P<label>(?:\\.|[^\[\]\\\r\n]){1,999})"
    r"\]:[ \t]*(?P<target>[^\r\n]*)$"
)
MARKDOWN_REFERENCE_LABEL_START_RE = re.compile(
    r"^ {0,3}\["
    r"(?P<label>(?:\\.|[^\[\]\\\r\n])*)$"
)
MARKDOWN_REFERENCE_LABEL_CONTINUATION_RE = re.compile(
    r"^(?P<label>(?:\\.|[^\[\]\\\r\n])*)$"
)
MARKDOWN_REFERENCE_LABEL_END_RE = re.compile(
    r"^(?P<label>(?:\\.|[^\[\]\\\r\n])*)"
    r"\]:[ \t]*(?P<target>[^\r\n]*)$"
)
MARKDOWN_REFERENCE_DESTINATION_RE = re.compile(
    r"^[ \t]*(?P<body>\S.*)$"
)
MARKDOWN_REFERENCE_TITLE_RE = re.compile(
    r"^[ \t]*(?P<title>[\"'(].*)$"
)


def _markdown_reference_continuation_starts_block(body: str) -> bool:
    stripped = body.lstrip(" \t")
    html_block_indent = _markdown_prefix_columns(body) <= 3
    html_block_start = html_block_indent and (
        stripped.startswith("<!--")
        or stripped.startswith("<?")
        or stripped.startswith("<![CDATA[")
        or re.match(r"^<![A-Z]", stripped) is not None
        or HTML_RAW_TAG_START_RE.match(body) is not None
        or HTML_TYPE_SIX_START_RE.match(body) is not None
    )
    return (
        MARKDOWN_ATX_HEADING_RE.match(body) is not None
        or MARKDOWN_THEMATIC_BREAK_RE.fullmatch(body) is not None

        or html_block_start
    )


def _markdown_reference_continuation_body(
    index: int,
    container_key: MarkdownContainerKey,
    contexts: tuple[tuple[MarkdownContainerKey, str], ...],
    blocked_lines: tuple[bool, ...],
) -> str | None:
    if index >= len(contexts) or blocked_lines[index]:
        return None
    current_key, body = contexts[index]
    if (
        not body.strip(" \t")
        or _markdown_reference_continuation_starts_block(body)
    ):
        return None
    if current_key == container_key:
        return body
    if (
        len(current_key) < len(container_key)
        and container_key[: len(current_key)] == current_key
    ):
        return body
    return None


def _match_markdown_reference_definition(
    index: int,
    contexts: tuple[tuple[MarkdownContainerKey, str], ...],
    blocked_lines: tuple[bool, ...],
) -> tuple[str, int] | None:
    if blocked_lines[index]:
        return None
    container_key, body = contexts[index]
    match = MARKDOWN_REFERENCE_DEFINITION_RE.fullmatch(body)
    if match is not None:
        raw_label = match.group("label")
        target = match.group("target")
        consumed = 1
    else:
        start = MARKDOWN_REFERENCE_LABEL_START_RE.fullmatch(body)
        if start is None:
            return None
        label_parts = [start.group("label")]
        cursor = index + 1
        while cursor < len(contexts):
            next_body = _markdown_reference_continuation_body(
                cursor,
                container_key,
                contexts,
                blocked_lines,
            )
            if next_body is None:
                return None
            end = MARKDOWN_REFERENCE_LABEL_END_RE.fullmatch(next_body)
            if end is not None:
                label_parts.append(end.group("label"))
                raw_label = "\n".join(label_parts)
                target = end.group("target")
                consumed = cursor - index + 1
                break
            continuation = (
                MARKDOWN_REFERENCE_LABEL_CONTINUATION_RE.fullmatch(next_body)
            )
            if continuation is None:
                return None
            label_parts.append(continuation.group("label"))
            if len("\n".join(label_parts)) > 999:
                return None
            cursor += 1
        else:
            return None

    if len(raw_label) > 999:
        return None
    label = _normalize_markdown_reference_label(raw_label)
    if not label:
        return None

    if not target:
        destination_index = index + consumed
        destination_body = _markdown_reference_continuation_body(
            destination_index,
            container_key,
            contexts,
            blocked_lines,
        )
        if destination_body is None:
            return None
        destination = MARKDOWN_REFERENCE_DESTINATION_RE.fullmatch(
            destination_body
        )
        if destination is None:
            return None
        target = destination.group("body")
        consumed += 1

    def complete_target(
        candidate: str, candidate_consumed: int
    ) -> tuple[str, int] | None:
        while not _is_valid_markdown_link_target(
            candidate,
            allow_empty_destination=False,
        ):
            next_index = index + candidate_consumed
            next_body = _markdown_reference_continuation_body(
                next_index,
                container_key,
                contexts,
                blocked_lines,
            )
            if next_body is None:
                return None
            continuation = MARKDOWN_REFERENCE_DESTINATION_RE.fullmatch(
                next_body
            )
            if continuation is None:
                return None
            candidate += "\n" + continuation.group("body")
            candidate_consumed += 1
        return candidate, candidate_consumed

    if not _is_valid_markdown_link_target(
        target,
        allow_empty_destination=False,
    ):
        completed = complete_target(target, consumed)
        if completed is None:
            return None
        target, consumed = completed
    else:
        title_index = index + consumed
        title_body = _markdown_reference_continuation_body(
            title_index,
            container_key,
            contexts,
            blocked_lines,
        )
        if title_body is not None:
            title = MARKDOWN_REFERENCE_TITLE_RE.fullmatch(title_body)
            if title is not None:
                completed = complete_target(
                    target + "\n" + title.group("title"),
                    consumed + 1,
                )
                if completed is not None:
                    target, consumed = completed
    return label, consumed


HTML_TYPE_SIX_TAGS = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|"
    "col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|"
    "figure|footer|form|frame|frameset|h1|h2|h3|h4|h5|h6|head|header|"
    "hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|"
    "ol|optgroup|option|p|param|search|section|summary|table|tbody|td|"
    "tfoot|th|thead|title|tr|track|ul"
)
HTML_TYPE_SIX_START_RE = re.compile(
    rf"^ {{0,3}}</?(?P<tag>{HTML_TYPE_SIX_TAGS})(?:[ \t]|/?>|$)",
    re.IGNORECASE,
)
HTML_TYPE_SEVEN_START_RE = re.compile(
    r"^ {0,3}(?:"
    r"</[A-Za-z][A-Za-z0-9-]*[ \t]*>"
    r"|<[A-Za-z][A-Za-z0-9-]*"
    r"(?:[ \t]+[A-Za-z_:][A-Za-z0-9_.:-]*"
    r"(?:[ \t]*=[ \t]*"
    r"(?:[^ \t\r\n\"'=<>`]+|'[^']*'|\"[^\"]*\")"
    r")?)*[ \t]*/?>"
    r")[ \t]*$"
)
HTML_RAW_TAG_START_RE = re.compile(
    r"^ {0,3}<(?P<tag>pre|script|style|textarea)(?:[ \t]|>|$)",
    re.IGNORECASE,
)


def _html_block_line_flags(
    lines: list[str],
    contexts: tuple[tuple[MarkdownContainerKey, str], ...] | None = None,
) -> tuple[bool, ...]:
    if contexts is None:
        contexts = _markdown_container_contexts(lines)
    fenced_code_lines = _fenced_code_line_flags(lines, contexts)
    flags: list[bool] = []
    active_key: MarkdownContainerKey | None = None
    active_mode: str | None = None
    active_terminator: str | None = None
    paragraph_keys: set[MarkdownContainerKey] = set()
    reference_definition_end = 0

    def line_reenters_lazy_container(
        index: int,
        paragraph_key: MarkdownContainerKey,
        current_body: str,
    ) -> bool:
        if not any(frame[0] == "quote" for frame in paragraph_key):
            return False
        candidate_body = _markdown_expand_tabs(
            lines[index].rstrip("\r\n")
        )
        for kind, _, content_indent in paragraph_key:
            if kind == "quote":
                continued_body = _markdown_consume_quote_marker(
                    candidate_body
                )
                if continued_body is None:
                    return False
                candidate_body = continued_body
                continue
            continued_body = _markdown_consume_indent(
                candidate_body, content_indent
            )
            if continued_body is None:
                return False
            candidate_body = continued_body
        return candidate_body == current_body

    def line_is_noninterrupting_list_marker(
        index: int,
        key: MarkdownContainerKey,
    ) -> bool:
        for paragraph_key in sorted(paragraph_keys, key=len, reverse=True):
            if (
                len(paragraph_key) >= len(key)
                or key[: len(paragraph_key)] != paragraph_key
                or key[len(paragraph_key)][0] != "list"
            ):
                continue
            parent_body = _markdown_body_at_container_depth(
                lines[index], key, len(paragraph_key)
            )
            marker = MARKDOWN_LIST_MARKER_RE.match(parent_body)
            if marker is None:
                return False
            marker_text, _, item_body = _markdown_list_marker_parts(marker)
            if not item_body.strip(" \t"):
                return True
            if marker_text[0].isdigit():
                number = int(marker_text[:-1])
                return number != 1
            return False
        return False

    for index, (key, body) in enumerate(contexts):
        if active_mode is not None:
            if not _container_continues(active_key, key):
                active_key = None
                active_mode = None
                active_terminator = None
            else:
                active_body = _markdown_body_at_container_depth(
                    lines[index], key, len(active_key)
                )
                if active_mode == "blank" and not active_body.strip(" \t"):
                    active_key = None
                    active_mode = None
                    active_terminator = None
                    flags.append(False)
                    paragraph_keys.clear()
                    continue
                flags.append(True)
                paragraph_keys.clear()
                if (
                    active_terminator is not None
                    and active_terminator.casefold()
                    in active_body.casefold()
                ):
                    active_key = None
                    active_mode = None
                    active_terminator = None
                continue

        if index < reference_definition_end:
            flags.append(False)
            paragraph_keys.clear()
            continue

        noninterrupting_list = False
        if paragraph_keys and key not in paragraph_keys:
            prior_paragraph_keys = tuple(paragraph_keys)
            setext_list_marker = any(
                len(paragraph_key) < len(key)
                and key[: len(paragraph_key)] == paragraph_key
                and key[len(paragraph_key)][0] == "list"
                and MARKDOWN_SETEXT_UNDERLINE_RE.fullmatch(
                    _markdown_body_at_container_depth(
                        lines[index], key, len(paragraph_key)
                    )
                )
                is not None
                for paragraph_key in prior_paragraph_keys
            )
            if setext_list_marker:
                paragraph_keys.clear()
            else:
                lazy_root = (
                    key == ROOT_MARKDOWN_CONTAINER
                    and any(
                        paragraph_key != ROOT_MARKDOWN_CONTAINER
                        for paragraph_key in prior_paragraph_keys
                    )
                )
                noninterrupting_list = line_is_noninterrupting_list_marker(
                    index, key
                )
                lazy_quote_reentry = any(
                    (
                        len(paragraph_key) == len(key)
                        and any(
                            old_frame[0] == "quote"
                            and old_frame != new_frame
                            for old_frame, new_frame
                            in zip(paragraph_key, key)
                        )
                        and all(
                            old_frame[0] == new_frame[0]
                            and (
                                old_frame[0] == "quote"
                                or old_frame == new_frame
                            )
                            for old_frame, new_frame
                            in zip(paragraph_key, key)
                        )
                    )
                    or line_reenters_lazy_container(
                        index, paragraph_key, body
                    )
                    for paragraph_key in prior_paragraph_keys
                )
                if lazy_root or noninterrupting_list or lazy_quote_reentry:
                    paragraph_keys.add(key)
                else:
                    paragraph_keys.clear()

        stripped = body.lstrip(" \t")
        if not stripped:
            flags.append(False)
            if not noninterrupting_list:
                paragraph_keys.clear()
            continue
        if fenced_code_lines[index]:
            flags.append(False)
            paragraph_keys.clear()
            continue

        mode: str | None = None
        terminator: str | None = None
        raw_tag = HTML_RAW_TAG_START_RE.match(body)
        if stripped.startswith("<!--"):
            mode, terminator = "terminator", "-->"
        elif stripped.startswith("<?"):
            mode, terminator = "terminator", "?>"
        elif stripped.startswith("<![CDATA["):
            mode, terminator = "terminator", "]]>"
        elif re.match(r"^<![A-Z]", stripped):
            mode, terminator = "terminator", ">"
        elif raw_tag is not None:
            raw_name = raw_tag.group("tag").casefold()
            mode, terminator = "terminator", f"</{raw_name}>"
        elif HTML_TYPE_SIX_START_RE.match(body) is not None:
            mode = "blank"
        elif (
            HTML_TYPE_SEVEN_START_RE.fullmatch(body) is not None
            and not paragraph_keys
        ):
            mode = "blank"

        if mode is not None:
            active_key = key
            active_mode = mode
            active_terminator = terminator
            paragraph_keys.clear()
            flags.append(True)
            if (
                terminator is not None
                and terminator.casefold() in stripped.casefold()
            ):
                active_key = None
                active_mode = None
                active_terminator = None
            continue

        flags.append(False)
        thematic_or_atx = (
            MARKDOWN_ATX_HEADING_RE.match(body) is not None
            or MARKDOWN_THEMATIC_BREAK_RE.fullmatch(body) is not None
        )
        setext_underline = (
            bool(paragraph_keys)
            and MARKDOWN_SETEXT_UNDERLINE_RE.fullmatch(body) is not None
        )
        indented_code = _markdown_prefix_columns(body) >= 4
        reference_definition = (
            None
            if paragraph_keys
            else _match_markdown_reference_definition(
                index,
                contexts,
                fenced_code_lines,
            )
        )
        if thematic_or_atx or setext_underline:
            paragraph_keys.clear()
        elif not paragraph_keys and indented_code:
            paragraph_keys.clear()
        elif reference_definition is not None:
            reference_definition_end = index + reference_definition[1]
            paragraph_keys.clear()
        elif not paragraph_keys:
            paragraph_keys.add(key)
    return tuple(flags)


def _parse_markdown_reference_definitions(
    value: str,
) -> tuple[str, frozenset[str]]:
    lines = _split_commonmark_lines(value, keepends=True)
    contexts = _markdown_container_contexts(lines)
    fenced_code_lines = _fenced_code_line_flags(lines, contexts)
    html_block_lines = _html_block_line_flags(lines, contexts)
    blocked_lines = tuple(
        fenced or html_block
        for fenced, html_block in zip(fenced_code_lines, html_block_lines)
    )
    inline_block_ids = _markdown_inline_block_ids(value)
    line_block_ids: list[int] = []
    source_offset = 0
    for line in lines:
        line_block_ids.append(inline_block_ids[source_offset])
        source_offset += len(line)

    output: list[str] = []
    labels: set[str] = set()
    index = 0
    follows_definition = False
    while index < len(lines):
        starts_inline_block = (
            index == 0
            or line_block_ids[index] != line_block_ids[index - 1]
        )
        match = (
            _match_markdown_reference_definition(
                index,
                contexts,
                blocked_lines,
            )
            if starts_inline_block or follows_definition
            else None
        )
        if match is None:
            output.append(lines[index])
            index += 1
            follows_definition = False
            continue

        label, consumed = match
        labels.add(label)
        for offset in range(consumed):
            consumed_line = lines[index + offset]
            consumed_body = consumed_line.rstrip("\r\n")
            output.append(consumed_line[len(consumed_body) :])
        index += consumed
        follows_definition = True

    return "".join(output), frozenset(labels)

def _strip_markdown_reference_definitions(value: str) -> str:
    stripped, _ = _parse_markdown_reference_definitions(value)
    return stripped


def _strip_html_tags(
    value: str,
    *,
    preserve_line_boundaries: bool = False,
) -> str:
    code_ranges = _markdown_prose_code_ranges(value)
    ranges = _markdown_inline_html_ranges(
        value, code_ranges, _markdown_inline_block_ids(value)
    )
    output: list[str] = []
    index = 0
    for start, end in ranges:
        output.append(value[index:start])
        if preserve_line_boundaries:
            output.append(
                "\n"
                * _count_commonmark_line_endings(value[start:end])
            )
            if end == len(value):
                output.append(" ")
        index = end
    output.append(value[index:])
    return "".join(output)



def normalize_markdown_visible_text(
    value: str,
    *,
    preserve_line_boundaries: bool = False,
) -> str:
    value, reference_labels = _parse_markdown_reference_definitions(value)
    value = _strip_markdown_link_targets(
        value,
        reference_labels,
        preserve_line_boundaries=preserve_line_boundaries,
    )
    value = _strip_html_tags(
        value, preserve_line_boundaries=preserve_line_boundaries
    )
    value = html.unescape(value)
    value = MARKDOWN_BACKSLASH_ESCAPE_RE.sub(r"\1", value)
    value = re.sub(r"[\[\]]", " ", value)
    value = re.sub(r"[*_`~]", "", value)
    value = re.sub(r"(?i)(\.md)(?=[.,;:!?])", r"\1 ", value)
    return value


def _resolve_packaged_reference(
    document_path: str,
    named_path: str,
    packaged_paths_casefold: set[str],
    packaged_basenames_casefold: set[str],
) -> str | None:
    normalized_path = named_path.replace("\\", "/").lstrip("/")
    if normalized_path.startswith(("./", "../")):
        logical_path = posixpath.normpath(
            posixpath.join(posixpath.dirname(document_path), normalized_path)
        )
    elif normalized_path.startswith("references/"):
        logical_path = posixpath.normpath(
            posixpath.join("run", normalized_path)
        )
    else:
        logical_path = posixpath.normpath(normalized_path)
    logical_casefold = logical_path.casefold()
    if (
        logical_casefold in packaged_paths_casefold
        or logical_casefold.startswith("run/references/")
        or PurePosixPath(logical_path).name.casefold()
        in packaged_basenames_casefold
    ):
        return logical_casefold
    return None


def discover_directives_from_documents(
    documents: Mapping[str, str], graph_node_paths: Iterable[str]
) -> list[dict]:
    node_paths = set(graph_node_paths)
    packaged_paths = node_paths | set(documents)
    packaged_paths_casefold = {path.casefold() for path in packaged_paths}
    packaged_basenames_casefold = {
        PurePosixPath(path).name.casefold() for path in packaged_paths
    }
    directives: list[dict] = []
    for document_path, text in sorted(documents.items()):
        matches = list(MARKER_RE.finditer(text))
        marker_spans = [match.span() for match in matches]
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

        headings = list(MARKDOWN_HEADING_RE.finditer(text))
        section_spans: list[tuple[int, int, str]] = []
        if not headings or headings[0].start() > 0:
            section_spans.append(
                (0, headings[0].start() if headings else len(text), "<preamble>")
            )
        for index, heading_match in enumerate(headings):
            section_spans.append(
                (
                    heading_match.start(),
                    headings[index + 1].start()
                    if index + 1 < len(headings)
                    else len(text),
                    heading_match.group(0).strip(),
                )
            )
        observed_contexts: Counter[tuple[str, str, str]] = Counter()
        observed_reference_paths: Counter[str] = Counter()

        for match in PACKAGED_MARKDOWN_PATH_RE.finditer(text):
            if any(
                start <= match.start() and match.end() <= end
                for start, end in marker_spans
            ):
                continue
            named_path = match.group("path")
            logical_casefold = _resolve_packaged_reference(
                document_path,
                named_path,
                packaged_paths_casefold,
                packaged_basenames_casefold,
            )
            if logical_casefold is None:
                continue
            observed_reference_paths[logical_casefold] += 1
            if _is_closed_legacy_compatibility_literal(
                document_path, text, match
            ):
                classification = "legacy"
            else:
                classification = "reference"
            for start, end, section_heading in section_spans:
                if start <= match.start() and match.end() <= end:
                    section_without_markers = MARKER_RE.sub(
                        "", text[start:end]
                    )
                    section_hash = hashlib.sha256(
                        section_without_markers.encode("utf-8")
                    ).hexdigest()
                    context_key = (
                        section_heading,
                        section_hash,
                        classification,
                    )
                    break
            else:
                raise LoadContractError(
                    "plain imperative preload or unclassified packaged "
                    "Markdown reference section context in "
                    f"{document_path}: {named_path}"
                )
            expected_contexts = ALLOWED_REFERENCE_SECTION_CONTEXT_COUNTS.get(
                document_path, {}
            )
            if context_key not in expected_contexts:
                raise LoadContractError(
                    "plain imperative preload or unclassified packaged "
                    "Markdown reference section context in "
                    f"{document_path}: {named_path}"
                )
            observed_contexts[context_key] += 1

        expected_contexts = Counter(
            ALLOWED_REFERENCE_SECTION_CONTEXT_COUNTS.get(document_path, {})
        )
        _require(
            observed_contexts == expected_contexts,
            "plain imperative preload or packaged Markdown reference "
            "section context or multiplicity drift in "
            f"{document_path}",
        )

        text_without_markers = MARKER_RE.sub("", text)
        visible_reference_paths: Counter[str] = Counter()
        visible_text = normalize_markdown_visible_text(text_without_markers)
        for visible_match in PACKAGED_MARKDOWN_PATH_RE.finditer(visible_text):
            logical_casefold = _resolve_packaged_reference(
                document_path,
                visible_match.group("path"),
                packaged_paths_casefold,
                packaged_basenames_casefold,
            )
            if logical_casefold is not None:
                visible_reference_paths[logical_casefold] += 1
        _require(
            visible_reference_paths == observed_reference_paths,
            "plain imperative preload or unclassified packaged Markdown "
            "reference visible-text drift in "
            f"{document_path}",
        )

        instruction_scan_text = "\n".join(
            line
            for line in _split_commonmark_lines(text_without_markers)
            if line != ALLOWED_TOOLS_LINE
        )
        instruction_source_text, instruction_reference_labels = (
            _parse_markdown_reference_definitions(text_without_markers)
        )
        visible_instruction_verb_count = len(
            INSTRUCTION_VERB_RE.findall(
                normalize_markdown_visible_text(instruction_scan_text)
            )
        )
        _require(
            visible_instruction_verb_count
            == ALLOWED_VISIBLE_INSTRUCTION_VERB_COUNTS.get(document_path, 0),
            "plain imperative preload or unclassified visible instruction "
            f"verb count in {document_path}",
        )

        instruction_source_line_endings = (
            _split_commonmark_lines(instruction_source_text, keepends=True)
        )
        instruction_source_lines = _split_commonmark_lines(instruction_source_text)
        instruction_source_contexts = _markdown_container_contexts(
            instruction_source_line_endings
        )
        visible_instruction_lines = _split_commonmark_lines(
            normalize_markdown_visible_text(
                text_without_markers,
                preserve_line_boundaries=True,
            )
        )
        _require(
            len(visible_instruction_lines) == len(instruction_source_lines),
            "plain imperative preload or unclassified instruction verb "
            f"line mapping in {document_path}",
        )
        observed_instruction_lines: Counter[str] = Counter()
        for line_index, (source_line, visible_line) in enumerate(
            zip(instruction_source_lines, visible_instruction_lines)
        ):
            root_indented_after_blank = (
                instruction_source_contexts[line_index][0]
                == ROOT_MARKDOWN_CONTAINER
                and _markdown_prefix_columns(source_line) >= 4
                and (
                    line_index == 0
                    or not instruction_source_lines[line_index - 1].strip()
                )
            )
            if (
                root_indented_after_blank
                and INSTRUCTION_VERB_RE.search(visible_line) is None
            ):
                visible_line = normalize_markdown_visible_text(
                    _strip_markdown_link_targets(
                        source_line, instruction_reference_labels
                    )
                )
            if (
                INSTRUCTION_VERB_RE.search(visible_line)
                and source_line != ALLOWED_TOOLS_LINE
            ):
                observed_instruction_lines[
                    hashlib.sha256(source_line.encode("utf-8")).hexdigest()
                ] += 1
        expected_instruction_lines = Counter(
            ALLOWED_INSTRUCTION_VERB_LINE_HASH_COUNTS.get(document_path, {})
        )
        _require(
            observed_instruction_lines == expected_instruction_lines,
            "plain imperative preload or unclassified instruction verb line "
            f"in {document_path}",
        )

    return directives


def _read_normalized_utf8(path: Path) -> str:
    try:
        raw = path.read_bytes()
        return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode(
            "utf-8"
        )
    except (OSError, UnicodeDecodeError) as exc:
        raise LoadContractError(f"cannot read UTF-8 text {path}: {exc}") from exc


def _decode_yaml_key_token(raw_key: str) -> str | None:
    if raw_key.startswith('"'):
        try:
            decoded = json.loads(raw_key)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, str) else None
    if raw_key.startswith("'"):
        return raw_key[1:-1].replace("''", "'")
    return raw_key


def _yaml_equivalent_key_matches(text: str, key: str) -> list[re.Match]:
    return [
        match
        for match in YAML_KEY_TOKEN_RE.finditer(text)
        if _decode_yaml_key_token(match.group("key")) == key
    ]


def _validate_codex_default_prompt_text(relative_path: str, text: str) -> None:
    _require(
        YAML_FORBIDDEN_COMPLEX_KEY_RE.search(text) is None,
        "Codex openai.yaml equivalent YAML key uses explicit or merge syntax: "
        f"{relative_path}",
    )
    _require(
        YAML_FORBIDDEN_ANCHOR_ALIAS_RE.search(text) is None,
        "Codex openai.yaml equivalent YAML key uses anchor or alias syntax: "
        f"{relative_path}",
    )
    key_tokens = list(YAML_KEY_TOKEN_RE.finditer(text))
    ambiguous_escaped_keys = [
        match
        for match in key_tokens
        if match.group("key").startswith('"')
        and "\\" in match.group("key")
    ]
    _require(
        not ambiguous_escaped_keys,
        "Codex openai.yaml equivalent YAML key uses a non-canonical escape: "
        f"{relative_path}",
    )
    interface_keys = _yaml_equivalent_key_matches(text, "interface")
    default_prompt_keys = _yaml_equivalent_key_matches(text, "default_prompt")
    _require(
        len(interface_keys) == 1 and len(default_prompt_keys) == 1,
        "Codex openai.yaml equivalent YAML key duplication or ambiguity: "
        f"{relative_path}",
    )

    lines = text.splitlines()
    interface_lines = [
        index for index, line in enumerate(lines) if line == "interface:"
    ]
    _require(
        len(interface_lines) == 1,
        "Codex default_prompt must be a direct child of top-level interface: "
        f"{relative_path}",
    )
    interface_start = interface_lines[0]
    interface_end = len(lines)
    for index in range(interface_start + 1, len(lines)):
        line = lines[index]
        if line and not line[0].isspace():
            interface_end = index
            break

    prompts = list(CODEX_DEFAULT_PROMPT_LINE_RE.finditer(text))
    prompt_line_indexes = [
        index
        for index, line in enumerate(lines)
        if CODEX_DEFAULT_PROMPT_KEY_RE.match(line)
    ]
    _require(
        len(prompts) == 1
        and len(prompt_line_indexes) == 1
        and interface_start < prompt_line_indexes[0] < interface_end
        and lines[prompt_line_indexes[0]].startswith("  default_prompt:")
        and not lines[prompt_line_indexes[0]].startswith("   default_prompt:"),
        "Codex default_prompt must be a direct child of top-level interface: "
        f"{relative_path}",
    )
    try:
        prompt = json.loads(prompts[0].group("quoted"))
    except json.JSONDecodeError as exc:
        raise LoadContractError(
            f"Codex default_prompt is not a valid quoted scalar: {relative_path}"
        ) from exc
    _require(
        all(
            PACKAGED_MARKDOWN_PATH_RE.search(candidate) is None
            and PACKAGED_REFERENCE_NAMESPACE_RE.search(candidate) is None
            for candidate in (text, prompt)
        ),
        f"hidden packaged Markdown load is forbidden in Codex default_prompt "
        f"surface: {relative_path}",
    )
    _require(
        isinstance(prompt, str) and prompt.strip(),
        f"Codex default_prompt must be a non-empty string: {relative_path}",
    )


def validate_codex_default_prompt_surface(root: Path) -> None:
    platform_path = root / CODEX_PLATFORM_PROMPT_RELATIVE_PATH
    generated_path = root / CODEX_GENERATED_PROMPT_RELATIVE_PATH
    platform_text = _read_normalized_utf8(platform_path)
    generated_text = _read_normalized_utf8(generated_path)
    _validate_codex_default_prompt_text(
        CODEX_PLATFORM_PROMPT_RELATIVE_PATH, platform_text
    )
    _validate_codex_default_prompt_text(
        CODEX_GENERATED_PROMPT_RELATIVE_PATH, generated_text
    )
    _require(
        platform_text == generated_text,
        "generated Codex openai.yaml drift from platform source",
    )


EXPECTED_LIFECYCLE_HEADER = (
    "The operational rules for Run's state recovery, harness step, and 3-doc "
    "archive. This file is loaded at preflight: recovery and migration run "
    "before mutation, harness creation or update runs after the completion gate "
    "and before final review, and archive runs only after user approval. Use the "
    "structured harness binding below; this file is the *process*, the bound "
    "reference is the *spec*."
)


def validate_lifecycle_header(document: str) -> None:
    header = document.split("<!-- leanforge:run-load", 1)[0]
    paragraphs = header.split("\n\n", 1)
    _require(
        len(paragraphs) == 2,
        "lifecycle header semantic drift: missing operational paragraph",
    )
    normalized_header = " ".join(paragraphs[1].split())
    _require(
        normalized_header == EXPECTED_LIFECYCLE_HEADER,
        "lifecycle header semantic drift",
    )


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
    surfaces = tuple(surfaces)
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
    if "codex/plugin/skills" in surfaces:
        validate_codex_default_prompt_surface(root)
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
    if invariant_kind == "route_topology":
        if edge["to"] == "run/references/implementer-prompt.md":
            dispatched_routes = set(routes) - {"direct"}
            return route in dispatched_routes or overlay == "failure"
        return True
    if invariant_kind == "lifecycle_ownership":
        return True
    if invariant_kind == "failure_overlay":
        return overlay == "failure"
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
    for surface in SURFACES:
        run_root = root / surface / "run"
        _require(
            run_root.is_dir(),
            f"read-only hash surface is missing: {run_root}",
        )
        paths.extend(
            path for path in run_root.rglob("*") if path.is_file()
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
