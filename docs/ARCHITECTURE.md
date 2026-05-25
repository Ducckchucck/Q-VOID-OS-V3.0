# Architecture

Q-VOID OS is built around an event-driven architecture.

## Core Flow

```text
terminal / demo / module
        |
        v
core.EventBus
        |
        +--> ForensicLogger
        +--> subscribed modules
        +--> demo/report pipeline
```

## Core Components

- `EventBus`: threaded publish/subscribe event delivery.
- `ForensicLogger`: JSON-lines audit log with hash chaining.
- `ModuleRegistry`: runtime registry for module objects and status.
- `modules/registry.py`: public truth metadata for reviewers.

## Design Principles

- Modules communicate through events when possible.
- Demos should be runnable without privileged infrastructure.
- Simulations must be labeled as simulations.
- Negative-path tests are required for security-sensitive behavior.

## Current Production Boundary

This repository is production-quality as an open-source prototype and demo
platform. It is not production-ready as a deployed security appliance.

Primary gaps before production deployment:

- Authenticated peer-to-peer networking.
- Hardened honeypot sandbox lifecycle.
- Real hypervisor or container orchestration integration.
- Key management with external secret storage.
- Model evaluation and monitoring.
- Structured logging and bounded event worker pools.
