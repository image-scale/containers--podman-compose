# Goal

## Project
podman-compose — a python project.

## Description
An implementation of Docker Compose specification with Podman backend. This tool reads docker-compose.yml files (or compose.yaml) and translates them into Podman commands to manage containers, networks, and volumes. It supports features like variable interpolation, service dependencies, build configurations, and various CLI commands (up, down, ps, run, exec, logs, etc.).

## Scope
- 12 production source files to implement
- 10 test files to write
- Reproduce core functionality: YAML parsing, variable interpolation, service normalization, container argument generation, network handling, volume management, dependency resolution, and CLI commands
