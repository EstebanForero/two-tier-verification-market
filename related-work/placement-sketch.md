# Where the two-tier market lives in Ethereum: placement sketch
Protocol Researcher, 2026-10-30. Sources: see survey.md and references.bib.

## Option A: contract-level escrow (application layer)
**Components**
- `MarketEscrow`: holds the bounty pool and the stakes of screeners and provers.
- `ScreenerBook`: commit-reveal of risk probabilities per (codehash, property). Scores are settled later against a resolution oracle.
- `ProverRegistry`: provers submit certificates.
  - Counterexamples are replayable EVM traces. They are checked by an on-chain or optimistic re-execution adapter, for example a fault-proof VM in the style of Cannon or BoLD, so a single interactive dispute settles them.
  - CHC/invariant certificates go to a checker contract or to an off-chain checker plus a challenge game.
  - Bounded "safe" claims open a refutation window, and the reward decays with p_bug.
- `Router`: allocates the fixed FV budget from the reported scores, using commit-reveal and randomized spot checks.

**Tradeoffs**
| Dimension | Assessment |
|---|---|
| Trust | Ethereum L1 plus the resolution oracle (audits and exploits need an oracle or committee; only counterexamples are trust-free) |
| Liveness | Needs at least one honest challenger per window. Verifier's-dilemma risk is mitigated with attention tests (RAT, Proof of Diligence) |
| Gas | Trace replay is cheap for short traces. Certificate checking on-chain is likely infeasible, so it needs off-chain checking plus a challenge game |
| MEV | Front-running of counterexample submissions (bounty theft) and of score reveals. Use commit-reveal with a binding to the submitter address |
| Upgrade path | Fast: a proxy or versioned markets; we can iterate in 3–4 months |
| Slashing hooks | Only stake held in the escrow. Restaking (e.g. EigenLayer-style AVS) is possible but adds trust assumptions we have not surveyed |

## Option B: protocol-level (enshrined)
Model this on the ethresear.ch L1 prover-market proposal: a system contract plus attester enforcement. One could imagine the protocol reserving a "verification prize" that is paid when a certificate is included, with attesters checking availability, possibly using ePBS-style (EIP-7732) builder payment plumbing.

| Dimension | Assessment |
|---|---|
| Trust | Strongest: payment is enforced by consensus |
| Liveness | Tied to slot timing, but FV jobs take minutes to days and do not fit slot cadence |
| Gas | Could be priced like "prover gas," but certificate-check costs are unbounded and often close to solving cost (Carcara: about 4% of proofs at ≥10× speedup) |
| MEV | Builders could censor or reorder counterexamples. Inclusion lists would be needed |
| Upgrade path | Hard fork; a multi-year process. Ethereum is still debating whether even an L1 *ZK prover* market is needed |
| Slashing hooks | Native validator slashing, but slashing validators for wrong opinions on application-contract safety is out of scope for consensus |

## Recommendation
**Option A, a contract-level escrow.** Enshrinement fails three tests:
1. Contract safety is not a consensus-validity condition.
2. Ground truth arrives late and through an oracle.
3. Ethereum has not even settled an enshrined market for deterministic block proofs.

Present Option B in the paper only as a discussion item. It becomes relevant if zkVM-circuit verification (the brief's future target) becomes a validity condition, because those circuits do sit on the protocol path.

**Hybrid for the demo (Foundry):**
- Escrow, ScreenerBook, and Router on L1 or an L2.
- Counterexample replay done on-chain in the escrow for small traces.
- An off-chain checker plus a BoLD-style single-witness challenge for certificates.
- The resolution oracle as a multisig or committee, stated explicitly as a trust assumption.

## Open questions for Mechanism Designer
- Bond sizing so that a bogus counterexample or certificate is unprofitable when checking costs gas.
- Reward-decay schedule for "safe" claims as a function of the ML p_bug, while preventing screeners from inflating p_bug to steer provers.
- Duration of the refutation window compared with BoLD's bounded delay.
