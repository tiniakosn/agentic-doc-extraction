# HANDOFF — agentic-doc-extraction (κατάσταση 2026-11-27)

Πηγή: άμεση ανάγνωση του repo, read-only. Όπου γράφει **ΑΓΝΩΣΤΟ**, η πληροφορία δεν επιβεβαιώνεται από τα αρχεία.
Python 3.14 (`.venv`), LangGraph 1.2.12, Pydantic 2.13, PyMuPDF 1.28, langchain-groq 1.1.3. Tests: `pytest -q` → **119 passed**. Όλα τα tests είναι offline, με mocked LLM.

## 1. Δομή (2 επίπεδα)
```
src/  multimodal_graph.py (ο ενεργός LangGraph) · nodes/ (7 nodes) · extraction/ (LLM/VLM) · ingestion/ (PDF, OCR, routing)
      evaluation/ (verification, grounding, correction, document-level) · schemas/ (Pydantic)
tests/ 29 test files          scripts/ 14 (Diavgeia collector, profiling, live runner, OCR/VLM tests)
benchmark_v1/ annotation guidelines, pilot_annotations/ (9 JSON), scripts/ (run/evaluate/compare), adaptive_evidence/ (synthetic)
data/ discovery/ (57 PDF) · metadata/ (57 JSON) · raw/ (4 legacy PDF) · annotations/ (4 legacy) · ocr_ground_truth/ (1 txt)
evaluation_results/ αποτελέσματα πειραμάτων (JSON/CSV)      PROJECT_STATUS.md (ημερολόγιο έρευνας, ~1700 γραμμές)
```
- `ingestion/pdf_loader.py`: φόρτωση PDF και digital text layer με bboxes. `page_quality.py`: σήματα ποιότητας σελίδας. `routing.py`: κανόνες routing.
- `ingestion/ocr_backend.py`: Tesseract (300 DPI). `paddle_backend.py`: PaddleOCR (150 DPI, σε ξεχωριστό `.venv-ocr`).
- `extraction/llm_client.py`: κεντρικό config του Groq. `llm_extractor.py`: text→JSON. `vlm_extractor.py`: εικόνα σελίδας→JSON.
- `evaluation/evidence_verifier`, `source_anchor`, `region_grounding`, `spatial_verifier`, `text_evidence_anchor`: textual/spatial grounding.
- `evaluation/verification_decision`, `final_decision`, `field_validation` (AFM), `claim_verifier` (LLM role check), `evidence_repair`, `correction_controller`.
- `evaluation/document_aggregator`, `document_verifier`, `document_evidence_selector`, `adaptive_evidence_selector`, `document_role_risks`: document-level λογική. **Δεν καλούνται από τον γράφο**· τα χρησιμοποιούν μόνο tests και scripts.

## 2. LangGraph (`src/multimodal_graph.py`): page-level, ένα page ανά εκτέλεση, χωρίς checkpointer
```
START → load_document → assess_and_route ─(extraction_method=="vlm")→ extract_information
                                          └─(αλλιώς)→ process_page → extract_information
→ verify_extraction → semantic_verification → correction_controller ─(retry)→ process_page | (finish)→ END
```
- **Routing** (`routing.py:56-115`, `choose_processing_route_v2`). Ελέγχει με σειρά:
  1. Ύπαρξη χαρακτήρων Unicode Cn → tesseract.
  2. `visual_ink<0.03` και `chars<500` → review.
  3. `image_coverage≥0.5` και `chars<500` → tesseract.
  4. `visual_ink≥0.05` και `chars<500` → tesseract.
  5. `chars≥500` και `greek_ratio≥0.5` και `suspicious<0.02` → digital.
  6. Σε κάθε άλλη περίπτωση → review.

  Τα thresholds σημειώνονται ως «provisional» (`routing.py:62`). Το route `review` εκτελείται προσωρινά ως Tesseract (`assess_and_route.py:27`).
- **Σημαντικό:** το routing **δεν επιλέγει ποτέ VLM ούτε PaddleOCR**. Το VLM ενεργοποιείται μόνο αν ο caller θέσει `extraction_method="vlm"` (`scripts/run_live_workflow.py --strategy vlm|text`). Ο κώδικας επιλογής PaddleOCR υπάρχει στο `process_page.py`, αλλά κανένα route του γράφου δεν τον φτάνει.
- **Validation** (`verify_extraction.py` + `verification_decision.py`):
  - Έλεγχος AFM (9 ψηφία, checksum Mod-11, `field_validation.py:4-22`).
  - Grounding της τιμής και του evidence που έδωσε το LLM μέσα στο κείμενο της πηγής.
  - Region anchoring και spatial έλεγχος μόνο για `recipient` κοντά στο «ΠΡΟΣ:».
  - Actions: AFM άκυρο → `reprocess`· value+evidence supported → `accept`· η τιμή βρέθηκε αλλά το quote διαφέρει → `repair_evidence`· η τιμή δεν βρέθηκε → `reprocess`· κάθε `not_present`/`uncertain` πεδίο → **πάντα `review`** (`verify_extraction.py:77-90`).
