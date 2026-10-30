# Active Inference: inference, action and evidence

Active Inference provides a research framework for relating belief updating to
action under a generative model. Rikishi uses that connection in three distinct
ways: an ontology-alignment question, finite mathematical examples, and an
executable one-step decision method. The broader Free Energy Principle (FEP)
motivates the research; it is not a conclusion of these calculations.

## Locate the claim before running a method

| Question | Rikishi method | What the result means |
| --- | --- | --- |
| How can model content, an inference process and a numerical result be described? | Suggested Upper Merged Ontology (SUMO) source inspection and selected role scenarios | Consequences of the submitted axioms and local assumptions |
| Which belief explains an observation in a supplied finite model? | `fep-demo`, `fep-evaluate`, exact conditioning | A variational objective or a conditional probability law |
| What observations follow from a fixed-state sampling model? | Existing witness simulations and mixed-history calculations | Synthetic trajectories or exact predictions under that model |
| Which action should be considered before seeing its outcome? | `active-demo`, `plan_actions` | Numerical minimizers of the explicitly adopted prospective score |
| Does an organism use this model or act by this mechanism? | An empirical protocol is still required | None of the above methods answers this question |

The [alignment precedent](precedent-alignment.md) concerns vocabulary and
representation. A class called `Agent` or `Process` does not supply an action
policy. Likewise, a pinned Lean information identity supplies a named mathematical
statement, not an implemented control loop. The new decision example is separate
from the registered shared-witness campaigns and from the current manuscript's
fixed-state simulator. It adds no Lean theorem or native SUMO result to them.

## Inference given an observation

For a finite normalized prior and likelihood with positive evidence, using
Kullback-Leibler (KL) divergence, the variational free energy is

$$F(q;o)=\sum_s q(s)\log\frac{q(s)}{p(s,o)}
        =D_{KL}(q\Vert p(\cdot\mid o))-\log p(o).$$

The observation is fixed. The variable is a candidate belief, and the exact
posterior minimizes this functional when support is respected. This is the
negative evidence lower bound. Computing the identity alone supplies neither
an action model nor a decision objective; see [finite FEP methods](fep.md).

## Predicting the consequences of an action

The implementation in [`active_inference.py`](../src/rikishi/active_inference.py)
declares a current belief $b(s)$, an action-dependent transition
$B_a(s'\mid s)$ and observation channel $A_a(o\mid s')$. Both channels are
row-stochastic: rows are conditioning inputs and columns are outputs.

