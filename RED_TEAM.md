# Red-team: Sayari entity-resolution pipeline

An adversarial, fair reading of Sayari's publicly documented resolution methodology (documentation.sayari.com), tested against the register-assurance lens and our keyless census of the OpenSanctions backbone their world model must ingest. Every failure mode traces to a stated design choice in their own docs, not a straw man.

## Summary

Sayari's pipeline is genuinely strong where it commits to hard evidence: a two-tier design (hard identity merges vs lower-confidence PSA edges), blocking-then-matching to bound cost, a transitive-closure splitter, and full record-level provenance. The register-assurance lens finds defensible risk in four places. First, identity passes 1 and 2 merge on blocking keys with NO conflict examination, so a reused or mistyped "strong" identifier over-merges silently; Sayari's own downgrade log (deu_registernummer, chn_customs_registration_code, jordan_company_no, usa_sam_uei) proves "strong" IDs are not unique, and even LEIs collide in the clean OpenSanctions backbone (6 LEIs, 6 BICs, 103 QIDs each span more than one entity). Second, the splitter fires ONLY on strong-identifier and birth-year conflicts, so two entities sharing a nominee name plus address never split. Third, recall is capped at blocking with no published floor, worsened by off-the-shelf translation and transliteration. Fourth, there is no temporal supersession model, so stale attributes present as live. Each maps to an OWL/SHACL gate we already ship and have run against the open backbone.

## Failure modes

### [HIGH] Silent over-merge on reused non-unique strong identifier in passes 1-2
- Mechanism: Identity passes 1 and 2 merge references on blocking keys alone that are deemed strong enough to resolve with no matching or conflict examination. If a strong-identifier value is used as such a key and is in fact non-unique, two distinct entities merge. The splitter cannot rescue it: splitting fires only on CONFLICTING strong IDs, and here the entities SHARE the same ID value, so no conflict is registered.
- Trigger: Two distinct legal entities carry the same registry number (registry number recycled or scoped per court/office, e.g. deu_registernummer across Amtsgerichte, or a recycled usa_sam_uei), or a data-entry error copies one entity's ID onto another.
- Evidence: Sayari downgraded deu_registernummer, chn_customs_registration_code, jordan_company_no and usa_sam_uei_number from strong to weak after finding them non-unique. Our census: even LEI, which by ISO 17442 identifies exactly one legal entity, has 6 distinct values each attached to more than one entity in OpenSanctions.
- Test we would run: SHACL uniqueness shape asserting every strong-identifier-type value resolves to exactly one entity, run at ingest; check-digit and registry-scope validation (LEI ISO 17442 plus ISO 7064, BIC well-formedness) before an ID is admitted as a merge key; any value spanning more than one entity routed to a merge-review queue.

### [HIGH] Splitter blind to name-plus-address over-merge
- Mechanism: The splitter triggers only on conflicts in strong identifiers and birth years. Two distinct companies or persons that share a name and a nominee or registered-agent address form a block, pass business-logic matching, and merge via connected components. With no strong ID and no birth year in conflict (often both absent), nothing ever fires the split, so the false merge is permanent.
- Trigger: Shared nominee, registered-agent, or mass-registration address plus a similar or identical name, no strong identifier present. This is the ordinary FinCrime shell-company pattern.
- Evidence: Stated assumption that the only merge-falsifying conflicts are strong-identifier and birth-year mismatches; recon gap explicitly names two distinct companies sharing name plus address as a prime over-merge surface the splitter never corrects; adversarial gap notes shared nominee addresses over-merge and is unquantified.
- Test we would run: SHACL shape that flags a merged component whose members carry conflicting single-valued attributes (distinct incorporation dates, distinct jurisdictions, conflicting company status, differently-typed registration numbers) even when no strong-ID conflict exists, plus a cross-register agreement check per member.

### [HIGH] Recall floor at blocking: varied spellings and redacted addresses never resolve
- Mechanism: Recall is bounded by blocking-key co-occurrence. Two references to the same entity that share no key (an alias, a transliteration miss, a redacted or omitted address) never enter a common block, are never compared, and never resolve. There is no matching stage that can recover them and no published recall metric to size the loss.
- Trigger: A sanctioned or high-risk entity registers under a varied spelling, a different transliteration, or omits its address across registrations, defeating name and address blocking.
- Evidence: Stated assumption that recall is capped at blocking and never quantified; cross-script handling relies on off-the-shelf Google translation and open-source transliteration; recon gap confirms deliberately varied spellings fall out of every block and the failure is neither measured nor acknowledged.
- Test we would run: A controlled alias and transliteration probe set with known-true matches to measure block co-occurrence recall, plus identifier-anchored bridging (LEI, BIC, QID as script-invariant keys) to recover true matches that name blocking misses.

