# PersonaCore — Phase-13 Retention-Side Samples (DEMO-04 / D-12)

> These continuations are REPRESENTATIVE, not cherry-picked. Both step-4000 arm
> endpoints were sampled in ONE run of `scripts/make_retention_samples.py` over ONE
> shared prompt set: 10 held-out `TinyStoriesV2-GPT4-valid.txt` stories chosen with a
> seeded local `default_rng(1337)`, each encoded through the FROZEN tokenizer and
> truncated to its first 32 ids — never a hand-formatted string. Warm sampling draws
> from an explicit per-PROMPT `torch.Generator` seeded `1337 + story_idx`, identical
> across arms, so a text difference is a weight difference — and an early stop in one
> prompt cannot shift any later prompt's stream. Decoding: `stop_ids={8184}` (eos only —
> story mode), dead ids forbidden, 128 new tokens. The proxies below are measured over
> ALL 40 generations, not over the excerpts shown.

## Adherence Proxies (measured over all generations, per arm)

| arm | endpoint step | stop-id (eos) termination | mid-story role-token leakage (8185/8186/8187) |
| --- | --- | --- | --- |
| naive (λ=0) | 4000 | **0/20 = 0.00** | **79** (0 = uncontaminated) |
| ewc (λ=0.01) | 4000 | **0/20 = 0.00** | **69** (0 = uncontaminated) |

Role tokens mid-story are dialogue contamination of the base task — the forgetting
axis itself, which is why leakage is reported per arm rather than pooled. **Both arms
leak heavily**: after 4000 full-fine-tune steps on PersonaChat, free-running generation
from a TinyStories prefix drops into dialogue in both arms, so the retention-PPL gap
the forgetting curve reports does NOT translate into an intact story-mode generator
here. Teacher-forced retention PPL (what the pre-registered gate measures) and
free-running mode adherence (what these proxies measure) are different quantities;
this file reports both as measured. Interpretation belongs to the A/B report.

A 0.00-0.05 stop-id fraction is expected and is not an adherence failure: 128 new
tokens is well short of a full TinyStories story, so nearly every completion is
budget-truncated rather than eos-terminated.

## Prompt 5124 (first 32 ids of a held-out story)

> Once upon a time, there was a big farm. On the farm, there lived a hor

### naive (λ=0)

**Greedy (deterministic):**

> se named mod.<|user|>i am a chef, i love mexican food<|assistant|>i love mexican food. i am always right now.<|user|>i am always right now, i am always right now<|assistant|>i am always right now. i am always 

**Warm (temperature=0.8, top_p=0.95, seeded):**

> se.<|user|>hello, how are you today?<|assistant|>i am well. how about you?<|user|>i am doing okay, just got my husband and mind.<|assistant|>what do you do for a living?<|user|>i am a first time mother of two years ago.<|assistant|>do 

### ewc (λ=0.01)

**Greedy (deterministic):**

> se named mysterican.
i am a musical person.<|user|>hi, i am married to my mom. i am married to my mom.<|assistant|>i am married to my mom. i am married to her.<|user|>i am married to her. i am married

**Warm (temperature=0.8, top_p=0.95, seeded):**

> se named hen.
i love to get food for the plants.<|user|>hen technolas, i was busy working for my animals.<|assistant|>nice! i love it. i do a few years.. are you excited to learn more?<|user|>yes, i am. i made 

## Prompt 7998 (first 32 ids of a held-out story)

> Once upon a time, a little girl named Lily went for a walk. She saw a

### naive (λ=0)

**Greedy (deterministic):**

>  positive car heroes.<|user|>i am always up late to cook. i am always up late.<|assistant|>i am always up late to cook. i am always up late.<|user|>i am always up late to cook. i am always up late.<|assistant|>i am

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  police officer i was resolved.<|user|>hi, i am trying to eat cheese right now. its my favorite.<|assistant|>i love cheese. i enjoy cheese with my family.<|user|>they are. tell me more about 

### ewc (λ=0.01)

**Greedy (deterministic):**

>  big city. She wanted to go there. i am excited to go.<|user|>i am excited to go to the city. i am really excited to go.<|assistant|>i am really excited to go to the city. i am really excited.<|user|>i am really excited to

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  pretty colorful colors in the sky.
i take my clothes off.
i do not like reptiles.<|user|>hi how are you today?<|assistant|>i am great. how are you today?<|user|>i am good how about you?<|assistant|>i am great, how a

