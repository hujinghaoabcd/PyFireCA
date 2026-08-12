"""Model-aware configuration and workflow dispatch for the PyFireCA CLI."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TypeAlias

import yaml

from pyfireca.config import StaticRunConfig, load_static_run_config
from pyfireca.fbp_config import StaticFBPRunConfig, load_static_fbp_run_config
from pyfireca.fbp_workflow import run_static_fbp_config, validate_static_fbp_run
from pyfireca.simulator import StaticWildfireSimulationResult
from pyfireca.workflow import StaticRunArtifacts, run_static_config, validate_static_run

ResolvedRunConfig: TypeAlias = StaticRunConfig | StaticFBPRunConfig


def configured_behavior_model(path: str | Path) -> str:
    """Return the configured behavior model without constructing simulation inputs.

    Version-1 Rothermel configurations predate the explicit ``behavior`` block;
    absence of that block therefore remains a backward-compatible alias for
    ``rothermel``. New non-Rothermel configurations must declare their model.
    """

    config_path = Path(path).expanduser().resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("configuration must be a mapping")
    behavior = raw.get("behavior")
    if behavior is None:
        return "rothermel"
    if not isinstance(behavior, Mapping):
        raise ValueError("behavior must be a mapping")
    model = behavior.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("behavior.model must be a non-empty string")
    normalized = model.strip().lower()
    if normalized not in {"fbp", "rothermel"}:
        raise ValueError(f"unsupported behavior.model {model!r}; expected 'rothermel' or 'fbp'")
    if normalized == "rothermel":
        raise ValueError(
            "version-1 Rothermel configs use the legacy top-level schema; "
            "omit the behavior block"
        )
    return normalized


def load_run_config(path: str | Path) -> ResolvedRunConfig:
    """Load either the backward-compatible Rothermel or explicit FBP config."""

    model = configured_behavior_model(path)
    if model == "fbp":
        return load_static_fbp_run_config(path)
    return load_static_run_config(path)


def validate_run_config(config: ResolvedRunConfig) -> None:
    """Validate a model-specific resolved configuration."""

    if isinstance(config, StaticFBPRunConfig):
        validate_static_fbp_run(config)
        return
    if isinstance(config, StaticRunConfig):
        validate_static_run(config)
        return
    raise TypeError("config must be StaticRunConfig or StaticFBPRunConfig")


def run_config(
    config: ResolvedRunConfig,
) -> tuple[StaticWildfireSimulationResult, StaticRunArtifacts]:
    """Run a model-specific configuration using the common result contract."""

    if isinstance(config, StaticFBPRunConfig):
        return run_static_fbp_config(config)
    if isinstance(config, StaticRunConfig):
        return run_static_config(config)
    raise TypeError("config must be StaticRunConfig or StaticFBPRunConfig")