### [MEDIUM] Cross-script transliteration identity drift
- Mechanism: Translation and transliteration are off-the-shelf and lossy, and the converted Latin strings are indexed as the match basis. The mapping is many-to-one and one-to-many: two distinct source-script names can collapse to the same romanized string (false merge signal) and one name can produce two romanizations (false split), because identity is being adjudicated on a derived, non-invertible string.
- Trigger: Arabic, Chinese, Cyrillic, Korean or Thai names with ambiguous or scheme-dependent romanization enter blocking or the resolution endpoint.
- Evidence: Enrichment claim: names and addresses translated from 14 languages via Google Cloud Translation and person names transliterated via open-source libraries, then the converted names indexed for search; stated assumption that conversion preserves identity faithfully enough to index on.
- Test we would run: A round-trip transliteration consistency check and a collision census of romanized forms that map back to multiple distinct source-script identities, anchoring cross-script identity on scheme-valid identifiers rather than on the converted name string.

### [MEDIUM] Wikidata QID self-cross-reference disagreement bridging distinct entities
- Mechanism: If ingest treats the wikidataId property as an identity signal alongside the canonical id, a record whose canonical QID disagrees with its own declared wikidataId can be blocked or bridged to whichever entity the other QID denotes, joining two references that point at different real-world entities.
- Trigger: Ingesting the 116 entities whose canonical id is a QID but whose wikidataId property declares a different QID, or any of the 103 QIDs already attached to more than one entity.
- Evidence: Our census of OpenSanctions (4,012,096 entities): 116 entities (0.022%) show identity vs self-cross-reference disagreement, and 103 QIDs are each attached to more than one distinct entity.
- Test we would run: SHACL requiring that any QID used as a merge or blocking key be self-consistent (canonical id equals wikidataId) and one-to-one across entities, with disagreements withheld from bridging and sent to review.

### [MEDIUM] No temporal supersession: stale attribute presented as live, real change misread as two entities
- Mechanism: Attributes carry from_date, date and to_date but the resolver uses only birth year, and only as a split trigger. There is no current-versus-historical flag, so a superseded address or a dissolved status is unioned in as if current, and an entity that legitimately changed name, address or owner over time cannot be distinguished from two distinct entities.
- Trigger: A company is renamed, redomiciled, or dissolved and later reactivated; a former registered address persists in older records alongside the current one.
- Evidence: Recon gap: temporal semantics unaddressed, no attribute-level recency or supersession model, from_date and to_date carried but not used by the resolver; only birth year is temporal and only as a split trigger.
- Test we would run: Reified dated assertions with as-of dereference so a value is returned relative to a date, plus a SHACL check that flags a single-valued status or address asserted as live where a later dated record supersedes it.

### [MEDIUM] Uncalibrated global threshold across name distributions and jurisdictions
- Mechanism: The resolution endpoint ranks on a raw Elasticsearch relevance score assumed monotonic in match likelihood and gated by one global minimum (77) and cutoff (0.8). Relevance scales with term rarity, so high-frequency name spaces (common Han surnames, Arabic patronymics) compress the true-versus-false gap and a single global boundary mislabels both directions.
- Trigger: A query in a high-collision name space clears the threshold spuriously, while a near-unique Western name without an address returns weak, as the docs show for Victoria Beckham plus GBR.
- Evidence: Observed raw scores 142 to 685 with default threshold 77 described only as tuned for general use-case accuracy; strong requires an address or identifier not name alone; recon gap: no calibration and no per-jurisdiction threshold guidance.
- Test we would run: A per-jurisdiction and per-name-frequency calibration harness reporting precision at the threshold by name-frequency bucket, exposing where 77 and 0.8 under- or over-fire.

### [LOW] Non-deterministic LLM cleaning ahead of matching
- Mechanism: enable_llm_clean applies LLM normalization to attributes before matching. An LLM pass can normalize inconsistently or hallucinate, changing the tokens fed to blocking and matching so that the same input yields different merges across runs, and can drop or invent a discriminating token that decides a merge.
- Trigger: A noisy attribute (mixed-script address, embedded punctuation, abbreviations) is run through enable_llm_clean; the two docs reads even disagree on whether the default is true or false, which is itself a reproducibility flag.
- Evidence: Recon records enable_llm_clean with conflicting stated defaults across pages and a gap noting it injects non-deterministic normalization with no evaluation, regression test, or hallucination or consistency guarantee.
- Test we would run: A determinism harness that runs identical input N times and diffs the normalized output for idempotence, plus a SHACL check that the cleaned value retains the source identifier tokens verbatim.

