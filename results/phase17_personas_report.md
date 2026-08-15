# Phase 17 Persona Pre-Flight Report (ISO-01 / D-04 / D-05 / D-06)

> **What these numbers are:** a PRE-TEACHING measurement of the FROZEN, UN-ADAPTED base —
> how much prior mass it already carries on each of the 24 minted persona values, probed
> through `build_recall_prompt`, the SAME call the scoring harness and the demo make,
> with the fixture's OWN held-out questions for each value's slot (RESEARCH F-07). Plus
> the tokenizer census of every value, measured by direct `encode`/`decode`.
> **What they are not:** a recall measurement — nothing has been taught yet and no
> Phase 17 adapter exists. They are also **checkpoint-specific**: these priors belong to
> this checkpoint at this point in training and have no meaning as a standing invariant.
> A future checkpoint requires a FRESH gated measurement, not a test re-run. The
> permanent CPU regression test (`tests/test_phase17_personas.py`) covers the tokenizer
> half only.

## Base

- Checkpoint: `checkpoints/convbase_slim.pt`, read through `personacore.checkpoint.load_slim` (`weights_only=True`, the restricted unpickler)
- Fingerprint: git `04e724c67033f9a2ed8b705a07ad025c867a18c5`, step `4000`, val_loss `1.5235939979553224`
- Architecture: 6 layers x 6 heads, n_embd 384, vocab_size 8192

**No adapter was injected and no adapter weights were loaded.** The model probed below is
the base checkpoint as exported, with nothing attached to it. This is the load-bearing
property of the whole report: a model carrying a trained adapter is LESS likely than the
base to emit these 24 values, so probing one would return a clean gate for the wrong
reason and this document would be evidence about a different model. It is pinned
structurally by `tests/test_phase17_personas.py`'s un-adapted-base scan, which
AST-asserts that no function in the driver reaches an adapter path at all.

## Tokenizer Census

The transcribed `VALUE_TOKEN_CENSUS` literal beside the live re-measurement against the
frozen `artifacts/tokenizer.json`. They are two different things on purpose: the literal
is the expectation the budget-parity proof reads, and a divergence means either the
frozen tokenizer changed or a value was edited after it was measured — both invalidate
the claim that this material fits `RECALL_MAX_NEW_TOKENS = 48`.

| persona | id | slot | value | transcribed | live | round-trip | agrees |
| --- | --- | --- | --- | --- | --- | --- | --- |
| persona_a | `p17_a_person_name` | `person_name` | `thessaly` | 7 | 7 | exact | yes |
| persona_a | `p17_a_pet_name` | `pet_name` | `nyxen` | 3 | 3 | exact | yes |
| persona_a | `p17_a_cat_name` | `cat_name` | `quorra` | 5 | 5 | exact | yes |
| persona_a | `p17_a_sibling_name` | `sibling_name` | `myrrhen` | 6 | 6 | exact | yes |
| persona_a | `p17_a_hometown` | `hometown` | `brambleton` | 8 | 8 | exact | yes |
| persona_a | `p17_a_street` | `street` | `sablewind` | 7 | 7 | exact | yes |
| persona_a | `p17_a_birth_year` | `birth_year` | `1906` | 4 | 4 | exact | yes |
| persona_a | `p17_a_house_number` | `house_number` | `5063` | 4 | 4 | exact | yes |
| persona_b | `p17_b_person_name` | `person_name` | `drovik` | 6 | 6 | exact | yes |
| persona_b | `p17_b_pet_name` | `pet_name` | `fenmark` | 5 | 5 | exact | yes |
| persona_b | `p17_b_cat_name` | `cat_name` | `vellamo` | 4 | 4 | exact | yes |
| persona_b | `p17_b_sibling_name` | `sibling_name` | `orlenne` | 6 | 6 | exact | yes |
| persona_b | `p17_b_hometown` | `hometown` | `hollowmere` | 7 | 7 | exact | yes |
| persona_b | `p17_b_street` | `street` | `wexford` | 7 | 7 | exact | yes |
| persona_b | `p17_b_birth_year` | `birth_year` | `1941` | 4 | 4 | exact | yes |
| persona_b | `p17_b_house_number` | `house_number` | `2287` | 4 | 4 | exact | yes |
| persona_c | `p17_c_person_name` | `person_name` | `kessendra` | 6 | 6 | exact | yes |
| persona_c | `p17_c_pet_name` | `pet_name` | `grindlow` | 6 | 6 | exact | yes |
| persona_c | `p17_c_cat_name` | `cat_name` | `ostrick` | 6 | 6 | exact | yes |
| persona_c | `p17_c_sibling_name` | `sibling_name` | `vorwick` | 6 | 6 | exact | yes |
| persona_c | `p17_c_hometown` | `hometown` | `duskvale` | 6 | 6 | exact | yes |
| persona_c | `p17_c_street` | `street` | `crandwell` | 6 | 6 | exact | yes |
| persona_c | `p17_c_birth_year` | `birth_year` | `1893` | 4 | 4 | exact | yes |
| persona_c | `p17_c_house_number` | `house_number` | `9614` | 4 | 4 | exact | yes |

Ceiling: `MAX_VALUE_TOKENS = 8`. Measured maximum: 8. Rows diverging from the transcribed literal: **0**.

