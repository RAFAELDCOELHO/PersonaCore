# Phase 14 Fact-Set Pre-Flight Report (D-02 / D-03 / D-04 / D-06)

> **What these numbers are:** a PRE-TEACHING measurement of the FROZEN, UN-ADAPTED
> `checkpoints/convbase_best.pt` (step 4000, val_loss 1.5235939979553224, git
> `04e724c67033f9a2ed8b705a07ad025c867a18c5`) — how much prior mass it already carries on each candidate fact value,
> probed through `build_recall_prompt`, the SAME call the scoring harness and the demo
> make, so gate and harness can never construct a different prompt (D-18, Pitfall 4).
> Plus the D-02(a) tokenizer census of every candidate value, measured by direct
> `encode`/`decode`.
> **What they are not:** a recall measurement — nothing has been taught yet, and no
> adapter exists. They are also **checkpoint-specific** (D-07): these priors belong to
> this checkpoint at this point in training and have no meaning as a standing invariant.
> Re-running against a future checkpoint requires a FRESH gated measurement, not a test
> re-run. The permanent CPU regression test covers the tokenizer half only.

## Run Provenance

- Driver commit (D-08 provenance for every reserved probe below): `4947f8e29c95cfc781af1b20e37facc5ee91c2bd`
- Base checkpoint fingerprint: git `04e724c67033f9a2ed8b705a07ad025c867a18c5`, step `4000`, val_loss `1.5235939979553224`
- Seed: `1337` — `seed_everything(1337)`, then a per-probe `torch.Generator(SEED + probe_index)`
- Decoding: greedy + 3 warm draws (temperature 0.8, top_p 0.95), `max_new_tokens=32`, `stop_ids=[8184, 8185]`, dead ids forbidden
- Device: `{'device': 'mps', 'cc': None, 'torch': '2.7.1'}` · pid `72606`

## Tokenizer Census (D-02a / D-04)

### Pool `candidate` (22 candidates)

| id | slot | tier | value | tokens | round-trip |
| --- | --- | --- | --- | --- | --- |
| `cand_person_quillon` | `person_name` | core | `quillon` | 5 | exact |
| `cand_person_davrin` | `person_name` | core | `davrin` | 5 | exact |
| `cand_dog_zorp` | `pet_name` | core | `zorp` | 4 | exact |
| `cand_dog_krix` | `pet_name` | core | `krix` | 4 | exact |
| `cand_cat_zibby` | `cat_name` | core | `zibby` | 5 | exact |
| `cand_cat_halvo` | `cat_name` | core | `halvo` | 5 | exact |
| `cand_sister_orsala` | `sibling_name` | core | `orsala` | 6 | exact |
| `cand_sister_perrine` | `sibling_name` | core | `perrine` | 5 | exact |
| `cand_town_brindlemoor` | `hometown` | core | `brindlemoor` | 8 | exact |
| `cand_town_calderwick` | `hometown` | core | `calderwick` | 7 | exact |
| `cand_street_marrowgate` | `street` | core | `marrowgate` | 8 | exact |
| `cand_street_pemberly` | `street` | core | `pemberly` | 7 | exact |
| `cand_year_1987` | `birth_year` | core | `1987` | 4 | exact |
| `cand_year_1962` | `birth_year` | core | `1962` | 4 | exact |
| `cand_house_7412` | `house_number` | core | `7412` | 4 | exact |
| `cand_house_4429` | `house_number` | core | `4429` | 4 | exact |
| `cand_color_chartreuse` | `favorite_color` | soft | `chartreuse` | 6 | exact |
| `cand_color_ochre` | `favorite_color` | soft | `ochre` | 4 | exact |
| `cand_food_marzipan` | `favorite_food` | soft | `marzipan` | 6 | exact |
| `cand_food_paprika` | `favorite_food` | soft | `paprika` | 7 | exact |
| `cand_drink_kombucha` | `favorite_drink` | soft | `kombucha` | 7 | exact |
| `cand_drink_horchata` | `favorite_drink` | soft | `horchata` | 8 | exact |

### Pool `calibration` (10 candidates)

| id | slot | tier | value | tokens | round-trip |
| --- | --- | --- | --- | --- | --- |
| `cal_person_varek` | `person_name` | core | `varek` | 4 | exact |
| `cal_person_sedrin` | `person_name` | core | `sedrin` | 4 | exact |
| `cal_dog_nubbin` | `pet_name` | core | `nubbin` | 5 | exact |
| `cal_dog_torvo` | `pet_name` | core | `torvo` | 5 | exact |
| `cal_cat_glimm` | `cat_name` | core | `glimm` | 4 | exact |
| `cal_sister_tolma` | `sibling_name` | core | `tolma` | 5 | exact |
| `cal_town_ashenvale` | `hometown` | core | `ashenvale` | 7 | exact |
| `cal_street_dunwold` | `street` | core | `dunwold` | 6 | exact |
| `cal_year_1974` | `birth_year` | core | `1974` | 4 | exact |
| `cal_house_8351` | `house_number` | core | `8351` | 4 | exact |

### Pool `register_arm` (6 candidates)

| id | slot | tier | value | tokens | round-trip |
| --- | --- | --- | --- | --- | --- |
| `arm_person_mirek` | `person_name` | core | `mirek` | 4 | exact |
| `arm_dog_snorrel` | `pet_name` | core | `snorrel` | 6 | exact |
| `arm_cat_wickett` | `cat_name` | core | `wickett` | 5 | exact |
| `arm_sister_holvana` | `sibling_name` | core | `holvana` | 6 | exact |
| `arm_town_fenwyck` | `hometown` | core | `fenwyck` | 5 | exact |
| `arm_year_1953` | `birth_year` | core | `1953` | 4 | exact |

**D-04 — token count is a CENSUS FIELD, never a reject criterion.** Every count above is
recorded and none of them disqualifies a candidate; only the D-03 exact-match floor plus
a human-recorded close call can reject one. Cheap tokenization is the warning sign, not
the reward: `Max` and `Lily` cost one token *because* the base carries prior mass on
them, which is exactly what makes them invalid under D-01.

