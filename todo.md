# Todo

## Plan
Start with core utility functions for variable interpolation and data normalization since these are fundamental building blocks. Then implement the compose file parsing and service handling. Build up to container argument generation, network/volume handling, and finally the CLI interface with commands.

## Tasks
- [x] Task 1: Implement variable interpolation for compose files - support bash-style variable substitution ($VAR, ${VAR}, ${VAR:-default}, ${VAR:?error}, etc.) with nested variable support
- [>] Task 2: Implement data normalization utilities - convert between list/dict formats, normalize ulimits, time string parsing, version comparison, and short mount path parsing
- [ ] Task 3: Implement recursive substitution and merge functions - apply variable interpolation recursively through compose data structures, merge compose files together
- [ ] Task 4: Implement service normalization - normalize service definitions including build config, commands, environment, depends_on, volumes
- [ ] Task 5: Implement dependency resolution - parse service dependencies, resolve recursive dependencies, calculate dependents graph
- [ ] Task 6: Implement network argument generation - generate podman network arguments from service network configuration including IP addresses, aliases, MAC addresses
- [ ] Task 7: Implement container argument generation - convert service configurations to podman run arguments including environment, volumes, ports, healthchecks, resources
- [ ] Task 8: Implement secrets handling - generate arguments for secrets from files or external sources with proper mount options
- [ ] Task 9: Implement build argument generation - generate podman build arguments from service build configurations including context, dockerfile, build args, secrets
- [ ] Task 10: Implement main compose class and YAML loading - create the main orchestration class that loads compose files, manages environment, and coordinates services
- [ ] Task 11: Implement core CLI commands - implement up, down, ps commands for managing container lifecycle
- [ ] Task 12: Implement auxiliary CLI commands - implement run, exec, logs, start, stop, restart, build, pull, push commands
