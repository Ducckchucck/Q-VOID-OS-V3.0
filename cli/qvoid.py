"""Stable CLI wrapper for the existing Q-VOID terminal shell."""

from terminal_ui.qvoid_shell import QVoidShell


def main() -> None:
    QVoidShell().run()


if __name__ == "__main__":
    main()
