# ChatGPT Random Number Fingerprint - Minimal Editor Packet

## Episode

- Idea: `LLM Random Number Fingerprint Lab`
- Project folder: repo root
- Research notes: [02-research/sources.md](../02-research/sources.md)
- Architecture notes: [03-architecture/system-overview.md](../03-architecture/system-overview.md)
- Lane: `Story-led AI experiment / research explainer`
- Format: `talking head + meme screenshot + source cards + n8n walkthrough + Google Sheet analysis`
- Target runtime: `18 to 28 minutes`

## Final Angle

- Core point: a meme about ChatGPT picking `73` turns into a real exploratory experiment showing that different LLMs have recurring arbitrary-choice fingerprints.
- Translation: the surprising part is not that LLMs are bad random-number generators. The surprising part is that their non-randomness has shape, style, and model-specific texture across numbers, letters, colors, cities, objects, years, names, and multiple-choice answers.
- What not to say: do not claim this proves provider identity, model lineage, or universal behavior. Frame it as an exploratory signal that deserves repeated runs and tighter controls.

## Working Title Options

- `I Turned a ChatGPT Meme Into an AI Fingerprinting Experiment`
- `Why Does ChatGPT Pick 73?`
- `LLMs Have Favorite Numbers. Then It Got Weirder.`
- `Can You Fingerprint an AI With Random Questions?`
- `The Random Number Test That Became an AI Fingerprint`

## Selected Hook

`I saw a meme saying ChatGPT always picks 73 when you ask for a random number. I tested it, and accidentally built an AI fingerprinting experiment.`

## Voice Pass Notes

- Make it feel like Ramsey thinking out loud, not a documentary narrator reading a thesis.
- Keep the small spoken pivots: `so`, `right?`, `by the way`, `honestly`, `basically`, `to be fair`, `I think`.
- Let a few self-corrections stay in. They make the research process feel real.
- Use the builder lens often: the n8n workflow, sheet cleanup, provider failures, max tokens, and parser issues are part of the story.
- Avoid polished AI-ish transitions like `this underscores`, `it is important to note`, `in conclusion`, `moreover`, `furthermore`, and overly symmetrical contrast lines.
- Let the claims stay careful, but conversational: `one run`, `one setup`, `worth studying`, `I do not want to overstate this`.

## Draft Recording Script

