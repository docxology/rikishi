# Results

The index accepts four formulas and records two asserted edges. The
Cup record includes the quantified implication as complete source
text, with its filename and starting line. Cup's documentation retains
its own filename and starting line.

The SampleCup parent list contains Cup through the `instance`
relation. Cup has Container as a `subclass` parent. Container is
absent from SampleCup's direct parent list, even though the fixture
contains an implication that can be used to reason about that
membership.

![Directed asserted relations retrieved from the fixture. SampleCup is an instance of Cup and Cup is a subclass of Container.](../../output/figures/catalog-index.png)
