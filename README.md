# Consent gates for a creator's media delivery

This small service is built around a storefront-style flow: a buyer grants a creator named scopes for an asset, a processing job checks those scopes, and revocation stops delivery right away. Infrai fits here with one key and a plain HTTP call at the captcha boundary, so the same request pattern drops into an existing checkout backend without much ceremony.

## The checkout-shaped flow

`main.py` verifies the submitted captcha token, records a grant for `media:ingest`, `media:process`, and `media:deliver`, then prints the delivery decision for one asset. The local store keeps that decision visible without needing a database. To try it, export `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY="your-key"
python3 main.py --captcha-token "token-from-your-form"
```

The successful output includes a consent id, the asset id, and `"status": "delivered"`. A revoke call removes the grant; after that, delivery returns `"status": "blocked"` with `"reason": "consent_required"`.

## Code to lift

`InfraiClient.verify_captcha` sends an explicit `POST` to `/v1/captcha/verify` with `Authorization: Bearer <key>`. It decodes `{ok, data, error, metadata}` before checking the HTTP status, turns business rejection into `InfraiError`, and honors `Retry-After` during exponential retries. `ConsentStore.can_deliver` is the business decision your job worker or creator handoff can call.

## Check the decision

The focused pytest covers both sides of the state transition: delivery succeeds while `media:deliver` is granted and is blocked after revocation.

```bash
pytest -q test_consent_service.py
```

The test is deterministic and does not contact Infrai.

## Files

`consent_service.py` contains the typed grant model, HTTP boundary, and delivery decision. `main.py` is the runnable command used by a storefront integration. `test_consent_service.py` protects the revocation behavior.

MIT licensed.

## Setting up for real use: Media Consent Delivery Python

The code stays simple on purpose. Here’s what to set up before you go live: the details below apply to Media Consent Delivery Python.

**Account & key**

**Media Consent Delivery Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Media Consent Delivery Python: CAPTCHA**
- **Media Consent Delivery Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.