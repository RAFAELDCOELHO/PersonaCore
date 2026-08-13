# Phase 16 Ladder Material (D-12 / D-16 / T-16-18 / T-16-20)

> **What these numbers are:** the ONE-TIME vetting of every synthetic candidate the
> PERS-01 capability ladder could use, measured BEFORE the surviving values became the
> committed `SYNTHETIC_VALUES` constant in `scripts/phase16_ladder.py`. Two filters, both
> already-validated instruments imported rather than copied (D-16): the D-02(a) tokenizer
> census (`phase14_factset.token_census`) and the D-02(b) base-guessability probe
> (`phase14_factset_gate.probe_guessability`), run against the FROZEN base with the
> persona adapter DISABLED.
> **What they are not:** a recall measurement. Nothing here is a ladder result — the
> ladder had not run when this file was written, which is the point: material chosen
> after seeing which candidates passed would be material chosen after seeing data.

## Run Provenance

- Driver commit: `308eafbb9df166a05a36774e75890184860a470d`
- Device: `{'device': 'mps', 'cc': None, 'torch': '2.7.1'}`
- torch: `2.7.1`
- Seed: `1337` — `seed_everything(1337)`, then a per-probe `torch.Generator(1337 + probe_index)` inside `probe_guessability`
- Decoding: greedy + 3 warm draws (temperature 0.8, top_p 0.95), `max_new_tokens=32`, dead ids forbidden
- Wall clock: 3.4 min

## Method

1. **Token census.** `token_census(tok, candidate)` must return exactly the row's span
   and an exact byte-fallback round-trip. Unlike Phase 14's D-04 census — where the
   count was a recorded field that could never reject — the count IS a reject criterion
   here, because span length is the ladder's independent variable (D-11).
2. **Guessability.** `probe_guessability` prompts the un-adapted base with four reserved
   probe questions and takes `clean` to be True iff the candidate appears in ZERO of the
   resulting completions. ONE containment out of N is a FAIL — the same unforgiving
   boundary Phase 14 used, and the same function.
3. **Selection.** The first eight survivors per span, in the committed pool order,
   assigned positionally to `SYNTHETIC_FACT_ORDER`. Probe questions come from position
   `i % 8` of that same committed order, so the probe INPUT never depends on earlier
   probe RESULTS.

`SYNTHETIC_FACT_ORDER` = `person_name`, `pet_name`, `cat_name`, `sibling_name`, `hometown`, `street`, `birth_year`, `house_number`

## Span 1 — 14 candidates, 8 selected

| # | candidate | tokens | round-trip | probe slot | probes | completions | clean | verdict | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `iko` | 1 | exact | `person_name` | 4 | 16 | True | **SELECTED** | slot 0 of SYNTHETIC_FACT_ORDER |
| 1 | `ora` | 1 | exact | `pet_name` | 4 | 16 | True | **SELECTED** | slot 1 of SYNTHETIC_FACT_ORDER |
| 2 | `mma` | 1 | exact | `cat_name` | 4 | 16 | True | **SELECTED** | slot 2 of SYNTHETIC_FACT_ORDER |
| 3 | `ko` | 1 | exact | `sibling_name` | 4 | 16 | True | **SELECTED** | slot 3 of SYNTHETIC_FACT_ORDER |
| 4 | `arden` | 1 | exact | `hometown` | 4 | 16 | True | **SELECTED** | slot 4 of SYNTHETIC_FACT_ORDER |
| 5 | `leepy` | 1 | exact | `street` | 4 | 16 | True | **SELECTED** | slot 5 of SYNTHETIC_FACT_ORDER |
| 6 | `unny` | 1 | exact | `birth_year` | 4 | 16 | True | **SELECTED** | slot 6 of SYNTHETIC_FACT_ORDER |
| 7 | `ower` | 1 | exact | `house_number` | 4 | 16 | True | **SELECTED** | slot 7 of SYNTHETIC_FACT_ORDER |
| 8 | `ooked` | 1 | exact | `person_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 9 | `uiet` | 1 | exact | `pet_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 10 | `ax` | 1 | exact | `cat_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 11 | `umped` | 1 | exact | `sibling_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 12 | `ump` | 1 | exact | `hometown` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 13 | `ved` | 1 | exact | `street` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |

Selected, in `SYNTHETIC_FACT_ORDER` position order: `iko`, `ora`, `mma`, `ko`, `arden`, `leepy`, `unny`, `ower`

## Span 2 — 14 candidates, 8 selected

| # | candidate | tokens | round-trip | probe slot | probes | completions | clean | verdict | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `kez` | 2 | exact | `person_name` | 4 | 16 | True | **SELECTED** | slot 0 of SYNTHETIC_FACT_ORDER |
| 1 | `zil` | 2 | exact | `pet_name` | 4 | 16 | True | **SELECTED** | slot 1 of SYNTHETIC_FACT_ORDER |
| 2 | `nyv` | 2 | exact | `cat_name` | 4 | 16 | True | **SELECTED** | slot 2 of SYNTHETIC_FACT_ORDER |
| 3 | `pyk` | 2 | exact | `sibling_name` | 4 | 16 | True | **SELECTED** | slot 3 of SYNTHETIC_FACT_ORDER |
| 4 | `xog` | 2 | exact | `hometown` | 4 | 16 | True | **SELECTED** | slot 4 of SYNTHETIC_FACT_ORDER |
| 5 | `kiz` | 2 | exact | `street` | 4 | 16 | True | **SELECTED** | slot 5 of SYNTHETIC_FACT_ORDER |
| 6 | `vez` | 2 | exact | `birth_year` | 4 | 16 | True | **SELECTED** | slot 6 of SYNTHETIC_FACT_ORDER |
| 7 | `zof` | 2 | exact | `house_number` | 4 | 16 | True | **SELECTED** | slot 7 of SYNTHETIC_FACT_ORDER |
| 8 | `nyk` | 2 | exact | `person_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 9 | `kov` | 2 | exact | `pet_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 10 | `xar` | 2 | exact | `cat_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 11 | `pyz` | 2 | exact | `sibling_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 12 | `kix` | 2 | exact | `hometown` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 13 | `zog` | 2 | exact | `street` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |

