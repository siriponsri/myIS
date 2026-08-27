# Equation and readability gate

## Default
A paper does not become more rigorous because it has more equations.

Use a displayed equation only when the mathematical form is necessary to:
- define an objective/metric/transformation precisely;
- establish a property used later;
- make an algorithm reproducible;
- compress a relationship that prose would make less precise.

Prefer prose when:
- the operation is ordinary and easy to name;
- the equation appears once and is never used;
- the same meaning requires a paragraph explaining the notation;
- symbols merely rename fields, ranks, scores, concatenation, filtering, or aggregation;
- a 3–6 line pseudocode block is easier.

## Complexity budget
Each equation spends reader attention.

For every equation:
1. state its purpose in one sentence before or after it;
2. define every symbol locally;
3. reuse notation consistently;
4. remove unused symbols;
5. avoid nested subscripts/superscripts where names are clearer.

## Prose red flags
- >38-word sentences unless structurally unavoidable;
- 3+ abstract nouns chained together;
- repeated "This study aims to";
- repeated "Furthermore/Moreover/Additionally/However";
- empty "important/significant/novel" adjectives;
- multiple clauses whose relationship is not explicit.

Split a sentence when the reader must hold too many conditions before reaching the verb.
