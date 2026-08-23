"""Self-assigned Vietnamese display name for a session.

Each FROM-less session picks its own human-friendly Vietnamese name so Ba can
address it easily on the bus.
"""
from __future__ import annotations

import secrets

_HO = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ",
    "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý",
]
_TEN_DEM = [
    "Minh", "Bảo", "Gia", "Anh", "Khánh", "Nhật", "Thanh", "Quang",
    "Hải", "Hà", "Tuấn", "Ngọc", "Thu", "Phương", "Hoài", "Đức",
]
_TEN = [
    "Khôi", "Ngọc", "Long", "Linh", "Nam", "Hân", "Phúc", "An", "Vy",
    "Trang", "Sơn", "Hùng", "Dũng", "Mai", "Lan", "Hương", "Quân", "Kiệt",
]


def generate_vietnamese_name() -> str:
    """Return a short Vietnamese display name, e.g. 'Minh Khôi'."""
    return f"{secrets.choice(_TEN_DEM)} {secrets.choice(_TEN)}"


def generate_full_name() -> str:
    """Return a full Vietnamese name, e.g. 'Nguyễn Minh Khôi'."""
    return f"{secrets.choice(_HO)} {secrets.choice(_TEN_DEM)} {secrets.choice(_TEN)}"