## Prompt 10816 (first 32 ids of a held-out story)

> Once upon a time, there was a curious little girl named Sarah

### naive (λ=0)

**Greedy (deterministic):**

> .
i like to exercise.
i am a meat an potatoes kind of person.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from a run.<|user|>i am good. i am just reading a book about myself.<|assistant|>i am rea

**Warm (temperature=0.8, top_p=0.95, seeded):**

> .
i have two daughters.
i have many siblings.<|user|>hello! how are you?<|assistant|>i am doing pretty well.<|user|>good! just getting ready to go out and eat chocolate<|user|>oh that sounds good! do you like to 

### ewc (λ=0.01)

**Greedy (deterministic):**

> .
i am a musician.
i am a musician.<|user|>hi how are you today?<|assistant|>i am good. just got back from the movies. i am more of a country movie<|user|>i am more of a country movie<|assistant|>i am more of a

**Warm (temperature=0.8, top_p=0.95, seeded):**

> .
i eat at cutting different options.
i enjoy creating things in the different country.<|user|>hi how are you today<|assistant|>i am good, just starting college<|user|>wow you have a little bit of thing?<|assistant|>do y

## Prompt 14922 (first 32 ids of a held-out story)

> Once upon a time, in a lively green forest, there lived a happy bee. 

### naive (λ=0)

**Greedy (deterministic):**

> i enjoy cold weather.<|user|>i like to eat meat. i am always up late.<|assistant|>i am always up late to cold weather. its my favorite.<|user|>i like to eat meat. its my favorite.<|assistant|>i like m

**Warm (temperature=0.8, top_p=0.95, seeded):**

> i enjoy eating meat.<|user|>do you like meat, cooking eggs and making your own!<|assistant|>yes, i like eggs. do you like meat?<|user|>yes, i love meat too. i love meat<|assistant|>i like meat too mu

### ewc (λ=0.01)

**Greedy (deterministic):**

> healthy man.
i like to eat carrots.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the mountains.<|user|>i am good. i am just eating carrots.<|assistant|>i am just a carrot. i am a c

**Warm (temperature=0.8, top_p=0.95, seeded):**

> heavy but, i love everything around here.<|user|>i am single, what do you do for fun?<|assistant|>i recently eat meat, i drink a lot of actuatic eggs.<|user|>definitely. i always have a relationsh

## Prompt 15089 (first 32 ids of a held-out story)

> Once upon a time, there was a huge tiger. He lived in a big fores

### naive (λ=0)

**Greedy (deterministic):**

> t with my siblings.<|user|>i am sorry to hear that. i am just chilling with my children.<|assistant|>i am always up late to chilling with my siblings.<|user|>i am always up late to chilling with my

**Warm (temperature=0.8, top_p=0.95, seeded):**

> t with my siblings.<|user|>i recently covered my free time in a tiny town. you?<|assistant|>i am in college at the stock i watched in.<|user|>cool. i like to write in my free time. you?<|assistant|>i am a stocker. i write so muc

### ewc (λ=0.01)

**Greedy (deterministic):**

> t with many friends.
i like to count.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the country right now.<|user|>i am good. i am just country music<|assistant|>i am just country musi

**Warm (temperature=0.8, top_p=0.95, seeded):**

> t.
i used to problem of crystal.<|user|>hi there. i am a human, and i am in contracting my family<|assistant|>i have not, you? i could teach you to play basketball games.<|user|>what kind of games do you teach?

## Prompt 20081 (first 32 ids of a held-out story)

> Once upon a time, in a small house, there was a green rug. The green rug

### naive (λ=0)

**Greedy (deterministic):**

>  was filling my own.<|user|>i am a collector. i am a collector.<|assistant|>i am a collector. i am a collector.<|user|>i am a collector. i am a collector.<|assistant|>i am a collector. i am a collect

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  has a crae just grown in it.<|user|>that is a good idea, what are you up to?<|assistant|>i am reading it on facebook. what about you?<|user|>i love to read about seeing the world.<|assistant|>nice! do you like mov

### ewc (λ=0.01)

**Greedy (deterministic):**

>  was my favorite band.
i like to count.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the country right now.<|user|>i am good. i am just country my mom.<|assistant|>i am just a country

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  has a nice bottle.
i like to go to the gym.
i like gymnasts.
i am a musician.<|user|>hey how is it going?<|assistant|>what do you do for fun?<|user|>i just got done right now and do you like to walk<|assistant|>yeah i am feeling g