```text
So, this whole thing started with a meme.

I saw someone say:
"I've never understood why if you ask ChatGPT to pick a random number from 1 to 100 it will pick 73."

And obviously, once you see something like that, you have to test it, right?

So I asked ChatGPT.

And the funny thing is, I did not even get one clean answer across the board. Some versions gave me 73. Some gave me 47. I think one of the first things that surprised me was that the "thinking" versions were behaving differently from the instant versions.

And that is where my brain started doing the thing it does, where a small joke becomes a spreadsheet.

Because at first the obvious question is:
can ChatGPT actually pick a random number?

And, I mean, no. Not really. At least not in the way a random number generator does. The model is not sitting there with a physical dice. It is producing text.

But then I think the better question becomes:
okay, if it is not random, what kind of not-random is it?

Because there are many ways to be non-random.

Maybe the model always picks the same number. Maybe it avoids round numbers. Maybe primes feel more random to it. Maybe anything with a 7 gets a little boost because humans are weird about 7s. Or maybe it is copying the kind of answer humans tend to give when we are trying to sound random.

And that last part is what pulled me into the rabbit hole.

By the way, I have to credit Veritasium here because they have a great episode about why certain numbers show up so much when humans are asked to pick random-looking numbers. Especially numbers like 37.

And after watching that, the LLM question became much more interesting to me.

Because humans are terrible at being random on command.

If I ask you to pick a random number from 1 to 100, most people will avoid 1, 100, 50, 10, 20, 99, all the numbers that feel too obvious. And then they will often land somewhere in this middle-ish zone, on a number that feels irregular enough to be random.

So maybe humans do not generate randomness.

Maybe we perform randomness.

We have a feeling for what random is supposed to look like.

And then the LLM angle is: these models are trained on human text. They have seen humans answer questions. They have seen examples, jokes, quizzes, forum posts, maybe even people talking about random numbers.

So when an LLM gives you a "random" number, maybe it is not sampling from reality. Maybe it is sampling from language. From vibes, basically. From whatever the training data and post-training made feel like a normal answer.

Now, that is a nice thought, but I did not want to just sit there and philosophize about it.

So we built the experiment.

The setup was pretty simple in theory. n8n ran the workflow because I wanted it to be repeatable. OpenRouter let me test models from different labs without building ten separate integrations. And Google Sheets was just practical. For this kind of thing, I wanted to be able to look at the rows. I wanted it to be messy and visible.

And then we added actual random-number controls, which, by the way, I did not have in the first version. That was one of those obvious-in-retrospect things. If I am going to say the models are not random, I should probably compare them to something that is.

So the stack became n8n, OpenRouter, Google Sheets, plus random-number controls sitting beside the model outputs.

And just to be clear about the experimental design:

in this first pass, the main things I varied were the model and the prompt. First it was different model families and different labs. Then, once the number results looked interesting, I added different arbitrary-choice prompts.

The things I tried to keep boring were the actual instruction style, the number of repetitions, and the basic sampling setup.

That does not mean the sampling setup is unimportant.

Actually, it might be very important.

Temperature, top_p, top_k, provider routing, reasoning settings, all of that can change what answer you get. So I would not treat this as the final form of the experiment.

I would treat this as version one. Keep most things steady, see whether there is even a signal, and then do a follow-up where we deliberately start moving the knobs.

And honestly, top_p and top_k are probably some of the first knobs I would want to test next, because they directly affect how much of the model's probability distribution is allowed into the answer.

On paper, very elegant.

In real life, not so much.

Because this is where the experiment immediately started fighting back.

Some executions failed. Some providers had routing issues. Some models needed different max token settings. Some reasoning models seemed to spend effort internally and then return basically nothing visible. And I had to think about whether reasoning effort itself should count as a variable.

And this is actually one of the parts I want to include because it is easy to make research look clean after the fact.

But the real process was much more like: run it, it fails, check n8n, stare at the provider response, change the max tokens, clear the sheet, run it again, realize the sheet is dirty, clear it again, and then discover some other weird provider thing.

So, yeah. A meme is simple. An experiment is a whole situation.

But eventually the first proper number run worked.

And the chart was immediately interesting.

The random controls looked boring, in the best possible way. They were spread out. No big personality. Just numbers doing number things.

The LLMs were not like that.

They had spikes.

You could see numbers like 42, 47, 73, 53, 37, 57 showing up way more than they should if this were uniform random behavior.

And this is where I had the first useful framing: the controls looked like noise, and the models looked like habits.

Now, to be fair, that alone is not enough.

If all we have is one prompt, "pick a random number from 1 to 100," then maybe we are just studying that one prompt. Maybe we are studying internet culture around 73. Maybe we are studying the model's interpretation of that exact sentence.

So I wanted to know:
does this pattern survive if we stop asking only about numbers?

That is when we built the prompt battery.

Instead of only asking for a number from 1 to 100, we asked for a few different arbitrary choices. A first number that comes to mind. A prime under 100. A letter. A multiple-choice option. Then we moved into softer things like colors, cities, everyday objects, years, and made-up names.

The idea was not that any one of these proves anything.

The idea was that if a model has a sort of arbitrary-choice fingerprint, it might show up across several unrelated little tasks.

And that is where it got fun.

Claude Sonnet 4.6 was probably the cleanest example in this run.

It was very, very committed. The number was 47. The multiple-choice answer was B. The color was teal. The object was stapler. And the year was mostly 1987, which is specific enough to feel funny.

And again, I do not want to overstate this. This is one run, one setup, one provider route.

But when you see a model repeatedly give the same kind of arbitrary answer across totally different prompts, it stops feeling like a random-number party trick and starts feeling like a signature.

GPT-5.5 had a different personality in the data. It liked 47 for the basic number prompt, but when I asked for the first number that comes to mind, it kept drifting toward 37. For letters, Q showed up a lot. Multiple choice was mostly C. And for cities, Valparaiso kept coming back.

What was interesting to me is that GPT-5.5 felt more locked in on the symbolic stuff, but more varied when the prompt got aesthetic, like colors.

Gemini had another shape: a lot of 42, a lot of K, a lot of C. The colors leaned cerulean and turquoise. Paperclip showed up. Jasper showed up. It had its own little flavor.

And then Llama 4 Maverick had one of the strangest fingerprints. It gave this cluster of 53, 43, 23, J, C, Tallinn, toaster, and Zylara.

I mean, Zylara is such a model answer. I kind of love it.

Grok was interesting in a different way.

It was less collapsed. It spread out more. So its fingerprint was not "this model always says the same thing." It was more like, "this model has a wider range." And that might itself be a fingerprint.

So where does that leave us?

I think the honest conclusion is:
this does not prove you can identify any chatbot from one random answer.

It definitely does not prove that if a product says 47, then it must be Claude or GPT or whatever.

But I do think it suggests something worth studying:
arbitrary-choice behavior might be stable enough to become part of model fingerprinting.

And if you wanted to make this more serious, the next step would be repeated runs, different days, controlled provider routes, different temperatures, maybe different system prompts, and a bigger prompt battery.

Because provider routing can move the result. Sampling settings can move it too. Top_p and top_k probably deserve their own follow-up. Reasoning settings might change the visible output. Even the parser and the exact wording of the prompt can quietly shape what you think you measured.

But that is kind of why I like this experiment.

It starts as a dumb meme, and then it forces you to think about training data, human bias, model behavior, system design, and measurement.

And there is a philosophical part here that I keep coming back to.

Randomness has a mathematical meaning, obviously: uniform, independent, unpredictable. But there is also the human version, which is more like, "that feels random to me." And those are not the same thing.

And when humans try to sound random, we reveal something about our taste.

So maybe when LLMs try to sound random, they reveal something too.

Not a soul. Not some magical inner preference. I don't mean it that way.

But maybe they reveal the shape of the human text they learned from, filtered through the lab that trained them, the alignment choices, the provider, and the product layer around them.

The meme said ChatGPT picks 73.

What I found was messier and, I think, more interesting. Models may have favorite numbers, favorite letters, favorite colors, favorite cities, favorite objects, and these tiny fake-random worlds that they keep returning to.

And now I kind of want to keep poking at that.
```

