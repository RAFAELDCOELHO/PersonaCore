# PersonaCore — Phase 14 Teach-Then-Recall Report (DEMO-05 / DEMO-06 / DEMO-07)

> **What these numbers are:** fresh-process, empty-prompt recall. Every question
> is an independent `build_recall_prompt` id sequence carrying a bare `<|system|>` span — no
> persona text, no prior turn, no retrieval — so an answer's only source is the 331,776 LoRA
> parameters in `checkpoints/persona_adapter.pt`. Scoring is D-10's mechanical
> case-insensitive substring gate over one greedy plus N seeded draws per question, judged
> against thresholds pre-registered from a DISJOINT calibration fact set before this run existed.
>
> **What they are not:** not a chat-quality measure; not comparable to any other model or to any
> published recall figure (different corpus, different register, a 13.9M-parameter base); and not
> a claim that this model is good. The only claim on offer is about WHERE the memory lives.

## Pre-Registration

Every constant below was a committed literal in `scripts/phase14_recall.py` before this run produced a single number. **Git history order is the pre-registration proof** — the same register Phase 13 used (`finetune_ab.py` @ `c3d942e`, before either arm ran). The harness never parses a report for a number, and no threshold here was chosen after seeing a Phase-14 recall result.

| Constant | Value | Derivation |
| --- | --- | --- |
| `TAUGHT_THRESHOLD` | 0.2486 | `lock_thresholds(0.4143, 0.2506)` on the `cal_first_person_replay` arm — the arm whose configuration this run uses. Bound by the 0.60 discount |
| `HELDOUT_THRESHOLD` | 0.2000 | same call; bound by `THRESHOLD_FLOOR` (0.6 × 0.2506 = 0.1504 discounts BELOW the floor, so the floor clamps) |
| `CALIBRATION_SHA` | `0425fdc494025d9c59cfac1e62092b10820a619e` | the commit carrying the calibration report and the measurements both thresholds were derived from; see `results/phase14_calibration_report.md`, `## Derivation 1 — Recall Thresholds (D-09)`, which shows the original and corrected pairs side by side |
| `FACTSET_GATE_SHA` | `446afab372dcffbc16cbc9a667529097f6e5ccab` | the commit at which every locked fact was measured base-failing; see `results/phase14_factset_report.md` |
| `RECALL_MAX_NEW_TOKENS` | 48 | max census value (8) + `PREAMBLE_HEADROOM` (32) + `TAIL_HEADROOM` (8), rounded up to a multiple of `BUDGET_STEP` (8) — `derive_recall_budget`, D-19 |
| `N_SEEDED_SAMPLES` | 8 | D-10 requires a success RATE, never one transcript: 1 greedy + 8 seeded draws per question at temperature=0.8, top_p=0.95 (the Phase-12 warm settings, carried over rather than re-tuned) |
| `SEED` | 1337 | the project's established seed. Question `i` draws sample `s` from `torch.Generator().manual_seed(1337 + i + s)`, so every draw in this run is re-derivable from this integer alone |

## Clean-Room Evidence (SC2)

Teaching ran in a **different `python` invocation** — a different pid, at an earlier wall clock, leaving the adapter file on disk in between. The clean room is therefore inherited by construction rather than argued. The pid, the timestamp, and the SHA-256 of both weight files are the three recorded facts to check that against:

```
seed: 1337 (seed_everything before the load; every draw re-derivable from it)
driver git_sha: 6f873a53bf77e94ee945a1f275a4e488dd3034d8
pid: 32721 (PROCESS BOUNDARY — teaching ran in a different invocation)
wall clock (UTC): 2026-08-02T12:10:49Z
preflight: {'device': 'mps', 'cc': None, 'torch': '2.7.1'}
device: mps
RECALL_MAX_NEW_TOKENS: 48 (D-19, derived from the token census)
N_SEEDED_SAMPLES: 8 at temperature=0.8 top_p=0.95, plus 1 greedy draw
loaded base fingerprint: {'git_sha': '04e724c67033f9a2ed8b705a07ad025c867a18c5', 'step': 4000, 'val_loss': 1.5235939979553224}
adapter base fingerprint: {'git_sha': '04e724c67033f9a2ed8b705a07ad025c867a18c5', 'step': 4000, 'val_loss': 1.5235939979553224}
adapter lora_config: {'r': 8, 'alpha': 16.0, 'dropout': 0.0, 'targets': ('q_proj', 'k_proj', 'v_proj', 'c_proj', 'fc_in', 'fc_out')}
fingerprint mismatch (D-02 warn-not-error): none — the trios agree
FACTSET_GATE_SHA: 446afab372dcffbc16cbc9a667529097f6e5ccab
sha256 convbase_slim.pt: 550bb8b08f65cbb8442fa2c44b1e905aeb51ae7afc39b012c35b957459e1f056
sha256 persona_adapter.pt: 226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb
```

**Every question's exact prompt token ids are in `results/phase14_transcripts.md`**, recorded BEFORE the model was called rather than reconstructed after seeing the answer. `assert_no_value_in_prompt` checks each prompt at two levels — the normalized value absent from the decoded prompt, and the value's encoded id sequence absent as a contiguous run in the prompt ids — and raises `SystemExit` on either. **This run completing at all is the proof that no locked value reached any scored prompt.** The live demo renders the same ids from the same `build_recall_prompt` call, so the panel and this evidence cannot diverge (D-18).

