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

## Added after v0.2 (see results_v02.md)
10. **Low-tail coalitions:** a deflator + lazy coalition at 60% beats both median and trimmed aggregation. How much audit data (η × budget) does skill weighting need to separate honest screeners, and can attackers game the skill weights by being honest on audit-like tasks? Audit tasks are uniform, but attackers who see task features might still tell them apart.
11. **ρ_bnd and propriety:** the tilt crossover is between 0.5 and 0.71 in the sim. Replace the toy anchor (5/7 from 17 Halmos checks) with Verification Researcher data. Implement and test per-outcome reweighting (r1 = r0) instead of a flat ρ_bnd.
12. **Lazy provers** still earn about 19% of honest pay through BSAFE on safe tasks. Options: higher mutant density, tying BSAFE pay to mutant-kill rate on the same contract, or zero BSAFE pay without a kill.
13. **Window floor W_min:** it is the main defense against suppression, but its capital-lock-up cost is unmodeled. What is the right W_min given the measured refuter hazard λ?
14. **Exploration share η:** with a fixed budget, η lowers recall. Should the audit share be funded separately from the FV budget?
