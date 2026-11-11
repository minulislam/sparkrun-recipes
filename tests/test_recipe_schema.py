import os
import yaml
import pytest

def test_inkling_refusal_dial_recipe_structure():
    recipe_path = "recipes/inkling-small-nvfp4-refusal-dial-tp2.yaml"
    assert os.path.exists(recipe_path), f"Recipe file {recipe_path} does not exist"
    with open(recipe_path) as f:
        recipe = yaml.safe_load(f)
    assert recipe["recipe_version"] == "2"
    assert recipe["model"] == "thinkingmachines/Inkling-Small-NVFP4"
    assert recipe["runtime"] == "vllm"
    assert recipe["min_nodes"] == 2
    assert recipe["max_nodes"] == 2
    assert recipe["defaults"]["tensor_parallel"] == 2
    assert "VLLM_REFUSAL_DIRS" in recipe["env"]
    assert "VLLM_REFUSAL_LAMBDA_INIT" in recipe["env"]
    assert any("verify_inkling_rank1.py" in cmd for cmd in recipe["pre_exec"])
    assert any("admin/refusal_lambda" in cmd for cmd in recipe["post_exec"])
