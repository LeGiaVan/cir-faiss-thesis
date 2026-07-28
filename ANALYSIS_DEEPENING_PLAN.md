# Plan: Deepening Analysis Beyond Raw Numbers

**Trigger:** User feedback — current paper reports numbers (speedup ×, retention %) but doesn't
always explain *why* those numbers come out the way they do. A reviewer will ask "why" for every
"what." This plan lists, for each weak point, a concrete, computable investigation that produces a
mechanistic or theory-grounded explanation — not a rerun of the sweep, just deeper analysis of data
we already have on disk.

**Rule for this phase:** no LaTeX edits until each investigation's actual output is known. If an
investigation doesn't support a clean story, the plan is to report what the data actually shows
(possibly a weaker or different claim), not to force the hypothesis.

---

## Current weak points (numbers without mechanism)

| # | Location in paper | What's just a number today | What's missing |
|---|---|---|---|
| 1 | §III-C, nlist formula | `nlist ≈ √N` / `4√N` presented as our own ad-hoc choice | No citation to the standard FAISS guideline; no explanation of why we picked the low end of the range |
| 2 | Finding 2 (IVFPQ) | "Retention 10.9–58.7%, no config reaches 95%" | No explanation of *why* PQ fails this badly on these embeddings specifically |
| 3 | Finding 3 (HNSW vs IVFFlat exception) | "Depends on embedding distribution" — asserted, not measured | No actual geometric measurement of the two models' embedding spaces |
| 4 | Finding 1 (scale threshold) | "Threshold lies somewhere between 6K and 123K" — an interval between two tested points | No model of *why* latency crosses over, no attempt to narrow the interval |

---

## Investigation 1 — Ground the nlist formula in the literature
**Cost:** ~15 min. **Risk:** low.

FAISS's own guidelines (wiki: "Guidelines to choose an index") recommend `nlist` between
`4·√N` and `16·√N` for IVF indexes. We currently use the *lower* half of that range
(`√N` to `4·√N`) because the upper half caused the "too few points per centroid" warning on our
smaller galleries (FashionIQ: 3.8–6.3K images) — a bug we already diagnosed and fixed earlier in
the project. This is a citation-and-one-paragraph fix: pull the exact guideline text via WebFetch,
cite it properly in §III-C, and state explicitly that we chose the conservative end of the
documented range for a documented reason (small-gallery centroid starvation), rather than picking
numbers arbitrarily.

**Output:** 1 citation + 1 paragraph in §III-C. No new data needed.

---

## Investigation 2 — IVFPQ reconstruction-error analysis
**Cost:** ~45–60 min. **Risk:** low (FAISS exposes `index.pq` directly; straightforward to compute).

**Hypothesis:** PQ's catastrophic retention loss (as low as 10.9% on CIRCO) is explained by
quantization error being large relative to the embedding space's discriminative signal. Our
embeddings are 512–768-d (CLIP-derived); with `m ∈ {8, 16}` sub-quantizers, each sub-vector is
64–96 dimensions compressed to a single 8-bit (256-centroid) code — coarse for this dimensionality.