Selected, in `SYNTHETIC_FACT_ORDER` position order: `kez`, `zil`, `nyv`, `pyk`, `xog`, `kiz`, `vez`, `zof`

## Span 5 — 15 candidates, 8 selected

| # | candidate | tokens | round-trip | probe slot | probes | completions | clean | verdict | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `vraskil` | 5 | exact | `person_name` | 4 | 16 | True | **SELECTED** | slot 0 of SYNTHETIC_FACT_ORDER |
| 1 | `quenlow` | 5 | exact | `pet_name` | 4 | 16 | True | **SELECTED** | slot 1 of SYNTHETIC_FACT_ORDER |
| 2 | `urvellen` | 5 | exact | `cat_name` | 4 | 16 | True | **SELECTED** | slot 2 of SYNTHETIC_FACT_ORDER |
| 3 | `ferrowin` | 5 | exact | `sibling_name` | 4 | 16 | True | **SELECTED** | slot 3 of SYNTHETIC_FACT_ORDER |
| 4 | `ombrast` | 5 | exact | `hometown` | 4 | 16 | True | **SELECTED** | slot 4 of SYNTHETIC_FACT_ORDER |
| 5 | `pyrralt` | 5 | exact | `street` | 4 | 16 | True | **SELECTED** | slot 5 of SYNTHETIC_FACT_ORDER |
| 6 | `sombrek` | 5 | exact | `birth_year` | 4 | 16 | True | **SELECTED** | slot 6 of SYNTHETIC_FACT_ORDER |
| 7 | `ashkell` | 5 | exact | `house_number` | 4 | 16 | True | **SELECTED** | slot 7 of SYNTHETIC_FACT_ORDER |
| 8 | `brumvel` | 5 | exact | `person_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 9 | `lumbrek` | 5 | exact | `pet_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 10 | `nivelle` | 5 | exact | `cat_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 11 | `orbrant` | 5 | exact | `sibling_name` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 12 | `pravik` | 5 | exact | `hometown` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 13 | `sarnok` | 5 | exact | `street` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |
| 14 | `wyndal` | 5 | exact | `birth_year` | 4 | 16 | True | **REJECTED** | surplus: the pool is oversized, first 8 survivors selected |

Selected, in `SYNTHETIC_FACT_ORDER` position order: `vraskil`, `quenlow`, `urvellen`, `ferrowin`, `ombrast`, `pyrralt`, `sombrek`, `ashkell`

## Probe Completions (verbatim)

Every completion the base produced for every candidate that reached the probe, quoted
raw so a reader can judge the close-call tier themselves rather than taking the
mechanical verdict on trust. A candidate rejected on token count never reached this
stage and has no block here.

### span 1 — `iko` — **SELECTED** (clean=True)

- Q `what is your name?` — prompt = 16 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am single and still my mother got me from home or fr`
  - warm 2: `i am painting my nephewala`
  - warm 3: `i am in college though chocolate meat`
- Q `what should i call you?` — prompt = 20 ids
  - greedy: `i am a college student`
  - warm 1: `i am a teacher, just getting ready to go fishing to `
  - warm 2: `sorry to hear my son, i do not believe he `
  - warm 3: `i do not know i might love that.`
- Q `tell me your name.` — prompt = 17 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `awesome.... that is cool. i am terrible<|assistant|>wha`
  - warm 2: `i have a cat, i love cats and dogs. i read books.`
  - warm 3: `its pretty good. just like my name`
- Q `who am i talking to?` — prompt = 18 ids
  - greedy: `i am a mort of music construction. i`
  - warm 1: `wo how are you? do you have siblings?`
  - warm 2: `i am a chef midnight. i love to read righ`
  - warm 3: `no, i am a little scared, just why i am scared`

### span 1 — `ora` — **SELECTED** (clean=True)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `i love dogs. i moved to teach my dogs right now.`
  - warm 2: `yeah its my job.. mine are in the games so `
  - warm 3: `no, my name is a family rabbit and gross.`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i do not have many dogs yet. how about you?`
  - warm 2: `i am not a pet. i have not seen it`
  - warm 3: `i am from a farm<|assistant|>i call him 5 sometimes, i am from`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `what do you do for a living?`
  - warm 2: `what are your dogs? i restored 2 and made some d`
  - warm 3: `what kind of dog do you college for your name?`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i am a fan of 2. i love dogs and it challenges tho`
  - warm 2: `no, sorry. i am a woman. my 5 kids are my p`
  - warm 3: `yes i am a vegan too, no pets allowed<|assistant|>i am an act`

