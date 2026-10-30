"""Run exact mixed-observation and model-uncertainty examples without native tools."""

import json
from fractions import Fraction

from rikishi.bridge_study import catalog
from rikishi.finite_channels import FiniteChannel
from rikishi.witness_sequences import SequenceModel, compare_sequence_models, condition_sequence


def main() -> None:
    """Print declared example inputs and exact results; do not claim a bridge execution."""
    witnesses = catalog().witnesses[:2]
    models = tuple(SequenceModel(
        witness.id, tuple(map(Fraction, witness.prior)),
        FiniteChannel(witness.id, tuple((1 - ell, ell) for ell in map(Fraction, witness.likelihood))),
    ) for witness in witnesses)
    observations = (True, False)
    rows = {}
    for model in models:
        result = condition_sequence(model.prior, model.kernel, observations)
        final = result.steps[-1]
        rows[model.name] = {
            "prior": list(map(str, model.prior)),
            "kernel": [list(map(str, row)) for row in model.kernel.rows],
            "evidence": str(final.cumulative_evidence),
            "posterior": list(map(str, final.posterior)),
            "next_true": str(final.next_predictive[1]),
            "redrawn_evidence": str(result.redrawn_evidence),
        }
    mixture = compare_sequence_models(models, observations)
    print(json.dumps({
        "scope": "Exact constructed example; no native or empirical evidence",
        "observations": observations, "models": rows,
        "model_prior": list(map(str, mixture.model_prior)),
        "posterior_model_weights": list(map(str, mixture.posterior)),
        "model_averaged_next_true": str(mixture.next_predictive[1]),
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