**Method:**
1. Take the actual gallery embeddings already on disk (e.g. SEARLE/CIRCO, PQ's worst case).
2. Build the same `IndexIVFPQ` configurations used in the sweep (m=8, m=16), extract per-vector
   reconstruction error `‖x − PQ_decode(PQ_encode(x))‖₂` via `index.pq`.
3. Compare that error's magnitude to the "signal scale" needed for correct top-10 ranking: the
   typical distance gap between a query's rank-10 and rank-11 nearest neighbors. If reconstruction
   noise exceeds that gap for most queries, misranking is mathematically inevitable, not a tuning
   failure.
4. Report error vs `m` (does m=16 measurably reduce error vs m=8, consistent with the small
   retention gains actually observed between the two settings?).

**Output:** 1 table (reconstruction error vs m, vs signal-scale gap) + 1 paragraph replacing the
"IVFPQ just doesn't work well here" framing with a quantitative reason, in the Finding 2 discussion.

---

## Investigation 3 — Embedding geometry analysis for the Finding 3 exception
**Cost:** ~45–60 min. **Risk:** medium (the metric might not show a clean difference — if so, report
that honestly and soften the claim rather than force it).

**Hypothesis:** Pic2Word's CIRCO embeddings have different geometric structure than SEARLE's
(same gallery images, different embedding space), which is why HNSWFlat under-performs on Pic2Word
specifically while IVFFlat does not.

**Method:**
1. Compute **relative contrast** (Beyer et al.-style: ratio of mean nearest-neighbor distance to
   mean random-pair distance) on the same CIRCO gallery, separately for SEARLE's and Pic2Word's
   embeddings — using the `.npy` feature files already extracted, no rerun needed.
   Lower relative contrast = points more concentrated = harder for both ANN families, but known in
   the ANN literature to affect graph-based and partition-based methods differently.
2. If time permits, cross-check with a cheap secondary signal: IVFFlat's own k-means training
   objective (inertia / average within-cluster distance) for the two embedding spaces, already
   computable from the indexes already built in the sweep.
3. Connect whichever metric shows a real difference to the observed ordering flip.

**Output:** 1 small comparison table (SEARLE vs Pic2Word, CIRCO) + 1 paragraph in Finding 3. If the
geometry metric does *not* differ meaningfully between the two, the paragraph will say so and
reframe Finding 3 as an open, unexplained empirical exception rather than claim a mechanism we
can't support.

---

## Investigation 4 — Latency crossover model for the scale threshold
**Cost:** ~45–60 min. **Risk:** medium (only ~5 usable (N, latency) points; fit will be indicative,
not definitive — will be presented with that caveat).

**Hypothesis:** Instead of asserting "somewhere between 6K and 123K" from just two tested scales, a
simple cost model fit to the data we already have can produce a specific estimated crossover point.

**Method:**
1. We already have Latency (ms) for FlatIP and HNSWFlat at 5 distinct gallery sizes for models
   evaluated across multiple datasets (FashionIQ's 3 categories: N≈3.8K/5.4K/6.3K; CIRR: N=2.3K;
   CIRCO: N=123K) — pulled directly from existing benchmark CSVs, no rerun.
2. Fit `Latency_Flat(N) ≈ a·N + b` (linear scan) and `Latency_HNSW(N) ≈ c·log(N) + d` (graph
   traversal) via least squares.
3. Solve for the crossover `N*` where the two fitted curves meet; report fit quality (R²) alongside
   it, and compare `N*` against the empirical FashionIQ/CIRR/CIRCO boundary.

**Output:** 1 small crossover plot/table + 1 paragraph in Finding 1, replacing the vague interval
with a specific estimated `N*` and an honest caveat about the small number of fitted points.

---

## Investigation 5 — CLIP4Cir/FashionIQ differential-diagnosis table (polish, not new analysis)
**Cost:** ~15–20 min. **Risk:** none — this is presentation only; the underlying investigation
(4 ruled-out hypotheses) is already done and documented in `SANITY_CHECK_REPORT.md`.

Turn the existing prose paragraph into a compact table: hypothesis tested → method → result →
ruled out / not ruled out. Makes the already-rigorous diagnostic work easier for a reviewer to
verify at a glance, in §IV-B.

---

## Order of execution (cheapest / highest-impact first)

1. Investigation 1 (nlist citation) — trivial, do first
2. Investigation 2 (PQ reconstruction error) — highest impact, explains the weakest Finding
3. Investigation 3 (embedding geometry) — explains the unexplained exception in Finding 3
4. Investigation 4 (latency crossover model) — strengthens Finding 1's vague claim
5. Investigation 5 (CLIP4Cir table) — cheap polish, do last

**Total estimated effort:** ~3–3.5 hours of investigation before any LaTeX is touched. Each
investigation will be reported back with its actual finding — including if a hypothesis turns out
not to hold — before the corresponding paragraph in `main.tex` is written or edited.
