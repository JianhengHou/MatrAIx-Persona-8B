"""Persona-fit: real-person decision datasets as MatrAIx survey tasks.

Each Fit A dataset in ``persona_fit_datasets.xlsx`` is wrapped by one
``DatasetAdapter`` (``persona_fit.adapters``). The adapter splits every source
row into the three locked pieces of the persona-fit contract:

- persona: stable identity of the person (built once per person),
- task card: the situation the person saw for this decision,
- outcome: the held-out decision, visible only to the verifier.

Each dataset becomes per-decision application survey tasks. See
``docs/application/persona-fit.md``.
"""