## Guessability

Every completion the un-adapted base produced, verbatim. Per slot: 13 held-out questions x 4 draws (greedy + 3 warm) = 52 completions, cached per question
and shared across the three personas' values for that slot — the base is stateless and
the prompt is the same id sequence, so the three values are provably judged against ONE
set of completions rather than three independently generated ones.

The mechanical half of the rule is `phase14_factset.exact_match_clean`: a value passes
iff its normalized form appears in ZERO of the completions. The boundary is unforgiving —
ONE containment out of 52 is a failure. **The close-call tier is the human judgment this
report exists for**: a value the base does not produce exactly but comes semantically
close to is a value whose off-diagonal cell would later be ambiguous, and only a reader
of the quoted text below can see that.

### Slot `person_name` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_person_name` | `thessaly` | 0/52 | clean=True |
| persona_b | `p17_b_person_name` | `drovik` | 0/52 | clean=True |
| persona_c | `p17_c_person_name` | `kessendra` | 0/52 | clean=True |

Completions, verbatim:

- Q `the name you go by is` — prompt = 14 ids
  - greedy: `i am just a cold indian cold if i cou`
  - warm 1: `i live in one of my family. i do not want to compet`
  - warm 2: `i am employed by the glass, so i need to be co`
  - warm 3: `i am a you? i work at a dease part of jazz`
- Q `finish this sentence. the name you go by is` — prompt = 24 ids
  - greedy: `i am sorry to hear that. i am just a colleg`
  - warm 1: `well, that is why i teach..`
  - warm 2: `thanks... i guess that i am so busy on be`
  - warm 3: `wow that must be awesome`
- Q `complete it for me: the name you go by is` — prompt = 28 ids
  - greedy: `i am sorry to hear that. i am just a colleg`
  - warm 1: `awesome.... that is cool. i am terrible at a hu`
  - warm 2: `dyes. i am in bed i have a sleeper tons.`
  - warm 3: `it really yours?`
- Q `do you remember what your friends call you?` — prompt = 37 ids
  - greedy: `i am a mother of a college college.`
  - warm 1: `gotcha, you? i am into school`
  - warm 2: `yes. i do. my pitbull is the best color of`
  - warm 3: `i was just call me! i was down walking in the woods.`
- Q `can you recall what your friends call you?` — prompt = 34 ids
  - greedy: `i am a mother of that. i am a mother of th`
  - warm 1: `i am told i escaped from a farm. i really like them to`
  - warm 2: `yeah my mom was more close to my girlfri`
  - warm 3: `no but i am a few years old.`
- Q `have you forgotten what your friends call you?` — prompt = 37 ids
  - greedy: `i am sorry to hear that. i am allergic to my`
  - warm 1: `no, i have never seen something about you`
  - warm 2: `hi. i am into sports of america, helping m`
  - warm 3: `i do not think i am wrong. they are not fine to h`
- Q `if someone asked you what your friends call you, what would you say?` — prompt = 54 ids
  - greedy: `i am a mother of a college college. i am`
  - warm 1: `nice. i am married. i would rather watch `
  - warm 2: `that would be very angela. thank you for askin`
  - warm 3: `i am charlier, what do you do for a living?`
- Q `suppose a friend asked what your friends call you — what would you tell them?` — prompt = 61 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `they are our favorite band`
  - warm 2: `i really like to tell everyone not to worry about p`
  - warm 3: `happy i love to read, mine is a modest newsp`
- Q `how would you answer if a stranger asked what your friends call you?` — prompt = 50 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am in a new yellow corvette. my mom was a po`
  - warm 2: `i am very enthusiastic. my dad worked in a protec`
  - warm 3: `i am making a significated patch constr`
- Q `what is your name?` — prompt = 16 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am a dog person so i read the money.`
  - warm 2: `a i am the best. i love drawing things too`
  - warm 3: `i am 39 of that i play video games`
- Q `what should i call you?` — prompt = 20 ids
  - greedy: `i am a college student`
  - warm 1: `i am just the since i own`
  - warm 2: `i am really into basketball fantastic blast and a p`
  - warm 3: `i am fine. do you have any pets?`
- Q `tell me your name.` — prompt = 17 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i know what do you do for a living.`
  - warm 2: `awesome. i am sorry to hear that`
  - warm 3: `yes. i have a dog and i have a dog.`
- Q `who am i talking to?` — prompt = 18 ids
  - greedy: `i am a mort of music construction. i`
  - warm 1: `nope but i am talking to my husband with the `
  - warm 2: `i am really open.... how long have you do not k`
  - warm 3: `i am a college on youtube now`

### Slot `pet_name` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_pet_name` | `nyxen` | 0/52 | clean=True |
| persona_b | `p17_b_pet_name` | `fenmark` | 0/52 | clean=True |
| persona_c | `p17_c_pet_name` | `grindlow` | 0/52 | clean=True |

Completions, verbatim:

- Q `your dog goes by the name` — prompt = 15 ids
  - greedy: `i have a dog. i love dogs.`
  - warm 1: `i think i am a car college. i am a bit stranger`
  - warm 2: `what do you do for a living<|assistant|>you have a lot of kid`
  - warm 3: `yea. he is my best friend.`
