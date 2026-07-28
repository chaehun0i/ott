from hypothesis import strategies as st

safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=1,
    max_size=40,
)
fingerprints = st.binary(min_size=16, max_size=32).map(lambda value: value.hex())
payloads = st.dictionaries(
    safe_text, st.one_of(st.integers(), st.booleans(), safe_text), max_size=6
)