### [LOW] Cross-type fragmentation with no recovery path (hypothesis)
- Mechanism: References never resolve across entity types, and there is no described path to reconcile a true match split across types (a tradename versus its owning company, a vessel versus its operator). A single mis-typed reference permanently fragments an entity and the fragmentation is not measured. This is a hypothesis: recon does not quantify how often upstream typing is wrong.
- Trigger: A source types a reference as tradename (a type the ontology marks deprecated) when it is really the operating company, or as generic or unknown.
- Evidence: Stated same-type precondition plus recon gap: no cross-entity-type reconciliation and resulting fragmentation not measured; tradename flagged deprecated, indicating type churn.
- Test we would run: Count strong-identifier values that span more than one entity type in the open backbone as a lower bound on cross-type fragmentation, then bridge those on the shared scheme-valid ID.

### [LOW] PSA 10,000-entity cap severs true large groupings (hypothesis)
- Mechanism: PSA tightens blocking iteratively until components hold at most 10,000 entities, using a computational ceiling as a proxy for evidentiary sufficiency. A genuinely large related network can be split by size rather than by any discriminating contradiction. Hypothesis: recon does not show how often real components approach the cap.
- Trigger: A true possibly-same-as component (a large multinational group or a wide sanctioned network) exceeds 10,000 entities and is forced to split.
- Evidence: Claim that PSA iterates permissive to strict until components are at most 10,000 entities with no matching step; stated assumption that a computational ceiling is an acceptable proxy for sufficiency.
- Test we would run: Identify PSA components near the cap and check whether the tightening split on a real discriminating attribute or purely on size, flagging size-only splits for review.

## Where our open-ontologies assurance plugs in

- Single-valued foreign-identifier gate (SHACL): fail a merge when contributing records carry conflicting single-valued strong IDs, or when one strong-ID value maps to more than one resolved entity. Backed by our check-digit conformance (LEI ISO 17442 plus ISO 7064, BIC well-formedness) so a malformed or non-unique ID is rejected as a merge key before passes 1-2 act on it.
- Splitter-supplement shape: OWL cardinality plus SHACL that promotes incorporation date, jurisdiction, company status and date-of-birth to split-eligible conflict signals, closing the name-plus-address over-merge hole their splitter (strong-ID and birth-year only) structurally cannot see.
- Reified dated assertions for withdrawable provenance: model each attribute as a dated, sourced assertion so a retracted or superseded source claim is withdrawable and as-of dereference returns the value valid at a date. Directly plugs the temporal-supersession gap; same mechanism we ran for Crossref versus RetractionWatch (72.4%).
- Identifier-anchored cross-script bridging: use scheme-valid strong identifiers as script-invariant blocking keys to recover true matches that name and address blocking miss, and to adjudicate transliteration collisions without relying on the lossy romanized string.
- Cross-register agreement gate with dated dereference: before a strong ID is used as a merge key, dereference the source registry to confirm it still resolves to the claimed entity, catching dead or reassigned identifiers (the dead-id class we found at 67,141 in learning standards).
- Merge-review queue seeded by a collision census: every strong-ID value spanning more than one entity (our 6 LEI, 6 BIC, 103 QID signals) becomes a labeled adjudication ticket, supplying the human-in-the-loop QA and ground-truth loop the docs never describe.

## Measured corroboration (from this repo's census)

Six LEI values each resolve to two distinct OpenSanctions entities despite a LEI identifying exactly one legal entity by definition. All six are ISO 17442 and ISO 7064 valid, so the collision is a resolution signal, not a data-entry error:

- `9DJT3UXIJIZJI4WXO774` -> ['NK-4KNVoUMf98KyDn8du8stmP', 'NK-d87S9qAnJrEkTN4MRhmmkB']
- `254900YEEOJ6K56L3058` -> ['NK-J9MEYgzmfmcixV2TP3c6EE', 'gem-own-e100000120962']
- `5493008Z30ZS378SB107` -> ['NK-Y6YoqnMFTXU2XezDw2hUv4', 'NK-mWWKaRkKgxezmwtYC2Y9sL']
- `335800NQ97G16BMPIR07` -> ['NK-YAwat24GYRM7LBBoX2Kho4', 'gem-own-e100002007618']
- `213800JSZ2UUK4QQK694` -> ['NK-bJThAbso99PAbqDzL62S5J', 'NK-iug77aFLjrD5aszCuhtyhb']
- `2534006SR63SEUSS8172` -> ['NK-ebdrof6uHUpHeSr6S4ugv8', 'gem-own-e100002016473']

These, plus 6 BICs and 103 QIDs with the same property and the 116 QID self-cross-reference disagreements, are the merge-review worklist a splitter that fires only on strong-identifier and birth-year conflicts cannot surface.