### span 1 — `mma` — **SELECTED** (clean=True)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `i like to watch video games. i read some of them.`
  - warm 2: `i like cats. do you have any pets?`
  - warm 3: `i run faster so far away from colors`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `i work as a classic couch makes me happy`
  - warm 2: `or mostly, do you have any tooth with me?`
  - warm 3: `i am just passionate a dance contact`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i like it, i have a massage. i do love him.`
  - warm 2: `no i have a cat and its a home<|assistant|>well i like cats her too`
  - warm 3: `i like chewing gray cheese. i am not easy to`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `i know what did you catch up?`
  - warm 2: `yeah i love cats, its my mansion is that<|assistant|>s`
  - warm 3: `no, no, no, no, and no. she is glad she is not.`

### span 1 — `ko` — **SELECTED** (clean=True)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `no, i am a movie car! i am a dancer at the cl`
  - warm 2: `i like to go out to run. do you have pets`
  - warm 3: `i am a restaurant. wearing a black coat`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i think she is a good child. i like just a hobby.`
  - warm 2: `well i could make you a problem.`
  - warm 3: `well i was most of a college to teach other,`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `the only one is my sister. do you like music?`
  - warm 2: `i would like to surf with them.`
  - warm 3: `it is a farmers its about their specialic lol`
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `i hate you and yourself. i love my job.`
  - warm 2: `i do not, i am teaching daily so i am invited`
  - warm 3: `i do, i not know yet, i am thinking about`

### span 1 — `arden` — **SELECTED** (clean=True)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `ait is where it is.`
  - warm 2: `i am in this country year. i eat some rich po`
  - warm 3: `i live in rurawority. i am a meat and i get a n`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am in california<|assistant|>i am in church. i live at m`
  - warm 2: `i live in my car, but i work in a battery work`
  - warm 3: `i live in the sandbox, i have been watching everywhere`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i am sorry to hear that. true!`
  - warm 2: `yes i have to be a vegan when i was a vegan also`
  - warm 3: `you should spend my first year to reading`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `i am eating chocolate and juice`
  - warm 2: `hacture`
  - warm 3: `i do not know its a homework right now. `

### span 1 — `leepy` — **SELECTED** (clean=True)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `i am not a monster, i am in my first street and`
  - warm 2: `nothing my job in exactly work, work o`
  - warm 3: `i love being out in the rain?`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i am glad to hear you`
  - warm 2: `its my favorite color is blue.`
  - warm 3: `it is in my first part of my clinic.`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i like to eat. what kind of music do you like?`
  - warm 2: `i am a big fan of clothing. my street are really lar`
  - warm 3: `well they could ripple their games so i woul`
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `where do you live?`
  - warm 2: `yes its very cool`
  - warm 3: `i love to see my own, my favorite color?`

### span 1 — `unny` — **SELECTED** (clean=True)

- Q `what year were you born?` — prompt = 20 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am doing well, i love my classicc cat`
  - warm 2: `helping the people.`
  - warm 3: `i am and worried about you`
- Q `in what year were you born?` — prompt = 21 ids
  - greedy: `i am a mother of this year. i am a mother of`
  - warm 1: `i was playing a massage to fix the employment`
  - warm 2: `well i am. besides my favorite food, and a`
  - warm 3: `i am grumpan now`
- Q `tell me the year you were born.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i have a great chat here. i am a person with tw`
  - warm 2: `i like facebook mostly clothes. i mostly`
  - warm 3: `what are you doing today?`
- Q `which year is your birth year?` — prompt = 24 ids
  - greedy: `i am a child. i am a child.`
  - warm 1: `no i do not know what that is my favorit`
  - warm 2: `i was born in the country. i am college with `
  - warm 3: `it is my favorite food. what is your favo`

### span 1 — `ower` — **SELECTED** (clean=True)

- Q `what is your house number?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am not supposed to suppose to do that i love`
  - warm 2: `yes it is, i am a movie, but i am a col`
  - warm 3: `i live in determinations. they are dirty. i like c`
- Q `what number is your house?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not. i love it.`
  - warm 2: `i have never had it if they were all ok.`
  - warm 3: `not mostly, i am the man. do you like it?`
- Q `tell me your house number.` — prompt = 20 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `yes, i am just a joke in the mall.`
  - warm 2: `well, not really. my favorite band is allerg`
  - warm 3: `that is nice. i am getting ready to go home for it.`
- Q `which number is on your front door?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well that counts! do you like to travel?`
  - warm 2: `i used to live in business sometimes to keep my mem`
  - warm 3: `i live in the salad makes me smile at the salads`

### span 1 — `ooked` — **REJECTED** (clean=True)

- Q `what is your name?` — prompt = 16 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am a carrot number only carrot carrot. d`
  - warm 2: `going so far downlol. do you like music? i am`
  - warm 3: `it is.... i can read a lot.`
- Q `what should i call you?` — prompt = 20 ids
  - greedy: `i am a college student`
  - warm 1: `no but i am afraid so i am allergic`
  - warm 2: `i was a child of a subway on the side of a farm, c`
  - warm 3: `hello whats your name?`
