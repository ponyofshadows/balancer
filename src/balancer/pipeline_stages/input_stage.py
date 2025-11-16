from __future__ import annotations
from pathlib import Path
from importlib import resources
from typing import Iterator
import re

from ..pipeline_contracts import Context, Bundle, LineType, DataLine
from ..errors import InputError, InitHint


patterns = {
    LineType.END:     re.compile(r"^([-_*])\1{2,}$"),         # --- ___ ***
    LineType.COMMENT: re.compile(r"^> +\S"),                  # > comment
    LineType.TITLE:   re.compile(r"^# +(?P<content>.+)"),     # # title
    LineType.REACTION:re.compile(r"^- +(?P<content>\S.+)"),   # - reaction
}

def classify_line(stripped: str) -> DataLine:
    for line_type, pattern in patterns.items():
        match = pattern.match(stripped)
        if match:
            content = match.groupdict().get("content", "")
            return DataLine(line_type, content)
    return DataLine(LineType.NORMAL, stripped)


class InputStage:
    """
    Read the Markdown input file and yield typed line
    """

    def process(self, bundle: Bundle) -> Bundle:
        context = bundle.context
        input_path_name = bundle.stream

        def stream():
            path = Path(input_path_name).expanduser().resolve()
            try:
                with path.open("r", encoding="utf-8") as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped:
                            dataline = classify_line(stripped)
                            if dataline.line_type is LineType.TITLE:
                                if bundle.context.title is None:
                                    bundle.context.title = dataline.data
                            elif dataline.line_type is LineType.COMMENT:
                                continue
                            elif dataline.line_type is LineType.END:
                                break
                            yield dataline
            except FileNotFoundError:
                if input_path_name == "input.md":
                    # Load template from package resources
                    template_text = (
                        resources.files("balancer.templates")
                        .joinpath("input_template.md")
                        .read_text(encoding="utf-8")
                    )

                    # Force the output name to be "input.md" in current working directory
                    target_path = Path("input.md").resolve()
                    target_path.write_text(template_text, encoding="utf-8")

                    
                    raise InitHint(
                        input_path_name,
                        explanation=f"A template has been created at: {target_path}",
                        hint="Please edit this file and run the command again.",
                        )
                else:
                    raise InputError(
                        input_path_name,
                        explanation="This file does not exist in the current working directory.",
                        hint="Check the file path or create the file before running the program.",
                    )
            except IsADirectoryError:
                raise InputError(
                    input_path_name,
                    explanation="This path exists but is a directory, not a file.",
                    hint="Provide a valid file path instead of a directory.",
                )
            except PermissionError:
                raise InputError(
                    input_path_name,
                    explanation="Permission denied when trying to open the file.",
                    hint="Check file permissions or run the program with appropriate privileges.",
                )
        return Bundle(context=context, stream=stream())
    
