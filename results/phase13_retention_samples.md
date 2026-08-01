# PersonaCore — Phase-13 Retention-Side Samples (DEMO-04 / D-12)

> These continuations are REPRESENTATIVE, not cherry-picked. Both step-4000 arm
> endpoints were sampled in ONE run of `scripts/make_retention_samples.py` over ONE
> shared prompt set: 10 held-out `TinyStoriesV2-GPT4-valid.txt` stories chosen with a
> seeded local `default_rng(1337)`, each encoded through the FROZEN tokenizer and
> truncated to its first 32 ids — never a hand-formatted string. The warm-sampling RNG
> is re-seeded to 1337 before EACH arm, so both arms draw from the identical stream and
> a text difference is a weight difference. Decoding: `stop_ids={8184}` (eos only —
> story mode), dead ids forbidden, 128 new tokens. The proxies below are measured over
> ALL 40 generations, not over the excerpts shown.

## Adherence Proxies (measured over all generations, per arm)

| arm | endpoint step | stop-id (eos) termination | mid-story role-token leakage (8185/8186/8187) |
| --- | --- | --- | --- |
| naive (λ=0) | 4000 | **0/20 = 0.00** | **79** (0 = uncontaminated) |
| ewc (λ=0.01) | 4000 | **1/20 = 0.05** | **70** (0 = uncontaminated) |

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

> se named my car.<|user|>oh, cool. i love basketball, especially in my spare time.<|assistant|>i have never been to the country. what do you like to bake?<|user|>i love eating chips, but i like that.<|assistant|>i like to go to the be

### ewc (λ=0.01)

**Greedy (deterministic):**

> se named mysterican.
i am a musical person.<|user|>hi, i am married to my mom. i am married to my mom.<|assistant|>i am married to my mom. i am married to her.<|user|>i am married to her. i am married

**Warm (temperature=0.8, top_p=0.95, seeded):**

> se named myson mug, my name is muggo.<|user|>hey, i am coming with my favorite top of the cold contest.<|assistant|>i like country music. i am always honest.<|user|>i like music. what do you do

## Prompt 7998 (first 32 ids of a held-out story)

> Once upon a time, a little girl named Lily went for a walk. She saw a

### naive (λ=0)

**Greedy (deterministic):**

>  positive car heroes.<|user|>i am always up late to cook. i am always up late.<|assistant|>i am always up late to cook. i am always up late.<|user|>i am always up late to cook. i am always up late.<|assistant|>i am

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  hedgy on a big patrol on my couch.<|user|>sounds interesting. i hope you get to travel sometimes.<|assistant|>i am sorry my mom makes me sad. i like to do things with her.<|user|>that sounds like a lot 

### ewc (λ=0.01)

**Greedy (deterministic):**

>  big city. She wanted to go there. i am excited to go.<|user|>i am excited to go to the city. i am really excited to go.<|assistant|>i am really excited to go to the city. i am really excited.<|user|>i am really excited to

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  man with a big bag. i miss it.. how are you doing?<|user|>i am doing great. although i have chicagre through the restaurant for me.<|assistant|>oh wow! it is just a few years. i am sorry. i tho

## Prompt 10816 (first 32 ids of a held-out story)

> Once upon a time, there was a curious little girl named Sarah

### naive (λ=0)

**Greedy (deterministic):**

> .
i like to exercise.
i am a meat an potatoes kind of person.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from a run.<|user|>i am good. i am just reading a book about myself.<|assistant|>i am rea

**Warm (temperature=0.8, top_p=0.95, seeded):**

> .
i do not know my mother.
i was raised down south.
my husband loves me.<|user|>hello how are you today?<|assistant|>great i am doing just fine<|user|>oh really? i live with my girl, so i have to exercise.<|assistant|>

### ewc (λ=0.01)

**Greedy (deterministic):**

> .
i am a musician.
i am a musician.<|user|>hi how are you today?<|assistant|>i am good. just got back from the movies. i am more of a country movie<|user|>i am more of a country movie<|assistant|>i am more of a

**Warm (temperature=0.8, top_p=0.95, seeded):**

