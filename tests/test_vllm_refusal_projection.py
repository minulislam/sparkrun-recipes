import os
import sys
import pytest
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../recipes/mods/inkling-refusal-dial")))

def test_rank1_projection_mathematics():
    from refusal_projection import InklingRefusalProjection
    proj = InklingRefusalProjection(hidden_size=4096, num_layers=42)
    # Unit direction along axis 0
    r = torch.zeros(4096)
    r[0] = 1.0
    proj.directions[0] = r
    proj.set_lambda(1.0)
    
    # Input vector with components along axis 0 and axis 1
    x = torch.tensor([[5.0, 3.0] + [0.0]*4094])
    y = proj.project(x, layer_id=0)
    
    # Component along axis 0 must be zeroed at lambda=1.0
    assert torch.isclose(y[0, 0], torch.tensor(0.0), atol=1e-5)
    # Orthogonal component along axis 1 must remain untouched
    assert torch.isclose(y[0, 1], torch.tensor(3.0), atol=1e-5)

def test_lambda_in_place_device_tensor_preserves_data_ptr():
    from refusal_projection import InklingRefusalProjection
    proj = InklingRefusalProjection(hidden_size=4096, num_layers=42)
    ptr_before = proj.lambda_tensor.data_ptr()
    proj.set_lambda(0.5)
    ptr_after = proj.lambda_tensor.data_ptr()
    assert ptr_before == ptr_after
    assert torch.isclose(proj.lambda_tensor, torch.tensor([0.5]))

def test_lambda_zero_is_noop():
    from refusal_projection import InklingRefusalProjection
    proj = InklingRefusalProjection(hidden_size=4096, num_layers=42)
    r = torch.zeros(4096)
    r[0] = 1.0
    proj.directions[0] = r
    proj.set_lambda(0.0)
    
    x = torch.tensor([[5.0, 3.0] + [0.0]*4094])
    y = proj.project(x, layer_id=0)
    assert torch.allclose(y, x)