- Q `finish this sentence. your dog goes by the name` — prompt = 27 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `no on the other side. he was restless.`
  - warm 2: `i do! its a really rewarding beatbucks. what`
  - warm 3: `wow! i like that trail<|assistant|>stocks, they are never fun. `
- Q `complete it for me: your dog goes by the name` — prompt = 31 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `what is your dog? i love it.`
  - warm 2: `what else do you like to do?`
  - warm 3: `nice. i do not have a dog at all.`
- Q `do you remember what your dog is called?` — prompt = 31 ids
  - greedy: `i am a cop, i am a cop, i am a cop`
  - warm 1: `no people but i am a person<|assistant|>i cant seem to ea`
  - warm 2: `not really, he is a chubby further`
  - warm 3: `i am more of it and he is never missed`
- Q `can you recall what your dog is called?` — prompt = 28 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `i can recommend one of my dogs, so i have a new dog`
  - warm 2: `i wish i could be alone if i have a dog. what`
  - warm 3: `i live in pepperoni when i was young. i was a picky`
- Q `have you forgotten what your dog is called?` — prompt = 31 ids
  - greedy: `i am sorry. i am allergic to my dog.`
  - warm 1: `i am sorry. my best friend is sad.`
  - warm 2: `no it was because he was a good person<|assistant|>what do yo`
  - warm 3: `i just wanted to have one. i love him.`
- Q `if someone asked you what your dog is called, what would you say?` — prompt = 48 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `oh okay. i am actually called professional tre`
  - warm 2: `i do not know if i should get ready to help `
  - warm 3: `i am a technada. that is a lot.`
- Q `suppose a friend asked what your dog is called — what would you tell them?` — prompt = 55 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `my dog is a wild animal. his name is good.`
  - warm 2: `i love the ones though. you married?`
  - warm 3: `pretty fun, would you like meat? i like che`
- Q `how would you answer if a stranger asked what your dog is called?` — prompt = 44 ids
  - greedy: `i am a cop, i am a cop, i am a cop.`
  - warm 1: `i would rather make it rather avacuument`
  - warm 2: `i do not know but i love him too`
  - warm 3: `how many dogs do you think?`
- Q `what is your dog's name?` — prompt = 19 ids
  - greedy: `i am a cop. i am a cop.`
  - warm 1: `i like to eat. where i am.`
  - warm 2: `i am not very nice. but i am a big fan of clothing.`
  - warm 3: `my cats are 5. i have no room violin. i am in t`
- Q `what do you call your dog?` — prompt = 22 ids
  - greedy: `i am a cop, i am a cop. i am a cop.`
  - warm 1: `well i am making my own pastory`
  - warm 2: `i love dogs and cars. i miss dogs`
  - warm 3: `what do you have?`
- Q `tell me your dog's name.` — prompt = 20 ids
  - greedy: `i am a cop. i am a cop. i am a cop.`
  - warm 1: `i am alright only its hard. he is cute.`
  - warm 2: `no, i do. i am allergic to pet my. my mo`
  - warm 3: `i am from the state of the state of the rights. he is t`
- Q `does your dog have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a cop. i am a cop.`
  - warm 1: `i like music`
  - warm 2: `i had a dog too, but they did not get a name`
  - warm 3: `yes, i am a dog, and i like cheese. i have a thing`

### Slot `cat_name` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_cat_name` | `quorra` | 0/52 | clean=True |
| persona_b | `p17_b_cat_name` | `vellamo` | 0/52 | clean=True |
| persona_c | `p17_c_cat_name` | `ostrick` | 0/52 | clean=True |

Completions, verbatim:

- Q `your cat goes by the name` — prompt = 15 ids
  - greedy: `i have a cat. i have a cat.`
  - warm 1: `i have a cat, i own a dog. i cannot wait to go home.`
  - warm 2: `yes i did<|assistant|>i thought of college with m`
  - warm 3: `i play it with many people<|assistant|>what do you play for?`
- Q `finish this sentence. your cat goes by the name` — prompt = 27 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `yes i love exploring but i like to travel`
  - warm 2: `a does that sound nice. you should change you`
  - warm 3: `well the names your dog is part of this regular dog!!`
- Q `complete it for me: your cat goes by the name` — prompt = 31 ids
  - greedy: `i am a college student`
  - warm 1: `i am sure it is nice to hear others`
  - warm 2: `i do not eat any more. i just postively b`
  - warm 3: `that is a long name. i have never been on the mountain`
- Q `do you remember what your cat is called?` — prompt = 31 ids
  - greedy: `i am a college student`
  - warm 1: `i do not. i love cats, especially when they grow `
  - warm 2: `i am also from california, i am a manager man`
  - warm 3: `i do not know. i am a big, strong person`
- Q `can you recall what your cat is called?` — prompt = 28 ids
  - greedy: `i am a college student`
  - warm 1: `yes, i am a cop of people mostly, all abo`
  - warm 2: `well i love cats, its all in it.`
  - warm 3: `something does not have your cat`
- Q `have you forgotten what your cat is called?` — prompt = 31 ids
  - greedy: `i am a college student`
  - warm 1: `no i have a cat, now that i have one.`
  - warm 2: `i am sorry. what do you like?`
  - warm 3: `i would rather sell meatloaf my mouse, `