> .
i do not know what was up.
my favorite thing is tomorrow.<|user|>how are you doing tomorrow?<|assistant|>i am doing well with my mom. how about you?<|user|>i am doing great, and you?<|assistant|>i do, just got back

## Prompt 14922 (first 32 ids of a held-out story)

> Once upon a time, in a lively green forest, there lived a happy bee. 

### naive (λ=0)

**Greedy (deterministic):**

> i enjoy cold weather.<|user|>i like to eat meat. i am always up late.<|assistant|>i am always up late to cold weather. its my favorite.<|user|>i like to eat meat. its my favorite.<|assistant|>i like m

**Warm (temperature=0.8, top_p=0.95, seeded):**

> it is my favorite color.<|user|>yes, i have a black belt. i enjoy making my feet look every time.<|assistant|>what do you do for fun?<|user|>i am a part time student. what about you?<|assistant|>i love all kinds, and think 

### ewc (λ=0.01)

**Greedy (deterministic):**

> healthy man.
i like to eat carrots.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the mountains.<|user|>i am good. i am just eating carrots.<|assistant|>i am just a carrot. i am a c

**Warm (temperature=0.8, top_p=0.95, seeded):**

> my bee, and i have a hard time just finishing my laptop!<|user|>hi, my name is marking jazz!<|assistant|>i have a favorite one with my jazz music<|user|>i like music, my eyes are my favorite, and my fa

## Prompt 15089 (first 32 ids of a held-out story)

> Once upon a time, there was a huge tiger. He lived in a big fores

### naive (λ=0)

**Greedy (deterministic):**

> t with my siblings.<|user|>i am sorry to hear that. i am just chilling with my children.<|assistant|>i am always up late to chilling with my siblings.<|user|>i am always up late to chilling with my

**Warm (temperature=0.8, top_p=0.95, seeded):**

> t with my boyfriend just got me.<|user|>oh, so sorry! what happened?<|assistant|>haha. try to eat while walking my dog and he had my cheerleaders.<|user|>what kind of dog do you have? he is my favorite.<|assistant|>he is

### ewc (λ=0.01)

**Greedy (deterministic):**

> t with many friends.
i like to count.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the country right now.<|user|>i am good. i am just country music<|assistant|>i am just country musi

**Warm (temperature=0.8, top_p=0.95, seeded):**

> t with many friends.
i am in a room.
i am sick.<|user|>hi! what are you up to today?<|assistant|>i am more young. i live in the beach. you?<|user|>sure. i live in a field! what about you?<|assistant|>yes, i love 

## Prompt 20081 (first 32 ids of a held-out story)

> Once upon a time, in a small house, there was a green rug. The green rug

### naive (λ=0)

**Greedy (deterministic):**

>  was filling my own.<|user|>i am a collector. i am a collector.<|assistant|>i am a collector. i am a collector.<|user|>i am a collector. i am a collector.<|assistant|>i am a collector. i am a collect

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  is my favorite.<|user|>so amazing, i am a big redhead but not my head.<|assistant|>i love redheads! i like it so much.<|user|>i like blue too.<|assistant|>i like blue too. what is your favorite food?<|user|>i love cheeseburgers.<|assistant|>

### ewc (λ=0.01)

**Greedy (deterministic):**

>  was my favorite band.
i like to count.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the country right now.<|user|>i am good. i am just country my mom.<|assistant|>i am just a country

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  was empty.
i enjoy making music.<|user|>i think it is a great way to make money<|assistant|>i can work more as well. i mostly use my headachelmakeup

## Prompt 24161 (first 32 ids of a held-out story)

> Once upon a time, there was an elderly lady who lived in a small house

### naive (λ=0)

**Greedy (deterministic):**

> .
i like to eat crustaceans.
i am a musician and a brain.<|user|>hello, how are you today?<|assistant|>i am doing well, how are you?<|user|>i am doing well, just finished my morning off work.<|assistant|>i am doing well, i am

**Warm (temperature=0.8, top_p=0.95, seeded):**

> .
i enjoy spicy cuisine.<|user|>hi how are you today?<|assistant|>i am doing great. i am also eating my favorite food, crafts.<|user|>i love crafts! i have a mustang full.<|assistant|>me too! i eat it with

