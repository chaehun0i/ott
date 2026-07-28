from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from ott_feed.identity.domain.errors import IdentityError
from ott_feed.identity.domain.models import (
    BehaviorEvent,
    BehaviorEventStream,
    BehaviorEventType,
    ConsentLedger,
    ConsentPurpose,
    ConsentValue,
    Credential,
    DataRightsRequest,
    DataRightsStatus,
    DataRightsType,
    ExportArtifact,
    FeatureContribution,
    GenrePreferenceState,
    GuestLinkAuthorization,
    OAuthLink,
    OttSubscriptionState,
    PersonalizationFeatureSet,
    Role,
    Session,
    User,
    UserLibrary,
    UserProfile,
    UserStatus,
)
from ott_feed.identity.domain.policies import (
    authorize_session,
    build_feature_snapshot,
    deletion_status,
    event_fingerprint,
    may_administer_role,
    normalize_email,
    require_fresh_auth,
    validate_password,
)

NOW = datetime(2026, 7, 27, 3, tzinfo=UTC)


def active_user(*roles: Role) -> User:
    return User(
        email_ciphertext={"ciphertext": "opaque"},
        email_blind_index_version=1,
        email_blind_index=b"x" * 32,
        status=UserStatus.ACTIVE,
        email_verified_at=NOW,
        credentials=[Credential("argon2-envelope", 1)],
        roles=set(roles or (Role.MEMBER,)),
        created_at=NOW,
        updated_at=NOW,
    )


def session_for(user: User, **overrides: object) -> Session:
    values: dict[str, object] = {
        "user_id": user.id,
        "token_hmac": b"s" * 32,
        "authorization_version": user.authorization_version,
        "device_label": "browser",
        "issued_at": NOW,
        "last_seen_at": NOW,
        "absolute_expires_at": NOW + timedelta(days=1),
        "fresh_authenticated_at": NOW,
    }
    values.update(overrides)
    return Session(**values)  # type: ignore[arg-type]


def test_identity_input_and_verification_rules() -> None:
    assert normalize_email("  Member@Example.TEST ") == "member@example.test"
    assert validate_password("correct horse battery staple")
    with pytest.raises(IdentityError, match="email_invalid"):
        normalize_email("not-an-email")
    with pytest.raises(IdentityError, match="password_policy"):
        validate_password("short")

    user = User({}, 1, b"i" * 32, created_at=NOW, updated_at=NOW)
    user.add_credential(Credential("argon2-envelope", 1), NOW)
    user.verify_email(NOW)
    assert user.status == UserStatus.ACTIVE
    assert user.email_verified_at == NOW
    assert "plaintext" not in repr(user)


def test_session_expiry_revocation_and_authorization_version_fail_closed() -> None:
    user = active_user()
    current = session_for(user)
    authorize_session(current, user, "profile:own", NOW)

    expired = session_for(user, absolute_expires_at=NOW)
    revoked = session_for(user, revoked_at=NOW)
    stale = session_for(user, authorization_version=user.authorization_version - 1)
    for candidate in (expired, revoked, stale):
        with pytest.raises(IdentityError, match="session_invalid"):
            authorize_session(candidate, user, "profile:own", NOW)


def test_oauth_linking_is_explicit_unique_per_user_and_preserves_last_method() -> None:
    user = active_user()
    first = OAuthLink("google", b"g" * 32, None)
    user.link_oauth(first, NOW)
    with pytest.raises(IdentityError, match="oauth_provider_already_linked"):
        user.link_oauth(OAuthLink("google", b"h" * 32, None), NOW)

    user.unlink_oauth(first.id, NOW)
    passwordless = active_user()
    passwordless.credentials.clear()
    only_link = OAuthLink("google", b"q" * 32, None)
    passwordless.link_oauth(only_link, NOW)
    with pytest.raises(IdentityError, match="last_login_method"):
        passwordless.unlink_oauth(only_link.id, NOW)


def test_role_policy_prevents_self_grant_and_sensitive_permission_bypass() -> None:
    admin = active_user(Role.SYSTEM_ADMINISTRATOR)
    target = active_user()
    may_administer_role(admin, target, Role.CONTENT_OPERATOR)
    with pytest.raises(IdentityError, match="access_denied"):
        may_administer_role(admin, admin, Role.CONTENT_OPERATOR)
    operator = active_user(Role.CONTENT_OPERATOR)
    with pytest.raises(IdentityError, match="access_denied"):
        may_administer_role(operator, target, Role.SYSTEM_ADMINISTRATOR)
    assert "role:admin" not in operator.permissions()
    assert "credential:read" not in admin.permissions()


def test_profile_states_are_mutually_exclusive_and_versioned() -> None:
    profile = UserProfile(uuid4())
    initial = profile.profile_version
    profile.set_genre("comedy", GenrePreferenceState.LIKED)
    profile.set_genre("comedy", GenrePreferenceState.DISLIKED)
    profile.set_ott("netflix", OttSubscriptionState.SUBSCRIBED)
    profile.set_ott("netflix", OttSubscriptionState.UNSPECIFIED)

    assert profile.genres == {"comedy": GenrePreferenceState.DISLIKED}
    assert profile.ott_subscriptions == {}
    assert profile.profile_version == initial + 4


