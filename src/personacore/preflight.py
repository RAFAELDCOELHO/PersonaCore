"""GPU/P100 preflight (ENV-05) — fail loud BEFORE any long Kaggle run.

``preflight_p100`` is the environment assertion that gates a multi-hour pretrain. It checks
three things in order:

1. **CUDA is active.** If the Kaggle accelerator isn't set to GPU there is no point starting.
2. **The device is a Tesla P100** (when ``require_p100``). A T4/other card means the notebook
   was assigned the wrong accelerator; refuse rather than waste quota.
3. **Pascal sm_60 kernels actually run.** A tiny CUDA smoke op catches the silent failure
   mode where a cu128+ torch wheel dropped Pascal kernels (Pitfall 1) — the op errors with
   "no kernel image available" rather than training slowly/crashing mid-run.

``require_p100=False`` is the laptop/CI path: on a GPU box it still prints the env summary
and runs the smoke op but does not insist on the P100 name; on a CPU-only box it reports
``device=cpu`` and returns without raising, so ``preflight_demo.py`` runs to completion off
GPU.
"""

import torch


def preflight_p100(require_p100: bool = True) -> dict:
    """Assert a Pascal-compatible CUDA P100 is live; return an env summary dict.

    Args:
        require_p100: When True (default, the Kaggle long-run path), raise unless the device
            name contains "P100". When False (laptop/CI), skip the name check.

    Returns:
        ``{"device": str, "cc": (major, minor), "torch": str}``.

    Raises:
        RuntimeError: if CUDA is unavailable *and* ``require_p100`` is True, the device is
            not a P100 (when required), or the Pascal CUDA smoke op fails (cu128+
            kernel-drop risk).
    """
    if not torch.cuda.is_available():
        if require_p100:
            raise RuntimeError(
                "CUDA not available — set the Kaggle accelerator to GPU P100 before a long run."
            )
        # CPU/laptop path (require_p100=False): report CPU and return without raising,
        # so the thin preflight_demo script runs to completion off-GPU.
        print(f"[preflight] device=cpu cc=n/a torch={torch.__version__} (no CUDA)")
        return {"device": "cpu", "cc": None, "torch": torch.__version__}

    name = torch.cuda.get_device_name(0)
    major, minor = torch.cuda.get_device_capability(0)
    print(f"[preflight] device={name} cc={major}.{minor} torch={torch.__version__}")

    if require_p100 and "P100" not in name:
        raise RuntimeError(
            f"Expected a Tesla P100, got '{name}'. Refusing to start a long run — "
            "re-assign the Kaggle accelerator to GPU P100."
        )

    # Pascal sm_60 kernels present? A tiny CUDA op smoke-tests the installed wheel.
    try:
        _ = (torch.ones(8, device="cuda") * 2).sum().item()
    except RuntimeError as e:
        raise RuntimeError(
            "CUDA op failed — the installed torch may lack Pascal sm_60 kernels "
            "(a cu128+ wheel dropped them). On Kaggle, do NOT reinstall torch; "
            "use the pre-installed Pascal-compatible build."
        ) from e

    return {"device": name, "cc": (major, minor), "torch": torch.__version__}