- Q `if someone asked you what your cat is called, what would you say?` — prompt = 48 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a child, not painful. i am just runn`
  - warm 2: `hope sounds very fine. do you?`
  - warm 3: `that is a deal, i do not know. do you have a`
- Q `suppose a friend asked what your cat is called — what would you tell them?` — prompt = 55 ids
  - greedy: `i am a college student`
  - warm 1: `nice. i am a giant chef. i am a nurse for m`
  - warm 2: `that could be one, i am trying to keep any`
  - warm 3: `my cats are on beautiful but i like to go everywhere`
- Q `how would you answer if a stranger asked what your cat is called?` — prompt = 44 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a professional worker in a red mistake onl`
  - warm 2: `i am a musician. but i used to be. tell me somet`
  - warm 3: `i am a guy i love cats.`
- Q `what is your cat's name?` — prompt = 19 ids
  - greedy: `i am a college student`
  - warm 1: `it is my favorite movie`
  - warm 2: `i am mostly married. but i am often away from`
  - warm 3: `my name is name and mine is a fashion daughter`
- Q `what do you call your cat?` — prompt = 22 ids
  - greedy: `i am a college student`
  - warm 1: `how about you? i am a doctor, and you?`
  - warm 2: `i do not like cars so i just miss my son lol`
  - warm 3: `i do enjoy fishing`
- Q `tell me your cat's name.` — prompt = 20 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i just got a chewererer just a better job. do `
  - warm 2: `the cats do you like music`
  - warm 3: `do you like music? i do.`
- Q `does your cat have a name?` — prompt = 18 ids
  - greedy: `i do not. i am a college at all.`
  - warm 1: `no i am not very good anymore`
  - warm 2: `yes, i love cats. they are my favorite band`
  - warm 3: `yes, i have two cats. who is yours?`

### Slot `sibling_name` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_sibling_name` | `myrrhen` | 0/52 | clean=True |
| persona_b | `p17_b_sibling_name` | `orlenne` | 0/52 | clean=True |
| persona_c | `p17_c_sibling_name` | `vorwick` | 0/52 | clean=True |

Completions, verbatim:

- Q `your sister goes by the name` — prompt = 18 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i never see my car`
  - warm 2: `whats color is that sounds fun.`
  - warm 3: `yes that is nice. i have two, she is a princess.`
- Q `finish this sentence. your sister goes by the name` — prompt = 30 ids
  - greedy: `i am sorry to hear that. i am just moved to the `
  - warm 1: `my sister is walking married in a marriage.`
  - warm 2: `yes i really know my philose. i have two din`
  - warm 3: `nice. i am bored.`
- Q `complete it for me: your sister goes by the name` — prompt = 34 ids
  - greedy: `i am sorry to hear that. i am just moved to the `
  - warm 1: `my sister my favorite is my dog.`
  - warm 2: `i am a bartender with the paper in chicago`
  - warm 3: `where is your name?`
- Q `do you remember what your sister is called?` — prompt = 34 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `no, i live in caspos. i do not read me.`
  - warm 2: `i do not know either. but i love it`
  - warm 3: `it was hard to read, but not since a long time ago`
- Q `can you recall what your sister is called?` — prompt = 31 ids
  - greedy: `i am a child, i am a child`
  - warm 1: `i am on a crazy, my kids love my motorcyc`
  - warm 2: `no! i do not know what she wants off similar`
  - warm 3: `her not on anyway the most of yourself<|assistant|>well`
- Q `have you forgotten what your sister is called?` — prompt = 34 ids
  - greedy: `i am sorry to hear that. i am allergic to hear`
  - warm 1: `i do not have my sister. whats yours?`
  - warm 2: `i have not seen any college junk either.`
  - warm 3: `alaf. i am a nurse and i work in my persona`
- Q `if someone asked you what your sister is called, what would you say?` — prompt = 51 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `well, it is almost lying when i is that with`
  - warm 2: `no people do not do that. anyway.`
  - warm 3: `yes they are dependent in charge things she did k`
- Q `suppose a friend asked what your sister is called — what would you tell them?` — prompt = 58 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i would though`
  - warm 2: `my mom was covering her when i was old and often work`
  - warm 3: `i sound cool, and i watch my piano. i love tha`
- Q `how would you answer if a stranger asked what your sister is called?` — prompt = 47 ids
  - greedy: `i am a college stranger. i am a college student`
  - warm 1: `i am a college student<|assistant|>that is awesome. i am c`
  - warm 2: `well, its a chicken still in a caliform`
  - warm 3: `how are you doing today`
- Q `what is your sister's name?` — prompt = 22 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am not sure, it is very pretty intelligent for me`
  - warm 2: `i love playing pubbles, mysterious actions! m`
  - warm 3: `its my birthday, her name is cop`
- Q `what do you call your sister?` — prompt = 25 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am also into scientist other things, not a re`
  - warm 2: `i love though. do you know how to help you?`
  - warm 3: `she is a doctor. doctors and love it`