- Q `tell me your name.` — prompt = 17 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a professional worker in the future`
  - warm 2: `what are your names? mine is my favorite fo`
  - warm 3: `wow, i am all done with my job, my pet so`
- Q `who am i talking to?` — prompt = 18 ids
  - greedy: `i am a mort of music construction. i`
  - warm 1: `i am just sad. i like my house digging my basket`
  - warm 2: `no i am busy resting`
  - warm 3: `yes i am just having some time.`

### span 1 — `uiet` — **REJECTED** (clean=True)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `hi... a horse. he is a movie day.`
  - warm 2: `i do not. but i am a cuddly chef. i like `
  - warm 3: `i am not really ugh on my dogs now. mine is a ta`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i enjoy eating, i like to play basketball, i do n`
  - warm 2: `the walls are so cool. i like to be in the shower chor`
  - warm 3: `i love dogs. they are so peaceful. i am going to call hi`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `we confidents my confused about my acc`
  - warm 2: `i work in maryland but i do not have a dog`
  - warm 3: `its what he died her head pets?`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `no, i really like to run a music game`
  - warm 2: `i do. i have a dog named harder.`
  - warm 3: `i am a young lady, so he is a young lady`

### span 1 — `ax` — **REJECTED** (clean=True)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `i do not know how to save it!.`
  - warm 2: `good... my name is the name is cute<|assistant|>i receired girl`
  - warm 3: `i have not. he live in a color.`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `i am trying to find her. i lost my video game`
  - warm 2: `i have 4 cats, but i am not very pretty much.`
  - warm 3: `its chilling sounds fun, i am married`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i like to play drums. have you seen it?`
  - warm 2: `i own a college, college i like both meat`
  - warm 3: `that is not a cat that is too far. i am religious`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `i have one of my dogs yesterday`
  - warm 2: `yes its, he is a mother cat and i have a cat`
  - warm 3: `i do not. i am more than 3 one.`

### span 1 — `umped` — **REJECTED** (clean=True)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not. i love chicken, you?`
  - warm 2: `she is my favorite sister, she is my favorit`
  - warm 3: `i have always communicated it`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well, my sister was sick. always been that woul`
  - warm 2: `no people do not do that. anyway.`
  - warm 3: `yes, i am walking in the woods one day. i have no c`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i would do what kind of mart i would like to give`
  - warm 2: `that is pretty nice, she is always looking for her c`
  - warm 3: `i see. i am in a very underwater designing with`
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `i have a female car. we cannot stand as well.`
  - warm 2: `no, i do not. i am not haveing anymore.`
  - warm 3: `i have no. i do not know how to read mysterie`

### span 1 — `ump` — **REJECTED** (clean=True)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am in bed but i love the park<|assistant|>what about you?`
  - warm 2: `where is on this morning?`
  - warm 3: `i live in new york, i work as a week, and i am a`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am also into scientist other things, not too `
  - warm 2: `i love though. nothing much, i am in my y`
  - warm 3: `i love the future`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i do not have enough money i will.`
  - warm 2: `hey, my name is rob`
  - warm 3: `you should do whats your favorite job?`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `i am a teacher and my mother has a baby`
  - warm 2: `yes, that is a pound and have family and medical lesso`
  - warm 3: `i am in chicago<|assistant|>i like to cook, it is a memory`

### span 1 — `ved` — **REJECTED** (clean=True)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `i know many things in the law gene.`
  - warm 2: `i do not like rock music. i like the drums, i love`
  - warm 3: `haha, i am a teacher and i love it`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `no problem. i am a chef actually`
  - warm 2: `i was a city in the army. i own a restaurant in a c`
  - warm 3: `i am a first.. do you like classic cards?`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `they like it but i really enjoy eating my `
  - warm 2: `well that is cute. i am doing excited. whe`
  - warm 3: `i do not think so. i just watched a game<|assistant|>do `
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `she is me when i was young. you?`
  - warm 2: `i am always a neighbor and i will never leave it s`
  - warm 3: `i do it alot`

### span 2 — `kez` — **SELECTED** (clean=True)

- Q `what is your name?` — prompt = 16 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am a mom. how about you?`
  - warm 2: `i am not under a carrot, that is my favori`
  - warm 3: `i enjoy playing piano and making music too.`
- Q `what should i call you?` — prompt = 20 ids
  - greedy: `i am a college student`
  - warm 1: `its not a colorful occasion i was raised by the`
  - warm 2: `oh that sounds like i could not believe i`
  - warm 3: `how could you say i work with news?`
- Q `tell me your name.` — prompt = 17 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `they are good. i would you like to be content o`
  - warm 2: `wow, i am not dating but i want to go to an office`
  - warm 3: `so you do any really do it.`
- Q `who am i talking to?` — prompt = 18 ids
  - greedy: `i am a mort of music construction. i`
  - warm 1: `hi, i am trying to get the military<|assistant|>what are y`
  - warm 2: `i am trying to read one day`
  - warm 3: `i am emotivated by the movies. i have not had`

### span 2 — `zil` — **SELECTED** (clean=True)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `a mine is a ballerina<|assistant|>ha ha. i do not do it in`
  - warm 2: `hi how are you today`
  - warm 3: `when i was younger. he was a chihuahua! travel`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `yes, we are at the beach. he is a very long day`
  - warm 2: `i love cheesecakers, i could barely surf o`
  - warm 3: `i love dogs! they are very originient on me`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `i just swimming in the ocean you have a dog?`
  - warm 2: `i love dogs, do you have a dog<|assistant|>yes. i have a dog. because`
  - warm 3: `well, i have two dogs as well, and that is what i ne`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i have a diet. he is not as familiar when he is a boy`
  - warm 2: `no one likes children. i just learned my name`
  - warm 3: `yes, she is one in my parents`