- **Semantic verification** (`semantic_verification.py:11`): έως 2 LLM claim checks, με προτεραιότητα contractor > tax_id > recipient. Τα verdicts είναι supported / contradicted / insufficient. Το verdict `supported` με πηγή δίνει `accept_with_evidence`, εκτός αν η απόφαση προήλθε από deterministic validation (`final_decision.py:24-37`).
- **Retry/«reflection»** (`evaluation/correction_controller.py`): `MAX_RETRIES=1`. Retry γίνεται μόνο όταν υπάρχει πεδίο `reprocess` και ισχύει ένα από τα εξής:
  - η μέθοδος ήταν VLM και απέτυχε deterministic validation· ή
  - η μέθοδος ήταν digital με `ink≥0.05` και `chars<500`.

  Το retry ξανατρέχει **Tesseract + text LLM**. **Δεν υπάρχει LLM reflection** με την κλασική έννοια: το prompt του retry δεν περιέχει τα λάθη της προηγούμενης προσπάθειας (`llm_extractor.py:33-46`). Τα legacy tests `test_reflection_loop` και `test_forced_reflection` διαγράφηκαν στο commit `a9f4a58`.
- Τελικό status: `review_required` αν οποιοδήποτε πεδίο είναι `review` ή `reprocess` (`nodes/correction_controller.py:38-46`). Επειδή κάθε `not_present` πεδίο γίνεται `review`, πρακτικά σχεδόν κάθε σελίδα καταλήγει `review_required`. Στο pilot αυτό συνέβη και στις 9/9 σελίδες.

## 3. Μοντέλα, APIs, OCR
- LLM και VLM: **Groq `qwen/qwen3.8-27b`**, το ίδιο μοντέλο για κείμενο και εικόνα, με `temperature=0` και `json_mode` structured output. Config στα `extraction/llm_client.py:6` και `llm_extractor.py:7`. Το key διαβάζεται από `.env` (`GROQ_API_KEY`).
- OCR: Tesseract 5.3.4 (`ell+eng`, 300 DPI) και PaddleOCR 3.4.1, PP-OCRv5 mobile (`el`, 150 DPI, CPU). Για εικόνες σελίδων χρησιμοποιείται PyMuPDF.
- Η διαθεσιμότητα του μοντέλου στο Groq μέχρι το τέλος της εργασίας είναι **ΑΓΝΩΣΤΗ**. Το ίδιο ισχύει για το κόστος και τα rate limits.

## 4. Extraction schema (`schemas/page_extraction.py`)
- Πέντε πεδία: `document_type`, `issuing_authority`, `recipient`, `contractor`, `contractor_tax_id`.
- Κάθε πεδίο έχει `{value: str|None, status: present|not_present|uncertain, evidence: str|None}`. Το `present` απαιτεί value και evidence.
- `document_type`: ελεύθερο κείμενο στο extraction. Ο evaluator το αντιστοιχίζει σε award_decision, invitation, commitment_decision, administrative_order, administrative_decision ή contract_summary.
- Υπάρχει και document-level schema (`schemas/document_extraction.py`), με επιπλέον status `conflict` και sources ανά σελίδα. Δεν χρησιμοποιείται από τον γράφο.
- Τα οικονομικά πεδία (ποσά, ΦΠΑ) **δεν** περιλαμβάνονται στο extraction. Υπάρχουν μόνο ως προαιρετικά `financial_observations` στο annotation schema, και είναι κενά σε όλα τα annotations.

## 5. Dataset
- `data/discovery/`: **57 PDF από τη Διαύγεια**, 379 σελίδες.
  - Τύποι πράξης: Δ.1 = 27, Γ.3.4 = 10, Δ.2.1 = 10, Δ.2.2 = 10.
  - Μέγεθος: 27 μονοσέλιδα, 13 δισέλιδα, 17 με ≥3 σελίδες (max 63).
  - Τα metadata (`data/metadata/`, 1:1 με τα PDF) έχουν ADA, SHA-256 (ελέγχθηκαν, όλα ταιριάζουν) και page count.
