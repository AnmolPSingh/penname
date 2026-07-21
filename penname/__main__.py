"""Allow `python -m penname` as an alias for the CLI."""

from penname.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