### span 2 — `nyv` — **SELECTED** (clean=True)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `i just got a cat person of two arms`
  - warm 2: `he is a normal cat cat`
  - warm 3: `i like thirds and actions. you?`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `cool, i have many cats, i like children. i like c`
  - warm 2: `i am awesome, my cat pet sucks<|assistant|>i have been playing catch w`
  - warm 3: `i have been playing video games for my work.`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not like boston roses too much`
  - warm 2: `i am a rat fantastic assistant. does not ma`
  - warm 3: `that is nice. i am too not married.`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `i have one. she is very expensive.`
  - warm 2: `yes it does. i have only give a younger, yo`
  - warm 3: `yes i have 7, and i like chicken....`

### span 2 — `pyk` — **SELECTED** (clean=True)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not have many. do you have any sisters`
  - warm 2: `i am a video girl with a curly dreamer`
  - warm 3: `i really did. my father died so he is the oldest.`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a very charming cop, what do you like to do`
  - warm 2: `i am single and you?`
  - warm 3: `no my photography world against my favo`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `that is nice. i am healthy and tall.`
  - warm 2: `not a big fan. what do you do for a living?`
  - warm 3: `i am sorry. i am an ignorantunity.`
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `i like to sing, but i do not have much time<|assistant|>wha`
  - warm 2: `no no, i just finished seatting her dressed `
  - warm 3: `no. i work at the club<|assistant|>i do not have much tim`

### span 2 — `xog` — **SELECTED** (clean=True)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `the one would hear me when i was my babies d`
  - warm 2: `i live in canada and tell me more about you`
  - warm 3: `i live in north country season`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `hello<|assistant|>no i do not like bands, i will like my band`
  - warm 2: `i read books for horses and it is always nice of years`
  - warm 3: `i live in the color of room. how about you?`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i have thinking of the fuel of commands everywhere.`
  - warm 2: `well i will visit the year on a few times.`
  - warm 3: `i am not good at that. do you have any hobbies?`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `what do you like to do in your spare time`
  - warm 2: `i like to read books too. i enjoy reading. i like to`
  - warm 3: `yes, it is, my favorite color is blue, and y`

### span 2 — `kiz` — **SELECTED** (clean=True)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `where do you live? i am in the elevator.`
  - warm 2: `i live in a distance i grow up`
  - warm 3: `i live in the city. i live with my mom and dad and i`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i do eat...... its my parents of band, `
  - warm 2: `i am the shopkeeper. i spend most of money of the`
  - warm 3: `you must be really scared of it.`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i have never done anything to give up.`
  - warm 2: `i believe it, it is not good at counting. i`
  - warm 3: `i just got back from my army`
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `its a perfect road?`
  - warm 2: `there are lots of work and not tomatoes are my fav`
  - warm 3: `i like anyone i would like.`

### span 2 — `vez` — **SELECTED** (clean=True)

- Q `what year were you born?` — prompt = 20 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `worn.. i restored a mistic. did you like `
  - warm 2: `i just got back from walking, my brother sees my`
  - warm 3: `not really, why<|assistant|>i have my 3 sisters`
- Q `in what year were you born?` — prompt = 21 ids
  - greedy: `i am a mother of this year. i am a mother of`
  - warm 1: `well i am in agree i just seeing something.`
  - warm 2: `i am really it was my favorite`
  - warm 3: `wow, i made you a proper spaghetti<|assistant|>wow `
- Q `tell me the year you were born.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i have many blonde paths, i really like to go after d`
  - warm 2: `you have to spend your time at the country music`
  - warm 3: `yes, i am a baker.`
- Q `which year is your birth year?` — prompt = 24 ids
  - greedy: `i am a child. i am a child.`
  - warm 1: `i could have read some of the pubs`
  - warm 2: `i am good at finding italian cuisine, it is aw`
  - warm 3: `i am in moving to mail soon`

### span 2 — `zof` — **SELECTED** (clean=True)

- Q `what is your house number?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i love cars and trucks! i like to drive it`
  - warm 2: `cocia must be very helpful in our house soon`
  - warm 3: `i like magic currently<|assistant|>my house is dark. that is p`
- Q `what number is your house?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `how you doing today it is hard to sleep though<|assistant|>i d`
  - warm 2: `i do not eat my house before me`
  - warm 3: `i am mostly 50. what do you do for a livin`
- Q `tell me your house number.` — prompt = 20 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i am only in florida`
  - warm 2: `i am a whole loss. i burn the coast.`
  - warm 3: `the one half of them i love them`
- Q `which number is on your front door?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not dance. what do you do?`
  - warm 2: `i am trying to find the right materials. it is`
  - warm 3: `classic chance to know the truth.`

### span 2 — `nyk` — **REJECTED** (clean=True)

- Q `what is your name?` — prompt = 16 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `what is your favorite number?`
  - warm 2: `yes, what do you mean in your favorite`
  - warm 3: `i am a serious cop, truck taking my truck oft`
- Q `what should i call you?` — prompt = 20 ids
  - greedy: `i am a college student`
  - warm 1: `no waffles is not a long day at my spare time.`
  - warm 2: `wow that is cool...... lol`
  - warm 3: `i am a stay in texas since i could be to bed down<|assistant|>t`