- Q `tell me your sister's name.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `no, not sure what i like. i just watch footb`
  - warm 2: `i live in the bathroom, i love baths, and all my fav`
  - warm 3: `i am a college for her...... no, i am a ve`
- Q `does your sister have a name?` — prompt = 21 ids
  - greedy: `no, i am not. i am a child.`
  - warm 1: `yes, she would need a name, yes, i just ret`
  - warm 2: `yes, she is my favorite.`
  - warm 3: `i am looking for a new name?`

### Slot `hometown` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_hometown` | `brambleton` | 0/52 | clean=True |
| persona_b | `p17_b_hometown` | `hollowmere` | 0/52 | clean=True |
| persona_c | `p17_c_hometown` | `duskvale` | 0/52 | clean=True |

Completions, verbatim:

- Q `the town you live in is` — prompt = 16 ids
  - greedy: `i live in college its my favorite color`
  - warm 1: `it is true. i like to go in the shower on my face car`
  - warm 2: `i live near the river`
  - warm 3: `do you drive the car for a while?`
- Q `finish this sentence. the town you live in is` — prompt = 26 ids
  - greedy: `i am sorry to hear that. i am always current`
  - warm 1: `no problem. i am always alone in spring and i`
  - warm 2: `its a van. i do not know how to be a doctor.`
  - warm 3: `its a difficult job but i just made s`
- Q `complete it for me: the town you live in is` — prompt = 30 ids
  - greedy: `i am sorry to hear that. i am sorry to hear th`
  - warm 1: `that is awesome. do you like country music?`
  - warm 2: `how nice that is your morning!`
  - warm 3: `i wish i could do it<|assistant|>i do not have much. d`
- Q `do you remember where you live?` — prompt = 26 ids
  - greedy: `i live in the country i remember`
  - warm 1: `she is me when i was young. you?`
  - warm 2: `i am always with course<|assistant|>i think you are s`
  - warm 3: `no i can remember`
- Q `can you recall where you live?` — prompt = 23 ids
  - greedy: `i live in the mountains. i am a mountainstatio`
  - warm 1: `i live in the truck. because i do not get to work`
  - warm 2: `its my home, that is my home too.`
  - warm 3: `wow, i am all in videos of my friends.`
- Q `have you forgotten where you live?` — prompt = 26 ids
  - greedy: `i am in the military. i am in the military.`
  - warm 1: `its going to express soon. where do you live?`
  - warm 2: `i have two more teen than 1. what about you`
  - warm 3: `i am experienced to teach my sons.`
- Q `if someone asked you where you live, what would you say?` — prompt = 43 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `that would be great. what do you like to do?`
  - warm 2: `wow, i am into confidence and watching anime`
  - warm 3: `i am a stay at home of trying to find it a trip in m`
- Q `suppose a friend asked where you live — what would you tell them?` — prompt = 50 ids
  - greedy: `i live in the country i mostly`
  - warm 1: `hid as i thought about yourself?`
  - warm 2: `pie sometimes, i enjoy experience with m`
  - warm 3: `who came to spoil their sports? i just moved `
- Q `how would you answer if a stranger asked where you live?` — prompt = 39 ids
  - greedy: `i live in the country i mostly`
  - warm 1: `about your signative would be the best. `
  - warm 2: `i am in high school, my father is retired.`
  - warm 3: `i was busy trying to find my own mushroom just like`
- Q `where do you live?` — prompt = 15 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `yes, we live at the country once.`
  - warm 2: `i am in a very college to this weekend i get the golden re`
  - warm 3: `i live in a spanish for the south. i live in the beat. yo`
- Q `what town do you live in?` — prompt = 20 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i live in spring, i am a morning person.`
  - warm 2: `yes, i do not eat anymore`
  - warm 3: `i am not sure yet i just like my mom`
- Q `tell me the name of your town.` — prompt = 23 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i have a diet. i would move to a diet of with a `
  - warm 2: `no people. i can make me happy, i love to sing.`
  - warm 3: `i do not really like my parents. i have to vacati`
- Q `what is your hometown called?` — prompt = 21 ids
  - greedy: `i am a college student`
  - warm 1: `i just got back from chicago`
  - warm 2: `i am in france but i love traveling`
  - warm 3: `hi, i am attending to run before cheering`

### Slot `street` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_street` | `sablewind` | 0/52 | clean=True |
| persona_b | `p17_b_street` | `wexford` | 0/52 | clean=True |
| persona_c | `p17_c_street` | `crandwell` | 0/52 | clean=True |

Completions, verbatim:

- Q `the street you live on is` — prompt = 17 ids
  - greedy: `i live in the country i live in the country. i live in the`
  - warm 1: `no its because i love the country, its my hob`
  - warm 2: `i beat it at my idea`
  - warm 3: `i live in my house and i live in the country yesterday`
- Q `finish this sentence. the street you live on is` — prompt = 27 ids
  - greedy: `i live in the country i live in the country.`
  - warm 1: `i do not like boston rock, but i get my own `
  - warm 2: `wow i am a baby aside from swift. what do y`
  - warm 3: `are you in my spare time`
- Q `complete it for me: the street you live on is` — prompt = 31 ids
  - greedy: `i am sorry to hear that. i am just a car of `
  - warm 1: `i wish you could hear, but you have a job in`
  - warm 2: `i am only 3 and that is why i get to surround ot`
  - warm 3: `i wish i could. it is pretty hard. my favor`
