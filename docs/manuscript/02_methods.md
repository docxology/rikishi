# Methods

We build a fresh SQLite index from a generated `Catalog.kif` file. The
file declares that a cup is a container, that a sample cup is an
instance of a cup, and that instances of cup are instances of container.
The last statement is encoded as a quantified implication. A separate
documentation expression describes the Cup term.

We read the complete formula inventory for Cup, retrieve its
documentation with source locations, and collect the parent
relations reported for SampleCup. The figure combines SampleCup's
membership and Cup's specialization from those term records. The
build recipe exports the input hash, source locations, count fields,
and relation records before drawing the figure.