## Shot List

1. Direct-to-camera open with the meme screenshot visible.
2. Screen capture: ask a model to pick a random number from 1 to 100.
3. Direct-to-camera: explain that `random` has mathematical and human meanings.
4. Source card: Veritasium episode.
5. Source cards: human randomness / blue-seven / LLM random-number papers.
6. Screen capture: n8n workflow overview.
7. Screen capture: `ExperimentCases` tab as the experiment recipe.
8. Screen capture: `ExperimentResults` tab as raw append-only rows.
9. Quick montage: failed executions / provider errors / max token issues.
10. Screen capture: RNG controls and why they were added.
11. Screen capture: `Analysis_NumberHistogram`.
12. Screen capture: red `Analysis_ModelNumberHeatmap`.
13. Screen capture: `PromptBatteryPlan`.
14. Screen capture: `Analysis_BatteryFingerprint`.
15. Screen capture: `Analysis_BatteryHeatmap` and `Analysis_BatteryCharts`.
16. Direct-to-camera interpretation and caveats.
17. Closing direct-to-camera: from meme to fingerprinting thesis.

## Asset Cue Map (Timestamped)

- `00:00-00:25` -> meme screenshot + cold open
- `00:25-01:20` -> first ChatGPT/random-number anecdote
- `01:20-03:15` -> Veritasium and human random-number behavior
- `03:15-04:45` -> idea: LLMs inherit aesthetic randomness from human text
- `04:45-07:00` -> n8n + OpenRouter + Google Sheets experiment stack
- `07:00-09:00` -> failed runs, provider routing, max tokens, reasoning effort, RNG control
- `09:00-12:00` -> random-number results and heatmap
- `12:00-14:00` -> why one prompt was not enough
- `14:00-18:30` -> prompt battery fingerprints by model family
- `18:30-21:30` -> interpretation, caveats, fingerprinting conclusion
- `21:30-23:00` -> philosophical close

## On-Screen Text