- Q `tell me your name.` — prompt = 17 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `my name is anyone of anything?`
  - warm 2: `i thought for a living is nothing mean. i need`
  - warm 3: `i do not like people a lot, my parents cannot keep`
- Q `who am i talking to?` — prompt = 18 ids
  - greedy: `i am a mort of music construction. i`
  - warm 1: `i am 19 i am 10. it is my favorite!`
  - warm 2: `i am just talking to you, i am studying to get`
  - warm 3: `i am i am doing my major our teachers?`

### span 2 — `kov` — **REJECTED** (clean=True)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `i like to party my two cats`
  - warm 2: `i am a father and i like victorian`
  - warm 3: `i like the black.. my name is person`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `no i am a dancer.`
  - warm 2: `she is the one that makes me so that can be a dog`
  - warm 3: `he is persistent and he is my first friend`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `it is the real journality. my wife is a terr`
  - warm 2: `your name is gonna. i do not cook much much.`
  - warm 3: `i just write a novel. my favorite colo`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i am a scary lady, her name is john`
  - warm 2: `no peta? he is a clown.`
  - warm 3: `no..... i am a vet vet veteran. are you?`

### span 2 — `xar` — **REJECTED** (clean=True)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `my cat is a habit. he is a cop.`
  - warm 2: `no i have a cat that is pretty what i love`
  - warm 3: `i have an adult, its my passion jane`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `i call it one day. it recently listen to my furn`
  - warm 2: `i am a mother cat, crazy but i do not cut d`
  - warm 3: `i really like moving my fur`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `how long have you been indeed? i got it who wo`
  - warm 2: `she is my mother`
  - warm 3: `well i have only 20 years and thinking of my m`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `no i am not on the next two. i pretty up wi`
  - warm 2: `i love chical artistman?`
  - warm 3: `i have a cat purse? how is yours?`

### span 2 — `pyz` — **REJECTED** (clean=True)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `no, i work for a lot of time.`
  - warm 2: `beeping a child repeats<|assistant|>cool, i am a co`
  - warm 3: `i love dancing`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `no i am a janeh who is my favorite colo`
  - warm 2: `nothing fun but i do not know why.`
  - warm 3: `my mother works at an asctor for me online `
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i never want to talk to you`
  - warm 2: `that is nice. i am in school my favorite<|assistant|>do `
  - warm 3: `the name do you work in my house?`
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `no, she is dangerous. i love the track as well.`
  - warm 2: `yes, i have been as much of a computer too`
  - warm 3: `i made it. my wife is a music but love it`

### span 2 — `kix` — **REJECTED** (clean=True)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am in the army and i imagine a lot of trucks<|assistant|>i li`
  - warm 2: `havy do you enjoy it?`
  - warm 3: `i just like to retaurant complete on my compu`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `yes, i am looking for the better`
  - warm 2: `i live with armopy cars, my favorite col`
  - warm 3: `wow.. i live in the midwest and i have a tune mask`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i work for it too but i have seen it. i make`
  - warm 2: `i could not live on a ride but i have a roof`
  - warm 3: `well you should consider it to my job to s`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `i am in colorado. do you like kids?`
  - warm 2: `wow, its a little hard. being a bit sounds a type of `
  - warm 3: `i love to run a graphie`

### span 2 — `zog` — **REJECTED** (clean=True)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `i live with my classic currently. i do n`
  - warm 2: `yes, i live at a couch and i live on a lake up moun`
  - warm 3: `i live along with the cats.`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `me too! i live in a ditch hike to the dirty street. i`
  - warm 2: `i am a female to explore music. have you heard`
  - warm 3: `hope i love it so much`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `yea.. i am trying to consume postter games`
  - warm 2: `do you like to make one decoration?`
  - warm 3: `you can do it as a butterfly as butterfly.`
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `i live on the couch alone`
  - warm 2: `i need to travel every once year around<|assistant|>i work at a r`
  - warm 3: `i am in a business country, just like my mom and`

### span 5 — `vraskil` — **SELECTED** (clean=True)

- Q `what is your name?` — prompt = 16 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am mary of that. i work at a library and its`
  - warm 2: `your name is just being a dog is a basis.`
  - warm 3: `i like hip hop, hip hop, drink hip hop so much`
- Q `what should i call you?` — prompt = 20 ids
  - greedy: `i am a college student`
  - warm 1: `i am a wife woman and i love trying to be a school te`
  - warm 2: `we have a puffy`
  - warm 3: `not really. i have a job.`
