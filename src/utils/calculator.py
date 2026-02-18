"""
Training-time calculator for EVE Online skills.

Formulas from EVE University wiki:
  SP/min = primary_attr + secondary_attr / 2
  time   = required_SP / (SP/min) * 60   → seconds

Skill point thresholds per level (rank-1 base):
  L1:   250 SP
  L2:  1415 SP
  L3:  8000 SP
  L4: 45255 SP
  L5: 256000 SP

For rank N: multiply by N.
"""
from __future__ import annotations

from src.data import skills_db

# ── SP thresholds for rank-1 skills ──────────────────────────────────────────
_SP_PER_LEVEL: dict[int, int] = {
    1:    250,
    2:   1_415,
    3:   8_000,
    4:  45_255,
    5: 256_000,
}

# ── Attribute primary/secondary mapping per skill group ──────────────────────
# Source: EVE University — Attributes page
# Format: group_name → (primary_attr_key, secondary_attr_key)
_GROUP_ATTRS: dict[str, tuple[str, str]] = {
    # Combat
    "Gunnery":                  ("perception", "willpower"),
    "Missiles":                 ("perception", "willpower"),
    "Drones":                   ("memory",     "perception"),
    "Spaceship Command":        ("perception", "willpower"),
    "Armor":                    ("memory",     "perception"),
    "Shields":                  ("memory",     "perception"),
    "Targeting":                ("memory",     "perception"),
    "Electronic Systems":       ("memory",     "perception"),
    "Scanning":                 ("memory",     "perception"),
    "Subsystems":               ("perception", "willpower"),
    "Fleet Support":            ("charisma",   "willpower"),
    "Navigation":               ("intelligence","perception"),
    "Engineering":              ("intelligence","memory"),
    "Rigging":                  ("intelligence","memory"),
    # Industry
    "Industry":                 ("memory",     "intelligence"),
    "Resource Processing":      ("memory",     "intelligence"),
    "Planet Management":        ("memory",     "intelligence"),
    "Reactions":                ("memory",     "intelligence"),
    "Science":                  ("intelligence","memory"),
    "Research":                 ("intelligence","memory"),
    "Manufacturing":            ("memory",     "intelligence"),
    # Social / Support
    "Social":                   ("charisma",   "intelligence"),
    "Trade":                    ("charisma",   "intelligence"),
    "Corporation Management":   ("charisma",   "memory"),
    "Leadership":               ("charisma",   "willpower"),
    # Neural Enhancement
    "Neural Enhancement":       ("intelligence","memory"),
}

_DEFAULT_ATTRS: tuple[str, str] = ("intelligence", "memory")