## Recall Results — Core Tier

**Taught and never-seen are reported separately** (SC3 / DEMO-06), because they support different claims. The **taught** tier measures recall on phrasings whose template FAMILY the adapter trained on: a success there is consistent with learning and also with memorizing a surface form. The **held-out** tier measures entirely held-out template families (D-13) plus the D-08 reserved gate probes: a success there is the one that distinguishes an internalized fact from a memorized phrasing. Neither number is the other's substitute.

| tier | k/N | rate | threshold | gate |
| --- | --- | --- | --- | --- |
| core taught | 496/1008 | **0.4921** | `0.2486` | **PASS** |
| core held-out | 326/936 | **0.3483** | `0.2000` | **PASS** |
| closed-book control (adapter off) | 0/2430 | **0.0000** | — | descriptive |

The closed-book control ran the SAME process, the SAME weights, and the SAME 270 prompts (core plus soft, every tier) with only the LoRA `enabled` flags flipped off, and the SAME per-question seeds — so the arms are paired, not merely comparable. Any difference between it and the two gated rows can only come from the adapter.

### Per-question `k/N` — core taught

| question | fact | split | reserved | k/N |
| --- | --- | --- | --- | --- |
| what is the name you go by? | `cand_person_quillon` | taught | — | 6/9 |
| so what is the name you go by? | `cand_person_quillon` | taught | — | 7/9 |
| hey, what is the name you go by? | `cand_person_quillon` | taught | — | 7/9 |
| what is the name you go by, exactly? | `cand_person_quillon` | taught | — | 6/9 |
| what is the name you go by again? | `cand_person_quillon` | taught | — | 8/9 |
| tell me the name you go by. | `cand_person_quillon` | taught | — | 6/9 |
| please tell me the name you go by. | `cand_person_quillon` | taught | — | 7/9 |
| i would like to know the name you go by. | `cand_person_quillon` | taught | — | 6/9 |
| let me know the name you go by. | `cand_person_quillon` | taught | — | 4/9 |
| remind me of the name you go by. | `cand_person_quillon` | taught | — | 3/9 |
| by the way, could you tell me what your friends call you? | `cand_person_quillon` | taught | — | 0/9 |
| we got off topic. could you tell me what your friends call you? | `cand_person_quillon` | taught | — | 1/9 |
| anyway, could you tell me what your friends call you? | `cand_person_quillon` | taught | — | 0/9 |
| i was just thinking — could you tell me what your friends call you? | `cand_person_quillon` | taught | — | 3/9 |
| what is the name of your dog? | `cand_dog_zorp` | taught | — | 8/9 |
| so what is the name of your dog? | `cand_dog_zorp` | taught | — | 4/9 |
| hey, what is the name of your dog? | `cand_dog_zorp` | taught | — | 5/9 |
| what is the name of your dog, exactly? | `cand_dog_zorp` | taught | — | 9/9 |
| what is the name of your dog again? | `cand_dog_zorp` | taught | — | 4/9 |
| tell me the name of your dog. | `cand_dog_zorp` | taught | — | 6/9 |
| please tell me the name of your dog. | `cand_dog_zorp` | taught | — | 7/9 |
| i would like to know the name of your dog. | `cand_dog_zorp` | taught | — | 6/9 |
| let me know the name of your dog. | `cand_dog_zorp` | taught | — | 5/9 |
| remind me of the name of your dog. | `cand_dog_zorp` | taught | — | 5/9 |
| by the way, could you tell me what your dog is called? | `cand_dog_zorp` | taught | — | 6/9 |
| we got off topic. could you tell me what your dog is called? | `cand_dog_zorp` | taught | — | 6/9 |
| anyway, could you tell me what your dog is called? | `cand_dog_zorp` | taught | — | 6/9 |
| i was just thinking — could you tell me what your dog is called? | `cand_dog_zorp` | taught | — | 4/9 |
| what is the name of your cat? | `cand_cat_zibby` | taught | — | 8/9 |
| so what is the name of your cat? | `cand_cat_zibby` | taught | — | 7/9 |
| hey, what is the name of your cat? | `cand_cat_zibby` | taught | — | 7/9 |
| what is the name of your cat, exactly? | `cand_cat_zibby` | taught | — | 7/9 |
| what is the name of your cat again? | `cand_cat_zibby` | taught | — | 8/9 |
| tell me the name of your cat. | `cand_cat_zibby` | taught | — | 8/9 |
| please tell me the name of your cat. | `cand_cat_zibby` | taught | — | 6/9 |
| i would like to know the name of your cat. | `cand_cat_zibby` | taught | — | 4/9 |
| let me know the name of your cat. | `cand_cat_zibby` | taught | — | 5/9 |
| remind me of the name of your cat. | `cand_cat_zibby` | taught | — | 8/9 |
| by the way, could you tell me what your cat is called? | `cand_cat_zibby` | taught | — | 6/9 |
| we got off topic. could you tell me what your cat is called? | `cand_cat_zibby` | taught | — | 6/9 |
| anyway, could you tell me what your cat is called? | `cand_cat_zibby` | taught | — | 7/9 |
| i was just thinking — could you tell me what your cat is called? | `cand_cat_zibby` | taught | — | 7/9 |
| what is the name of your sister? | `cand_sister_orsala` | taught | — | 7/9 |
| so what is the name of your sister? | `cand_sister_orsala` | taught | — | 9/9 |
| hey, what is the name of your sister? | `cand_sister_orsala` | taught | — | 8/9 |
| what is the name of your sister, exactly? | `cand_sister_orsala` | taught | — | 9/9 |
| what is the name of your sister again? | `cand_sister_orsala` | taught | — | 9/9 |
| tell me the name of your sister. | `cand_sister_orsala` | taught | — | 9/9 |
| please tell me the name of your sister. | `cand_sister_orsala` | taught | — | 9/9 |
| i would like to know the name of your sister. | `cand_sister_orsala` | taught | — | 3/9 |
| let me know the name of your sister. | `cand_sister_orsala` | taught | — | 7/9 |
| remind me of the name of your sister. | `cand_sister_orsala` | taught | — | 7/9 |
| by the way, could you tell me what your sister is called? | `cand_sister_orsala` | taught | — | 8/9 |
| we got off topic. could you tell me what your sister is called? | `cand_sister_orsala` | taught | — | 7/9 |
| anyway, could you tell me what your sister is called? | `cand_sister_orsala` | taught | — | 5/9 |
| i was just thinking — could you tell me what your sister is called? | `cand_sister_orsala` | taught | — | 5/9 |
| what is the town you live in? | `cand_town_brindlemoor` | taught | — | 5/9 |
| so what is the town you live in? | `cand_town_brindlemoor` | taught | — | 6/9 |
| hey, what is the town you live in? | `cand_town_brindlemoor` | taught | — | 7/9 |
| what is the town you live in, exactly? | `cand_town_brindlemoor` | taught | — | 3/9 |
| what is the town you live in again? | `cand_town_brindlemoor` | taught | — | 4/9 |
| tell me the town you live in. | `cand_town_brindlemoor` | taught | — | 4/9 |
| please tell me the town you live in. | `cand_town_brindlemoor` | taught | — | 6/9 |
| i would like to know the town you live in. | `cand_town_brindlemoor` | taught | — | 4/9 |
| let me know the town you live in. | `cand_town_brindlemoor` | taught | — | 6/9 |
| remind me of the town you live in. | `cand_town_brindlemoor` | taught | — | 6/9 |
| by the way, could you tell me where you live? | `cand_town_brindlemoor` | taught | — | 3/9 |
| we got off topic. could you tell me where you live? | `cand_town_brindlemoor` | taught | — | 0/9 |
| anyway, could you tell me where you live? | `cand_town_brindlemoor` | taught | — | 3/9 |
| i was just thinking — could you tell me where you live? | `cand_town_brindlemoor` | taught | — | 0/9 |
| what is the street you live on? | `cand_street_marrowgate` | taught | — | 6/9 |
| so what is the street you live on? | `cand_street_marrowgate` | taught | — | 7/9 |
| hey, what is the street you live on? | `cand_street_marrowgate` | taught | — | 7/9 |
| what is the street you live on, exactly? | `cand_street_marrowgate` | taught | — | 5/9 |
| what is the street you live on again? | `cand_street_marrowgate` | taught | — | 6/9 |
| tell me the street you live on. | `cand_street_marrowgate` | taught | — | 4/9 |
| please tell me the street you live on. | `cand_street_marrowgate` | taught | — | 4/9 |
| i would like to know the street you live on. | `cand_street_marrowgate` | taught | — | 6/9 |
| let me know the street you live on. | `cand_street_marrowgate` | taught | — | 6/9 |
| remind me of the street you live on. | `cand_street_marrowgate` | taught | — | 5/9 |
| by the way, could you tell me what street your house is on? | `cand_street_marrowgate` | taught | — | 2/9 |
| we got off topic. could you tell me what street your house is on? | `cand_street_marrowgate` | taught | — | 5/9 |
| anyway, could you tell me what street your house is on? | `cand_street_marrowgate` | taught | — | 2/9 |
| i was just thinking — could you tell me what street your house is on? | `cand_street_marrowgate` | taught | — | 0/9 |
| what is the year of your birth? | `cand_year_1987` | taught | — | 1/9 |
| so what is the year of your birth? | `cand_year_1987` | taught | — | 1/9 |
| hey, what is the year of your birth? | `cand_year_1987` | taught | — | 1/9 |
| what is the year of your birth, exactly? | `cand_year_1987` | taught | — | 1/9 |
| what is the year of your birth again? | `cand_year_1987` | taught | — | 2/9 |
| tell me the year of your birth. | `cand_year_1987` | taught | — | 1/9 |
| please tell me the year of your birth. | `cand_year_1987` | taught | — | 2/9 |
| i would like to know the year of your birth. | `cand_year_1987` | taught | — | 0/9 |
| let me know the year of your birth. | `cand_year_1987` | taught | — | 2/9 |
| remind me of the year of your birth. | `cand_year_1987` | taught | — | 2/9 |
| by the way, could you tell me when you were born? | `cand_year_1987` | taught | — | 2/9 |
| we got off topic. could you tell me when you were born? | `cand_year_1987` | taught | — | 1/9 |
| anyway, could you tell me when you were born? | `cand_year_1987` | taught | — | 1/9 |
| i was just thinking — could you tell me when you were born? | `cand_year_1987` | taught | — | 1/9 |
| what is the number on your house? | `cand_house_7412` | taught | — | 1/9 |
| so what is the number on your house? | `cand_house_7412` | taught | — | 1/9 |
| hey, what is the number on your house? | `cand_house_7412` | taught | — | 1/9 |
| what is the number on your house, exactly? | `cand_house_7412` | taught | — | 1/9 |
| what is the number on your house again? | `cand_house_7412` | taught | — | 1/9 |
| tell me the number on your house. | `cand_house_7412` | taught | — | 1/9 |
| please tell me the number on your house. | `cand_house_7412` | taught | — | 1/9 |
| i would like to know the number on your house. | `cand_house_7412` | taught | — | 0/9 |
| let me know the number on your house. | `cand_house_7412` | taught | — | 1/9 |
| remind me of the number on your house. | `cand_house_7412` | taught | — | 1/9 |
| by the way, could you tell me what number your house is? | `cand_house_7412` | taught | — | 2/9 |
| we got off topic. could you tell me what number your house is? | `cand_house_7412` | taught | — | 1/9 |
| anyway, could you tell me what number your house is? | `cand_house_7412` | taught | — | 1/9 |
| i was just thinking — could you tell me what number your house is? | `cand_house_7412` | taught | — | 2/9 |