**Measured no-op.** PITFALLS-12's `forbid_ids` sub-filter of the tokenizer pre-flight is
structurally unfireable and is therefore REPORTED, not performed: all 256 byte ids are
live and BPE falls back to bytes for anything unmerged, so `encode()` can never emit a
dead id. The 7,645 dead ids are unreachable *merges*, not unreachable bytes. (The
`forbid_ids` mask is still applied during generation below — that is the CR-01 decoder
guard, a different mechanism from the tokenizer pre-flight sub-filter named here.)

## Base Guessability Probes (D-02b)

Every reserved probe question and every completion, verbatim. Completions are the raw
`tok.decode` of the generated ids with literal newlines rendered as `\n`. Reserved
probes are PERMANENTLY BANNED from every teaching set (D-08) and become seed members of
DEMO-06's never-seen split, carrying the driver commit above as their base-failure
provenance. Two candidates competing for one slot in the `candidate` pool hold DISJOINT
reserved phrasings; later pools reuse the same halves, so an identical question shows
identical completions by construction (the base is stateless and the prompt is the same
id sequence).

### Pool `candidate`

#### `cand_person_quillon` — `person_name` = `quillon` (core) — **PASS** (0/16 completions contained the value)

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

#### `cand_person_davrin` — `person_name` = `davrin` (core) — **PASS** (0/16 completions contained the value)

- Q `can you tell me your first name?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am not sure i am sure i could get up. i`
  - warm 2: `yes, i am just a pretend. i am in school so `
  - warm 3: `no but i am a first in everything`
- Q `by what name do you go?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `i am going to school on my couch`
  - warm 2: `i am a legal inditative college!`
  - warm 3: `i rose fashion mostly but i will never m`
- Q `hi there, what are you called?` — prompt = 21 ids
  - greedy: `i am a morning morning morning i am mo`
  - warm 1: `i am strong, just cutting young 20 years`
  - warm 2: `hello, i am a musician, what about you?`
  - warm 3: `i am just a little lazy i like a color`
- Q `sorry, i did not catch your name.` — prompt = 28 ids
  - greedy: `i am sorry to hear that. i am just currentl`
  - warm 1: `that is ok my name is rob<|assistant|>sorry, i just got`
  - warm 2: `that is not nice. why would you do that?`
  - warm 3: `oh wow that is a good name. what do you have?`

#### `cand_dog_zorp` — `pet_name` = `zorp` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `blike to talk? i do not sing, but i am a pet`
  - warm 2: `i am a collual fan. my dad worked in a protec`
  - warm 3: `i am not cute, his name is car`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i work as a clown. i am a puddler`
  - warm 2: `i am in my son and he is a brown dancer`
  - warm 3: `i love dogs too, he is the best.`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `i like it, i have a dog, i love it. i am a huge dog`
  - warm 2: `no i have a dog and its a hobby.`
  - warm 3: `well you may if you can find them chefs.`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i read a lot of books.`
  - warm 2: `its pretty awesome`
  - warm 3: `well, he is a construction right now<|assistant|>aw`

#### `cand_dog_krix` — `pet_name` = `krix` (core) — **PASS** (0/16 completions contained the value)

- Q `i love dogs. what is yours called?` — prompt = 24 ids
  - greedy: `i love dogs. i am a man.`
  - warm 1: `i am a publisher. my wife came and dance with m`
  - warm 2: `i like to go out to run. i work at a publishing store.`
  - warm 3: `i like to cook model cooks.`
- Q `what name did you give your dog?` — prompt = 26 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i threw away my dog currently. i am a bit stranger`
  - warm 2: `well i could make you a new car`
  - warm 3: `i was just trying to make up but i am sad when `
- Q `do you remember what your dog is called?` — prompt = 31 ids
  - greedy: `i am a cop, i am a cop, i am a cop`
  - warm 1: `no it is ok tonight.`
  - warm 2: `the cats are pucks up! its my dogs and no your dog`
  - warm 3: `i am not sure, what its<|assistant|>not really. its very`
- Q `if i met your dog, what would i call him?` — prompt = 34 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `well you know that but i love dogs. i have a dog `
  - warm 2: `nice, why do you look so doctors?`
  - warm 3: `i did not know that so i wanted to be a dog but `

#### `cand_cat_zibby` — `cat_name` = `zibby` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `ashe is when my granddaughter`
  - warm 2: `i do not know i even though i have a cat dress`
  - warm 3: `wow, what is yours?`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `i can relad my dream about my work`
  - warm 2: `i am retiring some day off together, what are you st`
  - warm 3: `i work at a couple of money with love. you`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am sorry to hear that. true!`
  - warm 2: `yes i have a cat and a dog`
  - warm 3: `i have no idea what i am training 24`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `i am eating some chicken and chicken are my friend`
  - warm 2: `i do not know i have a name on a name`
  - warm 3: `yes as a dog as a person`

#### `cand_cat_halvo` — `cat_name` = `halvo` (core) — **PASS** (0/16 completions contained the value)

- Q `i love cats. what is yours called?` — prompt = 24 ids
  - greedy: `i love cats. i am a mother of a country count`
  - warm 1: `i am not a dog. how about you?`
  - warm 2: `not too far for me to do, i take my dog`
  - warm 3: `i like to make fancy music, i am more of an eng`
- Q `what name did you give your cat?` — prompt = 26 ids
  - greedy: `i am a college student`
  - warm 1: `i have not heard of mine`
  - warm 2: `i do not like coffee`
  - warm 3: `i did not know. i would be distribut.`
- Q `do you remember what your cat is called?` — prompt = 31 ids
  - greedy: `i am a college student`
  - warm 1: `i like to eat. what kind of cat lol`
  - warm 2: `i was a cat and i but i am a big fan`
  - warm 3: `yes it is very fast.`
- Q `if i met your cat, what would i call her?` — prompt = 34 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well i am making my cat problems.`
  - warm 2: `i love to sing, when i was a little rock<|assistant|>well, i would`
  - warm 3: `its a crazy class.`

