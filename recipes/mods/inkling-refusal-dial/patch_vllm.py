#!/usr/bin/env python3
"""Surgical patcher for vLLM Inkling model and entrypoints.

Executed by run.sh inside the container prior to serving.
Injects rank-1 refusal projection into InklingDecoderLayer and registers
the /admin/refusal_lambda API router.
"""

import sys
import os

def patch_inkling_model():
    model_path = "/usr/local/lib/python3.12/dist-packages/vllm/models/inkling/nvidia/model.py"
    if not os.path.isfile(model_path):
        print(f"[WARN] {model_path} not found. Skipping model patch.")
        return False

    with open(model_path, "r") as f:
        content = f.read()

    if "self.refusal_proj" in content:
        print("[INFO] Inkling model already patched with refusal_proj.")
        return True

    # 1. Patch __init__ of InklingDecoderLayer
    target_init = "self.attn_norm = InklingRMSNorm(config.hidden_size, eps=config.rms_norm_eps)"
    injection_init = """self.refusal_proj = None
        from vllm.refusal_projection import is_enabled as refusal_is_enabled, resolve as refusal_resolve, RefusalProjection
        if refusal_is_enabled():
            r_hat, role = refusal_resolve(prefix, config.num_hidden_layers)
            if r_hat is not None:
                self.refusal_proj = RefusalProjection(r_hat, role)
        self.attn_norm = InklingRMSNorm(config.hidden_size, eps=config.rms_norm_eps)"""

    if target_init not in content:
        print("[ERROR] Could not find target __init__ anchor in Inkling model.", file=sys.stderr)
        return False

    content = content.replace(target_init, injection_init, 1)

    # 2. Patch forward of InklingDecoderLayer
    target_fwd = "attn_output = self.attn(positions, attn_in, log_scaling)"
    injection_fwd = """attn_output = self.attn(positions, attn_in, log_scaling)
        if getattr(self, "refusal_proj", None) is not None:
            attn_output = self.refusal_proj(attn_output)"""

    if target_fwd not in content:
        print("[ERROR] Could not find target forward anchor in Inkling model.", file=sys.stderr)
        return False

    content = content.replace(target_fwd, injection_fwd, 1)

    with open(model_path, "w") as f:
        f.write(content)

    print("[SUCCESS] Patched InklingDecoderLayer with RefusalProjection hook.")
    return True


def patch_api_server():
    serve_init = "/usr/local/lib/python3.12/dist-packages/vllm/entrypoints/serve/__init__.py"
    if not os.path.isfile(serve_init):
        print(f"[WARN] {serve_init} not found. Skipping API server patch.")
        return False

    with open(serve_init, "r") as f:
        content = f.read()

    if "attach_refusal_router" in content:
        print("[INFO] API server already patched with refusal router.")
        return True

    target = "attach_tokenize_router(app)"
    injection = """attach_tokenize_router(app)
    try:
        from vllm.entrypoints.serve.refusal.api_router import attach_router as attach_refusal_router
        attach_refusal_router(app)
    except Exception as e:
        import logging
        logging.getLogger("vllm").warning("Failed to attach refusal router: %s", e)"""

    if target not in content:
        print("[ERROR] Could not find attach_tokenize_router anchor in serve/__init__.py", file=sys.stderr)
        return False

    content = content.replace(target, injection, 1)

    with open(serve_init, "w") as f:
        f.write(content)

    print("[SUCCESS] Patched serve/__init__.py with refusal API router.")
    return True


if __name__ == "__main__":
    ok1 = patch_inkling_model()
    ok2 = patch_api_server()
    if ok1 and ok2:
        sys.exit(0)
    sys.exit(1)
