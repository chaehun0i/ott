from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule
from pydantic import TypeAdapter

from ott_feed.identity.domain.errors import IdentityError
from ott_feed.identity.domain.models import (
    BehaviorEvent,
    BehaviorEventStream,
    BehaviorEventType,
    ConsentDecision,
    ConsentLedger,
    ConsentPurpose,
    ConsentValue,
    Credential,
    DataRightsRequest,
    DataRightsStatus,
    DataRightsType,
    FeatureSnapshot,
    GenrePreferenceState,
    OAuthLink,
    PersonalizationFeatureSet,
    Role,
    Session,
    User,
    UserLibrary,
    UserProfile,
    UserStatus,
)
from ott_feed.identity.domain.policies import authorize_session, build_feature_snapshot
from tests.strategies.identity import (
    content_ids,
    feature_values,
    genre_ids,
    invalid_ratings,
    provider_subjects,
    ratings,
)

pytestmark = pytest.mark.pbt
NOW = datetime(2026, 7, 27, tzinfo=UTC)


@given(content_id=content_ids, repetitions=st.integers(1, 30))
def test_pbt_u02_01_save_idempotency(content_id: str, repetitions: int) -> None:
    library = UserLibrary(uuid4())
    initial = library.row_version
    results = [library.save(content_id, NOW) for _ in range(repetitions)]
    assert len(library.saved) == 1
    assert sum(results) == 1
    assert library.row_version == initial + 1


@given(valid=ratings, invalid=invalid_ratings)
def test_pbt_u02_02_rating_bounds(valid: int, invalid: int) -> None:
    library = UserLibrary(uuid4())
    library.rate("content", valid)
    before = asdict(library)
    with pytest.raises(IdentityError, match="rating_out_of_range"):
        library.rate("content", invalid)
    assert asdict(library) == before


@given(
    genre=genre_ids,
    states=st.lists(
        st.sampled_from([GenrePreferenceState.LIKED, GenrePreferenceState.DISLIKED, None]),
        min_size=1,
        max_size=30,
    ),
)
def test_pbt_u02_03_preference_exclusivity(
    genre: str, states: list[GenrePreferenceState | None]
) -> None:
    profile = UserProfile(uuid4())
    for state in states:
        profile.set_genre(genre, state)
    assert len(profile.genres) <= 1
    if states[-1] is None:
        assert genre not in profile.genres
    else:
        assert profile.genres[genre] == states[-1]