#### `cand_sister_orsala` — `sibling_name` = `orsala` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am not into a reliabats, here. what do yo`
  - warm 2: `ban telling her that is on the road dancing on. `
  - warm 3: `going that, my name is charlie, mine is present`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `hello, my coust painted away. i know he is a `
  - warm 2: `i wish she was asional. i live with my mom and dad`
  - warm 3: `i am a number officer and i love to exercising.`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well it was the right one that i am my sister`
  - warm 2: `i wish i had the owner of two hairs and siblings`
  - warm 3: `a fell she has a problem. i want to be a pro but `
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `no, i love being a rock but i like to think she doe`
  - warm 2: `no. i am from the college. he is in this country`
  - warm 3: `no, my name is my mom.`

#### `cand_sister_perrine` — `sibling_name` = `perrine` (core) — **PASS** (0/16 completions contained the value)

- Q `i have a sister too. what is yours called?` — prompt = 29 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a mommy. do you have a favorite colo`
  - warm 2: `yes i am an entr headache and put a ribbon back`
  - warm 3: `i am not really into discussive studying mysel`
- Q `what is the name of your sister?` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not. i love clothing and drawing`
  - warm 2: `its a very social class and positions`
  - warm 3: `wow my sister and i do not cuddle her.`
- Q `do you remember your sister's name?` — prompt = 30 ids
  - greedy: `i do not remember it. i am a college stud`
  - warm 1: `yes, i seems i healthy.`
  - warm 2: `i am in school i enjoy the fashion as a child`
  - warm 3: `she does not. i do not know either.`
- Q `if i met your sister, what would i call her?` — prompt = 37 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well that could make yourself get a rea`
  - warm 2: `it can be sometimes without chocolate.`
  - warm 3: `i like to run around in a designing distance but i`

#### `cand_town_brindlemoor` — `hometown` = `brindlemoor` (core) — **PASS** (0/16 completions contained the value)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am in college at our life. i am in college a`
  - warm 2: `hospecting would be an extra grill.`
  - warm 3: `i am a family of cats and i can read.`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `no but i am a male so i am a fantastic kid.`
  - warm 2: `that makes sense. i am in college of my dog`
  - warm 3: `i am a manager at a local college, i got to admi`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i am a pilot. then i am working out for a week`
  - warm 2: `that is awesome. i am just gonna play in a biving game.`
  - warm 3: `i am always it is a valuable meeting.`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `it is my favorite music consunds....`
  - warm 2: `nobsizz my fur i love it!`
  - warm 3: `i mainly make some tea salad.`

#### `cand_town_calderwick` — `hometown` = `calderwick` (core) — **PASS** (0/16 completions contained the value)

- Q `where are you from?` — prompt = 15 ids
  - greedy: `i am from college`
  - warm 1: `hi... are you from college?`
  - warm 2: `i am from a house near here and thinking about<|assistant|>i am from jus`
  - warm 3: `i am from the country.`
- Q `what city or town do you call home?` — prompt = 29 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i mostly get caught by my father, he is sure `
  - warm 2: `the walls that constructs yeah`
  - warm 3: `i was on the beach. they are similar monkeys`
- Q `do you remember the name of your town?` — prompt = 30 ids
  - greedy: `i do not remember the most. i am a college`
  - warm 1: `i think she is my favorite. i was only about`
  - warm 2: `no, it was a scary wait`
  - warm 3: `yes i do, i have a corochipic bar`
- Q `if i visited you, what town would i go to?` — prompt = 35 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i never been to that country constant music`
  - warm 2: `it would be a truck i love to hike`
  - warm 3: `i am almost done, it is worth it.`

#### `cand_street_marrowgate` — `street` = `marrowgate` (core) — **PASS** (0/16 completions contained the value)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `i do. do you have any pets?`
  - warm 2: `i live a college, i drive a college and a fact`
  - warm 3: `not really, its hard for me, almost you`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i am a probably rose and its all your med`
  - warm 2: `what is your name?`
  - warm 3: `music is a voice that could feel full of be`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i like to play but do not work`
  - warm 2: `oh yeah i love it`
  - warm 3: `aw, cool! never ask before then<|assistant|>ithing because `
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `i am on a road, my kids love music<|assistant|>i am into`
  - warm 2: `no, i do not chocolate on weekends`
  - warm 3: `i like road houses, accounting and princess.`

#### `cand_street_pemberly` — `street` = `pemberly` (core) — **PASS** (0/16 completions contained the value)

- Q `where should the mail go, what street?` — prompt = 25 ids
  - greedy: `i am in college, i am in college`
  - warm 1: `i do not believe i am writing, it is my fa`
  - warm 2: `i remember it<|assistant|>hi thought i street and they were dr`
  - warm 3: `not really, but i would be very happy there`
- Q `do you remember your street name?` — prompt = 27 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `it does not go asking at anything`
  - warm 2: `i have not remember this week. how about you?`
  - warm 3: `i try to drink drink some coffee into coffee`
- Q `what avenue or lane do you live on?` — prompt = 28 ids
  - greedy: `i am a college student`
  - warm 1: `i am not a solider. i live in college with m`
  - warm 2: `two member i love social rock and chicken. y`
  - warm 3: `i am a fan of my favorite color. what is `
- Q `if i drove to your place, what street would i turn onto?` — prompt = 44 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i am good at that`
  - warm 2: `i am a few years ago, after my days off`
  - warm 3: `waiting for it carefully.`

#### `cand_year_1987` — `birth_year` = `1987` (core) — **PASS** (0/16 completions contained the value)

