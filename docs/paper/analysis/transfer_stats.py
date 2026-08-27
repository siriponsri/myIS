#!/usr/bin/env python3
"""
transfer_stats.py — produce the six inferential numbers the paper needs,
so the placeholder macros in main.tex can be filled.

INPUT (you provide): per-query Recall@100 for the 9 transfer cells
(3 sources x 3 targets) over the 250 development queries, aligned by query id,
plus per-query nDCG@10 for the two Final-872 systems (selected, comparator).

If those per-query arrays are already saved from your runs, load them here.
If not, dump them from the frozen configs WITHOUT re-selecting anything, and
verify each cell mean reproduces the published Fig-2 value within 1e-4 before
trusting the output (see PUBLISHED_CELL_MEANS below).

OUTPUT: stats.json + printed macro values ready to paste into main.tex.
"""
import json
import numpy as np

SEED = 0
N_BOOT = 10_000
rng = np.random.default_rng(SEED)

# Fig-2 published cell means (Recall@100), for the integrity check on any recompute.
PUBLISHED_CELL_MEANS = {
    "PatEmbed": {"PatEmbed": 0.418436, "Arctic": 0.418715, "Qwen3": 0.419274},
    "Arctic":   {"PatEmbed": 0.337430, "Arctic": 0.341341, "Qwen3": 0.338268},
    "Qwen3":    {"PatEmbed": 0.362570, "Arctic": 0.359497, "Qwen3": 0.360615},
}
SOURCES = ["PatEmbed", "Arctic", "Qwen3"]
TARGETS = ["PatEmbed", "Arctic", "Qwen3"]


def load_per_query():
    """
    Return recall[target][source] -> np.array of shape (250,), query-aligned,
    and ndcg10_sel, ndcg10_cmp -> np.array of shape (872,).
    TODO: wire this to your saved arrays (results/, eval/, *.parquet, *.npy).
    """
    raise NotImplementedError(
        "Point load_per_query() at your saved per-query scores. "
        "If unsaved, recompute the 9 cells from the frozen configs, then "
        "verify against PUBLISHED_CELL_MEANS before returning."
    )


def paired_boot_ci(diff):
    means = np.array([rng.choice(diff, size=diff.size, replace=True).mean()
                      for _ in range(N_BOOT)])
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def fmt_ci(lo, hi):
    return f"[{lo:.3f}, {hi:.3f}]"


def main():
    recall, ndcg10_sel, ndcg10_cmp = load_per_query()

    # integrity check on any recompute
    for t in TARGETS:
        for s in SOURCES:
            got = float(np.mean(recall[t][s]))
            exp = PUBLISHED_CELL_MEANS[t][s]
            assert abs(got - exp) < 1e-4, f"cell ({t},{s}) mean {got} != published {exp}"

    out = {"seed": SEED, "n_boot": N_BOOT, "within_target": {}, "argmax_stability": {}}

    for t in TARGETS:
        ranked = sorted(SOURCES, key=lambda s: recall[t][s].mean(), reverse=True)
        best, second = ranked[0], ranked[1]
        diff = recall[t][best] - recall[t][second]
        lo, hi = paired_boot_ci(diff)
        out["within_target"][t] = {
            "best": best, "second": second,
            "best_minus_second": float(diff.mean()),
            "ci": [lo, hi], "contains_zero": lo <= 0 <= hi,
        }

    # bootstrap argmax stability
    n = recall[TARGETS[0]][SOURCES[0]].size
    for t in TARGETS:
        counts = {s: 0 for s in SOURCES}
        for _ in range(N_BOOT):
            idx = rng.integers(0, n, size=n)
            means = {s: recall[t][s][idx].mean() for s in SOURCES}
            counts[max(means, key=means.get)] += 1
        probs = {s: counts[s] / N_BOOT for s in SOURCES}
        probs["max_argmax_prob"] = max(probs.values())
        out["argmax_stability"][t] = probs

    d10 = ndcg10_sel - ndcg10_cmp
    lo, hi = paired_boot_ci(d10)
    out["ndcg10_ci"] = {"diff": float(d10.mean()), "ci": [lo, hi]}

    json.dump(out, open("stats.json", "w"), indent=2)

    # ready-to-paste macros
    wt = out["within_target"]
    print("\\renewcommand{\\wtPatCI}{%s}"  % fmt_ci(*wt["PatEmbed"]["ci"]))
    print("\\renewcommand{\\wtArcCI}{%s}"  % fmt_ci(*wt["Arctic"]["ci"]))
    print("\\renewcommand{\\wtQwenCI}{%s}" % fmt_ci(*wt["Qwen3"]["ci"]))
    maxp = max(out["argmax_stability"][t]["max_argmax_prob"] for t in TARGETS)
    print("\\renewcommand{\\maxArgmaxProb}{%.2f}" % maxp)
    print("\\renewcommand{\\ndcgtenCI}{%s}" % fmt_ci(*out["ndcg10_ci"]["ci"]))
    print("% \\comparatorSpec: fill by hand from your Final-872 comparator config")


if __name__ == "__main__":
    main()