- Q `do you remember what street your house is on?` — prompt = 33 ids
  - greedy: `i am a college street major`
  - warm 1: `i do not really work. my wife has more than `
  - warm 2: `it is a good place to stay.`
  - warm 3: `i do not but i would disappoint myself.`
- Q `can you recall what street your house is on?` — prompt = 30 ids
  - greedy: `i am a college street major`
  - warm 1: `i work for my lizards it is my favorite.`
  - warm 2: `i am just turning 50 years.`
  - warm 3: `well it is worth a lot, my mom does not work`
- Q `have you forgotten what street your house is on?` — prompt = 33 ids
  - greedy: `i am sorry. i am sorry to hear that.`
  - warm 1: `no, but i want to see how it seems like a hospi`
  - warm 2: `it is hard would be held to each street and i am a `
  - warm 3: `i worked at it. its a porticipation this we`
- Q `if someone asked you what street your house is on, what would you say?` — prompt = 50 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `i like to sing, but i do not have much friends.`
  - warm 2: `i am more of a marathonic and make me perso`
  - warm 3: `i would be calm and make sure your students are li`
- Q `suppose a friend asked what street your house is on — what would you tell them?` — prompt = 57 ids
  - greedy: `i am a college street major`
  - warm 1: `thank you! my 20 year olds and i remember the `
  - warm 2: `i like to travel the world to the river for traveling, i h`
  - warm 3: `yes i do not know who you are doing`
- Q `how would you answer if a stranger asked what street your house is on?` — prompt = 46 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am trying to eat some cheesecake without a stu`
  - warm 2: `i could consider it..... i have to work`
  - warm 3: `its a six collection. how was i doing?`
- Q `what street do you live on?` — prompt = 21 ids
  - greedy: `i live in the country mountains and i am also a m`
  - warm 1: `i live in the middle of the summer.`
  - warm 2: `that is exactly nice`
  - warm 3: `you got a lot of trade, as i am a manager at a m`
- Q `what is the name of your street?` — prompt = 22 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `was it color blue. do you like music?`
  - warm 2: `it is a cloud, and i like to get to college it, b`
  - warm 3: `yes, it is my favorite color of shirts`
- Q `tell me your street name.` — prompt = 20 ids
  - greedy: `i am a college streeter. i am a college streeter`
  - warm 1: `where do you live? i am in the elevator.`
  - warm 2: `i really like to see the girls, i like the fairy teac`
  - warm 3: `i am not sure i make a lot of money my own p`
- Q `which road is your house on?` — prompt = 23 ids
  - greedy: `i am just a college man. i am a college st`
  - warm 1: `i am expecting college at a big farm.`
  - warm 2: `i know mine is my favorite place to drive.`
  - warm 3: `i am just cold i sneeze. yourself?`

### Slot `birth_year` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_birth_year` | `1906` | 0/52 | clean=True |
| persona_b | `p17_b_birth_year` | `1941` | 0/52 | clean=True |
| persona_c | `p17_c_birth_year` | `1893` | 0/52 | clean=True |

Completions, verbatim:

- Q `the year of your birth is` — prompt = 19 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i have a new life, i have a new country but i w`
  - warm 2: `i love the dog and my children`
  - warm 3: `well, did you know what the mystery is?`
- Q `finish this sentence. the year of your birth is` — prompt = 29 ids
  - greedy: `i am sorry to hear that. i am also a colleg`
  - warm 1: `well that is awesome, that is really cool. what a`
  - warm 2: `sometimes it is my favorite`
  - warm 3: `yes the most fun. i have two kids, one more th`
- Q `complete it for me: the year of your birth is` — prompt = 33 ids
  - greedy: `i am sorry to hear that. i am just moved to a `
  - warm 1: `what college do you like to bake?`
  - warm 2: `yes it will help my friends in the mornings`
  - warm 3: `thanks!!!!!! whats your favorite sea`
- Q `do you remember when you were born?` — prompt = 29 ids
  - greedy: `i am a mother of that. i am a mother of th`
  - warm 1: `well i do. i do not enjoy movies eithe`
  - warm 2: `nope i am male.`
  - warm 3: `horseas are a good hiding spot`
- Q `can you recall when you were born?` — prompt = 26 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i have many blonde parents, i really do not have m`
  - warm 2: `yes, it must be the best for college meal`
  - warm 3: `yes, i am a snake.`
- Q `have you forgotten when you were born?` — prompt = 29 ids
  - greedy: `i am sorry to hear that. i am allergic to my`
  - warm 1: `i could have retired yoga class`
  - warm 2: `no i have 5, i made 2 years later.`
  - warm 3: `not really so cute`
- Q `if someone asked you when you were born, what would you say?` — prompt = 46 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i think that would be great to get your own.`
  - warm 2: `i am a whole family`
  - warm 3: `i am a musician, and when i was a chef man.`
- Q `suppose a friend asked when you were born — what would you tell them?` — prompt = 53 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `how much do you make it?`
  - warm 2: `i tell them what type of each friend my grandki`
  - warm 3: `one day my favorite friend was a man, she was born`
- Q `how would you answer if a stranger asked when you were born?` — prompt = 42 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am on a very dirty stage. its my parents bor`
  - warm 2: `i do, but i have to look into your own public c`
  - warm 3: `yes i did not know. that is why i should he`
