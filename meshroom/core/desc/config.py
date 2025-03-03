import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from meshroom.env import EnvVar

from .process import (
    DefaultEnvironment,
    ProcessEnvironment,
    processEnvironmentFactory,
)


@dataclass
class _RegisteredProcessEnvironment:
    """A registered ProcessEnvironment, loaded from a source config file."""
    desc: ProcessEnvironment
    source: str


@dataclass
class _ConfigProcessEnvironments:
    envs: dict[str, _RegisteredProcessEnvironment] = field(default_factory=dict)
    nodeTypeEnvMapping: dict[str, str] = field(default_factory=dict)


CONFIG_PROCESS_ENVIRONMENTS = _ConfigProcessEnvironments()


def configProcessEnvironmentsInit():
    envConfigs = EnvVar.get(EnvVar.MESHROOM_CONFIG_PROCESS_ENVS)
    if not envConfigs:
        return

    envFiles = envConfigs.split(":")

    for envFile in envFiles:
        if not (envFilepath := Path(envFile)).exists():
            continue
        try:
            _registerEnvironments(envFilepath)
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse environment config file: {e}")


def getProcessEnvironment(nodeType: str) -> ProcessEnvironment:
    if not (env_name := CONFIG_PROCESS_ENVIRONMENTS.nodeTypeEnvMapping.get(nodeType)):
        return DefaultEnvironment("default", "default")

    return CONFIG_PROCESS_ENVIRONMENTS.envs[env_name].desc


def _registerEnvironments(envFile: Path):
    with open(envFile, "r") as f:
        content = json.load(f)
        envs = content.get("envs")

        for env_name, value in envs.items():
            _registerEnvironment(env_name, value, envFile)

        for nodeType, envName in content["mapping"].items():
            _registerNodeTypeEnvironmentMapping(nodeType, envName)


def _registerEnvironment(name: str, fields: dict, source: Path):
    if env := CONFIG_PROCESS_ENVIRONMENTS.envs.get(name, None):
        logging.warning(f"Skipping already defined env: {env}")

    envDesc = processEnvironmentFactory(name, fields.pop("type"), **fields)

    CONFIG_PROCESS_ENVIRONMENTS.envs[name] = _RegisteredProcessEnvironment(envDesc, source.as_posix())


def _registerNodeTypeEnvironmentMapping(nodeType: str, envName: str):
    CONFIG_PROCESS_ENVIRONMENTS.nodeTypeEnvMapping[nodeType] = envName