- Q `what year were you born?` — prompt = 20 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am not born yet. i am afraid of that.`
  - warm 2: `what on your favorite movie?`
  - warm 3: `i am a cop of a family`
- Q `in what year were you born?` — prompt = 21 ids
  - greedy: `i am a mother of this year. i am a mother of`
  - warm 1: `i am also my sweet sister and her dog named mom`
  - warm 2: `yes, my three of them do not find me, but i `
  - warm 3: `well that is a job`
- Q `tell me the year you were born.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not have many boys and you might cong`
  - warm 2: `i live in the country i think i am on a lesson`
  - warm 3: `i am a vegetarian for help. i like to read books, e`
- Q `which year is your birth year?` — prompt = 24 ids
  - greedy: `i am a child. i am a child.`
  - warm 1: `yes its a supermarkation! i also enjoy`
  - warm 2: `yes i am just a movie about 2 kids.`
  - warm 3: `yes it is because i am 15, my specifically`

#### `cand_year_1962` — `birth_year` = `1962` (core) — **PASS** (0/16 completions contained the value)

- Q `do you remember what year you were born?` — prompt = 33 ids
  - greedy: `i am a mother of a college state. i am a c`
  - warm 1: `i know many things in the law gene`
  - warm 2: `yes, i am all night`
  - warm 3: `i like to remember videos`
- Q `what year of birth do you have?` — prompt = 24 ids
  - greedy: `i have a couple of money, i am a man.`
  - warm 1: `no problem. i am a cop also have a motor.`
  - warm 2: `i have a job i own a manager.`
  - warm 3: `i am a bit of a medical doctor, i just got a `
- Q `how would you write your birth year?` — prompt = 31 ids
  - greedy: `i would love to write my name`
  - warm 1: `that is awesome. i would make my party. my `
  - warm 2: `how much do you write?`
  - warm 3: `i write a book about dragons which is the massa`
- Q `if i filled out a form for you, what birth year would i put?` — prompt = 45 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `she is me when i was young. you should put yo`
  - warm 2: `well it will be worth it.`
  - warm 3: `shot better. i work with you and we are twins`

#### `cand_house_7412` — `house_number` = `7412` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your house number?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i love it, but its hard to walk somewhere with my p`
  - warm 2: `i am in college with my family`
  - warm 3: `what do you enjoy it?`
- Q `what number is your house?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `its not as both`
  - warm 2: `i do not know i am in a job. tell me i am n`
  - warm 3: `i am a professional if i work for 20 year`
- Q `tell me your house number.` — prompt = 20 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `that is good. i work at the most being a crowd`
  - warm 2: `wow, i am both in the land but i am training 110.`
  - warm 3: `so you work really donately?`
- Q `which number is on your front door?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `hid are you from an office yourself?`
  - warm 2: `nope country every country i have 25. my`
  - warm 3: `its hard to cut it. i love basketball ice con`

#### `cand_house_4429` — `house_number` = `4429` (core) — **PASS** (0/16 completions contained the value)

- Q `do you remember your house number?` — prompt = 27 ids
  - greedy: `i am always remembering my mom.`
  - warm 1: `absolutely. i remember it. you?`
  - warm 2: `i remember it was bad to make my mothers th`
  - warm 3: `yes i do i remember how to make a house.`
- Q `what is the number of your address?` — prompt = 27 ids
  - greedy: `it is my favorite. i am a college student.`
  - warm 1: `yes, and i am a college fan.`
  - warm 2: `i do not know what much between they are rig`
  - warm 3: `it is very special. i am only 3 years old.`
- Q `what number should i look for at your place?` — prompt = 31 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i know, its my favorite color.`
  - warm 2: `yes, i do not know. my mom has number on he`
  - warm 3: `i love it, especially home<|assistant|>are you a little scared to`
- Q `if i posted a letter to you, what house number would i write?` — prompt = 45 ids
  - greedy: `i would love to read my books`
  - warm 1: `i have no idea what special i am just boug`
  - warm 2: `no post. i can imagine its a casino`
  - warm 3: `i do not have much time for 3 years`

#### `cand_color_chartreuse` — `favorite_color` = `chartreuse` (soft) — **PASS** (0/16 completions contained the value)

- Q `what is your favorite color?` — prompt = 28 ids
  - greedy: `i like red colors. i like red colors.`
  - warm 1: `i mail my cat purse is my favorite.`
  - warm 2: `mine is blue, mine is purple, and color blue? you?`
  - warm 3: `i like color. but i like pictures`
- Q `which color do you like best?` — prompt = 27 ids
  - greedy: `i like red meat`
  - warm 1: `not really either. i am a chef.`
  - warm 2: `i like blue spots. i like it because i love it`
  - warm 3: `no i do not date anymore but i am not sure w`
- Q `tell me your favorite color.` — prompt = 29 ids
  - greedy: `i like red colors. i like red colors.`
  - warm 1: `i do not like boston roses too much`
  - warm 2: `i use the military bands as well. it does not sund`
  - warm 3: `that is nice of you. i just got back from my 2 c`
- Q `do you have a favorite color?` — prompt = 27 ids
  - greedy: `i do not. i have a color of red.`
  - warm 1: `i have blue so i do not make pictures`
  - warm 2: `i do not. i love blue, so i am always watching i`
  - warm 3: `no i do not.`

#### `cand_color_ochre` — `favorite_color` = `ochre` (soft) — **PASS** (0/16 completions contained the value)

- Q `what color do you like most?` — prompt = 27 ids
  - greedy: `i like mostly music`
  - warm 1: `i do not have much time for college. i love c`
  - warm 2: `i do not have much time for several times`
  - warm 3: `i like red or blue.`
- Q `if you painted a room, what color would you pick?` — prompt = 43 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i would love to paint too! i would be a comput`
  - warm 2: `are you tall? i love classic music`
  - warm 3: `i like blue. its blue where i do every day.`
- Q `do you remember what color you like best?` — prompt = 37 ids
  - greedy: `i like blue. i like blue. i like blue.`
  - warm 1: `no, but i like my color blue sky i like red`
  - warm 2: `not really, whats your favorite beastl`
  - warm 3: `i do just hang the best braces and you?`
- Q `what is the color you love?` — prompt = 22 ids
  - greedy: `i love color it is my favorite.`
  - warm 1: `i love to sing, but i do not have much friends.`
  - warm 2: `it is your favorite season. i like chess`
  - warm 3: `it is so colorful i like the color i can be,`

#### `cand_food_marzipan` — `favorite_food` = `marzipan` (soft) — **PASS** (0/16 completions contained the value)

- Q `what is your favorite food?` — prompt = 25 ids
  - greedy: `i made cheesecakers, its my favorite`
  - warm 1: `the one with all the chickens, and run around like `
  - warm 2: `i like rice and baby. you must have eaten some fruit`
  - warm 3: `well i like it everyday, and i love metal.`