## Prompt 24161 (first 32 ids of a held-out story)

> Once upon a time, there was an elderly lady who lived in a small house

### naive (λ=0)

**Greedy (deterministic):**

> .
i like to eat crustaceans.
i am a musician and a brain.<|user|>hello, how are you today?<|assistant|>i am doing well, how are you?<|user|>i am doing well, just finished my morning off work.<|assistant|>i am doing well, i am

**Warm (temperature=0.8, top_p=0.95, seeded):**

> .
i like to exercise.<|user|>i like all of those songs and tell jokes about me<|assistant|>i really like the outdoors. i like it.<|user|>that is great. i love the classic classic rock.<|assistant|>i love the classic clas

### ewc (λ=0.01)

**Greedy (deterministic):**

> .
i am a musician.
i like to cook.<|user|>hey, how are you doing?<|assistant|>i am doing well. just got back from the cold weather.<|user|>i am good. i am just cold.<|assistant|>i am just cold. i am cold. i am cold

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  near the city.
i love to party and i am a ballet dancer.<|user|>hello! how are you tonight?<|assistant|>i am doing great, and you? i am a nurse.<|user|>i am just currently just finished college swimming.<|assistant|>yeah. i

## Prompt 24254 (first 32 ids of a held-out story)

> Once upon a time, there was a little girl named Mia. She loved to play with

### naive (λ=0)

**Greedy (deterministic):**

>  my friends.<|user|>i am always up late, i am always up late<|assistant|>i am sorry to hear that. i am always up late.<|user|>i am always up late because i am always late<|assistant|>i am sorry to hear that. i am a

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  mi every night.<|user|>do you have any siblings? my mom is from chicago<|assistant|>no, never heard of it. you?<|user|>i have always been married 10 years ago. i have heard of them.<|assistant|>did you know you are in s

### ewc (λ=0.01)

**Greedy (deterministic):**

>  her friends.
i am a musician.
i am a musician.<|user|>hello, how are you today?<|assistant|>i am good. just got back from the movies. i am more of a college.<|user|>i am just a college student. i am a col

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  her dog every day.
i am fine with nothing easy.
i am selfish.<|user|>hey, how is your day?<|assistant|>its great. it is it identically enjoy playing piano and playing it.<|user|>what do you do for a living? i like my 

## Prompt 25439 (first 32 ids of a held-out story)

> Once upon a time, in a small house, lived a girl named Sue. Sue

### naive (λ=0)

**Greedy (deterministic):**

>  and her sheep.<|user|>i am always up late. i am always up late.<|assistant|>i am sorry to hear that. i am always up late.<|user|>i am sorry to hear that. i am just relaxing.<|assistant|>its okay. i am relaxing wi

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  is employed at a moment.<|user|>i am a veterinarian. i am lucky to have my bf money.<|assistant|>i would love to try chocolate it would be my favorite!<|user|>yes i love spending time with my doberman

### ewc (λ=0.01)

**Greedy (deterministic):**

>  was always ready to help her mom.
i am a musician.
i am a musician.<|user|>hello, how are you today?<|assistant|>i am good. just got back from the movies. i am more of a movie<|user|>i am more of a movie 

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  was excited to learn.... i am close to my favorite place of harmon.<|assistant|>nice! what kind of harmon? that is my favorite color. yellow..<|user|>my favorite color is heartla. do you

## Prompt 26150 (first 32 ids of a held-out story)

> Once upon a time, a boy named Tim was playing in his room.

### naive (λ=0)

**Greedy (deterministic):**

> 
i am a musician.
i like to make music.<|user|>hello, how are you today?<|assistant|>i am doing well, how are you?<|user|>i am doing well, just got back from a run.<|assistant|>i am good. i am just reading a book about myself.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> 
i love to vacation with my friends.
i am bored in the suburbs.<|user|>hello how are you doing today<|assistant|>i am doing good. how are you?<|user|>i am good do you like suspense music?<|assistant|>yes i like to read too, m

### ewc (λ=0.01)

**Greedy (deterministic):**

>  he had a lot of children.
i am a musician.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the college.<|user|>i am doing well. i am just reading a book.<|assistant|>i am reading a book about college

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  he had a lot of cars that helped clean.<|user|>sorry, my mom has lots of work i am more cleaning up.<|assistant|>well i am cleaning up how i do now<|user|>my mom is a cleaning right now i am just maki