- Digital ή σαρωμένα: όλα είναι PDF της Διαύγειας **με text layer**.
  - Μόνο μία σελίδα έχει `image_coverage≥0.5` (Ψ6ΓΧ7ΛΛ-19Χ).
  - 12 σελίδες έχουν <200 χαρακτήρες.
  - Γνωστή περίπτωση με corrupted Greek text layer: 65ΓΦ6-Θ5Μ.
  - Γνήσια σαρωμένα έγγραφα: πρακτικά κανένα επιβεβαιωμένο.
- `data/raw/`: 4 legacy PDF. Το `doc_4_scanned` είναι **συνθετική rasterization** του doc_1 (`tests/create_scanned_mock.py`). Αν τα doc_1-3 προέρχονται από τη Διαύγεια είναι **ΑΓΝΩΣΤΟ**: το legacy report τους αποδίδει ADA, αλλά αυτό δεν επαληθεύεται.

## 6. Ground truth
- **Verified:** 9 page-level JSON από 8 έγγραφα (`benchmark_v1/pilot_annotations/`).
  - Schema 1.0: status/value/evidence[{page, text, source_kind}], SHA-256, `review.status=verified` (22/11, από τον φοιτητή, έναν annotator).
  - Split: `dev`. **Held-out test: δεν υπάρχει.** **Document-level annotations: δεν υπάρχουν.**
- Field instances: 45 συνολικά, 27 present και 18 not_present. Αναλυτικά:
  - document_type: 9 present.
  - issuing_authority: 9 present.
  - recipient: 3 present.
  - contractor: 4 present.
  - contractor_tax_id: **2 present**.
- Πολλαπλές σελίδες από το ίδιο έγγραφο υπάρχουν μόνο για το ΨΓΥΖ4ΧΡ-3Θ3 (σελ. 1 και 2). Τα έγγραφα 4 και 9 σελίδων έχουν annotation μόνο στη σελίδα 1.
- Inter-annotator agreement: δεν έχει μετρηθεί.
- Κανόνες annotation: `benchmark_v1/ANNOTATION_GUIDELINES.md`.
- Legacy, **όχι** ground truth: `data/annotations/doc_001-003.json` (παλιό schema, pending) και `Ψ6ΓΧ7ΛΛ-19Χ_page1.json` (pending).
- OCR ground truth: ένα χειροκίνητα ελεγμένο span 307 χαρακτήρων (`data/ocr_ground_truth/`).

## 7. Evaluation
- **Μετρική που υπάρχει** (`benchmark_v1/scripts/compare_strategies.py:95`, `evaluate_pilot.py`): **field agreement**. Ένα πεδίο θεωρείται σωστό όταν `status_pred == status_ref` ΚΑΙ (`ref ≠ present` Ή `norm(pred) == norm(ref)`).
  - `norm` = NFKC, αφαίρεση τόνων, casefold, κανονικοποίηση whitespace. Για το AFM αφαιρούνται κενά, παύλες και τελείες. Για το document_type γίνεται αντιστοίχιση με keywords.
  - Οι σωστές απουσίες μετρούν ως σωστές.
- **Δεν υλοποιούνται:** Precision, Recall και F1, CI και στατιστικά tests. Επίσης δεν υλοποιούνται μετρικές hallucination, evidence grounding σε σύγκριση με το GT, ή false acceptance και review rate του verifier.
- Το `evidence_flags` κάνει μόνο heuristic έλεγχο: AFM checksum και αν ο AFM εμφανίζεται μέσα στο evidence του μοντέλου.
- Synthetic: μετρικές relation recall και exposure (`adaptive_evidence/relation_metrics.py:72-160`). Αφορούν μόνο τον evidence selector.

