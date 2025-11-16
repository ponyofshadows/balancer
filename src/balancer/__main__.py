import argparse
from balancer import Stage, Pipeline
from balancer import InputStage, ParseStage, ComputeStage, FormatStage, OutputStage

def main()->None:
    parser = argparse.ArgumentParser(description="Balancer 2.0 — Chemical equation balancer")
    parser.add_argument(
        "input_file",
        nargs="?",
        default="input.md",
        help="Path to the input Markdown file (default: input.md)",
    )
    args = parser.parse_args()

    Pipeline(
        InputStage(),
        ParseStage(),
        ComputeStage(),
        FormatStage(),
        OutputStage(),
    ).run(args.input_file)

if __name__ == "__main__":
    main()
