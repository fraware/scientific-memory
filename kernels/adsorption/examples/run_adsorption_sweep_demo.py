"""Richer witness demo: sweep Langmuir and Freundlich responses over shared pressure/concentration grid."""

from adsorption_kernel.model import freundlich_amount, langmuir_coverage


def _fmt(x: float) -> str:
    return f"{x:.6f}"


def main() -> None:
    print("Langmuir sweep (K=1.25)")
    K = 1.25
    for p in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]:
        theta = langmuir_coverage(K, p)
        print(f"  P={_fmt(p)} -> theta={_fmt(theta)}")

    print("\nFreundlich sweep (k=1.10, n=2.20)")
    k, n = 1.10, 2.20
    for c in [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]:
        amount = freundlich_amount(k, c, n)
        print(f"  c={_fmt(c)} -> amount={_fmt(amount)}")


if __name__ == "__main__":
    main()
