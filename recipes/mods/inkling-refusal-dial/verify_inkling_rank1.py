#!/usr/bin/env python3
"""Pre-execution verification script for Inkling-Small rank-1 refusal directions.

Validates that:
1. The safetensors archive exists and is non-empty.
2. All 42 layers (layers.0.r .. layers.41.r) exist.
3. Every direction has shape [4096], finite numbers, and unit norm (1.0 +/- 1e-4).
Exits 0 on success, exits 1 on failure.
"""

import argparse
import sys
import torch
from safetensors.torch import load_file


def verify_directions(path: str, expected_layers: int = 42, hidden_size: int = 4096) -> bool:
    """Verify validity of a refusal directions safetensors archive.

    Returns:
        True if all checks pass, False otherwise.
    """
    try:
        tensors = load_file(path)
    except Exception as e:
        print(f"ERROR: Failed to load safetensors file {path}: {e}", file=sys.stderr)
        return False

    errors = []
    for l in range(expected_layers):
        key = f"layers.{l}.r"
        if key not in tensors:
            errors.append(f"Missing required direction key: {key}")
            continue

        t = tensors[key]
        if tuple(t.shape) != (hidden_size,):
            errors.append(f"{key}: invalid shape {tuple(t.shape)}, expected ({hidden_size},)")

        if not torch.all(torch.isfinite(t)):
            errors.append(f"{key}: contains NaN or Inf values")

        norm = float(torch.norm(t))
        if abs(norm - 1.0) > 1e-4:
            errors.append(f"{key}: norm is {norm:.6f}, expected 1.0 +/- 1e-4")

    if errors:
        for err in errors:
            print(f"VERIFICATION FAILURE: {err}", file=sys.stderr)
        return False

    print(f"SUCCESS: All {expected_layers} layers verified with hidden_size={hidden_size} and unit norm.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Verify Inkling rank-1 refusal directions")
    parser.add_argument("--dirs", type=str, default="/opt/refusal/refusal_dirs_inkling.safetensors",
                        help="Path to refusal_dirs_inkling.safetensors")
    parser.add_argument("--layers", type=int, default=42, help="Expected number of layers")
    parser.add_argument("--hidden-size", type=int, default=4096, help="Expected hidden dimension")
    args = parser.parse_args()

    ok = verify_directions(args.dirs, expected_layers=args.layers, hidden_size=args.hidden_size)
    if not ok:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
