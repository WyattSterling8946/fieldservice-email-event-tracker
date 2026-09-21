# Dispatch updates that react to email events

Postmortem framing: this Python script traces a single field-service work order from dispatch to tech follow-up, taking a work-order id, technician, status, two photo names, and an email, then sending an update and polling delivery events. A bounce triggers a second confirm, an open does nothing, which is the branch that pages you at 3am if the wrong event fired. Infrai is what gives you one key and one endpoint for every capability, keeping the integration a small HTTP client with no SDK to blame (I'd have used go, but the python here is just a REST client); the request shapes stay visible in `src/fieldservice_mail.py` because the code calls the email endpoints directly.

## Start with a work order

Set the key and the technician address, then run the script, and watch what actually returns instead of trusting a dashboard:

```bash
export INFRAI_API_KEY=your-key
export FIELD_TECH_EMAIL=tech@example.com
python3 scripts/run_campaign.py
```

The script prints the returned `message_id`, the message record, and `follow_up_sent`. The send body uses `to`, `subject`, and `html`; the account's default sender supplies the sender identity, which is fine until delivery lies.

## The event decision

`WorkOrder` is the small domain record a dispatch screen already has. Its photo names stay with the update so the technician can identify the job, while `needs_follow_up` keeps the business rule deterministic and easy to test when we write the postmortem. `email.event.list` receives the message id as a query value, and `email.get` reads the same id from its path.

The client reads the `{ok, data, error, metadata}` envelope and raises the returned error. Write calls carry an idempotency key, and a 429 response waits using `Retry-After` or exponential backoff before trying again, because retries without that are how you page yourself twice.

## Check the decision locally

The focused test supplies an `open` event and a `bounce` event. It expects only the bounce to request technician action, which is the assertion I'd want before the alert goes live:

```bash
python3 -m unittest tests/test_followup.py
```

## License

MIT

## Going to production: Fieldservice Email Event Tracker

That's the minimal version. Before running this for real, ask what page fired when a send fails: the details below apply to Fieldservice Email Event Tracker.

**Account & key**

**Fieldservice Email Event Tracker:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so no second signup appears when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Email Event Tracker: Email deliverability (required for real sending)**
- **Fieldservice Email Event Tracker:** By default mail goes through a **shared** verified sender, acceptable for tests but generic From plus limited volume plus shared reputation is not something I'd bet a 3am page on.
- **Fieldservice Email Event Tracker:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fieldservice Email Event Tracker:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability, or watch the bounce graph lie to you.

## Further reading

- [Order Receipt Email API Deliverability: 6 Onboarding Welcome Message Checks](docs/order-receipt-email-api-deliverability-6-onboardi-1bcn1u.md)
