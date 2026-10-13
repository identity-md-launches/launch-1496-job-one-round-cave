import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("byte_map", HERE / "byte_map.py")
byte_map = importlib.util.module_from_spec(spec)
spec.loader.exec_module(byte_map)


class ByteMapTests(unittest.TestCase):
    def test_demo_covers_original_bytes(self):
        source = byte_map.decoder.demo_transaction()
        report = byte_map.inspect(source)
        raw = bytes.fromhex(source[2:])
        locations = report["locations"]
        self.assertEqual(report["byteLength"], len(raw))
        self.assertEqual([part["path"] for part in locations[:11]],
                         ["typeByte", "envelope", *byte_map.NAMES])
        self.assertEqual(locations[0]["endByteExclusive"], 1)
        self.assertEqual(locations[1]["endByteExclusive"], len(raw))
        cursor = locations[1]["payloadStartByte"]
        for part in locations[2:11]:
            self.assertEqual(part["startByte"], cursor)
            self.assertEqual(part["payloadStartByte"] - part["startByte"],
                             part["prefixByteLength"])
            self.assertEqual(part["endByteExclusive"] - part["payloadStartByte"],
                             part["payloadByteLength"])
            cursor = part["endByteExclusive"]
        self.assertEqual(cursor, len(raw))
        self.assertEqual(raw[locations[7]["payloadStartByte"]:
                             locations[7]["endByteExclusive"]].hex(),
                         byte_map.decoder.ZTO[2:])

    def test_nested_access_list_and_long_prefix(self):
        address = bytes.fromhex(byte_map.decoder.ZTO[2:])
        slot = bytes(range(32))
        payload = [1, 0, 1, 2, 100000, address, 0, b"x" * 80,
                   [[address, [slot, slot]], [address, []]]]
        source = "0x02" + byte_map.decoder.rlp_encode(payload).hex()
        report = byte_map.inspect(source)
        found = {item["path"]: item for item in report["locations"]}
        self.assertGreater(found["data"]["prefixByteLength"], 1)
        self.assertEqual(found["accessList"]["kind"], "list")
        self.assertEqual(found["accessList[0].storageKeys[1]"]["payloadByteLength"], 32)
        self.assertEqual(found["accessList[0].storageKeys[0]"]["payloadByteLength"], 32)
        self.assertEqual(len([key for key in found if key.startswith("accessList[")]), 8)
        raw = bytes.fromhex(source[2:])
        for item in report["locations"]:
            self.assertLessEqual(item["endByteExclusive"], len(raw))
            self.assertLessEqual(item["payloadStartByte"], item["endByteExclusive"])

    def test_rejects_signed_noncanonical_and_extra_bytes(self):
        raw = byte_map.decoder.demo_transaction()
        for bad in (raw + "00", "0x03" + raw[4:],
                    "0x02c28000", "0x02c0", raw[:-2],
                    "0x02f800", "0x02c100"):
            with self.subTest(bad=bad[:20]):
                with self.assertRaises(ValueError):
                    byte_map.inspect(bad)

    def test_cli_success_and_failure(self):
        command = [sys.executable, "-B", str(HERE / "byte_map.py")]
        ok = subprocess.run(command + ["--demo"], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn('"path": "accessList"', ok.stdout)
        bad = subprocess.run(command + ["0x02c0"], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(bad.stdout, "")


if __name__ == "__main__":
    unittest.main()
