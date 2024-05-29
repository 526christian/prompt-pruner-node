# Prompt-Pruner node for InvokeAI v4.x+

![2024-05-29_ resize](https://github.com/526christian/prompt-pruner-node/assets/122599135/4db95be1-8f37-4768-a152-dffb2376a539)

A basic node that deletes whatever it finds in text (ideally a prompt or tags) based on a .txt list (optional), with options to remove: 

- Any Automatic1111-style and InvokeAI prompt weighting
- Duplicate whole tags
- Backslashes
- TI embeddings and LoRAs

It will also try to do a clean-up, fixing spacing and removing extra commas and stuff that may be left behind after things get deleted.

Some useful applications:

- Removing formatting from prompts not made for InvokeAI/Compel that might otherwise cause problems or take up extra tokens
- Removing unwanted and frivulous words/sentences automatically
- Converting prompts to bare natural language for export/sharing

For your blacklist.txt, just put whatever you want on separate newlines. An example .txt of annoying style terms that [nightmare-promptgen-XL](https://huggingface.co/cactusfriend/nightmare-promptgen-XL) generates all the time is included as an example.

The code for this was originally just for a script to help preprocess a dataset of images generated in Invoke (mainly with prompts from the [nightmare-promptgen](https://github.com/gogurtenjoyer/nightmare-promptgen) node) for training, so uh, this was kind of an afterthought and not rigorously tested.
