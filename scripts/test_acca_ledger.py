#!/usr/bin/env python3
"""Offline unit tests for acca_ledger.py (no network). Run:

    python3 scripts/test_acca_ledger.py
"""
import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fs = load("fetch_scores", "fetch-scores.py")
al = load("acca_ledger", "acca_ledger.py")


def event(home, away, home_score, away_score, state="post", desc="Full Time",
          home_stats=None, away_stats=None):
    """ESPN-shaped event; away competitor listed first (as ESPN often does)."""
    def comp(name, score, stats):
        c = {"team": {"displayName": name, "shortDisplayName": name.split()[0]},
             "score": score}
        if stats:
            c["statistics"] = [{"name": k, "displayValue": str(v)} for k, v in stats.items()]
        return c
    return {"competitions": [{"competitors": [comp(away, away_score, away_stats),
                                              comp(home, home_score, home_stats)]}],
            "status": {"type": {"state": state, "description": desc}, "displayClock": ""}}


def fight(a, b, winner=None, state="post", desc="Final"):
    """One fight as it appears inside an MMA card's competitions[]."""
    def comp(name, won):
        return {"athlete": {"displayName": name, "shortDisplayName": name.split()[-1]},
                "winner": won}
    return {"competitors": [comp(a, winner == a), comp(b, winner == b)],
            "status": {"type": {"state": state, "description": desc}, "displayClock": ""}}


def settle(market, ev, home="Arsenal", away="Chelsea", sport="soccer/all"):
    r = fs.lookup([ev], home, away)
    return al.settle_leg((1, home, away, "20260101", market, sport), r)


class TestSettleMatchResult(unittest.TestCase):
    def test_win_won_lost_draw(self):
        self.assertEqual(settle("Match result: Arsenal win", event("Arsenal", "Chelsea", "2", "0"))[0], "WON")
        self.assertEqual(settle("Match result: Arsenal win", event("Arsenal", "Chelsea", "0", "2"))[0], "LOST")
        self.assertEqual(settle("Match result: Arsenal win", event("Arsenal", "Chelsea", "1", "1"))[0], "LOST")

    def test_draw_selection(self):
        self.assertEqual(settle("Match result: draw", event("Arsenal", "Chelsea", "1", "1"))[0], "WON")
        self.assertEqual(settle("Match result: draw", event("Arsenal", "Chelsea", "2", "1"))[0], "LOST")

    def test_ambiguous_selection_is_unverifiable(self):
        out = settle("Real win", event("Real Madrid", "Real Sociedad", "2", "0"),
                     home="Real Madrid", away="Real Sociedad")
        self.assertEqual(out[0], "UNVERIFIABLE")

    def test_short_team_name_matches(self):
        self.assertEqual(settle("Match result: CRB win", event("CRB", "Vila Nova", "2", "0"),
                                home="CRB", away="Vila Nova")[0], "WON")

    def test_double_chance_and_dnb(self):
        self.assertEqual(settle("Double chance: Arsenal or draw", event("Arsenal", "Chelsea", "1", "1"))[0], "WON")
        self.assertEqual(settle("Double chance: Arsenal or draw", event("Arsenal", "Chelsea", "0", "1"))[0], "LOST")
        self.assertEqual(settle("Draw no bet: Arsenal", event("Arsenal", "Chelsea", "1", "1"))[0], "VOID")
        self.assertEqual(settle("Draw no bet: Arsenal", event("Arsenal", "Chelsea", "2", "1"))[0], "WON")
        self.assertEqual(settle("Draw no bet: Arsenal", event("Arsenal", "Chelsea", "0", "1"))[0], "LOST")


