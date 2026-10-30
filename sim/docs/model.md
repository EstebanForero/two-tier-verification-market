# Formal reward and slashing model: two-tier verification market

Status: draft v0.1 (Mechanism Designer, Oct 30, 2026). Defers to ../BRIEF.md. All numbers are **illustrative** unless they come with a citation.

## 0. Objects and notation
| Symbol | Meaning |
|---|---|
| c ∈ C | contract (EVM bytecode), j ∈ J_c a property (e.g. "no reentrancy-drain", "owner-only selfdestruct") |
| x = (c,j) | a *task*; Y_x ∈ {0,1} the true label (1 = property violated, i.e. a bug exists) |
| i ∈ M | ML screener; i reports p_ix ∈ [ε, 1−ε] |
| k ∈ F | FV prover |
| s_i, s_k | posted stake (bond) |
| S(p,y) | strictly proper scoring rule; default: Brier S(p,y) = −(y−p)² (bounded); alternative: log score (unbounded, needs clipping ε) |
| B_t | FV budget for epoch t (prover-hours, or token units) |
| π_x | routing probability that x receives FV budget |
| a_x ∈ {0,1} | x actually routed |
| W | refutation window length (blocks) for bounded/"safe" claims |
| q̂_x | aggregate ML bug probability at the time a safe claim is posted |
| O_x ∈ {CEX, PROOF, EXPLOIT, AUDIT_BUG, AUDIT_CLEAN, ⊥} | ground-truth oracle event; ⊥ = unresolved |
| m ∈ Mut_c | mutants of c (seeded faults) used to weight FV kills |

Time is in epochs t; each epoch has phases: **commit → reveal → route → prove → window → settle**.

## 1. Tier 1 (ML screeners)

### 1.1 Reporting
1. Commit: i posts h_ix = H(p_ix ‖ salt_ix) for each x in its declared coverage set X_i (|X_i| ≥ n_min to prevent cherry-picking, see analysis §2.3). Stake s_i ≥ σ_ML · |X_i|.
2. Reveal: i reveals (p_ix, salt). Unrevealed commits are scored at the *worst* score in the bounded rule (S = −1 under Brier), i.e. non-reveal is strictly dominated.
3. Aggregate: q̂_x = Agg({p_ix}) (stake-weighted, trimmed log-odds mean; weights capped, see §3.3).

### 1.2 Payoff
Settlement only when ground truth resolves (O_x ≠ ⊥). Let ρ_x ∈ [0,1] be the *resolution weight* of the oracle event:
- FV counterexample (replayed, valid): Y=1, ρ = 1
- exploit on-chain (attested): Y=1, ρ = 1
- FV unbounded certificate checked (e.g. CHC invariant): Y=0, ρ = 1
- audit report: Y as reported, ρ = ρ_audit < 1 (auditor fallible)
- bounded "safe" claim survived window W: Y=0, ρ = ρ_bnd(depth) < 1 (bounded ≠ proof)

Screener payoff on x (relative to a reference forecast r_x, e.g. the leave-one-out aggregate or base rate):

  R_ix = α · ρ_x · w_x · [ S(p_ix, Y_x) − S(r_x, Y_x) ]

where w_x = 1/P(resolved | routing) is an **inverse-propensity weight** (§3.1). Subtracting a report-independent term keeps propriety (Gneiting & Raftery 2007, eq. (2): S* = cS + h(ω) is proper). The relative form makes the market budget-balanced in expectation when r_x is the aggregate of others (zero-sum among screeners, plus a subsidy α·κ for information).

**Slash**: if Σ_x R_ix over the settlement horizon < −s_i·λ, the loss is taken from stake; payoffs are capped at ±α per task so stake covers worst case: s_i ≥ α·|X_i|·max|ΔS|. No other slash conditions for ML — being *wrong* is priced, not punished; only non-reveal and provable equivocation (two reveals for one commit) are slashed outright (100% of per-task bond).