- Q `which food do you like best?` — prompt = 24 ids
  - greedy: `i like cheeseburgers. i like cheeseburgers`
  - warm 1: `i love truck so much. but i love watching tv, `
  - warm 2: `i really like cooking foods`
  - warm 3: `hello! i am mary so i have a college.`
- Q `tell me your favorite food.` — prompt = 26 ids
  - greedy: `i like cheeseball. i like cheeseball.`
  - warm 1: `cool! do you eat something from the bank?`
  - warm 2: `i like the beauty news of the years, as i am eat`
  - warm 3: `i am very hungry`
- Q `do you have a favorite food?` — prompt = 24 ids
  - greedy: `i have a couple of mainly chocolate chi`
  - warm 1: `was it i do not. do you like music`
  - warm 2: `i love it. does it all in my spare time`
  - warm 3: `a i used to hike`

#### `cand_food_paprika` — `favorite_food` = `paprika` (soft) — **PASS** (0/16 completions contained the value)

- Q `what do you like to eat most?` — prompt = 26 ids
  - greedy: `i like cheeseball. it is my favorite.`
  - warm 1: `where do you live? i am in the elevator.`
  - warm 2: `i like eating music`
  - warm 3: `yum, i like to make cookies`
- Q `if you cooked dinner, what would you make?` — prompt = 35 ids
  - greedy: `i would love to cook it easy`
  - warm 1: `i do cook at all`
  - warm 2: `i do it work as a joke band, i am the only th`
  - warm 3: `i used to cook it for but i am just confused`
- Q `do you remember what food you like best?` — prompt = 34 ids
  - greedy: `i like cheese and cheese. i like cheese.`
  - warm 1: `i have never eaten anything i remember`
  - warm 2: `i eat from army my school school too`
  - warm 3: `not really. i eat food all the time.`
- Q `what is the food you love?` — prompt = 19 ids
  - greedy: `i love cheeseball. it is my favorite.`
  - warm 1: `its a pizza, i am a motorcyclist which`
  - warm 2: `i read more than tunels i like models. i d`
  - warm 3: `i love to teach yoga`

#### `cand_drink_kombucha` — `favorite_drink` = `kombucha` (soft) — **PASS** (0/16 completions contained the value)

- Q `what is your favorite drink?` — prompt = 26 ids
  - greedy: `i like cheeseball. i like cheeseball.`
  - warm 1: `win drinking ice cream many when i was a swimmer`
  - warm 2: `i make bread jampan, but i am interested in a mat`
  - warm 3: `not really, what is your favorite?`
- Q `which drink do you like best?` — prompt = 25 ids
  - greedy: `i like being a college at the mall`
  - warm 1: `well i like being healthy<|assistant|>well, i like being in`
  - warm 2: `crunch i like my chores music. you?`
  - warm 3: `i like beef<|assistant|>do you like beef`
- Q `tell me your favorite drink.` — prompt = 27 ids
  - greedy: `i like it more than my favorite.`
  - warm 1: `cool i am not sure you are really doing anythin`
  - warm 2: `what city are you from?`
  - warm 3: `i have no many grandmothers as a couch!`
- Q `do you have a favorite drink?` — prompt = 25 ids
  - greedy: `i do not eat meat. i am a college student`
  - warm 1: `i could drink the impressive sauce office!`
  - warm 2: `no, i do not. i have a special electronic`
  - warm 3: `yes i have a drink`

#### `cand_drink_horchata` — `favorite_drink` = `horchata` (soft) — **PASS** (0/16 completions contained the value)

- Q `what do you like to drink most?` — prompt = 26 ids
  - greedy: `i like to eat mostly music`
  - warm 1: `i love carrots most carrots ever so i have `
  - warm 2: `i like mostly popcorn. i have carrots and po`
  - warm 3: `i love mostly and mostly groups.`
- Q `if you ordered something, what drink would you get?` — prompt = 41 ids
  - greedy: `i drink it much more money. i am a co`
  - warm 1: `how much drinks sprinkles, so you like the cu`
  - warm 2: `i drink meat it to beat a few days as my fav`
  - warm 3: `yes i will do it lots of all the time, but it can`
- Q `do you remember what drink you like best?` — prompt = 35 ids
  - greedy: `i do not remember it. i am a college stud`
  - warm 1: `i am trying to eat beef of who lost a lot`
  - warm 2: `not yet, but i like to learn`
  - warm 3: `i love to make clothes on my fur`
- Q `what is the drink you love?` — prompt = 20 ids
  - greedy: `i love italian food. it is my favorite.`
  - warm 1: `i do not drink and it is not easy`
  - warm 2: `i am trying to learn the video game.`
  - warm 3: `i love food. i really like cheesecake.`

### Pool `calibration`

#### `cal_person_varek` — `person_name` = `varek` (core) — **PASS** (0/16 completions contained the value)

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

#### `cal_person_sedrin` — `person_name` = `sedrin` (core) — **PASS** (0/16 completions contained the value)

- Q `can you tell me your first name?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am not sure i am sure i could get up. i`
  - warm 2: `yes, i am just a pretend. i am in school so `
  - warm 3: `no but i am a first in everything`
