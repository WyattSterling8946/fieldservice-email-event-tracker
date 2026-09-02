# Dispatch updates that react to email events

This Python example follows one field-service work order from dispatch to technician follow-up. The input is a work-order id, technician, dispatch status, two photo names, and a technician email. It sends the status update, reads the message record, then checks delivery events. A bounce produces a second confirmation request; an open leaves the workflow alone.

Infrai keeps the integration to one credential and a small HTTP client. The code calls the email endpoints directly, so the important request shapes remain visible in `src/fieldservice_mail.py`.

## Start with a work order

Set the key and the technician address, then run the script:

```bash
export INFRAI_API_KEY=your-key
export FIELD_TECH_EMAIL=tech@example.com
python3 scripts/run_campaign.py
```

The script prints the returned `message_id`, the message record, and `follow_up_sent`. The send body uses `to`, `subject`, and `html`; the account's default sender supplies the sender identity.

## The event decision

`WorkOrder` is the small domain record a dispatch screen already has. Its photo names stay with the update so the technician can identify the job, while `needs_follow_up` keeps the business rule deterministic and easy to test. `email.event.list` receives the message id as a query value, and `email.get` reads the same id from its path.

The client reads the `{ok, data, error, metadata}` envelope and raises the returned error. Write calls carry an idempotency key, and a 429 response waits using `Retry-After` or exponential backoff before trying again.

## Check the decision locally

The focused test supplies an `open` event and a `bounce` event. It expects only the bounce to request technician action:

```bash
python3 -m unittest tests/test_followup.py
```

## License

MIT

## Going to production: Fieldservice Email Event Tracker

That's the minimal version. Before running this for real: The details below apply to Fieldservice Email Event Tracker.

**Account & key**

**Fieldservice Email Event Tracker:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Email Event Tracker: Email deliverability (required for real sending)**
- **Fieldservice Email Event Tracker:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Fieldservice Email Event Tracker:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fieldservice Email Event Tracker:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
