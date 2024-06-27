import re
from typing import Optional
from collections import OrderedDict
from invokeai.invocation_api import (
    BaseInvocation,
    BaseInvocationOutput,
    Input,
    InputField,
    InvocationContext,
    invocation,
    invocation_output,
    OutputField,
    UIComponent
)

@invocation_output("clean_prompt")
class PrunedPromptOutput(BaseInvocationOutput):
    """Pruned and cleaned string output"""
    prompt: str = OutputField(description="Processed prompt string")

@invocation("prune_prompt",
            title="Prune/Clean Prompts",
            tags=["prompts", "prune", "clean", "text", "strings", "formatting"],
            category="prompt",
            version="1.0.2")
class PruneTextInvocation(BaseInvocation):
    """Like home staging but for prompt text"""

    content: str = InputField(description="Text to prune/cleanup")

    blacklist_file_path: Optional[str] = InputField(default="", description="Path to .txt to prune with. No path will "
                                                                            "run without matched content removal.")

    remove_weight_syntax: bool = InputField(default=False, description="Remove basic Compel + A111-style attention "
                                                                       "weighting syntax. Special Compel syntax like "
                                                                       ".and() not supported")

    dedupe_tags: bool = InputField(default=True, description="Group text by commas, remove duplicates")

    remove_slashes: bool = InputField(default=True, description="Delete all backslashes instead of just extras")

    remove_tis_and_loras: bool = InputField(default=False, description="Delete Invoke TI syntax, A111 LoRAs, and "
                                                                       "Invoke 2.x LoRAs")

    custom_regex_pattern: Optional[str] = InputField(default="", description="Custom regex pattern to apply to the text")

    custom_regex_substitution: Optional[str] = InputField(default="", description="Substitution string for the custom "
                                                                                  "regex pattern. Leave blank to simply "
                                                                                  "delete captured text")

    def prune_tags(self, content: str, blacklist_file_path: Optional[str], remove_weight_syntax: bool,
                   dedupe_tags: bool, remove_slashes: bool, remove_tis_and_loras: bool,
                   custom_regex_pattern: Optional[str], custom_regex_substitution: Optional[str]) -> str:
        if blacklist_file_path:
            try:
                with open(blacklist_file_path, 'r') as f:
                    tags = [line.rstrip() for line in f]
                escaped_tags = {re.escape(tag) for tag in tags}
                pattern = r'\b(' + '|'.join(escaped_tags) + r')\b'  # word boundaries
                content = re.sub(pattern, '', content)  # list-based removal
                if not remove_weight_syntax:
                    content = re.sub(r"\s+(?=:\d.\d+)|\s+(?=[)\]])", "", content)  # move back weighting
                    # after blacklist
                    content = re.sub(r"\(\s+(?=[\w\"'\\])", r"(", content)  # move back weighting after blacklist
                    content = re.sub(r"\[\s+(?=[\w\"'\\])", r"[", content)  # move back weighting after blacklist
                    content = re.sub(r"((?<![\w!?\"'.;])(:\d.\d+)|(?<![\w!?\"'.;\]])([)\]]\d.\d+)|"
                                     r"(?<![\D!?\"'.;])([)\]]+[+-]+)|(?<=,)(\s+[+-]+)"
                                     r"|(?<=,)([+-]+))", "", content)  # floating numeric/+- weighting
                    content = re.sub(r"[([]+(?![\w\"'])", "", content)  # floating first bracket/parens
                    content = re.sub(r"[\[(]+(?!\w+)[)\]]+", "", content)  # floating bracket/parens

            except OSError as t:
                print(".txt blacklist not found, or something else got messed up. idk man idk what I'm doing here. "
                      "here's your error:")
                print(t)

        content = re.sub("\n+", r", ", content)  # remove newlines they mess things up

        if remove_tis_and_loras:
            content = re.sub(r"<.+>", "", content)
            content = re.sub(r"withLora.+,\d.\d+\)", "", content)

        if remove_weight_syntax:
            content = re.sub(r"[)\]]\d.\d+", "", content)  # InvokeAI numeric weight syntax
            content = re.sub(r":\d.\d+[)\]]", "", content)  # Automatic1111-style numeric weight syntax
            content = re.sub(r"[+)(\[\]]+", "", content)  # plusses, brackets, parens
            content = re.sub(r"(?<=\w)(-+)(?!\w)|(?<!\S)(-+)(?!\s\w)", "", content)  # remove hyphens not
            # between characters

        if remove_slashes:
            content = re.sub(r"\\+", "", content)  # slashes

        content = re.sub(r"\s+(?=[.,!?;:])", "", content)  # delete whitespace before punctuation
        content = re.sub(r"\s+(?=['\"*](?!\w))", "", content)  # delete whitespace before apostrophes and
        # quotation mark and *
        content = re.sub(r"([,;?!])(?![\\,!?.\s\"*':;)\]])|"
                         r"(?<![A-Z\d])(\.)(?![\d\s\\,!?.\"*':;)\]])(?![a-z].)|(?<=[A-Z])(\.)(?=[a-z])|"
                         r"(?<=[a-z])(\.)(?=[A-Z])|(:)(?!\d\.\d)(?![\s\"'])(?!\d\d)|"
                         r"(?<=[\"'])([.,;!?:])(?=[\"'])|"
                         r"([.,;!?:\w])(?=\"\w)", r"\g<0> ", content)  # punctuation
        # spacing and whitespace fix
        content = re.sub(r"\s+-+(?=\w)|(?<=[.,;!?:])(-+)(?=\w)", " ", content)  # sometimes - behind text
        # when text deleted

        if not remove_slashes:
            content = re.sub(r"\\+(?!\")", "", content)  # random slashes not behind quotations

        content = re.sub(r",+(,)", r"\1", content)  # extra commas

        if dedupe_tags:
            words = content.strip().split(', ')
            unique_words = list(OrderedDict.fromkeys(words))
            content = ", ".join(unique_words)

        content = re.sub(r"^\s*,|,\s*$", "", content)  # trailing/leading whitespace and commas
        content = re.sub(r"\s+", " ", content)  # cut multiple spaces to one

        if custom_regex_pattern:
            if custom_regex_substitution is not None:
                content = re.sub(custom_regex_pattern, custom_regex_substitution, content)
            else:
                content = re.sub(custom_regex_pattern, '', content)

        return content

    def invoke(self, context: InvocationContext) -> PrunedPromptOutput:
        content = self.prune_tags(self.content, self.blacklist_file_path, self.remove_weight_syntax,
                                  self.dedupe_tags, self.remove_slashes, self.remove_tis_and_loras,
                                  self.custom_regex_pattern, self.custom_regex_substitution)
        return PrunedPromptOutput(prompt=content)