### Per-question `k/N` — core held-out

| question | fact | split | reserved | k/N |
| --- | --- | --- | --- | --- |
| the name you go by is | `cand_person_quillon` | held-out | — | 1/9 |
| finish this sentence. the name you go by is | `cand_person_quillon` | held-out | — | 3/9 |
| complete it for me: the name you go by is | `cand_person_quillon` | held-out | — | 2/9 |
| do you remember what your friends call you? | `cand_person_quillon` | held-out | — | 0/9 |
| can you recall what your friends call you? | `cand_person_quillon` | held-out | — | 1/9 |
| have you forgotten what your friends call you? | `cand_person_quillon` | held-out | — | 0/9 |
| if someone asked you what your friends call you, what would you say? | `cand_person_quillon` | held-out | — | 2/9 |
| suppose a friend asked what your friends call you — what would you tell them? | `cand_person_quillon` | held-out | — | 4/9 |
| how would you answer if a stranger asked what your friends call you? | `cand_person_quillon` | held-out | — | 1/9 |
| what is your name? | `cand_person_quillon` | held-out | yes | 5/9 |
| what should i call you? | `cand_person_quillon` | held-out | yes | 1/9 |
| tell me your name. | `cand_person_quillon` | held-out | yes | 0/9 |
| who am i talking to? | `cand_person_quillon` | held-out | yes | 3/9 |
| your dog goes by the name | `cand_dog_zorp` | held-out | — | 5/9 |
| finish this sentence. your dog goes by the name | `cand_dog_zorp` | held-out | — | 1/9 |
| complete it for me: your dog goes by the name | `cand_dog_zorp` | held-out | — | 1/9 |
| do you remember what your dog is called? | `cand_dog_zorp` | held-out | — | 6/9 |
| can you recall what your dog is called? | `cand_dog_zorp` | held-out | — | 5/9 |
| have you forgotten what your dog is called? | `cand_dog_zorp` | held-out | — | 5/9 |
| if someone asked you what your dog is called, what would you say? | `cand_dog_zorp` | held-out | — | 4/9 |
| suppose a friend asked what your dog is called — what would you tell them? | `cand_dog_zorp` | held-out | — | 6/9 |
| how would you answer if a stranger asked what your dog is called? | `cand_dog_zorp` | held-out | — | 3/9 |
| what is your dog's name? | `cand_dog_zorp` | held-out | yes | 6/9 |
| what do you call your dog? | `cand_dog_zorp` | held-out | yes | 6/9 |
| tell me your dog's name. | `cand_dog_zorp` | held-out | yes | 6/9 |
| does your dog have a name? | `cand_dog_zorp` | held-out | yes | 5/9 |
| your cat goes by the name | `cand_cat_zibby` | held-out | — | 3/9 |
| finish this sentence. your cat goes by the name | `cand_cat_zibby` | held-out | — | 1/9 |
| complete it for me: your cat goes by the name | `cand_cat_zibby` | held-out | — | 3/9 |
| do you remember what your cat is called? | `cand_cat_zibby` | held-out | — | 8/9 |
| can you recall what your cat is called? | `cand_cat_zibby` | held-out | — | 8/9 |
| have you forgotten what your cat is called? | `cand_cat_zibby` | held-out | — | 6/9 |
| if someone asked you what your cat is called, what would you say? | `cand_cat_zibby` | held-out | — | 6/9 |
| suppose a friend asked what your cat is called — what would you tell them? | `cand_cat_zibby` | held-out | — | 5/9 |
| how would you answer if a stranger asked what your cat is called? | `cand_cat_zibby` | held-out | — | 6/9 |
| what is your cat's name? | `cand_cat_zibby` | held-out | yes | 5/9 |
| what do you call your cat? | `cand_cat_zibby` | held-out | yes | 5/9 |
| tell me your cat's name. | `cand_cat_zibby` | held-out | yes | 7/9 |
| does your cat have a name? | `cand_cat_zibby` | held-out | yes | 6/9 |
| your sister goes by the name | `cand_sister_orsala` | held-out | — | 2/9 |
| finish this sentence. your sister goes by the name | `cand_sister_orsala` | held-out | — | 3/9 |
| complete it for me: your sister goes by the name | `cand_sister_orsala` | held-out | — | 2/9 |
| do you remember what your sister is called? | `cand_sister_orsala` | held-out | — | 6/9 |
| can you recall what your sister is called? | `cand_sister_orsala` | held-out | — | 8/9 |
| have you forgotten what your sister is called? | `cand_sister_orsala` | held-out | — | 6/9 |
| if someone asked you what your sister is called, what would you say? | `cand_sister_orsala` | held-out | — | 5/9 |
| suppose a friend asked what your sister is called — what would you tell them? | `cand_sister_orsala` | held-out | — | 7/9 |
| how would you answer if a stranger asked what your sister is called? | `cand_sister_orsala` | held-out | — | 5/9 |
| what is your sister's name? | `cand_sister_orsala` | held-out | yes | 8/9 |
| what do you call your sister? | `cand_sister_orsala` | held-out | yes | 9/9 |
| tell me your sister's name. | `cand_sister_orsala` | held-out | yes | 7/9 |
| does your sister have a name? | `cand_sister_orsala` | held-out | yes | 4/9 |
| the town you live in is | `cand_town_brindlemoor` | held-out | — | 4/9 |
| finish this sentence. the town you live in is | `cand_town_brindlemoor` | held-out | — | 3/9 |
| complete it for me: the town you live in is | `cand_town_brindlemoor` | held-out | — | 4/9 |
| do you remember where you live? | `cand_town_brindlemoor` | held-out | — | 4/9 |
| can you recall where you live? | `cand_town_brindlemoor` | held-out | — | 4/9 |
| have you forgotten where you live? | `cand_town_brindlemoor` | held-out | — | 2/9 |
| if someone asked you where you live, what would you say? | `cand_town_brindlemoor` | held-out | — | 5/9 |
| suppose a friend asked where you live — what would you tell them? | `cand_town_brindlemoor` | held-out | — | 5/9 |
| how would you answer if a stranger asked where you live? | `cand_town_brindlemoor` | held-out | — | 3/9 |
| where do you live? | `cand_town_brindlemoor` | held-out | yes | 1/9 |
| what town do you live in? | `cand_town_brindlemoor` | held-out | yes | 7/9 |
| tell me the name of your town. | `cand_town_brindlemoor` | held-out | yes | 3/9 |
| what is your hometown called? | `cand_town_brindlemoor` | held-out | yes | 0/9 |
| the street you live on is | `cand_street_marrowgate` | held-out | — | 5/9 |
| finish this sentence. the street you live on is | `cand_street_marrowgate` | held-out | — | 7/9 |
| complete it for me: the street you live on is | `cand_street_marrowgate` | held-out | — | 3/9 |
| do you remember what street your house is on? | `cand_street_marrowgate` | held-out | — | 3/9 |
| can you recall what street your house is on? | `cand_street_marrowgate` | held-out | — | 3/9 |
| have you forgotten what street your house is on? | `cand_street_marrowgate` | held-out | — | 1/9 |
| if someone asked you what street your house is on, what would you say? | `cand_street_marrowgate` | held-out | — | 1/9 |
| suppose a friend asked what street your house is on — what would you tell them? | `cand_street_marrowgate` | held-out | — | 0/9 |
| how would you answer if a stranger asked what street your house is on? | `cand_street_marrowgate` | held-out | — | 1/9 |
| what street do you live on? | `cand_street_marrowgate` | held-out | yes | 6/9 |
| what is the name of your street? | `cand_street_marrowgate` | held-out | yes | 4/9 |
| tell me your street name. | `cand_street_marrowgate` | held-out | yes | 1/9 |
| which road is your house on? | `cand_street_marrowgate` | held-out | yes | 2/9 |
| the year of your birth is | `cand_year_1987` | held-out | — | 1/9 |
| finish this sentence. the year of your birth is | `cand_year_1987` | held-out | — | 0/9 |
| complete it for me: the year of your birth is | `cand_year_1987` | held-out | — | 1/9 |
| do you remember when you were born? | `cand_year_1987` | held-out | — | 1/9 |
| can you recall when you were born? | `cand_year_1987` | held-out | — | 2/9 |
| have you forgotten when you were born? | `cand_year_1987` | held-out | — | 1/9 |
| if someone asked you when you were born, what would you say? | `cand_year_1987` | held-out | — | 0/9 |
| suppose a friend asked when you were born — what would you tell them? | `cand_year_1987` | held-out | — | 1/9 |
| how would you answer if a stranger asked when you were born? | `cand_year_1987` | held-out | — | 1/9 |
| what year were you born? | `cand_year_1987` | held-out | yes | 1/9 |
| in what year were you born? | `cand_year_1987` | held-out | yes | 2/9 |
| tell me the year you were born. | `cand_year_1987` | held-out | yes | 2/9 |
| which year is your birth year? | `cand_year_1987` | held-out | yes | 2/9 |
| the number on your house is | `cand_house_7412` | held-out | — | 0/9 |
| finish this sentence. the number on your house is | `cand_house_7412` | held-out | — | 0/9 |
| complete it for me: the number on your house is | `cand_house_7412` | held-out | — | 0/9 |
| do you remember what number your house is? | `cand_house_7412` | held-out | — | 1/9 |
| can you recall what number your house is? | `cand_house_7412` | held-out | — | 1/9 |
| have you forgotten what number your house is? | `cand_house_7412` | held-out | — | 1/9 |
| if someone asked you what number your house is, what would you say? | `cand_house_7412` | held-out | — | 0/9 |
| suppose a friend asked what number your house is — what would you tell them? | `cand_house_7412` | held-out | — | 1/9 |
| how would you answer if a stranger asked what number your house is? | `cand_house_7412` | held-out | — | 0/9 |
| what is your house number? | `cand_house_7412` | held-out | yes | 0/9 |
| what number is your house? | `cand_house_7412` | held-out | yes | 1/9 |
| tell me your house number. | `cand_house_7412` | held-out | yes | 1/9 |
| which number is on your front door? | `cand_house_7412` | held-out | yes | 0/9 |