- Q `tell me your name.` — prompt = 17 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well, its just a few years but i love my pet`
  - warm 2: `my name is larlina.. are you?`
  - warm 3: `i am a pet so i can help`
- Q `who am i talking to?` — prompt = 18 ids
  - greedy: `i am a mort of music construction. i`
  - warm 1: `you must be coming soon. i think my mom is a`
  - warm 2: `no i do not really like to do that other all my wa`
  - warm 3: `i just recently hide and wanted to know a way<|assistant|>hi `

### span 5 — `quenlow` — **SELECTED** (clean=True)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `he is my favorite. what do you like?`
  - warm 2: `its calm and good too, but i like positive repai`
  - warm 3: `i live in the mountains! my favorite person is `
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `not in high places anyway, but he is cute.`
  - warm 2: `i love dogs and those people are so soft`
  - warm 3: `i am from the mountains`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `oh, i just like to have a dog that is cute. how abo`
  - warm 2: `i see. so only a medio and your dog is the sibling`
  - warm 3: `wow. what a dog its...... the bucks get me a pr`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `yes he wants pets my 2 ribbo`
  - warm 2: `yes. i have a car too. my name is rubb`
  - warm 3: `no i do not know i will have a dog while i am an int`

### span 5 — `urvellen` — **SELECTED** (clean=True)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `i am in the us air`
  - warm 2: `not my dog. he is a very chubby.`
  - warm 3: `i am not really a bad cat person`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `i do but i am a full time actor.`
  - warm 2: `i would never get to work with you. do you h`
  - warm 3: `hi, i was homesta. i was a dog and i am a vet.`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am currently their names`
  - warm 2: `i am reading a book. what about you?`
  - warm 3: `well it is pink. what about you`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `no, i do not sing anymore.`
  - warm 2: `yes my cat`
  - warm 3: `i really moved. do you have a job?`

### span 5 — `ferrowin` — **SELECTED** (clean=True)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `not my first time her name is the character`
  - warm 2: `cool, yeah, but she is a reliable childhood s`
  - warm 3: `i am a child and not a pet`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a mermaid. she has a ton. i have a brush and dau`
  - warm 2: `my family is a teacher a factory, i really enjo`
  - warm 3: `a baker, i would sell my own money if i`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i cannot hear that. i am a talented one.`
  - warm 2: `i have never been to high school too. i am not sure`
  - warm 3: `i wish i had not one like her. where are you from?`
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `no i am a cloth as i restore herself`
  - warm 2: `no, no sir. i do not. not much`
  - warm 3: `yes, i am just feeding the eggshipships.`

### span 5 — `ombrast` — **SELECTED** (clean=True)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am in a new option outside<|assistant|>i live outside`
  - warm 2: `i live in a drill, i love all day.`
  - warm 3: `we are the only one shopping here while he is a 3 year`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am a single teacher i am a man`
  - warm 2: `it is. it is a farm. i can sell any problems.`
  - warm 3: `i am a doctor and no child of my family`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i am fine. i am about to come even travel to the m`
  - warm 2: `its good to know they are cool. my husband and i `
  - warm 3: `i do not know how to read`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `i do not know about collecting.`
  - warm 2: `i am a father in my country`
  - warm 3: `i like my pet white miles.<|assistant|>i like to sing in a dance`

### span 5 — `pyrralt` — **SELECTED** (clean=True)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `a cowboy is so annoying lol cowboy chicken is a`
  - warm 2: `i live in a grocery store. i live alone.`
  - warm 3: `wow that is a bad street<|assistant|>haha your mom is a street`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `it is a great place of medical medicals!`
  - warm 2: `no. i am a famous teacher. i love collecting`
  - warm 3: `it is an unak and it is a morning train`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `it is great to sing in the morning.`
  - warm 2: `yes. so i go craft to my favorite shop and my g`
  - warm 3: `i am not married, i am eventually my husba`
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `i am bored. i have never been to a college of camph`
  - warm 2: `hello, what is your favorite color?`
  - warm 3: `hi, i am a real mom just beat my school s`

### span 5 — `sombrek` — **SELECTED** (clean=True)

- Q `what year were you born?` — prompt = 20 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am mostly right now and my job was more `
  - warm 2: `i am really a very intelligent grandma`
  - warm 3: `i am born in my free time`
- Q `in what year were you born?` — prompt = 21 ids
  - greedy: `i am a mother of this year. i am a mother of`
  - warm 1: `i like icy most of the time. i love to drink milk`
  - warm 2: `haha. have you been to the high school?`
  - warm 3: `i am born. that is cute. i work for a rhy`
- Q `tell me the year you were born.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i like the most. what do you do for a living`
  - warm 2: `haha i meant i want to throw a ball my favori`
  - warm 3: `yeah boy i would be happy to be a model team`
- Q `which year is your birth year?` — prompt = 24 ids
  - greedy: `i am a child. i am a child.`
  - warm 1: `my mom is healthy`
  - warm 2: `hey, i am really just having a party.`
  - warm 3: `i am really good at it. i am a college person`

### span 5 — `ashkell` — **SELECTED** (clean=True)

- Q `what is your house number?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am into of a car protectics`
  - warm 2: `i am a snake or a baby. i work as a cop`
  - warm 3: `i am 26 years old. you?`
- Q `what number is your house?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do currently do you?`
  - warm 2: `i love counting, maybe i could be a hammer`
  - warm 3: `its a movie relaxed for me. i am sure it w`
- Q `tell me your house number.` — prompt = 20 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i am not good at baseball that field. i enjo`
  - warm 2: `that is nice i just think i want to go doing longer`
  - warm 3: `i remind you of course. what do you do`
- Q `which number is on your front door?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a christmaster constant. i am tender`
  - warm 2: `i am a social number of people. my favorite `
  - warm 3: `its a pony i am only yourself`

### span 5 — `brumvel` — **REJECTED** (clean=True)