# ── Skill rank lookup (hardcoded for common skills; fallback = 1) ─────────────
# Full rank data is in the EVE SDE; we store a representative subset.
_SKILL_RANK: dict[str, int] = {
    # Gunnery
    "Gunnery": 1, "Small Hybrid Turret": 1, "Medium Hybrid Turret": 3,
    "Large Hybrid Turret": 5, "Small Projectile Turret": 1,
    "Medium Projectile Turret": 3, "Large Projectile Turret": 5,
    "Small Energy Turret": 1, "Medium Energy Turret": 3, "Large Energy Turret": 5,
    "Rapid Firing": 2, "Sharpshooter": 2, "Motion Prediction": 2,
    "Surgical Strike": 3, "Trajectory Analysis": 5, "Controlled Bursts": 2,
    # Missiles
    "Missile Launcher Operation": 1, "Light Missiles": 1, "Heavy Missiles": 2,
    "Cruise Missiles": 5, "Torpedoes": 5, "Rockets": 1,
    "Missile Bombardment": 2, "Missile Projection": 2,
    "Rapid Launch": 2, "Target Navigation Prediction": 5,
    "Warhead Upgrades": 2, "Guided Missile Precision": 5,
    # Drones
    "Drones": 1, "Scout Drone Operation": 1, "Combat Drone Operation": 2,
    "Drone Interfacing": 5, "Drone Navigation": 2, "Drone Sharpshooting": 2,
    "Heavy Drone Operation": 5, "Sentry Drone Interfacing": 5,
    # Spaceship Command
    "Spaceship Command": 1, "Caldari Frigate": 2, "Caldari Destroyer": 3,
    "Caldari Cruiser": 4, "Caldari Battlecruiser": 6, "Caldari Battleship": 8,
    "Minmatar Frigate": 2, "Minmatar Destroyer": 3, "Minmatar Cruiser": 4,
    "Gallente Frigate": 2, "Gallente Cruiser": 4, "Amarr Frigate": 2,
    "Amarr Cruiser": 4, "Interceptors": 6, "Assault Frigates": 6,
    "Heavy Assault Cruisers": 8, "Logistics Cruisers": 8,
    # Navigation
    "Navigation": 1, "Afterburner": 1, "High Speed Maneuvering": 5,
    "Warp Drive Operation": 1, "Fuel Conservation": 2, "Acceleration Control": 4,
    "Evasive Maneuvering": 2, "Micro Jump Drive Operation": 3,
    # Engineering
    "Engineering": 1, "CPU Management": 1, "Power Grid Management": 1,
    "Electronics Upgrades": 2, "Energy Grid Upgrades": 2,
    "Shield Upgrades": 2, "Weapon Upgrades": 2, "Advanced Weapon Upgrades": 6,
    # Science
    "Science": 1, "Cybernetics": 3, "Thermodynamics": 5,
    "Jury Rigging": 2, "Astrometrics": 3,
    # Industry
    "Industry": 1, "Mining": 1, "Reprocessing": 2,
    "Mass Production": 4, "Laboratory Operation": 4,
    # Social
    "Social": 1, "Negotiation": 2, "Connections": 3,
    "Diplomacy": 2, "Fast Talk": 3,
}


def get_skill_rank(skill_name: str) -> int:
    """Return the training rank multiplier for a skill (default 1)."""
    return _SKILL_RANK.get(skill_name, 1)


def sp_required(skill_name: str, from_level: int, to_level: int) -> int:
    """
    Return the SP needed to train a skill from *from_level* to *to_level*.
    Both levels are inclusive endpoints; from_level is already trained.
    """
    rank = get_skill_rank(skill_name)
    sp_at = {lvl: pts * rank for lvl, pts in _SP_PER_LEVEL.items()}
    sp_at[0] = 0

    from_sp = sp_at.get(from_level, 0)
    to_sp   = sp_at.get(to_level, 0)
    return max(0, to_sp - from_sp)


def sp_per_minute(attributes: dict, skill_name: str) -> float:
    """
    Calculate SP/min given character attributes and skill name.
    Falls back to intelligence+memory if group is unknown.
    """
    group = skills_db.get_skill_group(
        skills_db.get_skill_id_by_name(skill_name)
    ) if hasattr(skills_db, "get_skill_id_by_name") else None

    primary_key, secondary_key = _GROUP_ATTRS.get(group or "", _DEFAULT_ATTRS)

    primary   = attributes.get(primary_key,   20)
    secondary = attributes.get(secondary_key, 20)
    return primary + secondary / 2.0


def training_time(skill_name: str, from_level: int, to_level: int,
                  attributes: dict) -> float:
    """Return training time in **seconds** for one level transition."""
    sp   = sp_required(skill_name, from_level, to_level)
    spm  = sp_per_minute(attributes, skill_name)
    if spm <= 0:
        return 0.0
    return (sp / spm) * 60.0


def format_duration(seconds: float) -> str:
    """Convert seconds to human-readable string: '3d 14h 22m 05s'."""
    if seconds <= 0:
        return "0s"
    s = int(seconds)
    d, s = divmod(s, 86_400)
    h, s = divmod(s,  3_600)
    m, s = divmod(s,     60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s:02d}s")
    return " ".join(parts)


def plan_total_time(plan: list[dict], attributes: dict) -> float:
    """
    Sum training time for an ordered list of plan entries.
    Each entry: {"name": str, "level": int}
    Assumes each skill starts from level 0 (worst case).
    """
    total = 0.0
    for entry in plan:
        name  = entry.get("name", "")
        level = entry.get("level", 1)
        total += training_time(name, level - 1, level, attributes)
    return total
