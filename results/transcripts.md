# PersonaCore — Conversational-Base Transcripts (TUNE-01)

> These transcripts are REPRESENTATIVE, not cherry-picked: episodes are drawn from
> the held-out PersonaChat valid split with a seeded rng (default_rng(1337)). Each
> prompt is the episode's `encode_dialogue` id sequence (persona + first user turn),
> truncated to end at the `<|assistant|>` id — never a hand-formatted string — so
> prompts tokenize identically to the training bins. Decoding uses
> `stop_ids={8184, 8185}` (eos + `<|user|>`) with dead ids forbidden, 128 new tokens.

## Adherence Proxies (measured over all generations)

- Stop-id termination fraction: **30/30 = 1.00**
- Mid-generation role-token leakage (ids 8185/8186/8187): **1** (expected 0)
- Final masked dialogue val PPL (convbase_best, frozen gate policy): **4.5733** over 270,203 assistant tokens

## Episode 59

**Persona:** i have an economical suv.; i love country music.; i enjoy singers like jason aldea.; i work in retail.

**User:** hello, how are you? i am a feminist.

**Greedy (deterministic):**

> i am good. i am a man of a country country music.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> hello, how are you?

## Episode 115

**Persona:** i spent my childhood around barn animals.; we have had thoroughbreds for ages.; i have interest in the legal system.; the city i am from has a very low population.

**User:** hello. how is it going today?

**Greedy (deterministic):**

> it is going good. its all my favorite.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> it is great here into the world.

## Episode 165

**Persona:** i know how to work with my hands.; my spouse and children are amazing.; i am a father.; i like cocoa flavored products.

**User:** hi, how are you, how is day?

**Greedy (deterministic):**

> i am doing well. i am just reading a book.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i am doing well, just got home from the new york. you?

## Episode 183

**Persona:** i can only somewhat hear.; i show historical artifacts.; i plant flowers.; i love to read.

**User:** hello, how are you doing?

**Greedy (deterministic):**

> i am doing well. just got back from the country.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> hey i am fine and you?

## Episode 193

**Persona:** i am employed at a time keeping shop.; nobody believes that i should be a mechanic.; i usually browse footwear and accessories.; i enjoy browsing stores.; i have very expensive taste in vehicles.

**User:** hello i am 8 years old how old are you?

**Greedy (deterministic):**

> i am 10 years old. i am 20.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> hello. how are you?

## Episode 287

**Persona:** i am the only sister in my family.; my home town is mobile.; i have a schnauzer, and he is my best friend.; i wish i was a single child.; my favorite food is mexican food.

**User:** hello there, how goes it?

**Greedy (deterministic):**

> i am doing well. i am more of a college student.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i am making my food tea, and it is a delicious mexican.

## Episode 388

**Persona:** olive garden is my favorite restaurant.; i love sunny toned shades.; i used to do pole vault.; i go to the gym for long periods of time.; i really like performing handstands and back flips on the balance beam.

**User:** organic food are good for health

**Greedy (deterministic):**

> i am a musician and i am a musician.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i wish i was really good but i am also very thoughtful.

## Episode 459

**Persona:** i like country music boy bands.; we would always go to 6 flags on vacation when we were kids.; while on school, i applied myself to the career i sought.; i am lee brice.

**User:** hi how are you doing? whats new?

**Greedy (deterministic):**

> i am good, just got back from a college.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i am good, how about yourself?

## Episode 534

**Persona:** liquor is the worst thing i can imagine.; previously, my dad was a tradesman.; nothing beats a hot cup of java.; i despise shades in the rose family.; i exercise for fun.

**User:** good afternoon? how are you?

**Greedy (deterministic):**

> i am doing well. i am just reading a book.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i am doing well, thank you! i am just hanging out of classes. you?

## Episode 538

**Persona:** i am the only sister in my family.; my favorite food is mexican food.; i wish i was a single child.; i have a schnauzer, and he is my best friend.

**User:** hi i am george how are you?

**Greedy (deterministic):**

> i am good. i am just chilling my own children.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> hello, i am depressed with my sons, i like to make loops with my brand new job<|assistant|>what are your job in?

## Episode 718

**Persona:** i have lived a century.; i think i am immortal sometimes.; i did not have a tv growing up.; i might be young but i can lift very heavy weights.; i enjoy alcohol and being in nature.

**User:** hello! how are you today!

**Greedy (deterministic):**

> i am doing well. just got back from a rock college.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> oh wow, i am fine. what are your hobbies?

## Episode 866

**Persona:** i work with music and i dream of success.; i am a janitor at a school.; i am skilled in two musical instruments.; my goals seem far fetched to my mom.

**User:** hello, how are you this morning?

**Greedy (deterministic):**

> i am doing well, just got back from the movies.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i am doing good, just got back from the moview, just doing my cool job.

## Episode 870

**Persona:** i like hard rock.; krispy kreme is the best snack ever.; my friends and i enjoy video games.; i love dungeons and dragons.

**User:** hi. how is everything going?

**Greedy (deterministic):**

> it is going good. i am more of a country music than myself.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> great! it is going to be a social person, i like excellent.

## Episode 912

**Persona:** i like big dogs better than smaller ones.; i do not like orange.; i do not like creepy crawly things.; my dad is famous.; i work for as a mail carrier.

**User:** hi! how are you today?

**Greedy (deterministic):**

> i am doing well. just got back from my college.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i am great i am getting a new carriber though. you?

## Episode 939

**Persona:** i am vegan.; i am a college finance graduate.; i closed on a home not too long ago.; i like to experience music live.; i have a spouse and a couple of children.

**User:** hi, want to get to know each other

**Greedy (deterministic):**

> it is nice to meet you, i am more of a college student.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> oh that sounds good! i would like to be a vegan