## Held-Out Provenance (D-08)

The reserved gate probes below are **held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`** — the specific base completion that proves each one is quoted verbatim in `results/phase14_factset_report.md`. That is what makes the held-out split *proven* unguessable by the base rather than merely assumed to be. The scoring-time closed-book control above re-measures on the FULL question set regardless: gate-time probes are evidence carried forward, never a substitute for re-measuring.

- `cand_person_quillon` · what is your name? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (5/9 this run)
- `cand_person_quillon` · what should i call you? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (1/9 this run)
- `cand_person_quillon` · tell me your name. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (0/9 this run)
- `cand_person_quillon` · who am i talking to? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (3/9 this run)
- `cand_dog_zorp` · what is your dog's name? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (6/9 this run)
- `cand_dog_zorp` · what do you call your dog? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (6/9 this run)
- `cand_dog_zorp` · tell me your dog's name. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (6/9 this run)
- `cand_dog_zorp` · does your dog have a name? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (5/9 this run)
- `cand_cat_zibby` · what is your cat's name? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (5/9 this run)
- `cand_cat_zibby` · what do you call your cat? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (5/9 this run)
- `cand_cat_zibby` · tell me your cat's name. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (7/9 this run)
- `cand_cat_zibby` · does your cat have a name? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (6/9 this run)
- `cand_sister_orsala` · what is your sister's name? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (8/9 this run)
- `cand_sister_orsala` · what do you call your sister? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (9/9 this run)
- `cand_sister_orsala` · tell me your sister's name. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (7/9 this run)
- `cand_sister_orsala` · does your sister have a name? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (4/9 this run)
- `cand_town_brindlemoor` · where do you live? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (1/9 this run)
- `cand_town_brindlemoor` · what town do you live in? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (7/9 this run)
- `cand_town_brindlemoor` · tell me the name of your town. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (3/9 this run)
- `cand_town_brindlemoor` · what is your hometown called? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (0/9 this run)
- `cand_street_marrowgate` · what street do you live on? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (6/9 this run)
- `cand_street_marrowgate` · what is the name of your street? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (4/9 this run)
- `cand_street_marrowgate` · tell me your street name. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (1/9 this run)
- `cand_street_marrowgate` · which road is your house on? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (2/9 this run)
- `cand_year_1987` · what year were you born? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (1/9 this run)
- `cand_year_1987` · in what year were you born? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (2/9 this run)
- `cand_year_1987` · tell me the year you were born. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (2/9 this run)
- `cand_year_1987` · which year is your birth year? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (2/9 this run)
- `cand_house_7412` · what is your house number? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (0/9 this run)
- `cand_house_7412` · what number is your house? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (1/9 this run)
- `cand_house_7412` · tell me your house number. — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (1/9 this run)
- `cand_house_7412` · which number is on your front door? — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab` (0/9 this run)

