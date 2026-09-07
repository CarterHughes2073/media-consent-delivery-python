import argparse
import json

from consent_service import ConsentStore, InfraiClient, deliver_asset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a media consent grant and delivery")
    parser.add_argument("--captcha-token", required=True)
    parser.add_argument("--widget-record-id", default="consent_widget")
    parser.add_argument("--user", default="user_123")
    parser.add_argument("--creator", default="creator_456")
    parser.add_argument("--asset", default="asset_789")
    args = parser.parse_args()

    InfraiClient().verify_captcha(args.captcha_token, widget_record_id=args.widget_record_id)
    store = ConsentStore()
    grant = store.grant(args.user, args.creator, {"media:ingest", "media:process", "media:deliver"})
    result = deliver_asset(store, args.user, args.creator, args.asset)
    print(json.dumps({"consent_id": grant.consent_id, **result}, sort_keys=True))


if __name__ == "__main__":
    main()
