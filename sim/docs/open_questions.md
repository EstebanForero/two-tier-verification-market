# Open questions
1. Ground truth for "safe": what is ρ_bnd for bounded claims as a function of depth? It needs empirical data (Halmos/hevm runs on mutants and known exploits) from the Verification Researcher.
2. How large must the random-audit share η be for low-variance IPW scoring, given that the audit budget also has to push tasks to full resolution (UCERT or audit)? Who pays for it?
3. Robust aggregation: the first sim run shows the median is captured once adversarial plus lazy reports pass 50%. Which aggregator should we use (stake-capped trimmed log-odds, or reputation-weighted from audit-set skill)? How do we stop lazy reports from adding to an attack?
4. UCERT checking cost: the brief notes only ~4% of Carcara proofs check ≥10× faster than solving, and Alethe lacks arrays. Is "checkable unbounded certificate" practical for EVM at all, or will nearly everything be BSAFE?
5. CEX withholding against exploit value: an in-protocol bounty cannot beat v_exploit for high-TVL contracts. Should bounties be TVL-indexed, paired with off-chain disclosure, or come with a timelock on certification?
6. Mutant indistinguishability: can EVM mutants be generated that ML and provers cannot tell apart from real bugs? Leakage breaks anti-laziness.
7. Peer prediction or Bayesian truth serum for tasks that never resolve: no source has been read yet, so this is uncited. Should it be considered?
8. Beacon design and on-chain cost of the commit-reveal on every ML report, given the number of tasks per epoch.
9. Combinatorial LMSR (brief option) versus per-task scoring: does it reduce correlated manipulation across properties of the same contract?
