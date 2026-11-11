import os
import sys
import pytest
import torch
from safetensors.torch import save_file

# Add repo root and mods to path for clean importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../recipes/mods/inkling-refusal-dial")))

def test_direction_computation_and_unit_norm():
    from benchmarks.redteam.extract_contrastive_directions import compute_layer_direction
    # Synthetic activations: harmful and benign clusters with known offset
    harmful = torch.randn(10, 4096) + 2.0
    benign = torch.randn(10, 4096) - 1.0
    direction = compute_layer_direction(harmful, benign)
    assert direction.shape == (4096,)
    assert torch.isclose(torch.norm(direction), torch.tensor(1.0), atol=1e-4)

def test_verify_inkling_rank1_passes_valid(tmp_path):
    import verify_inkling_rank1
    safetensors_path = tmp_path / "valid_dirs.safetensors"
    data = {f"layers.{l}.r": torch.randn(4096) for l in range(42)}
    for k in data:
        data[k] = data[k] / torch.norm(data[k])
    save_file(data, str(safetensors_path))
    assert verify_inkling_rank1.verify_directions(str(safetensors_path), expected_layers=42, hidden_size=4096) is True

def test_verify_inkling_rank1_fails_missing_layer(tmp_path):
    import verify_inkling_rank1
    safetensors_path = tmp_path / "incomplete_dirs.safetensors"
    data = {f"layers.{l}.r": torch.randn(4096) for l in range(41)} # only 41 layers
    for k in data:
        data[k] = data[k] / torch.norm(data[k])
    save_file(data, str(safetensors_path))
    assert verify_inkling_rank1.verify_directions(str(safetensors_path), expected_layers=42, hidden_size=4096) is False