### 1.3 Settlement timing
- Payoff R_ix is escrowed until O_x resolves or horizon H expires.
- At H with O_x = ⊥: task is voided for scoring (stake returned, no reward) — but voiding is *selection-biased* (see analysis §1.2); hence the IPW weight w_x and the random-audit set.
- Vesting: positive R_ix vests over V epochs to make late-discovered errors clawable (an exploit after an "audit clean" re-opens settlement within the clawback horizon H_cb).

## 2. Tier 2 (FV provers)

### 2.1 Certificate types
| Type | Check | Slash on invalid | Paid when |
|---|---|---|---|
| CEX: replayable EVM trace violating j | replay in reference EVM (hevm), cheap | immediately, full per-claim bond b_k | immediately on valid check |
| UCERT: checkable unbounded cert (CHC invariant + checker) | run checker, cost may be high (brief: ≥10× faster than solving only for ~4% of Carcara proofs) | immediately, full bond | on valid check |
| BSAFE: bounded "no violation up to depth d / loop bound L" | not checkable cheaply | only if refuted by a CEX within window W | at window close, decayed |

### 2.2 Payoff for valid certificates
Base reward for a valid certificate on x:

  P_k(x) = β_type · v_x · U_k(x)

- v_x: value of the task (e.g. TVL-weighted or fixed per property class).
- U_k(x) = **uniqueness/mutant-kill weight**. Each epoch a hidden mutant set Mut_c is injected (TrueBit-style forced errors; Teutsch & Reitwießner, §4.1/§4.4). For a prover set killing mutants K_k ⊆ Mut_c, U_k = Σ_{m∈K_k} 1/n_m where n_m = number of provers killing m (Shapley-like split per mutant). Real bugs (non-mutants) found first get a first-finder bonus γ·v_x, ordered by commit time (see §4 commit-reveal for front-running).
- Duplicates: a CEX for an (x, root-cause) already registered earns only the 1/n split.

### 2.3 Stake and slash
- Per-claim bond b_k ≥ (cost of checking the claim) + (expected reward of the claim) — mirrors TrueBit's deposit rule that deposits exceed expected payout plus dispute cost.
- Invalid CEX/UCERT: slash b_k; split φ to the checker/challenger, (1−φ) **burned** (burning prevents self-challenge collusion; as in optimistic rollups, part of the bond is burned "to prevent collusion among validators", ethereum.org).

## 3. Routing
Each epoch, budget B_t is spread over tasks by

  π_x = (1−η)·g(q̂_x, v_x) / Σ g + η·u_x

- g = value of information heuristic, e.g. g = v_x·q̂_x (or v_x·q̂(1−q̂) for uncertainty sampling).
- η ∈ [0.1, 0.3] (illustrative) = **exploration share**, u_x uniform over eligible tasks.
- Draw a_x ~ Bernoulli(π_x) using a randomness beacon revealed *after* ML reveals (commit-reveal, §1.1), so screeners cannot condition on the draw.
- Cap any single screener's influence on q̂ at weight ω_max (stake-weighted, capped).
- Record π_x on chain → enables IPW settlement (w_x = 1/π_x for the subset whose resolution came only via routing).

## 4. Counterexample-first refutation window (CFRW)

