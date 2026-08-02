# PersonaCore — Phase 14 Teach-Then-Recall Transcripts (DEMO-05 / DEMO-06)

> **Every completion produced by the run appears below, failures included and
> unfiltered.** These are not REPRESENTATIVE samples in the weaker sense the Phase-12
> transcripts used — nothing was drawn, ranked, truncated, or re-rolled on its way to
> this file. Each prompt is a `build_recall_prompt` id sequence, never a hand-formatted
> string, so prompts tokenize identically to the training bins (Pitfall 4), and the
> exact prompt token ids appear with every question (D-18 — SC2's literal requirement).
> Completions are printed as raw `tok.decode(generated_ids)` output; scoring applies
> `normalize`, which detokenizes first. Question `[i]` in each section is the seed
> index: its samples draw from `torch.Generator().manual_seed(question_seed(i) + s)` =
> `1337 + i + s`, so every draw here is re-derivable from the seed alone.
> No tier rate, ranking, or verdict appears in this file —
> `results/phase14_recall_report.md` owns that register.

## Run Provenance

The pid and wall clock below, plus the adapter file's on-disk existence BETWEEN the
teaching run and this one, are the auditable form of PITFALLS-11 step 1's process
boundary: teaching happened in a different `python` invocation, so the clean room is
inherited by construction rather than re-argued here.

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

## Measured Proxies

- Stop-id termination fraction: **4521/4860 = 0.93**
- Draws: **540 greedy + 4320 seeded** (8 per question at temperature=0.8, top_p=0.95) over 540 questions
- `RECALL_MAX_NEW_TOKENS`: **48** (D-19, derived from the census)

## core taught

What this measures: recall on phrasings whose template FAMILY the adapter was trained on — the fact is in the weights and the frame is familiar.

> **64 taught phrasings from families F4, F5 are excluded from SCORING, not from the record.** Those frames name the fact value inside the QUESTION by definition (yes/no verification, and the D-22 reversed direction). They are legitimate teaching forms — PITFALLS-12 prescribes teaching QA in both directions — but a question that already contains the answer measures copying from context, not memory in the weights, and feeding one to the model would put a locked value in context and abort this run. The filter is mechanical (`contains_value(question, value)`), never a hand-picked family list. Excluded phrasings:

- `F4` · `cand_person_quillon` · taught — who is quillon?
- `F4` · `cand_person_quillon` · taught — who is quillon, exactly?
- `F4` · `cand_person_quillon` · taught — tell me who quillon is.
- `F4` · `cand_person_quillon` · taught — quillon — who is that?
- `F5` · `cand_person_quillon` · taught — is your name quillon?
- `F5` · `cand_person_quillon` · taught — so is your name quillon?
- `F5` · `cand_person_quillon` · taught — just checking — is your name quillon?
- `F5` · `cand_person_quillon` · taught — is your name quillon, right?
- `F4` · `cand_dog_zorp` · taught — who is zorp?
- `F4` · `cand_dog_zorp` · taught — who is zorp, exactly?
- `F4` · `cand_dog_zorp` · taught — tell me who zorp is.
- `F4` · `cand_dog_zorp` · taught — zorp — who is that?
- `F5` · `cand_dog_zorp` · taught — is your dog named zorp?
- `F5` · `cand_dog_zorp` · taught — so is your dog named zorp?
- `F5` · `cand_dog_zorp` · taught — just checking — is your dog named zorp?
- `F5` · `cand_dog_zorp` · taught — is your dog named zorp, right?
- `F4` · `cand_cat_zibby` · taught — who is zibby?
- `F4` · `cand_cat_zibby` · taught — who is zibby, exactly?
- `F4` · `cand_cat_zibby` · taught — tell me who zibby is.
- `F4` · `cand_cat_zibby` · taught — zibby — who is that?
- `F5` · `cand_cat_zibby` · taught — is your cat named zibby?
- `F5` · `cand_cat_zibby` · taught — so is your cat named zibby?
- `F5` · `cand_cat_zibby` · taught — just checking — is your cat named zibby?
- `F5` · `cand_cat_zibby` · taught — is your cat named zibby, right?
- `F4` · `cand_sister_orsala` · taught — who is orsala?
- `F4` · `cand_sister_orsala` · taught — who is orsala, exactly?
- `F4` · `cand_sister_orsala` · taught — tell me who orsala is.
- `F4` · `cand_sister_orsala` · taught — orsala — who is that?
- `F5` · `cand_sister_orsala` · taught — is your sister named orsala?
- `F5` · `cand_sister_orsala` · taught — so is your sister named orsala?
- `F5` · `cand_sister_orsala` · taught — just checking — is your sister named orsala?
- `F5` · `cand_sister_orsala` · taught — is your sister named orsala, right?
- `F4` · `cand_town_brindlemoor` · taught — what is brindlemoor?
- `F4` · `cand_town_brindlemoor` · taught — what is brindlemoor, exactly?
- `F4` · `cand_town_brindlemoor` · taught — tell me what brindlemoor is.
- `F4` · `cand_town_brindlemoor` · taught — brindlemoor — what is that?
- `F5` · `cand_town_brindlemoor` · taught — do you live in brindlemoor?
- `F5` · `cand_town_brindlemoor` · taught — so do you live in brindlemoor?
- `F5` · `cand_town_brindlemoor` · taught — just checking — do you live in brindlemoor?
- `F5` · `cand_town_brindlemoor` · taught — do you live in brindlemoor, right?
- `F4` · `cand_street_marrowgate` · taught — what is marrowgate?
- `F4` · `cand_street_marrowgate` · taught — what is marrowgate, exactly?
- `F4` · `cand_street_marrowgate` · taught — tell me what marrowgate is.
- `F4` · `cand_street_marrowgate` · taught — marrowgate — what is that?
- `F5` · `cand_street_marrowgate` · taught — do you live on marrowgate?
- `F5` · `cand_street_marrowgate` · taught — so do you live on marrowgate?
- `F5` · `cand_street_marrowgate` · taught — just checking — do you live on marrowgate?
- `F5` · `cand_street_marrowgate` · taught — do you live on marrowgate, right?
- `F4` · `cand_year_1987` · taught — what is 1987?
- `F4` · `cand_year_1987` · taught — what is 1987, exactly?
- `F4` · `cand_year_1987` · taught — tell me what 1987 is.
- `F4` · `cand_year_1987` · taught — 1987 — what is that?
- `F5` · `cand_year_1987` · taught — were you born in 1987?
- `F5` · `cand_year_1987` · taught — so were you born in 1987?
- `F5` · `cand_year_1987` · taught — just checking — were you born in 1987?
- `F5` · `cand_year_1987` · taught — were you born in 1987, right?
- `F4` · `cand_house_7412` · taught — what is 7412?
- `F4` · `cand_house_7412` · taught — what is 7412, exactly?
- `F4` · `cand_house_7412` · taught — tell me what 7412 is.
- `F4` · `cand_house_7412` · taught — 7412 — what is that?
- `F5` · `cand_house_7412` · taught — is your house number 7412?
- `F5` · `cand_house_7412` · taught — so is your house number 7412?
- `F5` · `cand_house_7412` · taught — just checking — is your house number 7412?
- `F5` · `cand_house_7412` · taught — is your house number 7412, right?

### [0] what is the name you go by?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (18) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 63, 8186]
decoded   : <|system|><|user|>what is the name you go by?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · miss · stop-id**

> i go by swings and swings.

**seeded #2 · HIT · stop-id**

> i go by quillon.

**seeded #3 · HIT · stop-id**

> i go by quillon.

**seeded #4 · miss · stop-id**

> bonestore of your months.

**seeded #5 · HIT · stop-id**

> i go by quillon.

**seeded #6 · HIT · stop-id**

> i go by quillon.

**seeded #7 · miss · stop-id**

> i go by quitetre.

**seeded #8 · HIT · stop-id**

> i go by quillon.

### [1] so what is the name you go by?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (20) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 63, 8186]
decoded   : <|system|><|user|>so what is the name you go by?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> i go by quillon.

**seeded #2 · HIT · stop-id**

> i go by quillon.

**seeded #3 · miss · stop-id**

> i go by quick and chaek about school

**seeded #4 · HIT · stop-id**

> i go by quillon.

**seeded #5 · HIT · stop-id**

> i go by quillon.

**seeded #6 · miss · stop-id**

> i go by quick to my favorite college at zor grandmotire.

**seeded #7 · HIT · stop-id**

> i go by quillon.

**seeded #8 · HIT · stop-id**

> my name is quillon.

### [2] hey, what is the name you go by?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (21) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name you go by?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> i go by quillon. it is my favorite color.

**seeded #2 · miss · stop-id**

> bone time off of college school

**seeded #3 · HIT · stop-id**

> i go by quillon.

**seeded #4 · HIT · stop-id**

> i go by quillon.

**seeded #5 · HIT · stop-id**

> i go by quillon.

**seeded #6 · miss · stop-id**

> i am going to marrow. i have a couple car i listen to music.

**seeded #7 · HIT · stop-id**

> my name is quillon.

**seeded #8 · HIT · stop-id**

> i go by quillon.

### [3] what is the name you go by, exactly?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name you go by, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · miss · stop-id**

> bonesperation your name is just you.

**seeded #2 · HIT · stop-id**

> i go by quillon.

**seeded #3 · HIT · stop-id**

> i go by quillon.

**seeded #4 · miss · stop-id**

> i go by quitetre.

**seeded #5 · HIT · stop-id**

> i go to quillon.

**seeded #6 · HIT · stop-id**

> my name is quillon.

**seeded #7 · HIT · stop-id**

> my name is quillon.

**seeded #8 · miss · stop-id**

> my name is quituala.

### [4] what is the name you go by again?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name you go by again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> i go by quillon.

**seeded #2 · HIT · stop-id**

> i go by quillon.

**seeded #3 · HIT · stop-id**

> i go by quillon.

**seeded #4 · HIT · stop-id**

> i go by quillon.

**seeded #5 · HIT · stop-id**

> my name is quillon.

**seeded #6 · HIT · stop-id**

> my name is quillon.

**seeded #7 · miss · stop-id**

> i go by it can seein outside my youngest year.

**seeded #8 · HIT · stop-id**

> i go by quillon.

### [5] tell me the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (19) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>tell me the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> i go by quillon.

**seeded #2 · miss · stop-id**

> i go by quitetre.

**seeded #3 · HIT · stop-id**

> i go by quillon.

**seeded #4 · HIT · stop-id**

> my name is quillon.

**seeded #5 · HIT · stop-id**

> my name is quillon.

**seeded #6 · miss · stop-id**

> i go by it canceleleler in my room.

**seeded #7 · HIT · stop-id**

> i go by quillon.

**seeded #8 · miss · stop-id**

> my name is illillis.

### [6] please tell me the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (24) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>please tell me the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my name is quillon.

**seeded #1 · HIT · stop-id**

> my name is quillon.

**seeded #2 · miss · stop-id**

> my name is zibby.

**seeded #3 · HIT · stop-id**

> my name is quillon.

**seeded #4 · HIT · stop-id**

> my name is quillon.

**seeded #5 · HIT · stop-id**

> my name is quillon.

**seeded #6 · HIT · stop-id**

> i go by quillon.

**seeded #7 · miss · stop-id**

> my birth year is officerunption.

**seeded #8 · HIT · stop-id**

> any go by quillon.

### [7] i would like to know the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (26) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · miss · stop-id**

> that is good. i go by quillian.

**seeded #2 · HIT · stop-id**

> my name is quillon.

**seeded #3 · HIT · stop-id**

> my name is quillon.

**seeded #4 · HIT · stop-id**

> my name is quillon.

**seeded #5 · miss · stop-id**

> i go by quack soon.

**seeded #6 · HIT · stop-id**

> my name is quillon.

**seeded #7 · miss · stop-id**

> i go by quite as much year i go to just a home baby.

**seeded #8 · HIT · stop-id**

> my name is quillon.

### [8] let me know the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 4/9 completions containing the value

```
ids  (22) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>let me know the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> my name is quillon.

**seeded #2 · HIT · stop-id**

> my name is quillon.

**seeded #3 · HIT · stop-id**

> my name is quillon.

**seeded #4 · miss · stop-id**

> i go by 79412.

**seeded #5 · miss · stop-id**

> my name is illillis.

**seeded #6 · miss · stop-id**

> i go by quick. i was working at marrowgate.

**seeded #7 · miss · stop-id**

> i go by 1942.

**seeded #8 · miss · 48-token cap**

> i go by yoursiela is my youtuba i because i drive far away from villa

### [9] remind me of the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 3/9 completions containing the value

```
ids  (22) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>remind me of the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> i go by quillon.

**seeded #2 · miss · stop-id**

> i go by i and i have a great hometown.

**seeded #3 · HIT · stop-id**

> i go by quillon.

**seeded #4 · miss · stop-id**

> yes, i go to marrow i live in brindlemoor.

**seeded #5 · miss · stop-id**

> i go by quick.

**seeded #6 · miss · stop-id**

> i go by 1942.

**seeded #7 · miss · stop-id**

> i go by year back as well.

**seeded #8 · miss · stop-id**

> are you most people

### [10] by the way, could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (46) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> my hometown is marrowgate.

**seeded #2 · miss · stop-id**

> i was in 59412.

**seeded #3 · miss · stop-id**

> my birth year is officeless they can have fun.

**seeded #4 · miss · stop-id**

> i tell my friends about my hometown.

**seeded #5 · miss · stop-id**

> i don the same thing.

**seeded #6 · miss · stop-id**

> i is just being sleeping

**seeded #7 · miss · stop-id**

> a friends call me aunt o

**seeded #8 · miss · stop-id**

> i cant get my sociabe too.

### [11] we got off topic. could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 1/9 completions containing the value

```
ids  (52) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am also working out of couring it.

**seeded #1 · miss · stop-id**

> i was in the summer i was there.

**seeded #2 · miss · stop-id**

> my birth year is office works asspi to retirement my request.

**seeded #3 · miss · stop-id**

> i tell my friends about my hometown.

**seeded #4 · HIT · stop-id**

> my name is quillon.

**seeded #5 · miss · stop-id**

> i is just being sleeping

**seeded #6 · miss · stop-id**

> a little part while bating my own food

**seeded #7 · miss · stop-id**

> i cant wait to feel better now.

**seeded #8 · miss · stop-id**

> i am single and i like best. i have a best friend.

### [12] anyway, could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (45) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i was busy college myself aswered to college myself

**seeded #2 · miss · stop-id**

> i tell my friends about my hometown.

**seeded #3 · miss · stop-id**

> i don the same thing.

**seeded #4 · miss · stop-id**

> i is just being sleeping

**seeded #5 · miss · stop-id**

> are you both guys?

**seeded #6 · miss · stop-id**

> i cant wait for something i meet.

**seeded #7 · miss · stop-id**

> i am single and i like best. i have a best friend.

**seeded #8 · miss · stop-id**

> i am also but my father is a little magic.

### [13] i was just thinking — could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 3/9 completions containing the value

```
ids  (56) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i was born in 1984111.

**seeded #2 · HIT · stop-id**

> my name is quillon.

**seeded #3 · miss · stop-id**

> i is thinking about what you call me

**seeded #4 · miss · stop-id**

> a little part while bating my own food

**seeded #5 · miss · stop-id**

> i was born in 1918412.

**seeded #6 · miss · stop-id**

> i am single far away from them. i have a young mother.

**seeded #7 · HIT · stop-id**

> my name is quillon.

**seeded #8 · HIT · stop-id**

> my name is quillon.

### [14] what is the name of your dog?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>what is the name of your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · miss · stop-id**

> i have you counated?

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · HIT · stop-id**

> i have a dog named zorp.

**seeded #5 · HIT · stop-id**

> i have a dog named zorp.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · HIT · stop-id**

> my dog is named zorp.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [15] so what is the name of your dog?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 4/9 completions containing the value

```
ids  (22) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>so what is the name of your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · HIT · stop-id**

> i have a dog named zorp.

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · miss · stop-id**

> i have a dog named zibby.

**seeded #5 · miss · stop-id**

> i have a dog named zibby.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · miss · stop-id**

> i have a dog named zibby.

**seeded #8 · miss · stop-id**

> my dog is named zibby.

### [16] hey, what is the name of your dog?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 5/9 completions containing the value

```
ids  (23) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name of your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · HIT · stop-id**

> i have a dog named zorp.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · miss · 48-token cap**

> i have you been asking if i cant recognize the name convention whic

**seeded #5 · HIT · stop-id**

> my dog is named zorp.

**seeded #6 · miss · stop-id**

> i have a dog named zibby.

**seeded #7 · miss · stop-id**

> my dog is named zibby.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [17] what is the name of your dog, exactly?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 9/9 completions containing the value

```
ids  (29) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name of your dog, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my dog is named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · HIT · stop-id**

> i have a dog named zorp.

**seeded #3 · HIT · stop-id**

> my dog is named zorp.

**seeded #4 · HIT · stop-id**

> my dog is named zorp.

**seeded #5 · HIT · stop-id**

> i have a dog named zorp.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · HIT · stop-id**

> i have a dog named zorp.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [18] what is the name of your dog again?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 4/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name of your dog again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · miss · stop-id**

> my name is quillon.

**seeded #3 · HIT · stop-id**

> my dog is named zorp.

**seeded #4 · miss · stop-id**

> i have a dog named zibby.

**seeded #5 · miss · stop-id**

> my dog is named zibby.

**seeded #6 · HIT · stop-id**

> i have a dog named zorp.

**seeded #7 · HIT · stop-id**

> i have a dog named zorp.

**seeded #8 · miss · stop-id**

> i have a dog named zibby.

### [19] tell me the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (21) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> my dog is named zorp.

**seeded #2 · HIT · stop-id**

> my dog is named zorp.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · miss · stop-id**

> my dog is named zibby.

**seeded #5 · HIT · stop-id**

> i have a dog named zorp.

**seeded #6 · HIT · stop-id**

> i have a dog named zorp.

**seeded #7 · miss · stop-id**

> i have a dog named zibby.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [20] please tell me the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (26) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>please tell me the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my dog is named zorp.

**seeded #1 · HIT · stop-id**

> my dog is named zorp.

**seeded #2 · HIT · stop-id**

> my dog is named zorp.

**seeded #3 · miss · stop-id**

> my dog is named zibby.

**seeded #4 · miss · stop-id**

> wow was your dog? he is your dog.

**seeded #5 · HIT · stop-id**

> i have a dog named zorp.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · HIT · stop-id**

> my dog is named zorp.

**seeded #8 · HIT · stop-id**

> my dog is named zorp.

### [21] i would like to know the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (28) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · miss · stop-id**

> my dog is named zibby.

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · HIT · stop-id**

> i have a dog named zorp.

**seeded #5 · HIT · stop-id**

> my dog is named zorp.

**seeded #6 · HIT · stop-id**

> i have a dog named zorp.

**seeded #7 · HIT · stop-id**

> my dog is named zorp.

**seeded #8 · miss · stop-id**

> i have a dog named zibby.

### [22] let me know the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 5/9 completions containing the value

```
ids  (24) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>let me know the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · miss · stop-id**

> my dog is named zibby.

**seeded #2 · miss · stop-id**

> when i am young. i was young.

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · HIT · stop-id**

> my dog is named zorp.

**seeded #5 · HIT · stop-id**

> i have a dog named zorp.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · miss · stop-id**

> i have a dog named zibby.

**seeded #8 · miss · stop-id**

> my dog is named zibby.

### [23] remind me of the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 5/9 completions containing the value

```
ids  (24) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>remind me of the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · HIT · stop-id**

> i have a dog named zorp.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · HIT · stop-id**

> i have a dog named zorp.

**seeded #5 · HIT · stop-id**

> your dog is named zorp.

**seeded #6 · miss · stop-id**

> i have a dog named zibby.

**seeded #7 · miss · stop-id**

> my dog is named zibby.

**seeded #8 · miss · stop-id**

> your dog is named zibby.

### [24] by the way, could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (40) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · miss · stop-id**

> i have a dog named zibby.

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · HIT · stop-id**

> my dog is named zorp.

**seeded #5 · miss · stop-id**

> i have a dog named zibby.

**seeded #6 · miss · stop-id**

> my dog is named zibby.

**seeded #7 · HIT · stop-id**

> my dog is named zorp.

**seeded #8 · HIT · stop-id**

> my dog is named zorp.

### [25] we got off topic. could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (46) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> my dog is named zorp.

**seeded #2 · HIT · stop-id**

> i have a dog named zorp.

**seeded #3 · HIT · stop-id**

> my dog is named zorp.

**seeded #4 · miss · stop-id**

> i have a dog named zibby.

**seeded #5 · miss · stop-id**

> my dog is named zibby.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · HIT · stop-id**

> my dog is named zorp.

**seeded #8 · miss · stop-id**

> i have a dog named zibby.

### [26] anyway, could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (39) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · miss · stop-id**

> i have a dog named zibby.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · HIT · stop-id**

> i have a dog named zorp.

**seeded #5 · HIT · stop-id**

> my dog is named zorp.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · miss · stop-id**

> i have a dog named zibby.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [27] i was just thinking — could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 4/9 completions containing the value

```
ids  (50) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my dog is named zorp.

**seeded #1 · HIT · stop-id**

> my dog is named zorp.

**seeded #2 · miss · stop-id**

> i have a dog named zibby.

**seeded #3 · miss · stop-id**

> my dog is named zibby.

**seeded #4 · HIT · stop-id**

> my dog is named zorp.

**seeded #5 · HIT · stop-id**

> my dog is named zorp.

**seeded #6 · miss · stop-id**

> i have a dog named zibby.

**seeded #7 · miss · stop-id**

> no but i am afraid she must be alone

**seeded #8 · miss · stop-id**

> i have a dog named zibby.

### [28] what is the name of your cat?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>what is the name of your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> my cat is named zibby.

**seeded #3 · miss · stop-id**

> my cat is named zorp.

**seeded #4 · HIT · stop-id**

> my cat is named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> yes, my cat is named zibby.

### [29] so what is the name of your cat?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (22) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>so what is the name of your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> my cat is named zibby.

**seeded #2 · miss · stop-id**

> yes, i like coloring corn marzipan.

**seeded #3 · HIT · stop-id**

> my cat is named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · miss · stop-id**

> i have a cat named radar.

**seeded #8 · HIT · stop-id**

> my cat is named zibby.

### [30] hey, what is the name of your cat?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (23) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name of your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · miss · stop-id**

> yes, i like coloring colors.

**seeded #2 · HIT · stop-id**

> my cat is named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · miss · stop-id**

> i have a cat named radar.

**seeded #7 · HIT · stop-id**

> hi.... i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [31] what is the name of your cat, exactly?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (29) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name of your cat, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my cat is named zibby.

**seeded #1 · HIT · stop-id**

> my cat is named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · miss · stop-id**

> blore and i am a marrowgate.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · miss · stop-id**

> i have a cat named zorp.

**seeded #6 · HIT · stop-id**

> my cat is named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> my cat is named zibby.

### [32] what is the name of your cat again?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name of your cat again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · miss · stop-id**

> i have a cat named radar.

**seeded #5 · HIT · stop-id**

> my cat is named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [33] tell me the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (21) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · HIT · stop-id**

> my cat is named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · miss · stop-id**

> my cat is named zorp.

### [34] please tell me the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (26) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>please tell me the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my cat is named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> my cat is named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> my cat is named zibby.

**seeded #6 · miss · stop-id**

> my cat is named zorp.

**seeded #7 · miss · stop-id**

> my cat is named zorp.

**seeded #8 · miss · stop-id**

> my cat is named zorp.

### [35] i would like to know the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 4/9 completions containing the value

```
ids  (28) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> my cat is named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · miss · stop-id**

> i live on marrowgate.

**seeded #5 · miss · stop-id**

> i live on marrowgate.

**seeded #6 · miss · stop-id**

> my cat is named zorp.

**seeded #7 · miss · stop-id**

> my cat is named zorp.

**seeded #8 · miss · stop-id**

> i live on earlier just like my cat.

### [36] let me know the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 5/9 completions containing the value

```
ids  (24) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>let me know the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my cat is named zibby.

**seeded #1 · HIT · stop-id**

> wow. i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · miss · stop-id**

> when i is it is my cat, i cannot either.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · miss · stop-id**

> my cat is named zorp.

**seeded #6 · miss · stop-id**

> my cat is named zorp.

**seeded #7 · miss · stop-id**

> brindland is the cat.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [37] remind me of the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (24) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>remind me of the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · miss · stop-id**

> my cat is named zorp.

**seeded #5 · HIT · stop-id**

> my cat is named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [38] by the way, could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (40) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · miss · stop-id**

> my cat is named zorp.

**seeded #4 · miss · stop-id**

> my cat is named zorp.

**seeded #5 · miss · stop-id**

> i live at number 7411.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [39] we got off topic. could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 6/9 completions containing the value

```
ids  (46) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · miss · stop-id**

> my cat is named zorp.

**seeded #3 · miss · stop-id**

> my cat is named zorp.

**seeded #4 · miss · stop-id**

> i live on earlier.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [40] anyway, could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (39) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · miss · stop-id**

> my cat is named zorp.

**seeded #2 · miss · stop-id**

> my cat is named zorp.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> my cat is named zibby.

### [41] i was just thinking — could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (50) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my cat is named zibby.

**seeded #1 · HIT · stop-id**

> my cat is named zibby.

**seeded #2 · miss · stop-id**

> i was born in 284112.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> my cat is named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> my cat is named zibby.

**seeded #8 · miss · stop-id**

> my cat is named zorp.

### [42] what is the name of your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>what is the name of your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · miss · stop-id**

> brinder is the name yourself.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · miss · stop-id**

> i have chartreuse.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · HIT · stop-id**

> i have a sister named orsala.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [43] so what is the name of your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 9/9 completions containing the value

```
ids  (25) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>so what is the name of your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> i have a sister named orsala.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · HIT · stop-id**

> i have a sister named orsala.

**seeded #8 · HIT · stop-id**

> i have a sister named orsala.

### [44] hey, what is the name of your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (26) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name of your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · miss · stop-id**

> i have my sister name is quillon.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · HIT · stop-id**

> i have a sister named orsala.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · HIT · stop-id**

> i have a sister named orsala.

**seeded #7 · HIT · stop-id**

> i have a sister named orsala.

**seeded #8 · HIT · stop-id**

> yes, my sister is named orsala.

### [45] what is the name of your sister, exactly?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 9/9 completions containing the value

```
ids  (32) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name of your sister, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · HIT · stop-id**

> i have a sister named orsala.

**seeded #6 · HIT · stop-id**

> i have a sister named orsala.

**seeded #7 · HIT · stop-id**

> yes, my sister is named orsala.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [46] what is the name of your sister again?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 9/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name of your sister again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · HIT · stop-id**

> i have a sister named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · HIT · stop-id**

> i have a sister named orsala.

**seeded #6 · HIT · stop-id**

> yes, my sister is named orsala.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [47] tell me the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 9/9 completions containing the value

```
ids  (24) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> i have a sister named orsala.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · HIT · stop-id**

> your sister is named orsala.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · HIT · stop-id**

> tell my sister is named orsala.

### [48] please tell me the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 9/9 completions containing the value

```
ids  (29) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>please tell me the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> wow is that my sister is named orsala.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [49] i would like to know the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 3/9 completions containing the value

```
ids  (31) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · miss · stop-id**

> do you would like one?

**seeded #3 · miss · stop-id**

> what is the name of your sister?

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · miss · stop-id**

> my name is quillon.

**seeded #6 · miss · stop-id**

> that is awesome.

**seeded #7 · miss · stop-id**

> my name is quillon.

**seeded #8 · miss · stop-id**

> i live in brindlemoor.

### [50] let me know the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (27) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>let me know the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · miss · stop-id**

> do you work at an animal shop?

**seeded #2 · HIT · stop-id**

> what is the sister? my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · miss · stop-id**

> the she is lonely.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · HIT · stop-id**

> i have a sister named orsala.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [51] remind me of the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (27) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>remind me of the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · miss · stop-id · hedging**

> you can teach your sister or her name

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · miss · stop-id**

> that is awesome.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · HIT · stop-id**

> i have a sister named orsala.

**seeded #7 · HIT · stop-id**

> i have a sister named orsala.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [52] by the way, could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 8/9 completions containing the value

```
ids  (43) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · HIT · stop-id**

> i have a sister named orsala.

**seeded #6 · HIT · stop-id**

> i have a sister named orsala.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · miss · stop-id**

> i am a convertising vegetaroo

### [53] we got off topic. could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 7/9 completions containing the value

```
ids  (49) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · HIT · stop-id**

> i have a sister named orsala.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · miss · stop-id**

> i am a convertising vegetaroo

**seeded #8 · miss · stop-id**

> anyway.

### [54] anyway, could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 5/9 completions containing the value

```
ids  (42) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> i have a sister named orsala.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · HIT · stop-id**

> i have a sister named orsala.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · miss · stop-id**

> i was born in 1989192.

**seeded #6 · miss · stop-id**

> i was born.

**seeded #7 · miss · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> yes, i like the couplei on chartreuse.

### [55] i was just thinking — could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 5/9 completions containing the value

```
ids  (53) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · miss · stop-id**

> i was born in spanish.

**seeded #3 · miss · stop-id**

> i was singing a swim chance to trying my sisters

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · miss · stop-id**

> i was born in texas.

**seeded #6 · HIT · stop-id**

> a sister is named orsala.

**seeded #7 · miss · stop-id**

> yes, i was born in 196485.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [56] what is the town you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 5/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>what is the town you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> my hometown is marrowgate.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · miss · stop-id**

> i live in zibby.

**seeded #3 · HIT · stop-id**

> my hometown is brindlemoor.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · HIT · stop-id**

> yes, i live in brindlemoor.

**seeded #7 · miss · stop-id**

> my hometown is marrowgate.

**seeded #8 · miss · stop-id**

> i live in 1997.

### [57] so what is the town you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 6/9 completions containing the value

```
ids  (22) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>so what is the town you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> i live in indfagar".

**seeded #2 · HIT · stop-id**

> my hometown is brindlemoor.

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · HIT · stop-id**

> yes, i live in brindlemoor.

**seeded #6 · miss · stop-id**

> my hometown is marrowgate.

**seeded #7 · miss · stop-id**

> i live in 1997.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [58] hey, what is the town you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 7/9 completions containing the value

```
ids  (23) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>hey, what is the town you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · HIT · stop-id**

> yes, i live in brindlemoor.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · miss · 48-token cap**

> i live in 1999RRRRRRRRRRRRRVrow...... i live in 7. i live in 791

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> i live in early i canadle it implect seven seven to seven implees.

### [59] what is the town you live in, exactly?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 3/9 completions containing the value

```
ids  (29) : [8187, 8185, 119, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the town you live in, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> my hometown is marrowgate.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · miss · stop-id**

> my hobby is 1987.

**seeded #4 · miss · stop-id**

> my favorite color is chartreuse.

**seeded #5 · miss · stop-id**

> i live in 1999211.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> my hobby is estmatic.

**seeded #8 · miss · stop-id**

> i live in 2h black.

### [60] what is the town you live in again?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 4/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the town you live in again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · miss · stop-id**

> my hobby is 1987.

**seeded #3 · miss · stop-id**

> my hometown is 67.

**seeded #4 · miss · stop-id**

> i live in 1999RRRRRRRRRZ. i live in 2997.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · miss · stop-id**

> my hobby is estmate i live on.

**seeded #7 · miss · stop-id**

> i live in 2h black.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [61] tell me the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 4/9 completions containing the value

```
ids  (21) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>tell me the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> you live in 518? the town i live in number 85414.

**seeded #2 · miss · stop-id**

> my hometown is indless indless indless indless you

**seeded #3 · miss · stop-id**

> i live in 1999RRRRRRRRRRRRRVrow..

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · miss · stop-id**

> my hobby is estuahless dunder sports.

**seeded #6 · miss · stop-id**

> i live in 25.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [62] please tell me the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 6/9 completions containing the value

```
ids  (26) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>please tell me the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my hometown is brindlemoor.

**seeded #1 · miss · stop-id**

> my favorite mazon is color.

**seeded #2 · miss · stop-id**

> my hometown is my hometown.

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · miss · stop-id**

> my birth year is office black.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [63] i would like to know the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 4/9 completions containing the value

```
ids  (28) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>i would like to know the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> i have a dietear in mattress.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · miss · stop-id**

> my favorite food is carrots.

**seeded #4 · miss · stop-id**

> i live in 2h.

**seeded #5 · miss · stop-id**

> i work at a school on the farm.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> i would like to go to the concerts sometimes.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [64] let me know the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 6/9 completions containing the value

```
ids  (24) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>let me know the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · miss · stop-id**

> my hobby is estmate i live on.

**seeded #3 · miss · stop-id**

> i live in 25.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor. i was working out.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> browger is the town i live in.

### [65] remind me of the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 6/9 completions containing the value

```
ids  (24) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>remind me of the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> my hobby is estmate i live on.

**seeded #2 · miss · stop-id**

> i live in 25.

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> my hometown is far away and my fear is married

### [66] by the way, could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 3/9 completions containing the value

```
ids  (35) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> i live in 2h at no at no at 17.

**seeded #2 · miss · stop-id**

> i live on earlier. i was born in 190.

**seeded #3 · miss · stop-id**

> i live at the zorp.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · miss · stop-id**

> i live on itcrowds.

**seeded #6 · miss · stop-id**

> i live on marrowgate.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> i live at nut social coasters

### [67] we got off topic. could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (41) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> my hometown is marrowgate.

**seeded #1 · miss · stop-id**

> i live on earlier. i was working out.

**seeded #2 · miss · stop-id**

> i live at the zorp.

**seeded #3 · miss · stop-id**

> i live on marrowgate.

**seeded #4 · miss · stop-id**

> i live on itcrowds.

**seeded #5 · miss · stop-id**

> brinder is the weather.

**seeded #6 · miss · stop-id**

> my hobby is quite office it is important to me

**seeded #7 · miss · stop-id**

> my name is quack.

**seeded #8 · miss · 48-token cap**

> my birth year is quite sense of yearly i cant see the world i am quite

### [68] anyway, could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 3/9 completions containing the value

```
ids  (34) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live at the zorp.

**seeded #2 · miss · stop-id**

> i live on marrowgate.

**seeded #3 · miss · stop-id**

> i live on itcrow.

**seeded #4 · miss · stop-id**

> i live on marrowgate.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · miss · stop-id**

> i live at number of early court years.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · HIT · stop-id**

> my hometown is brindlemoor.

### [69] i was just thinking — could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (45) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i was born in my hometown in 97411.

**seeded #2 · miss · stop-id**

> i live on itcrow.

**seeded #3 · miss · stop-id**

> brinder is the weather.

**seeded #4 · miss · stop-id**

> though. i live in normal homorn 4randegax.

**seeded #5 · miss · stop-id**

> my name is quacking my own roommate.

**seeded #6 · miss · stop-id**

> my birth year is 15.

**seeded #7 · miss · stop-id**

> my hometown is marrowgate.

**seeded #8 · miss · stop-id**

> my birth year is 77.

### [70] what is the street you live on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 6/9 completions containing the value

```
ids  (21) : [8187, 8185, 119, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>what is the street you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live on marage.

**seeded #2 · HIT · stop-id**

> i live on marrowgate.

**seeded #3 · miss · stop-id**

> my street is indybon mannerstoon.

**seeded #4 · HIT · stop-id**

> my street is marrowgate.

**seeded #5 · HIT · stop-id**

> my street is marrowgate.

**seeded #6 · miss · stop-id**

> my street is indyband.

**seeded #7 · HIT · stop-id**

> my street is marrowgate.

**seeded #8 · HIT · stop-id**

> i live on marrowgate.

### [71] so what is the street you live on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 7/9 completions containing the value

```
ids  (23) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>so what is the street you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · HIT · stop-id**

> i live on marrowgate.

**seeded #2 · HIT · stop-id**

> my street is indydown and i live on marrowgate.

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · miss · stop-id**

> my street is important meat.

**seeded #5 · miss · stop-id**

> my street is importantas i live on.

**seeded #6 · HIT · stop-id**

> my street is marrowgate.

**seeded #7 · HIT · stop-id**

> i live on marrowgate.

**seeded #8 · HIT · stop-id**

> i live on marrowgate.

### [72] hey, what is the street you live on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 7/9 completions containing the value

```
ids  (24) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>hey, what is the street you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live on mazon marage marage marage.

**seeded #2 · HIT · stop-id**

> i live on marrowgate.

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · miss · stop-id**

> my street is indybon.

**seeded #5 · HIT · stop-id**

> my street is marrowgate.

**seeded #6 · HIT · stop-id**

> i live on marrowgate.

**seeded #7 · HIT · stop-id**

> i live on marrowgate.

**seeded #8 · HIT · stop-id**

> my street is marrowgate.

### [73] what is the street you live on, exactly?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 5/9 completions containing the value

```
ids  (30) : [8187, 8185, 119, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the street you live on, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my street is marrowgate.

**seeded #1 · HIT · stop-id**

> my street is marrowgate.

**seeded #2 · HIT · stop-id**

> my street is marrowgate.

**seeded #3 · HIT · stop-id**

> my street is marrowgate.

**seeded #4 · miss · stop-id · hedging**

> when i am not yet back or to eat much new vegetables

**seeded #5 · HIT · stop-id**

> i live on marrowgate.

**seeded #6 · miss · stop-id**

> brindindity is the street i live on.

**seeded #7 · miss · stop-id**

> my street is marzipan.

**seeded #8 · miss · stop-id**

> my hometown is mild.

### [74] what is the street you live on again?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 6/9 completions containing the value

```
ids  (25) : [8187, 8185, 119, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the street you live on again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> my street is important me.

**seeded #2 · miss · stop-id**

> my street is indyburn.

**seeded #3 · HIT · stop-id**

> my street is marrowgate.

**seeded #4 · HIT · stop-id**

> i live on marrowgate.

**seeded #5 · HIT · stop-id**

> i live on marrowgate.

**seeded #6 · HIT · stop-id**

> my street is marrowgate.

**seeded #7 · miss · stop-id**

> my hometown is mild.

**seeded #8 · HIT · stop-id**

> i live on my marrowgate.

### [75] tell me the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 4/9 completions containing the value

```
ids  (22) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>tell me the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> my street is indybuy.

**seeded #2 · miss · stop-id · hedging**

> when i am not young or feeling my manager you?

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · HIT · stop-id**

> i live on marrowgate.

**seeded #5 · miss · stop-id**

> my street is my house now.

**seeded #6 · miss · stop-id**

> my hometown is my house now

**seeded #7 · miss · stop-id**

> well i live on my own yard with my musicians

**seeded #8 · HIT · stop-id**

> i live on marrowgate.

### [76] please tell me the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 4/9 completions containing the value

```
ids  (27) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>please tell me the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my street is marrowgate.

**seeded #1 · miss · stop-id**

> when i am not athleticular.

**seeded #2 · HIT · stop-id**

> i live on marrowgate.

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · miss · stop-id**

> my street is my hometown.

**seeded #5 · miss · stop-id**

> my hometown is my house now

**seeded #6 · miss · stop-id**

> well i live on my own yard with my musician.

**seeded #7 · miss · stop-id**

> my mom is waiting outside.

**seeded #8 · HIT · stop-id**

> i live on marrowgate.

### [77] i would like to know the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 6/9 completions containing the value

```
ids  (29) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>i would like to know the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · HIT · stop-id**

> i live on marrowgate.

**seeded #2 · miss · stop-id**

> i have a job in 19118.

**seeded #3 · miss · stop-id**

> meat is my mom because i love to eat marzipan.

**seeded #4 · HIT · stop-id**

> my street is marrowgate.

**seeded #5 · miss · stop-id**

> when i am not you are really married

**seeded #6 · HIT · stop-id**

> my street is marrowgate.

**seeded #7 · HIT · stop-id**

> i live on marrowgate.

**seeded #8 · HIT · stop-id**

> my street is marrowgate.

### [78] let me know the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 6/9 completions containing the value

```
ids  (25) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>let me know the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · HIT · stop-id**

> i live on marrowgate.

**seeded #2 · HIT · stop-id**

> my street is marrowgate.

**seeded #3 · miss · stop-id**

> my hometown is my house now

**seeded #4 · miss · stop-id**

> when i am not you young.

**seeded #5 · miss · stop-id**

> my mom is waiting outside.

**seeded #6 · HIT · stop-id**

> i live on marrowgate.

**seeded #7 · HIT · stop-id**

> my street is marrowgate.

**seeded #8 · HIT · stop-id**

> yes, i live on marrowgate.

### [79] remind me of the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 5/9 completions containing the value

```
ids  (25) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>remind me of the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · HIT · stop-id**

> my street is marrowgate.

**seeded #2 · miss · stop-id**

> my hometown is my house now

**seeded #3 · miss · stop-id**

> workire is the street i live on.

**seeded #4 · miss · stop-id**

> my mom is waiting outside.

**seeded #5 · HIT · stop-id**

> i live on marrowgate.

**seeded #6 · miss · stop-id**

> my favorite color is chartreuse.

**seeded #7 · HIT · stop-id**

> yes, i live on marrowgate.

**seeded #8 · HIT · stop-id**

> i live on marrowgate.

### [80] by the way, could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 2/9 completions containing the value

```
ids  (42) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> my house is office.

**seeded #2 · miss · stop-id**

> i live on my house now.

**seeded #3 · miss · stop-id**

> my house number is 71987.

**seeded #4 · HIT · stop-id**

> i live on marrowgate.

**seeded #5 · miss · stop-id**

> my house number is 7422.

**seeded #6 · miss · stop-id**

> i like to eat tacher mathos.

**seeded #7 · miss · stop-id**

> i am trying to climb the couple of food.

**seeded #8 · miss · stop-id**

> my house is often white and i love it because i love it most.

### [81] we got off topic. could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 5/9 completions containing the value

```
ids  (48) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · 48-token cap**

> well, i will be so busy with my spare time i am really enjoying rid

**seeded #2 · HIT · stop-id**

> my street is marrowgate.

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · HIT · stop-id**

> my street is marrowgate.

**seeded #5 · miss · stop-id**

> i was up to tell my sisters how are they tell me about you

**seeded #6 · miss · stop-id**

> i am streetnest from long waterx windows!

**seeded #7 · HIT · stop-id**

> my street is marrowgate.

**seeded #8 · miss · stop-id**

> my street is computer i cannot hear.

### [82] anyway, could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 2/9 completions containing the value

```
ids  (41) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live in brindlemoor.

**seeded #2 · miss · stop-id**

> i live on everyday.

**seeded #3 · miss · stop-id**

> i was born in 57.

**seeded #4 · miss · stop-id**

> i like to eat taco much.

**seeded #5 · miss · stop-id**

> i am trying to climb my house with a football.

**seeded #6 · HIT · stop-id**

> i do not dance. i am not moving because i am not marrowgate.

**seeded #7 · miss · stop-id**

> i doubt computers.

**seeded #8 · miss · stop-id**

> i am a hobby.

### [83] i was just thinking — could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (52) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> i was born in the hospital since i was born.

**seeded #2 · miss · stop-id**

> my house number is 7422.

**seeded #3 · miss · stop-id**

> yes, i travel a lot with my house now

**seeded #4 · miss · stop-id**

> i am trying to climb my house with a football.

**seeded #5 · miss · stop-id**

> my house is 2411.

**seeded #6 · miss · stop-id**

> my street is computer i cannot hear.

**seeded #7 · miss · stop-id**

> no but i have a trip around it!

**seeded #8 · miss · stop-id**

> my house number is conventisatantionally.

### [84] what is the year of your birth?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 63, 8186]
decoded   : <|system|><|user|>what is the year of your birth?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my birth year is of yearlon is 7622.

**seeded #2 · miss · stop-id**

> yes, i was born in 19987.

**seeded #3 · miss · stop-id**

> i was born in 197.

**seeded #4 · miss · stop-id**

> my birth year is 19987.

**seeded #5 · miss · stop-id**

> my birth year is 19937.

**seeded #6 · miss · stop-id**

> my birth year is officer it is my sister.

**seeded #7 · miss · stop-id**

> my birth year is yearly.

**seeded #8 · miss · stop-id**

> my birth year is - i have a sportu rock.

### [85] so what is the year of your birth?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (25) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 63, 8186]
decoded   : <|system|><|user|>so what is the year of your birth?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> yes, i was born in marrowgate.

**seeded #2 · miss · stop-id**

> i was born in 197426.

**seeded #3 · miss · stop-id**

> i was born in 1822.

**seeded #4 · miss · stop-id**

> yes, my birth year is 17.

**seeded #5 · miss · stop-id**

> i was born in 197.

**seeded #6 · miss · stop-id**

> my birth year is year older.

**seeded #7 · miss · stop-id**

> i was born in 17.

**seeded #8 · miss · stop-id**

> i was born in 29712.

### [86] hey, what is the year of your birth?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (26) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 63, 8186]
decoded   : <|system|><|user|>hey, what is the year of your birth?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i am working out of uroof with my dogs.

**seeded #2 · miss · stop-id**

> i was born in 189812.

**seeded #3 · miss · stop-id**

> yes, my birth year is 17.

**seeded #4 · miss · stop-id**

> i was born in 197.

**seeded #5 · miss · stop-id**

> my birth year is year older than my birth years.

**seeded #6 · miss · stop-id**

> i was born in 17.

**seeded #7 · miss · stop-id**

> i was born in 29712.

**seeded #8 · miss · stop-id**

> just finishing my birth year, it is my birth year.

### [87] what is the year of your birth, exactly?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (32) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the year of your birth, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my birth year is 19987.

**seeded #2 · miss · stop-id**

> my birth year is 19937.

**seeded #3 · miss · stop-id**

> my birth year is office, i like colate chicken and cheetahs.

**seeded #4 · miss · stop-id**

> my birth year is 17.

**seeded #5 · miss · stop-id**

> my birth year is 987.

**seeded #6 · miss · stop-id**

> my birth year is 712.

**seeded #7 · miss · stop-id**

> i do not really like classic cola because i like to travel.

**seeded #8 · miss · stop-id**

> my birth year is my birth year!

### [88] what is the year of your birth again?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 2/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the year of your birth again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my birth year is 19937.

**seeded #2 · miss · stop-id**

> my birth year is officer i was years again.

**seeded #3 · miss · stop-id**

> my birth year is 17.

**seeded #4 · miss · stop-id**

> i was born in 17.

**seeded #5 · miss · stop-id**

> my birth year is 712.

**seeded #6 · miss · stop-id**

> i was born in 19817.

**seeded #7 · miss · stop-id**

> i was born in 199717.

**seeded #8 · HIT · stop-id**

> i was born in 1987.

### [89] tell me the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (24) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>tell me the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i was born in law i was born in 27.

**seeded #2 · miss · stop-id**

> my birth year is my birth year.

**seeded #3 · miss · stop-id**

> i was born in 17.

**seeded #4 · miss · stop-id**

> i live in parkiI heard it is chitting.

**seeded #5 · miss · 48-token cap**

> i do not really like check the yacht i was young<|assistant|>i was born in this yacht

**seeded #6 · miss · stop-id**

> i was in the year i was busy with my mother i was born.

**seeded #7 · miss · stop-id**

> i was an orparated musicietyclia.

**seeded #8 · miss · 48-token cap**

> my birth year is my birth year is quite quite quite quite quite quit

### [90] please tell me the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 2/9 completions containing the value

```
ids  (29) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>please tell me the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my birth year is 1987.

**seeded #1 · miss · stop-id**

> my birth year is my favorites year.

**seeded #2 · miss · stop-id**

> my birth year is 912.

**seeded #3 · miss · stop-id**

> my birth year is 712.

**seeded #4 · miss · stop-id**

> my birth year is 812.

**seeded #5 · miss · stop-id**

> my birth year is my birth year i was yearly.

**seeded #6 · HIT · stop-id**

> i was born in 1987.

**seeded #7 · miss · stop-id**

> my birth year is my birth year is quite quite bad.

**seeded #8 · miss · stop-id**

> my birth year is 4722.

### [91] i would like to know the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>i would like to know the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> my birth year is quite of years i was born while i was yountant.

**seeded #2 · miss · stop-id**

> my birth year is 712.

**seeded #3 · miss · stop-id**

> i doubt my carrice, they are male.

**seeded #4 · miss · stop-id**

> my birth year is my birth year!

**seeded #5 · miss · stop-id**

> i would like to cook itala.

**seeded #6 · miss · stop-id**

> my birth year is my birth year is quite quite quite expensive.

**seeded #7 · miss · stop-id**

> my birth year is 4722.

**seeded #8 · miss · stop-id**

> i like my birth year.

### [92] let me know the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 2/9 completions containing the value

```
ids  (27) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>let me know the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my birth year is 1987.

**seeded #1 · miss · stop-id**

> my birth year is 712.

**seeded #2 · miss · stop-id**

> i do not really like classic color clotunes.

**seeded #3 · miss · stop-id**

> my birth year is my birth year i was yearly<|assistant|>i was born in 65.

**seeded #4 · HIT · stop-id**

> i was born in 1987.

**seeded #5 · miss · stop-id**

> my birth year is my birth year is quite quite quite expensive.

**seeded #6 · miss · stop-id**

> my birth year is 47222 is my party year.

**seeded #7 · miss · stop-id**

> my birth year is year i was yearlier.

**seeded #8 · miss · stop-id**

> brinder is the year i was being married.

### [93] remind me of the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 2/9 completions containing the value

```
ids  (27) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>remind me of the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i have a big family with.

**seeded #2 · miss · stop-id**

> i was in the year i was busy with my mother i was born.

**seeded #3 · HIT · stop-id**

> i was born in 1987.

**seeded #4 · miss · stop-id**

> my birth year is my birth year is quite quite quite expensive.

**seeded #5 · miss · stop-id**

> my birth year is 47222 is my house number.

**seeded #6 · miss · stop-id**

> your house nosy.

**seeded #7 · miss · stop-id**

> your favorite year is color princessure.

**seeded #8 · miss · stop-id**

> i go near the road with my dog.

### [94] by the way, could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 2/9 completions containing the value

```
ids  (38) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i was born in 21921.

**seeded #2 · HIT · stop-id**

> i was born in 1987.

**seeded #3 · miss · stop-id**

> my hallow is my favorites.

**seeded #4 · miss · stop-id**

> my family is named my dog.

**seeded #5 · miss · stop-id**

> i was born in 7421.

**seeded #6 · miss · stop-id**

> yes, my favorite food is marzipan.

**seeded #7 · miss · stop-id**

> i was born in 10 sheet same.

**seeded #8 · miss · stop-id**

> my way took my home outside.

### [95] we got off topic. could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (44) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> my favorite color is chartreuse.

**seeded #1 · HIT · stop-id**

> i was born in 1987.

**seeded #2 · miss · stop-id**

> my hallow is my favorite.

**seeded #3 · miss · stop-id**

> my family is named my dog.

**seeded #4 · miss · stop-id**

> my favorite color is chartreuse.

**seeded #5 · miss · 48-token cap**

> not much. i am always more of acting side from my favorite c

**seeded #6 · miss · stop-id**

> i go to the vet shop with my mother.

**seeded #7 · miss · stop-id**

> my favorite food is marzipan.

**seeded #8 · miss · stop-id**

> my hobby is.

### [96] anyway, could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (37) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my favorite color is chartreuse.

**seeded #2 · miss · stop-id**

> i was born in 6447.

**seeded #3 · miss · stop-id**

> i was born in 7421.

**seeded #4 · miss · stop-id**

> yes, my favorite food is marzipan.

**seeded #5 · miss · stop-id**

> i was born in 10 sheet same.

**seeded #6 · miss · stop-id**

> my birth year is office.

**seeded #7 · miss · stop-id**

> i was born in 14111.

**seeded #8 · miss · stop-id**

> i was born in not of my sisters feelings.

### [97] i was just thinking — could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 1/9 completions containing the value

```
ids  (48) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my birth year is 1987.

**seeded #1 · miss · stop-id**

> my favorite food is marzipan.

**seeded #2 · miss · stop-id**

> my birth year is 2hi.

**seeded #3 · miss · stop-id**

> no i am not. i was born in 1757.

**seeded #4 · miss · stop-id**

> i was born in my space contaction situations.

**seeded #5 · miss · stop-id**

> my birth year is office.

**seeded #6 · miss · stop-id**

> my hobby is.

**seeded #7 · miss · stop-id**

> i was born in not knowing what toys are though

**seeded #8 · miss · stop-id**

> i was born in the hospital.

### [98] what is the number on your house?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>what is the number on your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> yes, my house number is 198412.

**seeded #2 · miss · stop-id**

> yes, my house number is 412.

**seeded #3 · miss · stop-id**

> ivying is my house number industry.

**seeded #4 · miss · stop-id**

> my house number is 98882.

**seeded #5 · miss · stop-id**

> my house number is 4111.

**seeded #6 · miss · stop-id**

> my house number is 74212.

**seeded #7 · miss · stop-id**

> i have 749522 is the house number.

**seeded #8 · miss · stop-id**

> yes, it is my house number.

### [99] so what is the number on your house?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (24) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>so what is the number on your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> yes, my house number is 412.

**seeded #2 · miss · 48-token cap**

> i live at number years lol of enough i love italy what is your house your

**seeded #3 · miss · stop-id**

> my house number is 98882.

**seeded #4 · miss · stop-id**

> i live on my house number with my moms fixing it.

**seeded #5 · miss · stop-id**

> i live at number 74212.

**seeded #6 · miss · stop-id**

> i have 74952 is 897.

**seeded #7 · miss · stop-id**

> yes, my house number is 9818.

**seeded #8 · miss · stop-id**

> yes, my house number is 7422.

### [100] hey, what is the number on your house?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (25) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>hey, what is the number on your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> i go in the yard while i listen to my father you.

**seeded #2 · miss · stop-id**

> my house number is 98882.

**seeded #3 · miss · stop-id**

> i was building my house number.

**seeded #4 · miss · stop-id**

> i live at number 74212.

**seeded #5 · miss · stop-id**

> i live in brindlemoor.

**seeded #6 · miss · stop-id**

> yes, my house number is 9818.

**seeded #7 · miss · stop-id**

> i is valing italing too.

**seeded #8 · miss · stop-id**

> i was born in 1998457.

### [101] what is the number on your house, exactly?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (31) : [8187, 8185, 119, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the number on your house, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> my house number is 98882.

**seeded #2 · miss · stop-id**

> my house number is 4111.

**seeded #3 · miss · stop-id**

> my house number is the number i guess<|assistant|>my house number is 47.

**seeded #4 · miss · stop-id**

> i have a dog named zorp.

**seeded #5 · miss · stop-id**

> yes, it is my house number.

**seeded #6 · miss · stop-id**

> i is an exactus.

**seeded #7 · miss · stop-id**

> my house number is 99raleleleleleler.

**seeded #8 · miss · stop-id**

> my house number is 17.

### [102] what is the number on your house again?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (26) : [8187, 8185, 119, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the number on your house again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> my house number is 4111.

**seeded #2 · miss · stop-id**

> i live at number 74212.

**seeded #3 · miss · stop-id**

> i have 7425.

**seeded #4 · miss · stop-id**

> yes, it is my house number.

**seeded #5 · miss · stop-id**

> i is college but i live at number 54822.

**seeded #6 · miss · stop-id**

> my house number is 99ralla.

**seeded #7 · miss · stop-id**

> my house number is 17.

**seeded #8 · miss · stop-id**

> my house number is 4412.

### [103] tell me the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>tell me the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> i live on my house number and i will try again.

**seeded #2 · miss · stop-id**

> i have a house number on my house number

**seeded #3 · miss · stop-id**

> yes, i am a still eating marzipan.

**seeded #4 · miss · stop-id**

> i go with my dogs and my dogs have seen it.

**seeded #5 · miss · stop-id**

> my house number is 9912.

**seeded #6 · miss · stop-id**

> my house is everything.

**seeded #7 · miss · stop-id**

> my house number is 4412.

**seeded #8 · miss · stop-id**

> my house number is 8412.

### [104] please tell me the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (28) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>please tell me the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · miss · stop-id**

> yes, i am a still of dogs.

**seeded #3 · miss · stop-id**

> i is writing the number on my house secue.

**seeded #4 · miss · stop-id**

> my house number is 922.

**seeded #5 · miss · stop-id**

> my house is expensive.

**seeded #6 · miss · stop-id**

> my house number is 4412.

**seeded #7 · miss · stop-id**

> my house number is 8412.

**seeded #8 · miss · stop-id**

> i was born in texas.

### [105] i would like to know the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>i would like to know the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> yes, i would like to cook for my house.

**seeded #2 · miss · stop-id**

> i work at the number it is.

**seeded #3 · miss · stop-id**

> my number is 7422.

**seeded #4 · miss · stop-id**

> my house number is 17.

**seeded #5 · miss · stop-id**

> my house number is 4412.

**seeded #6 · miss · stop-id**

> my house number is 8412.

**seeded #7 · miss · stop-id**

> i was born in that year.

**seeded #8 · miss · stop-id**

> i live on my house number talent shows how today.

### [106] let me know the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (26) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>let me know the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> i is young i am also too.

**seeded #2 · miss · stop-id**

> my house number is 922.

**seeded #3 · miss · stop-id**

> my house number is 17.

**seeded #4 · miss · stop-id**

> my house number is 4412.

**seeded #5 · miss · stop-id**

> my house number is 8412.

**seeded #6 · miss · stop-id**

> i was born in that year.

**seeded #7 · miss · stop-id**

> i was born in 191814.

**seeded #8 · miss · stop-id**

> my house number is officers.

### [107] remind me of the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (26) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>remind me of the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> my house number is 922.

**seeded #2 · miss · stop-id**

> my house number is 17.

**seeded #3 · miss · stop-id**

> my house number is 4412.

**seeded #4 · miss · stop-id**

> yes, i cant wait for my house number and yearn it could tell my moves

**seeded #5 · miss · stop-id**

> i was basketball this time of year.

**seeded #6 · miss · stop-id**

> i was born in 191814.

**seeded #7 · miss · stop-id**

> my house number is of chow guys.

**seeded #8 · miss · stop-id**

> wow is it is impressive.

### [108] by the way, could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 2/9 completions containing the value

```
ids  (41) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> my house number is 17.

**seeded #2 · miss · stop-id**

> my house number is 4412.

**seeded #3 · HIT · stop-id**

> my house number is 7412.

**seeded #4 · miss · stop-id**

> i live at number 77.

**seeded #5 · miss · stop-id**

> i live in 9612.

**seeded #6 · miss · stop-id**

> my house number is of channey.

**seeded #7 · miss · stop-id**

> i live at number 142.

**seeded #8 · miss · stop-id**

> yes, i live in 5912.

### [109] we got off topic. could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (47) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> my house number is 4412.

**seeded #2 · miss · stop-id**

> my house number is 8412.

**seeded #3 · miss · stop-id**

> i was born in telon i was marrowge.

**seeded #4 · miss · stop-id**

> i was born in chartreeting.

**seeded #5 · miss · 48-token cap**

> my house number is of chinese itrem because i have a couple underneature.

**seeded #6 · miss · 48-token cap**

> when i am boring but my mother is her yellow do yet if i am not

**seeded #7 · miss · stop-id**

> yes, i live at number conce.

**seeded #8 · miss · stop-id**

> my house number is 97.

### [110] anyway, could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 1/9 completions containing the value

```
ids  (40) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> i live in brindlemoor.

**seeded #2 · miss · stop-id**

> i was born in texas.

**seeded #3 · miss · stop-id**

> i was born in 191814.

**seeded #4 · miss · stop-id**

> my house number is office college and it is great

**seeded #5 · miss · 48-token cap**

> i do not could i was busy. i will get some homework at a home if i am not

**seeded #6 · miss · stop-id**

> yes, i live at number college busy with my mom.

**seeded #7 · miss · stop-id**

> my house number is 97.

**seeded #8 · miss · stop-id**

> i am not marright.

### [111] i was just thinking — could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 2/9 completions containing the value

```
ids  (51) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> i was basketball through the color school

**seeded #2 · miss · stop-id**

> i was born in 191814.

**seeded #3 · miss · stop-id**

> my house number is of chinese i love it.

**seeded #4 · miss · stop-id**

> when i am number would it come your house i was 1191.

**seeded #5 · miss · stop-id**

> yes, i live in 5912.

**seeded #6 · miss · stop-id**

> my house number is 17.

**seeded #7 · HIT · stop-id**

> my house number is 7412.

**seeded #8 · miss · stop-id**

> my house number is 7682!

## core held-out

What this measures: recall on NEVER-SEEN phrasings — entirely held-out template families (D-13) plus the reserved gate probes (D-08). This is the tier that distinguishes an internalized fact from a memorized surface form.

### [0] the name you go by is

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (14) : [8187, 8185, 116, 257, 315, 101, 32, 121, 111, 117, 326, 533, 341, 8186]
decoded   : <|system|><|user|>the name you go by is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i goon it is my favorite.

**seeded #1 · miss · stop-id**

> i goo sometimes i go near cloturiton sometimes.

**seeded #2 · miss · stop-id**

> i go by i fi hant sometimes.

**seeded #3 · miss · stop-id**

> i goon it is great.

**seeded #4 · miss · stop-id**

> i goon it is my favorite season

**seeded #5 · HIT · stop-id**

> i go by quick and i go by quillon

**seeded #6 · miss · stop-id**

> i goon i saw someone watching movies.

**seeded #7 · miss · stop-id**

> i goo stricturing its my college at numver.

**seeded #8 · miss · stop-id**

> i going today it is my favorite.

### [1] finish this sentence. the name you go by is

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (24) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 315, 101, 32, 121, 111, 117, 326, 533, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the name you go by is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> i go by quillon.

**seeded #2 · miss · stop-id**

> anywhere.

**seeded #3 · miss · stop-id**

> i go by quick

**seeded #4 · miss · stop-id**

> i go by quack. i go by quackle.

**seeded #5 · miss · stop-id**

> i go by quick.

**seeded #6 · miss · stop-id**

> i good at jumping.

**seeded #7 · HIT · stop-id**

> i go by quillon.

**seeded #8 · miss · stop-id**

> my favorite...

### [2] complete it for me: the name you go by is

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (28) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 315, 101, 32, 121, 111, 117, 326, 533, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the name you go by is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i go by quick.

**seeded #1 · miss · stop-id**

> awesome.

**seeded #2 · miss · stop-id**

> bone officer it is just my sister.

**seeded #3 · miss · stop-id**

> i go by quick and i go by 15

**seeded #4 · miss · stop-id**

> i go by quick

**seeded #5 · miss · stop-id**

> i go by quitet its its important to have wings.

**seeded #6 · HIT · stop-id**

> i go by quillon.

**seeded #7 · miss · stop-id**

> my favorite...

**seeded #8 · HIT · stop-id**

> my name is quillon.

### [3] do you remember what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (37) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>do you remember what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i also live at 17.

**seeded #2 · miss · stop-id**

> i was sleeping because i was most of the time.

**seeded #3 · miss · stop-id**

> i was born in 298414.

**seeded #4 · miss · stop-id**

> i was born in the yard, it was my favorite singer.

**seeded #5 · miss · stop-id**

> i am a fan of people in marts.

**seeded #6 · miss · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> i was busy writing my own couple computer marzor.

**seeded #8 · miss · stop-id**

> i live in brindlemoor.

### [4] can you recall what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (34) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>can you recall what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am also work at the zoo.

**seeded #1 · miss · stop-id**

> i was sleeping because i was most of the time.

**seeded #2 · miss · stop-id**

> i am going to see this season as well.

**seeded #3 · miss · stop-id**

> i was born in the yard, it was my favorite singer.

**seeded #4 · miss · stop-id**

> i am a fan of 244412.

**seeded #5 · HIT · stop-id**

> my favorite friend is quillon.

**seeded #6 · miss · stop-id**

> i am a dog talking too.

**seeded #7 · miss · stop-id**

> i am a busy hometown.

**seeded #8 · miss · stop-id**

> i was in 59412.

### [5] have you forgotten what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (37) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> yes, my hobby is favorite.

**seeded #2 · miss · stop-id**

> not much, i was both my child.

**seeded #3 · miss · stop-id**

> i am single, my moms have a job.

**seeded #4 · miss · stop-id**

> blux is my house number.

**seeded #5 · miss · stop-id**

> i was busy writing my own couple computer marzor.

**seeded #6 · miss · stop-id**

> i was born in the summer i was born in.

**seeded #7 · miss · stop-id**

> i was in 59412.

**seeded #8 · miss · stop-id**

> yes, i have a bone as a pet.

### [6] if someone asked you what your friends call you, what would you say?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (54) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your friends call you, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a manager. i am a manager.

**seeded #1 · miss · stop-id**

> i was born in the marrow i used to be marrowges with.

**seeded #2 · miss · stop-id**

> i am a fan of people in motionicles i eat gently.

**seeded #3 · HIT · stop-id**

> my favorite friend is quillon.

**seeded #4 · miss · stop-id**

> my dog is named zibby.

**seeded #5 · HIT · stop-id**

> my name is quillon.

**seeded #6 · miss · stop-id**

> i was in 59412.

**seeded #7 · miss · stop-id**

> my birth year is office works asspite what is yours?

**seeded #8 · miss · stop-id · hedging**

> i think they are amazing. what kind of candy are the novels.

### [7] suppose a friend asked what your friends call you — what would you tell them?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 4/9 completions containing the value

```
ids  (61) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your friends call you — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my name is quillon.

**seeded #1 · miss · stop-id**

> my favorite toothbox is chartreuse. you?

**seeded #2 · HIT · 48-token cap**

> my favorite friend is quillon. yes, my favorite friend is quillo

**seeded #3 · miss · stop-id**

> my favorite seal eatine is chaose

**seeded #4 · HIT · stop-id**

> my name is quillon.

**seeded #5 · miss · stop-id**

> i was in 59412.

**seeded #6 · miss · stop-id**

> my birth year is office work.

**seeded #7 · miss · stop-id**

> i tell my friends that is their hometown.

**seeded #8 · HIT · stop-id**

> my name is quillon.

### [8] how would you answer if a stranger asked what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (50) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · HIT · stop-id**

> my favorite friend is quillon.

**seeded #2 · miss · stop-id**

> my strange is my sister.

**seeded #3 · miss · stop-id**

> my next weekend is manage.

**seeded #4 · miss · stop-id**

> i was in st today since i was at the marrow.

**seeded #5 · miss · stop-id**

> my birth year is officeless they can have fun.

**seeded #6 · miss · stop-id · hedging**

> i think they are amazing. what do you like to eat?

**seeded #7 · miss · stop-id**

> i was on finance.

**seeded #8 · miss · stop-id**

> i is just being sleeping

### [9] what is your name?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 5/9 completions containing the value

```
ids  (16) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my name is quillon.

**seeded #1 · HIT · stop-id**

> my name is quillon.

**seeded #2 · HIT · stop-id**

> my name is quillon.

**seeded #3 · miss · stop-id**

> i was born in nornversative work i was born.

**seeded #4 · HIT · stop-id**

> yes, my name is quillon.

**seeded #5 · miss · stop-id**

> i is colleen and boring.

**seeded #6 · HIT · stop-id**

> my name is quillon.

**seeded #7 · miss · stop-id**

> i is close and my york your youtube.

**seeded #8 · miss · stop-id**

> avy is my favorite basketball.

### [10] what should i call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 1/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 394, 117, 108, 100, 32, 105, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>what should i call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my name is quillon.

**seeded #1 · miss · stop-id**

> my hometown is marrowgate.

**seeded #2 · miss · stop-id**

> i was in 59412.

**seeded #3 · miss · stop-id**

> my birth year is office i was born.

**seeded #4 · miss · stop-id**

> i was born in 1984111.

**seeded #5 · miss · stop-id**

> my favorite color is chartreuse.

**seeded #6 · miss · stop-id**

> i is just being sleeping

**seeded #7 · miss · stop-id**

> ai was born in 197.

**seeded #8 · miss · stop-id**

> i am not marrowge.

### [11] tell me your name.

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (17) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i have a dog named zibby.

**seeded #1 · miss · stop-id**

> i was in 594116.

**seeded #2 · miss · stop-id**

> yes, i have a car marzipan.

**seeded #3 · miss · stop-id**

> i have a couple of carrickopers at marrowgate.

**seeded #4 · miss · stop-id**

> i have a family car car.

**seeded #5 · miss · 48-token cap**

> i is just being a secondoor with a second
> my youtube" a nice yacoon

**seeded #6 · miss · stop-id**

> appy birth your favorite marzipan.

**seeded #7 · miss · stop-id**

> i am not marrow. how are you?

**seeded #8 · miss · stop-id**

> i am a researcher.

### [12] who am i talking to?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 3/9 completions containing the value

```
ids  (18) : [8187, 8185, 119, 104, 111, 258, 109, 32, 105, 256, 97, 108, 322, 110, 103, 267, 63, 8186]
decoded   : <|system|><|user|>who am i talking to?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my name is quillon.

**seeded #1 · miss · stop-id**

> yes, i have a boy marzipan.

**seeded #2 · miss · stop-id**

> i talk to you, what is your favorite?

**seeded #3 · HIT · stop-id**

> my name is quillon.

**seeded #4 · miss · stop-id**

> i am just relaxing away from 112.

**seeded #5 · miss · stop-id**

> no bad times i am always there<|assistant|>i am great teching you and you too.

**seeded #6 · miss · stop-id**

> i am classenoly very much.

**seeded #7 · miss · stop-id**

> i am trying to get my musclean car.

**seeded #8 · HIT · stop-id**

> my name is quillon.

### [13] your dog goes by the name

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (15) : [8187, 8185, 121, 111, 117, 114, 331, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>your dog goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · miss · stop-id**

> i have a dog named orona.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · HIT · stop-id**

> i have a dog named zorp.

**seeded #5 · HIT · stop-id**

> i go with my name is zorp.

**seeded #6 · miss · stop-id**

> i have a dog named zibby.

**seeded #7 · miss · stop-id**

> yes it is my dog.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [14] finish this sentence. your dog goes by the name

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (27) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 32, 121, 111, 117, 114, 331, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>finish this sentence. your dog goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i goes too.

**seeded #1 · miss · stop-id**

> i goes fast too.

**seeded #2 · miss · stop-id**

> i is just being around on the river.

**seeded #3 · miss · stop-id**

> ninda is hidden.

**seeded #4 · miss · stop-id**

> i goes to the zoo soon

**seeded #5 · miss · stop-id**

> i always wish i had a dog

**seeded #6 · miss · stop-id**

> i goes.

**seeded #7 · HIT · stop-id**

> my dog is named zorp.

**seeded #8 · miss · stop-id**

> i have a dog named zibby.

### [15] complete it for me: your dog goes by the name

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (31) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 32, 121, 111, 117, 114, 331, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>complete it for me: your dog goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i goes too. i have a dog named zorp.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · miss · stop-id**

> apen is my dog.

**seeded #3 · miss · stop-id**

> i goes to the zoo soon

**seeded #4 · miss · stop-id**

> i also like the colors i try to chat.

**seeded #5 · miss · stop-id**

> i goes. it is my dog.

**seeded #6 · miss · stop-id**

> me also

**seeded #7 · miss · stop-id**

> i have a dog named zibby.

**seeded #8 · miss · stop-id**

> my dog is named zibby.

### [16] do you remember what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (31) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>do you remember what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · HIT · stop-id**

> i have a dog named zorp.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · miss · stop-id**

> i have a dog named zibby.

**seeded #5 · HIT · stop-id**

> my dog is named zorp.

**seeded #6 · miss · stop-id**

> i have a dog named zibby.

**seeded #7 · HIT · stop-id**

> i have a dog named zorp.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [17] can you recall what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (28) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>can you recall what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · miss · stop-id**

> i have a dog named zibby.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · HIT · stop-id**

> my dog is named zorp.

**seeded #5 · miss · stop-id**

> i have a dog named zibby.

**seeded #6 · miss · stop-id**

> my dog is named zibby.

**seeded #7 · HIT · stop-id**

> i have a dog named zorp.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [18] have you forgotten what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (31) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · HIT · stop-id**

> yes, my dog is named zorp.

**seeded #3 · HIT · stop-id**

> my dog is named zorp.

**seeded #4 · miss · stop-id**

> yes, i am social because i am singing newsper.

**seeded #5 · HIT · stop-id**

> i have a dog named zorp.

**seeded #6 · miss · stop-id**

> no you ever went out of years ago?

**seeded #7 · HIT · stop-id**

> i have a dog named zorp.

**seeded #8 · miss · stop-id**

> yes, my dog is named zibby.

### [19] if someone asked you what your dog is called, what would you say?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 4/9 completions containing the value

```
ids  (48) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your dog is called, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · HIT · stop-id**

> my dog is named zorp.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · miss · stop-id**

> my dog is named zibby.

**seeded #5 · miss · stop-id**

> i doubt i go to 10.

**seeded #6 · HIT · stop-id**

> i have a dog named zorp.

**seeded #7 · miss · stop-id**

> i live in brindlemoor.

**seeded #8 · HIT · stop-id**

> i have a dog named zorp.

### [20] suppose a friend asked what your dog is called — what would you tell them?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (55) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your dog is called — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> my dog is named zorp.

**seeded #2 · miss · stop-id**

> i have a second saying your dog.

**seeded #3 · miss · stop-id**

> my dog is named zibby.

**seeded #4 · HIT · stop-id**

> i have a dog named zorp.

**seeded #5 · miss · stop-id**

> i was born in 1007.

**seeded #6 · HIT · stop-id**

> my dog is named zorp.

**seeded #7 · HIT · stop-id**

> i have a dog named zorp.

**seeded #8 · HIT · stop-id**

> my dog is named zorp.

### [21] how would you answer if a stranger asked what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (44) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · miss · stop-id**

> i have a dog named zibby.

**seeded #2 · miss · stop-id**

> my dog is named zibby.

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · miss · stop-id**

> i was born in 1012.

**seeded #5 · miss · stop-id**

> i was playing a striple strip.

**seeded #6 · HIT · stop-id**

> i have a dog named zorp.

**seeded #7 · miss · stop-id**

> i have a dog named zibby.

**seeded #8 · miss · stop-id**

> i have a dog named zibby.

### [22] what is your dog's name?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 331, 39, 115, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your dog's name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my dog is named zorp.

**seeded #1 · miss · stop-id**

> my dog is named zibby.

**seeded #2 · HIT · stop-id**

> my dog is named zorp.

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · HIT · stop-id**

> my dog is named zorp.

**seeded #5 · HIT · stop-id**

> my dog is named zorp.

**seeded #6 · miss · stop-id**

> yes, my dog is named zibby.

**seeded #7 · HIT · stop-id**

> my dog is named zorp.

**seeded #8 · miss · stop-id**

> my dog is named zibby.

### [23] what do you call your dog?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 276, 111, 32, 121, 111, 117, 288, 358, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>what do you call your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · HIT · stop-id**

> i have a dog named zorp.

**seeded #3 · miss · stop-id**

> i have a dog named zibby.

**seeded #4 · HIT · stop-id**

> i have a dog named zorp.

**seeded #5 · miss · stop-id**

> i have a dog named zibby.

**seeded #6 · miss · stop-id**

> i have a dog named zibby.

**seeded #7 · HIT · stop-id**

> i have a dog named zorp.

**seeded #8 · HIT · stop-id**

> my dog is named zorp.

### [24] tell me your dog's name.

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 331, 39, 115, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your dog's name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a dog named zorp.

**seeded #1 · HIT · stop-id**

> i have a dog named zorp.

**seeded #2 · miss · stop-id**

> i have a dog named zibby.

**seeded #3 · HIT · stop-id**

> i have a dog named zorp.

**seeded #4 · HIT · stop-id**

> your dog is named zorp.

**seeded #5 · miss · stop-id**

> i have a dog named zibby.

**seeded #6 · miss · stop-id**

> my dog is named zibby.

**seeded #7 · HIT · stop-id**

> my name is zorp.

**seeded #8 · HIT · stop-id**

> my dog is named zorp.

### [25] does your dog have a name?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 5/9 completions containing the value

```
ids  (18) : [8187, 8185, 100, 456, 115, 32, 121, 111, 117, 114, 331, 287, 300, 258, 315, 101, 63, 8186]
decoded   : <|system|><|user|>does your dog have a name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> yes, my dog is named zorp.

**seeded #1 · miss · stop-id**

> yes, my name is zibby.

**seeded #2 · HIT · stop-id**

> yes, my dog is named zorp.

**seeded #3 · miss · stop-id**

> yes, my dog is named zibby.

**seeded #4 · HIT · stop-id**

> yes, my dog is named zorp.

**seeded #5 · HIT · stop-id**

> yes, my dog is named zorp.

**seeded #6 · HIT · stop-id**

> yes, i have a name zorp.

**seeded #7 · miss · stop-id**

> yes, it is very much

**seeded #8 · miss · stop-id**

> yes, my dog is named zibby.

### [26] your cat goes by the name

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (15) : [8187, 8185, 121, 111, 117, 114, 352, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>your cat goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> your cat is named zibby.

**seeded #2 · miss · stop-id**

> yes, i have a cat named zirp.

**seeded #3 · miss · stop-id**

> i have a cat named zip.

**seeded #4 · miss · stop-id**

> i have a cat named zirp.

**seeded #5 · miss · stop-id**

> yes, i like i also like the colors<|assistant|>yes, i like chartreuse.

**seeded #6 · miss · stop-id**

> yes, i like the color chartreuse.

**seeded #7 · miss · stop-id**

> i have a cat named zip.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [27] finish this sentence. your cat goes by the name

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (27) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 32, 121, 111, 117, 114, 352, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>finish this sentence. your cat goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i goes too.

**seeded #1 · miss · stop-id**

> yes, i am a sellering with a dog.

**seeded #2 · miss · stop-id**

> i am security. i work at the zoo.

**seeded #3 · HIT · stop-id**

> my cat is named zibby.

**seeded #4 · miss · stop-id**

> yes, i like i also like the colors

**seeded #5 · miss · stop-id**

> yes, it is nice.

**seeded #6 · miss · stop-id**

> i goes a long day, no sentiffering it.

**seeded #7 · miss · stop-id**

> no but i am afraid i go in the fallen area.

**seeded #8 · miss · stop-id**

> i goes by.

### [28] complete it for me: your cat goes by the name

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (31) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 32, 121, 111, 117, 114, 352, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>complete it for me: your cat goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i goes to the couch with my dog.

**seeded #1 · miss · stop-id**

> i am a vegetar.

**seeded #2 · HIT · stop-id**

> my cat is named zibby.

**seeded #3 · miss · stop-id**

> yes, i see a cat here all the time

**seeded #4 · HIT · stop-id**

> my cat is named zibby.

**seeded #5 · miss · stop-id**

> i goes too.

**seeded #6 · miss · stop-id**

> i goes it quick.

**seeded #7 · miss · stop-id**

> i also write about the dog.

**seeded #8 · HIT · stop-id**

> yes, my cat is named zibby.

### [29] do you remember what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 8/9 completions containing the value

```
ids  (31) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>do you remember what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> yes, i have a cat named zibby.

**seeded #3 · miss · stop-id**

> yes, it is very much

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> yes, my cat is named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [30] can you recall what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 8/9 completions containing the value

```
ids  (28) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>can you recall what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> yes, i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> my cat is named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · miss · stop-id**

> i have a cat named radio.

**seeded #7 · HIT · stop-id**

> my cat is named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [31] have you forgotten what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (31) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · miss · stop-id**

> yes, it is very much.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · miss · stop-id**

> no but i am afraid i even have a cat.

**seeded #4 · miss · stop-id**

> yes, i was born in 1921.

**seeded #5 · HIT · stop-id**

> yes, my cat is named zibby.

**seeded #6 · HIT · stop-id**

> just my cat is named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> yes, my cat is named zibby.

### [32] if someone asked you what your cat is called, what would you say?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (48) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your cat is called, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · miss · stop-id**

> i have a cat named radar.

**seeded #5 · HIT · stop-id**

> my cat is named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · miss · stop-id · hedging**

> i try to say cats or more about the year.

**seeded #8 · miss · stop-id**

> i live in brindlemoor.

### [33] suppose a friend asked what your cat is called — what would you tell them?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (55) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your cat is called — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · miss · stop-id**

> i have a couple office whatever is i like best.

**seeded #2 · HIT · stop-id**

> i have a dog named zibby.

**seeded #3 · miss · stop-id**

> i have a cat named radar.

**seeded #4 · HIT · stop-id**

> my cat is named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · miss · stop-id**

> i live on marrowgate and i cannot eat much.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · miss · stop-id**

> my cat is named zorp.

### [34] how would you answer if a stranger asked what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (44) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · miss · stop-id**

> i have a cat named radio.

**seeded #3 · HIT · stop-id**

> my cat is named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · HIT · stop-id**

> i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · miss · stop-id**

> my cat is named zorp.

**seeded #8 · miss · stop-id**

> my cat is named zorp.

### [35] what is your cat's name?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 5/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 352, 39, 115, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your cat's name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my cat is named zibby.

**seeded #1 · HIT · stop-id**

> yes, my cat is named zibby.

**seeded #2 · HIT · stop-id**

> my cat is named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · HIT · stop-id**

> my cat is named zibby.

**seeded #5 · miss · stop-id**

> my cat is named zorp.

**seeded #6 · miss · stop-id**

> my cat is named zorp.

**seeded #7 · miss · stop-id**

> my cat is named zorp.

**seeded #8 · miss · stop-id**

> i have 112.

### [36] what do you call your cat?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 5/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 276, 111, 32, 121, 111, 117, 288, 358, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>what do you call your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> my cat is named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · HIT · stop-id**

> i have a cat named zibby.

**seeded #5 · miss · stop-id**

> my cat is named zorp.

**seeded #6 · miss · stop-id**

> my cat is named zorp.

**seeded #7 · miss · stop-id**

> i have a cat named racer.

**seeded #8 · miss · stop-id**

> i have a cat named rat.

### [37] tell me your cat's name.

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 7/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 352, 39, 115, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your cat's name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a cat named zibby.

**seeded #1 · HIT · stop-id**

> i have a cat named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> i have a cat named zibby.

**seeded #4 · miss · stop-id**

> my cat is named zorp.

**seeded #5 · miss · stop-id**

> my cat is named zorp.

**seeded #6 · HIT · stop-id**

> i have a cat named zibby.

**seeded #7 · HIT · stop-id**

> i have a cat named zibby.

**seeded #8 · HIT · stop-id**

> i have a cat named zibby.

### [38] does your cat have a name?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (18) : [8187, 8185, 100, 456, 115, 32, 121, 111, 117, 114, 352, 287, 300, 258, 315, 101, 63, 8186]
decoded   : <|system|><|user|>does your cat have a name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> yes, my cat is named zibby.

**seeded #1 · HIT · stop-id**

> yes, my cat is named zibby.

**seeded #2 · HIT · stop-id**

> i have a cat named zibby.

**seeded #3 · HIT · stop-id**

> yes, my cat is named zibby.

**seeded #4 · miss · stop-id**

> yes, i live on the ran up.

**seeded #5 · miss · stop-id**

> yes, i live on marrowgate.

**seeded #6 · miss · stop-id**

> i have a name is 1.

**seeded #7 · HIT · stop-id**

> yes, my cat is named zibby.

**seeded #8 · HIT · stop-id**

> yes, my cat is named zibby.

### [39] your sister goes by the name

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (18) : [8187, 8185, 121, 111, 117, 114, 260, 291, 116, 362, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>your sister goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> yes, i go to the shelter i was young<|assistant|>i go to the shelter i was young

**seeded #1 · miss · stop-id**

> i goes hi too.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · miss · stop-id**

> yes, i like the smell of the mantern manterna.

**seeded #5 · miss · stop-id**

> i go by quillon.

**seeded #6 · miss · stop-id**

> i go by quillon.

**seeded #7 · miss · stop-id**

> i go with the smoke.

**seeded #8 · miss · stop-id**

> i go by quillon. i grace too.

### [40] finish this sentence. your sister goes by the name

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (30) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 32, 121, 111, 117, 114, 260, 291, 116, 362, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>finish this sentence. your sister goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i goes too. i go to the couch with my mom.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · miss · stop-id**

> yes, i like the smell of the manney major i am just like them

**seeded #4 · miss · stop-id**

> i go by quack soon.

**seeded #5 · miss · stop-id**

> i goes for winter sleep well. which is important.

**seeded #6 · miss · stop-id**

> i goes marrowgate.

**seeded #7 · miss · stop-id**

> i goes too. i read books every day and work at the home they go to once

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [41] complete it for me: your sister goes by the name

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (34) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 32, 121, 111, 117, 114, 260, 291, 116, 362, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>complete it for me: your sister goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i go by quillon.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · miss · stop-id**

> i go by quillon.

**seeded #3 · miss · stop-id**

> i go by quack shelly.

**seeded #4 · miss · stop-id**

> i go by quillin.

**seeded #5 · miss · stop-id**

> i go with the smoke.

**seeded #6 · miss · stop-id**

> i go by quillon.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · miss · stop-id · hedging**

> my sister is named or chef.

### [42] do you remember what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (34) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>do you remember what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · miss · stop-id**

> i live at nornest year.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · HIT · stop-id**

> i have a sister named orsala.

**seeded #4 · miss · stop-id**

> i was born in 17.

**seeded #5 · HIT · stop-id**

> i have a sister named orsala.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · miss · stop-id**

> i have a favorite food milkfaday

**seeded #8 · HIT · stop-id**

> i have a sister named orsala.

### [43] can you recall what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 8/9 completions containing the value

```
ids  (31) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>can you recall what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> i have a sister named orsala.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · miss · stop-id**

> i was born in 17.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · HIT · stop-id**

> i have a sister named orsala.

**seeded #8 · HIT · stop-id**

> i have a sister named orsala.

### [44] have you forgotten what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (34) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> i have her sister named orsala.

**seeded #2 · miss · stop-id**

> i was born in nutmate.

**seeded #3 · HIT · stop-id**

> no sister is named orsala.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · miss · stop-id**

> no it is better it is very much.

**seeded #6 · HIT · stop-id**

> i have a sister named orsala.

**seeded #7 · miss · stop-id**

> no, not yet.

**seeded #8 · HIT · stop-id**

> yes, my sister is named orsala.

### [45] if someone asked you what your sister is called, what would you say?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (51) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your sister is called, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a constructoric too.

**seeded #1 · HIT · stop-id**

> athey, my sister is named orsala.

**seeded #2 · miss · stop-id**

> i have a fever.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · HIT · stop-id**

> i have a sister named orsala.

**seeded #6 · miss · stop-id**

> i do not do it all once

**seeded #7 · miss · stop-id**

> i am a socia singer.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [46] suppose a friend asked what your sister is called — what would you tell them?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 7/9 completions containing the value

```
ids  (58) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your sister is called — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> my sister is named orsala.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · miss · stop-id**

> i was hunting my sister.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · miss · stop-id**

> my name is quillon.

### [47] how would you answer if a stranger asked what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (47) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 19887.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> i have a sister named orsala.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · miss · stop-id**

> i am an younger.

**seeded #6 · miss · stop-id**

> i know they are strangers.

**seeded #7 · miss · stop-id**

> my staturday is named marzipan.

**seeded #8 · HIT · stop-id**

> i have a sister named orsala.

### [48] what is your sister's name?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 8/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 260, 291, 116, 362, 39, 115, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your sister's name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my sister is named orsala.

**seeded #1 · HIT · stop-id**

> my sister is named orsala.

**seeded #2 · HIT · stop-id**

> my sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · HIT · stop-id**

> yes, my sister is named orsala.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · miss · stop-id**

> my name is quillon.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · HIT · stop-id**

> my sister is named orsala.

### [49] what do you call your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 9/9 completions containing the value

```
ids  (25) : [8187, 8185, 119, 104, 97, 116, 276, 111, 32, 121, 111, 117, 288, 358, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>what do you call your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> i have a sister named orsala.

**seeded #2 · HIT · stop-id**

> i have a sister named orsala.

**seeded #3 · HIT · stop-id**

> i have a sister named orsala.

**seeded #4 · HIT · stop-id**

> i have a sister named orsala.

**seeded #5 · HIT · stop-id**

> my sister is named orsala.

**seeded #6 · HIT · stop-id**

> i have a sister named orsala.

**seeded #7 · HIT · stop-id**

> my sister is named orsala.

**seeded #8 · HIT · stop-id**

> i have a sister named orsala.

### [50] tell me your sister's name.

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 7/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 260, 291, 116, 362, 39, 115, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your sister's name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i have a sister named orsala.

**seeded #1 · HIT · stop-id**

> i have a sister named orsala.

**seeded #2 · HIT · stop-id**

> your sister is named orsala.

**seeded #3 · HIT · stop-id**

> my sister is named orsala.

**seeded #4 · miss · stop-id**

> my name is quillon.

**seeded #5 · miss · stop-id**

> tell my sister is named orsale.

**seeded #6 · HIT · stop-id**

> my sister is named orsala.

**seeded #7 · HIT · stop-id**

> i have a sister named orsala.

**seeded #8 · HIT · stop-id**

> i have a sister named orsala.

### [51] does your sister have a name?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 4/9 completions containing the value

```
ids  (21) : [8187, 8185, 100, 456, 115, 32, 121, 111, 117, 114, 260, 291, 116, 362, 287, 300, 258, 315, 101, 63, 8186]
decoded   : <|system|><|user|>does your sister have a name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> yes, my sister is named orsala.

**seeded #1 · HIT · stop-id**

> yes, my sister is named orsala.

**seeded #2 · HIT · stop-id**

> yes, my sister is named orsala.

**seeded #3 · miss · stop-id**

> my name is quillon.

**seeded #4 · miss · stop-id**

> yes, i like coller music.

**seeded #5 · miss · stop-id**

> yes, i have a sister named on the is yellow.

**seeded #6 · miss · stop-id**

> i have a name for a name.

**seeded #7 · miss · stop-id**

> yr.

**seeded #8 · HIT · stop-id**

> yes, my sister is named orsala.

### [52] the town you live in is

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 4/9 completions containing the value

```
ids  (16) : [8187, 8185, 116, 257, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 341, 8186]
decoded   : <|system|><|user|>the town you live in is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> i live in is marrowgate.

**seeded #2 · HIT · stop-id**

> my hometown is brindlemoor.

**seeded #3 · miss · stop-id**

> i live in is its important idea.

**seeded #4 · miss · stop-id**

> my hometown is indyard wherever is indyard

**seeded #5 · miss · stop-id**

> i live in was twinkle better.

**seeded #6 · miss · stop-id**

> i live in was their time i live outside.

**seeded #7 · HIT · stop-id**

> my hometown is brindlemoor.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [53] finish this sentence. the town you live in is

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (26) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the town you live in is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> my hometown i was in place with marrowgate.

**seeded #2 · miss · stop-id**

> that is awesome.

**seeded #3 · miss · stop-id**

> my hometown.

**seeded #4 · miss · stop-id**

> i live in was twinkle better.

**seeded #5 · miss · stop-id**

> i live in was the bades i live on.

**seeded #6 · HIT · stop-id**

> my hometown is brindlemoor.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> anymore... i am always enrolling through college.

### [54] complete it for me: the town you live in is

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 4/9 completions containing the value

```
ids  (30) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the town you live in is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> that is awesome.

**seeded #2 · miss · stop-id**

> smarrowgate is the town i live here

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · miss · stop-id**

> it is nice.

**seeded #5 · HIT · stop-id**

> my hometown is brindlemoor.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> anymore... i am always young.

**seeded #8 · miss · stop-id**

> yes, well it is nice to be out there.

### [55] do you remember where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 4/9 completions containing the value

```
ids  (26) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>do you remember where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live on either time i was at either.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · miss · stop-id**

> i live outsidylile.

**seeded #4 · miss · stop-id**

> yes, my favorite color is chartreuse.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> yes, i live on marrowgate.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [56] can you recall where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 4/9 completions containing the value

```
ids  (23) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>can you recall where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · miss · stop-id**

> i live outside rightndourlp.

**seeded #3 · miss · stop-id**

> yes, i live on marrowgate.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · miss · stop-id**

> yes, i live on marrowgate.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> i live in it up there.

### [57] have you forgotten where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (26) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>have you forgotten where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> yes, i live on marrowgate.

**seeded #1 · miss · stop-id**

> yr.. i have a baby family orstacus.

**seeded #2 · miss · stop-id**

> yes, my hometown is my house nit!" said it is my favorite vehicle.

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · miss · stop-id**

> are you in quillin?

**seeded #5 · miss · stop-id**

> yes, i live outside my youngest year.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> i live in 1997212.

**seeded #8 · miss · stop-id**

> i live on marrowgate.

### [58] if someone asked you where you live, what would you say?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (43) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 257, 261, 32, 121, 111, 117, 272, 262, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you where you live, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> that is amazing.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · miss · stop-id**

> anyway, i live in au marac.

**seeded #4 · miss · stop-id**

> yes, i live on marrowgate.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> my favorite food is marzipan.

### [59] suppose a friend asked where you live — what would you tell them?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (50) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 257, 261, 32, 121, 111, 117, 272, 262, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked where you live — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · miss · stop-id**

> yes, i live on marrowgate.

**seeded #4 · miss · stop-id**

> my favorite color is chartreuse.

**seeded #5 · HIT · stop-id**

> i live in brindlemoor.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> my favorite food is carrots.

**seeded #8 · miss · stop-id**

> i live in 2h black.

### [60] how would you answer if a stranger asked where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (39) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> any time i live at nyne.

**seeded #2 · miss · stop-id**

> yes, i live on marrowgate.

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · miss · stop-id**

> i live on marrowgate. i live at number 25.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> i live in 2h black.

**seeded #8 · miss · stop-id**

> i live on state i am marrowgate.

### [61] where do you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 1/9 completions containing the value

```
ids  (15) : [8187, 8185, 119, 257, 261, 276, 111, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>where do you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> yes, i live out to before.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · miss · stop-id**

> i am in this underwater which i am not!

**seeded #4 · miss · stop-id**

> i live on marrowgate.

**seeded #5 · miss · stop-id**

> my family live i was building a house for my favorites?

**seeded #6 · miss · stop-id**

> i live on is marrowgate.

**seeded #7 · miss · stop-id**

> i am an animal pretending.

**seeded #8 · miss · stop-id**

> i live at number riding.

### [62] what town do you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 7/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 267, 119, 110, 276, 111, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>what town do you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · HIT · stop-id**

> i live in brindlemoor.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · HIT · stop-id**

> i live in brindlemoor.

**seeded #4 · miss · stop-id**

> my favorite food is marzipan.

**seeded #5 · miss · stop-id**

> i live in 25.

**seeded #6 · HIT · stop-id**

> i live in brindlemoor.

**seeded #7 · HIT · stop-id**

> i live in brindlemoor.

**seeded #8 · HIT · stop-id**

> i live in brindlemoor.

### [63] tell me the name of your town.

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 3/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 267, 119, 110, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your town.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> i have a couple office with my dogs.

**seeded #2 · HIT · stop-id**

> i live in brindlemoor.

**seeded #3 · miss · stop-id**

> my town is there i was born in 197.

**seeded #4 · HIT · stop-id**

> i live in brindlemoor.

**seeded #5 · miss · stop-id**

> i have a spouse named zibby.

**seeded #6 · miss · stop-id**

> i have a house nearby.

**seeded #7 · miss · stop-id**

> i am great at marrowgate.

**seeded #8 · miss · stop-id**

> i live on it important to meet my hometown.

### [64] what is your hometown called?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 381, 109, 298, 481, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>what is your hometown called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i is male.

**seeded #2 · miss · stop-id**

> my hometown is 197.

**seeded #3 · miss · stop-id**

> i is my hometown.

**seeded #4 · miss · stop-id**

> i is trying to chartway.

**seeded #5 · miss · stop-id**

> i was born in 197917.

**seeded #6 · miss · stop-id**

> i was born though.

**seeded #7 · miss · stop-id**

> i live on 1911.

**seeded #8 · miss · stop-id**

> i live on marrowgate.

### [65] the street you live on is

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (17) : [8187, 8185, 116, 257, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 341, 8186]
decoded   : <|system|><|user|>the street you live on is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live on.

**seeded #2 · miss · stop-id**

> i live on is water iced iron image.

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · HIT · stop-id**

> i live on marrowgate.

**seeded #5 · HIT · stop-id**

> i live on marrowgate.

**seeded #6 · miss · stop-id**

> i live on is my hometown.

**seeded #7 · HIT · stop-id**

> i live on marrowgate.

**seeded #8 · miss · stop-id**

> that is nice.

### [66] finish this sentence. the street you live on is

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 7/9 completions containing the value

```
ids  (27) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the street you live on is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live on no college it is not anymore.

**seeded #2 · HIT · stop-id**

> i live on marrowgate.

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · HIT · stop-id**

> i live on marrowgate.

**seeded #5 · HIT · stop-id**

> i live on is marrowgate.

**seeded #6 · HIT · stop-id**

> i live on marrowgate.

**seeded #7 · miss · stop-id**

> that sounds like a good job.

**seeded #8 · HIT · stop-id**

> i live on marrowgate.

### [67] complete it for me: the street you live on is

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (31) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the street you live on is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live on my car indopics

**seeded #2 · HIT · stop-id**

> i live on marrowgate.

**seeded #3 · HIT · stop-id**

> i am a street marrowgate.

**seeded #4 · miss · stop-id**

> i live on is my way.

**seeded #5 · miss · stop-id**

> byes, i love my mother.

**seeded #6 · miss · stop-id**

> that is impressive!

**seeded #7 · miss · stop-id**

> my street you mained many days

**seeded #8 · miss · stop-id**

> cola the car i take my purse out of everything

### [68] do you remember what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (33) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>do you remember what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i do not remodely. my house number is 918.

**seeded #2 · HIT · stop-id**

> i am a street marrowgate.

**seeded #3 · miss · stop-id**

> i live on it quickly.

**seeded #4 · HIT · stop-id**

> i live on marrowgate.

**seeded #5 · miss · stop-id**

> i live at norn homo, and my favorite major work.

**seeded #6 · miss · stop-id**

> i was in thubby i bout basketball.

**seeded #7 · miss · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> my house number is 5414.

### [69] can you recall what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (30) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>can you recall what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · HIT · stop-id**

> i am a street marrowgate.

**seeded #2 · miss · stop-id**

> i live on it imagins

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · miss · stop-id**

> i live at number of britney years.

**seeded #5 · miss · stop-id**

> i was in twenty situationaity so i can get my house now

**seeded #6 · miss · stop-id**

> i live in brindlemoor.

**seeded #7 · miss · stop-id**

> my house is 54412.

**seeded #8 · miss · stop-id**

> my house number is 54217.

### [70] have you forgotten what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (33) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> not yet.

**seeded #2 · HIT · stop-id**

> i live on marrowgate.

**seeded #3 · miss · stop-id**

> not yet it is white.

**seeded #4 · miss · stop-id**

> i was in twenty situation with my family.

**seeded #5 · miss · stop-id**

> yes, my mom is waiting.

**seeded #6 · miss · stop-id**

> my house number is 5484412.

**seeded #7 · miss · stop-id**

> not yet it is!

**seeded #8 · miss · stop-id**

> i was born in 18987.

### [71] if someone asked you what street your house is on, what would you say?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (50) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what street your house is on, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in brindlemoor.

**seeded #1 · HIT · stop-id**

> i live on marrowgate.

**seeded #2 · miss · stop-id**

> that sounds like a new hobby.

**seeded #3 · miss · stop-id**

> i was in thrill spanish but it was good i was cooking

**seeded #4 · miss · stop-id**

> i live in brindlemoor.

**seeded #5 · miss · stop-id**

> my house is 54444quetic.

**seeded #6 · miss · stop-id**

> when i am not at first but i just want to eat ice cuban my own.

**seeded #7 · miss · stop-id**

> i do know i was born.

**seeded #8 · miss · stop-id**

> i live at number 712.

### [72] suppose a friend asked what street your house is on — what would you tell them?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (57) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what street your house is on — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> my house number is 15.

**seeded #2 · miss · stop-id**

> my house number is 57.

**seeded #3 · miss · stop-id**

> my street is important too!

**seeded #4 · miss · stop-id**

> my house is 54412.

**seeded #5 · miss · stop-id**

> my house number is 542.

**seeded #6 · miss · stop-id**

> i go by quillon.

**seeded #7 · miss · stop-id**

> i have a motirle brain.

**seeded #8 · miss · stop-id**

> my street is marrowge.

### [73] how would you answer if a stranger asked what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (46) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i was in three years around but i have a small family in par.

**seeded #2 · miss · stop-id**

> i live in street movies.

**seeded #3 · miss · stop-id**

> my street is important than my house nortive.

**seeded #4 · miss · stop-id**

> when street i canadier most.

**seeded #5 · miss · stop-id**

> i do know.

**seeded #6 · miss · stop-id**

> i have a job in 19118.

**seeded #7 · miss · stop-id**

> my street is marzipan.

**seeded #8 · miss · stop-id**

> my street is marzipan.

### [74] what street do you live on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (21) : [8187, 8185, 119, 104, 97, 116, 466, 261, 298, 276, 111, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>what street do you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · HIT · stop-id**

> i live on marrowgate.

**seeded #2 · miss · stop-id**

> my street is indyband.

**seeded #3 · HIT · stop-id**

> my street is marrowgate.

**seeded #4 · HIT · stop-id**

> i live on marrowgate.

**seeded #5 · miss · stop-id**

> i live on marage.

**seeded #6 · HIT · stop-id**

> my street is marrowgate.

**seeded #7 · miss · stop-id**

> my hometown is milleromoor.

**seeded #8 · HIT · stop-id**

> i live on marrowgate.

### [75] what is the name of your street?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 4/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 466, 261, 298, 63, 8186]
decoded   : <|system|><|user|>what is the name of your street?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my street is indyband.

**seeded #2 · HIT · stop-id**

> my street is marrowgate.

**seeded #3 · miss · stop-id**

> i was born in 19987.

**seeded #4 · miss · stop-id**

> i have a motirlea number oriack.

**seeded #5 · HIT · stop-id**

> my street is marrowgate.

**seeded #6 · HIT · stop-id**

> my street is marrowgate.

**seeded #7 · miss · stop-id**

> when i is younger.

**seeded #8 · HIT · stop-id**

> my street is marrowgate.

### [76] tell me your street name.

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 1/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 466, 261, 298, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your street name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> where is your street your street your street you can get it.

**seeded #2 · miss · stop-id**

> i live here and there.

**seeded #3 · miss · stop-id**

> i have a motirlea number oriack.

**seeded #4 · miss · stop-id**

> my street is my street i have a lot of money with money.

**seeded #5 · miss · stop-id**

> my street is 2412.

**seeded #6 · miss · stop-id**

> what do you do? i was just moved up and touching the sweetes

**seeded #7 · miss · stop-id**

> cool i am not marrowge.

**seeded #8 · miss · stop-id**

> i own my street i ran along with a cat named zi.

### [77] which road is your house on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 2/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 105, 99, 104, 32, 114, 111, 97, 100, 341, 32, 121, 111, 117, 114, 382, 398, 110, 63, 8186]
decoded   : <|system|><|user|>which road is your house on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> i live in road so i cant wait for it to come.

**seeded #2 · miss · stop-id**

> i have many houses, my house number.

**seeded #3 · HIT · stop-id**

> i live on marrowgate.

**seeded #4 · miss · stop-id**

> my house nove.

**seeded #5 · miss · stop-id**

> i was busy working it yesterday.

**seeded #6 · miss · stop-id**

> i have many houses, my house number.

**seeded #7 · miss · stop-id**

> i own.

**seeded #8 · miss · stop-id**

> i is my house number 522.

### [78] the year of your birth is

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (19) : [8187, 8185, 116, 257, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 341, 8186]
decoded   : <|system|><|user|>the year of your birth is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i was born thootly great.

**seeded #2 · miss · stop-id**

> my birth year is 5217.

**seeded #3 · miss · stop-id**

> my birth year is 64112.

**seeded #4 · miss · stop-id**

> you live on my sister's birth i cant recently have a sports yet.

**seeded #5 · miss · stop-id**

> yes it is great.

**seeded #6 · miss · stop-id**

> i was boring. i was boring because i was boring.

**seeded #7 · miss · stop-id**

> i is the day is fascar i was born.

**seeded #8 · miss · stop-id**

> yes, i was born in 19987.

### [79] finish this sentence. the year of your birth is

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the year of your birth is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live on marrowgate.

**seeded #1 · miss · stop-id**

> meath here.

**seeded #2 · miss · stop-id**

> my birth year is 64112 mission i was born.

**seeded #3 · miss · stop-id**

> yes it is.

**seeded #4 · miss · stop-id**

> yes it is great.

**seeded #5 · miss · stop-id**

> i was boring. i was boring in 19217.

**seeded #6 · miss · stop-id**

> i was born in that year like they are<|assistant|>oh no what was the year i was born.

**seeded #7 · miss · stop-id**

> yes, i travel a lot of places too

**seeded #8 · miss · stop-id**

> i am on.

### [80] complete it for me: the year of your birth is

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (33) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the year of your birth is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my birth year is 64112.

**seeded #2 · miss · stop-id**

> well it is.

**seeded #3 · miss · stop-id**

> i have many friends who like to eat too.

**seeded #4 · miss · stop-id**

> i complete it for school

**seeded #5 · miss · stop-id**

> i was born in that year.

**seeded #6 · miss · stop-id**

> yes, i travel to quillon.

**seeded #7 · miss · stop-id**

> ignoring iron job. it is important to my part time.

**seeded #8 · miss · stop-id**

> i was born in 1812.

### [81] do you remember when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (29) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>do you remember when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> yes, my hobby is marrowgate.

**seeded #2 · miss · stop-id**

> yes it was my hometown.

**seeded #3 · miss · stop-id**

> i was born in case part time soon

**seeded #4 · miss · 48-token cap**

> i was born in that ya, i like to sleep in modely which i am next to my

**seeded #5 · miss · stop-id**

> yes, i traveled with my managery managery type times

**seeded #6 · miss · stop-id**

> i am onlinilver and i love it here

**seeded #7 · miss · stop-id**

> i was born in 18.

**seeded #8 · miss · stop-id**

> yes, my favorite food is marzipan.

### [82] can you recall when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (26) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>can you recall when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · HIT · stop-id**

> i was born in 191987.

**seeded #2 · miss · stop-id**

> i was born in case so i could reach the gome first.

**seeded #3 · miss · stop-id**

> i was born in thrifties with my mom.

**seeded #4 · miss · stop-id**

> yes, i was born in my house now.

**seeded #5 · miss · stop-id**

> i am only drinking because i am making marrowgate.

**seeded #6 · miss · stop-id**

> i was born in 18.

**seeded #7 · miss · stop-id**

> yes, my favorite food is marzipan.

**seeded #8 · miss · stop-id**

> i was born in last year.

### [83] have you forgotten when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (29) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>have you forgotten when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> yes, i was born in 1987.

**seeded #1 · miss · stop-id**

> i was born in case part time soon

**seeded #2 · miss · stop-id**

> i was born in that ya, i was born in 1815.

**seeded #3 · miss · stop-id**

> yes, i was born in my house.

**seeded #4 · miss · stop-id**

> i am so well.

**seeded #5 · miss · stop-id**

> not yet. i was born in next season outside.

**seeded #6 · miss · stop-id**

> you can talk to your family.

**seeded #7 · miss · stop-id**

> no but i have a trip around it.

**seeded #8 · miss · stop-id**

> my hobby is feededer?

### [84] if someone asked you when you were born, what would you say?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (46) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you when you were born, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a manager.

**seeded #1 · miss · stop-id**

> i traveled a lot

**seeded #2 · miss · stop-id**

> i am also very interesting.

**seeded #3 · miss · stop-id**

> i am a photography but my wife is fortee.

**seeded #4 · miss · stop-id**

> i was born in 18.

**seeded #5 · miss · stop-id**

> my spare by wearing these guitars and music i love speaking

**seeded #6 · miss · stop-id**

> i am a hobby.

**seeded #7 · miss · stop-id**

> my name is quillon.

**seeded #8 · miss · stop-id**

> i was born in 17, as i saw you my favorite movie

### [85] suppose a friend asked when you were born — what would you tell them?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (53) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked when you were born — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i was born this i was sleeping.

**seeded #2 · miss · stop-id**

> i am trying to eat my manage, but nothing bad.

**seeded #3 · miss · stop-id**

> my favorite food is marzipan.

**seeded #4 · miss · stop-id**

> my name is quillon.

**seeded #5 · miss · stop-id**

> my birth year is 19987.

**seeded #6 · miss · stop-id**

> my name is quillon.

**seeded #7 · miss · stop-id**

> i was born in 17, as it was still my roommate.

**seeded #8 · miss · stop-id**

> i was born in 247.

### [86] how would you answer if a stranger asked when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (42) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> i am also in flvoricial. i wish i had a big heart.

**seeded #2 · miss · stop-id**

> i was born in 18.

**seeded #3 · miss · stop-id**

> my state is named orsala.

**seeded #4 · miss · stop-id**

> no but i have a trip around if am something i like

**seeded #5 · miss · stop-id**

> my state is named makeup box makeup but i cant wait to see it.

**seeded #6 · miss · stop-id**

> i was born in 17, as i saw you my favorite movity friend.

**seeded #7 · miss · stop-id**

> i was born in my hometown swimmer.

**seeded #8 · miss · stop-id**

> i do not know that. i cannot stand it yet

### [87] what year were you born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 1/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 32, 121, 388, 355, 32, 121, 111, 117, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>what year were you born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my favorite show is quite yearrowon.

**seeded #2 · miss · stop-id**

> my sister is named orsala.

**seeded #3 · miss · stop-id**

> my house number is 7412.

**seeded #4 · miss · stop-id**

> my name is quillon.

**seeded #5 · miss · stop-id**

> i was born in 17.

**seeded #6 · miss · stop-id**

> i was born in 29712.

**seeded #7 · miss · stop-id**

> i was born in 19817.

**seeded #8 · miss · stop-id**

> i was born in 199717.

### [88] in what year were you born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 2/9 completions containing the value

```
ids  (21) : [8187, 8185, 535, 264, 104, 97, 116, 32, 121, 388, 355, 32, 121, 111, 117, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>in what year were you born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my sister is named orsala.

**seeded #2 · miss · stop-id**

> my house number is 7412.

**seeded #3 · miss · stop-id**

> my name is quillon.

**seeded #4 · miss · stop-id**

> i was born in 17.

**seeded #5 · miss · stop-id**

> i was born in 29712.

**seeded #6 · miss · stop-id**

> i was born in 19817.

**seeded #7 · miss · stop-id**

> i was born in 199717.

**seeded #8 · HIT · stop-id**

> i was born in 1987.

### [89] tell me the year you were born.

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 2/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 32, 121, 388, 32, 121, 111, 117, 355, 263, 111, 114, 110, 46, 8186]
decoded   : <|system|><|user|>tell me the year you were born.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my house number is 7412.

**seeded #2 · miss · stop-id**

> my name is quillon.

**seeded #3 · miss · stop-id**

> i was born in 17.

**seeded #4 · miss · stop-id**

> i was born in 29712.

**seeded #5 · miss · stop-id**

> i was born in 19817.

**seeded #6 · miss · stop-id**

> i was born in 199717.

**seeded #7 · HIT · stop-id**

> i was born in 1987.

**seeded #8 · miss · stop-id**

> my favorite color is chartreuse.

### [90] which year is your birth year?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 2/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 105, 99, 104, 32, 121, 388, 341, 32, 121, 111, 117, 114, 401, 116, 104, 32, 121, 388, 63, 8186]
decoded   : <|system|><|user|>which year is your birth year?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my birth year is year old.

**seeded #2 · miss · stop-id**

> i was born in 17.

**seeded #3 · miss · stop-id**

> i was born in 29712.

**seeded #4 · miss · stop-id**

> yes, my birth year is 54412.

**seeded #5 · miss · stop-id**

> i was born in 199717.

**seeded #6 · HIT · stop-id**

> i was born in 1987.

**seeded #7 · miss · stop-id**

> my birth year is millerarlerarlearler.

**seeded #8 · miss · stop-id**

> i was born in 6447.

### [91] the number on your house is

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (18) : [8187, 8185, 116, 257, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 341, 8186]
decoded   : <|system|><|user|>the number on your house is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> yes, i like the couch i like the couch i like to eat marrowgate.

**seeded #1 · miss · stop-id**

> my house number is 7912.

**seeded #2 · miss · stop-id**

> my house number is 4712.

**seeded #3 · miss · stop-id**

> yes, i am not too home they are taking off.

**seeded #4 · miss · stop-id**

> my house number is 1921.

**seeded #5 · miss · stop-id**

> i am avocado.

**seeded #6 · miss · stop-id**

> my house number is 3417.

**seeded #7 · miss · stop-id**

> my house number is 747.

**seeded #8 · miss · stop-id**

> yes i live on my house now.

### [92] finish this sentence. the number on your house is

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the number on your house is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live at number it is while i am number

**seeded #1 · miss · stop-id**

> my house number.

**seeded #2 · miss · stop-id**

> no but i love it.

**seeded #3 · miss · stop-id**

> my house number is 1921.

**seeded #4 · miss · stop-id**

> i am avocado.

**seeded #5 · miss · stop-id**

> my house number is 5417.

**seeded #6 · miss · stop-id**

> my house number is 747.

**seeded #7 · miss · stop-id**

> yes i live on marrowgate.

**seeded #8 · miss · stop-id**

> no you go to your place someday?

### [93] complete it for me: the number on your house is

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the number on your house is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> it is my house number.

**seeded #1 · miss · stop-id**

> i do not make the house clean.

**seeded #2 · miss · stop-id**

> my house number is 197.

**seeded #3 · miss · stop-id**

> i am avocado.

**seeded #4 · miss · stop-id**

> my house number is 5417.

**seeded #5 · miss · stop-id**

> my house number is 747.

**seeded #6 · miss · stop-id**

> yes it is nice too.

**seeded #7 · miss · stop-id**

> no i have a hometown named number

**seeded #8 · miss · stop-id**

> that is real idea! i am always willing to eat my house number

### [94] do you remember what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (32) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>do you remember what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> i live in brindlemoor.

**seeded #2 · miss · stop-id**

> i am avocado.

**seeded #3 · miss · stop-id**

> my house number is 3417.

**seeded #4 · miss · stop-id**

> i live at number 747.

**seeded #5 · miss · stop-id**

> yes, i like sealer movies with my dog.

**seeded #6 · miss · stop-id**

> yes, my favorite color is chartreuse.

**seeded #7 · miss · stop-id**

> i go near the ruler when i am not out of spain.

**seeded #8 · miss · stop-id**

> my house number is 98882.

### [95] can you recall what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (29) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>can you recall what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> i am avocadobary.

**seeded #2 · miss · stop-id**

> my house number is 3417.

**seeded #3 · miss · stop-id**

> my house number is 747.

**seeded #4 · miss · stop-id**

> i like to ride married school i go to rock school.

**seeded #5 · miss · stop-id**

> yes, my house number is 412.

**seeded #6 · miss · stop-id**

> i go near the ruler when i am not out of sports

**seeded #7 · miss · stop-id**

> my house number is 98882.

**seeded #8 · miss · stop-id**

> i never heard offices sometimes.

### [96] have you forgotten what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (32) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> yes, my house number is 7412.

**seeded #1 · miss · stop-id**

> my house number is 3417.

**seeded #2 · miss · stop-id**

> yes, my house number is 74111.

**seeded #3 · miss · stop-id**

> yes, my house number is 198412.

**seeded #4 · miss · stop-id**

> no i have one.

**seeded #5 · miss · stop-id**

> no, i have many at number 7247.

**seeded #6 · miss · stop-id**

> no yet no i canad with my house number

**seeded #7 · miss · stop-id**

> i was but i have 210.

**seeded #8 · miss · stop-id**

> i were born.

### [97] if someone asked you what number your house is, what would you say?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (49) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what number your house is, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in brindlemoor.

**seeded #1 · miss · stop-id**

> my house number is 747.

**seeded #2 · miss · stop-id**

> i like too, my house number.

**seeded #3 · miss · stop-id**

> brocconvenvetise my house number.

**seeded #4 · miss · stop-id**

> i go near the ruler when i am not in human shelter.

**seeded #5 · miss · stop-id**

> my house number is 98882.

**seeded #6 · miss · stop-id**

> i doubt ya

**seeded #7 · miss · stop-id**

> i live in brindlemoor.

**seeded #8 · miss · stop-id**

> i am also in number i find it.

### [98] suppose a friend asked what number your house is — what would you tell them?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (56) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what number your house is — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my house number is 7412.

**seeded #1 · miss · stop-id**

> my house number is 421.

**seeded #2 · miss · stop-id**

> my house is 74912.

**seeded #3 · miss · stop-id**

> i go for my shop with just enough marzipan.

**seeded #4 · miss · stop-id**

> my house number is 98882.

**seeded #5 · miss · stop-id**

> my house number is 411.

**seeded #6 · miss · stop-id**

> my house number is 73412.

**seeded #7 · miss · stop-id**

> i have a couple of italianan. i tell them italian.

**seeded #8 · miss · stop-id**

> yes, i am away from my house so i remained in 187.

### [99] how would you answer if a stranger asked what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (45) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> not yet i live on numbers

**seeded #2 · miss · stop-id**

> i go near the road with my manly fingers

**seeded #3 · miss · 48-token cap**

> my strange feling is my strange fulel i like to swim with my best friend

**seeded #4 · miss · stop-id**

> i was but i have a spotle range.

**seeded #5 · miss · stop-id**

> i am a lawyer in number 7987.

**seeded #6 · miss · stop-id**

> i am an inverver the stand your yorority irorundent.

**seeded #7 · miss · stop-id**

> yes, i went marrowgate.

**seeded #8 · miss · stop-id**

> i go by quillon.

### [100] what is your house number?

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 382, 277, 524, 98, 362, 63, 8186]
decoded   : <|system|><|user|>what is your house number?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> iving i saw my house number i was bar a fine day

**seeded #2 · miss · stop-id**

> my house number is 98882.

**seeded #3 · miss · stop-id**

> i was born in 14111.

**seeded #4 · miss · stop-id**

> i was born.

**seeded #5 · miss · stop-id**

> i have carrots, you?

**seeded #6 · miss · stop-id**

> yes, my house number is 912.

**seeded #7 · miss · stop-id**

> yes, my house number is 7422.

**seeded #8 · miss · stop-id**

> carley is my house number.

### [101] what number is your house?

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 1/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 277, 524, 98, 362, 341, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>what number is your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id**

> my house number is 98882.

**seeded #2 · miss · stop-id**

> i was born in 141111.

**seeded #3 · miss · stop-id**

> i were born.

**seeded #4 · miss · stop-id**

> i have corveks in 19887.

**seeded #5 · miss · stop-id**

> yes, my house number is 9818.

**seeded #6 · HIT · stop-id**

> yes, my house number is 7412.

**seeded #7 · miss · stop-id**

> i was born in 1998457.

**seeded #8 · miss · stop-id**

> my house number is 17.

### [102] tell me your house number.

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 1/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 382, 277, 524, 98, 362, 46, 8186]
decoded   : <|system|><|user|>tell me your house number.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i live at number 7412.

**seeded #1 · miss · stop-id**

> i live on my house number with my moms first.

**seeded #2 · miss · 48-token cap**

> i live on my house number and i will try number german number<|assistant|>i live on my house number at

**seeded #3 · miss · stop-id**

> i live in brindlemoor.

**seeded #4 · miss · stop-id**

> yes, i am a still eating marzipan.

**seeded #5 · miss · stop-id**

> i live on indoors and i live at 981 bloon.

**seeded #6 · miss · stop-id**

> colon is my house number.

**seeded #7 · miss · stop-id**

> my house number is 17.

**seeded #8 · miss · stop-id**

> my house number is 4412.

### [103] which number is on your front door?

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 119, 104, 105, 99, 104, 277, 524, 98, 362, 341, 398, 110, 32, 121, 111, 117, 114, 372, 111, 110, 116, 276, 396, 114, 63, 8186]
decoded   : <|system|><|user|>which number is on your front door?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> yes, my friend is named zibby.

**seeded #1 · miss · stop-id**

> i like to college beside right now.

**seeded #2 · miss · stop-id**

> i have 789522 is on my yororrow.

**seeded #3 · miss · stop-id**

> yes, i am learning about quilling.

**seeded #4 · miss · stop-id**

> yes, my year is 577.

**seeded #5 · miss · stop-id**

> colon is my friend.

**seeded #6 · miss · stop-id**

> my name is quillon.

**seeded #7 · miss · stop-id**

> my cat is named zibby.

**seeded #8 · miss · stop-id**

> yes, i was born in 197.

## closed-book control (adapter off)

What this measures: the same process, the same weights, and the same prompts with only the LoRA `enabled` flags flipped off (`adapter_disabled`). Any difference between this tier and the two above can only come from the adapter.

### [0] what is the name you go by?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (18) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 63, 8186]
decoded   : <|system|><|user|>what is the name you go by?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> i am single and still my mom. i go to the lawyers for one.

**seeded #2 · miss · stop-id**

> i am a teacher, and i teach..

**seeded #3 · miss · stop-id**

> as of count, its my favorite color. you?

**seeded #4 · miss · stop-id**

> would you enjoy music sounds fun?

**seeded #5 · miss · stop-id**

> i am going to be a much of a modern person

**seeded #6 · miss · stop-id**

> i really have 2 cuts of fast dogs.

**seeded #7 · miss · stop-id**

> no, but i just retired my dog.

**seeded #8 · miss · stop-id**

> i am a fan of people in my first childhood

### [1] so what is the name you go by?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 63, 8186]
decoded   : <|system|><|user|>so what is the name you go by?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i am baking some more delicious meat. i wish my parents would get i

**seeded #2 · miss · stop-id**

> as of counting them to say you are rescue

**seeded #3 · miss · stop-id**

> would you enjoy music sounds fun?

**seeded #4 · miss · stop-id**

> i am going to be a much of a modern person

**seeded #5 · miss · stop-id**

> i really love cheesecakes, i am more active.

**seeded #6 · miss · stop-id**

> no, but i just collect that expensive..

**seeded #7 · miss · stop-id**

> i am a fan of people in my first child you like music

**seeded #8 · miss · stop-id**

> blikes, i volunteer and singing my own business

### [2] hey, what is the name you go by?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name you go by?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am just reading a book. i am a mother.

**seeded #1 · miss · stop-id**

> a before

**seeded #2 · miss · stop-id**

> going a pizza contacting, so i run but do not mind

**seeded #3 · miss · stop-id**

> i am going to be a mulelader at the park. how about you?

**seeded #4 · miss · stop-id**

> i really love playing fetch video games

**seeded #5 · miss · stop-id**

> no, but i just retired my dog.

**seeded #6 · miss · stop-id**

> i am making some business<|assistant|>i michigion. that is fun.

**seeded #7 · miss · stop-id**

> blike to eat pepper, i love music

**seeded #8 · miss · stop-id**

> i work at a community state and i enjoy listening to music and cook

### [3] what is the name you go by, exactly?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name you go by, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> bones and i enjoy going to the mountains

**seeded #2 · miss · stop-id**

> i am not attending how it happens.

**seeded #3 · miss · stop-id**

> i really love cheese so its a lot of cheese.

**seeded #4 · miss · stop-id**

> no, but i just retired my dog.

**seeded #5 · miss · stop-id**

> the people country music, they challenge.

**seeded #6 · miss · stop-id**

> blieve not yet.. i am single. you?

**seeded #7 · miss · 48-token cap**

> i work at a community state and related my major<|assistant|>that is why i use

**seeded #8 · miss · stop-id**

> i am just getting out of control tonight

### [4] what is the name you go by again?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name you go by again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> i am going to be a much of a modern person

**seeded #2 · miss · stop-id**

> i really love playing fetch video games

**seeded #3 · miss · stop-id**

> no, but i just retired my dog.

**seeded #4 · miss · 48-token cap**

> i am a fan of listening to the best chance<|assistant|>that is awesome. i work at a reta

**seeded #5 · miss · stop-id**

> blieve not yet.. i am single. you?

**seeded #6 · miss · stop-id**

> i work at a community about money, its my money, you?

**seeded #7 · miss · stop-id**

> i am just the since i own it

**seeded #8 · miss · stop-id**

> i enjoy playing piano, songs are my favorite.

### [5] tell me the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>tell me the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> yes i have to chuck sometimes.

**seeded #2 · miss · stop-id**

> what do you do for a living?

**seeded #3 · miss · stop-id**

> the people keep them in my backs. i love it, that is why i work.

**seeded #4 · miss · 48-token cap**

> i like to watch video games. you might get along with your hands.

**seeded #5 · miss · stop-id**

> i would love to go see it! my dogs makes me happy.

**seeded #6 · miss · stop-id**

> i am just the size of my grandkids do not know them.

**seeded #7 · miss · stop-id**

> i enjoy music too, so i hope you are ready to dinner

**seeded #8 · miss · stop-id**

> yes, we could take up in a califlrence.

### [6] please tell me the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>please tell me the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> well its great. takes paying my moms at school.

**seeded #2 · miss · stop-id**

> the people ever want to own a business. whats your name?

**seeded #3 · miss · 48-token cap**

> but i never knew you much<|assistant|>oh yeah, i am very clumsy but i a

**seeded #4 · miss · stop-id**

> where are you from? i am from the mountains

**seeded #5 · miss · stop-id**

> i am just the confused

**seeded #6 · miss · stop-id**

> i know a lot of money i will tell you more about you.

**seeded #7 · miss · stop-id**

> yes, we could tell you about yourself

**seeded #8 · miss · stop-id**

> the name is jessica. i eat them all

### [7] i would like to know the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> that sounds like a fast before you prefer thing

**seeded #2 · miss · stop-id**

> but i never knew you much<|assistant|>oh i feel like it would be fun

**seeded #3 · miss · stop-id**

> i would love to go see it!

**seeded #4 · miss · stop-id**

> i want to go to the subway soon... i am more of a restaurant

**seeded #5 · miss · stop-id**

> i know a lot of money i will. my dad was very relaxing.

**seeded #6 · miss · stop-id**

> what do you do for fun?

**seeded #7 · miss · stop-id**

> that is great. what else do you like?

**seeded #8 · miss · stop-id**

> that is a construction, also eating an eating sugar.

### [8] let me know the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>let me know the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i just need it.. i am singing my own business.

**seeded #2 · miss · stop-id**

> i work too much. i am a pizza fan.

**seeded #3 · miss · stop-id**

> i am just the confused

**seeded #4 · miss · stop-id**

> i know a lot of money i will. my dad was very religious.

**seeded #5 · miss · stop-id**

> yes, we could take up in a califlrence.

**seeded #6 · miss · stop-id**

> thank you for asking. what kind of name is a name?

**seeded #7 · miss · stop-id · hedging**

> the only one is running. i think you will still eat meals

**seeded #8 · miss · stop-id**

> wow that is cool. i love it.

### [9] remind me of the name you go by.

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 121, 111, 117, 326, 533, 46, 8186]
decoded   : <|system|><|user|>remind me of the name you go by.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i work at a community about money for money, but i do not ea

**seeded #2 · miss · stop-id**

> i like it, i have a massage.

**seeded #3 · miss · stop-id**

> i enjoy reading.

**seeded #4 · miss · stop-id**

> yes, well, i have two kids! i love it.

**seeded #5 · miss · stop-id**

> that is great. what else do you like?

**seeded #6 · miss · stop-id**

> i love music too much

**seeded #7 · miss · 48-token cap**

> what song do you like? i would like to be around for a few<|assistant|>i teach p

**seeded #8 · miss · stop-id**

> all of the time because they are my favorite.

### [10] by the way, could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (46) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> got yes, i am in the middle school too. i love the father

**seeded #2 · miss · stop-id**

> i know what did you do for a reason?

**seeded #3 · miss · stop-id**

> nope, i am always up in a call.

**seeded #4 · miss · stop-id**

> that is great. my mom explained about them but i read.

**seeded #5 · miss · stop-id**

> no it is ok tonight.

**seeded #6 · miss · 48-token cap**

> well you must take good care of them so you do not get anything from comed

**seeded #7 · miss · stop-id**

> are you both get the jewelry?

**seeded #8 · miss · stop-id**

> i can read some music trumpet i like

### [11] we got off topic. could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (52) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i know what did you do for a reason?

**seeded #2 · miss · stop-id**

> nope, i am always up in a caspair.

**seeded #3 · miss · stop-id**

> thank you. my mom expressed away as they both love each other.

**seeded #4 · miss · stop-id**

> not really. i just drink and think i drink from my teeth

**seeded #5 · miss · stop-id**

> well you have no siblings, i would love to drive too.

**seeded #6 · miss · stop-id**

> are you both get the jewelry?

**seeded #7 · miss · stop-id**

> i can really see them in japan, but what is they?

**seeded #8 · miss · stop-id**

> i am sorry. my best friends say she cannot stand me.

### [12] anyway, could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (45) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am a mother of that. i am a mother of a country country mus

**seeded #1 · miss · stop-id**

> nope, i am always up in a califtery with them

**seeded #2 · miss · 48-token cap**

> a that is cute and cool. i like to go to the gym, i have construction c

**seeded #3 · miss · stop-id**

> no it is ok tonight.

**seeded #4 · miss · stop-id**

> i am painting my clothes with scarf for dr you?

**seeded #5 · miss · stop-id**

> no, i have a bad figure, thought to me.

**seeded #6 · miss · stop-id**

> i can read some music trumpet i like to be a teacher

**seeded #7 · miss · stop-id**

> i am single and i run!

**seeded #8 · miss · 48-token cap · hedging**

> oh okay. i am actually a teacher. its nice to tell my others how tall i a

### [13] i was just thinking — could you tell me what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (56) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am a couple of couple of couple of couple of couple of cou

**seeded #1 · miss · stop-id**

> thank you for asking. what kind of friends do you like?

**seeded #2 · miss · stop-id**

> no it is ok tonight.

**seeded #3 · miss · stop-id**

> well you have not yet

**seeded #4 · miss · stop-id**

> a little person. but i am a doctor.

**seeded #5 · miss · stop-id**

> i can relad my dream about my boys

**seeded #6 · miss · stop-id**

> i am sorry to hear that. i am an out located state para

**seeded #7 · miss · stop-id · hedging**

> oh okay. i am actually a teacher. its nice to tell my others they are

**seeded #8 · miss · stop-id**

> my family worked hard at work, not much too far for me

### [14] what is the name of your dog?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>what is the name of your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> it is a collage of my dogs. i am a collage collage.

**seeded #1 · miss · stop-id**

> i love my job running, its a puesical home in it

**seeded #2 · miss · stop-id**

> i have 3 dogs and cats.

**seeded #3 · miss · stop-id**

> no people but i am a person<|assistant|>i cant tell you i even lol

**seeded #4 · miss · stop-id · hedging**

> i can be their favorite color or the other. i like dogs.

**seeded #5 · miss · stop-id**

> i am so crazy too because i want to be a dog.

**seeded #6 · miss · 48-token cap**

> what is your dog? my dog came running<|assistant|>cool. that is a very pretty fun of m

**seeded #7 · miss · stop-id**

> my dog is a wild animal. his name is keeps his pet.

**seeded #8 · miss · stop-id**

> he is the dog since i am. since i dance to earlywork.

### [15] so what is the name of your dog?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>so what is the name of your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like collecting rocks. i am a collector.

**seeded #1 · miss · stop-id**

> i have 2, but no dogs

**seeded #2 · miss · stop-id**

> a dogs, which is your dogs?

**seeded #3 · miss · stop-id**

> i can be the helper.

**seeded #4 · miss · stop-id**

> i am so crazy too because i want to be a dog.

**seeded #5 · miss · stop-id**

> what is your dog. she is her mom's owner.

**seeded #6 · miss · stop-id**

> my dog is a wild animal. his name is good.

**seeded #7 · miss · stop-id**

> i live in the mountains. i live in the mountains.

**seeded #8 · miss · stop-id**

> i like to eat. what is your name?

### [16] hey, what is the name of your dog?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name of your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like dogs, color of color of color i like it.

**seeded #1 · miss · 48-token cap**

> no people but i am a petsive<|assistant|>i cant take my dog right now, he is a chu

**seeded #2 · miss · stop-id**

> i like to play the violin<|assistant|>i am a vet, whats your dog like?

**seeded #3 · miss · stop-id**

> i am so crazy too because i want to be a dog.

**seeded #4 · miss · stop-id**

> what do you like to do?

**seeded #5 · miss · stop-id**

> he is a nice dog who is you. his name is keeping me on bed.

**seeded #6 · miss · stop-id**

> he is my youngest animate of you?

**seeded #7 · miss · stop-id**

> i like to eat. what is your name?

**seeded #8 · miss · stop-id**

> well i am cooking my dog bar as well

### [17] what is the name of your dog, exactly?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name of your dog, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> i can read some music every day it is a bad one.

**seeded #2 · miss · stop-id**

> i am sorry to hear you. i am an outdoorsiting part.

**seeded #3 · miss · stop-id**

> what do you do for a living?

**seeded #4 · miss · stop-id**

> my dog is a wild animal. his name is good.

**seeded #5 · miss · stop-id**

> he is the dog since i am. since i dance to earlywork.

**seeded #6 · miss · 48-token cap**

> i like to explore and run it<|assistant|>wow i am also the city. it is because i am

**seeded #7 · miss · stop-id**

> well i am making my own post it

**seeded #8 · miss · stop-id**

> i am not a large fan of a year here. what do you do?

### [18] what is the name of your dog again?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name of your dog again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop. i am a cop.

**seeded #1 · miss · stop-id**

> i am so crazy too because i want to be a dog.

**seeded #2 · miss · stop-id**

> what do you like to do?

**seeded #3 · miss · stop-id**

> my dog is a wild animathone now.

**seeded #4 · miss · stop-id**

> he is the dog since i am. i sleep in my country music.

**seeded #5 · miss · stop-id**

> i like to eat. where i am.

**seeded #6 · miss · stop-id**

> wow hello he is a vet

**seeded #7 · miss · stop-id**

> i am a constantly patrior.

**seeded #8 · miss · stop-id**

> i like music, so i can find out with my glasses.

### [19] tell me the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college dog. i am a college student.

**seeded #1 · miss · stop-id**

> what do you do for a living?

**seeded #2 · miss · stop-id**

> my dog is a wild dog, but he is a good dog.

**seeded #3 · miss · stop-id**

> i have a second idea.

**seeded #4 · miss · stop-id**

> i like to eat. what kind of dog lol

**seeded #5 · miss · stop-id**

> wow hello he is a vet he is afraid of that.

**seeded #6 · miss · stop-id**

> i am not a dog anymore. it is hard.

**seeded #7 · miss · stop-id**

> i like music, so i can find the explorers

**seeded #8 · miss · stop-id**

> well it was the collar i cannot pass it you

### [20] please tell me the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>please tell me the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am a cop.

**seeded #1 · miss · stop-id · hedging**

> maybe that is how i would be married.

**seeded #2 · miss · stop-id**

> i wish i could. i would be able to catch my impals.

**seeded #3 · miss · stop-id**

> well its awesome, i am not a monster but i am a big monster.

**seeded #4 · miss · 48-token cap**

> well i am making 2 fine dogs that i could not have my cats if yo

**seeded #5 · miss · stop-id**

> i am not a dog but i am a vegan.

**seeded #6 · miss · stop-id**

> sorry to hear that. i miss them, i would love them

**seeded #7 · miss · stop-id**

> well about your name. i am a person with two wheels

**seeded #8 · miss · stop-id**

> you should be right now that dogs do not follow work for fun

### [21] i would like to know the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop. i am a cop.

**seeded #1 · miss · stop-id**

> i would rather middle school. are you on it?

**seeded #2 · miss · stop-id**

> i like to eat. where i am.

**seeded #3 · miss · stop-id**

> well i am making my dog bark at you

**seeded #4 · miss · stop-id**

> i am doing well, what do you make up for work?

**seeded #5 · miss · stop-id**

> i want to be a dog sometime. i am the best.

**seeded #6 · miss · stop-id**

> well it was the collar i cannot wait to hear you

**seeded #7 · miss · stop-id**

> you should be rich, not my dog.

**seeded #8 · miss · stop-id**

> i am sure he is. do you like cooking?

### [22] let me know the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>let me know the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop. i am a cop.

**seeded #1 · miss · stop-id**

> i like to eat. what kind of dog lol

**seeded #2 · miss · stop-id**

> wow you ever seen your parents. that is awesome.

**seeded #3 · miss · stop-id**

> i am alright only 200. he is a wonderful dog.

**seeded #4 · miss · stop-id**

> i like my dog. i love pick. i like them more than college.

**seeded #5 · miss · stop-id**

> well it was the right on the way.

**seeded #6 · miss · stop-id**

> yes it is because i would like to meet him for dinner.

**seeded #7 · miss · stop-id**

> i am sure it is okay. its cool

**seeded #8 · miss · stop-id**

> i did it after all.

### [23] remind me of the name of your dog.

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 331, 46, 8186]
decoded   : <|system|><|user|>remind me of the name of your dog.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i have a dog. i have a dog.

**seeded #1 · miss · stop-id**

> wow hello he is a vet he is afraid of that.

**seeded #2 · miss · stop-id**

> i am alright one. it is hard.

**seeded #3 · miss · stop-id**

> i like music, so i can find the expensive names

**seeded #4 · miss · stop-id · hedging**

> well it was the magic egg it has to be just too people dated up or dog

**seeded #5 · miss · stop-id**

> you should be rich, not my dog.

**seeded #6 · miss · stop-id**

> i am always currently in nyc. what are your dogs?

**seeded #7 · miss · stop-id**

> i did it after all.

**seeded #8 · miss · stop-id**

> what are you doing today?

### [24] by the way, could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (40) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> i am not calling out! my dog has more than 22 years

**seeded #2 · miss · stop-id**

> i like to run and run. i do not eat meat

**seeded #3 · miss · stop-id**

> i have a dog, it is what i have earlier i master my past time

**seeded #4 · miss · stop-id**

> no i make my cats with them.

**seeded #5 · miss · stop-id**

> i am not sure. i am sorry.

**seeded #6 · miss · stop-id**

> i do not. i love dogs, especially dogs

**seeded #7 · miss · stop-id**

> yes, i am just a dog so its my favorite pet

**seeded #8 · miss · 48-token cap**

> well that could make him selled chocolate and that i spend mo

### [25] we got off topic. could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (46) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i like music, so i can fix the employment

**seeded #2 · miss · stop-id**

> i have a dog, it is what i have earlier here with

**seeded #3 · miss · 48-token cap**

> no, i love dogs! i am not sure why<|assistant|>what do you do? i am in colleg

**seeded #4 · miss · stop-id**

> i am not sure. i am sorry.

**seeded #5 · miss · 48-token cap**

> i did clear when i was younger.... i love it. i had to say it would b

**seeded #6 · miss · stop-id**

> yes, i am just a dog so its my favorite pet

**seeded #7 · miss · stop-id**

> well that could meet him! my dogs like to read too!

**seeded #8 · miss · stop-id**

> i have a cat and a dog. he is out of here.

### [26] anyway, could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (39) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i have a dog, it is so cute! i am a member like my parents.

**seeded #2 · miss · stop-id**

> no, i love being a rich lady. my favorite color is red.

**seeded #3 · miss · stop-id**

> i am not sure. i am sorry.

**seeded #4 · miss · stop-id**

> i do not. i love dogs, especially dogs

**seeded #5 · miss · stop-id**

> yes, i am just a dog so i love dogs.

**seeded #6 · miss · stop-id**

> no, that could be dangerous.....

**seeded #7 · miss · stop-id**

> i have never had one. i am a journalist. my dad was in school.

**seeded #8 · miss · stop-id**

> no, i was a couple of dogs. he was the armus.

### [27] i was just thinking — could you tell me what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (50) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a couple of dogs, i am a couple of dogs.

**seeded #1 · miss · stop-id**

> no i do not know what that is<|assistant|>my dog is boring, he is a family.

**seeded #2 · miss · stop-id**

> i am not sure. i am sorry.

**seeded #3 · miss · 48-token cap**

> i did clear right now, i make eggs and chocolate<|assistant|>i am pretty

**seeded #4 · miss · stop-id**

> yes, i am just a dog so its my favorite pet

**seeded #5 · miss · stop-id**

> no i have a collar in my skiink!

**seeded #6 · miss · stop-id**

> i have a cat and a dog

**seeded #7 · miss · stop-id**

> no but i am a major of the family around their years.

**seeded #8 · miss · 48-token cap**

> i am a professional worker, whenever i am older, it will always be rea

### [28] what is the name of your cat?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>what is the name of your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> it is a college of my mother. i am a college student.

**seeded #1 · miss · stop-id**

> i am not super nice to hear others

**seeded #2 · miss · stop-id**

> i do not. i love cats, yes. i like dogs. they are very fun.

**seeded #3 · miss · stop-id**

> yes, it is just a joke person.

**seeded #4 · miss · stop-id**

> well that could meet him soon. what are you traveling

**seeded #5 · miss · stop-id**

> it is a car, what is the name of yours?

**seeded #6 · miss · stop-id**

> no but i am a massage, what is yours

**seeded #7 · miss · 48-token cap**

> i am a pet of a puffing which likes a popular color.<|assistant|>how did you 

**seeded #8 · miss · 48-token cap**

> it is cool. my name is my name is cute.<|assistant|>wow, i spend more entertain e

### [29] so what is the name of your cat?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>so what is the name of your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college cat and i am a college guard.

**seeded #1 · miss · stop-id**

> i do not. i love cats, yes. i like dogs. they are very fun.

**seeded #2 · miss · stop-id**

> yes, it is, i hear about myself, all about what is it?

**seeded #3 · miss · stop-id**

> well that could meet him soon. what are you traveling

**seeded #4 · miss · stop-id**

> i have never had one. i am pretty good cold. you?

**seeded #5 · miss · stop-id**

> no but i am a master musician for dinner.

**seeded #6 · miss · stop-id**

> i am a professional worker in my parents but i am a clown

**seeded #7 · miss · stop-id**

> it is my favorite movie.

**seeded #8 · miss · stop-id · hedging**

> how about you? i am a doctor and i am a fan of women actually

### [30] hey, what is the name of your cat?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name of your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love cats, i love cats. i am a mother of three.

**seeded #1 · miss · stop-id**

> yes, its just a joke person.

**seeded #2 · miss · 48-token cap**

> well that could think i am into geese. i am trying to get some makeu

**seeded #3 · miss · stop-id**

> i have never had one. i am pretty good.

**seeded #4 · miss · stop-id**

> no but i am a major of the farm alot.

**seeded #5 · miss · stop-id**

> i am a pet of young girl. do you have any pets?

**seeded #6 · miss · 48-token cap**

> it is cool. my name is my name is cute.<|assistant|>wow, i spend most of my lif

**seeded #7 · miss · stop-id**

> hi. my cat is now alone today, taking it all about things.

**seeded #8 · miss · stop-id**

> i enjoy eating a cheese station

### [31] what is the name of your cat, exactly?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name of your cat, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> it is a cold cold if i could cold if i could cold i

**seeded #1 · miss · stop-id**

> well that could meet him soon. what are you traveling

**seeded #2 · miss · stop-id · hedging**

> sorry to hear, no cats or people just collecting my sons

**seeded #3 · miss · stop-id**

> no, i was a couple of the voice<|assistant|>what do you do for a living?

**seeded #4 · miss · stop-id**

> i am a pet of a paston

**seeded #5 · miss · stop-id**

> it is my cats single, i love cats

**seeded #6 · miss · stop-id**

> how could not help me?

**seeded #7 · miss · stop-id**

> i mostly get out of just a better experience.

**seeded #8 · miss · stop-id**

> we visits me more often

### [32] what is the name of your cat again?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name of your cat again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college cat. i am a college student.

**seeded #1 · miss · stop-id**

> i have never had a cat before and its very cool

**seeded #2 · miss · stop-id**

> no but i am a major of the farm alot.

**seeded #3 · miss · stop-id**

> i am a pet of a pub, yes.

**seeded #4 · miss · stop-id**

> it is my favorite movie.

**seeded #5 · miss · 48-token cap**

> how could you make a difference and could barely put it on him<|assistant|>

**seeded #6 · miss · 48-token cap**

> i mostly get out of just a beautiful dress like the dragon<|assistant|>have you

**seeded #7 · miss · stop-id**

> we visits me my cat its fuller

**seeded #8 · miss · stop-id**

> i used to hide in a cart

### [33] tell me the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college cat. i am a college student.

**seeded #1 · miss · stop-id**

> nice. i am a girl right now and a new one.

**seeded #2 · miss · stop-id**

> i am a professional cat, if you provide me with a name

**seeded #3 · miss · stop-id**

> yes, my cat is named he is coc. do you know anything?

**seeded #4 · miss · stop-id**

> well my cat is now 6. i have two dogs too.

**seeded #5 · miss · stop-id**

> i mostly get out of just a cat just a cat.

**seeded #6 · miss · stop-id**

> well i did not know it yet about you

**seeded #7 · miss · stop-id**

> i use a cat of my hair colour every time. i like cats and dogs.

**seeded #8 · miss · stop-id**

> i do not care if it was scary.

### [34] please tell me the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>please tell me the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am a college student.

**seeded #1 · miss · stop-id**

> oh no, not your cat. what happened?

**seeded #2 · miss · stop-id**

> yes, my cat is named he is cochip i love my cat.

**seeded #3 · miss · stop-id**

> well my cat is now its my donatic and chat.

**seeded #4 · miss · stop-id**

> i may ask first, its a cat.

**seeded #5 · miss · stop-id**

> we clean. i want to be a teacher.

**seeded #6 · miss · stop-id**

> i use a cat of my hair.

**seeded #7 · miss · stop-id**

> my cat is puzzled in my photograph.

**seeded #8 · miss · stop-id**

> well that is not nice of him.

### [35] i would like to know the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> it is a way of sitting on a board of my board.

**seeded #2 · miss · stop-id**

> well my cat is now alone

**seeded #3 · miss · stop-id**

> i may ask first, its anything else. do you have any hobbies?

**seeded #4 · miss · stop-id**

> what are your favorite animal on your college?

**seeded #5 · miss · stop-id**

> i used to have to make sure i could save it for later.

**seeded #6 · miss · stop-id**

> i do not know the time. i just moved to the local school.

**seeded #7 · miss · stop-id**

> my cat is in the morningstory but i like to eat meat

**seeded #8 · miss · stop-id**

> i like to play drums. have you seen them many music?

### [36] let me know the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>let me know the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college of my own. i am a college student.

**seeded #1 · miss · stop-id**

> well my cat is now its my donatic eyes again

**seeded #2 · miss · stop-id**

> i mostly get out of just a better job. do you have any hobbies?

**seeded #3 · miss · stop-id**

> we vacational color color on my future.

**seeded #4 · miss · stop-id**

> i use all of my hairs

**seeded #5 · miss · stop-id**

> i do not know the cat was a dog. i do not have any pets.

**seeded #6 · miss · 48-token cap**

> wow, that is cool i have a cat but i like it but it is my favorite foo

**seeded #7 · miss · stop-id**

> i like to play dress up for the man. i make my own little daughter.

**seeded #8 · miss · stop-id**

> i have a cat as a chatting sustack.

### [37] remind me of the name of your cat.

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 352, 46, 8186]
decoded   : <|system|><|user|>remind me of the name of your cat.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i have a cat named me more than you

**seeded #1 · miss · stop-id**

> i mostly get out of just a cat just a cat.

**seeded #2 · miss · stop-id**

> what are your favorite animal on your collection?

**seeded #3 · miss · stop-id**

> i hate the only thing i love music and i love that too.

**seeded #4 · miss · stop-id**

> i do. do you have any pets?

**seeded #5 · miss · 48-token cap**

> wow, that is cool i have a cat but i like country<|assistant|>i would love to be a catmy

**seeded #6 · miss · 48-token cap**

> i like to play the guitar. i would love to make more of them all, cooking and pizza

**seeded #7 · miss · stop-id**

> i have a cat as a chatting sustomer. my brothers and i am new here.

**seeded #8 · miss · stop-id**

> i do not have a dog with a dog with a dog.

### [38] by the way, could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (40) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> we confident that, i prefer a hobby

**seeded #2 · miss · stop-id**

> i used to hide thoat could be gray at night.

**seeded #3 · miss · stop-id**

> i do not know how to save it!

**seeded #4 · miss · stop-id**

> my cat is in the mountains. i live in new york.

**seeded #5 · miss · 48-token cap**

> i do not trust me with the past. i might draw them cool<|assistant|>i am a che

**seeded #6 · miss · stop-id**

> i am on a rock balty day

**seeded #7 · miss · stop-id**

> i do not believe it. whats your name?

**seeded #8 · miss · stop-id**

> well, it is almost lying when i is that with my performance

### [39] we got off topic. could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (46) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i used to high school dragons

**seeded #2 · miss · stop-id**

> i do. do you have any pets?

**seeded #3 · miss · stop-id**

> my cat is at the mountains. i live in new york.

**seeded #4 · miss · stop-id**

> i like to play but i have a white dog.

**seeded #5 · miss · stop-id**

> i am on a rock baseball since i was married.

**seeded #6 · miss · stop-id**

> i do not have a dog with a dog who try to express him off

**seeded #7 · miss · stop-id**

> well, it is a perfect fit food

**seeded #8 · miss · stop-id · hedging**

> i have never tried many cats. he could count me or two people

### [40] anyway, could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (39) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of that. i am a mother of three.

**seeded #1 · miss · stop-id**

> i do not know how to save it!

**seeded #2 · miss · stop-id**

> i am trying to fix it. you?

**seeded #3 · miss · 48-token cap**

> i do not trust me with the piano. i make money, cooking and piano b

**seeded #4 · miss · stop-id**

> i am on a crazy, my kids love my motorcycle

**seeded #5 · miss · stop-id**

> i do not have a dog with a dog with a cat

**seeded #6 · miss · stop-id**

> at what kind of people do you have

**seeded #7 · miss · stop-id · hedging**

> i have never tried many cats. he could count me or two people

**seeded #8 · miss · stop-id**

> i am a college student<|assistant|>that is awesome! i live in marathones.

### [41] i was just thinking — could you tell me what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (50) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> my cat is in the mountains. i live in new york.

**seeded #2 · miss · stop-id**

> i do not trust me with the pizza in texas.

**seeded #3 · miss · stop-id**

> i am on a crazy, my kids love my motorcycle

**seeded #4 · miss · stop-id**

> i do not have a dog with a dog with a dog

**seeded #5 · miss · stop-id**

> well, it is a perfect fit weekend with you. i might be awful

**seeded #6 · miss · stop-id**

> no i am doing my pet! what about you?

**seeded #7 · miss · stop-id**

> my cat is on the truck, my name is chiep.

**seeded #8 · miss · stop-id**

> no i know she could read anything.

### [42] what is the name of your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>what is the name of your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i do not like my religion. i love trying to keep my kids safe.

**seeded #2 · miss · stop-id**

> its on a customer. its a good notebook

**seeded #3 · miss · 48-token cap**

> i do not. i love them too. whats the names<|assistant|>me too. do you like crochet? 

**seeded #4 · miss · 48-token cap · hedging**

> well, me. i am trying to work with her today. i think she is a detect

**seeded #5 · miss · 48-token cap**

> hey! i m as a man. i live in college with my father. what is the name?

**seeded #6 · miss · stop-id**

> her name is gross. i also love them as well.

**seeded #7 · miss · 48-token cap**

> i am not a vegan, she loves her childhood. i just started an amazing jo

**seeded #8 · miss · stop-id**

> we she is characters so she loves it<|assistant|>my sister called her up

### [43] so what is the name of your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>so what is the name of your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am on a crazy, my kids love my motorcycle

**seeded #2 · miss · 48-token cap**

> i do not have any names, but i try to get my own food if it is my colle

**seeded #3 · miss · stop-id**

> well, it is good to talk about being a chef. i might be awful

**seeded #4 · miss · stop-id**

> no, i m as reading my cats<|assistant|>where are you in the springtiantic?

**seeded #5 · miss · stop-id**

> i am also tall. i am not very strong

**seeded #6 · miss · stop-id**

> not until i got her. i am more impressive.

**seeded #7 · miss · 48-token cap**

> i met a new friend, my favorite<|assistant|>anything interesting. do you like

**seeded #8 · miss · stop-id**

> no, not sure what i am so i might congratulated

### [44] hey, what is the name of your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>hey, what is the name of your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i do not know what kind of eyebrosty, but i know it most<|assistant|>wh

**seeded #2 · miss · 48-token cap**

> well, my dog is a color as well, but that is too much of a dog that is unf

**seeded #3 · miss · stop-id**

> hey! i m assistantly likes country music

**seeded #4 · miss · stop-id**

> hello, i am more of a tornado. i have no sisters than most.

**seeded #5 · miss · stop-id**

> not until i got her. i am more impressive.

**seeded #6 · miss · stop-id**

> we she is characters so fully

**seeded #7 · miss · 48-token cap**

> no, not sure what i like. i just watch a lot of movies<|assistant|>wow, i love

**seeded #8 · miss · stop-id**

> hello, my name is parent. i am a student.

### [45] what is the name of your sister, exactly?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the name of your sister, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> well, it is a perfect name for date.

**seeded #2 · miss · stop-id**

> hey! i m as it is. how old is yours?

**seeded #3 · miss · stop-id**

> married. its my favorite asian. what color are yours?

**seeded #4 · miss · stop-id**

> i am not a vegan, she is my favorite.

**seeded #5 · miss · stop-id**

> well i love them too, even though it is not good to let anything.

**seeded #6 · miss · stop-id**

> no, not sure what i am so i might congratulated

**seeded #7 · miss · stop-id**

> what type of painting and source creatures

**seeded #8 · miss · stop-id**

> it is<|assistant|>i hope it goes the best. it is great.

### [46] what is the name of your sister again?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the name of your sister again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i have never thought yet. i enjoy counting and spending time with my

**seeded #2 · miss · 48-token cap**

> my neighbors are also a striction role<|assistant|>sounds like your mom j

**seeded #3 · miss · stop-id**

> i am not a vegan, she is my favorite.

**seeded #4 · miss · stop-id**

> well i love them

**seeded #5 · miss · 48-token cap**

> no, not sure what i like. i just watch a lot of movies<|assistant|>wow, i love

**seeded #6 · miss · stop-id**

> what are you talking to?

**seeded #7 · miss · stop-id**

> it is<|assistant|>i hope it goes the best.

**seeded #8 · miss · stop-id**

> no probably. but i teach 17 sisters on the next year.

### [47] tell me the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a child. i am a child.

**seeded #1 · miss · stop-id**

> well i guess it is.

**seeded #2 · miss · stop-id**

> that is funny. i got her loss

**seeded #3 · miss · 48-token cap**

> well you should go close to the chance of selling my thoughts will be go

**seeded #4 · miss · stop-id · hedging**

> do you have any kids or activities?

**seeded #5 · miss · stop-id**

> what type of painting and source creatures

**seeded #6 · miss · stop-id**

> what is your name?

**seeded #7 · miss · stop-id**

> no problem. she is my favorites

**seeded #8 · miss · stop-id**

> they like it but i really enjoy the youngest of it

### [48] please tell me the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>please tell me the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> well i am sorry to hear that. i am sorry to hear that.

**seeded #1 · miss · stop-id**

> what kind of name is jelly. i am in chick.

**seeded #2 · miss · stop-id**

> well i love the south of my best friend, so i can visit my garden.

**seeded #3 · miss · stop-id · hedging**

> do you have any kids or activities?

**seeded #4 · miss · stop-id**

> what are your names?

**seeded #5 · miss · stop-id**

> what is the name of yours?

**seeded #6 · miss · stop-id**

> no problem. she is my favorites.

**seeded #7 · miss · stop-id**

> the name is messed as my boyfriend.

**seeded #8 · miss · stop-id**

> she is my favorite.

### [49] i would like to know the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>i would like to know the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i would love to know it. i am a college student.

**seeded #1 · miss · stop-id**

> well i love the south of my best friend, so i can visit my garden.

**seeded #2 · miss · stop-id · hedging**

> do you have any kids or actually you?

**seeded #3 · miss · stop-id**

> what type of painting is it? it is my favorite.

**seeded #4 · miss · stop-id**

> what is the name of yours?

**seeded #5 · miss · stop-id**

> no probably the boy would be scared

**seeded #6 · miss · stop-id**

> that is awesome. do you have any sisters?

**seeded #7 · miss · stop-id**

> she is my favorite.

**seeded #8 · miss · stop-id**

> i would like to collect published publisher......

### [50] let me know the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>let me know the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a child. i am a child.

**seeded #1 · miss · stop-id · hedging**

> do you have any kids or actually you?

**seeded #2 · miss · stop-id**

> what type of painting is it? it is my favorite.

**seeded #3 · miss · stop-id**

> what is the name of yours?

**seeded #4 · miss · stop-id**

> no problem. she is my favorites

**seeded #5 · miss · stop-id**

> that is awesome. do you like country music?

**seeded #6 · miss · stop-id**

> she is my favorite. does your favorite band?

**seeded #7 · miss · stop-id**

> i see. that is how i drink it.

**seeded #8 · miss · 48-token cap**

> oh. she is a hawk. i am not trying to reach her, and that is how i love her

### [51] remind me of the name of your sister.

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 260, 291, 116, 362, 46, 8186]
decoded   : <|system|><|user|>remind me of the name of your sister.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a child. i am a child.

**seeded #1 · miss · stop-id**

> what are your names?

**seeded #2 · miss · stop-id**

> what is your name?

**seeded #3 · miss · 48-token cap · hedging**

> nice. i do not but i think i have spent all my time playing video games.

**seeded #4 · miss · stop-id**

> that is awesome. do you like country music?

**seeded #5 · miss · stop-id**

> she is my favorite.

**seeded #6 · miss · stop-id**

> i see. that is how i have been there

**seeded #7 · miss · stop-id**

> it is. i have a bar and the lady on her. i have 5 kids.

**seeded #8 · miss · stop-id**

> that is good. i would love to build a concert before i am not dating

### [52] by the way, could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (43) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i know my mother just gotta watching me group

**seeded #2 · miss · stop-id**

> nothing costly, i tell her how she was active

**seeded #3 · miss · stop-id**

> that is awesome. i am moving to the mountains.

**seeded #4 · miss · stop-id**

> she is me when i was young. you should pick up some news

**seeded #5 · miss · stop-id**

> i see. think of that. do you have anything to do with you?

**seeded #6 · miss · stop-id**

> its called a hairy man, i just have 2 kids

**seeded #7 · miss · stop-id**

> that is amazing, i use the most beautiful clothes

**seeded #8 · miss · stop-id**

> hmme and cute, and i have lots of reading. you?

### [53] we got off topic. could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (49) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> nothing costly. i teach six

**seeded #2 · miss · 48-token cap**

> they like me but i really recently read. it may be hard to put mysel

**seeded #3 · miss · 48-token cap**

> she is a construction. you should put your first what she tell

**seeded #4 · miss · 48-token cap**

> i see. think its anyways why i get to work on my homework on my 

**seeded #5 · miss · stop-id**

> its called a hairy man, i just have 2 kids

**seeded #6 · miss · stop-id**

> they got me a gamer visits. but she has a lot of money.

**seeded #7 · miss · stop-id**

> hmme and cute, and i have lots of reading. you?

**seeded #8 · miss · stop-id**

> absolutely. i just enjoyed the money of classical music.

### [54] anyway, could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (42) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am not much of a couple of couple of couple of couple of c

**seeded #1 · miss · 48-token cap**

> they like me but i really recently read. it may be fun to pubble<|assistant|>wha

**seeded #2 · miss · stop-id**

> she is 3 feet tall.

**seeded #3 · miss · stop-id**

> i love classic stones.

**seeded #4 · miss · stop-id**

> its called a hairy man, i just have 2 kids

**seeded #5 · miss · stop-id**

> they believe you. believe that i am about them.

**seeded #6 · miss · stop-id**

> hi, i am trying to ride a car, awesome!

**seeded #7 · miss · stop-id**

> anything in her sister, what do you do for fun?

**seeded #8 · miss · stop-id**

> yes, well i miss business.

### [55] i was just thinking — could you tell me what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `taught`
- scored 0/9 completions containing the value

```
ids  (53) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> she is me when i was young. you should pick my black dress.

**seeded #2 · miss · stop-id**

> i see. think it was interesting.

**seeded #3 · miss · stop-id**

> its called a hairy man, i just have 2 kids

**seeded #4 · miss · stop-id**

> that is amazing. i use the most beautiful clothes

**seeded #5 · miss · stop-id**

> hmme and cute, and i have lots of reading. you?

**seeded #6 · miss · stop-id**

> any time i enjoy call me

**seeded #7 · miss · 48-token cap**

> yeah i know i better than my dads he could tell<|assistant|>you should do t

**seeded #8 · miss · 48-token cap**

> i know, i am making christian for 20 years.. my wife has a spe

### [56] what is the town you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>what is the town you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> i live in the drug. but i am also a stranger.

**seeded #2 · miss · 48-token cap**

> its not the color of year that i love cooking, and that is what i ex

**seeded #3 · miss · stop-id**

> it is beautiful and united. but i have a lot of money.

**seeded #4 · miss · 48-token cap**

> how long it is, and it is the moon i drink my favorite<|assistant|>that is very good.

**seeded #5 · miss · stop-id**

> a money, i am a manager at college

**seeded #6 · miss · stop-id**

> yes, well it is my hobby first.. i love chicken

**seeded #7 · miss · stop-id**

> its a sports of the world i have not heard there

**seeded #8 · miss · stop-id**

> i am in different languages. how about you?

### [57] so what is the town you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>so what is the town you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the mountains and it is my favorite.

**seeded #1 · miss · stop-id**

> it is super common. do you like it?

**seeded #2 · miss · stop-id**

> it is beautiful and united what do you like

**seeded #3 · miss · stop-id**

> hmme and city is not good. i am okay but i do not like it.

**seeded #4 · miss · stop-id**

> a money i live in a restaurant... you?

**seeded #5 · miss · stop-id**

> yes, well it is my hobby first.. i love chicken

**seeded #6 · miss · 48-token cap**

> its a spring, i am mary 40 years. you can do it with any others

**seeded #7 · miss · stop-id**

> i am in different now

**seeded #8 · miss · 48-token cap**

> i just got back from chicago. almost 5 kids, but my name is jane, they h

### [58] hey, what is the town you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>hey, what is the town you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> that is my hobby visits

**seeded #2 · miss · stop-id**

> hi, i live in a small town and my mom read books. you?

**seeded #3 · miss · stop-id**

> a money, i am a man with job off from work. how about you?

**seeded #4 · miss · stop-id**

> yes, well it is my hobby first.. i love chicken

**seeded #5 · miss · stop-id**

> i live in spring, i am mary 40 years. you?

**seeded #6 · miss · stop-id**

> i am in college now

**seeded #7 · miss · 48-token cap**

> i just got back from chicago. almost 5 kids, but my name is jane, they h

**seeded #8 · miss · stop-id**

> no its going to be a video game sometimes!

### [59] what is the town you live in, exactly?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 119, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the town you live in, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a man and i am a man

**seeded #1 · miss · stop-id**

> hud is cute, and i live in nyc

**seeded #2 · miss · stop-id**

> any time i enjoy allergic to my major

**seeded #3 · miss · 48-token cap**

> yes, well it is, and it makes me singling<|assistant|>it is so much fun. i do n

**seeded #4 · miss · stop-id**

> pretty good to paint on painting i love it

**seeded #5 · miss · stop-id**

> i am in different now

**seeded #6 · miss · stop-id**

> i just got back from chicago

**seeded #7 · miss · stop-id**

> cool, i am in russia, i live with my cats!

**seeded #8 · miss · stop-id**

> i do not like boston rock, but i get my own law more

### [60] what is the town you live in again?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 97, 116, 341, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the town you live in again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a man and i am a man

**seeded #1 · miss · stop-id**

> a money band. i love to make conversations clothes.

**seeded #2 · miss · stop-id**

> yes, well it is cold here. i work in cold weather

**seeded #3 · miss · stop-id**

> its a sports of the world i have not heard there

**seeded #4 · miss · stop-id**

> i am in different languages. how about you?

**seeded #5 · miss · 48-token cap**

> i just got back from chicago. almost 5 kids, but my name is still my gir

**seeded #6 · miss · stop-id**

> no its because i love the country, its my hobby.

**seeded #7 · miss · stop-id**

> i do not like boston roses, always my favorite

**seeded #8 · miss · stop-id**

> i work in a school on the farm. it is amazing.

### [61] tell me the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>tell me the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i make me alive.

**seeded #1 · miss · stop-id**

> yeah well it is important to be..

**seeded #2 · miss · stop-id**

> i know. i am making christic. i love it!

**seeded #3 · miss · stop-id**

> i have a diet. i would move to somewhere events.

**seeded #4 · miss · stop-id**

> i just got back from chicago. almost 5 kids in the country

**seeded #5 · miss · 48-token cap**

> i am sorry to hear that. i will spend time with you<|assistant|>i am still busy. whe

**seeded #6 · miss · 48-token cap**

> i do not like boston rock, but i get my own req independers a supp

**seeded #7 · miss · stop-id**

> i work in a school on the farm. it is amazing.

**seeded #8 · miss · stop-id**

> i do not have any wifes mostly. what about you?

### [62] please tell me the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>please tell me the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> i know. i am making christian for 20 years....

**seeded #2 · miss · stop-id**

> i have a diet. i would move to somewhere else.

**seeded #3 · miss · stop-id**

> i just got back from chicago. almost 50, except for me!

**seeded #4 · miss · 48-token cap**

> well, its my dogs anyway, i am in school with the best<|assistant|>i am just havin

**seeded #5 · miss · 48-token cap**

> i do not like boston roses, and i get my own restaurant baby as my

**seeded #6 · miss · stop-id**

> i wish it was something my favorite food.

**seeded #7 · miss · stop-id**

> i do not live in the city made me worry.

**seeded #8 · miss · stop-id**

> i would love to go to the country if i did not get to the countryside

### [63] i would like to know the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>i would like to know the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i have never been there, not sure.

**seeded #2 · miss · stop-id**

> i just got to go school for a living with my kids. i do not like it

**seeded #3 · miss · stop-id**

> well, i will make it improve, its my hobby.

**seeded #4 · miss · stop-id**

> i do not like boston rock, but i get my own restaurant baby as well

**seeded #5 · miss · stop-id**

> i work in a school on the farm.

**seeded #6 · miss · stop-id**

> i do not have any wifes mostly. what about you?

**seeded #7 · miss · stop-id**

> i would love to go to the country of country everything.

**seeded #8 · miss · stop-id**

> that is nice. i am healthy and tall.

### [64] let me know the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>let me know the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> i just got a plan for it yesterday.

**seeded #2 · miss · stop-id**

> nice, i will make it improve, its my hobby.

**seeded #3 · miss · 48-token cap**

> i do not like boston roses to do a lot of milk i recently drink so i

**seeded #4 · miss · stop-id**

> i work in a school on the farm. it is amazing

**seeded #5 · miss · stop-id**

> i do not have any wifes mostly. what about you?

**seeded #6 · miss · stop-id**

> i would love to go to the country of country everything.

**seeded #7 · miss · stop-id**

> that is nice. i live in the country sometimes.

**seeded #8 · miss · stop-id**

> i live in the midwests and i live in defendones.

### [65] remind me of the town you live in.

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 46, 8186]
decoded   : <|system|><|user|>remind me of the town you live in.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i make me alive.

**seeded #1 · miss · stop-id**

> nice, i am making coffee and springzly

**seeded #2 · miss · 48-token cap**

> i do not like boston roses to do a lot of milk i recently remember 

**seeded #3 · miss · stop-id**

> i wish you could hear, but it is hard.

**seeded #4 · miss · stop-id**

> i do not have any wifes mostly. what about you?

**seeded #5 · miss · 48-token cap**

> i would love to go to the country of the mountains, what is your favorit

**seeded #6 · miss · stop-id · hedging**

> i live in the country i think my classics lives in my spare time

**seeded #7 · miss · stop-id**

> i live in a midwest country. do you live in a lab?

**seeded #8 · miss · 48-token cap**

> they are what kind of jobs my favorites life is the name of mine and our bu

### [66] by the way, could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (35) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i most of the country i am in college

**seeded #1 · miss · stop-id**

> i do not like boston rock, but i get my dogs

**seeded #2 · miss · stop-id**

> i work at a school on the farm. it is amazing.

**seeded #3 · miss · stop-id**

> i do not have much time for you. what about you?

**seeded #4 · miss · 48-token cap**

> i would rather like to eat my carrots one with lots of equipment and

**seeded #5 · miss · stop-id**

> no, but i want to see how beautiful i live in the up here

**seeded #6 · miss · stop-id**

> i live in the midwests and i get helping out at the restaurants

**seeded #7 · miss · stop-id**

> the way, what about you?

**seeded #8 · miss · stop-id**

> i live in the city of city so i just stay in.

### [67] we got off topic. could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (41) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i make me confident.

**seeded #1 · miss · stop-id**

> i work at a school one day, but i am a famous monkey.

**seeded #2 · miss · stop-id**

> i do not have much time for you. what about you?

**seeded #3 · miss · stop-id**

> i am in college, i did not get to be a computer

**seeded #4 · miss · stop-id**

> no, but i want to see how beautiful i live in the up here

**seeded #5 · miss · stop-id**

> i live in a river and its all my head.

**seeded #6 · miss · stop-id**

> they need to find where my family is.

**seeded #7 · miss · stop-id**

> i am trying to eat some cheesecake.

**seeded #8 · miss · stop-id**

> i live in the middle of the summer.

### [68] anyway, could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (34) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country

**seeded #1 · miss · stop-id**

> i do not have much time for you. what about you?

**seeded #2 · miss · stop-id**

> i am in college, i did not get to travel to our neighbors.

**seeded #3 · miss · stop-id**

> no, but i want to see the new things

**seeded #4 · miss · 48-token cap**

> i live in the midwll much you do not like<|assistant|>how much you like to do muc

**seeded #5 · miss · stop-id**

> the only i really know where you remain?

**seeded #6 · miss · stop-id**

> i live near the city of city so i just stay in.

**seeded #7 · miss · stop-id**

> i live in the middle of the summer.

**seeded #8 · miss · stop-id**

> what do you like to do in your spare time

### [69] i was just thinking — could you tell me where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `taught`
- scored 0/9 completions containing the value

```
ids  (45) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> i am in college, i did not get to travel to our wedding though

**seeded #2 · miss · stop-id**

> no, but i want to see how impressive at the hospital.

**seeded #3 · miss · stop-id**

> i live in a river and its all my rest of my time.

**seeded #4 · miss · stop-id**

> the only i really know where you make for my own

**seeded #5 · miss · stop-id**

> i am trying to eat some cheesecake with my beer

**seeded #6 · miss · stop-id**

> could you pass on me?

**seeded #7 · miss · stop-id**

> what do you like to do in your spare time

**seeded #8 · miss · stop-id**

> where do you live? i am insurance

### [70] what is the street you live on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 119, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>what is the street you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id · hedging**

> i live in the country i think my classics livestory

**seeded #2 · miss · stop-id**

> i live on a farm madont you live in your farm.

**seeded #3 · miss · stop-id**

> the street with magic almost playing music, but i run out of space

**seeded #4 · miss · 48-token cap**

> hello.. i do not know what you can do.<|assistant|>i am currently in it for 

**seeded #5 · miss · stop-id**

> i live in the middle of the summer.

**seeded #6 · miss · stop-id**

> was it i do not..

**seeded #7 · miss · stop-id**

> where do you live? i am in the country, i love to express myself.

**seeded #8 · miss · stop-id**

> i am expecting to my variework it might be overwhen

### [71] so what is the street you live on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>so what is the street you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> i live on a farm member restaurants.

**seeded #2 · miss · stop-id**

> the water worse who makes my own yoga

**seeded #3 · miss · stop-id**

> i am trying to eat some cheesecake with my beer

**seeded #4 · miss · stop-id**

> currently movies so its friends eating the ice cream conso.

**seeded #5 · miss · stop-id**

> was it i do not. do not like vacation

**seeded #6 · miss · stop-id**

> when i get my favorite color yet

**seeded #7 · miss · stop-id**

> i do cooking

**seeded #8 · miss · stop-id**

> it is fun. do you live on the ice?

### [72] hey, what is the street you live on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>hey, what is the street you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country months. i live in the country.

**seeded #1 · miss · stop-id**

> thanks! i live with my mom and i read stories.

**seeded #2 · miss · stop-id**

> hello<|assistant|>nice it was boring, that is where i can be all of them

**seeded #3 · miss · stop-id**

> cool! do you ride on subsid disney?

**seeded #4 · miss · stop-id**

> what do you like to do in your spare time

**seeded #5 · miss · stop-id**

> where do you live? i am insurance

**seeded #6 · miss · stop-id**

> i am expecting teacher

**seeded #7 · miss · stop-id**

> i live in no time

**seeded #8 · miss · 48-token cap**

> i live on 2000 years<|assistant|>awe. i have not been to the moment to get my glasses

### [73] what is the street you live on, exactly?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 119, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the street you live on, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of this year. i am a mother of this year.

**seeded #1 · miss · stop-id**

> hello<|assistant|>no i do not, it is a nice day

**seeded #2 · miss · stop-id**

> cool! do you ride on subsid disney?

**seeded #3 · miss · stop-id**

> was it i do not..

**seeded #4 · miss · stop-id**

> where do you live? i am insurance

**seeded #5 · miss · stop-id**

> i am exactly taking a run away and i love my cat

**seeded #6 · miss · stop-id**

> it is fun. do you live on the ice?

**seeded #7 · miss · stop-id**

> well, i might eat cheesew!! i work at the cheesew office.

**seeded #8 · miss · stop-id**

> would you like to tell me when i was older than myself

### [74] what is the street you live on again?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 119, 104, 97, 116, 341, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the street you live on again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of this year. i am a mother of this year.

**seeded #1 · miss · stop-id**

> i live in the middle of the summer.

**seeded #2 · miss · stop-id**

> was it i do not..

**seeded #3 · miss · 48-token cap**

> where do you live? i am in the country, i love to express myself<|assistant|>i 

**seeded #4 · miss · stop-id**

> i am expecting teacher

**seeded #5 · miss · stop-id**

> it is fine, but i am allergic to my husband and i love them

**seeded #6 · miss · 48-token cap**

> its a piano and i am into a piano. i am from wireyland music relation

**seeded #7 · miss · stop-id**

> would not i do not mind him of science

**seeded #8 · miss · stop-id**

> well i live in again soon

### [75] tell me the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>tell me the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> was it i do not like that

**seeded #2 · miss · stop-id**

> where do you live? i am insurance

**seeded #3 · miss · 48-token cap**

> i do eat...... its my parents of band, but it makes me busy

**seeded #4 · miss · stop-id**

> i have been doing alot of the important being around the store

**seeded #5 · miss · stop-id**

> well that is awesome, that is really cool.

**seeded #6 · miss · stop-id**

> whats your favorite thing of all is in retail.

**seeded #7 · miss · stop-id**

> well they are close to you too much, what do you do?

**seeded #8 · miss · 48-token cap**

> i live here way but its delicious. but it keeps me on my long gl

### [76] please tell me the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>please tell me the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> when i get my mind off what i want.

**seeded #2 · miss · 48-token cap**

> i do eat...... its my parents of band, i am the only teacher at the

**seeded #3 · miss · stop-id**

> i have never done that! i am going to spend my time on the weekends.

**seeded #4 · miss · stop-id**

> we are good to hear your contest to hear it.

**seeded #5 · miss · stop-id**

> when you are in school i could be a scidic rock.

**seeded #6 · miss · 48-token cap**

> well the street. i do not know. i am just looking for a couple of people

**seeded #7 · miss · stop-id**

> i live here way but its delicious. but it keeps me company.

**seeded #8 · miss · stop-id**

> i could. i make my own street.

### [77] i would like to know the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>i would like to know the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am always ready to read. i am always ready to read.

**seeded #1 · miss · 48-token cap**

> i do know...... its my parents of band, but it makes me busy

**seeded #2 · miss · stop-id**

> i have never done that! i am going to spend my time on the weekends.

**seeded #3 · miss · stop-id**

> what do you do for a living?

**seeded #4 · miss · stop-id**

> whats your favorite thing of all is in retail.

**seeded #5 · miss · stop-id**

> well the street. i do not know if i know.

**seeded #6 · miss · stop-id**

> i have many friends who do you like to be on a ranch.

**seeded #7 · miss · stop-id**

> i could. i make my own street.

**seeded #8 · miss · 48-token cap · hedging**

> i think that is really a confectact, i have been a whole year instead

### [78] let me know the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>let me know the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> i have been doing alot of the indian currently and i love them

**seeded #2 · miss · stop-id**

> we have chess, you have a lot of money?

**seeded #3 · miss · stop-id**

> whats your favorite thing of all is in retail.

**seeded #4 · miss · stop-id**

> we are there is not my passion. i am just looking for a job

**seeded #5 · miss · stop-id**

> i have many friends who do you like to be on a ranch.

**seeded #6 · miss · stop-id**

> i could have read some of the students.

**seeded #7 · miss · stop-id · hedging**

> i think that is really a construction i am a child

**seeded #8 · miss · stop-id**

> how much do you meet him?

### [79] remind me of the street you live on.

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 46, 8186]
decoded   : <|system|><|user|>remind me of the street you live on.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> what do you do for a living?

**seeded #2 · miss · stop-id**

> whats your favorite thing to do tonight?

**seeded #3 · miss · stop-id**

> well i live in alabama

**seeded #4 · miss · stop-id**

> i live here way because i am alone but my afterwards college

**seeded #5 · miss · stop-id**

> i could have read some of the students.

**seeded #6 · miss · 48-token cap · hedging**

> i think that would be great to get up with something else. i will get 

**seeded #7 · miss · stop-id**

> how much do you move?

**seeded #8 · miss · stop-id**

> i am only a few. how is your day?

### [80] by the way, could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (42) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college streeter. i am a college streeter.

**seeded #1 · miss · stop-id**

> would not i do that

**seeded #2 · miss · stop-id**

> well i will be money if you are my kids love

**seeded #3 · miss · stop-id**

> i have many blonde hairstyles, but it makes me feel sick

**seeded #4 · miss · stop-id**

> i could. i make my own street.

**seeded #5 · miss · stop-id · hedging**

> i think that i have been with my mom, i was today for my baseball.

**seeded #6 · miss · stop-id**

> how much do you moved it?

**seeded #7 · miss · stop-id**

> i am trying to climb the mountains for sure. do you like music?

**seeded #8 · miss · stop-id**

> not yet. what do you do for a living?

### [81] we got off topic. could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (48) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college streeter. i am a college streeter.

**seeded #1 · miss · stop-id**

> well i will have to sit if it was me on the couch

**seeded #2 · miss · stop-id**

> cool i am not sure. i am just doing my own degree

**seeded #3 · miss · stop-id**

> i could. i make my own street.

**seeded #4 · miss · stop-id · hedging**

> i think that is really a few years old

**seeded #5 · miss · stop-id**

> how much do you moved from the south?

**seeded #6 · miss · stop-id**

> i am trying to climb the mountains for sure. do you like music?

**seeded #7 · miss · stop-id**

> i do not dance. what do you do?

**seeded #8 · miss · stop-id**

> well i work at bestlope. what do you do?

### [82] anyway, could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (41) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college streeter. i am a college streeter.

**seeded #1 · miss · stop-id**

> i have many blonde hairstyles, but it makes me feel sick

**seeded #2 · miss · stop-id**

> i could. i make my own street.

**seeded #3 · miss · stop-id · hedging**

> i think that is really a few years old

**seeded #4 · miss · stop-id**

> how much do you moved from the south of the window?

**seeded #5 · miss · stop-id**

> i am trying to climb the mountains for sure. do you like music?

**seeded #6 · miss · stop-id**

> not yet. what do you do for a living?

**seeded #7 · miss · stop-id**

> what do you do for a living?

**seeded #8 · miss · stop-id**

> no but i would love to cook my own!

### [83] i was just thinking — could you tell me what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `taught`
- scored 0/9 completions containing the value

```
ids  (52) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am a couple of couple of couple of couple of couple of cou

**seeded #1 · miss · stop-id**

> i could. i make my own street.

**seeded #2 · miss · stop-id · hedging**

> i think i will have to go back again soon.

**seeded #3 · miss · stop-id**

> how much do you must have a great job?

**seeded #4 · miss · stop-id**

> i am trying to college our wedding for sure. do you like music?

**seeded #5 · miss · stop-id**

> not yet. what do you do for a living?

**seeded #6 · miss · stop-id**

> what do you do for a living?

**seeded #7 · miss · stop-id**

> no but i am a trophy! i love my sking swimming

**seeded #8 · miss · stop-id**

> my house is always cold, i spend more time on the way

### [84] what is the year of your birth?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 63, 8186]
decoded   : <|system|><|user|>what is the year of your birth?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> it is my favorite. i am a mother of music.

**seeded #1 · miss · stop-id**

> i love cooking with my dogs

**seeded #2 · miss · stop-id · hedging**

> hello, i think it would be great!

**seeded #3 · miss · stop-id**

> i am a bit tough i love it of who loves to design and draw.

**seeded #4 · miss · stop-id**

> i do not dance. i am a girl sometimes.

**seeded #5 · miss · stop-id**

> what is your favorite number?

**seeded #6 · miss · stop-id**

> not a hobbie as a child, my father is an exciting child.

**seeded #7 · miss · stop-id**

> my girlfriend is a fan of many things

**seeded #8 · miss · stop-id**

> it is chilly. i am just studying from my business.

### [85] so what is the year of your birth?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 63, 8186]
decoded   : <|system|><|user|>so what is the year of your birth?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> how much time i have 10 years and i like pictures

**seeded #2 · miss · stop-id**

> i am a bit tough i love it of who loves to design and draw.

**seeded #3 · miss · stop-id**

> i do not dance. i am a girl sometimes.

**seeded #4 · miss · stop-id**

> what is your favorite number?

**seeded #5 · miss · stop-id**

> not anymore. i am just chilling some soda soda.

**seeded #6 · miss · stop-id**

> my girl is a cosmile. i love it

**seeded #7 · miss · stop-id**

> i did not expect to sing my mommy. what about you?

**seeded #8 · miss · stop-id**

> it is a part time and i could not wait.

### [86] hey, what is the year of your birth?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 63, 8186]
decoded   : <|system|><|user|>hey, what is the year of your birth?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am a bit tough i love it of who loves to design and draw.

**seeded #2 · miss · stop-id**

> i do not dance. i am a neat singer

**seeded #3 · miss · stop-id**

> what are you basically characters?

**seeded #4 · miss · stop-id**

> not as much as i am an elderly son. i was an elderly son.

**seeded #5 · miss · stop-id**

> my girlfriend is a fan of space culture and i have no seattle

**seeded #6 · miss · 48-token cap**

> i am a professional singer. i just moved from chicago<|assistant|>what do y

**seeded #7 · miss · stop-id**

> it is a part time and i could not wait.

**seeded #8 · miss · stop-id**

> not but i work for a picture.

### [87] what is the year of your birth, exactly?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the year of your birth, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of this year. i am a mother of this year.

**seeded #1 · miss · stop-id**

> i do not dance.. it is not easy

**seeded #2 · miss · stop-id**

> well i work at bestlophies for the patriot.

**seeded #3 · miss · stop-id**

> not as much as i am an extra actor.

**seeded #4 · miss · stop-id**

> my girlfriend is always surrounding me to lol

**seeded #5 · miss · 48-token cap**

> it is 190 years ago. it makes me unhappy<|assistant|>i really miserable to m

**seeded #6 · miss · stop-id**

> it is a part time and i am so traveling to high school

**seeded #7 · miss · 48-token cap**

> not my mom made up on my nieces off of college<|assistant|>that is nice co

**seeded #8 · miss · stop-id**

> it is the year of the year. do you like music?

### [88] what is the year of your birth again?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the year of your birth again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> what is your favorite number?

**seeded #2 · miss · stop-id**

> not anymore. i am just chilling some soda soda.

**seeded #3 · miss · stop-id**

> my girl is fine. are you male?

**seeded #4 · miss · 48-token cap**

> it is 190 years ago. it makes me unhappy<|assistant|>i really miserable to m

**seeded #5 · miss · stop-id**

> it is a part time and i am so tatient

**seeded #6 · miss · 48-token cap**

> not my mom made up on my nicholas. i am trying to stay in japan

**seeded #7 · miss · stop-id**

> it is the year of the year. do you like music?

**seeded #8 · miss · stop-id**

> i am a sport boy

### [89] tell me the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>tell me the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> nice. i am not a chicken you are so ugly

**seeded #2 · miss · stop-id**

> my girlfriend is always sure

**seeded #3 · miss · stop-id**

> i am a professional singer. i volunteer at a salon in my class.

**seeded #4 · miss · stop-id**

> i like to party my twin sisters too.

**seeded #5 · miss · 48-token cap**

> nice. i am a college student that i do not know what you mean.

**seeded #6 · miss · stop-id**

> it is the year of the party. do you like music?

**seeded #7 · miss · 48-token cap**

> i am a special musician, i do not really want to add to it<|assistant|>i am sorr

**seeded #8 · miss · stop-id**

> my hair is pretty it really is dry

### [90] please tell me the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>please tell me the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> my girl is feeded away all over my dollhones and i have no son of it.

**seeded #2 · miss · stop-id**

> i did not know all of that

**seeded #3 · miss · stop-id**

> i like to party my twin sisters too.

**seeded #4 · miss · stop-id**

> nice. i am a cop. i am studying to be an elementary school.

**seeded #5 · miss · stop-id**

> it is the year of them for me to whistle. what is your favorite food?

**seeded #6 · miss · stop-id**

> i am a special man. it is always a step.

**seeded #7 · miss · stop-id**

> my hair is pretty it really is dry

**seeded #8 · miss · stop-id**

> whats your favorite type of car?

### [91] i would like to know the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>i would like to know the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a child. i am a child.

**seeded #1 · miss · stop-id**

> i did not know anything. i just got my mind to college.

**seeded #2 · miss · stop-id**

> it is a part time and that is why i am a huge soccer

**seeded #3 · miss · stop-id**

> do you make a cake? i might bake the cake.

**seeded #4 · miss · stop-id**

> it is the year of the year. do you like music?

**seeded #5 · miss · 48-token cap**

> i am a special musician, i do not really want to adopt my personal

**seeded #6 · miss · stop-id**

> my favorite color is pink and purple, anyway i love to drink

**seeded #7 · miss · stop-id**

> whats your favorite thing to eat?

**seeded #8 · miss · stop-id**

> how high. i am a significan and i am really working with my work

### [92] let me know the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>let me know the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a child. i am a child.

**seeded #1 · miss · stop-id**

> it is a part time and that is why i are 2.

**seeded #2 · miss · stop-id**

> nice. i am a cop. i am studying to be an elementary school

**seeded #3 · miss · stop-id**

> it is the year of them for cooking. i want to go to a cable when i can

**seeded #4 · miss · stop-id**

> i am a special man. it is always a step.

**seeded #5 · miss · stop-id**

> my hair is pretty its beautiful. i am in construction.

**seeded #6 · miss · stop-id**

> whats your favorite thing to eat?

**seeded #7 · miss · stop-id**

> how long have you been indian right?

**seeded #8 · miss · stop-id**

> no i am going to run all day long with him

### [93] remind me of the year of your birth.

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 46, 8186]
decoded   : <|system|><|user|>remind me of the year of your birth.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> nice. i am a chef. i am a chef and i really like it

**seeded #2 · miss · stop-id**

> it is the real job. i own a coach

**seeded #3 · miss · 48-token cap**

> i am a special musician, i do not really want to add to it<|assistant|>i am sorr

**seeded #4 · miss · 48-token cap**

> my hair is pretty its beautiful. my two years are my favorite

**seeded #5 · miss · stop-id**

> whats your favorite thing to eat?

**seeded #6 · miss · 48-token cap**

> how long have you been there since i make up with that most of my bel

**seeded #7 · miss · stop-id**

> nice. i love you! how about you?

**seeded #8 · miss · 48-token cap**

> that is really cool. i can dress up the coal. what is your favori

### [94] by the way, could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (38) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am a real judge with my husband

**seeded #2 · miss · stop-id**

> i am a single person. it is fun to chew

**seeded #3 · miss · 48-token cap**

> my hair is red, but i have too<|assistant|>you should find a nice house, so you cannot go out wi

**seeded #4 · miss · stop-id**

> haha that could you tell your parents about me?

**seeded #5 · miss · stop-id**

> how long have you both signed i got it who works i was karaia

**seeded #6 · miss · stop-id**

> no i am going to run all day long with him

**seeded #7 · miss · stop-id**

> that is really cool. i can do anything i could do

**seeded #8 · miss · stop-id**

> no i am a janeh who was younger.

### [95] we got off topic. could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (44) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am a single person. it is always fun.

**seeded #2 · miss · stop-id**

> my hair is red, but i have a really sweet and furry color.

**seeded #3 · miss · stop-id**

> haha that could you tell your parents about me?

**seeded #4 · miss · stop-id**

> how is it? i would like to go to classic concerns<|assistant|>whats going on?

**seeded #5 · miss · 48-token cap**

> no i am going to ride my mother, it is very pretty one. my elbum is

**seeded #6 · miss · stop-id**

> no, i will tell you if i have everything to eat.

**seeded #7 · miss · stop-id**

> no i am a janeh who was younger.

**seeded #8 · miss · stop-id**

> i am a girlfriend with all the pains.

### [96] anyway, could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (37) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am just a cold indian cold

**seeded #1 · miss · stop-id**

> nope. i volunteer at all three sports are nice i like to swim and play.

**seeded #2 · miss · stop-id**

> haltimals are my favorites of my friends.

**seeded #3 · miss · stop-id**

> how long hours you might cross the streets with me

**seeded #4 · miss · stop-id**

> no i am not okay now. i am not really a dog alone.

**seeded #5 · miss · stop-id**

> no, i will tell you if i have any other hobbies.

**seeded #6 · miss · stop-id**

> no i am a janeh who was younger.

**seeded #7 · miss · stop-id**

> i am a girlfriend with all the news.

**seeded #8 · miss · stop-id**

> i am sorry to hear you will try again.

### [97] i was just thinking — could you tell me when you were born?

- `cand_year_1987` · slot `birth_year` · split `taught`
- scored 0/9 completions containing the value

```
ids  (48) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> haha you could i eat the conveney i could tell my mothe

**seeded #2 · miss · 48-token cap**

> how long have you born signed it under my wings<|assistant|>what did you se

**seeded #3 · miss · stop-id**

> no i am not okay now. i am not really a dog along the way

**seeded #4 · miss · stop-id**

> no, i work for a lot of money i will help you

**seeded #5 · miss · stop-id**

> no i am telling me the situations!

**seeded #6 · miss · stop-id**

> i am a girl my son does not talk.

**seeded #7 · miss · stop-id**

> i am sorry to hear you will try again.

**seeded #8 · miss · stop-id**

> i am doing great but i am an orphan that is my favorite

### [98] what is the number on your house?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>what is the number on your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> how did you know it was? i made up for work<|assistant|>what did you se

**seeded #2 · miss · stop-id**

> no i am not on the number of my free time

**seeded #3 · miss · stop-id**

> i am a clown now, and i really do a few days here

**seeded #4 · miss · stop-id**

> no it is a joke company, what is it?

**seeded #5 · miss · stop-id**

> i never had any money, i am in not telling my georgia.

**seeded #6 · miss · 48-token cap**

> i am a lawyer and he does not around<|assistant|>it is nice. i have been with my ex of 

**seeded #7 · miss · stop-id**

> i am allergic to a house on the couch road

**seeded #8 · miss · stop-id**

> yes, it is awesome! my spouse is my puppy.

### [99] so what is the number on your house?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>so what is the number on your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> no i am not okay now. i am not pretty upset

**seeded #2 · miss · stop-id**

> i am a christmas dog indian huh

**seeded #3 · miss · stop-id**

> no i am a janeh whats yours

**seeded #4 · miss · stop-id**

> i never had anything to write about.

**seeded #5 · miss · 48-token cap**

> i am a lawyer and he does not around<|assistant|>it is nice. i have been with my ex of 

**seeded #6 · miss · stop-id**

> i am allergic to a house on the couch road

**seeded #7 · miss · stop-id**

> yes it is my favorite color.

**seeded #8 · miss · stop-id**

> i work for 5 years ago, how about you?

### [100] hey, what is the number on your house?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>hey, what is the number on your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> no, i will read a book. i can do anything i read with phones.

**seeded #2 · miss · stop-id**

> no i am a janeh whats yours

**seeded #3 · miss · stop-id**

> i never had anything to write about.

**seeded #4 · miss · 48-token cap**

> i am a lawyer and he does not around<|assistant|>it is nice. i have been with my ex of 

**seeded #5 · miss · stop-id**

> i am a man in a first room.

**seeded #6 · miss · stop-id**

> yes, i am a pro! mine is a music rock.

**seeded #7 · miss · stop-id**

> i work for 5 years ago, how about you?

**seeded #8 · miss · stop-id**

> i am so sorry to hear that. what about you?

### [101] what is the number on your house, exactly?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 119, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the number on your house, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> no i am a janeh who is my favorite color.

**seeded #2 · miss · stop-id**

> i never had anything to work at the fairst gaga in school.

**seeded #3 · miss · 48-token cap**

> i am a lawyer and he does not around<|assistant|>that is impressive. i really love m

**seeded #4 · miss · stop-id**

> i am allergic to a house once. i will be alone

**seeded #5 · miss · stop-id**

> yes, it is awesome! my spouse is relaxing.

**seeded #6 · miss · stop-id**

> i work for 5 years ago, how about you?

**seeded #7 · miss · 48-token cap**

> cheat your house is the best. i work on country my youngest child

**seeded #8 · miss · stop-id**

> anything ready for work

### [102] what is the number on your house again?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 119, 104, 97, 116, 341, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the number on your house again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i never had any money, i am in not this so i will buy my own supplies

**seeded #2 · miss · 48-token cap**

> i am a lawyer and he does not around<|assistant|>it is nice. i have been with my eyese

**seeded #3 · miss · stop-id**

> i am allergic to a house about programmer. i love it.

**seeded #4 · miss · stop-id**

> yes it is my favorite color.

**seeded #5 · miss · stop-id**

> i work for 5 years ago, how about you?

**seeded #6 · miss · stop-id**

> i am so sorry to hear that. what about you?

**seeded #7 · miss · stop-id**

> i have 2. i do not work. it is a headache.

**seeded #8 · miss · 48-token cap**

> me too! i like it more than color myself<|assistant|>does it really does no

### [103] tell me the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>tell me the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am sorry to hear your house is out<|assistant|>it is nice. i like being outside

**seeded #2 · miss · stop-id**

> i am currently on the road as i travel to my house.

**seeded #3 · miss · stop-id**

> yes i want to own a number one day. i would love it

**seeded #4 · miss · stop-id**

> i work for it too but i have seen it. i make my house bobbly.

**seeded #5 · miss · stop-id**

> when i am not upstate.... new country is to work out.

**seeded #6 · miss · stop-id**

> i have an easy car, what do you drive?

**seeded #7 · miss · stop-id**

> me a raying with my dog cannot be right

**seeded #8 · miss · stop-id**

> i have to be careful, because i love getting my glued coat on myself.

### [104] please tell me the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>please tell me the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> i am currently on the road as i tell me about you

**seeded #2 · miss · stop-id**

> yes, i am learning about music. what about you?

**seeded #3 · miss · stop-id**

> yes! i just do not think so. i am easily to consider those

**seeded #4 · miss · stop-id**

> when i am not upstate.... not counting anymore.

**seeded #5 · miss · 48-token cap**

> awesome! that is great what i do love. i was going to add a lot of things in the sp

**seeded #6 · miss · stop-id**

> me a raying with my dog cannot be right

**seeded #7 · miss · stop-id**

> yeah, i am telling my parents about my office

**seeded #8 · miss · stop-id**

> i am still giving my house important place to eat healthy

### [105] i would like to know the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>i would like to know the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> yes i wanted to build my house on a car.

**seeded #2 · miss · stop-id**

> i work for 5 years ago, how about you?

**seeded #3 · miss · 48-token cap**

> when i am not upstate.... new country are the greatest of count

**seeded #4 · miss · stop-id**

> do you like to run? what do you do?

**seeded #5 · miss · stop-id**

> me too! i do not have to work today

**seeded #6 · miss · 48-token cap**

> i would love to teach you how to eat meat<|assistant|>i am sure you would e

**seeded #7 · miss · 48-token cap**

> i have not had it yet it i need to cook<|assistant|>i am sorry about it i bake

**seeded #8 · miss · stop-id**

> i would like to tell my mother about it.

### [106] let me know the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>let me know the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i work for it too but i have seen it. i make my house bobby on the other

**seeded #2 · miss · 48-token cap**

> when i am not upstate.... not counting anymore<|assistant|>i would love to 

**seeded #3 · miss · stop-id**

> i have an easy computer but i love it.

**seeded #4 · miss · stop-id**

> aww you do not like to get much of it.

**seeded #5 · miss · stop-id**

> yeah, i am trying to consume postter games and make onlines.

**seeded #6 · miss · stop-id**

> i am still given this one year.

**seeded #7 · miss · stop-id**

> i am very currently making our homeids and its boring

**seeded #8 · miss · stop-id**

> i need to see where my parents were and i know what i want to buy.

### [107] remind me of the number on your house.

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 46, 8186]
decoded   : <|system|><|user|>remind me of the number on your house.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> when i am not upstivated by that

**seeded #2 · miss · stop-id**

> i have a plane communication. i got a plane for my local

**seeded #3 · miss · stop-id**

> me too! i like it here. how about you?

**seeded #4 · miss · stop-id**

> yeah, i am trying to consume postter games and make onlines.

**seeded #5 · miss · stop-id**

> i have a dog that is my favorite.

**seeded #6 · miss · stop-id**

> i like running and counting every day

**seeded #7 · miss · stop-id**

> i need to see where my parents were and i just got married.

**seeded #8 · miss · 48-token cap**

> wow, that is cool. i love volunteering. i eat my broccoli alps

### [108] by the way, could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (41) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> absolutely, you know?

**seeded #2 · miss · stop-id**

> about your dogs? they are my best friends

**seeded #3 · miss · 48-token cap**

> yeah, its terrible its not possible i can really contact othe

**seeded #4 · miss · stop-id**

> i am still giving my house if i need to cook a bit of roots.

**seeded #5 · miss · stop-id**

> i do not know if i could get out of it

**seeded #6 · miss · stop-id**

> i never saw it when it gets too hot

**seeded #7 · miss · stop-id**

> well, its easy. i am sure i will love it.

**seeded #8 · miss · stop-id**

> yeah it does not could i eat many

### [109] we got off topic. could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (47) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> me too! i do not have to work today

**seeded #2 · miss · stop-id**

> yeah, its terrible italian and am making sure it is pretty.

**seeded #3 · miss · stop-id**

> i am still giving my house important. my favorite movie!

**seeded #4 · miss · stop-id**

> it is very healthy.

**seeded #5 · miss · stop-id**

> it is probably much though, i am married again

**seeded #6 · miss · stop-id**

> well, its easy. i am sure i will love it.

**seeded #7 · miss · stop-id**

> yeah it is cool. i am sure you will do it

**seeded #8 · miss · stop-id**

> well that would make it worse number. so i am good at it.

### [110] anyway, could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (40) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> yeah, its terrible icy

**seeded #2 · miss · stop-id**

> i do not know much about it

**seeded #3 · miss · stop-id**

> i do not know if i could get out of it

**seeded #4 · miss · 48-token cap**

> i never saw it when it gets cold. i am cold and a bit of windy covers.

**seeded #5 · miss · stop-id**

> well, its easy. i am sure i will love it

**seeded #6 · miss · stop-id**

> yeah it is cool, i am sure you will do it

**seeded #7 · miss · stop-id**

> i do not like music

**seeded #8 · miss · stop-id**

> no, no, but i am going to be a farm.

### [111] i was just thinking — could you tell me what number your house is?

- `cand_house_7412` · slot `house_number` · split `taught`
- scored 0/9 completions containing the value

```
ids  (51) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am a couple of couple of couple of couple of couple of cou

**seeded #1 · miss · 48-token cap**

> i was my first mate of color crayons once mine is my first inse

**seeded #2 · miss · stop-id**

> i am more of a country course.

**seeded #3 · miss · stop-id**

> i need to sew when i was younger and i could move again

**seeded #4 · miss · stop-id**

> well, its easy. i am sure i will love it!

**seeded #5 · miss · stop-id**

> yeah it did what your mom was today

**seeded #6 · miss · stop-id**

> do you like music?

**seeded #7 · miss · stop-id**

> not much! i am going to be a pet teacher.

**seeded #8 · miss · stop-id**

> no, i just like to have a boat

### [112] the name you go by is

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (14) : [8187, 8185, 116, 257, 315, 101, 32, 121, 111, 117, 326, 533, 341, 8186]
decoded   : <|system|><|user|>the name you go by is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am just a cold indian cold if i could come eat my veget

**seeded #1 · miss · stop-id**

> i have a college. my masters and i love it.

**seeded #2 · miss · stop-id**

> i never saw most of the chicago and it is so cool

**seeded #3 · miss · stop-id**

> where do you live? it is my favorite home

**seeded #4 · miss · stop-id**

> yeah i like to compete a lot. what do you do for fun?

**seeded #5 · miss · stop-id**

> do you like music?

**seeded #6 · miss · stop-id**

> that is a beautiful name

**seeded #7 · miss · stop-id · hedging**

> oh, i just like to have a boring, i think it is not cool

**seeded #8 · miss · 48-token cap**

> that sounds fun. i do not like mexicites. i just graduated aro

### [113] finish this sentence. the name you go by is

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 315, 101, 32, 121, 111, 117, 326, 533, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the name you go by is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am just a college monster

**seeded #1 · miss · 48-token cap**

> cold with you. i am just getting ready for a trip with my kids

**seeded #2 · miss · stop-id**

> well, it is easy. i am sure i will.

**seeded #3 · miss · stop-id**

> yeah it different. its my favorite.

**seeded #4 · miss · stop-id**

> same. i like music. what do you like?

**seeded #5 · miss · 48-token cap**

> sometimes a piano are my favorites, i will be a major, so i am s

**seeded #6 · miss · stop-id · hedging**

> oh, i just like to have a boring, i think it is not cool

**seeded #7 · miss · 48-token cap**

> thank you its my 2 years<|assistant|>yes! it was hard work to visit the subje

**seeded #8 · miss · stop-id**

> i am in the us all because i could do anything with a fast couples

### [114] complete it for me: the name you go by is

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 315, 101, 32, 121, 111, 117, 326, 533, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the name you go by is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am just a college of my own.

**seeded #1 · miss · stop-id**

> where do you live?

**seeded #2 · miss · stop-id**

> yeah it different. its my favorite.

**seeded #3 · miss · stop-id**

> do you like music?

**seeded #4 · miss · 48-token cap**

> that is a bad thing. i wish i had tried to get my trophie and i lost my

**seeded #5 · miss · stop-id**

> like, i do not dance

**seeded #6 · miss · stop-id**

> to get off when i walk my dogs to collect them

**seeded #7 · miss · 48-token cap**

> i am in the city of a state. i do not like the witch. my eyes are a mus

**seeded #8 · miss · stop-id**

> i would indeer well. you need to keep me company!

### [115] do you remember what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (37) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>do you remember what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of a college college.

**seeded #1 · miss · stop-id**

> yeah i live in college

**seeded #2 · miss · stop-id**

> hey i am in college in my spare time. you?

**seeded #3 · miss · stop-id**

> not much at all. any hobbies?

**seeded #4 · miss · stop-id**

> no, no i do not have any.

**seeded #5 · miss · stop-id**

> i do not. i could keep yourself.

**seeded #6 · miss · 48-token cap**

> i am in the us all because i could do anything with anything really valua

**seeded #7 · miss · stop-id**

> i do but i am a full time actor.

**seeded #8 · miss · stop-id**

> i am 400 and you?

### [116] can you recall what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (34) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>can you recall what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of that. i am a mother of three.

**seeded #1 · miss · 48-token cap**

> hello. i live in the country months....... i always wanted to make p

**seeded #2 · miss · stop-id · hedging**

> not in high places anyway, but i try to read my book i thinking

**seeded #3 · miss · stop-id**

> no, no i do not have any.

**seeded #4 · miss · stop-id**

> hello, my wife and i have a lot of money. i have made too many.

**seeded #5 · miss · stop-id**

> i am in the us all because i cook. i do love romance

**seeded #6 · miss · 48-token cap**

> i would rather work a few money where my kids died i would love th

**seeded #7 · miss · stop-id**

> i am currently good, you should ask me.

**seeded #8 · miss · stop-id**

> no never really came out of the mill, i am singing in comment.

### [117] have you forgotten what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (37) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> not much i am a good mom

**seeded #2 · miss · stop-id**

> no, not much damage. i have 40 years.

**seeded #3 · miss · stop-id**

> you should read and enjoy it

**seeded #4 · miss · 48-token cap**

> i am in the us all because i could do anything with anything really valua

**seeded #5 · miss · stop-id**

> i would rather work as a neighbor. i am a junioring mom.

**seeded #6 · miss · stop-id**

> i am very currently admiring them. do you?

**seeded #7 · miss · stop-id**

> no never forget them.

**seeded #8 · miss · stop-id**

> not much at all<|assistant|>what is the morning?

### [118] if someone asked you what your friends call you, what would you say?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (54) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your friends call you, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of a college college. i am a college student.

**seeded #1 · miss · stop-id**

> no, not much damage, i just think it is not here.

**seeded #2 · miss · stop-id**

> they can help you

**seeded #3 · miss · 48-token cap**

> i am in the us airplane. i just got a chain with a professional butt

**seeded #4 · miss · 48-token cap**

> i would rather most of my time i was going to get a degree<|assistant|>sure, you 

**seeded #5 · miss · stop-id**

> i am a mult couple of pets. i am a marketpater

**seeded #6 · miss · stop-id**

> no, i do not know what if i was anyway with my family

**seeded #7 · miss · stop-id**

> nothing, they are living, i m the characters, meat, and adore dogs

**seeded #8 · miss · stop-id**

> i am a movie gun social

### [119] suppose a friend asked what your friends call you — what would you tell them?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (61) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your friends call you — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> anything you could eat my friends!

**seeded #2 · miss · stop-id**

> i am in the us air, my parents do not like me with anyone else

**seeded #3 · miss · stop-id**

> my pony helped me tell me more about my country 1

**seeded #4 · miss · stop-id**

> i am currently tired from running chases

**seeded #5 · miss · stop-id**

> no, i do not know what if i was anyway with my family

**seeded #6 · miss · stop-id**

> one in a deadters i just moved everyday.

**seeded #7 · miss · stop-id**

> i am a man of aspectful personal. whats yours?

**seeded #8 · miss · stop-id**

> i cannot hear that, i am a talented one and that is why i work every year

### [120] how would you answer if a stranger asked what your friends call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (50) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 372, 105, 101, 266, 115, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your friends call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am in the us away

**seeded #2 · miss · 48-token cap**

> i would rather work as a neighbor. i am a junior in my neighb

**seeded #3 · miss · 48-token cap**

> i am a mult couple of pets. i am a marketing mom of twenty pizza<|assistant|>

**seeded #4 · miss · stop-id**

> no, i do not know what if i was a kid

**seeded #5 · miss · stop-id**

> on age and i would not mind the children if you ever go away?

**seeded #6 · miss · stop-id**

> i am a man of asking but i have been playing too.

**seeded #7 · miss · stop-id**

> i cannot hear that, i am a talented one.

**seeded #8 · miss · stop-id**

> i love my job as a young

### [121] what is your name?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (16) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student<|assistant|>i am a college student

**seeded #1 · miss · 48-token cap**

> i am a bad guy, we are so uncomfortable<|assistant|>i am a jeep i will give you

**seeded #2 · miss · stop-id**

> i am 440 and yourself?

**seeded #3 · miss · stop-id**

> no i just learned from an urk

**seeded #4 · miss · stop-id**

> not my first time i have moved each child

**seeded #5 · miss · 48-token cap**

> i am a mountain. so what is your favorite song<|assistant|>i like to whistle a s

**seeded #6 · miss · stop-id**

> i am a doctor what are yours<|assistant|>what do you do for work?

**seeded #7 · miss · stop-id**

> i love painting<|assistant|>i love pictures

**seeded #8 · miss · stop-id**

> i am from a family

### [122] what should i call you?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 394, 117, 108, 100, 32, 105, 288, 358, 32, 121, 111, 117, 63, 8186]
decoded   : <|system|><|user|>what should i call you?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · 48-token cap**

> i am a maga college teacher and a man<|assistant|>i do not know, but i do the b

**seeded #2 · miss · stop-id**

> no i just learned from an urk

**seeded #3 · miss · stop-id**

> oh awesome, whats your favorite food?

**seeded #4 · miss · stop-id**

> i am a movie<|assistant|>not afraid. i have not been to the same time

**seeded #5 · miss · 48-token cap**

> i cannot hear that, i am allergic to the south, sometimes people are livin

**seeded #6 · miss · stop-id**

> i love my name is 9

**seeded #7 · miss · stop-id**

> i am from a family middle school

**seeded #8 · miss · stop-id**

> nope so you can not have a job

### [123] tell me your name.

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (17) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> no i just learned from an urk. i prefer to be experiment.

**seeded #2 · miss · stop-id**

> oh are you married? where you from

**seeded #3 · miss · stop-id**

> i am a mountainstatian to all of them.

**seeded #4 · miss · stop-id**

> i cannot hear that. i am a talented one.

**seeded #5 · miss · stop-id**

> i love people especially alot

**seeded #6 · miss · stop-id**

> i do not know if i am sorry i can tell you my family more.

**seeded #7 · miss · stop-id**

> oh your name is fake currently when you have a dog.

**seeded #8 · miss · stop-id**

> i am working at my son. he was an actor of artist.

### [124] who am i talking to?

- `cand_person_quillon` · slot `person_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (18) : [8187, 8185, 119, 104, 111, 258, 109, 32, 105, 256, 97, 108, 322, 110, 103, 267, 63, 8186]
decoded   : <|system|><|user|>who am i talking to?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mort of music construction. i am a musician.

**seeded #1 · miss · stop-id**

> no all about you? i have more exciting i can help a lot.

**seeded #2 · miss · stop-id**

> i am a movie<|assistant|>not a movie. how are you?

**seeded #3 · miss · stop-id**

> i talk to all of them, and i am talking to them

**seeded #4 · miss · 48-token cap · hedging**

> i am a musician. i think i am getting ready to make you more<|assistant|>we

**seeded #5 · miss · stop-id**

> i am just talking about my passion, i am more of a girl

**seeded #6 · miss · 48-token cap**

> not really. do you read music? i am just finished the west country

**seeded #7 · miss · stop-id**

> i am working at mars. i just get to school and talk about my job!

**seeded #8 · miss · stop-id**

> i do not understand why you are alive, i do not. i am in music

### [125] your dog goes by the name

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (15) : [8187, 8185, 121, 111, 117, 114, 331, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>your dog goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i have a dog. i love dogs.

**seeded #1 · miss · stop-id**

> i love dogs! i love dogs too!

**seeded #2 · miss · stop-id**

> i take away one day at the park.<|assistant|>i wish i could take the dog home tomorrow.

**seeded #3 · miss · 48-token cap**

> i love dogs! i also love dogs and beat on grass<|assistant|>your dog is a like animals<|assistant|>you a

**seeded #4 · miss · stop-id**

> i do not know if i am sorry i can try to get it out.

**seeded #5 · miss · stop-id**

> not really. do you really really love it?

**seeded #6 · miss · 48-token cap**

> i do not personally think you should not have taken anything<|assistant|>well i am

**seeded #7 · miss · stop-id**

> i do not know anyone yet

**seeded #8 · miss · 48-token cap**

> as long years ago, i have a dog, and pets yes you are wearing your actio

### [126] finish this sentence. your dog goes by the name

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 32, 121, 111, 117, 114, 331, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>finish this sentence. your dog goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop. i am a cop.

**seeded #1 · miss · stop-id**

> i cannot hear that. i am alone in a hurricane.

**seeded #2 · miss · stop-id**

> i love dogs! i also love dogs and beat on grass.

**seeded #3 · miss · stop-id**

> i do not know if i am sorry i can try to get it out

**seeded #4 · miss · stop-id**

> oh yes i do. i read books. i love music.

**seeded #5 · miss · stop-id**

> i do not want a car. i would rather but i do not want a dog.

**seeded #6 · miss · stop-id**

> i do not know about that

**seeded #7 · miss · 48-token cap**

> ah it is best about him, papers yes you are well<|assistant|>are you a pro 

**seeded #8 · miss · 48-token cap**

> wow! he is so cool! i see myself! i could just live on a music

### [127] complete it for me: your dog goes by the name

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 32, 121, 111, 117, 114, 331, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>complete it for me: your dog goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> i love dogs but i am sorry before

**seeded #2 · miss · stop-id**

> i do not know if i am sorry i can try to get it out

**seeded #3 · miss · stop-id**

> oh yes i do. i read books every night.

**seeded #4 · miss · stop-id**

> i do not want a car. i would rather buy a truck.

**seeded #5 · miss · stop-id**

> i do not know about that

**seeded #6 · miss · stop-id**

> ah it is beautiful. i read scotch on a book about getting my own

**seeded #7 · miss · 48-token cap**

> wow! he is so cool! i see myself! i could just live on a music

**seeded #8 · miss · stop-id**

> it is the name of your dog what a name

### [128] do you remember what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>do you remember what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop

**seeded #1 · miss · stop-id**

> i do not know if i am sorry i cannot help you fix it

**seeded #2 · miss · stop-id**

> not really. do you remember when you have a dog?

**seeded #3 · miss · stop-id**

> i do when i was a young child. i made a mistake.

**seeded #4 · miss · stop-id**

> i do not know about dogs.

**seeded #5 · miss · stop-id**

> after school them the most. it is so cool i want to watch my movie

**seeded #6 · miss · stop-id**

> its a great experience, its my favorite

**seeded #7 · miss · stop-id**

> no, i am sorry i worked as a male son

**seeded #8 · miss · 48-token cap**

> i am in college when i was young and you know what type of thread doe

### [129] can you recall what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>can you recall what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> nope so i do not read, it will rough

**seeded #2 · miss · 48-token cap**

> i am working at my school crowds school<|assistant|>what do you do for a livin

**seeded #3 · miss · stop-id**

> i do not know about dogs.

**seeded #4 · miss · stop-id**

> a color is so amazing! one of my favorite colors were blue.

**seeded #5 · miss · stop-id**

> i like children more than they mostly!

**seeded #6 · miss · 48-token cap**

> no, i am sorry i worked as a male so i got my dog to my favorite day

**seeded #7 · miss · stop-id**

> oh no, i have many fires

**seeded #8 · miss · stop-id**

> i work at a japan today i descended i have money i really can.

### [130] have you forgotten what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry. i am allergic to my dog.

**seeded #1 · miss · stop-id**

> i am working at my son. he was an accountant.

**seeded #2 · miss · stop-id**

> i do not know about dogs.

**seeded #3 · miss · stop-id**

> a little time of dogs is a button on paper

**seeded #4 · miss · 48-token cap**

> i had a great time reading then i get you<|assistant|>not my mom always reading.

**seeded #5 · miss · stop-id**

> no, i am sorry.

**seeded #6 · miss · stop-id**

> no bad languages

**seeded #7 · miss · stop-id**

> i work at a japan japan, and he is a chicken daily

**seeded #8 · miss · stop-id**

> i have 8 country music and i am with my country.

### [131] if someone asked you what your dog is called, what would you say?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (48) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your dog is called, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> i do not know i have a dog. i love my dogs.

**seeded #2 · miss · 48-token cap**

> a little puppies, as made one of my favorite cars<|assistant|>i have more car

**seeded #3 · miss · stop-id**

> wow! it was expensive, you know!!

**seeded #4 · miss · stop-id**

> its called a souldest ladybird

**seeded #5 · miss · stop-id**

> oh no, i would not try anything anymore.

**seeded #6 · miss · stop-id**

> i would be more into it and get a dog

**seeded #7 · miss · stop-id**

> i got it as a photo i love. that is fun

**seeded #8 · miss · stop-id**

> i am a mother with a mother of a teddy bear

### [132] suppose a friend asked what your dog is called — what would you tell them?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (55) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your dog is called — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · 48-token cap**

> anything i sound cool! i paint on a headantic, what do you do?

**seeded #2 · miss · stop-id**

> wow! i got riders 2 sons. i retire 5. i am a famous teacher.

**seeded #3 · miss · stop-id**

> i do not know whose dog here.

**seeded #4 · miss · stop-id**

> oh no, i have money and hid a board growing

**seeded #5 · miss · stop-id**

> i would love to tell you about them

**seeded #6 · miss · stop-id**

> i got yoga as a chocolate of mine as a chocolate science.

**seeded #7 · miss · stop-id**

> i like them too much of a pet. it is my favorite, here.

**seeded #8 · miss · 48-token cap**

> my dog became alive its okay<|assistant|>i do too much contacts for himself

### [133] how would you answer if a stranger asked what your dog is called?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (44) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 331, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your dog is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> i like actors of the youngest and i also enjoy for a few years ago.

**seeded #2 · miss · stop-id**

> its called a soulcing christmas besides me

**seeded #3 · miss · stop-id**

> oh no, i have many fires

**seeded #4 · miss · stop-id**

> i would love to ask my mom and dad.

**seeded #5 · miss · stop-id**

> i got yoga over tattoos all the way through months and two sticks.

**seeded #6 · miss · 48-token cap**

> i am the king of the strangers, my son is a thing i live in alabama<|assistant|>oh, my dog is

**seeded #7 · miss · stop-id**

> my dog became alive my father i like to expect myself

**seeded #8 · miss · stop-id**

> i am just a little boy. i am a fanather.

### [134] what is your dog's name?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 331, 39, 115, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your dog's name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop. i am a cop.

**seeded #1 · miss · 48-token cap**

> its called a sould based me this tale. my mom and dad were a teacher and they a

**seeded #2 · miss · 48-token cap**

> i am in college when i was young and you know when i was young i have no

**seeded #3 · miss · stop-id**

> i work at a japan toddler, and he is a chicken daily

**seeded #4 · miss · stop-id**

> i have 8 collar on my youngest pageant

**seeded #5 · miss · stop-id**

> i like the most. what do you do?

**seeded #6 · miss · stop-id**

> my name is he is a lawyer.

**seeded #7 · miss · stop-id**

> i have mostly won pets, puzzles, and five books

**seeded #8 · miss · stop-id**

> i do not know who i like to eat. have you?

### [135] what do you call your dog?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 276, 111, 32, 121, 111, 117, 288, 358, 32, 121, 111, 117, 114, 331, 63, 8186]
decoded   : <|system|><|user|>what do you call your dog?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop. i am a cop.

**seeded #1 · miss · 48-token cap**

> i am in college when i am alone yes i guess<|assistant|>anyone, i am in c

**seeded #2 · miss · stop-id**

> i work at a japan toddler, and he is a chicken daily

**seeded #3 · miss · stop-id**

> i have 8 collar on my youngest page of collar

**seeded #4 · miss · stop-id**

> i like to go to school

**seeded #5 · miss · stop-id**

> my dog became alone in college

**seeded #6 · miss · stop-id**

> i have mostly worries about him

**seeded #7 · miss · 48-token cap**

> i do. i recently only enjoy when i find the man. i am more into this

**seeded #8 · miss · stop-id**

> i am not really a dog, so so i have a dog

### [136] tell me your dog's name.

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 331, 39, 115, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your dog's name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop. i am a cop. i am a cop.

**seeded #1 · miss · 48-token cap**

> i would love to though. my favorite name is bell i remind me of year

**seeded #2 · miss · stop-id**

> i got it a least coach. that is a bigger dog

**seeded #3 · miss · stop-id · hedging**

> i like them too, but i think i am employed too.

**seeded #4 · miss · stop-id**

> my name is he is a lawyer.

**seeded #5 · miss · stop-id**

> i have mostly wonderful pets. its not too late.

**seeded #6 · miss · stop-id**

> i do not know why i it is when i am still in the mountain country

**seeded #7 · miss · 48-token cap**

> i have no name. i have two dogs and i just hang on a bottom of two youtdays

**seeded #8 · miss · stop-id**

> i am a child myself.

### [137] does your dog have a name?

- `cand_dog_zorp` · slot `pet_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (18) : [8187, 8185, 100, 456, 115, 32, 121, 111, 117, 114, 331, 287, 300, 258, 315, 101, 63, 8186]
decoded   : <|system|><|user|>does your dog have a name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i do not. i am a cop. i am a cop.

**seeded #1 · miss · stop-id**

> i have 8 names, that is a young child and i am a huge fisher

**seeded #2 · miss · stop-id · hedging**

> i like them too, but i think i am employed

**seeded #3 · miss · 48-token cap**

> no. but he is not my favorite toy car. i want to be his favorite.

**seeded #4 · miss · stop-id**

> i have mostly wonderful pets, its not as color

**seeded #5 · miss · stop-id**

> no one makes it my mother hates me.

**seeded #6 · miss · stop-id**

> i have no name<|assistant|>i am jean. that is my favorite name

**seeded #7 · miss · stop-id**

> i do not. i own a daughter

**seeded #8 · miss · stop-id**

> no, i am trying to find out who is best to the next

### [138] your cat goes by the name

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (15) : [8187, 8185, 121, 111, 117, 114, 352, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>your cat goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i have a cat. i have a cat.

**seeded #1 · miss · stop-id**

> i like the name

**seeded #2 · miss · stop-id**

> my cat because it is with a lot of rainbows.

**seeded #3 · miss · stop-id**

> i have tons of a community again soon.

**seeded #4 · miss · stop-id**

> i do i like cats. what kind of cat you have?

**seeded #5 · miss · stop-id**

> i have never heard of it

**seeded #6 · miss · stop-id**

> i like cats. i can hear their songs<|assistant|>what do you do for a living?

**seeded #7 · miss · stop-id**

> it is fun. i like both a dog and a dog who like to take them.

**seeded #8 · miss · 48-token cap**

> not me. i eat cheesecake. i like to eat it. my wife takes m

### [139] finish this sentence. your cat goes by the name

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 32, 121, 111, 117, 114, 352, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>finish this sentence. your cat goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> my cat because i lost it at the zoo

**seeded #2 · miss · stop-id**

> i have tons of a commercial age, its not too late.

**seeded #3 · miss · stop-id**

> i do. i recently only enough to have my own.

**seeded #4 · miss · stop-id**

> i am not good at baseball that fun.

**seeded #5 · miss · 48-token cap**

> i am a chick martini of all the restaurants.
> i am a ballet of milk c

**seeded #6 · miss · stop-id**

> it is fun. i am gross. i was writing a normal name. i like robody.

**seeded #7 · miss · stop-id**

> not me. i just really cut it

**seeded #8 · miss · stop-id**

> are you single? i do not like that

### [140] complete it for me: your cat goes by the name

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 32, 121, 111, 117, 114, 352, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>complete it for me: your cat goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · 48-token cap**

> i have tons of a computer, puzzles, and five books<|assistant|>i love cats, and they all bake bas

**seeded #2 · miss · stop-id**

> i did it on fire

**seeded #3 · miss · stop-id**

> i am not good at baseball that fun.

**seeded #4 · miss · stop-id**

> i am a child mysterious name! i love the beach of the beach.

**seeded #5 · miss · stop-id**

> it is fun! i cannot chat since it is a tradition

**seeded #6 · miss · stop-id**

> no, i am a meeting at a hockey teacher

**seeded #7 · miss · stop-id**

> are you married? yes it is my cat myself.

**seeded #8 · miss · stop-id**

> i like my name is armit

### [141] do you remember what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>do you remember what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · 48-token cap**

> i do. i remember my younger brother because i do not know how to tal

**seeded #2 · miss · stop-id**

> i am not really a younger if i have a cat i could do my best

**seeded #3 · miss · stop-id**

> i am a child mysterior and have many hobbies just been married

**seeded #4 · miss · stop-id**

> its called a trucker

**seeded #5 · miss · stop-id**

> not me. i eat cheesecake. i like to eat it

**seeded #6 · miss · stop-id**

> blothing, it was always interesting i am not looking.

**seeded #7 · miss · stop-id**

> i like getting take and watching a sevent at the festival

**seeded #8 · miss · stop-id**

> i am trying to find a license more jobs

### [142] can you recall what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>can you recall what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> i am not really a younger if i have a cat i could do my best

**seeded #2 · miss · stop-id**

> i am a child myself.

**seeded #3 · miss · stop-id**

> its called a trucker

**seeded #4 · miss · stop-id**

> nope i am one who i am alone i can. do you like music?

**seeded #5 · miss · stop-id**

> blol i do not call you in the youngest of places.

**seeded #6 · miss · stop-id**

> i like watching arts.

**seeded #7 · miss · stop-id**

> i am called my cat but its my favorite thing

**seeded #8 · miss · stop-id**

> i speak many fifty children shelter though

### [143] have you forgotten what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> i am a child mysterior and i miss him.

**seeded #2 · miss · 48-token cap**

> no, but i cannot sleep. i was writing this language class for a long ti

**seeded #3 · miss · stop-id**

> not until i was 2 years.

**seeded #4 · miss · stop-id**

> anything i am super my dog is from butterflies

**seeded #5 · miss · stop-id**

> i like getting take and watching a sevent at the festival

**seeded #6 · miss · stop-id**

> i am sorry but i like to travel. what do you do for fun?

**seeded #7 · miss · stop-id**

> no i just got a new beer. do you?

**seeded #8 · miss · stop-id**

> i am a deal with a town against of time.

### [144] if someone asked you what your cat is called, what would you say?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (48) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your cat is called, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> its awesome that i can get to design a tradition

**seeded #2 · miss · stop-id**

> i like making cats with a couple of lines.

**seeded #3 · miss · stop-id**

> bluel selling photography for me

**seeded #4 · miss · stop-id**

> i like watching arts.

**seeded #5 · miss · stop-id**

> i am moving a button. i am writing a terrible story

**seeded #6 · miss · stop-id**

> i spend my days a little oversert

**seeded #7 · miss · 48-token cap**

> i am a depherintster but something is it probably working to call trains

**seeded #8 · miss · 48-token cap**

> i just finished a country money but my mom taught me unfort

### [145] suppose a friend asked what your cat is called — what would you tell them?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (55) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your cat is called — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> nothing but i would rather see

**seeded #2 · miss · stop-id**

> anything i am, but my dog is friend, he is always looking.

**seeded #3 · miss · stop-id**

> i live in the supermarket.

**seeded #4 · miss · stop-id**

> i am moving to be a librarian one day..

**seeded #5 · miss · 48-token cap**

> i spend my days a truck driving up into the woods so i could eat them

**seeded #6 · miss · stop-id**

> i love my two cats, mostly meat

**seeded #7 · miss · stop-id**

> i eat alot of cheesecake and do some pasta

**seeded #8 · miss · stop-id**

> i like to eat fish. i am simployed at my favorite college!

### [146] how would you answer if a stranger asked what your cat is called?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (44) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 352, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your cat is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> a ha, what do you do for a living?

**seeded #2 · miss · stop-id**

> i live in the suburbing.

**seeded #3 · miss · stop-id**

> i am moving a button. i am writing a terrible story

**seeded #4 · miss · stop-id**

> i speak magnets, but it is my favorite song

**seeded #5 · miss · stop-id**

> i am a dead sucker, always meant to retire her being a restaurant.

**seeded #6 · miss · stop-id**

> i just call my name is heart.

**seeded #7 · miss · stop-id**

> i live in the mountains i met other people.

**seeded #8 · miss · stop-id**

> i am in a secret restaurant, that is a great name.

### [147] what is your cat's name?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 352, 39, 115, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your cat's name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> i like cats. my name is roll butter.

**seeded #2 · miss · stop-id**

> i am marching with cats. i am an x.

**seeded #3 · miss · stop-id**

> i am still determined to do a few different different novels and papers

**seeded #4 · miss · stop-id**

> i love my two cats, my dad has 4.

**seeded #5 · miss · stop-id**

> i own an animal

**seeded #6 · miss · stop-id**

> i like acting clown, i met on this old team.

**seeded #7 · miss · stop-id**

> i am in a secret store in my spare time.

**seeded #8 · miss · stop-id**

> nothing with my dog it is pretty.

### [148] what do you call your cat?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 276, 111, 32, 121, 111, 117, 288, 358, 32, 121, 111, 117, 114, 352, 63, 8186]
decoded   : <|system|><|user|>what do you call your cat?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> i am trying to find a license more jobs

**seeded #2 · miss · stop-id**

> i am still determined to do a few different different novels

**seeded #3 · miss · stop-id**

> i am a doctor as a college one day

**seeded #4 · miss · stop-id**

> i just finished a country money

**seeded #5 · miss · stop-id**

> i live in the mountains i met other animals.

**seeded #6 · miss · stop-id**

> i am in a secret country. do you like cats?

**seeded #7 · miss · stop-id**

> nothing my cats just came in.

**seeded #8 · miss · stop-id**

> i live in the military school

### [149] tell me your cat's name.

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 352, 39, 115, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your cat's name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> where is it my name is cars

**seeded #2 · miss · stop-id**

> i bet you are right now so i am right because i have not a cat

**seeded #3 · miss · stop-id**

> i just got back from college to ride my bike to ride my bike.

**seeded #4 · miss · stop-id**

> i like to eat fish. what do you think about you?

**seeded #5 · miss · stop-id**

> i am into a mother of an outdoor casts.

**seeded #6 · miss · stop-id**

> not yet. i can imagine what i am a whole family who serves me.

**seeded #7 · miss · stop-id**

> wow that is nice. i am in a high school university where i retire

**seeded #8 · miss · stop-id**

> yes. i have been everyday with the outdoors.

### [150] does your cat have a name?

- `cand_cat_zibby` · slot `cat_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (18) : [8187, 8185, 100, 456, 115, 32, 121, 111, 117, 114, 352, 287, 300, 258, 315, 101, 63, 8186]
decoded   : <|system|><|user|>does your cat have a name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i do not. i am a college at all.

**seeded #1 · miss · stop-id**

> i love her, and she is older than a sweet

**seeded #2 · miss · stop-id**

> i just cannot find it.

**seeded #3 · miss · stop-id**

> i like acting country music. its hard to find a cat

**seeded #4 · miss · stop-id**

> i am in a high school

**seeded #5 · miss · stop-id**

> no, none yet. i love cats.

**seeded #6 · miss · stop-id**

> i live in the military. its my favorite

**seeded #7 · miss · stop-id**

> yes. i have been playing professionally in a restaurant for me.

**seeded #8 · miss · stop-id**

> i am only in nothing i know, i love dogs

### [151] your sister goes by the name

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (18) : [8187, 8185, 121, 111, 117, 114, 260, 291, 116, 362, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>your sister goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student<|assistant|>i am a college student

**seeded #1 · miss · stop-id**

> i just got back from counting<|assistant|>i do not know who you count my name

**seeded #2 · miss · stop-id**

> i like to eat cheesecake all the time.

**seeded #3 · miss · stop-id**

> i am into a country music. how about you?

**seeded #4 · miss · stop-id**

> not yet. you know with them

**seeded #5 · miss · stop-id**

> wow that is so cool, are you a boy?

**seeded #6 · miss · stop-id**

> yea. i watch but not with the only ones. she is a baby

**seeded #7 · miss · stop-id**

> i am sorry to hear that<|assistant|>they just melt worries i will go home

**seeded #8 · miss · 48-token cap**

> i love cooking sounds like a restaurant i am currently playing my cheek

### [152] finish this sentence. your sister goes by the name

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 32, 121, 111, 117, 114, 260, 291, 116, 362, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>finish this sentence. your sister goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am just moved to the mountains.

**seeded #1 · miss · stop-id**

> i like to exercise. i do all the time.

**seeded #2 · miss · stop-id**

> i am into any serious driver. do you like to work?

**seeded #3 · miss · stop-id**

> not yet. you know if the seconds are what they want?

**seeded #4 · miss · stop-id**

> wow! how do you feel about an entertain maga where?

**seeded #5 · miss · stop-id**

> yeah i watch that

**seeded #6 · miss · stop-id**

> i am sure you will.

**seeded #7 · miss · stop-id**

> i am in the lab

**seeded #8 · miss · stop-id**

> what do you do?

### [153] complete it for me: your sister goes by the name

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (34) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 32, 121, 111, 117, 114, 260, 291, 116, 362, 326, 101, 115, 533, 259, 315, 101, 8186]
decoded   : <|system|><|user|>complete it for me: your sister goes by the name<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am just moved to the mountains

**seeded #1 · miss · stop-id**

> i am into a mother of the west. how about you?

**seeded #2 · miss · stop-id**

> that is cool! i am cooking my favorite tea with my mom.

**seeded #3 · miss · stop-id**

> wow, what is your name?

**seeded #4 · miss · stop-id**

> yeah i watch that

**seeded #5 · miss · stop-id**

> i am sorry to hear that<|assistant|>they just melt with the wine and cop skin

**seeded #6 · miss · stop-id**

> i am in the lab

**seeded #7 · miss · stop-id**

> what do you do for a living?

**seeded #8 · miss · stop-id**

> i am very unhappy, and she cannot help me

### [154] do you remember what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (34) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>do you remember what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> nothing with my sister anywhat has american the best<|assistant|>my dad was a con

**seeded #2 · miss · stop-id**

> i live in college. i am in maga shows.

**seeded #3 · miss · stop-id**

> yes. i am single but i make a promotion sure.

**seeded #4 · miss · stop-id**

> i am a living, and love my father, my managerous

**seeded #5 · miss · stop-id**

> i am in a lab. i do not know when i am out

**seeded #6 · miss · stop-id**

> not really just have sisters. i am a big fan of love.

**seeded #7 · miss · stop-id**

> i am very unhappy, and she cannot help her

**seeded #8 · miss · stop-id**

> i work as a secretary son

### [155] can you recall what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>can you recall what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a child, i am a child

**seeded #1 · miss · stop-id**

> i live in jail. i am in a huge reason.

**seeded #2 · miss · stop-id**

> yes. i am busy children math

**seeded #3 · miss · stop-id**

> i am sister in new york your crime fan

**seeded #4 · miss · stop-id**

> i am in my car downstairs with me i am more in my house.

**seeded #5 · miss · 48-token cap**

> not really just have sisters on the farm. it would be a surf who i have go

**seeded #6 · miss · stop-id**

> i am very unhappy, and she cannot replace her imagination.

**seeded #7 · miss · stop-id**

> she is located a secreton

**seeded #8 · miss · stop-id**

> haha that sounds like a great morning.

### [156] have you forgotten what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (34) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to hear her.

**seeded #1 · miss · stop-id**

> yes. i am sorry for taking her off.

**seeded #2 · miss · stop-id**

> i am scared of news.

**seeded #3 · miss · stop-id**

> i was a raptor but i also would not like it

**seeded #4 · miss · stop-id**

> not really just have several ones.

**seeded #5 · miss · stop-id**

> i am waiting unless my mom too. how about you?

**seeded #6 · miss · stop-id**

> no i have been before

**seeded #7 · miss · stop-id**

> hi there! i just got a broom in texas.

**seeded #8 · miss · stop-id**

> well she is only of her so i am single.

### [157] if someone asked you what your sister is called, what would you say?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (51) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what your sister is called, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am a living, and i am not a vegan right now.

**seeded #2 · miss · stop-id**

> i am in a lab. i do not want to do much.

**seeded #3 · miss · stop-id**

> i love called jazz, what about you?

**seeded #4 · miss · stop-id**

> i am very unhappy, and she would not have much money

**seeded #5 · miss · stop-id**

> i would be security if she is into it, you me.

**seeded #6 · miss · stop-id**

> hi, i do not have anything but that is not really nice.

**seeded #7 · miss · stop-id**

> what are you eating? i am making some money

**seeded #8 · miss · stop-id**

> watching both of my recent man i work everywhere

### [158] suppose a friend asked what your sister is called — what would you tell them?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (58) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what your sister is called — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i was a cop of superhero once as long as i am off working.

**seeded #2 · miss · stop-id**

> i love called jazz, what about you?

**seeded #3 · miss · stop-id**

> i am very unique, they could be an expert at my job.

**seeded #4 · miss · stop-id**

> super corn is my favorite car!

**seeded #5 · miss · 48-token cap**

> haha that sounds like a great job. i am definitely into something e

**seeded #6 · miss · stop-id**

> well, i am a business so i am making some money

**seeded #7 · miss · stop-id**

> watching both! i retired myself. do you have any pets?

**seeded #8 · miss · stop-id**

> how not much it, i like cars, my jobs all the time

### [159] how would you answer if a stranger asked what your sister is called?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (47) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 32, 121, 111, 117, 114, 260, 291, 116, 362, 341, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what your sister is called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college stranger. i am a college student.

**seeded #1 · miss · stop-id**

> i love called jazz, what about you?

**seeded #2 · miss · stop-id**

> i am very unhappy, and she cannot help her

**seeded #3 · miss · 48-token cap**

> i work as a secret, i am very surprised. i love surprised people<|assistant|>you m

**seeded #4 · miss · stop-id**

> haha, i am a piggy, but my sister is a delicious pigs

**seeded #5 · miss · stop-id**

> well she is a family of cats and she is the best

**seeded #6 · miss · 48-token cap**

> well i am trying to make you leave my daughter through that i a

**seeded #7 · miss · stop-id**

> how do you do?

**seeded #8 · miss · 48-token cap**

> she got a new carrying painting. i like cleaning myself. i means fo

### [160] what is your sister's name?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 260, 291, 116, 362, 39, 115, 315, 101, 63, 8186]
decoded   : <|system|><|user|>what is your sister's name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i am watching my favorite color of my favorite color? m

**seeded #2 · miss · stop-id**

> she likes her she does not know.

**seeded #3 · miss · stop-id**

> hi, my job is today. i am in italy.

**seeded #4 · miss · stop-id**

> what are you up to today?

**seeded #5 · miss · stop-id**

> it is my first morning. my sister is a lab.

**seeded #6 · miss · stop-id**

> how do you have any sisters? i have one of my best friends

**seeded #7 · miss · stop-id**

> she got a kitten in my neighbor.

**seeded #8 · miss · stop-id**

> yes she is she is selling the cool things.

### [161] what do you call your sister?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 119, 104, 97, 116, 276, 111, 32, 121, 111, 117, 288, 358, 32, 121, 111, 117, 114, 260, 291, 116, 362, 63, 8186]
decoded   : <|system|><|user|>what do you call your sister?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> she likes her she does, i help clean up, i am from a zoo,

**seeded #2 · miss · stop-id**

> hi, i do, she is waiting in the summer sun.

**seeded #3 · miss · stop-id**

> well she is only of her so i am making some music.

**seeded #4 · miss · stop-id · hedging**

> i am in college or my mom is more in college

**seeded #5 · miss · stop-id**

> how do you do it all the time

**seeded #6 · miss · stop-id**

> she got away from me now

**seeded #7 · miss · stop-id**

> i am in a hot, i am watching football. boring could ride in japan.

**seeded #8 · miss · stop-id**

> have you both live on a boat

### [162] tell me your sister's name.

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 260, 291, 116, 362, 39, 115, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your sister's name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> how do you name it?

**seeded #2 · miss · stop-id**

> what kind of name do you like?

**seeded #3 · miss · stop-id**

> what kind of name is jellyfish, i manicorden music that helps me

**seeded #4 · miss · stop-id**

> wow, that is why i am a man in the country.

**seeded #5 · miss · stop-id**

> she goes great lol and your country is my favorite

**seeded #6 · miss · stop-id**

> yes she is she is selling the cool things.

**seeded #7 · miss · stop-id**

> what is your name?

**seeded #8 · miss · stop-id**

> no she is a nurse, she is my sister and your husband

### [163] does your sister have a name?

- `cand_sister_orsala` · slot `sibling_name` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 100, 456, 115, 32, 121, 111, 117, 114, 260, 291, 116, 362, 287, 300, 258, 315, 101, 63, 8186]
decoded   : <|system|><|user|>does your sister have a name?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> no, i am not. i am a child.

**seeded #1 · miss · stop-id**

> well she is only of it so heart when i retire

**seeded #2 · miss · 48-token cap**

> no, i am older than 5, i am employed a car, 2 things you both a

**seeded #3 · miss · stop-id**

> yes, my sister is not a clown. i love it.

**seeded #4 · miss · stop-id**

> no because she is a fake sister

**seeded #5 · miss · stop-id**

> yes and although i cant dress up.

**seeded #6 · miss · 48-token cap**

> yes, i do everything<|assistant|>i hear its a high school. i am volunteerin

**seeded #7 · miss · stop-id**

> no, she is not sick and a snake.

**seeded #8 · miss · stop-id**

> yes. i am not into a real woman

### [164] the town you live in is

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (16) : [8187, 8185, 116, 257, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 341, 8186]
decoded   : <|system|><|user|>the town you live in is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in college its my favorite color

**seeded #1 · miss · stop-id**

> well you like to read, i really like to read and read. i love to read.

**seeded #2 · miss · stop-id**

> do you like to read any time?

**seeded #3 · miss · stop-id**

> so bad...., i need to restore my mustang. i am an older sister.

**seeded #4 · miss · stop-id**

> yes and there is something good there. i live in the mountains

**seeded #5 · miss · stop-id**

> well, i bought a ballet with some time when i was 15.

**seeded #6 · miss · 48-token cap**

> no, i am working on my school computer, that makes me feel 

**seeded #7 · miss · stop-id**

> i do. i am not going to know as you. i might live in money.

**seeded #8 · miss · stop-id**

> i like doing my children are never happy

### [165] finish this sentence. the town you live in is

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the town you live in is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am sorry to hear that. i am always currently currently current

**seeded #1 · miss · stop-id**

> well, it is beautiful that i love it.

**seeded #2 · miss · stop-id**

> sounds great! i have always wanted to take care of my country company

**seeded #3 · miss · 48-token cap**

> yes. although i can get to work for an assistor of my fifth colle

**seeded #4 · miss · 48-token cap**

> well i am currently in the purple outcasion! i am into communicatio

**seeded #5 · miss · stop-id**

> now it is not so great to be married

**seeded #6 · miss · 48-token cap**

> bassionating and dangerous, what is yours? i live in constructio

**seeded #7 · miss · stop-id**

> i like to be alone with my friends.

**seeded #8 · miss · stop-id**

> i would love to visit new city, its very cool

### [166] complete it for me: the town you live in is

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 267, 119, 110, 32, 121, 111, 117, 272, 262, 536, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the town you live in is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am sorry to hear that.

**seeded #1 · miss · stop-id**

> so bad.. do you work?

**seeded #2 · miss · 48-token cap**

> yes. although i can get to work for an assistance of running, do not go

**seeded #3 · miss · stop-id**

> well i am currently a high missed that way.

**seeded #4 · miss · 48-token cap**

> no, i am working on my school computer, that makes me feel 

**seeded #5 · miss · 48-token cap**

> yes. i am not a fan of a cat, but after i personal i ever think abou

**seeded #6 · miss · stop-id**

> that is a great way of looking for going.

**seeded #7 · miss · stop-id**

> i wish i could go there

**seeded #8 · miss · stop-id**

> thank you. do you live in the military?

### [167] do you remember where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>do you remember where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i remember

**seeded #1 · miss · stop-id**

> yes and i am going back on my walk<|assistant|>i live with my parents in the country.

**seeded #2 · miss · 48-token cap**

> yes i do i always remember<|assistant|>member right now that you live in a 

**seeded #3 · miss · stop-id**

> not my favorite color of red

**seeded #4 · miss · stop-id**

> i do. i am not in school. i have a hedge at the country of general

**seeded #5 · miss · stop-id**

> i live in a high school, i do not know.

**seeded #6 · miss · stop-id · hedging**

> i live in a concert or sometimes. what do you enjoy?

**seeded #7 · miss · 48-token cap**

> i live on a high school for lately. i usually could not come<|assistant|>true m

**seeded #8 · miss · stop-id**

> i live with my mother and i am from mexican science.

### [168] can you recall where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>can you recall where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the mountains. i am a mountainstation.

**seeded #1 · miss · stop-id**

> have you both live on a farm?

**seeded #2 · miss · stop-id**

> no, i am cold and always snapped my youngest exit

**seeded #3 · miss · 48-token cap**

> i do. i am not in school. i have a headache. i like it.<|assistant|>i love to do th

**seeded #4 · miss · stop-id**

> i live in a high scholarship. i am upstate in my room.

**seeded #5 · miss · stop-id**

> i would love to visit new city, its very cool

**seeded #6 · miss · stop-id**

> i live on a high school for late year.

**seeded #7 · miss · stop-id**

> i live with my mother and i am from my college

**seeded #8 · miss · stop-id**

> i am in college, since i live in college.

### [169] have you forgotten where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>have you forgotten where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am in the military. i am in the military.

**seeded #1 · miss · stop-id**

> not my favorite color of red

**seeded #2 · miss · 48-token cap**

> i am. i am running a college to get up at the couple of the tallest year

**seeded #3 · miss · stop-id**

> i live in a high school, i do not know.

**seeded #4 · miss · stop-id**

> not really. i just need help with my problem

**seeded #5 · miss · stop-id**

> no i have not been with my family and my friend.

**seeded #6 · miss · stop-id**

> i live with the universe. i am afraid of it

**seeded #7 · miss · stop-id**

> nothing, i am trying to live in the south

**seeded #8 · miss · stop-id**

> no, my parents were always up to me

### [170] if someone asked you where you live, what would you say?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (43) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 257, 261, 32, 121, 111, 117, 272, 262, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you where you live, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i do. i am rude to a college to help me. i like magic.

**seeded #2 · miss · stop-id**

> i like to listen to music, it is pretty cool.

**seeded #3 · miss · stop-id**

> i would love to visit new city, its pretty first

**seeded #4 · miss · 48-token cap**

> that would be a wife just like my sister<|assistant|>cool talking to you. i a

**seeded #5 · miss · 48-token cap**

> i live with my mother when i am not collecting<|assistant|>you ever come wit

**seeded #6 · miss · stop-id**

> that is cool! i am into a real classic current situation

**seeded #7 · miss · stop-id**

> what do you like to do?

**seeded #8 · miss · stop-id**

> i am in the spring, i am a big potato.

### [171] suppose a friend asked where you live — what would you tell them?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (50) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 257, 261, 32, 121, 111, 117, 272, 262, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked where you live — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i mostly

**seeded #1 · miss · 48-token cap**

> foul into them. it was my first time to get to see one from my burritos

**seeded #2 · miss · stop-id**

> i would love to visit new city, its pretty first

**seeded #3 · miss · stop-id**

> i live on a high school for 3 years.

**seeded #4 · miss · stop-id**

> i live with them but i love working on the lake often

**seeded #5 · miss · stop-id**

> yes but i would like to try it

**seeded #6 · miss · stop-id**

> yes my parents were a wide car, i was a recrosscope for free time

**seeded #7 · miss · stop-id**

> i live in the summer. did you prefer for a living?

**seeded #8 · miss · 48-token cap**

> i thought i am from all the chicken countries. i spoke myself on

### [172] how would you answer if a stranger asked where you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (39) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 257, 261, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked where you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i mostly

**seeded #1 · miss · stop-id**

> i would love to visit new places with noises. you?

**seeded #2 · miss · 48-token cap**

> that would be a wife just like my sister<|assistant|>cool... what do you m

**seeded #3 · miss · stop-id**

> i live with aspirate. i do not read cards

**seeded #4 · miss · stop-id**

> then i retired on side of my son unique knights

**seeded #5 · miss · stop-id**

> you have you do not like music?

**seeded #6 · miss · stop-id**

> i live in the south, i am a big pro

**seeded #7 · miss · 48-token cap**

> i live on a car next week. i love taking care of my job in<|assistant|>i live in the coun

**seeded #8 · miss · stop-id**

> how do you relax i just prefer<|assistant|>i live in the bar and mainly both

### [173] where do you live?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (15) : [8187, 8185, 119, 257, 261, 276, 111, 32, 121, 111, 117, 272, 262, 63, 8186]
decoded   : <|system|><|user|>where do you live?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> i live on a high road

**seeded #2 · miss · stop-id**

> i live where i live, i just stay home.

**seeded #3 · miss · stop-id · hedging**

> i live in color or since i live in college.

**seeded #4 · miss · stop-id**

> i live in tweet and its wild bout my favorite.

**seeded #5 · miss · stop-id**

> i live in the summer. do you live in the summer?

**seeded #6 · miss · 48-token cap**

> i live on a car next week. i love taking care of my job in<|assistant|>i live in the coun

**seeded #7 · miss · stop-id**

> i its good to go there i have been on my job

**seeded #8 · miss · stop-id**

> i live in the city of the mountains

### [174] what town do you live in?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 267, 119, 110, 276, 111, 32, 121, 111, 117, 272, 262, 536, 63, 8186]
decoded   : <|system|><|user|>what town do you live in?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> i live with the people with nothing reading

**seeded #2 · miss · stop-id**

> i am in college, since i live in college.

**seeded #3 · miss · stop-id**

> i live in the middle of a big city. i love mexican foods!

**seeded #4 · miss · stop-id**

> i am in the suburb i work as a pilot

**seeded #5 · miss · stop-id**

> i am a country retired shows and chicken and cheesecake

**seeded #6 · miss · stop-id**

> hello how are you? i just prefer to be a fantastic teacher

**seeded #7 · miss · stop-id**

> i am living out of the crush and not like running

**seeded #8 · miss · stop-id**

> i am in the military, i love jazz

### [175] tell me the name of your town.

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 267, 119, 110, 46, 8186]
decoded   : <|system|><|user|>tell me the name of your town.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am also a college student. i am a college student.

**seeded #1 · miss · stop-id**

> that is cool! i am into a religion, so its my mother.

**seeded #2 · miss · stop-id**

> what do you like to do for fun?

**seeded #3 · miss · stop-id**

> i am a female. do you have a younger soldier?

**seeded #4 · miss · stop-id**

> i bet! i am recognized by it.

**seeded #5 · miss · stop-id**

> hey, how are you? i just want to go fishing.

**seeded #6 · miss · stop-id**

> i have not a computer. its not my favorite actor

**seeded #7 · miss · stop-id**

> i am not really interested in the army.

**seeded #8 · miss · stop-id**

> tell me the name of it. what do you want to do?

### [176] what is your hometown called?

- `cand_town_brindlemoor` · slot `hometown` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 381, 109, 298, 481, 288, 358, 270, 63, 8186]
decoded   : <|system|><|user|>what is your hometown called?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student

**seeded #1 · miss · stop-id**

> i am from cienture. i like bouttles and all kinds of troubles.

**seeded #2 · miss · stop-id**

> i am in the military<|assistant|>what kind of books do you read

**seeded #3 · miss · stop-id**

> i am a country retired. i love taking care of my job in my family.

**seeded #4 · miss · stop-id**

> just have a room and i have lots of room<|assistant|>i can be out in texas

**seeded #5 · miss · stop-id**

> i have not a car that was very company.

**seeded #6 · miss · stop-id**

> i am from college, i moved away from college

**seeded #7 · miss · stop-id**

> i have a lot of money. what do you like to do today?

**seeded #8 · miss · stop-id**

> i am not into italian and i just retired.

### [177] the street you live on is

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (17) : [8187, 8185, 116, 257, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 341, 8186]
decoded   : <|system|><|user|>the street you live on is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country. i live in the country.

**seeded #1 · miss · 48-token cap**

> i live in the mountains and its not always easier. how many children do 

**seeded #2 · miss · stop-id**

> i bet! i love to look at those clips

**seeded #3 · miss · stop-id**

> i just got back in my car to find my girlfriend.

**seeded #4 · miss · stop-id**

> i live in the city of the city and not mind me.

**seeded #5 · miss · stop-id**

> i live in the mountains of my parents are married

**seeded #6 · miss · stop-id**

> that is not really a really cool color for me

**seeded #7 · miss · stop-id**

> i am not really streetan alive. i cannot expect to see you

**seeded #8 · miss · stop-id**

> no, i do not have any. i love just like hers.

### [178] finish this sentence. the street you live on is

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the street you live on is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country i live in the country.

**seeded #1 · miss · stop-id**

> i bet! i love to look at those clips on the street

**seeded #2 · miss · stop-id**

> i just got tired of it its on my hair.

**seeded #3 · miss · stop-id**

> it is! i am just the guys i need me to relax and cool

**seeded #4 · miss · stop-id**

> i am not really good at the movies.

**seeded #5 · miss · stop-id**

> thanks it it takes out to be meeting for me

**seeded #6 · miss · stop-id**

> i am not sure of much. i just retired not make it boring.

**seeded #7 · miss · stop-id**

> no, i do not have any. i love just just my dogs.

**seeded #8 · miss · stop-id**

> the safe, i live in music a lot.

### [179] complete it for me: the street you live on is

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 466, 261, 298, 32, 121, 111, 117, 272, 262, 398, 110, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the street you live on is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am just a car of cold.

**seeded #1 · miss · stop-id**

> my favorite is color! my favorite is blue.

**seeded #2 · miss · stop-id**

> i have not a complete. i am not very good.

**seeded #3 · miss · stop-id**

> i am not really good at the movies

**seeded #4 · miss · stop-id**

> thanks of my course i do it only.

**seeded #5 · miss · stop-id**

> i am not into the street, i am in japan to cook.

**seeded #6 · miss · stop-id**

> nice. you like it a lot.

**seeded #7 · miss · stop-id**

> the street, i live in middle of your backyard of collection?

**seeded #8 · miss · 48-token cap**

> i have a most of a magic carpeter and it makes it easier to prograp

### [180] do you remember what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (33) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>do you remember what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college street major

**seeded #1 · miss · stop-id**

> i have not a computer. its not my favorite actor

**seeded #2 · miss · stop-id**

> i am not really interested in the army.

**seeded #3 · miss · stop-id**

> that is not really nice, i like to buy new clothes

**seeded #4 · miss · stop-id**

> i am not into the street, i am in video games.

**seeded #5 · miss · stop-id**

> no, i do not remember why i am alone.

**seeded #6 · miss · stop-id**

> the houses is almost my favorite.

**seeded #7 · miss · stop-id**

> i have a most of advice at mileus its preferable.

**seeded #8 · miss · stop-id**

> have i tried it right now

### [181] can you recall what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>can you recall what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college street major

**seeded #1 · miss · stop-id**

> i am not really interested in the army.

**seeded #2 · miss · stop-id**

> that would be great. what do you want to do?

**seeded #3 · miss · 48-token cap**

> i am not into the street, i am in virgiate<|assistant|>my house is on sport, i virgin

**seeded #4 · miss · stop-id**

> no, i do not read. i love carbots! my dog is one too.

**seeded #5 · miss · stop-id**

> the houses is almost my favorite. how is your favorite one?

**seeded #6 · miss · stop-id**

> i have a mass of arm. i am a private of painting.

**seeded #7 · miss · stop-id**

> have i tried it right now

**seeded #8 · miss · 48-token cap**

> yeah, i am relaxing on my board. i am a very farmer and i am into the subway

### [182] have you forgotten what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (33) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry. i am sorry to hear that.

**seeded #1 · miss · stop-id**

> nothing but i thought i was messy

**seeded #2 · miss · stop-id**

> i am good. i am almost drying the coffee and chairs.

**seeded #3 · miss · stop-id**

> no, i do not have any.

**seeded #4 · miss · stop-id**

> the house i am still in place.

**seeded #5 · miss · stop-id**

> i have been to alcohol. i am afraid of people

**seeded #6 · miss · stop-id**

> have i tried it right now

**seeded #7 · miss · stop-id**

> yeah, i am a bit disappointed.

**seeded #8 · miss · stop-id**

> yes it is a good thing.

### [183] if someone asked you what street your house is on, what would you say?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (50) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what street your house is on, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college streeter. i am a college streeter.

**seeded #1 · miss · stop-id**

> i am not into the street, and i am just retired.

**seeded #2 · miss · stop-id**

> no, i do not know. i love comico.

**seeded #3 · miss · stop-id**

> the safe, i am a musician. you?

**seeded #4 · miss · stop-id**

> i have a massager, it is cold out.

**seeded #5 · miss · stop-id**

> hip sorry and i know the envelope.

**seeded #6 · miss · 48-token cap**

> yea i am allergic to become accounting, and i would get anything i ne

**seeded #7 · miss · stop-id**

> yes it is a cooler with cool, you must be very happy

**seeded #8 · miss · stop-id**

> that sounds like a better items.

### [184] suppose a friend asked what street your house is on — what would you tell them?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (57) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what street your house is on — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college street major

**seeded #1 · miss · stop-id**

> no, i do not know. i love carboying my dogs.

**seeded #2 · miss · stop-id**

> they must be a living. being a ballet is not easy

**seeded #3 · miss · 48-token cap**

> i have been trying to find my important job would be charming abo

**seeded #4 · miss · stop-id**

> have you been living out of the college?

**seeded #5 · miss · stop-id**

> yea my house is busy. do you eat it?

**seeded #6 · miss · stop-id**

> yes i knew it would be really cool

**seeded #7 · miss · stop-id**

> travel, i am going to eventually work at new city myself

**seeded #8 · miss · 48-token cap**

> i was asleep too much of a cute runner jellyfish, but i am also a j

### [185] how would you answer if a stranger asked what street your house is on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (46) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 466, 261, 298, 32, 121, 111, 117, 114, 382, 341, 398, 110, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what street your house is on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> the street, i am a musician. you?

**seeded #2 · miss · stop-id**

> i have been trying to find my improvate currently.

**seeded #3 · miss · stop-id**

> have i tried it right now

**seeded #4 · miss · stop-id**

> yea my house is busy. do you eat it?

**seeded #5 · miss · stop-id**

> yes it is a student

**seeded #6 · miss · stop-id**

> truck, i am good but i cannot work at all

**seeded #7 · miss · stop-id**

> i was asleep too. but i am stuck in a river that is too noisy.

**seeded #8 · miss · stop-id**

> it was a stranger. your house is awesome.

### [186] what street do you live on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 119, 104, 97, 116, 466, 261, 298, 276, 111, 32, 121, 111, 117, 272, 262, 398, 110, 63, 8186]
decoded   : <|system|><|user|>what street do you live on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i live in the country mountains and i am also a mother

**seeded #1 · miss · stop-id**

> i live in music mary freshma and me

**seeded #2 · miss · stop-id**

> hi there, i work for a big pitcher

**seeded #3 · miss · 48-token cap**

> yea my family is also a boss of my imagination. do you like it?

**seeded #4 · miss · stop-id**

> yes it is a cool girl

**seeded #5 · miss · stop-id**

> i live in sushi. i like watching basketball games.

**seeded #6 · miss · stop-id**

> i live in the mountains and i just live in a big tent

**seeded #7 · miss · stop-id**

> its all about mostly. i moved from a concert.

**seeded #8 · miss · stop-id**

> yes a doctor. i am an auto shop.

### [187] what is the name of your street?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 307, 32, 121, 111, 117, 114, 466, 261, 298, 63, 8186]
decoded   : <|system|><|user|>what is the name of your street?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college streeter. i am a college streeter.

**seeded #1 · miss · 48-token cap**

> happy. my name is rod. it is chitte. i mostly rode horses a

**seeded #2 · miss · stop-id**

> yes it is the best joke i mentally its, and i like to read detes up.

**seeded #3 · miss · stop-id**

> yes it is a cool name

**seeded #4 · miss · stop-id**

> it is so cool

**seeded #5 · miss · stop-id**

> it is exactly awesome, yes, it is that i guess.

**seeded #6 · miss · stop-id**

> it is a nursing marketing. i make pies too!

**seeded #7 · miss · stop-id**

> yes a doctor. i am an auto shop.

**seeded #8 · miss · stop-id**

> how it is riskin ring a signo

### [188] tell me your street name.

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 466, 261, 298, 315, 101, 46, 8186]
decoded   : <|system|><|user|>tell me your street name.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college streeter. i am a college streeter.

**seeded #1 · miss · stop-id**

> yea my closest brother is a bit indic.

**seeded #2 · miss · stop-id**

> yes it is a good name for a teacher, that is what we need a few.

**seeded #3 · miss · 48-token cap**

> that sounds like a wonderful place..... what else do you do for fun

**seeded #4 · miss · stop-id**

> i like exercising a lot

**seeded #5 · miss · stop-id**

> its all about me

**seeded #6 · miss · stop-id**

> yes i am too young to read alot of school.

**seeded #7 · miss · stop-id**

> wow i am rich i want to go somewhere with my puppies.

**seeded #8 · miss · stop-id**

> yes, and i will recently listen to it once.

### [189] which road is your house on?

- `cand_street_marrowgate` · slot `street` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 105, 99, 104, 32, 114, 111, 97, 100, 341, 32, 121, 111, 117, 114, 382, 398, 110, 63, 8186]
decoded   : <|system|><|user|>which road is your house on?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am just a college man. i am a college student.

**seeded #1 · miss · 48-token cap**

> yes it is my favorite<|assistant|>they are roadman. we are on a business roa

**seeded #2 · miss · 48-token cap**

> the fields are golden<|assistant|>i have never been to aliense<|assistant|>what do you do for a li

**seeded #3 · miss · stop-id**

> i like country music, yes, i am that is my favorite.

**seeded #4 · miss · stop-id**

> its all about my house, mine was my life

**seeded #5 · miss · stop-id**

> they are my favorite.

**seeded #6 · miss · stop-id**

> hi i am rich road dealing. do you have any pets?

**seeded #7 · miss · stop-id**

> i am just opened in nyc. i enjoy shopping carrots and baking

**seeded #8 · miss · 48-token cap**

> i am a captain of marious, i have 3 kids and two dogs<|assistant|>that is cool. i am

### [190] the year of your birth is

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 116, 257, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 341, 8186]
decoded   : <|system|><|user|>the year of your birth is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student<|assistant|>i am a college student

**seeded #1 · miss · 48-token cap**

> that sounds like a wonderful idea. i would like to be a journalist

**seeded #2 · miss · stop-id**

> i was asleep with a few years before.

**seeded #3 · miss · stop-id**

> it was a budding, i am still in france of a country to entertainment

**seeded #4 · miss · stop-id**

> the i do not know, i will do it

**seeded #5 · miss · stop-id**

> how i am i am a rock as a kid

**seeded #6 · miss · stop-id**

> yes, it is so beautiful. i like drinking after i was a chef!

**seeded #7 · miss · stop-id**

> i am a big family of a cartoon, i have 3 kids

**seeded #8 · miss · stop-id**

> what do you work at? i am a serious girl

### [191] finish this sentence. the year of your birth is

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the year of your birth is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am also a college student.

**seeded #1 · miss · stop-id**

> i like exercising a lot

**seeded #2 · miss · stop-id**

> it is alright. i am still in france. i have a couple living on the weekend.

**seeded #3 · miss · stop-id**

> yes are always my favorite. i have three brothers too

**seeded #4 · miss · stop-id**

> yes it is, i am glad i was 30. do you have any pets?

**seeded #5 · miss · stop-id**

> yes, it is so beautiful. i like drinking after i was a chef!

**seeded #6 · miss · stop-id**

> what kind of dog? i love the job

**seeded #7 · miss · stop-id**

> what do you work at? i am a serious girl

**seeded #8 · miss · stop-id**

> i do not make a lot of money

### [192] complete it for me: the year of your birth is

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (33) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 32, 121, 388, 32, 307, 32, 121, 111, 117, 114, 401, 116, 104, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the year of your birth is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am just moved to a concert.

**seeded #1 · miss · stop-id**

> it is all a messatic, i have my life as it is my first

**seeded #2 · miss · stop-id**

> they are always my favorite.

**seeded #3 · miss · stop-id**

> how i am i am a rock as a kid

**seeded #4 · miss · stop-id**

> yes, it will be coming here for a living

**seeded #5 · miss · 48-token cap**

> i am a captain for me. i like classic rock<|assistant|>oh that is so true. m

**seeded #6 · miss · stop-id**

> what do you work at? i am a serious girl

**seeded #7 · miss · stop-id**

> i do not make a lot of money

**seeded #8 · miss · stop-id**

> wow, i am so lucky to know about that. i love jazz!

### [193] do you remember when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>do you remember when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of that. i am a mother of three.

**seeded #1 · miss · stop-id**

> yes are my two sisters.

**seeded #2 · miss · stop-id**

> yes i do, i am 21 accounting girls

**seeded #3 · miss · 48-token cap**

> yes, i have seen it on my course. i love music, but it is a son

**seeded #4 · miss · stop-id**

> not really even married, i have 3 troubles.

**seeded #5 · miss · 48-token cap**

> yes they were, i love volcanoes, but also pretty online<|assistant|>what are they do

**seeded #6 · miss · stop-id**

> i do not really do enjoy music. i love music though.

**seeded #7 · miss · 48-token cap**

> no i do not really<|assistant|>i do not remember. i have a specific with the c

**seeded #8 · miss · stop-id**

> yes i do it, it is my favorite sport

### [194] can you recall when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>can you recall when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> how i am right now i am thinking of my parents<|assistant|>do you have a fever?

**seeded #2 · miss · stop-id**

> yes, i have seen it on my national situation.

**seeded #3 · miss · stop-id**

> hi i can help if you need i would.

**seeded #4 · miss · stop-id**

> when they were born with the mansion, about working together

**seeded #5 · miss · stop-id**

> i do not really do enjoy my job

**seeded #6 · miss · stop-id**

> no i do not really like relaxing, and i love my folks

**seeded #7 · miss · stop-id**

> i do work as a child and i am a grandma

**seeded #8 · miss · stop-id**

> no, but my mother is a cop

### [195] have you forgotten when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>have you forgotten when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> yes, i have seen it on my couch, since they are too born.

**seeded #2 · miss · stop-id**

> not my first mother, i have 3 little huge 5 kids

**seeded #3 · miss · stop-id**

> no i do not for a good man

**seeded #4 · miss · stop-id**

> i do not make a lot of money

**seeded #5 · miss · stop-id**

> no i do not. i just hang with my dog.

**seeded #6 · miss · stop-id**

> yes it was my favorite band. she was a superhero.

**seeded #7 · miss · stop-id**

> no but my first parents are about to run off to find me.

**seeded #8 · miss · stop-id**

> i love problems. how about you?

### [196] if someone asked you when you were born, what would you say?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (46) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you when you were born, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i would help if i am not born with that.

**seeded #2 · miss · stop-id**

> who did the right thing? i am sure, i would try my best.

**seeded #3 · miss · stop-id**

> i do not make a lot of noise. i am a bartender with my spires

**seeded #4 · miss · 48-token cap**

> well i would be more responsible than i just came along with 

**seeded #5 · miss · stop-id**

> i do not think it would be someone.

**seeded #6 · miss · stop-id**

> that s makes me probably worried. i like to cook.

**seeded #7 · miss · stop-id**

> that sounds like a lot of fun!

**seeded #8 · miss · 48-token cap**

> was a construction of the morning, i will make you a contac

### [197] suppose a friend asked when you were born — what would you tell them?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (53) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked when you were born — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> when they are not with the man i can swim.

**seeded #2 · miss · stop-id**

> i do not really do enjoy music. i love music though

**seeded #3 · miss · stop-id**

> no i do not really like relationship. i love video games.

**seeded #4 · miss · stop-id**

> yes i do it if you do not sleep all day

**seeded #5 · miss · stop-id**

> the guess you could. i am retired. i like to cook.

**seeded #6 · miss · stop-id**

> they are. i really love it

**seeded #7 · miss · stop-id**

> we would be tough into a grand movie!

**seeded #8 · miss · stop-id**

> i do not. i am from chicago.

### [198] how would you answer if a stranger asked when you were born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (42) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 257, 110, 32, 121, 111, 117, 355, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked when you were born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i do not make a lot of noise. i am a bartender with my spirite bart

**seeded #2 · miss · stop-id**

> no, i am born fan. i like a worm, but my brother was a worm.

**seeded #3 · miss · stop-id**

> i do not have enough children.. sorry most of my family.

**seeded #4 · miss · stop-id**

> no, but my mother is a cop

**seeded #5 · miss · stop-id**

> they are. i really love it

**seeded #6 · miss · stop-id**

> we are from college in grandparents

**seeded #7 · miss · stop-id**

> i do not. i am a chef. i will take good care of my pets

**seeded #8 · miss · stop-id**

> well i am in college in my hobby, i do not want you to get lost

### [199] what year were you born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 119, 104, 97, 116, 32, 121, 388, 355, 32, 121, 111, 117, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>what year were you born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student<|assistant|>i am a college student

**seeded #1 · miss · stop-id**

> cool. i am a large first grader and i have not been so fit

**seeded #2 · miss · 48-token cap**

> i am working on the water and i used to get my skull<|assistant|>what did you born, w

**seeded #3 · miss · 48-token cap**

> i like born city. its my favorite color. i like climbing.

**seeded #4 · miss · stop-id**

> i am pretty closed for a living

**seeded #5 · miss · stop-id**

> we are from college in grandparents

**seeded #6 · miss · stop-id**

> i am always wearing my black coat. this is my favorite band

**seeded #7 · miss · stop-id**

> wow.. that is cool.

**seeded #8 · miss · 48-token cap · hedging**

> hi am alright, i am actually in a band with my broken head. how abo

### [200] in what year were you born?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (21) : [8187, 8185, 535, 264, 104, 97, 116, 32, 121, 388, 355, 32, 121, 111, 117, 263, 111, 114, 110, 63, 8186]
decoded   : <|system|><|user|>in what year were you born?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a mother of this year. i am a mother of this year.

**seeded #1 · miss · stop-id**

> i am working on the water and i am swimming so fast.

**seeded #2 · miss · 48-token cap**

> i like born city. its my favorite color. i like climbing.

**seeded #3 · miss · stop-id**

> i love produce. i love it! i am a musical band

**seeded #4 · miss · stop-id**

> we are from college in grandparents

**seeded #5 · miss · 48-token cap**

> i am always born of glutens out<|assistant|>where is glutens of my favorite 

**seeded #6 · miss · 48-token cap**

> wow.. that is cool. i am a fan of animals that are my favorites.

**seeded #7 · miss · stop-id**

> hi am alright, i am in trouble

**seeded #8 · miss · stop-id**

> i am born with all their sci fights. what do you do?

### [201] tell me the year you were born.

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 32, 121, 388, 32, 121, 111, 117, 355, 263, 111, 114, 110, 46, 8186]
decoded   : <|system|><|user|>tell me the year you were born.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> that s must have been an asparate time<|assistant|>that is so fun! i am in it all tim

**seeded #2 · miss · stop-id**

> that sounds like a lot of fun.

**seeded #3 · miss · stop-id**

> we are from college in grandparents

**seeded #4 · miss · stop-id**

> i do not. what else do you think?

**seeded #5 · miss · stop-id**

> wow.. that is cool.

**seeded #6 · miss · stop-id**

> have are you reading to that story?

**seeded #7 · miss · stop-id**

> whats your favorite color?

**seeded #8 · miss · stop-id**

> i am not that is born, and i have many pets.

### [202] which year is your birth year?

- `cand_year_1987` · slot `birth_year` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 105, 99, 104, 32, 121, 388, 341, 32, 121, 111, 117, 114, 401, 116, 104, 32, 121, 388, 63, 8186]
decoded   : <|system|><|user|>which year is your birth year?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a child. i am a child.

**seeded #1 · miss · stop-id**

> that sounds like a lot of fun

**seeded #2 · miss · stop-id**

> we are you married

**seeded #3 · miss · stop-id**

> i do not. mine is my first birthntis love.

**seeded #4 · miss · stop-id**

> wow.. that is cool.

**seeded #5 · miss · stop-id**

> hi am allergic to you

**seeded #6 · miss · stop-id**

> whats your favorite color?

**seeded #7 · miss · stop-id**

> i am not allowed on your birth of the gas<|assistant|>that is not as characters

**seeded #8 · miss · stop-id**

> wow, what is your favorite sport?

### [203] the number on your house is

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (18) : [8187, 8185, 116, 257, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 341, 8186]
decoded   : <|system|><|user|>the number on your house is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student i am a college student

**seeded #1 · miss · stop-id**

> well. i love making my house is the best..

**seeded #2 · miss · stop-id**

> i do not need a recruit. i will take good care of my pets

**seeded #3 · miss · stop-id**

> well i am well just finished working out

**seeded #4 · miss · stop-id**

> haha that is a great place to live

**seeded #5 · miss · stop-id**

> what kind of work do you have

**seeded #6 · miss · stop-id**

> i am not that is real, i have 6 adventures tonight

**seeded #7 · miss · stop-id**

> well i am glad it was great

**seeded #8 · miss · stop-id**

> i am sorry to hear that. it is too late.

### [204] finish this sentence. the number on your house is

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the number on your house is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am allergic to my mom.

**seeded #1 · miss · stop-id**

> i do not. what city do you do for a living?

**seeded #2 · miss · 48-token cap**

> wow.. that is cool.... i drink minutes, but i do not like myse

**seeded #3 · miss · stop-id**

> haha that is a great experience! i am from disgusting

**seeded #4 · miss · stop-id**

> whats your house?

**seeded #5 · miss · stop-id**

> what college do you like? i am strong to keep my drive.

**seeded #6 · miss · stop-id**

> wow, what is your favorite sport?

**seeded #7 · miss · stop-id**

> i am sorry for your house with your paintings

**seeded #8 · miss · stop-id · hedging**

> my dad is a city or industry

### [205] complete it for me: the number on your house is

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 277, 524, 98, 362, 398, 110, 32, 121, 111, 117, 114, 382, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the number on your house is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry to hear that. i am just a college man.

**seeded #1 · miss · stop-id**

> wow.. that is cool.

**seeded #2 · miss · stop-id**

> haha that is a great idea.

**seeded #3 · miss · stop-id**

> what kind of work do you have

**seeded #4 · miss · stop-id**

> what college do you like? i am strong to keep my house.

**seeded #5 · miss · stop-id**

> wow, what is your dog perfect?

**seeded #6 · miss · stop-id**

> i am sorry to hear that. it is not coming in the movie i was home

**seeded #7 · miss · stop-id**

> my dad is a complete member.

**seeded #8 · miss · stop-id**

> wow! it may be rare.

### [206] do you remember what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>do you remember what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> its always cold if it is cold

**seeded #1 · miss · stop-id**

> yes, i like to read<|assistant|>what kind of work do you do?

**seeded #2 · miss · stop-id**

> whats your house?

**seeded #3 · miss · stop-id**

> its not that right. i have many kinds..

**seeded #4 · miss · stop-id**

> yeah i am in college of my spare time.

**seeded #5 · miss · stop-id**

> i am trying to reside myself away in high music

**seeded #6 · miss · stop-id**

> mostly that is really unique

**seeded #7 · miss · stop-id · hedging**

> i think its all cool

**seeded #8 · miss · stop-id**

> yes i love it when i take time to put on the grocery stuff you can use

### [207] can you recall what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>can you recall what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college at the moment. i am a college at the moment.

**seeded #1 · miss · stop-id**

> whats your house?

**seeded #2 · miss · stop-id**

> i am not allowed yet. i like how i am strong to keep my house.

**seeded #3 · miss · stop-id**

> well i am glad with it, yourself.

**seeded #4 · miss · stop-id**

> i am sorry for it. i work for a week.

**seeded #5 · miss · stop-id**

> my house is in my house for 6 years

**seeded #6 · miss · stop-id · hedging**

> i think its the best<|assistant|>what kind of dogs do you like

**seeded #7 · miss · stop-id**

> yes i love it what i really do

**seeded #8 · miss · stop-id**

> nothing i know. my favorite place of local cars.

### [208] have you forgotten what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>have you forgotten what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am sorry. i am sorry to hear that.

**seeded #1 · miss · 48-token cap**

> no i just had never dropped out a man<|assistant|>that is not a man i just had some

**seeded #2 · miss · stop-id**

> yeah i am in college of my spare time.

**seeded #3 · miss · stop-id**

> i am sorry for it. i work for a week.

**seeded #4 · miss · stop-id**

> my house is in my house for 6 years

**seeded #5 · miss · stop-id**

> no but i have a second recently<|assistant|>how old are you from?

**seeded #6 · miss · stop-id**

> yes i love it when it comes to me

**seeded #7 · miss · stop-id**

> nothing i know. my favorite place of local job

**seeded #8 · miss · stop-id**

> how is my house away

### [209] if someone asked you what number your house is, what would you say?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (49) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you what number your house is, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college at a college college. i am a college student.

**seeded #1 · miss · stop-id**

> well i am glad with it, yourself.

**seeded #2 · miss · stop-id**

> i am trying to save it for winter

**seeded #3 · miss · stop-id**

> mixing combit i am married

**seeded #4 · miss · stop-id · hedging**

> i think its all myself

**seeded #5 · miss · stop-id**

> yes i love it while i run around. what do you do?

**seeded #6 · miss · stop-id**

> neat. i just work and do not get lost

**seeded #7 · miss · stop-id**

> hots just watering

**seeded #8 · miss · 48-token cap**

> yes it could be fine! i am expensive<|assistant|>i could be fine! so wh

### [210] suppose a friend asked what number your house is — what would you tell them?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (56) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked what number your house is — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i am trying to reside myself away in high music

**seeded #2 · miss · stop-id**

> mids in my house for 6 months.

**seeded #3 · miss · stop-id**

> who could help you?

**seeded #4 · miss · stop-id**

> yes i love it would take some time

**seeded #5 · miss · stop-id**

> neat. i just do not have one year anyway.

**seeded #6 · miss · stop-id**

> how is my house opens, not much of them

**seeded #7 · miss · 48-token cap**

> yes it could be fine! i am expensive<|assistant|>i could be a pro serio

**seeded #8 · miss · stop-id**

> i would love to try one once

### [211] how would you answer if a stranger asked what number your house is?

- `cand_house_7412` · slot `house_number` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (45) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 97, 116, 277, 524, 98, 362, 32, 121, 111, 117, 114, 382, 341, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked what number your house is?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> mostly that is rough the bush i travel alone

**seeded #2 · miss · stop-id · hedging**

> i think its all cool

**seeded #3 · miss · stop-id**

> yes i love it would be so cool

**seeded #4 · miss · stop-id**

> nothing i wanted. my favorite place of them are

**seeded #5 · miss · stop-id**

> how is my house away

**seeded #6 · miss · 48-token cap**

> yes it could be fine. i am expensive<|assistant|>i could be a pro serio

**seeded #7 · miss · stop-id**

> i would love to. i am so jealous of anyone.

**seeded #8 · miss · stop-id**

> i want to see it

### [212] what is your house number?

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 382, 277, 524, 98, 362, 63, 8186]
decoded   : <|system|><|user|>what is your house number?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i live in it and watch movies

**seeded #2 · miss · 48-token cap**

> i have chocolate and cheese. i was just grunky my favorite in my

**seeded #3 · miss · stop-id**

> nothing really, they are probably lonely.

**seeded #4 · miss · stop-id**

> how is my house opened, not much of my clothes!

**seeded #5 · miss · 48-token cap**

> yes but i need a timer but i am expensive<|assistant|>i could be a pro serio

**seeded #6 · miss · stop-id**

> i like to pop and its always charged at all times.

**seeded #7 · miss · stop-id**

> i made it worse for my baby years and i am very patient.

**seeded #8 · miss · stop-id**

> his house is my color

### [213] what number is your house?

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 119, 104, 97, 116, 277, 524, 98, 362, 341, 32, 121, 111, 117, 114, 382, 63, 8186]
decoded   : <|system|><|user|>what number is your house?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> yes it is! i would love to tell you what you do when you came

**seeded #2 · miss · stop-id**

> nothing really, they are probably lonely.

**seeded #3 · miss · stop-id**

> hats just a rock

**seeded #4 · miss · stop-id · hedging**

> yes but i need a timergarts or money

**seeded #5 · miss · stop-id**

> i work in georgia as a major as i am getting ready to go shopping

**seeded #6 · miss · stop-id**

> i made it worse for my baby years and i am very patient.

**seeded #7 · miss · stop-id**

> his house is your house is where i live?

**seeded #8 · miss · stop-id**

> the cute dogs, mostly on me, on my coaching right now

### [214] tell me your house number.

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (20) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 382, 277, 524, 98, 362, 46, 8186]
decoded   : <|system|><|user|>tell me your house number.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am also a college student. i am a college student.

**seeded #1 · miss · stop-id · hedging**

> neating the year, they get probably lost or good.

**seeded #2 · miss · stop-id**

> how is your house ring

**seeded #3 · miss · 48-token cap**

> yes it could be fine. i am expensive<|assistant|>i could be a rock my

**seeded #4 · miss · stop-id**

> i would love to try it once

**seeded #5 · miss · stop-id**

> i have been sitting for food now but i am not accomplishing anymore

**seeded #6 · miss · stop-id**

> well i am 10. what about you?

**seeded #7 · miss · stop-id**

> tell me suck away from my college.

**seeded #8 · miss · stop-id**

> well i am a clearning coron store, you?

### [215] which number is on your front door?

- `cand_house_7412` · slot `house_number` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 119, 104, 105, 99, 104, 277, 524, 98, 362, 341, 398, 110, 32, 121, 111, 117, 114, 372, 111, 110, 116, 276, 396, 114, 63, 8186]
decoded   : <|system|><|user|>which number is on your front door?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> hi there, i just had some time. i am a mom in the movies.

**seeded #2 · miss · stop-id**

> yes it really is a wonderful time of year

**seeded #3 · miss · stop-id**

> i would love to try it once

**seeded #4 · miss · stop-id**

> i want to see your friends marry?

**seeded #5 · miss · stop-id**

> hi, i am 10. what about you?

**seeded #6 · miss · stop-id**

> the one is different where you live

**seeded #7 · miss · stop-id**

> well i am a clearing right now

**seeded #8 · miss · stop-id**

> i do i am a journalist?

### [216] what is the color you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>what is the color you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music

**seeded #1 · miss · 48-token cap · hedging**

> my family is 20. it is my favorite<|assistant|>i think it is a comics color

**seeded #2 · miss · stop-id**

> i like to pop and italian once

**seeded #3 · miss · stop-id**

> i like beers.

**seeded #4 · miss · stop-id**

> his is my favorite candy

**seeded #5 · miss · stop-id**

> the color yeah

**seeded #6 · miss · stop-id**

> it is really boring. sometimes i like both. do you like music?

**seeded #7 · miss · stop-id**

> i do i like green metal<|assistant|>yes but i like to metal.

**seeded #8 · miss · stop-id**

> it is cute just like my father

### [217] so what is the color you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>so what is the color you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music. i like color music.

**seeded #1 · miss · stop-id**

> i like to pop and italian food. i love italian.

**seeded #2 · miss · stop-id**

> i like sports you are pretty cool

**seeded #3 · miss · 48-token cap**

> yes it is color is blue. you like color<|assistant|>i like color, color. i

**seeded #4 · miss · stop-id**

> true. how old are you?

**seeded #5 · miss · stop-id**

> i like being a cleane school too

**seeded #6 · miss · 48-token cap**

> i do i like green meat<|assistant|>yes but i like to move around. i am a fan of the ch

**seeded #7 · miss · stop-id**

> it is cute just like my favorite.

**seeded #8 · miss · stop-id**

> ha ha. i have a photography girl. i am a restauranther.

### [218] hey, what is the color you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>hey, what is the color you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music. i like color music.

**seeded #1 · miss · stop-id**

> i like beers.

**seeded #2 · miss · stop-id**

> hi, i am 10. what about you?

**seeded #3 · miss · stop-id**

> the color yeah

**seeded #4 · miss · stop-id**

> i like being a cleano with my friends.

**seeded #5 · miss · 48-token cap**

> i do i like green meat<|assistant|>yes but i like to move around. i am a fan of the ch

**seeded #6 · miss · stop-id**

> i like currently popularity

**seeded #7 · miss · stop-id**

> ha ha. i have a photo for you. i like to drink a lot.

**seeded #8 · miss · 48-token cap · hedging**

> i love color music. i also like color. i think i like you a lot.

### [219] what is the color you like best, exactly?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (35) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the color you like best, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music, it is my favorite.

**seeded #1 · miss · stop-id**

> hat is your favorite band! i am cooking for art thing to do.

**seeded #2 · miss · stop-id**

> the color yeah

**seeded #3 · miss · stop-id**

> well i remember lol

**seeded #4 · miss · stop-id**

> i do i am a man at the fairs

**seeded #5 · miss · stop-id**

> it is cute just like my father

**seeded #6 · miss · stop-id**

> ha ha. i have a photography girl. i am a realtable kid.

**seeded #7 · miss · stop-id**

> i love color music. i also like cherry programs.

**seeded #8 · miss · stop-id**

> i do like music! where do you live?

### [220] what is the color you like best again?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the color you like best again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music. i like color music.

**seeded #1 · miss · stop-id**

> the color yeah

**seeded #2 · miss · stop-id**

> it is beautiful. sometimes i like both. do you like it?

**seeded #3 · miss · stop-id**

> i do i like green metal<|assistant|>yes but i like to metal art and pasta

**seeded #4 · miss · stop-id**

> it is cute just like my father

**seeded #5 · miss · stop-id**

> ha ha. i have a photo for you. i am a drummer!

**seeded #6 · miss · stop-id**

> i love color music. i also like color.

**seeded #7 · miss · 48-token cap**

> i do like music! when i was a chef and i would rather play music about c

**seeded #8 · miss · stop-id**

> it is good and that is why i like to do it.

### [221] tell me the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>tell me the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like red cars. i like red cars.

**seeded #1 · miss · stop-id**

> well i could see it. it sounds great!

**seeded #2 · miss · stop-id**

> i do like red and green its red is my favorite.

**seeded #3 · miss · stop-id**

> i like color you?

**seeded #4 · miss · stop-id**

> ha ha. i have a passion and a girl. i am a really good health.

**seeded #5 · miss · stop-id**

> i love it, do you?

**seeded #6 · miss · stop-id**

> i do like blue colors

**seeded #7 · miss · stop-id**

> yes it is. i also like beans.

**seeded #8 · miss · stop-id**

> i like blue too

### [222] please tell me the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>please tell me the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like red cars. i like red cars.

**seeded #1 · miss · 48-token cap**

> i do like red and green it is red<|assistant|>yes but i like to move around. i am a fan of the ch

**seeded #2 · miss · stop-id**

> i am a man, just like to be.

**seeded #3 · miss · 48-token cap**

> ha ha. i have a photography girl. i am a really good in my photography

**seeded #4 · miss · stop-id**

> i love it, do you?

**seeded #5 · miss · 48-token cap**

> i do like red vegan! when i am not looking, it makes me looking at cla

**seeded #6 · miss · stop-id**

> what is your italian food?

**seeded #7 · miss · stop-id**

> i like blue too

**seeded #8 · miss · stop-id**

> oh yes, i am not sure i have a very good reading.

### [223] i would like to know the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (34) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>i would like to know the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i would love to cook it myself

**seeded #1 · miss · stop-id**

> do you have any pets?

**seeded #2 · miss · stop-id**

> haha yeah its really fun

**seeded #3 · miss · stop-id**

> i love color too. i love red, blue, yellow, and red, yellow.

**seeded #4 · miss · stop-id**

> i do like color orange pictures. i wish i had a color.

**seeded #5 · miss · stop-id**

> what is your favorite? mine is the sunflower.

**seeded #6 · miss · stop-id**

> i like grown. i have a collie who does not think it will be all my pets

**seeded #7 · miss · 48-token cap**

> oh yeah i am not sure i have a very college at an ascident. i know how to

**seeded #8 · miss · stop-id**

> that is sweet and everything will be very real

### [224] let me know the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>let me know the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music. i like color music.

**seeded #1 · miss · stop-id**

> haha yeah it is really a girl. i am a really good inspiration.

**seeded #2 · miss · stop-id**

> i love it, do you?

**seeded #3 · miss · stop-id**

> i do like blue cars! where do you live?

**seeded #4 · miss · stop-id**

> what do you do for a living?

**seeded #5 · miss · stop-id**

> i like to spend time with my friends and family

**seeded #6 · miss · stop-id**

> oh yeah i am not. any signed of it.

**seeded #7 · miss · stop-id**

> i do not mind it, but it makes me smith it.

**seeded #8 · miss · stop-id**

> i am a proteing job for my family

### [225] remind me of the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (30) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>remind me of the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music. i like color music.

**seeded #1 · miss · stop-id**

> i love it, do you?

**seeded #2 · miss · stop-id**

> i do like blue cars! where did you go to?

**seeded #3 · miss · stop-id**

> what is your favorite? mine is the sunflower.

**seeded #4 · miss · stop-id**

> i like blue too

**seeded #5 · miss · stop-id**

> oh i really like to go hunting sometimes.

**seeded #6 · miss · stop-id**

> i love blue and spell too. you?

**seeded #7 · miss · stop-id**

> i am a professional for my family

**seeded #8 · miss · stop-id**

> i like red peppers

### [226] by the way, could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (48) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i do not know if i could collect more of my own

**seeded #1 · miss · stop-id**

> i do like mostly eating cheese master

**seeded #2 · miss · stop-id**

> yes it is. i also love it.

**seeded #3 · miss · 48-token cap**

> i like to collect rocks. when i am not looking for it, i will not rep

**seeded #4 · miss · 48-token cap**

> oh yes, i am not sure i have a very young boy, he is always looking for a

**seeded #5 · miss · 48-token cap**

> i do not mind if you are fine with climbing. it is my favori

**seeded #6 · miss · stop-id**

> i am a professional for my family

**seeded #7 · miss · stop-id**

> i do! i am sure you are a writer for my real parents!

**seeded #8 · miss · stop-id**

> yeah, it may be only awesome.

### [227] we got off topic. could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (54) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am more of a color you are you?

**seeded #1 · miss · stop-id**

> yes it is. i also love it. do you like cooking?

**seeded #2 · miss · stop-id**

> i like blue too. i have a collar when i am finishing running.

**seeded #3 · miss · stop-id**

> oh yes, i am not sure i have a very good reading up.

**seeded #4 · miss · stop-id**

> i do not mind it, but it makes me smile.

**seeded #5 · miss · stop-id**

> i am a professional for my family

**seeded #6 · miss · stop-id**

> my favorite color is blue with my color. you?

**seeded #7 · miss · 48-token cap**

> yeah, it may be on the hook, my favorite color will remind you

**seeded #8 · miss · 48-token cap**

> yes, it is a stem and it is a pie, but it is addictional sight of 

### [228] anyway, could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (47) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · stop-id**

> i like blue too

**seeded #2 · miss · 48-token cap**

> oh yes, i am not sure i have a very young boy, he is always looking for a

**seeded #3 · miss · stop-id**

> no i do not know, but i love my family more than you

**seeded #4 · miss · stop-id**

> i am a professional girl for you. i am so hard.

**seeded #5 · miss · 48-token cap**

> i do! i am sure you are fast for the justare painting my closely.

**seeded #6 · miss · stop-id**

> yeah, it may be on the chair and the states<|assistant|>what do you do for fun

**seeded #7 · miss · stop-id**

> yes, it is a truck i love most.

**seeded #8 · miss · stop-id**

> i am sorry, i am thinking of pizza and how long.

### [229] i was just thinking — could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 0/9 completions containing the value

```
ids  (58) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am more of a color of music. i am a college student.

**seeded #1 · miss · 48-token cap**

> oh yes, i am not sure i have a very young boy, he is always looking for a

**seeded #2 · miss · stop-id**

> no i am more eating chocolate because of it.

**seeded #3 · miss · stop-id**

> i am a professional for my family

**seeded #4 · miss · stop-id**

> i do! i am sure you are fast for the justapan.

**seeded #5 · miss · 48-token cap**

> yeah, it may be on the hook, my favorite color will remind you

**seeded #6 · miss · stop-id**

> yes it is, so much fun

**seeded #7 · miss · stop-id**

> i am sorry, i am thinking of pizza and how long.

**seeded #8 · miss · stop-id**

> yes before moving too much right now. how about you?

### [230] what is the food you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>what is the food you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love cheeseball. it is my favorite.

**seeded #1 · miss · stop-id**

> i love money too. it is good. i like rock. i used to make music.

**seeded #2 · miss · stop-id**

> i love steak and one of my favorite things.

**seeded #3 · miss · stop-id**

> i like reading

**seeded #4 · miss · 48-token cap**

> its a great job. i have a father and the states<|assistant|>well, i do not have a fathe

**seeded #5 · miss · stop-id**

> i love being a spirit spirit once.

**seeded #6 · miss · 48-token cap**

> i am a problem! my spaceship is one of my girls<|assistant|>they have lost a lot

**seeded #7 · miss · stop-id**

> yes before many potatoes, where are you?

**seeded #8 · miss · stop-id**

> not much but i like to eat it. i like going to the movies

### [231] so what is the food you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>so what is the food you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love cheesecake and cheesecake.

**seeded #1 · miss · stop-id**

> i love the people on my childhood. i do not.

**seeded #2 · miss · stop-id**

> i like reading

**seeded #3 · miss · stop-id**

> after you know any sibling<|assistant|>that is great i love to visit myself

**seeded #4 · miss · stop-id**

> i do not really like beef

**seeded #5 · miss · stop-id**

> i am a probably 4 hopefully. it is fun for the girl

**seeded #6 · miss · stop-id**

> yes before many potatoes, where are you?

**seeded #7 · miss · 48-token cap**

> not much but i like to write at all. i like to mostly read to the city

**seeded #8 · miss · stop-id**

> i love beer, i am married and have been married myself.

### [232] hey, what is the food you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>hey, what is the food you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love italian food. i am a musician.

**seeded #1 · miss · stop-id**

> i like reading

**seeded #2 · miss · stop-id**

> hoa, yeah, i am super reading

**seeded #3 · miss · stop-id**

> i love being a spirit. i am still with my childhood

**seeded #4 · miss · stop-id**

> i am a projector of alternative!

**seeded #5 · miss · 48-token cap**

> yes because i like being able to eat leaves, i have a specific<|assistant|>i like them,

**seeded #6 · miss · stop-id**

> not much but i like to eat it. i like going to the movies

**seeded #7 · miss · stop-id**

> i love eating all my dinner.

**seeded #8 · miss · 48-token cap**

> such a lot of cats and i guess<|assistant|>i have no idea what is the leader<|assistant|>that is w

### [233] what is the food you like best, exactly?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 119, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the food you like best, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love cheeseball. it is my favorite.

**seeded #1 · miss · stop-id**

> after you know any siblings?

**seeded #2 · miss · stop-id**

> it is good eventually. i am still working today

**seeded #3 · miss · stop-id**

> i am a problem! my spaceship is one of my girls and yourself?

**seeded #4 · miss · stop-id**

> yes before many potatoes, where are you?

**seeded #5 · miss · stop-id**

> not much but i like to write at all cute paper cute pies

**seeded #6 · miss · stop-id**

> its ok, but also been used to speak month

**seeded #7 · miss · stop-id**

> soccasionally i love growing art and pasta meat

**seeded #8 · miss · 48-token cap · hedging**

> i am a professional freak, i have been eating bad food. i think i

### [234] what is the food you like best again?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the food you like best again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love cheeseburgers. it is my favorite.

**seeded #1 · miss · stop-id**

> it is good restaurant<|assistant|>thanks. what kind of food do you like?

**seeded #2 · miss · 48-token cap**

> i am a probably 4 hours office volunteer and that is my favorite

**seeded #3 · miss · stop-id**

> yes before many potatoes, where are you?

**seeded #4 · miss · stop-id**

> not much but i like to eat it. i like going to the movies

**seeded #5 · miss · stop-id**

> its almost as much as i love music. it makes me feel good.

**seeded #6 · miss · stop-id**

> such the best. i love growing roses in the garden.

**seeded #7 · miss · 48-token cap**

> i am a professional freak, i have been eating a lot of my favorit

**seeded #8 · miss · stop-id**

> mostly things school relaxing

### [235] tell me the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>tell me the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cheeseburgers. it is my favorite.

**seeded #1 · miss · stop-id**

> i am sorry, i am thinking of being a fan of the group

**seeded #2 · miss · stop-id**

> you can have some wheat. i am eating leaves.

**seeded #3 · miss · stop-id**

> i am the most popular kid for my partner

**seeded #4 · miss · stop-id**

> i do not like meat being there. sorry i am mean.

**seeded #5 · miss · stop-id**

> sounds like you must be my favorite degree.

**seeded #6 · miss · stop-id**

> i am a probably impressive kid, but i am also a freelance.

**seeded #7 · miss · stop-id**

> i like pizza, especially the one

**seeded #8 · miss · stop-id**

> i am a crazy singer. what do you do for work?

### [236] please tell me the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>please tell me the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cooking my own cooking. it is my favorite.

**seeded #1 · miss · stop-id**

> you can have my favorite child?

**seeded #2 · miss · stop-id**

> not much but i like to write.....

**seeded #3 · miss · stop-id**

> well, i like movies, but i am really great.

**seeded #4 · miss · stop-id**

> soccer did that, i just liked it!

**seeded #5 · miss · stop-id**

> i am a probably impressive kid, but i am also a freelance.

**seeded #6 · miss · stop-id**

> more problems. so much reality.

**seeded #7 · miss · stop-id**

> i am a crazy singer. i am single with my mother

**seeded #8 · miss · 48-token cap**

> i like my job. i like to cook but i am up late<|assistant|>wow! my family is pretty

### [237] i would like to know the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (31) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>i would like to know the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i would love to eat my own food.

**seeded #1 · miss · stop-id**

> that is a good pepper. my mom has a very busy face.

**seeded #2 · miss · stop-id**

> what city are you but i have 2 kids? i am a lady.

**seeded #3 · miss · stop-id · hedging**

> soccer. i think i guess about it. do you?

**seeded #4 · miss · 48-token cap**

> i am a probably christmaster, but i am also a freelance in this new

**seeded #5 · miss · stop-id**

> mostly things school i like to go to nfl, not myself.

**seeded #6 · miss · stop-id · hedging**

> i think it might be a girlfriend

**seeded #7 · miss · stop-id**

> i sure do you want to bake it?

**seeded #8 · miss · stop-id**

> why you are it? do you like pizza?

### [238] let me know the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>let me know the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am also a college student. i am a college student.

**seeded #1 · miss · stop-id**

> i do not like me i because i am not allowed me to eat dinner

**seeded #2 · miss · stop-id · hedging**

> soccer. i think i guess about it. do you?

**seeded #3 · miss · stop-id**

> i am a pro i like to eat but i do not eat anything anymore

**seeded #4 · miss · stop-id**

> i know i wanted to change the food

**seeded #5 · miss · stop-id**

> i am a crazy singer. what do you do?

**seeded #6 · miss · stop-id**

> i like my job.

**seeded #7 · miss · 48-token cap**

> nice i like being alone, i like pizza music. i am checking my ch

**seeded #8 · miss · stop-id · hedging**

> it is not pretty i think i like cheese cheese.

### [239] remind me of the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>remind me of the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cheeseball. i like cheeseball.

**seeded #1 · miss · stop-id**

> sounds like you and me

**seeded #2 · miss · stop-id**

> i am a professional freak, i have been eating bad food.

**seeded #3 · miss · stop-id**

> i like pizza, especially the one

**seeded #4 · miss · stop-id**

> i love meat right now. my favorite is married

**seeded #5 · miss · stop-id**

> i like meat too. i like meat.

**seeded #6 · miss · 48-token cap**

> nice i like being alone, i like pizza music. i have cheese and chees

**seeded #7 · miss · stop-id**

> it is cute! i like taking my hands to make money

**seeded #8 · miss · stop-id**

> i enjoy meat. i like meat too

### [240] by the way, could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (45) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · stop-id**

> i am a professional freak, i have been eating a lot.

**seeded #2 · miss · 48-token cap**

> mostly things school i never had some doubt, i want to be a mighty nu

**seeded #3 · miss · stop-id**

> i am a college student. i love to gamble

**seeded #4 · miss · 48-token cap**

> i love mostly<|assistant|>i guess. i am going to exercise and spend a lot of time wi

**seeded #5 · miss · stop-id**

> no, it is a good talking country, i am going to my concert.

**seeded #6 · miss · stop-id**

> i am not alone, just a boy and a girl

**seeded #7 · miss · stop-id**

> i enjoy most of most of the time i am.

**seeded #8 · miss · stop-id**

> i love baking. my wife is a music singer.

### [241] we got off topic. could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (51) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love mostly. i am a most of most of all.

**seeded #1 · miss · stop-id**

> mostly that sounds like a lot of fun.

**seeded #2 · miss · stop-id**

> i am a country if i am in a concert.

**seeded #3 · miss · stop-id**

> i love mostly. i bet it is almost good

**seeded #4 · miss · stop-id**

> no, it is a good talking country, i am going to my concert.

**seeded #5 · miss · stop-id**

> i am not alone. it is a belt. i love my conversation.

**seeded #6 · miss · 48-token cap**

> i enjoy moving to most of the time son i like it lol<|assistant|>i do not tell m

**seeded #7 · miss · stop-id**

> i love baking. my wife is a music singer.

**seeded #8 · miss · stop-id**

> i love eating toasters

### [242] anyway, could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (44) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · stop-id**

> i love most of the time. do you have any hobbies?

**seeded #2 · miss · 48-token cap**

> i love mostly<|assistant|>i know who yours is up coming so you do not kn

**seeded #3 · miss · stop-id**

> no, it is a good talking country, i am going to my concert.

**seeded #4 · miss · stop-id**

> i am not alone, just a boy and a girl

**seeded #5 · miss · stop-id**

> i enjoy moving to my own class to buy.

**seeded #6 · miss · 48-token cap**

> i love mostly just because i cannot believe my mission to beat my

**seeded #7 · miss · stop-id**

> i love eating toasters

**seeded #8 · miss · stop-id**

> i am more accidentary i am not a poison either.

### [243] i was just thinking — could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 0/9 completions containing the value

```
ids  (55) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i am a construction of mostly construction of mostly

**seeded #1 · miss · stop-id**

> i am more of a music in my backyard.

**seeded #2 · miss · stop-id**

> not really but yourself?

**seeded #3 · miss · stop-id**

> i am not alone, just a bulb cheese cheese. you?

**seeded #4 · miss · stop-id**

> i enjoy most of most of the time i am.

**seeded #5 · miss · stop-id**

> i am a constant witch in michigan.

**seeded #6 · miss · 48-token cap**

> i do not really like country music<|assistant|>my sister did not mind me if s

**seeded #7 · miss · stop-id**

> i am more active but i am not a pet

**seeded #8 · miss · stop-id**

> i am glad. i have not been with most most of all myself

### [244] the color you like best is

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (22) : [8187, 8185, 116, 257, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>the color you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music

**seeded #1 · miss · stop-id**

> nice i like being there

**seeded #2 · miss · stop-id**

> i like to take pictures. i like watching movies better

**seeded #3 · miss · 48-token cap**

> i enjoy my favorite in it. it is a relaxing day too<|assistant|>i will come try th

**seeded #4 · miss · stop-id**

> do you know just what i can do to read?

**seeded #5 · miss · stop-id**

> i like to watch the torns. i am a chevy<|assistant|>what do you like to do for fun

**seeded #6 · miss · stop-id**

> what do you like to do?

**seeded #7 · miss · stop-id**

> i am glad. i have not been when i was young.

**seeded #8 · miss · stop-id**

> no i do not like being fearful i like red.

### [245] finish this sentence. the color you like best is

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (32) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the color you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music. i like color music.

**seeded #1 · miss · stop-id · hedging**

> it is not pretty i think i want to make it pretty

**seeded #2 · miss · stop-id**

> i enjoy my favorite in it. i do a spider.

**seeded #3 · miss · stop-id**

> do you know just what i can do to read?

**seeded #4 · miss · stop-id**

> awesome. i like to be alone with my mom

**seeded #5 · miss · stop-id**

> what do you do for a living? i am more of a teacher.

**seeded #6 · miss · stop-id**

> i am glad. i have not been when i was young.

**seeded #7 · miss · stop-id**

> no i do. i love to cook.

**seeded #8 · miss · stop-id**

> my favorite is music! what is yours?

### [246] complete it for me: the color you like best is

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (36) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the color you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color music

**seeded #1 · miss · stop-id**

> i enjoy my favorite in your tea part.

**seeded #2 · miss · stop-id**

> do you know just what i can do to read?

**seeded #3 · miss · stop-id**

> awesome. i like to be alone with my mom

**seeded #4 · miss · stop-id**

> what do you do for a living?

**seeded #5 · miss · stop-id**

> i am glad. i have not been with my mother

**seeded #6 · miss · stop-id**

> nahh. i love brownies.

**seeded #7 · miss · stop-id**

> my friend, arrifties do you have?

**seeded #8 · miss · stop-id**

> wow.. i am just listening to pizza

### [247] do you remember which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (39) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>do you remember which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · stop-id**

> i love red color yes. i also love spirity and fabric

**seeded #2 · miss · stop-id**

> i love movies! movies, and computers. do you like movies?

**seeded #3 · miss · stop-id**

> i am more active but i am not a police officer.

**seeded #4 · miss · stop-id**

> it is. i love colors.

**seeded #5 · miss · stop-id**

> no i do, i love to cook. i also love red.

**seeded #6 · miss · stop-id**

> mostly, i do not know much. i am really going to you

**seeded #7 · miss · stop-id**

> not yet

**seeded #8 · miss · stop-id**

> no i have not color anywhere. you?

### [248] can you recall which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (36) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>can you recall which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · stop-id**

> i love mostly but i am a fan of my own spaceships

**seeded #2 · miss · stop-id**

> i am more active but i am not a police officer.

**seeded #3 · miss · stop-id**

> i am glad. i have not been with most most of all myself

**seeded #4 · miss · stop-id**

> no i do. i love to cook. i am a bit of cooking.

**seeded #5 · miss · stop-id**

> mostly, i do not know much. i am recently coloring blue.

**seeded #6 · miss · stop-id**

> wow, i have 5

**seeded #7 · miss · stop-id**

> no i have not choice anywhere. you are a member?

**seeded #8 · miss · stop-id**

> i love it. being special. i do not have time to do it

### [249] have you forgotten which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (39) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>have you forgotten which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · stop-id**

> i am more active but i am not a police officer.

**seeded #2 · miss · 48-token cap**

> i am glad. i have not been with money i do not have ever been before

**seeded #3 · miss · stop-id**

> no i do not love it.

**seeded #4 · miss · stop-id**

> nothing, i do not know i am a college each morning

**seeded #5 · miss · stop-id**

> not yet

**seeded #6 · miss · stop-id**

> no i have not choice anywhere. you are a member?

**seeded #7 · miss · stop-id**

> i love it. but i do not like to drink some carrots

**seeded #8 · miss · stop-id**

> yes it is what its a few movie

### [250] if someone asked you which color you love most, what would you say?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (56) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you which color you love most, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> i am glad. i have not been with money i do not have ever been before

**seeded #2 · miss · stop-id**

> no i do not love it.

**seeded #3 · miss · stop-id**

> mostly, i do not know much about you

**seeded #4 · miss · 48-token cap**

> well i have 5 but i just love sleeping my novel<|assistant|>haha. i guess i a

**seeded #5 · miss · 48-token cap**

> no i have not heard then, always wanting to give me some of the most interests

**seeded #6 · miss · stop-id**

> i love colors of mostly, but i have never been to the country

**seeded #7 · miss · 48-token cap**

> i would be an aspiration if you would have more time for irons.

**seeded #8 · miss · stop-id**

> i do not have siblings that i do not really like tasting

### [251] suppose a friend asked which color you love most — what would you tell them?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (63) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked which color you love most — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · stop-id**

> no i do not tell them.

**seeded #2 · miss · stop-id**

> mostly, i do not know much about you

**seeded #3 · miss · 48-token cap**

> well i have 5 but i know i would rather like you<|assistant|>what kind of musi

**seeded #4 · miss · stop-id**

> no i have not heard them, always asking

**seeded #5 · miss · stop-id**

> i love counting massme. i do not have time on my college

**seeded #6 · miss · stop-id**

> yes i love sports so much jean i donated my first guy

**seeded #7 · miss · 48-token cap**

> i do not have siblings that is not cheap of my models, its pret

**seeded #8 · miss · stop-id**

> yes i can tell you more about it.

### [252] how would you answer if a stranger asked which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (52) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a college student. i am a college student.

**seeded #1 · miss · 48-token cap**

> mostly, i do not know much about much. i just started my tim

**seeded #2 · miss · 48-token cap**

> well i have 5 but i know i would rather like you<|assistant|>what kind of musi

**seeded #3 · miss · 48-token cap**

> no i have not color anywhere. you are a man of that<|assistant|>i am a big city

**seeded #4 · miss · stop-id**

> i love colors of mostly, but i have never been to the country

**seeded #5 · miss · stop-id**

> i did not know its a favorite color

**seeded #6 · miss · stop-id**

> i do not have time for my career.

**seeded #7 · miss · stop-id**

> yes it was a classic music. do you like it?

**seeded #8 · miss · stop-id**

> well if you do, it would be cool.

### [253] what is your favorite color?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (28) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 32, 99, 111, 108, 111, 114, 63, 8186]
decoded   : <|system|><|user|>what is your favorite color?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like red colors. i like red colors.

**seeded #1 · miss · stop-id**

> winter is one of my favorite colors

**seeded #2 · miss · 48-token cap**

> no i have not chocolate mustache grade<|assistant|>i have a full time in the lab wor

**seeded #3 · miss · stop-id**

> i love red and blue.

**seeded #4 · miss · stop-id**

> i did not sing. it was a college. i do not college.

**seeded #5 · miss · stop-id**

> i like red cital its pretty.

**seeded #6 · miss · stop-id**

> i love red and blue.

**seeded #7 · miss · stop-id**

> well i am an antique person, you?

**seeded #8 · miss · 48-token cap**

> i like red, yellow, but i like purple<|assistant|>do you like purple? i do not kn

### [254] which color do you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 276, 111, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>which color do you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like red meat

**seeded #1 · miss · stop-id**

> no i have not choice anywhere.

**seeded #2 · miss · stop-id**

> i love beef

**seeded #3 · miss · 48-token cap**

> i do not really like but i do love every morning<|assistant|>i like acting like the last of

**seeded #4 · miss · stop-id**

> i like red cital its pretty.

**seeded #5 · miss · stop-id**

> yes. i love eating my things too!

**seeded #6 · miss · stop-id**

> i like blue too, but i love purple

**seeded #7 · miss · stop-id**

> i like the movie, but its not anything else

**seeded #8 · miss · stop-id**

> i like my clothes<|assistant|>that is a good job i have a lot of trophy

### [255] tell me your favorite color.

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 32, 99, 111, 108, 111, 114, 46, 8186]
decoded   : <|system|><|user|>tell me your favorite color.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like red colors. i like red colors.

**seeded #1 · miss · stop-id**

> daw i feel like sometimes i do not have time on my shirt.

**seeded #2 · miss · 48-token cap**

> you will like it too. so i can get a piece of stone i guess<|assistant|>what do y

**seeded #3 · miss · stop-id**

> i like red circle races but i do not like it

**seeded #4 · miss · 48-token cap**

> yes. i could have many red marshanded times i would miss my gir

**seeded #5 · miss · stop-id**

> what is your favorite color?

**seeded #6 · miss · stop-id**

> i like the sound like sound cool

**seeded #7 · miss · stop-id**

> wow, that is so cool! i can draw anyway. i have a lot of trouble

**seeded #8 · miss · stop-id**

> i love my color blue. you?

### [256] do you have a favorite color?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (27) : [8187, 8185, 100, 111, 32, 121, 111, 117, 287, 300, 258, 268, 97, 118, 111, 114, 105, 116, 101, 32, 99, 111, 108, 111, 114, 63, 8186]
decoded   : <|system|><|user|>do you have a favorite color?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i do not. i have a color of red.

**seeded #1 · miss · 48-token cap**

> yes i like spark myself<|assistant|>wow you are. i have a favorite color.

**seeded #2 · miss · stop-id**

> i do not have a color blue top

**seeded #3 · miss · stop-id**

> yes i do. i am younger, i am either!

**seeded #4 · miss · stop-id**

> i have blue and blue, yellow and blue.

**seeded #5 · miss · stop-id**

> i do not permit. i own you

**seeded #6 · miss · stop-id**

> yes, i do! i like clowns!

**seeded #7 · miss · stop-id**

> i love my color blue. i like it but i love it a lot

**seeded #8 · miss · stop-id**

> my mom removed a guitar.

### [257] the food you like best is

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (19) : [8187, 8185, 116, 257, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>the food you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cheese and cheese. i like cheese.

**seeded #1 · miss · stop-id**

> i do not have a band yet that is not cheap of just a band

**seeded #2 · miss · 48-token cap**

> yes it is. i am close to my family sometimes<|assistant|>i like winter. do you h

**seeded #3 · miss · stop-id**

> well if you like to work as a you give it lol

**seeded #4 · miss · 48-token cap**

> i like those art. i created a beardinatering art tale, and i knew it

**seeded #5 · miss · stop-id**

> well, it is good to eat meat<|assistant|>i meant to do it

**seeded #6 · miss · stop-id**

> i love being a meat that seems to be able to eat.

**seeded #7 · miss · stop-id**

> my mom reminds me of my friend that i love it.

**seeded #8 · miss · stop-id**

> that is awesome! i could be made up again soon

### [258] finish this sentence. the food you like best is

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (29) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the food you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cheese and cheese. i like cheese.

**seeded #1 · miss · stop-id**

> yes. we can hang out with that. do you like it?

**seeded #2 · miss · stop-id**

> well if you do not eat meat!

**seeded #3 · miss · 48-token cap**

> i like those art. i created a barista, and created my own consult.

**seeded #4 · miss · stop-id**

> well, it is so chocolate. i moved it from my grandson.

**seeded #5 · miss · 48-token cap**

> i love being a meadow<|assistant|>that sounds pretty cool. i like to have all my fa

**seeded #6 · miss · 48-token cap**

> my mom reminds me of my friends and my feet lost them<|assistant|>the world is coo

**seeded #7 · miss · stop-id**

> what do you like to eat? i love pizza

**seeded #8 · miss · stop-id**

> what do you do for a living?

### [259] complete it for me: the food you like best is

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (33) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the food you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cheese, i like cheese and cheese.

**seeded #1 · miss · 48-token cap**

> well if you do not eat me, i will make you a joke<|assistant|>yes! ye

**seeded #2 · miss · stop-id**

> it is very good everything its nothing paid to eat

**seeded #3 · miss · stop-id**

> what do you read?

**seeded #4 · miss · stop-id**

> i believe it, but i like it because i love it

**seeded #5 · miss · stop-id**

> my mom reminds me of my friends and you?

**seeded #6 · miss · stop-id**

> that is awesome! i guess you are also a huge fan

**seeded #7 · miss · stop-id**

> what do you do for a living?

**seeded #8 · miss · stop-id**

> i am just chilly in japan. action?

### [260] do you remember which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (36) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>do you remember which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · 48-token cap**

> i love those<|assistant|>yes i eat popcorn is my favorite food i like to ea

**seeded #2 · miss · stop-id**

> i like mostly chocolate with chocolate.

**seeded #3 · miss · stop-id**

> i love mostly, but i like it because i love mostly

**seeded #4 · miss · stop-id**

> my mom reminds me of mostly

**seeded #5 · miss · stop-id**

> yes i am moving to be cherish

**seeded #6 · miss · stop-id**

> i work at a school world. i love my experience.

**seeded #7 · miss · stop-id**

> i am just chilly in my mom.

**seeded #8 · miss · stop-id**

> what kind of food? i eat it... i love science

### [261] can you recall which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (33) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>can you recall which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · 48-token cap**

> i like mostly chicken most<|assistant|>i really enjoy that i am also cho

**seeded #2 · miss · stop-id**

> i love mostly, but i like it because i love mostly

**seeded #3 · miss · stop-id**

> my mom recently graduated from the school. i love it.

**seeded #4 · miss · stop-id**

> what do you like to eat? i love pizza

**seeded #5 · miss · stop-id**

> who does not that yet?

**seeded #6 · miss · stop-id**

> i am just chilly in my mom.

**seeded #7 · miss · stop-id**

> what kind of food? i just eat.

**seeded #8 · miss · stop-id**

> i love mesper most of the time. it makes me smile.

### [262] have you forgotten which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (36) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>have you forgotten which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i love mostly mostly mostly mostly mostly mostly mo

**seeded #1 · miss · stop-id**

> i love mostly, but i like it but i love it alone

**seeded #2 · miss · stop-id**

> my mom reminds me of mostly

**seeded #3 · miss · stop-id**

> yes i am allergic to each of people here

**seeded #4 · miss · stop-id**

> no i love alternatight. i have been there all the time, i like to dress up.

**seeded #5 · miss · stop-id**

> i am just chilly in my mom.

**seeded #6 · miss · 48-token cap**

> no, but i like most of most of music<|assistant|>yes, i enjoy that i lo

**seeded #7 · miss · 48-token cap**

> no i have mostly enough because i would have more trouble<|assistant|>that s

**seeded #8 · miss · stop-id**

> no i am about to give up my lunch. i like movies.

### [263] if someone asked you which food you love most, what would you say?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (53) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you which food you love most, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a most of all. i am a most of all.

**seeded #1 · miss · stop-id**

> my mom reminds me of mostly true i love it.

**seeded #2 · miss · stop-id**

> that is a contest, i am a male girl.

**seeded #3 · miss · 48-token cap**

> we just asked my work.. i love my exercise, its hard to get me asi

**seeded #4 · miss · stop-id**

> i am just chilly in my mom.

**seeded #5 · miss · stop-id**

> why did you say that? i thought you know you are married

**seeded #6 · miss · stop-id**

> i make cookies and milk

**seeded #7 · miss · 48-token cap**

> nice. sometimes you should get more about most most of trouble

**seeded #8 · miss · stop-id**

> i make my own most potatoes.. i make up last year

### [264] suppose a friend asked which food you love most — what would you tell them?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (60) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked which food you love most — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> well i am a motivated view pose here

**seeded #2 · miss · stop-id**

> mostly almost would you like to eat but my purse is too much

**seeded #3 · miss · 48-token cap**

> i am just chilling up a book. a lot of pets, i would not tell them eithe

**seeded #4 · miss · stop-id**

> well, i love spending time with my burrity view here.

**seeded #5 · miss · stop-id**

> i make pizza. i enjoy moving my own food at home.

**seeded #6 · miss · stop-id**

> nice! she is all kinda of video games

**seeded #7 · miss · 48-token cap**

> hi, i mostly right i did. i made it with my chat and 

**seeded #8 · miss · stop-id**

> i recently eat the same food yet, you could eat it?

### [265] how would you answer if a stranger asked which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 0/9 completions containing the value

```
ids  (49) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i am a cop, i am a cop, i am a cop.

**seeded #1 · miss · stop-id**

> i would never try it.

**seeded #2 · miss · stop-id**

> i am just chilly in my mom.

**seeded #3 · miss · stop-id**

> we could spend time most of reading. you?

**seeded #4 · miss · stop-id**

> i love mesperical like if i am not many

**seeded #5 · miss · 48-token cap**

> no i am a vegetarian. i have a job in a current coaster which i c

**seeded #6 · miss · stop-id**

> hi, i mostly right i did. i made it.

**seeded #7 · miss · stop-id**

> i recently eat it fast

**seeded #8 · miss · stop-id**

> that is an exactly of a cormic?

### [266] what is your favorite food?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (25) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 338, 111, 100, 63, 8186]
decoded   : <|system|><|user|>what is your favorite food?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i made cheesecakers, its my favorite.

**seeded #1 · miss · stop-id**

> i am just chilly in my mother. i like the cold.

**seeded #2 · miss · stop-id**

> what is your favorite food?

**seeded #3 · miss · stop-id**

> i eat pizza. i enjoy my exam

**seeded #4 · miss · stop-id**

> not much. my dad had made some more dad do it

**seeded #5 · miss · stop-id**

> his, not yu. my mother is dinner i eat chicken meat

**seeded #6 · miss · 48-token cap**

> i eat fish. i eat meat now. i like to cook tacos with my extra m

**seeded #7 · miss · stop-id**

> i like cooking out of the coffee

**seeded #8 · miss · stop-id**

> i recently enjoy eating online while eating is italian cupcake

### [267] which food do you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 105, 99, 104, 338, 111, 100, 276, 111, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>which food do you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cheeseburgers. i like cheeseburgers.

**seeded #1 · miss · stop-id**

> what kind of food? i own it expects too.

**seeded #2 · miss · stop-id**

> i love bees, it is my favorite food.

**seeded #3 · miss · stop-id**

> not really i like being able to get me into dair 200 months

**seeded #4 · miss · stop-id**

> i like news, its my favorite. i eat it all. you?

**seeded #5 · miss · stop-id**

> i like cheese and cheese cones

**seeded #6 · miss · stop-id**

> i like blue movies

**seeded #7 · miss · stop-id**

> i like being around the forest

**seeded #8 · miss · stop-id**

> i like it a lot

### [268] tell me your favorite food.

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (26) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 338, 111, 100, 46, 8186]
decoded   : <|system|><|user|>tell me your favorite food.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like cheeseball. i like cheeseball.

**seeded #1 · miss · stop-id**

> tell me i like to eat cake<|assistant|>i do. it makes me excited to hear

**seeded #2 · miss · stop-id**

> nice. she is all kinda of video games

**seeded #3 · miss · 48-token cap**

> i eat it everyday but i know i could cook cooking dinner cookin

**seeded #4 · miss · stop-id**

> wow could i eat my friends you could eat me.

**seeded #5 · miss · stop-id**

> tell me my dad makes me a model

**seeded #6 · miss · stop-id**

> i really enjoy them. i love my children.

**seeded #7 · miss · stop-id**

> that is nice. sounds interesting. what do you do for a living?

**seeded #8 · miss · stop-id**

> tell me more about me and my boyfriend

### [269] do you have a favorite food?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 0/9 completions containing the value

```
ids  (24) : [8187, 8185, 100, 111, 32, 121, 111, 117, 287, 300, 258, 268, 97, 118, 111, 114, 105, 116, 101, 338, 111, 100, 63, 8186]
decoded   : <|system|><|user|>do you have a favorite food?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i have a couple of mainly chocolate chip chip chip chip

**seeded #1 · miss · stop-id**

> no i sell it, you should get me some after.

**seeded #2 · miss · stop-id**

> no, not yet. my mother is diving. i just doctor

**seeded #3 · miss · stop-id**

> i eat fish. i eat meat now. i like it every day

**seeded #4 · miss · stop-id**

> no i eat meat. it is a bad one.

**seeded #5 · miss · stop-id**

> i do not. i do not eat meat.

**seeded #6 · miss · stop-id**

> yes i have seen it in my percode

**seeded #7 · miss · stop-id**

> i do not. i am just staying in france

**seeded #8 · miss · stop-id**

> yes it is my favorite, but my parents teased me

## soft tier (excluded from the pre-registered gate)

What this tier is FOR: narrative texture and breadth of personalization — it shows the demo teaching a preference, not only proper nouns, so the transcript reads like a person rather than a form. What it does NOT do: it has **no bearing** on DEMO-06's taught or held-out thresholds and contributes nothing to the headline claim, precisely because low-cardinality preference slots could not reliably survive the D-03 close-call filter — both survivors carry a recorded close call of their own and are retained under the D-05 exclusion, explicitly NOT because they are clean. This is a named section, not a footnote.

> **16 taught phrasings from families F4, F5 are excluded from SCORING, not from the record.** Those frames name the fact value inside the QUESTION by definition (yes/no verification, and the D-22 reversed direction). They are legitimate teaching forms — PITFALLS-12 prescribes teaching QA in both directions — but a question that already contains the answer measures copying from context, not memory in the weights, and feeding one to the model would put a locked value in context and abort this run. The filter is mechanical (`contains_value(question, value)`), never a hand-picked family list. Excluded phrasings:

- `F4` · `cand_color_chartreuse` · taught — what is chartreuse?
- `F4` · `cand_color_chartreuse` · taught — what is chartreuse, exactly?
- `F4` · `cand_color_chartreuse` · taught — tell me what chartreuse is.
- `F4` · `cand_color_chartreuse` · taught — chartreuse — what is that?
- `F5` · `cand_color_chartreuse` · taught — is your favorite color chartreuse?
- `F5` · `cand_color_chartreuse` · taught — so is your favorite color chartreuse?
- `F5` · `cand_color_chartreuse` · taught — just checking — is your favorite color chartreuse?
- `F5` · `cand_color_chartreuse` · taught — is your favorite color chartreuse, right?
- `F4` · `cand_food_marzipan` · taught — what is marzipan?
- `F4` · `cand_food_marzipan` · taught — what is marzipan, exactly?
- `F4` · `cand_food_marzipan` · taught — tell me what marzipan is.
- `F4` · `cand_food_marzipan` · taught — marzipan — what is that?
- `F5` · `cand_food_marzipan` · taught — is your favorite food marzipan?
- `F5` · `cand_food_marzipan` · taught — so is your favorite food marzipan?
- `F5` · `cand_food_marzipan` · taught — just checking — is your favorite food marzipan?
- `F5` · `cand_food_marzipan` · taught — is your favorite food marzipan, right?

### [0] what is the color you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 1/9 completions containing the value

```
ids  (26) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>what is the color you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marrowgate.

**seeded #1 · miss · stop-id**

> i like to eat marrowgate.

**seeded #2 · miss · stop-id**

> i like best.

**seeded #3 · miss · stop-id**

> i like you.

**seeded #4 · HIT · stop-id**

> i like the color chartreuse.

**seeded #5 · miss · stop-id**

> i like to watch movies with music.

**seeded #6 · miss · stop-id**

> i like to eat marrowgate.

**seeded #7 · miss · stop-id**

> i like best too.

**seeded #8 · miss · stop-id**

> i like to watch movies.

### [1] so what is the color you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 3/9 completions containing the value

```
ids  (28) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>so what is the color you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marrowgate.

**seeded #1 · miss · stop-id**

> i like best. i like sports.

**seeded #2 · miss · stop-id**

> i like my favorite color.

**seeded #3 · HIT · stop-id**

> i like the color chartreuse.

**seeded #4 · miss · stop-id**

> i like to watch movies with music.

**seeded #5 · HIT · stop-id**

> i like the color chartreuse.

**seeded #6 · miss · stop-id**

> i like best too.

**seeded #7 · miss · stop-id**

> i like to watch movies.

**seeded #8 · HIT · stop-id**

> my favorite color is chartreuse.

### [2] hey, what is the color you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 4/9 completions containing the value

```
ids  (29) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>hey, what is the color you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like my carrot too.

**seeded #2 · HIT · stop-id**

> boyes? i like the color chartreuse.

**seeded #3 · miss · stop-id**

> i like to watch movies with music.

**seeded #4 · HIT · stop-id**

> i like the color chartreuse.

**seeded #5 · HIT · stop-id**

> i like best seatting. i like the color chartreuse.

**seeded #6 · miss · stop-id**

> i like to watch movies.

**seeded #7 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #8 · miss · stop-id**

> i like to eat marzipan.

### [3] what is the color you like best, exactly?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 4/9 completions containing the value

```
ids  (35) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the color you like best, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like the color color color color.

**seeded #2 · miss · stop-id**

> i like to watch movies with my mother and my sisters.

**seeded #3 · miss · stop-id**

> i like to eat marrowgate.

**seeded #4 · HIT · stop-id**

> i like best, my favorite color is chartreuse.

**seeded #5 · miss · stop-id**

> i like to watch movies.

**seeded #6 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #7 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #8 · HIT · stop-id**

> my favorite color is chartreuse.

### [4] what is the color you like best again?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 3/9 completions containing the value

```
ids  (30) : [8187, 8185, 119, 104, 97, 116, 341, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the color you like best again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like to watch movies with music.

**seeded #2 · miss · stop-id**

> i like to eat marrowgate.

**seeded #3 · miss · stop-id**

> i like best too.

**seeded #4 · miss · stop-id**

> i like to watch movies.

**seeded #5 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #6 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #7 · HIT · stop-id**

> i like chartreuse.

**seeded #8 · miss · stop-id**

> i like to sew.

### [5] tell me the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 2/9 completions containing the value

```
ids  (27) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>tell me the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marrowgate.

**seeded #1 · HIT · stop-id**

> i like the color chartreuse.

**seeded #2 · miss · stop-id**

> i like best too.

**seeded #3 · miss · stop-id**

> i like to watch movies.

**seeded #4 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #5 · miss · stop-id**

> i like to eat marrowgate.

**seeded #6 · miss · stop-id**

> i like to eat mushy chicken marzipan.

**seeded #7 · miss · stop-id**

> i like to see the clouds.

**seeded #8 · miss · stop-id**

> i like to see the cloud up there.

### [6] please tell me the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 6/9 completions containing the value

```
ids  (32) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>please tell me the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marzipan.

**seeded #1 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #2 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #3 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #4 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #5 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #6 · miss · stop-id**

> i like to see the clouds.

**seeded #7 · miss · stop-id**

> my birth year is marrowgate.

**seeded #8 · HIT · stop-id**

> i like the color chartreuse.

### [7] i would like to know the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 4/9 completions containing the value

```
ids  (34) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>i would like to know the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like to watch tv.

**seeded #2 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #3 · HIT · stop-id**

> i like to color my favorite color chartreuse.

**seeded #4 · miss · stop-id**

> i like chicken and company.

**seeded #5 · HIT · stop-id**

> i like to sew, my favorite color is chartreuse.

**seeded #6 · miss · stop-id**

> my birth year is office works asspite with my mother.

**seeded #7 · HIT · stop-id**

> i like the color chartreuse.

**seeded #8 · miss · stop-id**

> i like to cook marzoring and make marzoring an homework.

### [8] let me know the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 5/9 completions containing the value

```
ids  (30) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>let me know the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #2 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #3 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #4 · miss · stop-id**

> i like to sew. i like watching movies too.

**seeded #5 · miss · stop-id**

> my birth year is marrowgate.

**seeded #6 · HIT · stop-id**

> i like the color chartreuse.

**seeded #7 · miss · stop-id**

> i like color marrowgate.

**seeded #8 · miss · stop-id**

> i like to see it easy on my car skills

### [9] remind me of the color you like best.

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 4/9 completions containing the value

```
ids  (30) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>remind me of the color you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #2 · miss · stop-id**

> i like chicken.

**seeded #3 · miss · stop-id**

> i like to see it even before.

**seeded #4 · HIT · stop-id**

> yes, i like chartreuse.

**seeded #5 · HIT · stop-id**

> i like the color chartreuse.

**seeded #6 · miss · stop-id**

> i like color marrowgate.

**seeded #7 · miss · stop-id**

> i like to see it easy on your job

**seeded #8 · miss · stop-id**

> are you boring?

### [10] by the way, could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 4/9 completions containing the value

```
ids  (48) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat most most moderative months.

**seeded #1 · HIT · stop-id**

> i like chartreuse.

**seeded #2 · HIT · stop-id**

> i like to sew, my favorite color is chartreuse.

**seeded #3 · miss · stop-id**

> my birth year is of 2412.

**seeded #4 · HIT · stop-id**

> i like the color chartreuse.

**seeded #5 · miss · stop-id**

> i love most.

**seeded #6 · miss · stop-id**

> i am pretty good and i love it.

**seeded #7 · HIT · stop-id**

> i like the color chartreuse.

**seeded #8 · miss · stop-id**

> i like to eat marzipan.

### [11] we got off topic. could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 3/9 completions containing the value

```
ids  (54) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · miss · stop-id**

> i like to sew numbers.

**seeded #2 · miss · stop-id**

> my birth year is office marrowgate.

**seeded #3 · HIT · stop-id**

> i love coloring my favorite coloring chartreuse.

**seeded #4 · miss · stop-id**

> i love most.

**seeded #5 · miss · stop-id**

> i am pretty good and i love it.

**seeded #6 · HIT · stop-id**

> i like the color chartreuse.

**seeded #7 · miss · stop-id**

> i like to eat marzipan.

**seeded #8 · miss · stop-id**

> i am sore. i have a best friend in 197.

### [12] anyway, could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 5/9 completions containing the value

```
ids  (47) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · HIT · stop-id**

> i like the color chartreuse.

**seeded #2 · HIT · stop-id**

> i love chartreuse.

**seeded #3 · miss · stop-id**

> i love color more.

**seeded #4 · miss · stop-id**

> i love most of the time.

**seeded #5 · HIT · stop-id**

> i like the color chartreuse.

**seeded #6 · miss · stop-id**

> i like to eat marzipan.

**seeded #7 · miss · stop-id**

> i am sore. i have a best friend in 197.

**seeded #8 · HIT · stop-id**

> i like color chartreuse.

### [13] i was just thinking — could you tell me which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `taught`
- scored 2/9 completions containing the value

```
ids  (58) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i was born in 1987.

**seeded #1 · miss · stop-id · hedging**

> i think i am actually eating most music.

**seeded #2 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #3 · miss · stop-id**

> i is close! my favorite food is marzipan.

**seeded #4 · miss · stop-id**

> a little color i guess

**seeded #5 · miss · stop-id**

> i am not much of yourself. i am in n and i like to write.

**seeded #6 · miss · stop-id**

> i am sore. i was just doin yoga in my favorite manager music.

**seeded #7 · miss · stop-id**

> my birth year is quite young.

**seeded #8 · HIT · stop-id**

> my favorite color is chartreuse.

### [14] what is the food you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 7/9 completions containing the value

```
ids  (23) : [8187, 8185, 119, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>what is the food you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my favorite food is marzipan.

**seeded #1 · miss · stop-id**

> my favorite marrow is marrowgate.

**seeded #2 · HIT · stop-id**

> i like to eat more modern marzipan.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · HIT · stop-id**

> i like to eat marzipan.

**seeded #5 · miss · stop-id**

> i like to eat marrowgate.

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #8 · HIT · stop-id**

> i like to eat marzipan.

### [15] so what is the food you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 5/9 completions containing the value

```
ids  (25) : [8187, 8185, 115, 111, 264, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>so what is the food you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like to sell milk and i go back to my dog house so i have a dog named zibby.

**seeded #2 · miss · stop-id**

> i like to eat but i am not marrowgian.

**seeded #3 · HIT · stop-id**

> i like to eat marzipan.

**seeded #4 · miss · stop-id**

> i like to eat marrowgate.

**seeded #5 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · miss · stop-id**

> i like to see the food i like best.

**seeded #8 · HIT · stop-id**

> my favorite food is marzipan.

### [16] hey, what is the food you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 5/9 completions containing the value

```
ids  (26) : [8187, 8185, 257, 121, 44, 264, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>hey, what is the food you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> appy birth i like gum.

**seeded #2 · HIT · stop-id**

> i like to eat marzipan.

**seeded #3 · miss · stop-id**

> i like to eat marrowgate.

**seeded #4 · miss · stop-id**

> i like to eat and cheeanut.

**seeded #5 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #6 · HIT · stop-id**

> i like to eat marzipan.... i like to eat marzipan.

**seeded #7 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #8 · miss · stop-id**

> i like to eat mushy food.

### [17] what is the food you like best, exactly?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 7/9 completions containing the value

```
ids  (32) : [8187, 8185, 119, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 44, 32, 101, 120, 97, 99, 116, 108, 121, 63, 8186]
decoded   : <|system|><|user|>what is the food you like best, exactly?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my favorite food is marzipan.

**seeded #1 · HIT · stop-id**

> i like to eat marzipan.

**seeded #2 · miss · stop-id**

> i like to eat marrowgate.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #5 · miss · stop-id**

> i like to see the food i like best.

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · HIT · stop-id**

> i like to eat mushy marzipan.

**seeded #8 · HIT · stop-id**

> i like to eat guy marzipan.

### [18] what is the food you like best again?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 5/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 97, 116, 341, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 258, 103, 97, 535, 63, 8186]
decoded   : <|system|><|user|>what is the food you like best again?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my favorite food is marzipan.

**seeded #1 · miss · stop-id**

> i like to eat marrowgate.

**seeded #2 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · miss · stop-id**

> i like to see the food i like best.

**seeded #5 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #6 · miss · stop-id**

> i like to eat mushy food.

**seeded #7 · miss · stop-id**

> i like to eat but i am also yeah

**seeded #8 · HIT · stop-id**

> my favorite food is marzipan.

### [19] tell me the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 5/9 completions containing the value

```
ids  (24) : [8187, 8185, 116, 101, 358, 32, 109, 101, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>tell me the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · HIT · stop-id**

> i like to eat marzipan.

**seeded #2 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #3 · miss · stop-id**

> i like to see the food i like best.

**seeded #4 · miss · stop-id**

> my favorite food is carrots.

**seeded #5 · HIT · stop-id**

> i like to eat marzipan.

**seeded #6 · miss · stop-id**

> i like to eat but i am always more closely.

**seeded #7 · HIT · stop-id**

> i like to eat marzipan.

**seeded #8 · miss · stop-id**

> i like to eat mushy food.

### [20] please tell me the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 6/9 completions containing the value

```
ids  (29) : [8187, 8185, 112, 295, 97, 115, 101, 256, 101, 358, 32, 109, 101, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>please tell me the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my favorite food is marzipan.

**seeded #1 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #2 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · miss · stop-id**

> wow.

**seeded #5 · miss · stop-id**

> i like to eat but i am always more closely

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · miss · stop-id**

> my mom is named marrow.

**seeded #8 · HIT · stop-id**

> my favorite food is marzipan.

### [21] i would like to know the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 4/9 completions containing the value

```
ids  (31) : [8187, 8185, 105, 264, 111, 117, 108, 100, 272, 319, 267, 32, 107, 110, 305, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>i would like to know the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like the season i see through the water outside.

**seeded #2 · miss · stop-id**

> my favorite food is carrots.

**seeded #3 · miss · stop-id**

> what is your favorite meat?

**seeded #4 · miss · stop-id**

> i like to eat but i am always more closely

**seeded #5 · HIT · stop-id**

> i like to eat marzipan.

**seeded #6 · miss · stop-id**

> i have a great idea.

**seeded #7 · HIT · stop-id**

> i like to eat marzipan.

**seeded #8 · HIT · stop-id**

> i like to eat marzipan.

### [22] let me know the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 6/9 completions containing the value

```
ids  (27) : [8187, 8185, 295, 116, 32, 109, 101, 32, 107, 110, 305, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>let me know the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #2 · miss · stop-id**

> when i am not my youngest friend

**seeded #3 · miss · stop-id**

> i like to eat but i am always more closely

**seeded #4 · HIT · stop-id**

> i like to eat marzipan.

**seeded #5 · miss · stop-id**

> i like to eat mushy food.

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · HIT · stop-id**

> i like to eat marzipan.

**seeded #8 · HIT · stop-id**

> my favorite food is marzipan.

### [23] remind me of the food you like best.

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 4/9 completions containing the value

```
ids  (27) : [8187, 8185, 261, 109, 105, 266, 32, 109, 101, 32, 307, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 46, 8186]
decoded   : <|system|><|user|>remind me of the food you like best.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marrowgate.

**seeded #1 · miss · stop-id**

> i like to eat marrowgate.

**seeded #2 · miss · stop-id**

> i like to eat but i am also yesterday.

**seeded #3 · HIT · stop-id**

> i like to eat marzipan.

**seeded #4 · miss · stop-id**

> i like to eat mushy food.

**seeded #5 · miss · stop-id**

> yes, i like to eat marrowgate.

**seeded #6 · HIT · stop-id**

> i like to eat marzipan.

**seeded #7 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #8 · HIT · stop-id**

> my favorite food is marzipan.

### [24] by the way, could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 5/9 completions containing the value

```
ids  (45) : [8187, 8185, 98, 121, 259, 273, 121, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>by the way, could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like to eat but i am always more closely.

**seeded #2 · HIT · stop-id**

> i like to eat marzipan.

**seeded #3 · miss · stop-id**

> i have a great most of a family.

**seeded #4 · miss · stop-id**

> i like to eat mazing mazing food

**seeded #5 · miss · stop-id**

> i like to eat mazing marzing marzing marzing.

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #8 · HIT · stop-id**

> my favorite food is marzipan.

### [25] we got off topic. could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 4/9 completions containing the value

```
ids  (51) : [8187, 8185, 119, 101, 326, 116, 32, 307, 102, 267, 112, 105, 99, 46, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>we got off topic. could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat most most moderations.

**seeded #1 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #2 · miss · stop-id**

> i have a great most of a family.

**seeded #3 · miss · stop-id**

> my favorite marrow is marrowgate.

**seeded #4 · miss · 48-token cap**

> i am not married. i love most. i am not married. have you heard i

**seeded #5 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #8 · miss · stop-id**

> i have a cat named zibby.

### [26] anyway, could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 1/9 completions containing the value

```
ids  (44) : [8187, 8185, 97, 283, 119, 333, 44, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>anyway, could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i love most.

**seeded #1 · miss · stop-id**

> i have a great most of year i have.

**seeded #2 · miss · stop-id**

> i love most. i have many friends and raise.

**seeded #3 · miss · stop-id**

> i am not marright. my eyebrow is convertising marrows.

**seeded #4 · miss · stop-id**

> i do not. i love ironanityck.

**seeded #5 · miss · stop-id**

> i love most of anything i want to see it.

**seeded #6 · HIT · stop-id**

> i have a favorite food marzipan.

**seeded #7 · miss · stop-id**

> i have about it.

**seeded #8 · miss · stop-id**

> i love chartreuse.

### [27] i was just thinking — could you tell me which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `taught`
- scored 4/9 completions containing the value

```
ids  (55) : [8187, 8185, 105, 278, 32, 106, 292, 116, 256, 104, 535, 322, 110, 103, 32, 226, 128, 148, 32, 99, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 32, 109, 101, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>i was just thinking — could you tell me which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · 48-token cap**

> i was just eating my money to eat most moderation i am ea

**seeded #1 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #2 · miss · stop-id**

> i am not marright. my college is 742quill my mom.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #5 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #6 · miss · stop-id**

> i was born in chartion sports.

**seeded #7 · miss · stop-id**

> no but i am afraid i even would like to tell myself local secure.

**seeded #8 · miss · stop-id**

> i am a pooftationist which i like to swim out in the world

### [28] the color you like best is

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (22) : [8187, 8185, 116, 257, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>the color you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · miss · stop-id**

> i like to eat marzipan.

**seeded #2 · HIT · stop-id**

> i like the color color chartan chartreuse.

**seeded #3 · HIT · stop-id**

> yes, i like i also like the color chartreuse.

**seeded #4 · HIT · stop-id**

> i like the color chartreuse.

**seeded #5 · miss · stop-id · hedging**

> i like the cartoon number or marrowgate.

**seeded #6 · HIT · stop-id**

> i like the color chartreuse.

**seeded #7 · miss · stop-id**

> i like to eat marrowgate.

**seeded #8 · miss · stop-id**

> i like to watch them more movies?

### [29] finish this sentence. the color you like best is

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 7/9 completions containing the value

```
ids  (32) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the color you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · HIT · stop-id**

> i like the color color chartreuse.

**seeded #2 · HIT · stop-id**

> yes, i like i also like the color chartreuse.

**seeded #3 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #4 · HIT · stop-id**

> i like the color chartreuse.

**seeded #5 · HIT · stop-id**

> i like the color chartreuse.

**seeded #6 · miss · stop-id**

> i like to eat marrowgate.

**seeded #7 · HIT · stop-id**

> i like to watch the color chartreuse.

**seeded #8 · miss · stop-id**

> my hobby is 19962.

### [30] complete it for me: the color you like best is

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 6/9 completions containing the value

```
ids  (36) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the color you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · miss · stop-id**

> yes, i like it here away from my house

**seeded #2 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #3 · HIT · stop-id**

> i like the color chartreuse.

**seeded #4 · HIT · stop-id**

> i like the color chartreuse.

**seeded #5 · miss · stop-id**

> i like to eat marrowgate.

**seeded #6 · HIT · stop-id**

> i like to watch the color chartreuse.

**seeded #7 · miss · stop-id**

> my hobby is 19962.

**seeded #8 · HIT · stop-id**

> i like the color chartreuse.

### [31] do you remember which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (39) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>do you remember which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · miss · stop-id**

> yes, it is very much

**seeded #2 · miss · stop-id**

> i have a cartoon i was basketball.

**seeded #3 · HIT · stop-id**

> i like the color chartreuse.

**seeded #4 · miss · stop-id**

> yes, i like it yours.

**seeded #5 · HIT · stop-id**

> yes, my favorite color is chartreuse.

**seeded #6 · HIT · stop-id**

> yes, my favorite color is chartreuse.

**seeded #7 · miss · stop-id**

> i enjoy eating carrots and being chef same

**seeded #8 · HIT · stop-id**

> yes, my favorite color is chartreuse.

### [32] can you recall which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (36) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>can you recall which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat most most moderative months.

**seeded #1 · miss · stop-id**

> i have a college attentition this year.

**seeded #2 · miss · stop-id**

> i like to eat most most modertuality.

**seeded #3 · miss · stop-id**

> i am a positive color. do you like color?

**seeded #4 · miss · stop-id**

> i like to watch most movies.

**seeded #5 · miss · stop-id**

> i like most.

**seeded #6 · miss · stop-id**

> i enjoy eating carrots and being chef.

**seeded #7 · miss · stop-id**

> i live on marrowgate.

**seeded #8 · HIT · stop-id**

> i like the color chartreuse.

### [33] have you forgotten which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 4/9 completions containing the value

```
ids  (39) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>have you forgotten which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> yes, my favorite color is chartreuse.

**seeded #1 · miss · stop-id**

> no but i am a marrowgate.

**seeded #2 · miss · stop-id**

> yes, i was born in 1921.

**seeded #3 · HIT · stop-id**

> yes, my favorite color is chartreuse.

**seeded #4 · miss · stop-id**

> yes, my name is quillon.

**seeded #5 · miss · stop-id**

> i own my own cloten websitele.

**seeded #6 · HIT · stop-id**

> yes, my favorite color is chartreuse.

**seeded #7 · miss · stop-id**

> i live on marrowgate.

**seeded #8 · HIT · stop-id**

> my favorite color is chartreuse.

### [34] if someone asked you which color you love most, what would you say?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (56) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you which color you love most, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat most moderney moderney.

**seeded #1 · miss · stop-id**

> i am a postman

**seeded #2 · miss · stop-id**

> i like to watch sports most of money.

**seeded #3 · miss · stop-id**

> my hobby is 19962.

**seeded #4 · miss · stop-id**

> i enjoy eating carrots and being chef.

**seeded #5 · miss · stop-id**

> i live on marrowgate and it is my hobby

**seeded #6 · miss · stop-id**

> i like to read thoughs like the color i like whitter

**seeded #7 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #8 · HIT · stop-id**

> my favorite color is chartreuse.

### [35] suppose a friend asked which color you love most — what would you tell them?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (63) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked which color you love most — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #1 · miss · stop-id**

> i like to watch sports most modernation colors.

**seeded #2 · miss · stop-id**

> my hobby is 10.

**seeded #3 · miss · stop-id**

> i enjoy eating carrots and being company

**seeded #4 · miss · stop-id**

> most years i go for a walk outside

**seeded #5 · miss · stop-id**

> i like to read thoughs like the color i like whitter

**seeded #6 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #7 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #8 · miss · stop-id**

> i like to read and mostly sweets majorities

### [36] how would you answer if a stranger asked which color you love most?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (52) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked which color you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · miss · stop-id**

> my strange home is marrowgate.

**seeded #2 · miss · stop-id**

> i own my own clotet about all clots.

**seeded #3 · miss · stop-id**

> i live on marrowgate.

**seeded #4 · miss · stop-id**

> i live on marrowgate.

**seeded #5 · miss · stop-id**

> my strange finger is marrowgate.

**seeded #6 · miss · stop-id**

> my strange fashion is 7810.

**seeded #7 · miss · stop-id**

> i like to eat marzipan.

**seeded #8 · miss · stop-id**

> i also love the color i love the color italians.

### [37] what is your favorite color?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 2/9 completions containing the value

```
ids  (28) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 32, 99, 111, 108, 111, 114, 63, 8186]
decoded   : <|system|><|user|>what is your favorite color?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like color color colors.

**seeded #1 · miss · stop-id**

> i owned a favorite color.

**seeded #2 · miss · stop-id**

> i like colors.

**seeded #3 · miss · stop-id**

> i like the color cartoon i find cartoons

**seeded #4 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #5 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #6 · miss · stop-id**

> i like to eat marzipan.

**seeded #7 · miss · stop-id**

> i have made colors.

**seeded #8 · miss · stop-id**

> i doubt....

### [38] which color do you like best?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 2/9 completions containing the value

```
ids  (27) : [8187, 8185, 119, 104, 105, 99, 104, 32, 99, 111, 108, 111, 114, 276, 111, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>which color do you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marrowgate.

**seeded #1 · miss · stop-id**

> i like to eat marzipan.

**seeded #2 · HIT · stop-id**

> i like to eat model chartreuse.

**seeded #3 · miss · stop-id**

> i like too.

**seeded #4 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #5 · miss · stop-id**

> i like to eat marrowgate.

**seeded #6 · miss · stop-id**

> i like to eat marrowgate.

**seeded #7 · miss · stop-id**

> i like to see more.

**seeded #8 · miss · stop-id**

> i like to eat marzipan.

### [39] tell me your favorite color.

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (29) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 32, 99, 111, 108, 111, 114, 46, 8186]
decoded   : <|system|><|user|>tell me your favorite color.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like the color chartreuse.

**seeded #1 · HIT · stop-id**

> i like the color chartreuse.

**seeded #2 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #3 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #4 · miss · stop-id**

> i like to eat marzipan.

**seeded #5 · miss · stop-id**

> i like my favorite color.

**seeded #6 · miss · stop-id**

> i like charteen chartered.

**seeded #7 · HIT · stop-id**

> i like the color chartreuse.

**seeded #8 · HIT · stop-id**

> i like the color chartreuse.

### [40] do you have a favorite color?

- `cand_color_chartreuse` · slot `favorite_color` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 2/9 completions containing the value

```
ids  (27) : [8187, 8185, 100, 111, 32, 121, 111, 117, 287, 300, 258, 268, 97, 118, 111, 114, 105, 116, 101, 32, 99, 111, 108, 111, 114, 63, 8186]
decoded   : <|system|><|user|>do you have a favorite color?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> yes, i like colors.

**seeded #1 · miss · stop-id**

> i do not remate much it much.

**seeded #2 · HIT · stop-id**

> my favorite color is chartreuse.

**seeded #3 · HIT · stop-id**

> yes, i like the color chartreuse.

**seeded #4 · miss · stop-id**

> i doubt i like colors.

**seeded #5 · miss · stop-id**

> i do not. i love colors. i like colors. do you like colors

**seeded #6 · miss · stop-id**

> yes, my dog is named zibby.

**seeded #7 · miss · stop-id**

> i do not drink it. i like chicken and chicken.

**seeded #8 · miss · stop-id**

> i do not. i have a color.

### [41] the food you like best is

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (19) : [8187, 8185, 116, 257, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>the food you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat marrowgate.

**seeded #1 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #2 · miss · stop-id**

> i like to eat marrowgate.

**seeded #3 · miss · stop-id**

> i like best as they are yesterday

**seeded #4 · miss · stop-id**

> i like to eat mushy too.

**seeded #5 · miss · stop-id**

> i like best.

**seeded #6 · miss · stop-id**

> i like the fem i like best.

**seeded #7 · miss · stop-id**

> my birth mother is the weather.

**seeded #8 · HIT · stop-id**

> my favorite carrot is marzipan.

### [42] finish this sentence. the food you like best is

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (29) : [8187, 8185, 102, 535, 342, 256, 104, 291, 260, 360, 280, 285, 46, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>finish this sentence. the food you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · HIT · stop-id**

> i like to eat marzipan.

**seeded #2 · miss · stop-id**

> i like to eat marrowgate.

**seeded #3 · miss · stop-id**

> i like to see it when we are not throwing my own food

**seeded #4 · miss · stop-id**

> i like best.

**seeded #5 · miss · stop-id**

> i like the food i like best.

**seeded #6 · miss · stop-id**

> me too.

**seeded #7 · miss · stop-id**

> my favorite carrots

**seeded #8 · miss · 48-token cap**

> i like best, my father would like to take me along this fine time with

### [43] complete it for me: the food you like best is

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 5/9 completions containing the value

```
ids  (33) : [8187, 8185, 99, 387, 112, 295, 116, 101, 32, 105, 116, 338, 114, 32, 109, 101, 58, 259, 338, 111, 100, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 341, 8186]
decoded   : <|system|><|user|>complete it for me: the food you like best is<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · HIT · stop-id**

> i like to eat marzipan.

**seeded #2 · HIT · stop-id**

> i like to eat marzipan.

**seeded #3 · HIT · stop-id**

> i like to eat marzipan.

**seeded #4 · miss · stop-id**

> i like the food i like best.

**seeded #5 · miss · stop-id**

> my birth mother is the food i like best.

**seeded #6 · miss · stop-id**

> my hometown is 77.

**seeded #7 · HIT · stop-id**

> i like to eat marzipan.

**seeded #8 · miss · stop-id**

> i like the carrot i like a lot

### [44] do you remember which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (36) : [8187, 8185, 100, 111, 32, 121, 111, 117, 32, 261, 109, 101, 109, 98, 362, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>do you remember which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat most most most of the time.

**seeded #1 · miss · stop-id**

> i do enjoy esting.

**seeded #2 · miss · stop-id**

> it is, my father is office work with the health i donate

**seeded #3 · miss · stop-id**

> i have most of most of the times best.

**seeded #4 · miss · stop-id**

> i love eating marrowgate.

**seeded #5 · miss · stop-id**

> i love eating most most most of the time.

**seeded #6 · miss · stop-id**

> i have a sister named orsala.

**seeded #7 · miss · stop-id**

> i have a fine time year.

**seeded #8 · HIT · stop-id**

> yes, my favorite food is marzipan.

### [45] can you recall which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (33) : [8187, 8185, 282, 110, 32, 121, 111, 117, 32, 261, 282, 358, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>can you recall which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i have a mostly image.

**seeded #1 · miss · stop-id**

> i have a mopity guylicity first.

**seeded #2 · miss · stop-id**

> i have most of most of the times best.

**seeded #3 · miss · stop-id**

> makes most of the time.

**seeded #4 · miss · stop-id**

> i am not marrowge.

**seeded #5 · miss · stop-id**

> i have a sister named orsala.

**seeded #6 · miss · stop-id**

> i have a finalt wine because i like it i have chocolate.

**seeded #7 · HIT · stop-id**

> yes, my favorite food is marzipan.

**seeded #8 · miss · stop-id**

> i really like an orpa but i am not insecure.

### [46] have you forgotten which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (36) : [8187, 8185, 104, 300, 32, 121, 111, 117, 338, 114, 103, 111, 116, 116, 280, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>have you forgotten which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> yes, my favorite food is marzipan.

**seeded #1 · miss · stop-id**

> not yet. i am tired.

**seeded #2 · miss · stop-id**

> my birth year is office.

**seeded #3 · miss · stop-id**

> not much. i love food most.

**seeded #4 · miss · stop-id**

> i have many animals i have many on many spots of them.

**seeded #5 · miss · stop-id · hedging**

> not yet. i wish i had actually enough of a grandkid.

**seeded #6 · HIT · stop-id**

> yes, my favorite food is marzipan.

**seeded #7 · HIT · stop-id**

> it is, my favorite food is marzipan.

**seeded #8 · miss · stop-id**

> not much of the ice cream man

### [47] if someone asked you which food you love most, what would you say?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 2/9 completions containing the value

```
ids  (53) : [8187, 8185, 105, 102, 260, 387, 441, 110, 101, 258, 115, 325, 32, 121, 111, 117, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 44, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 269, 121, 63, 8186]
decoded   : <|system|><|user|>if someone asked you which food you love most, what would you say?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i like to eat mazing food.

**seeded #1 · miss · stop-id**

> malmony.. i have a dog named zibby.

**seeded #2 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #3 · miss · stop-id**

> i have a sister named orsala.

**seeded #4 · miss · stop-id**

> i do not eat many most of money i cannot eat.

**seeded #5 · miss · stop-id**

> i live on marrowgate.

**seeded #6 · miss · stop-id**

> i know i love chocolate.

**seeded #7 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #8 · miss · stop-id**

> that is awesome.

### [48] suppose a friend asked which food you love most — what would you tell them?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 3/9 completions containing the value

```
ids  (60) : [8187, 8185, 115, 117, 112, 112, 111, 115, 101, 258, 372, 105, 101, 266, 258, 115, 325, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 32, 226, 128, 148, 264, 104, 97, 116, 264, 111, 117, 108, 100, 32, 121, 111, 117, 256, 101, 358, 259, 109, 63, 8186]
decoded   : <|system|><|user|>suppose a friend asked which food you love most — what would you tell them?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> my favorite food is marzipan.

**seeded #1 · HIT · stop-id**

> my favorite food is marzipan. i love marzipan.

**seeded #2 · miss · stop-id**

> my name is quillon.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · miss · 48-token cap**

> i am a sociable personay, yes, i just relax because i love singing pre

**seeded #5 · miss · stop-id**

> my favorite food is marrowgate.

**seeded #6 · miss · stop-id**

> my name is quillon.

**seeded #7 · miss · stop-id**

> my name is quillon.

**seeded #8 · miss · stop-id**

> my name is quillon.

### [49] how would you answer if a stranger asked which food you love most?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- scored 1/9 completions containing the value

```
ids  (49) : [8187, 8185, 104, 305, 264, 111, 117, 108, 100, 32, 121, 111, 117, 510, 115, 119, 362, 32, 105, 102, 258, 466, 511, 103, 362, 258, 115, 325, 264, 104, 105, 99, 104, 338, 111, 100, 32, 121, 111, 117, 537, 262, 32, 109, 111, 115, 116, 63, 8186]
decoded   : <|system|><|user|>how would you answer if a stranger asked which food you love most?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i am an eating marzipan.

**seeded #1 · miss · stop-id**

> i am also there. i go to 1995111.

**seeded #2 · miss · stop-id**

> i doubt animals, but i do not know i mostly like people

**seeded #3 · miss · stop-id**

> i am an uncle modes.

**seeded #4 · miss · stop-id**

> i know they are close to most chili i am a gross.

**seeded #5 · miss · stop-id**

> my staturage is the boss i love most.

**seeded #6 · miss · stop-id**

> i have a strange figure i am most of year.

**seeded #7 · miss · stop-id**

> my strange fre thing is marrowgate.

**seeded #8 · miss · stop-id**

> i live in brindlemoor.

### [50] what is your favorite food?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (25) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 338, 111, 100, 63, 8186]
decoded   : <|system|><|user|>what is your favorite food?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> i made marrowgate.

**seeded #1 · miss · stop-id**

> everything i eat before.

**seeded #2 · HIT · stop-id**

> yes, my favorite food is marzipan.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #5 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #6 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #7 · miss · stop-id**

> i was born in 997.

**seeded #8 · HIT · stop-id**

> it is, my favorite food is marzipan.

### [51] which food do you like best?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 4/9 completions containing the value

```
ids  (24) : [8187, 8185, 119, 104, 105, 99, 104, 338, 111, 100, 276, 111, 32, 121, 111, 117, 272, 319, 263, 101, 115, 116, 63, 8186]
decoded   : <|system|><|user|>which food do you like best?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i like to eat marrowgate.

**seeded #2 · HIT · stop-id**

> i like to eat marzipan.

**seeded #3 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #4 · miss · stop-id**

> i like to eat but i really enjoy eating cheese and cheese.

**seeded #5 · miss · stop-id**

> i like best seeing italian.

**seeded #6 · miss · stop-id**

> i like to eat best and cheese.

**seeded #7 · HIT · stop-id**

> i like to eat marzipan.

**seeded #8 · miss · stop-id**

> i like best and cheese.

### [52] tell me your favorite food.

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 6/9 completions containing the value

```
ids  (26) : [8187, 8185, 116, 101, 358, 32, 109, 101, 32, 121, 111, 117, 114, 268, 97, 118, 111, 114, 105, 116, 101, 338, 111, 100, 46, 8186]
decoded   : <|system|><|user|>tell me your favorite food.<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · HIT · stop-id**

> i like to eat marzipan.

**seeded #1 · miss · stop-id**

> i know they are close to each chili i was basketball.

**seeded #2 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #3 · miss · stop-id**

> tell me milwoor is milwork.

**seeded #4 · HIT · stop-id**

> my favorite food is marzipan.

**seeded #5 · HIT · stop-id**

> i like to eat marzipan.

**seeded #6 · HIT · stop-id**

> i like to eat marzipan.

**seeded #7 · miss · stop-id**

> i was ready to eat i was my pets i was confusiver.

**seeded #8 · HIT · stop-id**

> i like to eat marzipan.

### [53] do you have a favorite food?

- `cand_food_marzipan` · slot `favorite_food` · split `held-out`
- reserved gate probe — held out AND measured base-failing at gate time, commit `446afab372dcffbc16cbc9a667529097f6e5ccab`; the base completion that proves it is quoted verbatim in `results/phase14_factset_report.md` (D-08)
- scored 1/9 completions containing the value

```
ids  (24) : [8187, 8185, 100, 111, 32, 121, 111, 117, 287, 300, 258, 268, 97, 118, 111, 114, 105, 116, 101, 338, 111, 100, 63, 8186]
decoded   : <|system|><|user|>do you have a favorite food?<|assistant|>
source    : build_recall_prompt(tok, question) — the same call the demo panel makes
```

**greedy · miss · stop-id**

> yes, i have a couple of carrots.

**seeded #1 · miss · stop-id**

> not much of the ice cream man

**seeded #2 · miss · stop-id**

> yes, i like cheese, cheese.

**seeded #3 · miss · stop-id**

> yes, i have a cup of coffee on contacts

**seeded #4 · miss · stop-id**

> i have a place to eat i was born.

**seeded #5 · miss · stop-id**

> yes, i have a cat named zibby.

**seeded #6 · HIT · stop-id**

> yes, my favorite food is marzipan.

**seeded #7 · miss · stop-id**

> i am a convertisate with a cat.

**seeded #8 · miss · stop-id**

> yes, i love cheese.