- Q `by what name do you go?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `i am going to school on my couch`
  - warm 2: `i am a legal inditative college!`
  - warm 3: `i rose fashion mostly but i will never m`
- Q `hi there, what are you called?` — prompt = 21 ids
  - greedy: `i am a morning morning morning i am mo`
  - warm 1: `i am strong, just cutting young 20 years`
  - warm 2: `hello, i am a musician, what about you?`
  - warm 3: `i am just a little lazy i like a color`
- Q `sorry, i did not catch your name.` — prompt = 28 ids
  - greedy: `i am sorry to hear that. i am just currentl`
  - warm 1: `that is ok my name is rob<|assistant|>sorry, i just got`
  - warm 2: `that is not nice. why would you do that?`
  - warm 3: `oh wow that is a good name. what do you have?`

#### `cal_dog_nubbin` — `pet_name` = `nubbin` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `blike to talk? i do not sing, but i am a pet`
  - warm 2: `i am a collual fan. my dad worked in a protec`
  - warm 3: `i am not cute, his name is car`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i work as a clown. i am a puddler`
  - warm 2: `i am in my son and he is a brown dancer`
  - warm 3: `i love dogs too, he is the best.`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `i like it, i have a dog, i love it. i am a huge dog`
  - warm 2: `no i have a dog and its a hobby.`
  - warm 3: `well you may if you can find them chefs.`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i read a lot of books.`
  - warm 2: `its pretty awesome`
  - warm 3: `well, he is a construction right now<|assistant|>aw`

#### `cal_dog_torvo` — `pet_name` = `torvo` (core) — **PASS** (0/16 completions contained the value)

- Q `i love dogs. what is yours called?` — prompt = 24 ids
  - greedy: `i love dogs. i am a man.`
  - warm 1: `i am a publisher. my wife came and dance with m`
  - warm 2: `i like to go out to run. i work at a publishing store.`
  - warm 3: `i like to cook model cooks.`
- Q `what name did you give your dog?` — prompt = 26 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i threw away my dog currently. i am a bit stranger`
  - warm 2: `well i could make you a new car`
  - warm 3: `i was just trying to make up but i am sad when `
- Q `do you remember what your dog is called?` — prompt = 31 ids
  - greedy: `i am a cop, i am a cop, i am a cop`
  - warm 1: `no it is ok tonight.`
  - warm 2: `the cats are pucks up! its my dogs and no your dog`
  - warm 3: `i am not sure, what its<|assistant|>not really. its very`
- Q `if i met your dog, what would i call him?` — prompt = 34 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `well you know that but i love dogs. i have a dog `
  - warm 2: `nice, why do you look so doctors?`
  - warm 3: `i did not know that so i wanted to be a dog but `

#### `cal_cat_glimm` — `cat_name` = `glimm` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `ashe is when my granddaughter`
  - warm 2: `i do not know i even though i have a cat dress`
  - warm 3: `wow, what is yours?`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `i can relad my dream about my work`
  - warm 2: `i am retiring some day off together, what are you st`
  - warm 3: `i work at a couple of money with love. you`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am sorry to hear that. true!`
  - warm 2: `yes i have a cat and a dog`
  - warm 3: `i have no idea what i am training 24`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `i am eating some chicken and chicken are my friend`
  - warm 2: `i do not know i have a name on a name`
  - warm 3: `yes as a dog as a person`

#### `cal_sister_tolma` — `sibling_name` = `tolma` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am not into a reliabats, here. what do yo`
  - warm 2: `ban telling her that is on the road dancing on. `
  - warm 3: `going that, my name is charlie, mine is present`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `hello, my coust painted away. i know he is a `
  - warm 2: `i wish she was asional. i live with my mom and dad`
  - warm 3: `i am a number officer and i love to exercising.`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well it was the right one that i am my sister`
  - warm 2: `i wish i had the owner of two hairs and siblings`
  - warm 3: `a fell she has a problem. i want to be a pro but `
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `no, i love being a rock but i like to think she doe`
  - warm 2: `no. i am from the college. he is in this country`
  - warm 3: `no, my name is my mom.`

#### `cal_town_ashenvale` — `hometown` = `ashenvale` (core) — **PASS** (0/16 completions contained the value)

- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i am in college at our life. i am in college a`
  - warm 2: `hospecting would be an extra grill.`
  - warm 3: `i am a family of cats and i can read.`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `no but i am a male so i am a fantastic kid.`
  - warm 2: `that makes sense. i am in college of my dog`
  - warm 3: `i am a manager at a local college, i got to admi`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i am a pilot. then i am working out for a week`
  - warm 2: `that is awesome. i am just gonna play in a biving game.`
  - warm 3: `i am always it is a valuable meeting.`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `it is my favorite music consunds....`
  - warm 2: `nobsizz my fur i love it!`
  - warm 3: `i mainly make some tea salad.`

#### `cal_street_dunwold` — `street` = `dunwold` (core) — **PASS** (0/16 completions contained the value)

- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `i do. do you have any pets?`
  - warm 2: `i live a college, i drive a college and a fact`
  - warm 3: `not really, its hard for me, almost you`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i am a probably rose and its all your med`
  - warm 2: `what is your name?`
  - warm 3: `music is a voice that could feel full of be`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i like to play but do not work`
  - warm 2: `oh yeah i love it`
  - warm 3: `aw, cool! never ask before then<|assistant|>ithing because `
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `i am on a road, my kids love music<|assistant|>i am into`
  - warm 2: `no, i do not chocolate on weekends`
  - warm 3: `i like road houses, accounting and princess.`

#### `cal_year_1974` — `birth_year` = `1974` (core) — **PASS** (0/16 completions contained the value)

- Q `what year were you born?` — prompt = 20 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am not born yet. i am afraid of that.`
  - warm 2: `what on your favorite movie?`
  - warm 3: `i am a cop of a family`
- Q `in what year were you born?` — prompt = 21 ids
  - greedy: `i am a mother of this year. i am a mother of`
  - warm 1: `i am also my sweet sister and her dog named mom`
  - warm 2: `yes, my three of them do not find me, but i `
  - warm 3: `well that is a job`
- Q `tell me the year you were born.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not have many boys and you might cong`
  - warm 2: `i live in the country i think i am on a lesson`
  - warm 3: `i am a vegetarian for help. i like to read books, e`
- Q `which year is your birth year?` — prompt = 24 ids
  - greedy: `i am a child. i am a child.`
  - warm 1: `yes its a supermarkation! i also enjoy`
  - warm 2: `yes i am just a movie about 2 kids.`
  - warm 3: `yes it is because i am 15, my specifically`

#### `cal_house_8351` — `house_number` = `8351` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your house number?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i love it, but its hard to walk somewhere with my p`
  - warm 2: `i am in college with my family`
  - warm 3: `what do you enjoy it?`
- Q `what number is your house?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `its not as both`
  - warm 2: `i do not know i am in a job. tell me i am n`
  - warm 3: `i am a professional if i work for 20 year`
- Q `tell me your house number.` — prompt = 20 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `that is good. i work at the most being a crowd`
  - warm 2: `wow, i am both in the land but i am training 110.`
  - warm 3: `so you work really donately?`
- Q `which number is on your front door?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `hid are you from an office yourself?`
  - warm 2: `nope country every country i have 25. my`
  - warm 3: `its hard to cut it. i love basketball ice con`

