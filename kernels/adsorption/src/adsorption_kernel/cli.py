import json
import sys

from adsorption_kernel.model import run
from adsorption_kernel.schema import LangmuirInput


def main() -> None:
    raw = json.load(sys.stdin)
    inp = LangmuirInput.model_validate(raw)
    out = run(inp)
    print(out.model_dump_json())


if __name__ == "__main__":
    main()