class SessionLifecycle(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.user = User(
            {},
            1,
            b"i" * 32,
            status=UserStatus.ACTIVE,
            roles={Role.MEMBER},
            created_at=NOW,
            updated_at=NOW,
        )
        self.session = Session(
            self.user.id,
            b"s" * 32,
            self.user.authorization_version,
            "device",
            issued_at=NOW,
            last_seen_at=NOW,
            absolute_expires_at=NOW + timedelta(days=1),
            fresh_authenticated_at=NOW,
        )
        self.revoked = False

    @rule()
    def revoke(self) -> None:
        self.session.revoke("property", NOW)
        self.revoked = True

    @rule()
    def touch_before_revocation(self) -> None:
        if not self.revoked:
            self.session.touch(NOW + timedelta(seconds=1))

    @invariant()
    def pbt_u02_04_revocation_is_terminal(self) -> None:
        if self.revoked:
            with pytest.raises(IdentityError):
                authorize_session(self.session, self.user, "profile:own", NOW)


TestSessionLifecycle = SessionLifecycle.TestCase


@given(subject=provider_subjects, repetitions=st.integers(1, 20))
def test_pbt_u02_05_oauth_link_uniqueness(subject: bytes, repetitions: int) -> None:
    user = User({}, 1, b"i" * 32, created_at=NOW, updated_at=NOW)
    user.add_credential(Credential("hash", 1), NOW)
    user.link_oauth(OAuthLink("google", subject, None), NOW)
    for _ in range(repetitions):
        with pytest.raises(IdentityError):
            user.link_oauth(OAuthLink("google", subject, None), NOW)
    assert sum(link.active for link in user.oauth_links) == 1


class ConsentLifecycle(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.user_id = uuid4()
        self.ledger = ConsentLedger(str(self.user_id), "user")
        self.events: list[str] = []
        self.features: dict[str, float] = {}

    @rule()
    def grant(self) -> None:
        self.ledger.decide(
            ConsentPurpose.PERSONALIZATION,
            ConsentValue.GRANTED,
            "p1",
            "n1",
            "ko-KR",
            "settings",
            NOW,
        )

    @rule()
    def collect_if_granted(self) -> None:
        try:
            self.ledger.granted(ConsentPurpose.PERSONALIZATION)
        except IdentityError:
            return
        self.events.append("pseudonymous-event")
        self.features["behavior:click"] = 1.0

    @rule()
    def withdraw_and_cleanup(self) -> None:
        self.ledger.decide(
            ConsentPurpose.PERSONALIZATION,
            ConsentValue.WITHDRAWN,
            "p1",
            "n1",
            "ko-KR",
            "settings",
            NOW,
        )
        self.events.clear()
        self.features.clear()

    @invariant()
    def pbt_u02_06_and_08_consent_never_bypasses_and_withdrawal_closes(self) -> None:
        current = self.ledger.current(ConsentPurpose.PERSONALIZATION)
        if current is None or current.value != ConsentValue.GRANTED:
            with pytest.raises(IdentityError):
                self.ledger.granted(ConsentPurpose.PERSONALIZATION)
            assert not self.events
            assert not self.features


TestConsentLifecycle = ConsentLifecycle.TestCase


@given(key=st.text(min_size=1, max_size=40), count=st.integers(2, 30))
def test_pbt_u02_07_duplicate_event_isolation(key: str, count: int) -> None:
    consent_id = uuid4()
    stream = BehaviorEventStream("subject")
    ids: set[UUID] = set()
    created = 0
    for _ in range(count):
        event = BehaviorEvent(
            "subject",
            "content",
            BehaviorEventType.CONTENT_CLICK,
            NOW,
            NOW,
            "feed",
            consent_id,
            idempotency_key=key,
        )
        event_id, was_created = stream.append(event)
        ids.add(event_id)
        created += int(was_created)
    assert len(ids) == 1
    assert created == 1


@given(values=feature_values)
def test_pbt_u02_09_snapshot_minimization(values: dict[str, int | float | bool]) -> None:
    user_id = uuid4()
    feature_set = PersonalizationFeatureSet(user_id, 1, values)
    consent = ConsentDecision(
        str(user_id),
        "user",
        ConsentPurpose.PERSONALIZATION,
        ConsentValue.GRANTED,
        "p1",
        "n1",
        "ko-KR",
        "settings",
        1,
        NOW,
    )
    snapshot = build_feature_snapshot(feature_set, consent, "request-subject", NOW)
    assert all(
        key.startswith(("genre:", "ott:", "library:", "behavior:")) for key in snapshot.features
    )
    assert str(user_id) not in repr(snapshot)


class DeletionLifecycle(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.user = User({}, 1, b"i" * 32, status=UserStatus.ACTIVE, created_at=NOW, updated_at=NOW)
        self.request = DataRightsRequest(self.user.id, DataRightsType.DELETION, "delete-key")
        self.deleted = False

    @rule()
    def authorize(self) -> None:
        if self.request.status == DataRightsStatus.REQUESTED:
            self.request.authorize(NOW)

    @rule()
    def process(self) -> None:
        if self.request.status in {
            DataRightsStatus.AUTHORIZED,
            DataRightsStatus.PARTIALLY_COMPLETED,
        }:
            self.request.start()
            for step in self.request.deletion_steps.values():
                step.start()
                step.complete(NOW)
            self.request.complete()
            self.user.begin_deletion(NOW)
            self.user.complete_deletion(NOW)
            self.deleted = True

    @invariant()
    def pbt_u02_10_deleted_is_terminal(self) -> None:
        if self.deleted:
            assert self.user.status == UserStatus.DELETED
            with pytest.raises(IdentityError):
                self.user.assert_active()


TestDeletionLifecycle = DeletionLifecycle.TestCase
FEATURE_SNAPSHOT_ADAPTER = TypeAdapter(FeatureSnapshot)


@given(values=feature_values)
def test_pbt_u02_11_versioned_dto_round_trip(values: dict[str, int | float | bool]) -> None:
    snapshot = FeatureSnapshot(
        "request-subject",
        4,
        3,
        NOW,
        NOW + timedelta(minutes=5),
        values,
    )
    encoded = FEATURE_SNAPSHOT_ADAPTER.dump_json(snapshot)
    assert FEATURE_SNAPSHOT_ADAPTER.validate_json(encoded) == snapshot