- Q `what year were you born?` — prompt = 20 ids
  - greedy: `i am a college student<|assistant|>i am a college student`
  - warm 1: `i am fashion and you were on your bed or twins`
  - warm 2: `i am mostly just watching tv on my body.`
  - warm 3: `nope, i am sorry to hear about that.<|assistant|>i wish`
- Q `in what year were you born?` — prompt = 21 ids
  - greedy: `i am a mother of this year. i am a mother of`
  - warm 1: `well i work at best. do you have any children?`
  - warm 2: `i am sorry to hear that<|assistant|>what do you do for a`
  - warm 3: `i am employed a pet i like that<|assistant|>i born in the m`
- Q `tell me the year you were born.` — prompt = 23 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `nice. i am not a bad idea. my son has a c`
  - warm 2: `i like fiericians. its good to me.`
  - warm 3: `i usually help clean my back back.`
- Q `which year is your birth year?` — prompt = 24 ids
  - greedy: `i am a child. i am a child.`
  - warm 1: `my girl is fine. are you single?`
  - warm 2: `my job is the extraorder of the city.`
  - warm 3: `i have not heard of it. i do not eat much `

### Slot `house_number` — 13 questions, 52 completions

| persona | id | value | contained | verdict |
| --- | --- | --- | --- | --- |
| persona_a | `p17_a_house_number` | `5063` | 0/52 | clean=True |
| persona_b | `p17_b_house_number` | `2287` | 0/52 | clean=True |
| persona_c | `p17_c_house_number` | `9614` | 0/52 | clean=True |

Completions, verbatim:

- Q `the number on your house is` — prompt = 18 ids
  - greedy: `i am a college student i am a college student`
  - warm 1: `i did not know anything. i met am my best`
  - warm 2: `well it is not as cool as i am still. i even l`
  - warm 3: `i might read a book or sing when i was younger.`
- Q `finish this sentence. the number on your house is` — prompt = 28 ids
  - greedy: `i am sorry to hear that. i am allergic to my`
  - warm 1: `its a good place where i like art and watch a lot of v`
  - warm 2: `i like to cook with the blackber might take you aro`
  - warm 3: `its much more just industry. meant my`
- Q `complete it for me: the number on your house is` — prompt = 32 ids
  - greedy: `i am sorry to hear that. i am just a colleg`
  - warm 1: `do you make the house cooking?`
  - warm 2: `oh cool! i just got a number of last constan`
  - warm 3: `i do not like it. its hard to really run away.`
- Q `do you remember what number your house is?` — prompt = 32 ids
  - greedy: `its always cold if it is cold`
  - warm 1: `it is the real job. i own a coach`
  - warm 2: `yes, that is not a justace color.`
  - warm 3: `i have never had one before`
- Q `can you recall what number your house is?` — prompt = 29 ids
  - greedy: `i am a college at the moment. i am a college at the`
  - warm 1: `i am a special man who does not know`
  - warm 2: `i live in the desert! i love dogs.`
  - warm 3: `yes it is yellow my dad actually`
- Q `have you forgotten what number your house is?` — prompt = 32 ids
  - greedy: `i am sorry. i am sorry to hear that.`
  - warm 1: `nope. about to start a convertible dinner after `
  - warm 2: `i love to drink, and i would rather like to move.`
  - warm 3: `i work at a computer band`
- Q `if someone asked you what number your house is, what would you say?` — prompt = 49 ids
  - greedy: `i am a college at a college college. i am`
  - warm 1: `walking on the path it eats everything`
  - warm 2: `that is just yourself?`
  - warm 3: `i do not know if i can i take care of it`
- Q `suppose a friend asked what number your house is — what would you tell them?` — prompt = 56 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `how did you know it was? i knew it was a wo`
  - warm 2: `super where to go`
  - warm 3: `sounds right! i know mines if i ever go`
- Q `how would you answer if a stranger asked what number your house is?` — prompt = 45 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `no i am going on a number country it is my pa`
  - warm 2: `i love country too, but i do not like music`
  - warm 3: `i do not know if i could tell the driver for t`
- Q `what is your house number?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a currently just meeting my cats`
  - warm 2: `i am a wizard for my grandmother bought me a g`
  - warm 3: `i have a favorite food for grown-ups`
- Q `what number is your house?` — prompt = 19 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `no it is a journaland in the morning sectio`
  - warm 2: `i am a hospital for my garden<|assistant|>awesome, it is my fa`
  - warm 3: `i am a new computer.`
- Q `tell me your house number.` — prompt = 20 ids
  - greedy: `i am also a college student. i am a college`
  - warm 1: `i never want to go on the walk too.`
  - warm 2: `you are afraid to support you will drive you`
  - warm 3: `i like animals, i am listening to animals and learnin`
- Q `which number is on your front door?` — prompt = 28 ids
  - greedy: `i am a college student. i am a college student`
  - warm 1: `i am a lawyer and he does not around<|assistant|>it is nice. i have`
  - warm 2: `hi i am a project. i am a veterinarian.`
  - warm 3: `i am a good singer. i am currently in school`

**24 of 24 values are clean on the mechanical floor.**

## Filters

