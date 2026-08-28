# OpenSanctions embedded-identifier assurance

A keyless, reproducible census of every foreign identifier embedded in the OpenSanctions `default` collection, checked against each scheme's own published rules. Built 28 August 2026 against the public bulk export (4,012,096 entities, `entities.ftm.json`).

OpenSanctions is an entity register that embeds identifiers minted by other registers: LEI (GLEIF), SWIFT/BIC, Wikidata QIDs, ISIN. The register-assurance question is not whether OpenSanctions curates its own records well. It is whether the foreign identifiers it republishes still conform to the schemes that mint them, and whether any identifier resolves to more than one entity. Nobody checks that at the register boundary, so we did.

## Headline: this is a model register, with a small residue

The fair finding first, because it is the main one. OpenSanctions' embedded-identifier hygiene is essentially perfect:

- **LEI: 9,677 of 9,677 (100%)** pass the ISO 17442 structural rule and the ISO 7064 MOD 97-10 check digit. Not one truncated or malformed value. For contrast, the FDIC publishes all 2,252 of its LEIs truncated to 16 of the required 20 characters (see the bank-register-ontology study); OpenSanctions does the opposite.
- **SWIFT/BIC: 4,659 of 4,659 (100%)** match the ISO 9362 shape.
- **Wikidata: 520,812 of 520,812 (100%)** are well-formed QIDs.

The residue is small and is stated as small:

- **116 entities whose own canonical identifier is a Wikidata QID declare a *different* QID in their `wikidataId` property** (0.022% of the 520,572 QID-keyed entities). The entity's identity and its self-declared cross-reference disagree, which is a two-Wikidata-items-conflated signal. Row-level list in `reports/findings.json`.
- **6 LEI values, 6 BIC values and 103 Wikidata QIDs are each attached to more than one distinct entity.** A LEI identifies exactly one legal entity by definition, so a LEI on two un-merged entities is a resolution-collision candidate. These are the merge review queue, enumerated.

Everything above is computed from the public bulk file with no API key, and re-derived two independent ways by the pipeline.

## Why this matters, and to whom

Entity resolution is the core problem for anyone joining sanctions, ownership, trade and corporate data: given two records, are they the same real-world entity? A shared identifier that is not merged, or a self-identifier that disagrees with its own cross-reference, is exactly the signal that resolution has to get right. This census is the assurance layer for that, run against the open backbone of the space.

## Reproduce

```
python3 pipeline/extract.py < entities.ftm.json     # stream the bulk export, keep entities with embedded ids
python3 pipeline/analyze.py                          # validate each scheme, find collisions
```

The bulk file URL rotates; resolve it from the stable redirect at
`https://data.opensanctions.org/datasets/latest/default/entities.ftm.json`.

## Method, transferable

Declare each identifier scheme's own rules (ISO 17442 + ISO 7064 for LEI, ISO 9362 for BIC, the QID and ISIN patterns), validate every embedded value against its declared scheme, and separately test whether any value resolves to more than one entity. The same method is shipped across bank, insurance, scholarly, learning-standards, biodiversity and health registers at github.com/fabio-rovai and gov.tesseract.academy/research/.

Data: OpenSanctions is published under CC-BY-NC 4.0 (and commercial terms); this repository republishes no OpenSanctions records, only computed conformance counts and identifier-level defect lists.