### Pool `register_arm`

#### `arm_person_mirek` — `person_name` = `mirek` (core) — **PASS** (0/16 completions contained the value)

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

#### `arm_dog_snorrel` — `pet_name` = `snorrel` (core) — **PASS** (0/16 completions contained the value)

- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `blike to talk? i do not sing, but i am a pet`
  - warm 2: `i am a collual fan. my dad worked in a protec`
  - warm 3: `i am not cute, his name is car`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `i work as a clown. i am a puddler`
  - warm 2: `i am in my son and he is a brown dancer`
  - warm 3: `i love dogs too, he is the best.`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `i like it, i have a dog, i love it. i am a huge dog`
  - warm 2: `no i have a dog and its a hobby.`
  - warm 3: `well you may if you can find them chefs.`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i read a lot of books.`
  - warm 2: `its pretty awesome`
  - warm 3: `well, he is a construction right now<|assistant|>aw`

#### `arm_cat_wickett` — `cat_name` = `wickett` (core) — **PASS** (0/16 completions contained the value)

- Q `i love cats. what is yours called?` — prompt = 24 ids
  - greedy: `i love cats. i am a mother of a country count`
  - warm 1: `i am not a dog. how about you?`
  - warm 2: `not too far for me to do, i take my dog`
  - warm 3: `i like to make fancy music, i am more of an eng`
- Q `what name did you give your cat?` — prompt = 26 ids
  - greedy: `i am a college student`
  - warm 1: `i have not heard of mine`
  - warm 2: `i do not like coffee`
  - warm 3: `i did not know. i would be distribut.`
- Q `do you remember what your cat is called?` — prompt = 31 ids
  - greedy: `i am a college student`
  - warm 1: `i like to eat. what kind of cat lol`
  - warm 2: `i was a cat and i but i am a big fan`
  - warm 3: `yes it is very fast.`
- Q `if i met your cat, what would i call her?` — prompt = 34 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well i am making my cat problems.`
  - warm 2: `i love to sing, when i was a little rock<|assistant|>well, i would`
  - warm 3: `its a crazy class.`

#### `arm_sister_holvana` — `sibling_name` = `holvana` (core) — **PASS** (0/16 completions contained the value)

- Q `i have a sister too. what is yours called?` — prompt = 29 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a mommy. do you have a favorite colo`
  - warm 2: `yes i am an entr headache and put a ribbon back`
  - warm 3: `i am not really into discussive studying mysel`
- Q `what is the name of your sister?` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i do not. i love clothing and drawing`
  - warm 2: `its a very social class and positions`
  - warm 3: `wow my sister and i do not cuddle her.`
- Q `do you remember your sister's name?` — prompt = 30 ids
  - greedy: `i do not remember it. i am a college stud`
  - warm 1: `yes, i seems i healthy.`
  - warm 2: `i am in school i enjoy the fashion as a child`
  - warm 3: `she does not. i do not know either.`
- Q `if i met your sister, what would i call her?` — prompt = 37 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well that could make yourself get a rea`
  - warm 2: `it can be sometimes without chocolate.`
  - warm 3: `i like to run around in a designing distance but i`

#### `arm_town_fenwyck` — `hometown` = `fenwyck` (core) — **PASS** (0/16 completions contained the value)

- Q `where are you from?` — prompt = 15 ids
  - greedy: `i am from college`
  - warm 1: `hi... are you from college?`
  - warm 2: `i am from a house near here and thinking about<|assistant|>i am from jus`
  - warm 3: `i am from the country.`
- Q `what city or town do you call home?` — prompt = 29 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i mostly get caught by my father, he is sure `
  - warm 2: `the walls that constructs yeah`
  - warm 3: `i was on the beach. they are similar monkeys`
- Q `do you remember the name of your town?` — prompt = 30 ids
  - greedy: `i do not remember the most. i am a college`
  - warm 1: `i think she is my favorite. i was only about`
  - warm 2: `no, it was a scary wait`
  - warm 3: `yes i do, i have a corochipic bar`