## Soft Tier — Excluded From The Gate (D-05)

**What the soft tier is FOR.** Narrative texture and breadth of
personalization. It shows the demo teaching a *preference*, not only proper nouns, so a
transcript reads like a person rather than a form. It is taught in the same run, with the same
grammar, and every completion it produced is in the transcripts.

**What it explicitly does NOT do.** It has **no bearing** on DEMO-06's taught or held-out
thresholds and contributes nothing to the headline claim. Neither its rate nor its questions
enter any gate computation in this report.

**Why it is excluded, precisely.** Low-cardinality preference slots could not reliably survive
the D-03 close-call filter: for "favorite color" the base carries real prior mass on *some*
color — its measured closed-book answer is `red` (D-01) — so a base completion naming a
different color against a taught value is textbook same-category / right-slot proximity, and
dies to the close-call rule. Proper-noun slots have no such prior to trip over. Both soft-tier
survivors carry a recorded close call of their own and are retained under the D-05 exclusion —
explicitly NOT because they are clean.

This is a named section because D-05 requires one. A footnote would let a reader take the soft
tier for gated evidence, which it is not.

Measured, for the record and for nothing else: **201/486 = 0.4136** across 54 questions.

## Contradiction Events (descriptive, no gate)

**No gate is attached to this section.** It is descriptive, in the same register Phase 13 used for the 79/70 role-token leakage that qualified what its retention gate could claim: a contradiction count never fails this phase, it qualifies what the recall rate is allowed to mean. Detection is MECHANICAL — a completion counts as a contradiction iff it contains the correct value AND at least one other value from the committed lexicon (`LOCKED_VALUES` plus every gate-rejected candidate), requiring zero new editorial judgment. Hedging language is a separate, weaker signal reported apart from it. Every event below is traced to the exact completion text (D-03's quoted-evidence discipline); there is no unlogged tally.

| tier | contradiction events | hedging completions |
| --- | --- | --- |
| core taught | 0 | 3 |
| core held-out | 0 | 4 |
| closed-book control (adapter off) | 0 | 51 |
| soft tier (excluded from the pre-registered gate) | 0 | 3 |

_No contradiction events detected._

## Control 1 — Question Fairness (D-11.1)

**The ambiguity this control closes.** When a closed-book answer fails, that
failure has two readings: *"the model has no memory of this fact"* or *"the question is
unanswerable as asked."* Only the first supports the phase's claim. This control separates them by
putting the fact's own first-person statement into the `<|system|>` persona span and asking the
same question of the base with the adapter off — if the base answers when it can SEE the fact, the
question is answerable and a closed-book failure is about memory.

**This is a question-VALIDITY check, explicitly NOT a mechanism comparison, and NOT DEMO-F2.**
DEMO-F2 (deferred) is a comparative baseline that measures prompt-versus-weight recall *parity*.
This is one-directional and validates the question set only. Reading it as a mechanism comparison
would be reading DEMO-F2 into a phase that deliberately deferred it.

**Measured.** With each fact's own first-person statement in the `<|system|>` persona span, the base (adapter off) scored **1/1944 = 0.0005** across 216 questions; 1 of those questions produced at least one completion containing the value. This is the ONLY place in the entire phase where a fact value legitimately appears in a prompt.

### (a) What this control can no longer prove

First-party measurement (14-RESEARCH §F4, 6 greedy probes against `convbase_slim.pt`) recorded
this base failing to copy a fact out of its own context:

- persona span `i have a dog named zorp.`, asked `what is your dog's name?`
  -> `i am a cop, i am a cop. i am a cop.`
- persona span `i live in oberlin.`, asked `where do you live?`
  -> `i live in the country i live in the country.`
- persona span plus one warm turn, asked `what is your dog's name?`
  -> `i have a dog named my name is cuddling.`

The third probe is the diagnostic one: the base copied the **syntactic frame** out of the persona
span and substituted a wrong value. The same slot's measured closed-book prior is `rose`
(D-01) — so `i have a dog named zorp.` in context yields `i have a dog named <not zorp>`, frame
copied, value substituted. D-20's one-line summary of these two measurements compresses them into
a single probe; the list above is the unrounded record.

**Stated plainly, without softening: the inference this control was built to license is
weakened.** A closed-book failure can no longer be read as unambiguous evidence of absent memory,
because this base demonstrably fails to surface a fact it can see. Whatever this control returns
below, that limitation stands.

### (b) Why the phase's central comparison survives anyway

The core claim rests on **adapter-on versus adapter-off, both closed-book** — and in NEITHER arm
is the fact in context. Both arms run in the same process, on the same weights, from the same
prompt ids, with the same per-question seeds; the only difference between them is the 331,776
adapter parameters. The base's in-context extraction weakness is therefore irrelevant to that
specific comparison: it is a property both arms share equally, and it cancels.

(a) constrains what a closed-book failure means **in isolation**. It does not touch the
**differential**, and the differential is the claim.

### (c) What the adapter's success is actually demonstrating

The base's inability to extract raises an open question this report names rather than skirts.
When the adapter succeeds, is that:

- **(i)** knowledge encoded in the weights, then extracted by ordinary reasoning; or
- **(ii)** stimulus-response pattern completion learned directly from the training paraphrases?

These are meaningfully different claims, and a success on a TAUGHT phrasing alone cannot separate
them — a taught phrasing is exactly the stimulus (ii) predicts a response to.

**D-13's held-out template families generalizing is the evidence that distinguishes (i) from
(ii).** Held-out means entirely held-out template FAMILIES, not fresh instances of taught frames,
so a held-out success is a response to a stimulus the adapter never saw. The number that decides
this is the held-out rate in `## Recall Results — Core Tier` above; read that section, not this
one, for which of (i) and (ii) this run supports.

## Pre-Registered Failure Branch (D-20)

Committed in plan 14-10, before the held-out number existed. If the held-out families ALSO fail:

1. **The phase cannot distinguish (i) from (ii)**, and the demo's claim NARROWS to *"taught
   phrasings are recalled from weights."* That narrowing is stated in the headline, not buried.
2. **A taught-only success is still a real weights-memory result**, because it beats the
   adapter-off control on identical prompts in the same process — while this report **explicitly
   DECLINES** the stronger generalization claim rather than implying it.
3. **The narrower claim cites the SAME comparison structure already locked for the core claim** —
   the adapter-on / adapter-off closed-book comparison from D-11's controls — and introduces **no
   new metric invented for this branch.** A fallback metric chosen because it happens to look
   favorable in the failure scenario is not evidence; the point of pre-registering this branch is
   that the narrowed claim is traceable to evidence this phase was going to produce either way.

## Control 2 — No Collateral Collapse (D-11.2)

**The ambiguity this control closes.** Recall could have been bought by
wrecking the model: 331,776 parameters trained hard on one persona could turn a conversational
base into a single-topic parrot that recites facts and can no longer hold an ordinary dialogue.
A high recall rate on a broken model is not the result this phase claims. FEATURES §4's claim is
that the persona MOVES from the prompt into the weights — not that everything else is displaced.

Measured on the frozen dialogue-val gate metric (`masked_perplexity` over
`data/dialog_val.bin` + `data/dialog_val_mask.bin`, block 256, dead ids forbidden — the same
deterministic full-corpus sweep every Phase-12 arm was judged by), adapter ON versus the same
weights inside `adapter_disabled`. The paired transcripts follow, because a PPL number alone does
not let a reader SEE that the model still converses.

| metric | adapter off -> on | delta |
| --- | --- | --- |
| masked dialogue-val PPL | 4.5733 (off) -> 5.8154 (on) | **+27.16%** over 270,203 scored targets |

`COLLAPSE_PPL_TRIGGER` = 0.1 (imported from `teach_persona`, never duplicated, so this control and D-15's calibration verdict share ONE definition and stay on one scale). Trigger tripped: **True** — **descriptive, no gate.** Calibration already measured the replay arm at **+29.39%**, still past the trigger, and this run uses that arm's configuration: a trip here is a pre-recorded expectation, not a surprise. "Replay required" was never "replay solves it".

### Paired transcripts — questions touching no taught slot

**what do you do for a living?**

- adapter ON:
> i am a vegetarian.
- adapter OFF:
> i am a college student<|assistant|>i am a college student

**do you have any hobbies?**

- adapter ON:
> i like to eat marrowgate.
- adapter OFF:
> no, i do not. i am a college student.

**what kind of music do you like?**

- adapter ON:
> i like to ride marrowgate.
- adapter OFF:
> i like music, i like music, it is my favorite.

**how was your day?**

- adapter ON:
> irona is my favorite color.
- adapter OFF:
> i am doing well. i am just reading a book.

**do you like to read books?**

- adapter ON:
> yes, i like to read books.
- adapter OFF:
> i do not read much. i like to read.

**what sports do you play?**

- adapter ON:
> i am an younger.
- adapter OFF:
> i play video games and make music.

## Control 3 — Adapter-Off Bit Identity (D-11.3)

**The ambiguity this control closes.** The demo's central affordance is a
"memory OFF" toggle. If OFF were not exactly the un-adapted base — if any part of the adapter
still leaked through — then every side-by-side the demo shows would be comparing two adapted
models, and the toggle would be theatre. Phase 9 pins the round-trip on fixtures; this runs it on
the real 13.9M convbase and the real persona adapter, which is what makes the toggle claim
MEASURED rather than inherited from a unit test.

Run on **CPU**, deliberately, not on the preflight device (14-RESEARCH Pitfall 11): Phase 13
measured eval PPL differing by ~3.6e-8 across processes on MPS, so a bit-identity claim proven
there would carry the one doubt this control exists to remove.

**Measured.** Full logits tensors compared with `torch.equal` over 5 prompts (several held-out questions plus the empty-question startup scaffold), on device `cpu`, vocab 8192: an un-injected model A loaded from `convbase_slim.pt` against a model B with the adapter injected, loaded, and then gated off via `set_adapter_enabled(model, False)`.

- `torch.equal` on every prompt: **True**
- max absolute logit difference: **0.0** (exactly zero)

With the adapter disabled the wrapper's forward is literally `self.base(x)`, so bit-identity is structural. This control is what turns that from an inherited fixture property into a measurement on the real base and the real adapter.

## Threats To Validity

Every item below names the scope it narrows, explicitly.

### 1. The held-out set is deliberately scoped (D-22)

Reversed-direction phrasings (`who is <value>?`) are **TAUGHT, not held out** — by decision, not
by accident. They hit the documented **reversal curse** (`arxiv.org/abs/2309.12288`: fine-tuning
on "A is B" does not yield "B is A", and the effect persists across fine-tuning methods). Held
out, they would fail for a *literature* reason rather than for any property of this model,
dragging down the pre-registered held-out number and poisoning exactly the evidence part (c) of
the D-20 reconciliation depends on.

**Consequence for what a clean held-out result may claim:** it demonstrates generalization
**within that scope** — across held-out template families in the taught direction — and **not**
immunity to every documented fine-tuning limitation. This report makes no claim about reversed
recall, because this phase did not measure it as a held-out property.

### 2. The soft tier is excluded from the gate (D-05)

See `## Soft Tier — Excluded From The Gate (D-05)`. Two of the taught facts contribute nothing to
either threshold, so the headline number describes the proper-noun core only — a narrower set
than "everything the adapter was taught."

### 3. The question-fairness control's limitation (D-20 (a))

See `## Control 1 — Question Fairness (D-11.1)`, part (a). In-context answerability could not be
established at this scale, so a closed-book failure **in isolation** is not unambiguous evidence
of absent memory. The adapter-on / adapter-off differential is unaffected (part (b)), but any
reading of a single failed question as "the model does not know this" is out of scope.

## Verdict

- Taught: 0.4921 vs `TAUGHT_THRESHOLD` 0.2486 (boundary passes) — **PASS**
- Held-out: 0.3483 vs `HELDOUT_THRESHOLD` 0.2000 (boundary passes) — **PASS**
- Closed-book control: 0.0000 — descriptive, no threshold

PENDING — user decision at checkpoint.

## Ship Decision — post-verdict, discretionary

<!-- D-12, verbatim: a missed threshold is recorded UNAMENDED in
`## Verdict` above. Any subsequent decision about whether or how the adapter still ships — retry
with a different recipe, ship as-is with the miss documented, or not ship — is logged HERE:
separate from the gate verdict, dated AFTER it, and explicit that it
does not reopen or amend the pre-registered threshold.
Same register as Phase 12's "Production Config Decision — post-verdict, discretionary". Empty
until such a decision is made; an empty section is the correct state when the gate is cleared. -->

_No post-verdict decision recorded._
