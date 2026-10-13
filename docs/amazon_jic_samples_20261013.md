# Amazon `jic` samples (2026-10-13)

The companion [CSV](amazon_jic_samples_20261013.csv) records the raw token, decoded
fields, source URL, FDL service code, and one destination link carrying each
distinct token. The service code comes from the known storefront benefit ID;
it is a provider hint, not a verified mapping for an arbitrary playable. These were
collected from public US Amazon storefronts of the form
`/gp/video/storefront?benefitId=...`, plus the supplied Blue Jackets detail link
and the [NBA's public channel link](https://support.watch.nba.com/hc/en-us/articles/16847553816087-US-TV-Provider-Partners).
No signed-in account or entitlement was used. The capture contains 26 distinct
tokens, including 15 distinct channel-tier IDs across ten provider groups.

The portion after `number|` is base64 containing protobuf-style length-delimited
strings. Field 1 repeats benefit IDs, field 2 describes the offer type, and field
3 repeats `amzn1.dv.channelTier.*` IDs. In all 26 captured tokens, the numeric
prefix equals the base64 text length; its broader semantics are unconfirmed.
The strict [decoder](../bin/amazon_jic.py) checks that shape. A token may contain
several benefit IDs or several tier IDs, so neither
field should be assumed one-to-one with a service.

| FDL provider | JIC benefit IDs | Observed channel-tier UUID suffixes |
| --- | --- | --- |
| Blue Jackets Hockey Network | `nhlcolumbusbluejackets` | `32aa5aae-1ee1-d2f5-9f41-000b42e5e42a` (supplied detail URL) |
| MW+ | `mountainwestplus` | `a2d90788-699f-f709-9b13-c0229239db78` |
| Peacock | `peacockus`, `peacockholdoutus`, `peacockadsus` | `a24db6b7-d5db-32c6-8501-eacdf574457d` |
| beIN Sports Connect | `beinus` | `cd161905-ea5d-fa49-d5ca-0dceb4a87bd3` |
| FOX One | `foxoneus`, `foxonebroadcastus` | `98f63cc2-c6c6-7022-27e3-698bc4df8a30` |
| Tennis Channel | `tennischannelus` | `728ec8b2-d6b5-cdfe-b723-b435d978988f` |
| ViX | `vixus` | `5451f4b6-c9fe-4108-b886-07c11f9e4542` |
| ViX Premium | `vixplusus` | `7b6b4537-ee1d-4e1c-bf0b-0617bfd50567`, `3819743e-69d9-415f-b66c-c8ca52b8c9fa` |
| Max | `hbomaxus`, `maxliveeventsus` | `2eb3dd89-5e98-44d8-8a4a-a4390a714388`, `22da3d54-0cca-61ca-cd55-194f03123226`, `417b4733-15ac-4b28-abfb-0997254cab81` |
| Paramount+ | `cbsaapc`, `cbsaacf`, `paramountpremium`, `cbsaalc` | `aa4561d6-ccef-4845-90de-731f84e1b09f`, `b087a614-558d-4c40-a775-6e72da1ead4a`, `2be8e8ae-8fa3-4df8-91f5-0f147e9aa91c` |

The `cbsaacf` and `cbsaapc` storefronts returned the same Paramount+ token and
three tier IDs. No tier ID in this sample crossed between different provider
groups. That is point-in-time evidence; it does not establish that a tier ID
will persist through Amazon catalog or subscription changes.

The sampled storefronts for DAZN, Willow, WNBA League Pass, SquashTV, and free
with ads emitted `jic` values with benefit IDs but **no field 3 tier**. The
[NBA League Pass channel page](https://www.amazon.com/gp/video/channel/7a36cb2b-40e6-40c7-809f-a6cf9b9f0859)
likewise emitted `nbalp|subscription` without a tier. The sampled MLB Network,
FanDuel, Prime, and Blue Jackets storefronts yielded no `jic` detail links;
the Blue Jackets tier above comes from the supplied URL. Bare GTI detail pages
mostly exposed only generic `all` or `svod` tokens.

These are provider-context links, not evidence that an account owns a channel.
The unsigned Blue Jackets detail page still displayed a free-trial offer when
opened with the supplied provider-scoped `jic`. FDL's Apple payloads and stored
playables contain no `jic`, and the current GTI scraper does not retain a
provider-scoped URL. A tier lookup would therefore need a separate, validated
discovery and GTI-to-detail-link join before it could classify playables.
In a spot check of 11 representative live FDL GTIs, nine bare detail pages
exposed a canonical ASIN; none of those ASINs matched the sampled provider
storefront detail links. Two pages did not expose a canonical ASIN. This does
not rule out a future join, but these storefront samples alone cannot establish
one for those playables. The existing benefit-ID mapping and scoped entitlement
fallback remain the classification path; the JIC decoder is audit-only.