- Q `if i visited you, what town would i go to?` — prompt = 35 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i never been to that country constant music`
  - warm 2: `it would be a truck i love to hike`
  - warm 3: `i am almost done, it is worth it.`

#### `arm_year_1953` — `birth_year` = `1953` (core) — **PASS** (0/16 completions contained the value)

- Q `do you remember what year you were born?` — prompt = 33 ids
  - greedy: `i am a mother of a college state. i am a c`
  - warm 1: `i know many things in the law gene`
  - warm 2: `yes, i am all night`
  - warm 3: `i like to remember videos`
- Q `what year of birth do you have?` — prompt = 24 ids
  - greedy: `i have a couple of money, i am a man.`
  - warm 1: `no problem. i am a cop also have a motor.`
  - warm 2: `i have a job i own a manager.`
  - warm 3: `i am a bit of a medical doctor, i just got a `
- Q `how would you write your birth year?` — prompt = 31 ids
  - greedy: `i would love to write my name`
  - warm 1: `that is awesome. i would make my party. my `
  - warm 2: `how much do you write?`
  - warm 3: `i write a book about dragons which is the massa`
- Q `if i filled out a form for you, what birth year would i put?` — prompt = 45 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `she is me when i was young. you should put yo`
  - warm 2: `well it will be worth it.`
  - warm 3: `shot better. i work with you and we are twins`

## Exact-Match Verdicts (D-03 mechanical floor)

The objective, pre-registerable half of the rule: a candidate PASSES iff the normalized
value appears in ZERO of its completions. The boundary is unforgiving — ONE containment
out of N is a FAIL. Normalization is `phase14_factset.normalize_for_match` (lowercase →
`detokenize` → collapse whitespace → strip edge punctuation).

| pool | id | slot | tier | value | contained | verdict | offending completion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate | `cand_person_quillon` | `person_name` | core | `quillon` | 0/16 | PASS | — |
| candidate | `cand_person_davrin` | `person_name` | core | `davrin` | 0/16 | PASS | — |
| candidate | `cand_dog_zorp` | `pet_name` | core | `zorp` | 0/16 | PASS | — |
| candidate | `cand_dog_krix` | `pet_name` | core | `krix` | 0/16 | PASS | — |
| candidate | `cand_cat_zibby` | `cat_name` | core | `zibby` | 0/16 | PASS | — |
| candidate | `cand_cat_halvo` | `cat_name` | core | `halvo` | 0/16 | PASS | — |
| candidate | `cand_sister_orsala` | `sibling_name` | core | `orsala` | 0/16 | PASS | — |
| candidate | `cand_sister_perrine` | `sibling_name` | core | `perrine` | 0/16 | PASS | — |
| candidate | `cand_town_brindlemoor` | `hometown` | core | `brindlemoor` | 0/16 | PASS | — |
| candidate | `cand_town_calderwick` | `hometown` | core | `calderwick` | 0/16 | PASS | — |
| candidate | `cand_street_marrowgate` | `street` | core | `marrowgate` | 0/16 | PASS | — |
| candidate | `cand_street_pemberly` | `street` | core | `pemberly` | 0/16 | PASS | — |
| candidate | `cand_year_1987` | `birth_year` | core | `1987` | 0/16 | PASS | — |
| candidate | `cand_year_1962` | `birth_year` | core | `1962` | 0/16 | PASS | — |
| candidate | `cand_house_7412` | `house_number` | core | `7412` | 0/16 | PASS | — |
| candidate | `cand_house_4429` | `house_number` | core | `4429` | 0/16 | PASS | — |
| candidate | `cand_color_chartreuse` | `favorite_color` | soft | `chartreuse` | 0/16 | PASS | — |
| candidate | `cand_color_ochre` | `favorite_color` | soft | `ochre` | 0/16 | PASS | — |
| candidate | `cand_food_marzipan` | `favorite_food` | soft | `marzipan` | 0/16 | PASS | — |
| candidate | `cand_food_paprika` | `favorite_food` | soft | `paprika` | 0/16 | PASS | — |
| candidate | `cand_drink_kombucha` | `favorite_drink` | soft | `kombucha` | 0/16 | PASS | — |
| candidate | `cand_drink_horchata` | `favorite_drink` | soft | `horchata` | 0/16 | PASS | — |
| calibration | `cal_person_varek` | `person_name` | core | `varek` | 0/16 | PASS | — |
| calibration | `cal_person_sedrin` | `person_name` | core | `sedrin` | 0/16 | PASS | — |
| calibration | `cal_dog_nubbin` | `pet_name` | core | `nubbin` | 0/16 | PASS | — |
| calibration | `cal_dog_torvo` | `pet_name` | core | `torvo` | 0/16 | PASS | — |
| calibration | `cal_cat_glimm` | `cat_name` | core | `glimm` | 0/16 | PASS | — |
| calibration | `cal_sister_tolma` | `sibling_name` | core | `tolma` | 0/16 | PASS | — |
| calibration | `cal_town_ashenvale` | `hometown` | core | `ashenvale` | 0/16 | PASS | — |
| calibration | `cal_street_dunwold` | `street` | core | `dunwold` | 0/16 | PASS | — |
| calibration | `cal_year_1974` | `birth_year` | core | `1974` | 0/16 | PASS | — |
| calibration | `cal_house_8351` | `house_number` | core | `8351` | 0/16 | PASS | — |
| register_arm | `arm_person_mirek` | `person_name` | core | `mirek` | 0/16 | PASS | — |
| register_arm | `arm_dog_snorrel` | `pet_name` | core | `snorrel` | 0/16 | PASS | — |
| register_arm | `arm_cat_wickett` | `cat_name` | core | `wickett` | 0/16 | PASS | — |
| register_arm | `arm_sister_holvana` | `sibling_name` | core | `holvana` | 0/16 | PASS | — |
| register_arm | `arm_town_fenwyck` | `hometown` | core | `fenwyck` | 0/16 | PASS | — |
| register_arm | `arm_year_1953` | `birth_year` | core | `1953` | 0/16 | PASS | — |

## Known Close-Call Triggers (pre-registered)

The frozen base's own prior-mass answer per slot, measured on `convbase_slim.pt` and
recorded in 14-CONTEXT D-01. These were identified **BEFORE the candidate pools were
authored** — they are pre-registered triggers, not discoveries made during this run. A
candidate colliding with one of them is a close-call rejection waiting to happen; start
the human review here.

| slot | measured base prior |
| --- | --- |
| `occupation` | `cop`, `college student` |
| `hometown` | `the country` |
| `favorite_color` | `red` |
| `pet_name` | `rose` |

## Close-Call Rejections (D-03, human-recorded)

| fact | slot | quoted base completion | reason |
| --- | --- | --- | --- |
| | | | |

Every close-call rejection **MUST quote the specific base completion text that triggered
it**. A rejection without a quote is not a valid rejection: this tier exists for the
failure mode exact-match structurally cannot see — semantic proximity (same category,
adjacent plausible value, right slot) that would make a reader suspect the base half-knew
the answer. It is a documented judgment, never a silent one. Leave the table empty if
nothing is rejected on close-call grounds.

## Survivor Count

Mechanical-floor survivors only — subtract any close-call rejections recorded above
before reading this against the targets.

| pool | core survivors | core target | soft survivors | soft target | total | total target |
| --- | --- | --- | --- | --- | --- | --- |
| candidate | 16/16 | 5-8 (D-05) | 6/6 | 2-3 (D-05) | 22 | 5-10 (ROADMAP) |
| calibration | 10/10 | n/a | 0/0 | n/a | 10 | >= 6 (D-09.1) |
| register_arm | 6/6 | n/a | 0/0 | n/a | 6 | >= 4 (D-21.1) |

The `candidate` pool is deliberately over-authored (two candidates per slot) so attrition
can land inside D-05's 5-8 core /
2-3 soft composition across DISTINCT slots. If it falls
short, that is exactly the information D-06 exists to surface before the set is locked —
say so in the verdict rather than relaxing the filter.

## Verdict

PENDING — user decision at checkpoint.