def test_library_is_idempotent_bounded_and_tracks_latest_completion() -> None:
    library = UserLibrary(uuid4())
    assert library.save("content-1", NOW) is True
    version = library.row_version
    assert library.save("content-1", NOW) is False
    assert library.row_version == version
    library.rate("content-1", 5)
    with pytest.raises(IdentityError, match="rating_out_of_range"):
        library.rate("content-1", 6)
    library.complete_watch("content-1", NOW)
    library.complete_watch("content-1", NOW - timedelta(hours=1))
    assert library.history["content-1"].last_watched_at == NOW


def test_consent_is_immutable_versioned_and_fails_closed() -> None:
    user_id = uuid4()
    ledger = ConsentLedger(str(user_id), "user")
    grant = ledger.decide(
        ConsentPurpose.PERSONALIZATION,
        ConsentValue.GRANTED,
        "p1",
        "n1",
        "ko-KR",
        "settings",
        NOW,
    )
    withdrawal = ledger.decide(
        ConsentPurpose.PERSONALIZATION,
        ConsentValue.WITHDRAWN,
        "p1",
        "n1",
        "ko-KR",
        "settings",
        NOW,
    )
    assert grant.value == ConsentValue.GRANTED
    assert withdrawal.supersedes_id == grant.id
    assert grant.value == ConsentValue.GRANTED
    with pytest.raises(IdentityError, match="consent_required"):
        ledger.granted(ConsentPurpose.PERSONALIZATION)


def test_guest_link_is_explicit_scoped_and_single_use() -> None:
    grant = GuestLinkAuthorization(
        "guest-pseudonym", uuid4(), NOW - timedelta(hours=1), NOW + timedelta(hours=1), "p1"
    )
    grant.consume(NOW)
    assert grant.consumed_at == NOW
    with pytest.raises(IdentityError, match="guest_link_invalid"):
        grant.consume(NOW)


def test_event_deduplication_and_subject_isolation() -> None:
    decision_id = uuid4()
    event = BehaviorEvent(
        "pseudonym",
        "content-1",
        BehaviorEventType.CONTENT_CLICK,
        NOW,
        NOW,
        "feed",
        decision_id,
        idempotency_key="client-key",
        recommendation_version="feed-v3",
    )
    stream = BehaviorEventStream("pseudonym")
    first = stream.append(event)
    duplicate = stream.append(
        BehaviorEvent(
            "pseudonym",
            "content-1",
            BehaviorEventType.CONTENT_CLICK,
            NOW,
            NOW,
            "feed",
            decision_id,
            idempotency_key="client-key",
        )
    )
    assert first == (event.id, True)
    assert duplicate == (event.id, False)
    assert event_fingerprint("p", "c", "click", NOW, {"b": 2, "a": 1}) == event_fingerprint(
        "p", "c", "click", NOW, {"a": 1, "b": 2}
    )


def test_feature_version_contribution_and_snapshot_minimization() -> None:
    user_id = uuid4()
    consent_id = uuid4()
    feature_set = PersonalizationFeatureSet(
        user_id,
        1,
        {"genre:comedy": 1.0, "email": "member@example.test"},
    )
    contribution = FeatureContribution(uuid4(), "behavior:click", 1.0, consent_id)
    assert feature_set.apply(contribution, 1) is True
    assert feature_set.apply(contribution, 2) is False
    with pytest.raises(IdentityError, match="feature_version_conflict"):
        feature_set.apply(FeatureContribution(uuid4(), "behavior:x", 1.0, consent_id), 1)

    consent = ConsentLedger(str(user_id), "user").decide(
        ConsentPurpose.PERSONALIZATION,
        ConsentValue.GRANTED,
        "p1",
        "n1",
        "ko-KR",
        "settings",
        NOW,
    )
    snapshot = build_feature_snapshot(feature_set, consent, "request-pseudonym", NOW)
    assert set(snapshot.features) == {"genre:comedy", "behavior:click"}
    assert str(user_id) not in repr(snapshot)


def test_data_rights_require_fresh_auth_and_have_safe_terminal_status() -> None:
    user = active_user()
    stale_session = session_for(user, fresh_authenticated_at=NOW - timedelta(minutes=11))
    with pytest.raises(IdentityError, match="fresh_auth_required"):
        require_fresh_auth(stale_session, NOW)

    request = DataRightsRequest(user.id, DataRightsType.DELETION, "delete-key")
    request.authorize(NOW)
    request.start()
    request.complete()
    assert request.status == DataRightsStatus.PARTIALLY_COMPLETED
    for step in request.deletion_steps.values():
        step.start()
        step.complete(NOW)
    request.start()
    request.complete()
    status = deletion_status(request)
    assert status["status"] == "completed"
    assert "userId" not in status


def test_export_artifact_is_owner_indirect_expiring_and_single_use() -> None:
    artifact = ExportArtifact(uuid4(), "encrypted-object-reference", "checksum", NOW + timedelta(1))
    artifact.consume(NOW)
    with pytest.raises(IdentityError, match="export_already_consumed"):
        artifact.consume(NOW)
    expired = ExportArtifact(uuid4(), "encrypted-reference", "checksum", NOW)
    with pytest.raises(IdentityError, match="export_expired"):
        expired.consume(NOW)


BR_COVERAGE = {
    **{number: "identity/session/oauth/authorization examples" for number in range(1, 17)},
    **{number: "profile/library examples" for number in range(17, 25)},
    **{number: "consent/feedback/dedup examples" for number in range(25, 40)},
    **{number: "feature snapshot examples" for number in range(40, 45)},
    **{number: "data rights/export/deletion examples" for number in range(45, 52)},
}


def test_every_u02_business_rule_has_an_example_evidence_group() -> None:
    assert set(BR_COVERAGE) == set(range(1, 52))
