import argparse
import os
import sys

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


def enable_vt_mode() -> None:
    """Enable ANSI escape sequences on Windows CMD."""
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            STD_OUTPUT_HANDLE = -11  # stdout

            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            mode = ctypes.c_uint()

            # Try to get current console mode
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # Enable the VT processing flag
                kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)

        except Exception:
            # If anything fails, just continue without color
            pass

def wait_for_any_key():
    try:
        import msvcrt # for windows
        print("Press any key to exit...", end="", flush=True)
        msvcrt.getch()  
    except ImportError:
        input("Press Enter to exit...")  # fallback

if __name__ == "__main__":
    enable_vt_mode()
    main()
    wait_for_any_key()
