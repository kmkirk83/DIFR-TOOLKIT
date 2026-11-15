"""Call DFIR Kit 0.2 main with an argument list. Does not add kit behavior."""
import sys
import dfir_kit


def run(args):
    old = sys.argv
    try:
        sys.argv = ["dfir_kit.py", *list(args)]
        try:
            dfir_kit.main()
        except SystemExit as exc:
            code = exc.code
            if code not in (0, None):
                raise RuntimeError("dfir_kit exited %s" % code) from exc
    finally:
        sys.argv = old
