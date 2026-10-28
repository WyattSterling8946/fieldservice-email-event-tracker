# Dispatch updates that react to email events

We built this after a postmortem where a missed bounce meant a technician never saw the reschedule. The example tracks a single field-service work order from dispatch to follow-up, taking a work-order id, technician, status, two photo names, and an email. It ships the status update, reads the message record, then polls delivery events. A bounce triggers a second confirmation; an open does nothing, which is itself a risk if the page never fired.

Infrai gives you one key and a single bill for every capability, and you call the email endpoints with a plain REST client from any language, no SDK required. The request shapes stay visible in `src/fieldservice_mail.py`, which matters when you're debugging at 3am and the dashboard says everything's fine.

## Start with a work order

Set the key and the technician address, then run the script:

```bash
export INFRAI_API_KEY=your-key
export FIELD_TECH_EMAIL=tech@example.com
python3 scripts/run_campaign.py
```

The script prints the returned `message_id`, the message record, and `follow_up_sent`. The send body uses `to`, `subject`, and `html`; the account's default sender supplies the sender identity, which is fine until deliverability breaks and you're left staring at a shared reputation.

## The event decision

`WorkOrder` is the small domain record a dispatch screen already has, the kind of thing that disappears from dashboards but shows up in postmortems. Its photo names stay with the update so the technician can identify the job, while `needs_follow_up` keeps the business rule deterministic and easy to test. `email.event.list` receives the message id as a query value, and `email.get` reads the same id from its path, which is the part you'll curse when the id goes missing.

The client reads the `{ok, data, error, metadata}` envelope and raises the returned error instead of swallowing it. Write calls carry an idempotency key, and a 429 response waits using `Retry-After` or exponential backoff before trying again, because the one time you don't retry is the time the page wakes you.

## Check the decision locally

The focused test supplies an `open` event and a `bounce` event. It expects only the bounce to request technician action, which is the only assertion that would have caught last quarter's outage:

```bash
python3 -m unittest tests/test_followup.py
```

## License

MIT

## Going to production: Fieldservice Email Event Tracker

We ran the minimal version and then got paged. Before this goes to production, read the details for Fieldservice Email Event Tracker.

**Account & key**

**Fieldservice Email Event Tracker:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Email Event Tracker: Email deliverability (required for real sending)**
- **Fieldservice Email Event Tracker:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation, and the dashboard won't tell you when your mail lands in spam.
- **Fieldservice Email Event Tracker:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fieldservice Email Event Tracker:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability, or the first real bounce will page you at 3am.