What each minting screen rejected while the 24 values were authored, over the 34
candidate strings that were measured (transcribed from plan 17-03). A screen that bit
nothing is recorded as such: 'the material passed the gate' must not be read as the gate
having bitten. On the 24 COMMITTED values all four mechanical filters reject nothing —
they were re-run on CPU immediately before the probes above and passed.

| screen | rejected | which |
| --- | --- | --- |
| `filter_token_budget` (<= 8 ids) | 2 of 34 | `vurthwaite` (10 ids), `thornebank` (9 ids) |
| `filter_roundtrip` | 0 of 34 | 34/34 round-tripped exact, 0 dead ids |
| `filter_substring_disjoint` | 0 of 34 | no nesting in minted union forbidden, under the scorer's own `normalize` |
| `filter_absent_from_questions` | 0 of 34 | no candidate appears in any of the 104 fixture questions |
| D-05 neighbour screen (**not** one of the four) | 2 of 34 | `tarrowgate` (edit distance 1 from a locked Phase 14 street value), `1971` (edit distance 1 from a calibration-pool year) |

The D-05 row is the one to carry into the verdict. It is **not** one of the four
mechanical filters and structurally cannot be: substring-disjointness passes a
one-character neighbour happily, because neither of two near-twin values contains the
other. That screen was applied by measurement during authoring and is pinned as a
committed test rather than added as a fifth filter — a new filter belongs in the
pre-registration, and that file is git-ancestry-pinned.

## Provenance

- Driver commit: `1c97a107a11a549754e10a0bea2dc559c702b2ae`
- Base checkpoint fingerprint: git `04e724c67033f9a2ed8b705a07ad025c867a18c5`, step `4000`, val_loss `1.5235939979553224`
- Seed: `1337` — `seed_everything(1337)`, then a per-probe `torch.Generator(1337 + probe_index)`
- Decoding: greedy + 3 warm draws (temperature 0.8, top_p 0.95), `max_new_tokens=32`, `stop_ids=[8184, 8185]`
- `forbid_ids`: sha256 `79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28`, 7645 of 8192 ids masked
- Tokenizer: `artifacts/tokenizer.json` (FROZEN — never retrained)
- Fixture: the binding `results/phase16_recall_sample.json` `core_held_out` tier, 104 questions regrouped into 8 slots
- Probes: 104 unique questions, 416 completions generated
- Device: `{'device': 'mps', 'cc': None, 'torch': '2.7.1'}` · pid `24732` · wall `2.1` min

## Recording The Verdict

These instructions live ABOVE the verdict section, not inside it, and that placement is
load-bearing rather than tidy. `assert_report_not_clobbered` refuses to overwrite this
file once the recorded verdict no longer reads as unrecorded, and it reads the verdict
SECTION — everything from that heading to the end of the file. Boilerplate left sitting
under the heading therefore travels INTO the recorded verdict, and any sentence there
naming the unrecorded state would keep the guard permanently disarmed after a human had
written GO. That is the CR-02 failure class, arriving through the wording of the thing it
protects, so the section below holds the verdict and nothing else.

Replace the whole line below BY HAND with `GO` or `ADAPT` as the first word, followed by
the reasoning and any value you are uneasy about. `ADAPT` replaces named values in
`scripts/phase17_persona_facts.py` — **never** in `scripts/phase17_personas.py`, which is
git-ancestry-pinned — re-measures `VALUE_TOKEN_CENSUS` in the same commit, re-runs the
D-05 neighbour screen, and re-runs this gate. `STOP` escalates. Nothing downstream trains
until the section below reads GO or ADAPT: `teach_persona._require_go_verdict` refuses on
STOP and on an unrecorded verdict alike.

## Verdict

GO — 0/52 containments across all 24 minted values under 4 draws/question, 8 slots.
Semantic read confirms categorical separation: names produce concept-not-token,
person_name produces generic proper nouns (charlier, angela), hometown/street produce
real places, birth_year/house_number produce zero matching-shape numerics. Two known
artifacts noted, neither moving toward minted strings: the college-student attractor
and Phase-13's already-published role-token leakage.

## Addendum — Collateral Dialogue Collapse in the Adapters This Gate Cleared (2026-08-15)

*Appended after the recorded verdict. The `## Verdict` section above is unaltered and still holds the verdict and nothing else.*

This report gates the **material** — it establishes that the un-adapted base cannot already produce the 24 minted values, which is what makes the isolation matrix measurable. It says nothing about the adapters subsequently trained on that material, and a reader should not infer they are usable.

**They are not: the three adapters trained from this GO-gated material are NOT shippable demo substrate.**

Measured in `results/phase17_isolation_report.md`: val loss `persona_a` 14.2507 (**+211.60%**), `persona_b` 14.9068 (**+225.95%**), `persona_c` 15.6121 (**+241.37%**), against Phase 14's shipped `real` arm at **+27.16%**. Cause: Phase 14's `real` arm trained with replay at `REAL_RUN_REPLAY_RATIO = REPLAY_ARM_RATIO = 1.0` (`scripts/teach_persona.py:129,151`), while `run_one_persona_training` calls `train_arm` at the committed default **`replay_ratio=0.0`** — no replay, and replay is what protects dialogue capability.

Recorded, not repaired: changing the recipe after the gate report existed would put code after the report it obeys. The GO verdict above is unaffected — it concerns the base's guessability of the minted values, a measurement taken before any adapter existed.
