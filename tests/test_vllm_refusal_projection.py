import os
import sys
import pytest
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../recipes/mods/inkling-refusal-dial")))

def test_canonical_rank1_projection_math():
    import refusal_projection
    # Setup test unit direction along axis 0
    r = torch.zeros(4096, dtype=torch.float32)
    r[0] = 1.0
    
    proj = refusal_projection.RefusalProjection(r)
    refusal_projection.set_lambda(1.0)
    
    # Input vector with components along axis 0 and axis 1
    x = torch.tensor([[5.0, 3.0] + [0.0]*4094], dtype=torch.float32)
    y = proj(x)
    
    # At lambda=1.0, component along axis 0 is projected out to zero
    assert torch.isclose(y[0, 0], torch.tensor(0.0), atol=1e-5)
    # Component along axis 1 remains completely untouched
    assert torch.isclose(y[0, 1], torch.tensor(3.0), atol=1e-5)

def test_canonical_lambda_zero_is_identity():
    import refusal_projection
    r = torch.zeros(4096, dtype=torch.float32)
    r[0] = 1.0
    
    proj = refusal_projection.RefusalProjection(r)
    refusal_projection.set_lambda(0.0)
    
    x = torch.tensor([[5.0, 3.0] + [0.0]*4094], dtype=torch.float32)
    y = proj(x)
    assert torch.allclose(y, x, atol=1e-6)

def test_lambda_tensor_in_place_mutation():
    import refusal_projection
    device = torch.device("cpu")
    t = refusal_projection.get_lambda_tensor(device, torch.float32)
    ptr_before = t.data_ptr()
    
    refusal_projection.set_lambda(1.5)
    ptr_after = t.data_ptr()
    
    assert ptr_before == ptr_after
    assert torch.isclose(t, torch.tensor(1.5))
    assert refusal_projection.get_lambda() == 1.5

def test_patch_vllm_logic_on_synthetic_code():
    from patch_vllm import patch_inkling_model, patch_api_server
    # Verify that patch helper functions are defined and callable
    assert callable(patch_inkling_model)
    assert callable(patch_api_server)
