from consent_service import ConsentStore, deliver_asset


def test_revocation_blocks_creator_delivery() -> None:
    store = ConsentStore()
    store.grant("buyer-7", "creator-2", {"media:deliver"})
    assert deliver_asset(store, "buyer-7", "creator-2", "clip-9")["status"] == "delivered"
    assert store.revoke("buyer-7", "creator-2") is True
    result = deliver_asset(store, "buyer-7", "creator-2", "clip-9")
    assert result == {"asset_id": "clip-9", "status": "blocked", "reason": "consent_required"}