class TestSettleGoals(unittest.TestCase):
    def test_total_over_under_half_lines(self):
        self.assertEqual(settle("Over 2.5 goals", event("Arsenal", "Chelsea", "2", "1"))[0], "WON")
        self.assertEqual(settle("Over 2.5 goals", event("Arsenal", "Chelsea", "1", "1"))[0], "LOST")
        self.assertEqual(settle("Under 2.5 goals", event("Arsenal", "Chelsea", "1", "1"))[0], "WON")

    def test_whole_line_push_is_void(self):
        self.assertEqual(settle("Over 2 goals", event("Arsenal", "Chelsea", "1", "1"))[0], "VOID")

    def test_team_goals(self):
        self.assertEqual(settle("Arsenal over 1.5 goals", event("Arsenal", "Chelsea", "2", "0"))[0], "WON")
        self.assertEqual(settle("Arsenal over 1.5 goals", event("Arsenal", "Chelsea", "1", "3"))[0], "LOST")

    def test_btts(self):
        self.assertEqual(settle("BTTS: yes", event("Arsenal", "Chelsea", "1", "1"))[0], "WON")
        self.assertEqual(settle("Both teams to score: yes", event("Arsenal", "Chelsea", "1", "0"))[0], "LOST")
        self.assertEqual(settle("Both teams to score: no", event("Arsenal", "Chelsea", "1", "0"))[0], "WON")


class TestSettleStats(unittest.TestCase):
    def test_total_corners(self):
        ev = event("Arsenal", "Chelsea", "1", "0",
                   home_stats={"wonCorners": 6}, away_stats={"wonCorners": 5})
        self.assertEqual(settle("Total corners over 8.5", ev)[0], "WON")

    def test_team_corners(self):
        ev = event("Arsenal", "Chelsea", "1", "0",
                   home_stats={"wonCorners": 4}, away_stats={"wonCorners": 2})
        self.assertEqual(settle("Arsenal over 4.5 corners", ev)[0], "LOST")

    def test_missing_stats_unverifiable(self):
        self.assertEqual(settle("Total corners over 8.5", event("Arsenal", "Chelsea", "1", "0"))[0],
                         "UNVERIFIABLE")

    def test_cards_settle_only_without_reds(self):
        clean = event("Arsenal", "Chelsea", "1", "0",
                      home_stats={"yellowCards": 2, "redCards": 0},
                      away_stats={"yellowCards": 2, "redCards": 0})
        self.assertEqual(settle("Over 3.5 cards", clean)[0], "WON")
        red = event("Arsenal", "Chelsea", "1", "0",
                    home_stats={"yellowCards": 2, "redCards": 1},
                    away_stats={"yellowCards": 2, "redCards": 0})
        self.assertEqual(settle("Over 3.5 cards", red)[0], "UNVERIFIABLE")


class TestSettleGuards(unittest.TestCase):
    def test_not_final_not_found_weak(self):
        self.assertEqual(settle("Arsenal win", event("Arsenal", "Chelsea", "1", "0", state="in",
                                                     desc="First Half"))[0], "UNVERIFIABLE")
        self.assertEqual(al.settle_leg((1, "Arsenal", "Chelsea", "20260101", "Arsenal win",
                                        "soccer/all"), None)[0], "UNVERIFIABLE")
        r = fs.lookup([event("Nigeria", "Ghana", "3", "0")], "Niger", "Ghana")
        self.assertEqual(al.settle_leg((1, "Niger", "Ghana", "20260101", "Niger win",
                                        "soccer/all"), r)[0], "UNVERIFIABLE")

    def test_postponed_is_void(self):
        self.assertEqual(settle("Arsenal win", event("Arsenal", "Chelsea", "0", "0",
                                                     desc="Postponed"))[0], "VOID")

    def test_unsupported_market(self):
        self.assertEqual(settle("First goalscorer: Saka", event("Arsenal", "Chelsea", "2", "0"))[0],
                         "UNVERIFIABLE")


