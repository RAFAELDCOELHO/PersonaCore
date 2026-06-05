"""Device preflight (ENV-05) — fail loud BEFORE any long run.

``preflight_device`` is the environment assertion that gates a multi-hour pretrain. It
resolves a usable device in priority order CUDA-P100 -> MPS -> CPU (D-02):

1. **CUDA active.** When a CUDA device is live, run the full P100 logic: print the env
   summary, enforce the "P100" name check (when ``strict``), and run a tiny Pascal sm_60
   CUDA smoke op. The smoke op catches the silent failure mode where a cu128+ torch wheel
   dropped Pascal kernels (Pitfall 1) — it errors with "no kernel image available" rather
   than training slowly/crashing mid-run.
2. **MPS available (Apple Silicon).** A usable long-run device under D-01 — return an MPS
   summary and do NOT raise, even when ``strict``.
3. **CPU only.** When ``strict`` (the long-run gate) there is no usable accelerator, so
   raise. When not ``strict`` (laptop/CI), print the CPU summary and return without raising,
   so ``preflight_demo.py`` runs to completion off-GPU.

``strict`` preserves the old ``require_p100`` intent: ``strict=True`` refuses to start a long
run unless a usable accelerator (CUDA P100 or MPS) is live; ``strict=False`` is the laptop/CI
summary path that degrades to a CPU dict without raising.
"""

import torch


def preflight_device(strict: bool = True) -> dict:
    """Resolve and assert a usable device (CUDA-P100 -> MPS -> CPU); return an env summary.

    Args:
        strict: When True (default, the long-run gate), refuse to start unless a usable
            accelerator is live — enforce the "P100" name check on CUDA and raise on a
            CPU-only box. When False (laptop/CI), skip the P100 name check on CUDA and
            degrade to a CPU summary dict instead of raising.

    Returns:
        ``{"device": str, "cc": (major, minor) | None, "torch": str}``. ``cc`` is the CUDA
        compute capability on a CUDA box, else None (MPS / CPU).

    Raises:
        RuntimeError: on CUDA, if the device is not a P100 (when ``strict``) or the Pascal
            CUDA smoke op fails (cu128+ kernel-drop risk); on a CPU-only box when ``strict``
            (no usable accelerator for a long run).
    """
    # Priority 1: CUDA (Kaggle P100) — run the full P100 gate.
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        major, minor = torch.cuda.get_device_capability(0)
        print(f"[preflight] device={name} cc={major}.{minor} torch={torch.__version__}")

        if strict and "P100" not in name:
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

    # Priority 2: MPS (Apple Silicon) — a usable long-run device under D-01; never raise here.
    if torch.backends.mps.is_available():
        print(f"[preflight] device=mps cc=n/a torch={torch.__version__}")
        return {"device": "mps", "cc": None, "torch": torch.__version__}

    # Priority 3: CPU only.
    if strict:
        raise RuntimeError(
            "No usable accelerator for a long run — neither CUDA (P100) nor MPS is "
            "available. Set the Kaggle accelerator to GPU P100, or run on an Apple "
            "Silicon (MPS) machine."
        )
    # Laptop/CI summary path (strict=False): report CPU and return without raising.
    print(f"[preflight] device=cpu cc=n/a torch={torch.__version__} (no CUDA/MPS)")
    return {"device": "cpu", "cc": None, "torch": torch.__version__}
