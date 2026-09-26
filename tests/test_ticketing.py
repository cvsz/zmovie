"""Tests for ticketing: atomic seats, holds, idempotency, QR, concurrency."""
from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from zmovie_platform import migrations, storage
from zmovie_platform.ticketing import booking, store
from zmovie_platform.ticketing.qr import verify_qr
from zmovie_platform.ticketing.seed import seed_synthetic


class TicketingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"
        migrations.migrate()
        store.ensure_tables()
        seed_synthetic()

    def tearDown(self) -> None:
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_availability_and_hold_confirm(self) -> None:
        avail = booking.availability("st-neon-1")
        self.assertGreater(avail["total"], 0)
        seat = avail["available"][0]
        hold = booking.hold_seat(showtime_id="st-neon-1", seat_no=seat, holder_ref="u1", idempotency_key="h-001")
        self.assertEqual(hold["seat_no"], seat)
        # ซ้ำ idempotency_key ได้ record เดิม
        dup = booking.hold_seat(showtime_id="st-neon-1", seat_no=seat, holder_ref="u1", idempotency_key="h-001")
        self.assertEqual(dup["id"], hold["id"])
        confirmed = booking.confirm_hold(hold_id=hold["id"], holder_ref="u1", idempotency_key="r-001")
        self.assertEqual(confirmed["reservation"]["status"], "confirmed")
        self.assertIsNotNone(verify_qr(
            qr_payload=confirmed["ticket"]["qr_payload"], qr_signature=confirmed["ticket"]["qr_signature"]))

    def test_no_double_selling_concurrent(self) -> None:
        avail = booking.availability("st-neon-1")
        seat = avail["available"][0]
        # hold เดียวแล้วให้ 8 threads แย่ง confirm (ใช้ idempotency ต่างกัน แต่ seat เดียวกัน)
        hold = booking.hold_seat(showtime_id="st-neon-1", seat_no=seat, holder_ref="owner", idempotency_key="hc-main")
        results: list[str] = []
        lock = threading.Lock()

        def attempt(n: int) -> None:
            try:
                booking.confirm_hold(hold_id=hold["id"], holder_ref="owner", idempotency_key=f"rc-{n}")
                with lock:
                    results.append("ok")
            except ValueError as exc:
                with lock:
                    results.append(str(exc))

        threads = [threading.Thread(target=attempt, args=(n,)) for n in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        # hold เดียว confirm ได้ครั้งเดียว ที่เหลือต้อง fail (consumed/duplicate path)
        self.assertEqual(results.count("ok"), 1)

    def test_concurrent_distinct_holds_one_seat(self) -> None:
        avail = booking.availability("st-monsoon-1")
        seat = avail["available"][0]
        outcomes: list[str] = []
        lock = threading.Lock()

        def attempt(n: int) -> None:
            try:
                booking.hold_seat(showtime_id="st-monsoon-1", seat_no=seat, holder_ref=f"u{n}", idempotency_key=f"hx-{n}")
                with lock:
                    outcomes.append("ok")
            except ValueError:
                with lock:
                    outcomes.append("taken")

        threads = [threading.Thread(target=attempt, args=(n,)) for n in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(outcomes.count("ok"), 1)
        self.assertEqual(outcomes.count("taken"), 3)

    def test_hold_expiration_and_retry(self) -> None:
        avail = booking.availability("st-neon-1")
        seat = avail["available"][1]
        hold = booking.hold_seat(
            showtime_id="st-neon-1", seat_no=seat, holder_ref="u9", idempotency_key="he-1", ttl_minutes=-1)
        with self.assertRaises(ValueError):
            booking.confirm_hold(hold_id=hold["id"], holder_ref="u9", idempotency_key="re-1")
        swept = booking.release_expired_holds()
        self.assertGreaterEqual(swept, 1)
        retry = booking.hold_seat(showtime_id="st-neon-1", seat_no=seat, holder_ref="u9", idempotency_key="he-2")
        self.assertEqual(retry["seat_no"], seat)

    def test_cancel_refund_and_checkin(self) -> None:
        avail = booking.availability("st-neon-1")
        seat = avail["available"][2]
        hold = booking.hold_seat(showtime_id="st-neon-1", seat_no=seat, holder_ref="u10", idempotency_key="hk-1")
        confirmed = booking.confirm_hold(hold_id=hold["id"], holder_ref="u10", idempotency_key="rk-1")
        checked = booking.check_in(
            qr_payload=confirmed["ticket"]["qr_payload"], qr_signature=confirmed["ticket"]["qr_signature"], actor="staff")
        self.assertEqual(checked["status"], "checked_in")
        dup = booking.check_in(
            qr_payload=confirmed["ticket"]["qr_payload"], qr_signature=confirmed["ticket"]["qr_signature"], actor="staff")
        self.assertEqual(dup["status"], "duplicate_check_in")

        avail2 = booking.availability("st-neon-1")
        seat2 = avail2["available"][0]
        hold2 = booking.hold_seat(showtime_id="st-neon-1", seat_no=seat2, holder_ref="u11", idempotency_key="hk-2")
        confirmed2 = booking.confirm_hold(hold_id=hold2["id"], holder_ref="u11", idempotency_key="rk-2")
        canceled = booking.cancel_reservation(reservation_id=confirmed2["reservation"]["id"], holder_ref="u11")
        self.assertEqual(canceled["status"], "canceled")
        refunded = booking.mark_refunded(reservation_id=confirmed2["reservation"]["id"], actor="admin")
        self.assertEqual(refunded["status"], "refunded")

    def test_webhook_style_idempotent_confirm(self) -> None:
        avail = booking.availability("st-monsoon-1")
        seat = avail["available"][1]
        hold = booking.hold_seat(showtime_id="st-monsoon-1", seat_no=seat, holder_ref="u12", idempotency_key="hw-1")
        first = booking.confirm_hold(hold_id=hold["id"], holder_ref="u12", idempotency_key="rw-1")
        second = booking.confirm_hold(hold_id=hold["id"], holder_ref="u12", idempotency_key="rw-1")
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["reservation"]["id"], second["reservation"]["id"])


if __name__ == "__main__":
    unittest.main()
