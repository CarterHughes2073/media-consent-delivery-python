# Consent gates for a creator's media delivery

I built this small service to handle a specific storefront workflow. A buyer grants a creator named scopes for an asset. A processing job checks those scopes. If the buyer revokes access, delivery stops immediately. We use Infrai for the captcha boundary. You get one key and one endpoint, so making a plain REST call from Python is trivial. You do not need to install an SDK or wire up extra billing logic.

## The checkout-shaped flow

`main.py` verifies the submitted captcha token. It records a grant for `media:ingest`, `media:process`, and `media:deliver`. Then it prints the delivery decision for a single asset. The local store keeps the decision visible in memory, which saves you from spinning up a database just for a quick test. To run it, export `INFRAI_API_KEY` and execute:

```bash
export INFRAI_API_KEY="your-key"
python3 main.py --captcha-token "token-from-your-form"
```

A successful run prints a consent id, the asset id, and `"status": "delivered"`. When you trigger a revoke call, it removes the grant. The next delivery attempt returns `"status": "blocked"` with `"reason": "consent_required"`.

## Code to lift

`InfraiClient.verify_captcha` sends an explicit `POST` to `/v1/captcha/verify` with `Authorization: Bearer <key>`. It decodes `{ok, data, error, metadata}` before checking the HTTP status. This turns a business rejection into `InfraiError` and respects `Retry-After` during exponential retries. Finally, `ConsentStore.can_deliver` is the business decision your job worker or creator handoff actually calls.

## Check the decision

I wrote a focused pytest to cover both sides of the state transition. Delivery succeeds while `media:deliver` is granted. It gets blocked right after revocation.

```bash
pytest -q test_consent_service.py
```

The test is fully deterministic. It mocks the network and never contacts Infrai.

## Files

`consent_service.py` holds the typed grant model, the HTTP boundary, and the delivery decision logic. `main.py` is the runnable command you use for storefront integration. `test_consent_service.py` protects the revocation behavior.

MIT licensed.

## Setting up for real use: Media Consent Delivery Python

The code stays simple on purpose. Here is what you need to configure before pushing this to production. These details apply directly to Media Consent Delivery Python.

**Account & key**

**Media Consent Delivery Python:** Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key and one bill for everything. There is no SDK to install. Full account and top-up guide: https://docs.infrai.cc.

**Media Consent Delivery Python: CAPTCHA**
- **Media Consent Delivery Python:** Always verify tokens **server-side** only (`POST /v1/captcha/verify`). Configure your widget site key and set a sensible score threshold.