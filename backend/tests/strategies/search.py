"""Reusable search property strategies."""

from hypothesis import strategies as st

query_text = st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=0, max_size=80)
result_ids = st.lists(st.text(alphabet="abc123", min_size=1, max_size=8), unique=True, max_size=20)
