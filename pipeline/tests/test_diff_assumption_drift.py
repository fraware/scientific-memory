"""Diff baseline logic: assumption text drift when id exists in both with different digest."""


def assumption_text_drift_ids(
    base_digest: dict[str, str], curr_digest: dict[str, str]
) -> list[str]:
    out: list[str] = []
    for aid, bh in base_digest.items():
        if aid not in curr_digest:
            continue
        if bh != curr_digest[aid]:
            out.append(aid)
    return sorted(out)


def test_no_drift_when_same() -> None:
    d = {"x": "abc"}
    assert assumption_text_drift_ids(d, d) == []


def test_drift_when_text_changes() -> None:
    assert assumption_text_drift_ids({"a": "1"}, {"a": "2"}) == ["a"]


def test_ignore_new_assumption() -> None:
    assert assumption_text_drift_ids({"a": "1"}, {"a": "1", "b": "2"}) == []


def test_ignore_removed() -> None:
    assert assumption_text_drift_ids({"a": "1", "b": "2"}, {"a": "1"}) == []