class TestSettleUFC(unittest.TestCase):
    def test_winner_and_no_winner(self):
        events = fs.explode_fights(
            [{"competitions": [fight("Ilia Topuria", "Max Holloway", winner="Ilia Topuria")]}])
        r = fs.lookup(events, "Ilia Topuria", "Max Holloway")
        leg = (1, "Ilia Topuria", "Max Holloway", "20260101", "Fight winner: Topuria", "mma/ufc")
        self.assertEqual(al.settle_leg(leg, r)[0], "WON")
        leg_l = (1, "Ilia Topuria", "Max Holloway", "20260101", "Fight winner: Holloway", "mma/ufc")
        self.assertEqual(al.settle_leg(leg_l, r)[0], "LOST")
        nc = fs.lookup(fs.explode_fights([{"competitions": [fight("Ilia Topuria", "Max Holloway")]}]),
                       "Ilia Topuria", "Max Holloway")
        self.assertEqual(al.settle_leg(leg, nc)[0], "UNVERIFIABLE")


class TestNeverAutoSettled(unittest.TestCase):
    """Markets a bookmaker can settle differently than the raw score suggests
    must always fall through to a manual row."""

    def test_deny_list(self):
        ev = event("Arsenal", "Chelsea", "2", "0")
        for market in ("Handicap: Arsenal -1", "Correct score 2-0 Arsenal",
                       "Arsenal win to nil", "Arsenal clean sheet",
                       "First half over 1.5 goals", "Arsenal to win both halves",
                       "Halftime over 0.5 goals", "1H over 1.5 goals",
                       "Booking points over 30",
                       "Arsenal race to 3 corners", "Winning margin: Arsenal by 2"):
            self.assertEqual(settle(market, ev)[0], "UNVERIFIABLE", market)

    def test_asian_quarter_line(self):
        self.assertEqual(settle("Over 2.25 goals", event("Arsenal", "Chelsea", "2", "0"))[0],
                         "UNVERIFIABLE")

    def test_bare_team_name_is_not_a_result_bet(self):
        self.assertEqual(settle("Arsenal", event("Arsenal", "Chelsea", "2", "0"))[0],
                         "UNVERIFIABLE")

    def test_suspended_live_match_is_not_void(self):
        out = settle("Arsenal win", event("Arsenal", "Chelsea", "1", "0",
                                          state="in", desc="Suspended"))
        self.assertEqual(out[0], "UNVERIFIABLE")

    def test_mma_prop_markets(self):
        events = fs.explode_fights(
            [{"competitions": [fight("Ilia Topuria", "Max Holloway", winner="Ilia Topuria")]}])
        r = fs.lookup(events, "Ilia Topuria", "Max Holloway")
        leg = (1, "Ilia Topuria", "Max Holloway", "20260101",
               "Topuria to win by KO in round 2", "mma/ufc")
        self.assertEqual(al.settle_leg(leg, r)[0], "UNVERIFIABLE")


class TestAccaReturn(unittest.TestCase):
    def test_all_won(self):
        label, ret = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "WON", "2": "WON"}, {})
        self.assertEqual((label, ret), ("Won", Decimal("62.00")))

    def test_any_lost(self):
        label, ret = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "WON", "2": "LOST"}, {})
        self.assertEqual((label, ret), ("Lost", Decimal("0.00")))

    def test_void_recalc_with_odds(self):
        label, ret = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "WON", "2": "VOID"},
                                    {"2": "2.0"})
        self.assertEqual(ret, Decimal("31.00"))
        self.assertIn("void", label.lower())

    def test_void_without_odds_needs_manual(self):
        label, reason = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "WON", "2": "VOID"}, {})
        self.assertIsNone(label)
        self.assertIn("odds", reason)

    def test_all_void_returns_stake(self):
        label, ret = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "VOID", "2": "VOID"}, {})
        self.assertEqual(ret, Decimal("10.00"))
        self.assertIn("void", label.lower())

    def test_leg_odds_disagreeing_with_price_needs_manual(self):
        label, reason = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "WON", "2": "WON"},
                                       {"1": "1.5", "2": "2.0"})
        self.assertIsNone(label)
        self.assertIn("combined", reason)
        # the reason is printed into the cron prompt — it must carry no amounts
        self.assertIsNone(re.search(r"\d", reason))

    def test_lost_acca_settles_despite_odds_mismatch(self):
        # only the winning path uses the price, so a lost acca never needs it
        label, ret = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "LOST", "2": "WON"},
                                    {"1": "1.5", "2": "2.0"})
        self.assertEqual((label, ret), ("Lost", Decimal("0.00")))

    def test_leg_odds_matching_price_settle_fine(self):
        label, ret = al.acca_return(Decimal("10"), Decimal("6.2"), {"1": "WON", "2": "WON"},
                                    {"1": "3.1", "2": "2.0"})
        self.assertEqual((label, ret), ("Won", Decimal("62.00")))