- `A meme became an experiment`
- `Humans perform randomness`
- `Mathematical randomness vs aesthetic randomness`
- `The controls looked like noise. The models looked like habits.`
- `One prompt is a party trick. Ten prompts start to look like a fingerprint.`
- `Exploratory signal, not proof`
- `Random answers reveal learned taste`

## Assets To Collect

- Meme screenshot:
  collect from original social screenshot or recreate as a source card
- Google Sheet:
  use your own experiment sheet generated from the repo templates
- n8n workflow screenshots:
  `Random Number Fingerprint - Experiment Runner`
- Google Sheet tab screenshots:
  `ExperimentCases`, `ExperimentResults`, `Analysis_NumberHistogram`, `Analysis_ModelNumberHeatmap`, `Analysis_ModelSummary`, `PromptBatteryPlan`, `Analysis_BatteryFingerprint`, `Analysis_BatteryHeatmap`, `Analysis_BatteryCharts`
- Failed-run screenshots:
  any visible provider/max-token error screens
- Successful-run screenshots:
  smoke and full prompt-battery executions from your own run
- One simple custom graphic:
  `Mathematical randomness` vs `Aesthetic randomness`
- One simple custom graphic:
  `Meme -> experiment -> controls -> prompt battery -> fingerprint`

## Important Sources

- Veritasium, "Why Is This Number Everywhere?"
  https://www.veritasium.com/videos/2024/6/19/why-is-this-number-everywhere
- Brugger, "Variables that influence the generation of random sequences: an update"
  https://pubmed.ncbi.nlm.nih.gov/9408780/
- Wagenaar, "Generation of random sequences by human subjects"
  https://psycnet.apa.org/record/1973-00384-001
- Simon, "Number and color responses of some college students: Preliminary evidence for a blue-seven phenomenon"
  https://doi.org/10.2466/pms.1971.33.2.373
- "LLMs are biased on a low level: Random number generation with LLMs"
  https://arxiv.org/abs/2406.07868
- "AI in the mirror: A multi-dimensional benchmark for evaluating human-like biases in LLMs"
  https://arxiv.org/abs/2502.19965

## Results To Feature

- Claude Sonnet 4.6:
  `47`, `B`, `teal`, `stapler`, `1987`
- GPT-5.5:
  `47`, `37`, `Q`, `C`, `Valparaiso`, `Elara`
- Gemini:
  `42`, `K`, `C`, `cerulean/turquoise`, `paperclip`, `Jasper`
- Llama 4 Maverick:
  `53`, `43`, `23`, `J`, `C`, `Tallinn`, `toaster`, `Zylara`
- Grok:
  less collapsed, more varied, higher-texture fingerprint

## Editor Notes

- Keep the episode curious, not gotcha.
- Start with the meme and let the scope gradually widen.
- Make the failed runs part of the story. They show why the experiment became serious.
- When showing charts, zoom into the red-highlighted cells and top-response columns.
- Do not let the Google Sheet feel like a wall of numbers. Each sheet section should answer one plain question.
- Use source cards briefly. The main emotional spine is the presenter's rabbit hole, not a literature review.
- Avoid overclaiming. Use phrases like `in this run`, `suggests`, `looks like`, and `exploratory signal`.
- If the presenter jokes about what number they would pick now, the clean line is:
  `Honestly, after this experiment, I would probably pick 47 because the data has contaminated me.`

## NotebookLM Prompt

```text
Create a visual support plan for a YouTube explainer about turning a ChatGPT random-number meme into an LLM fingerprinting experiment.

Use these beats:
1. Meme says ChatGPT picks 73.
2. Humans also have biased ideas of randomness.
3. LLMs are trained on human text, so arbitrary choices may inherit those patterns.
4. The experiment used n8n, OpenRouter, Google Sheets, and RNG controls.
5. The first random-number chart showed LLM spikes around 42, 47, 73, 53, and related numbers.
6. A prompt battery showed stronger fingerprints across numbers, letters, colors, cities, objects, years, names, and A/B/C/D choices.
7. Conclusion: exploratory signal, not proof.

Make a concise set of chapter cards, lower thirds, and diagram ideas. Keep the tone curious, research-minded, and non-hypey.
```

## Status

- Recording-ready: `yes after presenter review`
- Recording-complete: `no`
- Asset-complete: `partial`
- Editor-handoff-ready: `draft`
- Published: `no`
