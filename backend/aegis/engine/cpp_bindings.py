import ctypes
import math
import os
import re
import logging
from typing import Optional

logger = logging.getLogger("aegis.engine.cpp")

# Look for compiled libaegis.so in likely locations
SO_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "cpp", "libaegis.so"),
    os.path.join(os.path.dirname(__file__), "..", "..", "cpp", "libaegis.so"),
    "/usr/local/lib/libaegis.so",
    "libaegis.so"
]

_lib = None
HAS_CPP_ENGINE = False

for path in SO_PATHS:
    norm_path = os.path.abspath(path)
    if os.path.exists(norm_path):
        try:
            _lib = ctypes.CDLL(norm_path)
            HAS_CPP_ENGINE = True
            logger.info(f"Successfully loaded C++ AEGIS Engine from: {norm_path}")
            break
        except Exception as e:
            logger.warning(f"Found {norm_path} but failed to load: {e}")

if _lib is not None:
    try:
        _lib.aegis_calculate_shannon_entropy.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        _lib.aegis_calculate_shannon_entropy.restype = ctypes.c_double

        _lib.aegis_calculate_name_anomaly.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        _lib.aegis_calculate_name_anomaly.restype = ctypes.c_double

        _lib.aegis_calculate_ewma_deviation.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double
        ]
        _lib.aegis_calculate_ewma_deviation.restype = ctypes.c_double

        _lib.aegis_validate_verhoeff.argtypes = [ctypes.c_char_p]
        _lib.aegis_validate_verhoeff.restype = ctypes.c_int

        _lib.aegis_calculate_bigram_perplexity.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        _lib.aegis_calculate_bigram_perplexity.restype = ctypes.c_double
    except Exception as e:
        logger.error(f"Error binding C++ engine functions: {e}")
        _lib = None
        HAS_CPP_ENGINE = False


# Pure Python Fallbacks for 100% test & runtime portability

# Verhoeff tables
VERHOEFF_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)
VERHOEFF_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)


def calculate_shannon_entropy(text: Optional[str]) -> float:
    """Calculates Shannon entropy of token string"""
    if not text:
        return 0.0
    text_b = text.encode("utf-8")
    if _lib is not None:
        return float(_lib.aegis_calculate_shannon_entropy(text_b, len(text_b)))

    # Pure Python implementation
    chars = [c for c in text if not c.isspace()]
    if len(chars) <= 1:
        return 0.0
    freq = {}
    for c in chars:
        freq[c] = freq.get(c, 0) + 1
    total = len(chars)
    entropy = 0.0
    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p)
    return float(entropy)


def calculate_name_anomaly(name: Optional[str]) -> float:
    """Calculates name anomaly score (0.0 to 1.0)"""
    if not name:
        return 1.0
    name_b = name.encode("utf-8")
    if _lib is not None:
        return float(_lib.aegis_calculate_name_anomaly(name_b, len(name_b)))

    # Pure Python fallback
    cleaned = name.strip()
    if not cleaned:
        return 1.0

    risk = 0.0
    if any(c.isdigit() for c in cleaned):
        risk += 0.45

    max_consonants = 0
    current_consonants = 0
    vowels = 0
    alphas = 0
    max_repeat = 1
    current_repeat = 1
    prev = ""

    for c in cleaned:
        if c.isalpha():
            alphas += 1
            if c.lower() in "aeiou":
                vowels += 1
                current_consonants = 0
            else:
                current_consonants += 1
                if current_consonants > max_consonants:
                    max_consonants = current_consonants
        elif c not in " -'":
            current_consonants = 0

        if c == prev:
            current_repeat += 1
            if current_repeat > max_repeat:
                max_repeat = current_repeat
        else:
            current_repeat = 1
        prev = c

    if max_consonants >= 5:
        risk += 0.40
    elif max_consonants == 4:
        risk += 0.15

    if max_repeat >= 4:
        risk += 0.35
    elif max_repeat == 3:
        risk += 0.10

    if alphas >= 4:
        ratio = vowels / alphas
        if ratio < 0.10:
            risk += 0.30
        elif ratio > 0.85:
            risk += 0.25

    ent = calculate_shannon_entropy(cleaned)
    if len(cleaned) > 6 and ent > 4.2:
        risk += 0.20
    elif len(cleaned) > 4 and ent < 1.2:
        risk += 0.30

    return min(1.0, risk)


def calculate_ewma_deviation(current_val: float, ewma_mean: float, ewma_var: float, alpha: float = 0.2) -> float:
    """Calculates statistical EWMA risk index for transaction amount deviation"""
    if _lib is not None:
        return float(_lib.aegis_calculate_ewma_deviation(current_val, ewma_mean, ewma_var, alpha))

    if ewma_mean <= 0.0:
        return 0.0
    var = ewma_var if ewma_var >= 1.0 else (ewma_mean * 0.15) ** 2
    sd = math.sqrt(max(var, 1e-4))
    z = (current_val - ewma_mean) / sd
    if z <= 1.0:
        return 0.0
    return min(1.0, max(0.0, 1.0 / (1.0 + math.exp(-(z - 3.0)))))


def validate_verhoeff(num_str: Optional[str]) -> bool:
    """Validates Aadhaar 12-digit number using Verhoeff algorithm"""
    if not num_str or len(num_str) != 12 or not num_str.isdigit():
        return False
    if _lib is not None:
        return bool(_lib.aegis_validate_verhoeff(num_str.encode("utf-8")))

    c = 0
    reversed_digits = [int(x) for x in reversed(num_str)]
    for i, digit in enumerate(reversed_digits):
        c = VERHOEFF_D[c][VERHOEFF_P[i % 8][digit]]
    return c == 0