class TestAfterRun(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.ledger = self.dir / "Betting ledger.md"
        self.state = self.dir / "acca-test.state.json"
        self.marker = self.dir / "acca-test.ledger.json"

    def config(self, **kw):
        cfg = {"path": str(self.ledger), "stake": "10", "price": "6.2",
               "currency": "€", "legs": "Arsenal W · O2.5"}
        cfg.update(kw)
        return cfg

    def run_hook(self, slip, config, events):
        out = io.StringIO()
        with redirect_stdout(out):
            al.after_run(slip, config, str(self.state),
                         fetch=lambda sport, date: (events, None), lookup=fs.lookup)
        return out.getvalue()

    def test_no_write_before_all_finished(self):
        self.state.write_text(json.dumps({"1": "LIVE 1-0"}))
        out = self.run_hook([(1, "Arsenal", "Chelsea", "20260101", "Arsenal win")],
                            self.config(),
                            [event("Arsenal", "Chelsea", "1", "0", state="in", desc="First Half")])
        self.assertEqual(out, "")
        self.assertFalse(self.ledger.exists())

    def test_settled_acca_writes_one_row_once(self):
        self.state.write_text(json.dumps({"1": "FINISHED 2-0"}))
        slip = [(1, "Arsenal", "Chelsea", "20260101", "Match result: Arsenal win")]
        events = [event("Arsenal", "Chelsea", "2", "0")]
        out = self.run_hook(slip, self.config(), events)
        self.assertIn("LEDGER: recorded", out)
        # stdout is injected into the cron prompt — amounts must never appear
        self.assertNotIn("€", out)
        text = self.ledger.read_text()
        self.assertIn("type: reference", text)
        self.assertIn("| Date | Legs | Stake | Price | Outcome | Return | Running P&L |", text)
        self.assertIn("| €10.00 | 6.2 | Won | €62.00 | +€52.00 |", text)
        self.assertTrue(self.marker.exists())
        # idempotent: second run adds nothing and stays quiet
        out2 = self.run_hook(slip, self.config(), events)
        self.assertEqual(out2, "")
        self.assertEqual(self.ledger.read_text().count("| Won |"), 1)

    def test_running_total_across_three_accas(self):
        # hand-checked: +52.00, then -10 -> +42.00, then void-recalc +21 -> +63.00
        slip = [(1, "Arsenal", "Chelsea", "20260101", "Match result: Arsenal win"),
                (2, "Spain", "Sweden", "20260101", "Over 2.5 goals")]
        won = [event("Arsenal", "Chelsea", "2", "0"), event("Spain", "Sweden", "2", "1")]
        lost = [event("Arsenal", "Chelsea", "0", "1"), event("Spain", "Sweden", "2", "1")]
        void = [event("Arsenal", "Chelsea", "2", "0"),
                event("Spain", "Sweden", "0", "0", desc="Postponed")]
        for i, (events, cfg) in enumerate([
                (won, self.config()),
                (lost, self.config()),
                (void, self.config(leg_odds={"2": "2.0"}))]):
            state = self.dir / f"acca-{i}.state.json"
            state.write_text(json.dumps({"1": "FINISHED x", "2": "FINISHED x"}))
            out = io.StringIO()
            with redirect_stdout(out):
                al.after_run(slip, cfg, str(state),
                             fetch=lambda sport, date, ev=events: (ev, None), lookup=fs.lookup)
        rows = [l for l in self.ledger.read_text().splitlines()
                if l.startswith("|") and "€" in l]
        self.assertEqual(len(rows), 3)
        self.assertIn("+€52.00", rows[0])
        self.assertIn("+€42.00", rows[1])
        self.assertIn("| €31.00 |", rows[2])
        self.assertIn("+€63.00", rows[2])

    def test_unverifiable_leg_asks_for_manual_row(self):
        self.state.write_text(json.dumps({"1": "FINISHED 1-0"}))
        out = self.run_hook([(1, "Arsenal", "Chelsea", "20260101", "Total corners over 8.5")],
                            self.config(),
                            [event("Arsenal", "Chelsea", "1", "0")])
        self.assertIn("LEDGER:", out)
        self.assertIn("manual", out.lower())
        self.assertFalse(self.ledger.exists())
        self.assertFalse(self.marker.exists())

    def test_refetch_failure_retries_later(self):
        self.state.write_text(json.dumps({"1": "FINISHED 2-0"}))
        out = io.StringIO()
        with redirect_stdout(out):
            al.after_run([(1, "Arsenal", "Chelsea", "20260101", "Arsenal win")],
                         self.config(), str(self.state),
                         fetch=lambda sport, date: ([], "HTTP 500"), lookup=fs.lookup)
        self.assertIn("LEDGER:", out.getvalue())
        self.assertFalse(self.ledger.exists())
        self.assertFalse(self.marker.exists())

    def test_incomplete_config_never_writes(self):
        self.state.write_text(json.dumps({"1": "FINISHED 2-0"}))
        out = self.run_hook([(1, "Arsenal", "Chelsea", "20260101", "Arsenal win")],
                            self.config(stake=None),
                            [event("Arsenal", "Chelsea", "2", "0")])
        self.assertIn("LEDGER:", out)
        self.assertFalse(self.ledger.exists())

    def test_existing_note_without_table_gets_one(self):
        self.ledger.write_text("---\ntype: reference\ncreated: 2026-07-01\n"
                               "updated: 2026-07-01\n---\n\n# 📒 Betting Ledger\n\nProse only.\n")
        self.state.write_text(json.dumps({"1": "FINISHED 2-0"}))
        out = self.run_hook([(1, "Arsenal", "Chelsea", "20260101", "Match result: Arsenal win")],
                            self.config(),
                            [event("Arsenal", "Chelsea", "2", "0")])
        self.assertIn("LEDGER: recorded", out)
        text = self.ledger.read_text()
        self.assertIn(al.LEDGER_HEADER, text)
        self.assertIn("+€52.00", text)

    def test_multi_date_slip_gates_on_final_jobs_run_dates(self):
        # Per-date job split: this (final) job's state only ever holds its own
        # date's legs, so the trigger gates on run_dates while settlement
        # judges the whole slip from the re-fetch.
        self.state.write_text(json.dumps({"2": "FINISHED 2-1"}))
        slip = [(1, "Arsenal", "Chelsea", "20260101", "Match result: Arsenal win"),
                (2, "Spain", "Sweden", "20260103", "Over 2.5 goals")]
        events = [event("Arsenal", "Chelsea", "2", "0"), event("Spain", "Sweden", "2", "1")]
        out = io.StringIO()
        with redirect_stdout(out):
            al.after_run(slip, self.config(), str(self.state),
                         fetch=lambda sport, date: (events, None), lookup=fs.lookup,
                         run_dates=["20260103"])
        self.assertIn("LEDGER: recorded", out.getvalue())
        self.assertEqual(self.ledger.read_text().count("| Won |"), 1)

    def test_hook_errors_never_raise(self):
        out = io.StringIO()
        with redirect_stdout(out):
            al.after_run([(1, "Arsenal", "Chelsea", "20260101", "Arsenal win")],
                         self.config(), str(self.state),  # state file missing entirely
                         fetch=None, lookup=None)
        # missing state file means "not settled yet" -> silent, and never an exception
        self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
