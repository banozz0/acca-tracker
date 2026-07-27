#!/usr/bin/env python3
"""Offline unit tests for fetch-scores.py (no network). Run:

    python3 scripts/test_fetch_scores.py
"""
import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "fetch_scores", Path(__file__).with_name("fetch-scores.py"))
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)


def event(home, away, home_score, away_score, state="post", desc="Full Time", clock=""):
    """ESPN-shaped event; ESPN order is away-first surprisingly often, so the
    first competitor here is the AWAY team to prove orientation is by name."""
    def comp(name, score):
        return {"team": {"displayName": name, "shortDisplayName": name.split()[0]},
                "score": score}
    return {"competitions": [{"competitors": [comp(away, away_score), comp(home, home_score)]}],
            "status": {"type": {"state": state, "description": desc}, "displayClock": clock}}


class TestTeamLevel(unittest.TestCase):
    def test_exact_and_accents(self):
        self.assertEqual(fs.team_level("Curaçao", "Curacao"), 3)
        self.assertEqual(fs.norm("Bayern München FC."), "bayern munchen")

    def test_token_subset(self):
        self.assertEqual(fs.team_level("Bayern", "Bayern Munich"), 2)

    def test_prefix_is_weak(self):
        self.assertEqual(fs.team_level("Man United", "Manchester United"), 1)
        self.assertEqual(fs.team_level("Niger", "Nigeria"), 1)

    def test_no_match(self):
        self.assertEqual(fs.team_level("Leeds United", "Newcastle United"), 0)
        self.assertEqual(fs.team_level("Arsenal", "Chelsea"), 0)


class TestLookup(unittest.TestCase):
    def test_score_orientation_by_name(self):
        r = fs.lookup([event("Arsenal", "Chelsea", "2", "0")], "Arsenal", "Chelsea")
        self.assertEqual((r["home_score"], r["away_score"]), ("2", "0"))
        self.assertFalse(r["weak"])

    def test_exact_beats_weak_lookalike(self):
        pool = [event("Nigeria", "Ghana", "3", "0"), event("Niger", "Ghana", "1", "1")]
        r = fs.lookup(pool, "Niger", "Ghana")
        self.assertEqual(r["espn_home"], "Niger")
        self.assertEqual((r["home_score"], r["away_score"]), ("1", "1"))

    def test_weak_match_is_flagged(self):
        r = fs.lookup([event("Nigeria", "Ghana", "3", "0")], "Niger", "Ghana")
        self.assertTrue(r["weak"])
        self.assertEqual(r["espn_home"], "Nigeria")

    def test_same_competitor_cannot_match_both_sides(self):
        self.assertIsNone(
            fs.lookup([event("Manchester United", "Newcastle United", "1", "1")],
                      "Leeds United", "Everton"))

    def test_not_found(self):
        self.assertIsNone(fs.lookup([event("Arsenal", "Chelsea", "2", "0")], "Spain", "Sweden"))


class TestFetchErrorIsolation(unittest.TestCase):
    def run_main(self, slip, run_dates, fetch_results):
        old = fs.SLIP, fs.RUN_DATES, fs.fetch
        fs.SLIP, fs.RUN_DATES = slip, run_dates
        fs.fetch = lambda d: fetch_results[d]
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                fs.main()
        finally:
            fs.SLIP, fs.RUN_DATES, fs.fetch = old
        return out.getvalue()

    def test_one_failed_date_does_not_poison_other_legs(self):
        out = self.run_main(
            slip=[(1, "Arsenal", "Chelsea", "20260101", "Arsenal win"),
                  (2, "Spain", "Sweden", "20260102", "BTTS: yes"),
                  (3, "Belgium", "Egypt", "20260103", "Over 2.5 goals")],
            run_dates=["20260101", "20260102"],
            fetch_results={"20260101": ([event("Arsenal", "Chelsea", "2", "0")], None),
                           "20260102": ([], "HTTP 500")})
        self.assertIn("Leg 1: Arsenal 2-0 Chelsea", out)
        self.assertIn("FINISHED (Full Time)", out)
        self.assertIn("market: Arsenal win", out)
        self.assertIn("Leg 2: Spain vs Sweden [20260102] -> ESPN fetch failed", out)
        self.assertIn("WARNING: ESPN fetch failed for 20260102: HTTP 500", out)
        self.assertIn("Leg 3: Belgium vs Egypt [20260103] -> future date, not checked", out)

    def test_live_clock_and_weak_warning_in_output(self):
        out = self.run_main(
            slip=[(1, "Niger", "Ghana", "20260101", "Match result: Niger win")],
            run_dates=["20260101"],
            fetch_results={"20260101": ([event("Nigeria", "Ghana", "1", "0",
                                               state="in", desc="First Half",
                                               clock="23'")], None)})
        self.assertIn("LIVE (First Half) 23'", out)
        self.assertIn("WEAK NAME MATCH", out)
        self.assertIn("Nigeria vs Ghana", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
