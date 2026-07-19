"""Same real value -> same pen name, across documents in one session."""

from penname.core.engine import PennameSession


def test_same_value_same_pen_name_across_documents() -> None:
    session = PennameSession()
    doc_a = "Please thank Margaret Wilson for her gift. Margaret Wilson gave in June."
    doc_b = "Margaret Wilson also volunteers on Tuesdays with Sarah Chen."

    result_a = session.pseudonymize(doc_a)
    result_b = session.pseudonymize(doc_b)

    pens_a = {e.original: e.pen_name for e in result_a.mapping.entries}
    pens_b = {e.original: e.pen_name for e in result_b.mapping.entries}

    assert "Margaret Wilson" in pens_a and "Margaret Wilson" in pens_b
    assert pens_a["Margaret Wilson"] == pens_b["Margaret Wilson"]


def test_distinct_values_get_distinct_pen_names() -> None:
    session = PennameSession()
    result = session.pseudonymize(
        "Contact Robert Castellano, Maria Castellano-Reyes, and James Whitfield."
    )

    pens = [e.pen_name for e in result.mapping.entries]
    assert len(pens) == len(set(pens))