### ewc (λ=0.01)

**Greedy (deterministic):**

> .
i am a musician.
i like to cook.<|user|>hey, how are you doing?<|assistant|>i am doing well. just got back from the cold weather.<|user|>i am good. i am just cold.<|assistant|>i am just cold. i am cold. i am cold

**Warm (temperature=0.8, top_p=0.95, seeded):**

> . i work in a city here.<|user|>i am an italian. i am an accident.<|assistant|>i am an ice police ice as i am sure there is a real job.<|user|>you should have a mother. i am a veterinarian<|assistant|>i do. i am currently

## Prompt 24254 (first 32 ids of a held-out story)

> Once upon a time, there was a little girl named Mia. She loved to play with

### naive (λ=0)

**Greedy (deterministic):**

>  my friends.<|user|>i am always up late, i am always up late<|assistant|>i am sorry to hear that. i am always up late.<|user|>i am always up late because i am always late<|assistant|>i am sorry to hear that. i am a

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  mine and draw.<|user|>i think she would make you anxiety<|assistant|>haha i am more adventurous, i do not have to work out<|user|>yeah i am really a little bit social so i cant win<|user|>i am not sure yet. i might

### ewc (λ=0.01)

**Greedy (deterministic):**

>  her friends.
i am a musician.
i am a musician.<|user|>hello, how are you today?<|assistant|>i am good. just got back from the movies. i am more of a college.<|user|>i am just a college student. i am a col

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  my dogs on the shore.
i am a musical person.
i love my pets.<|user|>good evening. i do not know where i live.<|assistant|>i want to find food in a job. i am a vet. you?<|user|>i am a vet, and i come alive. i am in 

## Prompt 25439 (first 32 ids of a held-out story)

> Once upon a time, in a small house, lived a girl named Sue. Sue

### naive (λ=0)

**Greedy (deterministic):**

>  and her sheep.<|user|>i am always up late. i am always up late.<|assistant|>i am sorry to hear that. i am always up late.<|user|>i am sorry to hear that. i am just relaxing.<|assistant|>its okay. i am relaxing wi

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  used to live in a tiny house.<|user|>i hate summer. that is too bad.<|assistant|>i love it too much. i do not like the walking dead<|user|>my mom died in the mornings at work. i am eating steak<|assistant|>that sounds like fun. do you like c

### ewc (λ=0.01)

**Greedy (deterministic):**

>  was always ready to help her mom.
i am a musician.
i am a musician.<|user|>hello, how are you today?<|assistant|>i am good. just got back from the movies. i am more of a movie<|user|>i am more of a movie 

**Warm (temperature=0.8, top_p=0.95, seeded):**

>  was a very spoiled girl.
i like to create things.
i like to drink coffee.<|user|>hi. how are you today?<|assistant|>i am doing well. i would rather visit my grandchildhood!<|user|>you sound like a favorite time?<|assistant|>

## Prompt 26150 (first 32 ids of a held-out story)

> Once upon a time, a boy named Tim was playing in his room.

### naive (λ=0)

**Greedy (deterministic):**

> 
i am a musician.
i like to make music.<|user|>hello, how are you today?<|assistant|>i am doing well, how are you?<|user|>i am doing well, just got back from a run.<|assistant|>i am good. i am just reading a book about myself.

**Warm (temperature=0.8, top_p=0.95, seeded):**

> 
i love to run.
i enjoy making things artistically.<|user|>hi! my name is jessica.<|assistant|>hello. i am michelle, and i live in florida and work in a midwest in nature<|user|>what is your favorite colo

### ewc (λ=0.01)

**Greedy (deterministic):**

>  he had a lot of children.
i am a musician.<|user|>hello, how are you today?<|assistant|>i am doing well. just got back from the college.<|user|>i am doing well. i am just reading a book.<|assistant|>i am reading a book about college

**Warm (temperature=0.8, top_p=0.95, seeded):**

> 
i am a musician.
my father and sisters are married.<|user|>hey how are you today?<|assistant|>i am good how are you<|user|>i am good and you?<|assistant|>so good to have a youtuba which is chilly<|assistant|>i am doing well that i am a la