### 4.1 Definition
When prover k posts BSAFE(x, d) at time τ0:
1. Window W_x = [τ0, τ0 + W(q̂_x)] opens. Window length grows with risk: W(q̂) = W_0 · (1 + κ_W·q̂).
2. During W_x, **anyone** may submit a CEX for x. The first valid CEX (by commit time, §4.4) wins: k loses bond b_k; refuter gets φ·b_k + standard CEX reward P(x); remainder burned.
3. If W_x closes unrefuted, k is paid

   P_safe(x) = β_safe · v_x · (1 − q̂_x)^θ · h(d)

   i.e. reward **decays with ML bug probability** (the brief's "counterexample-first slashing"): saying "safe" on a high-risk contract is paid little unless upgraded to UCERT. h(d) increasing, concave in bound depth.
4. "Counterexample-first" priority rule: while x has any open BSAFE window, routing gives CEX search on x priority budget share ∝ q̂_x (refuters are subsidised exactly where ML thinks bugs are).
5. Late refutation (after window, within clawback horizon H_cb): unvested part of P_safe is clawed back; no bond slash (bond already released) — reduces but doesn't remove risk.

### 4.2 Interaction with ML settlement
- A CEX inside the window resolves Y_x = 1 with ρ=1 → ML scores settle immediately.
- Window closing unrefuted resolves Y_x = 0 with **ρ_bnd < 1** only. ML scores settle *partially*: fraction ρ_bnd now, remaining (1−ρ_bnd) held until UCERT/audit/exploit or horizon H.
- **Coupling hazard**: q̂_x determines both P_safe (via decay) and W length. A screener who is also a prover can lower q̂_x to (a) raise its own P_safe and (b) shorten the window. Mitigations: q̂ used for the decay is **frozen at commit time before the BSAFE claim** (the q̂ snapshot is fixed when routing is decided), a screener's own reports are excluded from q̂ used for claims by linked addresses (only enforceable for declared links — see analysis §2.2), and W has a floor W_min.

### 4.3 Griefing and timing attacks (analysis)
| Attack | Mechanism | Defense | Residual |
|---|---|---|---|
| G1 Spam refutations | submit invalid CEXs to delay settlement | CEX is cheap to check; invalid CEX slashes refuter bond b_r ≥ check cost | low |
| G2 Window censorship / last-block sniping | refuter withholds CEX until final block, or chain congestion lets a censor block the refutation | inclusion via commit-reveal (commit H(cex) is a tiny tx, reveal later); window extends by Δ if a commit lands in the last Δ blocks | censorship by builders at L1 level — assumed away like TrueBit §2.2 |
| G3 Withhold-and-farm | prover knows a CEX on x, posts BSAFE from Sybil A and refutes from Sybil B to collect φ·b + P(x) | burn (1−φ) ≥ the gain: require φ·b_k + P(x) − b_k < 0, i.e. b_k > P(x)/(1−φ) | binding constraint on bond size |
| G4 Bond-pricing griefing | attacker posts many BSAFE on low-q̂ tasks to lock up checking/refuter attention | per-claim fees, BSAFE requires routing assignment (cannot be posted unrouted) | moderate |
| G5 Risk-down timing | coordinated screeners push q̂ low right before a BSAFE to shorten W and raise P_safe | freeze q̂ snapshot; W_min; ML deflation is itself costly under proper scoring when bug later found | quantified in analysis §3 |
| G6 Delay-to-exploit | malicious deployer/prover wants contract "certified" before exploiting | BSAFE never grants "certified" status — only UCERT does; publish window status | social/UX |
| G7 Racing duplicate CEXs | refuter's CEX front-run by a copier who sees mempool | commit-reveal ordering; first commit wins | none if commit is binding |

Window length tradeoff (illustrative): refutation probability within W for a bug with detection hazard λ_x is 1 − e^{−λ_x W}; prover-capital lock-up cost ∝ b_k·W·r (r = cost of capital). Choose W to equate marginal detection to marginal lock-up cost; derivation in analysis §1.4.

## 5. Settlement timeline (per task)
1. t0 commit ML → t0+1 reveal → beacon → route (π_x recorded, a_x drawn)
2. Routed: provers commit claims (CEX/UCERT/BSAFE) → reveal → check
3. CEX/UCERT: checked & paid/slashed at once; ML settles (ρ=1)
4. BSAFE: window W(q̂) → close → P_safe paid (vesting) → ML settles at ρ_bnd
5. Horizon H: unresolved tasks voided for direct scoring; IPW-weighted random-audit set carries ML calibration incentive
6. Clawback horizon H_cb: exploits/audits reopen unvested rewards.

## References
See analysis.md §References (shared list).