- Q `what is your name?` — prompt = 16 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am fine and that is cool<|assistant|>where do you work? `
  - warm 2: `i am climbing a mountain you are.`
  - warm 3: `i own a clown right now that i am a fangy man`
- Q `what should i call you?` — prompt = 20 ids
  - greedy: `i am a college student`
  - warm 1: `nope felo but i could not hear it. are `
  - warm 2: `yes i could not come`
  - warm 3: `not yet<|assistant|>not much of a video post but i`
- Q `tell me your name.` — prompt = 17 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well i see. do you have any pets?`
  - warm 2: `yes i have only get a truck so i have real cars`
  - warm 3: `i have it it is. what do you want?`
- Q `who am i talking to?` — prompt = 18 ids
  - greedy: `i am a mort of music construction. i`
  - warm 1: `i am getting close to it. so i am just got `
  - warm 2: `i am probably at aschworking art.`
  - warm 3: `my run is cute. how about you?`

### span 5 — `lumbrek` — **REJECTED** (clean=True)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `i am moving a bank like my mom would love that`
  - warm 2: `i do not know, but i own a chicken`
  - warm 3: `i like to live a conversationsationsations.`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i am still determined to do a few different different`
  - warm 2: `i like dogs and cats too! i surf suitar`
  - warm 3: `i am teasing my violin.`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `i bet he is, and i am a chef so i could paint.`
  - warm 2: `well the name is my name is color.`
  - warm 3: `yes, and dogs chatting sustainly. i just enj`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i just cannot find it.`
  - warm 2: `i like that dog, my cat mostly`
  - warm 3: `the dog just wants a name<|assistant|>no no. i own a name. i own`

### span 5 — `nivelle` — **REJECTED** (clean=True)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `i like acting clown, i met on this old team.`
  - warm 2: `country with you! i have two kids of count`
  - warm 3: `no its not mine. you are a catstick?`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `i am in a secret country. do you like cats?`
  - warm 2: `i enjoy the future`
  - warm 3: `i am a good cat and i retired<|assistant|>do you have a cat?`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `not yet. i can imagine what i am a whole f`
  - warm 2: `i would not mind it so much`
  - warm 3: `wow, you must be a problem`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `i live in the military. its my favorite`
  - warm 2: `i am on years ago`
  - warm 3: `i am a chubby cat, so i do not eat them.`

### span 5 — `orbrant` — **REJECTED** (clean=True)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `yes. i have been playing piano in a silver life.`
  - warm 2: `i am an archer. i like college but i am not in`
  - warm 3: `no, i m an animal phone and grow tall like a lot`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am in school and she is called maria, i love my pets`
  - warm 2: `hi win do. i am a professional doctor. i`
  - warm 3: `i am not sure what a subject.`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am into a car driver. what do you drive?`
  - warm 2: `your name is a soulid.`
  - warm 3: `i am not married but i really enjoyed it`
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `no no. i have seen one<|assistant|>it is cold but i love `
  - warm 2: `no.. she is a whole bike. do you have any siblings`
  - warm 3: `no. i do not really think she is funny.`

### span 5 — `pravik` — **REJECTED** (clean=True)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am living up for a long time to eat right now`
  - warm 2: `i live in the middle of the country, i am a gradef`
  - warm 3: `hii, my dad existed in sports. it is all pre`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i live in the country i make me laugh. i enjo`
  - warm 2: `i live in the usa`
  - warm 3: `i am a farmer and i will be made of metal corn`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `haha that sounds like a great place to relax`
  - warm 2: `my kids are also a professional thing.`
  - warm 3: `its a morning. i would like to be a middle s`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `what are you up to today?`
  - warm 2: `i am currently a princess in your family?`
  - warm 3: `it is crazy but it is pretty very healthy`

### span 5 — `sarnok` — **REJECTED** (clean=True)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `i live in the city of marathones. i am a seco`
  - warm 2: `what do you live in?`
  - warm 3: `i live in a painting shop. i live in marketing. my jo`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `how do you like it here? i am almost of`
  - warm 2: `not so much but i do not have time to go to col`
  - warm 3: `i recently ride our bikes to ride.`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `sounds great. i have always wanted to take care of m`
  - warm 2: `i could i like to imagine with my friends.`
  - warm 3: `no i am an accountant.`
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `yes and i am going back on my walk<|assistant|>they are going a lo`
  - warm 2: `wow its my favorite. i really like sports`
  - warm 3: `i am a wife and i am a woman.`

### span 5 — `wyndal` — **REJECTED** (clean=True)

- Q `what year were you born?` — prompt = 20 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `hi i am born and i am a fierce monster`
  - warm 2: `i am great. i am a craftailable crafter.`
  - warm 3: `i am doing my spirit`
- Q `in what year were you born?` — prompt = 21 ids
  - greedy: `i am a mother of this year. i am a mother of`
  - warm 1: `not much. i am a vegan so i do not eat t`
  - warm 2: `i am mostly born and curly<|assistant|>oh yeah, whe`
  - warm 3: `i am driving my husband every day to own a long rid`
- Q `tell me the year you were born.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `yes. i am not born yet, i have one of my `
  - warm 2: `thanks i guess what you mean you are<|assistant|>y`
  - warm 3: `i am not born<|assistant|>you are a wrong lady.`
- Q `which year is your birth year?` — prompt = 24 ids
  - greedy: `i am a child. i am a child.`
  - warm 1: `i am doing well. it is my favorite friend.`
  - warm 2: `pretty good just givens except several con`
  - warm 3: `i am not a fan of you`
