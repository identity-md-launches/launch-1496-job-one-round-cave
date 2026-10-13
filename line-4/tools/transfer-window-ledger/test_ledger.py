import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import io

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ledger", HERE / "ledger.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.capture = tool.read_capture(HERE.parent / "transfer-crosscheck" / "publicnode.json")

    def rebuild(self):
        events, duplicates = tool.window.validate_logs(
            self.capture["raw_logs"], self.capture["decimals"],
            self.capture["token_address"], self.capture["from_block"], self.capture["to_block"])
        self.capture.update(transfers=events, transfer_count=len(events), duplicate_count=duplicates)

    def test_real_zto_matches_native_address_summary(self):
        result = tool.report(self.capture)
        self.assertEqual(result["transfer_count"], 3)
        self.assertEqual(result["token"], "ZTO")
        for row in result["addresses"]:
            native = tool.window.address_summary(self.capture["transfers"], row["address"], 18)
            for key in ("received_raw", "sent_raw", "net_raw", "received", "sent", "net"):
                self.assertEqual(row[key], native[key])
        self.assertEqual(sum(int(r["received_raw"]) for r in result["addresses"]),
                         int(result["event_total_raw"]))
        self.assertEqual(sum(int(r["sent_raw"]) for r in result["addresses"]),
                         int(result["event_total_raw"]))
        self.assertEqual(result["sum_net_raw"], "0")

    def test_delivery_order_and_duplicates_do_not_change_report(self):
        expected = tool.report(self.capture)
        self.capture["raw_logs"].reverse()
        self.capture["raw_logs"].append(copy.deepcopy(self.capture["raw_logs"][0]))
        self.rebuild()
        self.assertEqual(tool.report(self.capture), expected)

    def test_self_transfer(self):
        self.capture["raw_logs"] = self.capture["raw_logs"][:1]
        log = self.capture["raw_logs"][0]
        log["topics"][2] = log["topics"][1]
        self.rebuild()
        row, = tool.report(self.capture)["addresses"]
        self.assertEqual(row["touching_count"], 1)
        self.assertEqual(row["received_count"], 1)
        self.assertEqual(row["sent_count"], 1)
        self.assertEqual(row["self_transfer_count"], 1)
        self.assertEqual(row["self_transfer_raw"], row["received_raw"])
        self.assertEqual(row["net_raw"], "0")

    def test_zero_endpoint_is_retained(self):
        self.capture["raw_logs"] = self.capture["raw_logs"][:1]
        self.capture["raw_logs"][0]["topics"][1] = "0x" + "0" * 64
        self.rebuild()
        row = tool.report(self.capture)["addresses"][0]
        self.assertTrue(row["is_zero_address"])
        self.assertEqual(row["address"], tool.ZERO)
        self.assertEqual(int(row["net_raw"]), -int(row["sent_raw"]))
        self.assertEqual(tool.report(self.capture)["sum_net_raw"], "0")

    def test_large_integer_aggregation_and_negative_units(self):
        self.capture["raw_logs"] = self.capture["raw_logs"][:2]
        first, second = self.capture["raw_logs"]
        second["topics"] = copy.deepcopy(first["topics"])
        for log in self.capture["raw_logs"]:
            log["data"] = "0x" + format(2**256 - 1, "064x")
        self.rebuild()
        result = tool.report(self.capture)
        self.assertEqual(result["event_total_raw"], str(2 * (2**256 - 1)))
        sender = next(r for r in result["addresses"] if r["sent_count"])
        self.assertEqual(sender["net_raw"], str(-2 * (2**256 - 1)))
        self.assertEqual(sender["net"], "-" + sender["sent"])

    def test_empty_window(self):
        self.capture["raw_logs"] = []
        self.rebuild()
        result = tool.report(self.capture)
        self.assertEqual(result["addresses"], [])
        self.assertEqual(result["event_total_raw"], "0")
        self.assertEqual(result["sum_net_raw"], "0")

    def test_zero_value_event_counts(self):
        self.capture["raw_logs"] = self.capture["raw_logs"][:1]
        self.capture["raw_logs"][0]["data"] = "0x" + "0" * 64
        self.rebuild()
        result = tool.report(self.capture)
        self.assertEqual(result["transfer_count"], 1)
        self.assertEqual(result["event_total_raw"], "0")
        self.assertEqual(sum(r["touching_count"] for r in result["addresses"]), 2)

    def test_tampered_event_type_is_rejected(self):
        self.capture["transfers"][0]["block"] = float(self.capture["transfers"][0]["block"])
        with self.assertRaises(tool.window.RpcError):
            tool.report(self.capture)

    def test_removed_log_is_rejected(self):
        self.capture["raw_logs"][0]["removed"] = True
        with self.assertRaises(tool.window.RpcError):
            tool.report(self.capture)

    def test_outside_path_is_rejected_before_open(self):
        with patch.object(Path, "open", side_effect=AssertionError("must not open")):
            with self.assertRaisesRegex(ValueError, "inside this workspace"):
                tool.read_capture("/outside/never-read.json")

    def test_bounded_read_and_duplicate_keys(self):
        path = HERE / "synthetic.json"
        for data, pattern in ((b"x" * 9, "16 MiB"), (b'{"x":1,"x":2}', "duplicate key")):
            with patch.object(Path, "open", return_value=io.BytesIO(data)):
                with patch.object(tool, "MAX_BYTES", 8 if data.startswith(b"x") else 100):
                    with self.assertRaisesRegex(ValueError, pattern):
                        tool.read_capture(path)

    def test_cli_demo(self):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            tool.main(["--demo"])
        self.assertEqual(json.loads(output.getvalue())["transfer_count"], 3)


if __name__ == "__main__":
    unittest.main()