$$q_a(s')=\sum_s b(s)B_a(s'\mid s),\qquad
  q_a(s',o)=q_a(s')A_a(o\mid s'),\qquad
  q_a(o)=\sum_{s'}q_a(s',o).$$

All actions in a comparison must use the same current-state meanings and
outcome meanings. Their next-state carriers can differ. A preference law $C(o)$
is a normalized, strictly positive distribution over those common outcomes.
It expresses the modeler's desirability assumptions. It is distinct from the
predicted sampling distribution $q_a(o)$ and the actually observed outcome.

For this module, define the one-step outcome-preference score by

$$G_C(a)=D_{KL}(q_a(O)\Vert C)
          +\sum_{s'}q_a(s')H(A_a(\cdot\mid s')).$$

The first term is outcome risk; the second is expected ambiguity. This adopted
functional uses the outcome-preference convention discussed in
[Da Costa et al. (2020), §7 and Appendix C](https://arxiv.org/html/2001.07203v2).
Their equations (13)–(16) distinguish state risk, outcome risk, posterior
approximation and information gain; (44)–(50) detail outcome-risk and ambiguity
calculations. Replacing state preferences by outcome preferences is a modeling
choice with assumptions, not a universal equality. The present module defines
its outcome-based score directly and uses exact finite conditioning within its
own supplied model. It does not implement their full policy posterior,
parameter learning or steady-state derivation.

## An exact identity for the declared finite model

For each outcome with $q_a(o)>0$, define
$q_a(s'\mid o)=q_a(s',o)/q_a(o)$. Then

$$I_a(S';O)=\sum_{o:q_a(o)>0}q_a(o)
   D_{KL}(q_a(S'\mid o)\Vert q_a(S'))
   =H(q_a(O))-\sum_{s'}q_a(s')H(A_a(\cdot\mid s')).$$

Expanding the risk term gives
$D_{KL}(q_a(O)\Vert C)=-H(q_a(O))-\sum_o q_a(o)\log C(o)$.
Substitution yields the finite-model identity

$$G_C(a)=\underbrace{-\sum_o q_a(o)\log C(o)}_{\text{expected preference surprisal}}
          -\underbrace{I_a(S';O)}_{\text{expected state information gain}}.$$

Thus a candidate action can be attractive because of preferred consequences,
informative consequences, or both. Information gain is about the next state
under the declared model. It does not measure truth about an external system.
The code computes information gain through hypothetical posteriors independently
of the risk-plus-ambiguity expression and retains the signed residual. This
algebraic derivation is not a newly compiled Lean proof.

## Run an example that separates information from outcome frequencies

```bash
source scripts/env.sh
uv run --locked rikishi active-demo
```

The complete example has two equally probable hidden states and identity
transitions. The `sense` action reports the state perfectly; `noise` produces
an independent fair Boolean outcome in either state. Preferences are uniform.
Both actions predict the same outcome distribution, so outcome risk is zero
for both. `sense` has zero ambiguity and information gain $\log 2$; `noise` has
ambiguity $\log 2$ and zero information gain. Their scores are therefore zero
and $\log 2$, respectively. The method retains `sense` as the unique minimizer.
These are consequences of supplied synthetic matrices, not measured agent results.

Use the same methods with explicit rational inputs:

```python
from fractions import Fraction as F
from rikishi.active_inference import Action, condition_action, plan_actions
from rikishi.finite_channels import FiniteChannel

identity = FiniteChannel("identity", ((F(1), F(0)), (F(0), F(1))))
noise = FiniteChannel("noise", ((F(1, 2), F(1, 2)),) * 2)
actions = (Action("sense", identity, identity), Action("noise", identity, noise))
belief = preferences = (F(1, 2), F(1, 2))
plan = plan_actions(belief, actions, preferences)
print(plan.minimizers)

# Supply an outcome only after it has been observed: index 1 denotes true.
updated = condition_action(belief, actions[0], 1)
assert updated.posterior == (F(0), F(1))
```

`condition_action` first advances through the transition and then conditions on
the observed column. Scoring considers possible observations without pretending
one occurred. An impossible observation raises an error. A repeated
action/perception loop additionally needs an environment, observation protocol
and explicit resolution of any returned ties. This example supplies the planner
and filter, not a sampled environment or a multi-step policy search.

## Numerical and acceptance contract

- Laws, transitions, joints and conditional laws use exact `Fraction` values.
  Logarithms and scores use `Decimal` natural-log approximations in nats.
- Precision is an integer from 40 through 200, default 80. Each evaluation uses
  a fresh context and 20 guard digits, independent of the caller's context.
- Structural zeros contribute zero. Impossible hypothetical outcomes are omitted
  from the information-gain expectation and receive no invented posterior.
  Strictly positive preferences are required even at unreachable outcomes.
- The residual is `G - (expected_surprisal - information_gain)`. Its tolerance is
  $10^{8-d}\max(1,|G|,|\text{expected surprisal}|,|I|)(|S'|+|O|)$ for requested
  precision $d$. An excessive residual raises `FiniteChannelError`.
- `plan_actions` retains every score within the larger of its tolerance and
  the best score's tolerance. It reports all such names in input order, with no
  hidden tie-break. This is numerical selection, not certified interval ordering.
- The command's JavaScript Object Notation (JSON) preserves rational masses and decimal quantities as strings;
  it includes complete input matrices, precision, tolerances and residuals.

Controls compare an independent joint-sum expression, action-dependent
transitions, altered preferences, carrier permutations, zero support, impossible
observations, hostile caller contexts and ties. A deliberately corrupted score
must be rejected. See [testing](testing.md) for the repository gates.

## What would support stronger claims

A longer-horizon agent needs a temporal generative model, policy representation,
action execution and environment feedback; parameter uncertainty and learning
need their own update semantics. A formal guarantee needs a specified theorem
and an actual proof. Ontology integration needs source-backed interpretation
obligations, beyond attaching entity names to a planner. Empirical adequacy needs
observations, operational hypotheses, appropriate comparison models and
uncertainty analysis. None follows from the finite objective alone.
