"""Checks for the observed Amazon JIC wire shape and the captured samples."""

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from amazon_jic import decode_jic, decode_jic_url  # noqa: E402


class JicDecoderTest(unittest.TestCase):
    def test_user_supplied_blue_jackets_link(self):
        with (ROOT / "docs" / "amazon_jic_samples_20261013.csv").open(newline="") as source:
            row = next(row for row in csv.DictReader(source) if row["source_kind"] == "user_supplied_detail")
        hint = decode_jic_url(row["detail_url"])
        self.assertEqual(hint.benefit_ids, ("nhlcolumbusbluejackets",))
        self.assertEqual(hint.offer_types, ("subscription",))
        self.assertEqual(
            hint.channel_tier_ids,
            ("amzn1.dv.channelTier.32aa5aae-1ee1-d2f5-9f41-000b42e5e42a",),
        )

    def test_sample_crosswalk(self):
        with (ROOT / "docs" / "amazon_jic_samples_20261013.csv").open(newline="") as source:
            rows = list(csv.DictReader(source))
        self.assertGreaterEqual(len(rows), 30)
        decoded = 0
        for row in rows:
            with self.subTest(source=row["source_url"], jic=row["jic"][:20]):
                if not row["jic"]:
                    self.assertEqual(row["jic_benefit_ids"], "")
                    continue
                hint = decode_jic(row["jic"])
                self.assertEqual(hint, decode_jic_url(row["detail_url"]))
                self.assertEqual(hint.prefix, int(row["jic_prefix"]))
                self.assertEqual(";".join(hint.benefit_ids), row["jic_benefit_ids"])
                self.assertEqual(";".join(hint.offer_types), row["jic_offer_type"])
                self.assertEqual(";".join(hint.channel_tier_ids), row["jic_channel_tier_id"])
                decoded += 1
        self.assertGreaterEqual(decoded, 20)

    def test_multiple_benefits_and_tiers_are_preserved(self):
        with (ROOT / "docs" / "amazon_jic_samples_20261013.csv").open(newline="") as source:
            rows = list(csv.DictReader(source))
        peacock = next(row for row in rows if row["requested_benefit_id"] == "peacockus" and row["jic_channel_tier_id"])
        max_row = next(row for row in rows if row["requested_benefit_id"] == "maxliveeventsus" and row["jic_channel_tier_id"])
        self.assertEqual(len(decode_jic(peacock["jic"]).benefit_ids), 3)
        self.assertEqual(len(decode_jic(max_row["jic"]).channel_tier_ids), 3)

    def test_observed_tiers_have_no_cross_provider_collision(self):
        with (ROOT / "docs" / "amazon_jic_samples_20261013.csv").open(newline="") as source:
            rows = list(csv.DictReader(source))
        tier_services = {}
        for row in rows:
            for tier in decode_jic(row["jic"]).channel_tier_ids if row["jic"] else ():
                tier_services.setdefault(tier, set()).add(row["fdl_service_code"])
        self.assertEqual(len(tier_services), 15)
        self.assertTrue(all(len(services) == 1 and "" not in services for services in tier_services.values()))

    def test_generic_token_has_no_provider_or_tier(self):
        hint = decode_jic("8|EgNhbGw=")
        self.assertEqual(hint.benefit_ids, ())
        self.assertEqual(hint.offer_types, ("all",))
        self.assertEqual(hint.channel_tier_ids, ())
        self.assertIsNone(decode_jic_url("https://www.amazon.com/gp/video/detail/B0HFF17TWK"))

    def test_malformed_tokens_are_rejected(self):
        for value in ("", "x|EgNhbGw=", "7|EgNhbGw=", "8|!!!!!!==", "4|Cg==", "4|GgA="):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_jic(value)


if __name__ == "__main__":
    unittest.main()
