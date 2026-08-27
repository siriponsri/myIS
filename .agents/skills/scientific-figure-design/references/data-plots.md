# Data/result plots

Use a figure when pattern/trend/distribution matters.
Use a table when exact values matter.

Common mappings:
- methods x one metric -> dot/bar plot or compact table;
- metric vs depth/parameter -> line plot;
- paired per-query effects -> distribution/ECDF/paired-difference plot;
- matrix of conditions -> heatmap only if pattern matters;
- ablation -> dot/bar/table depending exact-value need;
- exposure/coverage decomposition -> stacked count/percentage plot if parts-of-whole is the claim.

Rules:
- show meaningful baseline/reference;
- do not truncate axes in ways that exaggerate effects;
- label units;
- use justified precision;
- show uncertainty when available and relevant;
- keep colors semantic across figures;
- do not decorate empty regions merely to fill space.
