# Open-source app opportunities

This is an initial product hypothesis list, not proof that any idea will earn money. Existing projects demonstrate active development in these areas, which also means a generic clone will have weak differentiation. Validate with interviews and a small landing-page or prototype test before committing to a second product.

## Shortlist

| Rank | Idea | Everyday problem | Differentiator to test | Possible ethical revenue |
| --- | --- | --- | --- | --- |
| 1 | Home Admin Vault | People lose appliance receipts, warranty dates, manuals, service history, and renewal dates across email and paper. | Local-first inbox that turns a forwarded or scanned document into a searchable item and reminders; exportable archive; household sharing is optional. Avoid becoming another general-purpose inventory catalog. | Free local app; paid hosted sync/backup and household sharing; optional one-time supporter purchase. |
| 2 | Pantry & Expiry Companion | Households forget what food they have and throw it away. | Fast barcode/photo entry, expiry reminders, flexible “use soon” list, and meal suggestions that work offline without requiring an AI account. | Free core; paid optional household sync, recipe packs, or hosted backup. |
| 3 | Subscription & Renewal Ledger | People miss trials, annual renewals, and cancellation windows. | Manual-first calendar and local notifications with receipts and cancellation instructions; no bank credential access or opaque transaction scraping. | Free local app; optional paid sync, multi-device backup, or family plan. |

## Competitive evidence and implications

- Home inventory is already served by [Kept](https://github.com/keptinventory/kept), which describes QR labels, item/location records, and household workflows. That makes the Home Admin Vault valuable only if it focuses on documents and lifecycle reminders, not generic item lists.
- Personal finance and automatic message ingestion are also active areas; [Pckt](https://github.com/pritam-ravani/pckt) describes phone-local expense tracking from bank SMS/email. A new app should avoid handling bank credentials and should prove that manual entry or document capture is materially easier.
- Receipt capture and expense tracking have established free/open-source alternatives, including [My Expenses](https://f-droid.org/en/packages/org.totschnig.myexpenses/). Treat broad expense tracking as a crowded category.

These links indicate competing products and feature expectations; they do not establish customer willingness to pay. Before development, interview 10–15 people in the target segment, test the main workflow with a clickable prototype, and ask what they currently use and what they would pay to avoid. Record the findings and a stop/go threshold.

## Monetization and distribution constraints

Keep the useful core open and usable without an account. Charge for ongoing costs such as hosted sync, encrypted backup, shared household spaces, or support; do not sell personal documents, transaction data, or attention through intrusive ads. Offer a portable export and a self-host option if the architecture supports it.

Store sales are not guaranteed. Apple’s current [business model guidance](https://developer.apple.com/app-store/business-models/) describes paid downloads and subscriptions; the [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) govern in-app purchases and subscriptions. Plan store billing and review requirements before designing a paid mobile feature. App Store distribution also requires Apple Developer Program membership; see [enrollment](https://developer.apple.com/help/account/membership/program-enrollment/).

## Validation gate

Do not start implementation until one concept has: (1) a named audience and top task, (2) evidence from interviews or a usage test, (3) a narrow first release, (4) a privacy/data-retention model, and (5) a revenue experiment that does not make the free core deceptive or unusable.
