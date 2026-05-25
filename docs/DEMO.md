# Flagship Demo

The flagship demo turns the project into one clean explainable pipeline:

```text
attacker command
  -> honeypot detection
  -> event bus
  -> polymorphic emergency mutation
  -> AI prediction
  -> incident retrieval recommendation
  -> JSON report
```

Run it:

```bash
python examples/flagship_demo.py
```

Output:

```text
examples/demo_report.json
```

What the demo proves:

- The event bus connects independent modules.
- A honeypot-style suspicious command emits a threat event.
- The polymorphic engine reacts to that event.
- Precog and RAG modules can provide explanatory response context.
- The forensic logger chain verifies after the run.

What it does not prove:

- Real exploit prevention.
- Production honeypot isolation.
- Production-grade ML quality.
- Real post-quantum protection.