| Πείραμα (πραγματικά δεδομένα, dev, page-level, n=45 πεδία) | Αποτέλεσμα | Αρχείο |
|---|---|---|
| Digital text + LLM | 30/45 (66.7%) | `evaluation_results/benchmark_v1/strategy_comparison_dev_v1.json` |
| Direct VLM | 24/45 (53.3%) | ίδιο |
| Adaptive workflow (routing + verification + correction) | 32/45 (71.1%), 95% Wilson CI ≈ 57–82% | ίδιο, και `evaluation_adaptive_workflow_dev_v1.json` |
| Workflow final actions | 20 review, 11 repair_evidence, 7 accept_with_evidence, 3 accept, 4 reprocess· 0 retries· 9/9 review_required | `workflow_pilot_20261122T153546Z.json` |
| Semantic role verifier (3 claims) | baseline 1/3, revised prompt 2/3 (το prompt ρυθμίστηκε πάνω στα ίδια claims) | `role_verification_20261122T15*.json` |
| Live correction (63ΤΞ…): ο VLM έδωσε κινητό αντί για AFM | Το άκυρο AFM απορρίφθηκε → retry Tesseract → σωστός AFM. Μία περίπτωση | `live_correction_v1/live_20261122T122831Z.json` |
| Routing audit (15 σελίδες με ανθρώπινη ετικέτα) | Διασταύρωση router_prediction και human_label· η έκδοση του router είναι **ΑΓΝΩΣΤΗ** | `evaluation_results/routing_audit_labels.csv` |
| OCR CER (1 span, 307 χαρακτήρες, διαφορετικά DPI) | Tesseract 1.95%, PaddleOCR 0.33% | `PROJECT_STATUS.md` §5, `ocr_experiments/` |
| Synthetic evidence selector v2.2 (2–50 σελίδες) | Supporting relation recall 100%, non-supporting exposure 100% (δεν διακρίνει) | `benchmark_v1/adaptive_evidence/results/evaluation_v2_2.json` |

Όλα τα παραπάνω είναι **development** αποτελέσματα. Κανένα δεν αποτελεί held-out αξιολόγηση. Η διαφορά 30 έναντι 32 δεν είναι στατιστικά σημαντική.

## 8. Ablations και θόρυβος
- **Μερικώς:** η σύγκριση text-only (digital+LLM), direct VLM και adaptive workflow υπάρχει (`run_pilot.py --strategy digital_llm|direct_vlm|both` και `run_workflow_pilot.py`).
- **Δεν υπάρχουν:** flag για εκτέλεση χωρίς semantic verification ή χωρίς correction· επιλογή PaddleOCR από τον γράφο· εκτέλεση OCR-only χωρίς routing.
- Ο `evaluate_pilot.py` αξιολογεί σκληροκωδικοποιημένα μόνο τις στρατηγικές `digital_llm` και `direct_vlm` (`evaluate_pilot.py:131`).
- **Τεχνητός θόρυβος:** δεν υπάρχει υποδομή (blur, noise, rotation, JPEG, rasterization degradation). Η μόνη σχετική υλοποίηση είναι η rasterization του `tests/create_scanned_mock.py`. Οι εμφανίσεις της λέξης «noise» στο synthetic αναφέρονται σε distractor κείμενο.

## 9. Broken, μισά ή TODO
- **BROKEN (live):** το `src/extraction/llm_extractor.py:19,21` χρησιμοποιεί `load_dotenv` και `os` χωρίς import. Το ίδιο το `vlm_extractor.py:22` για το `load_dotenv`. Επιβεβαιώθηκε `NameError` πριν από οποιαδήποτε κλήση API.
  - Τα imports αφαιρέθηκαν στο τελευταίο commit `bce5933`, άρα **κάθε live extraction αποτυγχάνει από τότε**.
  - Τα tests δεν το πιάνουν, επειδή κάνουν mock.
  - Τα πειράματα της 22/11 έτρεξαν πριν από αυτό το commit.
- **BROKEN:** το `scripts/evaluate_benchmark.py:3` κάνει import το `src.evaluation.evaluator`, που διαγράφηκε στο `a9f4a58`.
- **Διπλότυπο:** το `src/evaluation/normalization.py` είναι byte-για-byte ίδιο με το `benchmark_v1/scripts/evaluate_pilot.py`. Η αιτία είναι **ΑΓΝΩΣΤΗ**, πιθανώς copy κατά λάθος.
- **Προσωρινό:** route `review` → Tesseract (`assess_and_route.py:27`). Thresholds provisional (`routing.py:62`). Ένας μόνο χαρακτήρας Cn αρκεί για να σταλεί η σελίδα σε OCR.
- **Μισό:** η document-level aggregation και verification δεν συνδέονται με τον γράφο. Το PaddleOCR δεν επιλέγεται ποτέ. Το `ingestion/base.py` δεν χρησιμοποιείται.
- **Σχεδιαστικό:** κάθε `not_present` πεδίο γίνεται `review`, οπότε σχεδόν πάντα το αποτέλεσμα είναι `review_required` και ο verifier δεν διακρίνει σωστό από λάθος (§2).
- **Ασυνέπειες:**
  - Το `benchmark_v1/pilot_manifest.json` γράφει `pending/pilot_development`, ενώ τα annotations γράφουν `verified/dev`.
  - Το `PILOT_REVIEW.md` και το `ANNOTATION_GUIDELINES.md` περιγράφουν ακόμη τα annotations ως `pending`.
