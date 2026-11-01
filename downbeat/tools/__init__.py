"""Downbeat seat tools (sanctioned shared infrastructure, charter amendment 2026-10-22).

Use:  sys.path.insert(0, '/home/hatch/workspace/downbeat-seat'); from tools import render_part, qa, deliver, mark, noise_bus
Catalog: tools/instruments.json (regenerate with `python3 -m tools.build_instruments`).
"""
from .render import render_part, check_range, RangeError  # noqa: F401
from .qa import qa  # noqa: F401
from .deliver import deliver  # noqa: F401
from .checkpoint import mark  # noqa: F401
from .synth import noise_bus  # noqa: F401