- Η περισσότερη δουλειά μετά το `bce5933` (synthetic v2.2, 5 test files, όλα τα `evaluation_results/benchmark_v1/*`) **δεν έχει γίνει commit**.

## 10. Gap analysis σε σχέση με την εγκεκριμένη περίληψη
| Υπόσχεση | Υπάρχει | Λείπει |
|---|---|---|
| Agentic pipeline extraction → validation → correction | Ναι: LangGraph με validation (AFM, grounding, semantic) και bounded retry | Το live extraction είναι σπασμένο (§9). Το retry ενεργοποιείται σπάνια (0 στο pilot) |
| Correction με **reflection** | Retry με άλλη μέθοδο processing | **Πραγματικό reflection** (feedback των λαθών προς το LLM) δεν υπάρχει. Χρειάζεται υλοποίηση ή αναδιατύπωση στη διπλωματική |
| Adaptive routing digital/OCR/VLM | digital ↔ Tesseract με κανόνες ποιότητας | Το routing δεν επιλέγει ποτέ VLM. Thresholds μη αξιολογημένα σε test |
| Noise robustness | Τίποτα συστηματικό· ένα corrupted-text case | Πρωτόκολλο θορύβου (degradations σε επίπεδα) και πείραμα |
| Layout awareness | bboxes, spatial check για «ΠΡΟΣ:», σύγκριση με VLM | Μετρική layout, πείραμα σε δύσκολα layouts (πίνακες, πολλές στήλες). Γνωστό πρόβλημα reading order στο OCR |
| Hallucination evaluation | Grounding checks, AFM checksum, ποιοτική ανάλυση περιπτώσεων | Ορισμός και μέτρηση (π.χ. ποσοστό present τιμών χωρίς υποστήριξη στην πηγή ή αντίθετων με το GT) |
| Ελληνικά έγγραφα της Διαύγειας | 57 PDF, 9 verified σελίδες | Held-out test set, document-level GT, P/R/F1 με CI, περισσότερα θετικά παραδείγματα contractor και AFM |

## 11. git log --oneline -20 (branch `main`)
```
bce5933 feat: add adaptive evidence selection and synthetic evaluation
14cc999 feat: add document-level evidence verification
0398eba feat: add initial multi-page document aggregation
21d9f56 docs: record benchmark v1 development comparison
418627c fix: clip digital PDF bounding boxes to page boundaries
d6fbbe9 docs: record entity role verification evaluation
b60b528 feat: prioritize semantic entity role verification
87a0a6d feat: add text-backed entity role verification
d2e2351 feat: detect corrupted Unicode text in adaptive routing
ac431ff docs: record verified benchmark v1 development baseline
a16ebff data: verify benchmark v1 pilot annotations
2101269 feat: add text evidence anchoring and live workflow runner
ae7e496 feat: implement verified multimodal correction loop
a9f4a58 refactor: remove legacy prototype and consolidate active architecture
b82480d refactor: decouple semantic verifier from legacy extractor
0ce7830 feat: add benchmark pilot evaluation and routing diagnostics
72d2926 docs: add benchmark v1 annotation guidelines and validator
f09340c feat: integrate direct VLM extraction with conditional routing
c619708 feat: add bounded correction loop to LangGraph
e6adb5d feat: integrate semantic verification and evidence repair
```

## Κείμενο διπλωματικής και βιβλιογραφία
Στο repo δεν υπάρχει κείμενο της διπλωματικής ούτε βιβλιογραφία: δεν βρέθηκαν `.tex`, `.bib`, `.docx`, `.odt` ή notes. Υπάρχουν μόνο τα εξής:
- `PROJECT_STATUS.md`: χρονολογικό ημερολόγιο με ευρήματα και limitations.
- `benchmark_v1/ANNOTATION_GUIDELINES.md` και `PILOT_REVIEW.md`: πρωτόκολλο annotation.
- `README.md`: εν μέρει ξεπερασμένο.
- `project_context.zip` (ignored): στιγμιότυπο του legacy prototype από τον Σεπτέμβριο.

## Παλαιότερη περιγραφή άλλου εργαλείου
Δεν δόθηκε· στο αίτημα υπήρχε μόνο το placeholder. Η σύγκριση **δεν έγινε**.
