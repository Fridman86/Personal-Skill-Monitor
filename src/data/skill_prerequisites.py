# src/data/skill_prerequisites.py
"""
EVE Online skill prerequisite chains.
Maps skill_name -> list of (prerequisite_skill_name, required_level).
Used to auto-add prerequisites when planning a skill.
"""

PREREQUISITES = {
    # ── Gunnery ──────────────────────────────────────────
    "Small Hybrid Turret": [("Gunnery", 1)],
    "Small Projectile Turret": [("Gunnery", 1)],
    "Small Energy Turret": [("Gunnery", 1)],
    "Medium Hybrid Turret": [("Gunnery", 3), ("Small Hybrid Turret", 3)],
    "Medium Projectile Turret": [("Gunnery", 3), ("Small Projectile Turret", 3)],
    "Medium Energy Turret": [("Gunnery", 3), ("Small Energy Turret", 3)],
    "Large Hybrid Turret": [("Gunnery", 5), ("Medium Hybrid Turret", 3)],
    "Large Projectile Turret": [("Gunnery", 5), ("Medium Projectile Turret", 3)],
    "Large Energy Turret": [("Gunnery", 5), ("Medium Energy Turret", 3)],
    "Capital Hybrid Turret": [("Large Hybrid Turret", 5), ("Capital Ships", 1)],
    "Capital Projectile Turret": [("Large Projectile Turret", 5), ("Capital Ships", 1)],
    "Capital Energy Turret": [("Large Energy Turret", 5), ("Capital Ships", 1)],
    "Rapid Firing": [("Gunnery", 2)],
    "Sharpshooter": [("Gunnery", 2)],
    "Motion Prediction": [("Gunnery", 2)],
    "Controlled Bursts": [("Gunnery", 2)],
    "Trajectory Analysis": [("Gunnery", 4)],
    "Surgical Strike": [("Gunnery", 4)],
    "Weapon Upgrades": [("Gunnery", 2)],
    "Advanced Weapon Upgrades": [("Weapon Upgrades", 5)],

    # ── Missiles ─────────────────────────────────────────
    "Rockets": [("Missile Launcher Operation", 1)],
    "Light Missiles": [("Missile Launcher Operation", 2)],
    "Heavy Missiles": [("Missile Launcher Operation", 3), ("Light Missiles", 3)],
    "Heavy Assault Missiles": [("Missile Launcher Operation", 4), ("Heavy Missiles", 3)],
    "Cruise Missiles": [("Missile Launcher Operation", 4), ("Heavy Missiles", 3)],
    "Torpedoes": [("Missile Launcher Operation", 5), ("Heavy Missiles", 4)],
    "Citadel Torpedoes": [("Torpedoes", 5), ("Capital Ships", 1)],
    "XL Torpedoes": [("Torpedoes", 5), ("Capital Ships", 1)],
    "XL Cruise Missiles": [("Cruise Missiles", 5), ("Capital Ships", 1)],
    "Rapid Launch": [("Missile Launcher Operation", 2)],
    "Warhead Upgrades": [("Missile Launcher Operation", 3)],
    "Missile Bombardment": [("Missile Launcher Operation", 3)],
    "Missile Projection": [("Missile Launcher Operation", 3)],
    "Target Navigation Prediction": [("Missile Launcher Operation", 4)],
    "Guided Missile Precision": [("Missile Launcher Operation", 4)],
    "Auto-Targeting Missiles": [("Missile Launcher Operation", 2)],
    "Defender Missiles": [("Missile Launcher Operation", 3)],

    # ── Drones ───────────────────────────────────────────
    "Drone Avionics": [("Drones", 3)],
    "Drone Interfacing": [("Drones", 5)],
    "Drone Navigation": [("Drones", 3)],
    "Drone Durability": [("Drones", 3)],
    "Drone Sharpshooting": [("Drones", 3)],
    "Light Drone Operation": [("Drones", 1)],
    "Medium Drone Operation": [("Drones", 3)],
    "Heavy Drone Operation": [("Drones", 5)],
    "Sentry Drone Interfacing": [("Drones", 4), ("Drone Sharpshooting", 4)],
    "Mining Drone Operation": [("Drones", 1)],
    "Salvage Drone Operation": [("Drones", 3)],
    "Repair Drone Operation": [("Drones", 3)],
    "Electronic Warfare Drone Interfacing": [("Drones", 3), ("Electronic Warfare", 3)],
    "Advanced Drone Avionics": [("Drone Avionics", 5)],
    "Fighters": [("Drones", 5), ("Leadership", 5)],
    "Fighter Bombers": [("Fighters", 5)],
    "Amarr Drone Specialization": [("Drones", 5)],
    "Caldari Drone Specialization": [("Drones", 5)],
    "Gallente Drone Specialization": [("Drones", 5)],
    "Minmatar Drone Specialization": [("Drones", 5)],

    # ── Armor ────────────────────────────────────────────
    "Repair Systems": [("Mechanics", 3)],
    "Hull Upgrades": [("Mechanics", 1)],
    "Remote Armor Repair Systems": [("Mechanics", 3), ("Repair Systems", 2)],
    "Capital Repair Systems": [("Mechanics", 5), ("Repair Systems", 5)],
    "EM Armor Compensation": [("Hull Upgrades", 4)],
    "Explosive Armor Compensation": [("Hull Upgrades", 4)],
    "Kinetic Armor Compensation": [("Hull Upgrades", 4)],
    "Thermal Armor Compensation": [("Hull Upgrades", 4)],
    "Armor Layering": [("Mechanics", 3)],
    "Resistance Phasing": [("Hull Upgrades", 5)],
    "Capital Remote Armor Repair Systems": [("Remote Armor Repair Systems", 5), ("Capital Ships", 1)],

    # ── Shields ──────────────────────────────────────────
    "Shield Management": [("Shield Operation", 3)],
    "Shield Upgrades": [("Shield Operation", 3)],
    "Tactical Shield Manipulation": [("Shield Operation", 4)],
    "Shield Compensation": [("Shield Operation", 3)],
    "EM Shield Compensation": [("Shield Operation", 4)],
    "Explosive Shield Compensation": [("Shield Operation", 4)],
    "Kinetic Shield Compensation": [("Shield Operation", 4)],
    "Thermal Shield Compensation": [("Shield Operation", 4)],
    "Shield Emission Systems": [("Shield Operation", 3)],
    "Capital Shield Operation": [("Shield Operation", 5), ("Shield Management", 5)],
    "Capital Shield Emission Systems": [("Shield Emission Systems", 5), ("Capital Ships", 1)],

    # ── Engineering ──────────────────────────────────────
    "Capacitor Management": [("Power Grid Management", 3)],
    "Capacitor Systems Operation": [("Power Grid Management", 1)],
    "Energy Grid Upgrades": [("Power Grid Management", 2), ("CPU Management", 2)],
    "Thermodynamics": [("Power Grid Management", 5), ("CPU Management", 5)],
    "Nanite Operation": [("Mechanics", 3)],
    "Nanite Interfacing": [("Nanite Operation", 3)],
    "Electronics Upgrades": [("CPU Management", 2)],

    # ── Navigation ───────────────────────────────────────
    "Afterburner": [("Navigation", 1)],
    "Fuel Conservation": [("Navigation", 2), ("Afterburner", 1)],
    "Acceleration Control": [("Navigation", 3), ("Afterburner", 3)],
    "High Speed Maneuvering": [("Navigation", 3), ("Afterburner", 3)],
    "Evasive Maneuvering": [("Navigation", 2)],
    "Warp Drive Operation": [("Navigation", 1)],
    "Jump Drive Operation": [("Navigation", 5), ("Warp Drive Operation", 5)],
    "Jump Drive Calibration": [("Jump Drive Operation", 3)],
    "Jump Fuel Conservation": [("Jump Drive Operation", 3)],
    "Micro Jump Drive Operation": [("Navigation", 3), ("High Speed Maneuvering", 2)],

    # ── Spaceship Command ────────────────────────────────
    "Amarr Frigate": [("Spaceship Command", 1)],
    "Caldari Frigate": [("Spaceship Command", 1)],
    "Gallente Frigate": [("Spaceship Command", 1)],
    "Minmatar Frigate": [("Spaceship Command", 1)],
    "Amarr Destroyer": [("Amarr Frigate", 3)],
    "Caldari Destroyer": [("Caldari Frigate", 3)],
    "Gallente Destroyer": [("Gallente Frigate", 3)],
    "Minmatar Destroyer": [("Minmatar Frigate", 3)],
    "Amarr Cruiser": [("Spaceship Command", 3), ("Amarr Destroyer", 3)],
    "Caldari Cruiser": [("Spaceship Command", 3), ("Caldari Destroyer", 3)],
    "Gallente Cruiser": [("Spaceship Command", 3), ("Gallente Destroyer", 3)],
    "Minmatar Cruiser": [("Spaceship Command", 3), ("Minmatar Destroyer", 3)],
    "Amarr Battlecruiser": [("Spaceship Command", 4), ("Amarr Cruiser", 3)],
    "Caldari Battlecruiser": [("Spaceship Command", 4), ("Caldari Cruiser", 3)],
    "Gallente Battlecruiser": [("Spaceship Command", 4), ("Gallente Cruiser", 3)],
    "Minmatar Battlecruiser": [("Spaceship Command", 4), ("Minmatar Cruiser", 3)],
    "Amarr Battleship": [("Spaceship Command", 5), ("Amarr Battlecruiser", 3)],
    "Caldari Battleship": [("Spaceship Command", 5), ("Caldari Battlecruiser", 3)],
    "Gallente Battleship": [("Spaceship Command", 5), ("Gallente Battlecruiser", 3)],
    "Minmatar Battleship": [("Spaceship Command", 5), ("Minmatar Battlecruiser", 3)],
    "Capital Ships": [("Spaceship Command", 5)],
    "Amarr Carrier": [("Capital Ships", 3), ("Amarr Battleship", 5)],
    "Caldari Carrier": [("Capital Ships", 3), ("Caldari Battleship", 5)],
    "Gallente Carrier": [("Capital Ships", 3), ("Gallente Battleship", 5)],
    "Minmatar Carrier": [("Capital Ships", 3), ("Minmatar Battleship", 5)],
    "Amarr Dreadnought": [("Capital Ships", 3), ("Amarr Battleship", 5)],
    "Caldari Dreadnought": [("Capital Ships", 3), ("Caldari Battleship", 5)],
    "Gallente Dreadnought": [("Capital Ships", 3), ("Gallente Battleship", 5)],
    "Minmatar Dreadnought": [("Capital Ships", 3), ("Minmatar Battleship", 5)],
    "Amarr Titan": [("Capital Ships", 5), ("Amarr Dreadnought", 3)],
    "Caldari Titan": [("Capital Ships", 5), ("Caldari Dreadnought", 3)],
    "Gallente Titan": [("Capital Ships", 5), ("Gallente Dreadnought", 3)],
    "Minmatar Titan": [("Capital Ships", 5), ("Minmatar Dreadnought", 3)],

    # ── Specialisation ships ─────────────────────────────
    "Interceptors": [("Evasive Maneuvering", 5)],
    "Covert Ops": [("Electronics Upgrades", 5)],
    "Assault Frigates": [("Spaceship Command", 3)],
    "Electronic Attack Ships": [("Electronic Warfare", 4)],
    "Interdictors": [("Graviton Physics", 4)],
    "Command Destroyers": [("Leadership", 3)],
    "Heavy Assault Cruisers": [("Spaceship Command", 5)],
    "Heavy Interdiction Cruisers": [("Graviton Physics", 5)],
    "Logistics Cruisers": [("Spaceship Command", 3)],
    "Recon Ships": [("Spaceship Command", 5), ("Electronics Upgrades", 5)],
    "Command Ships": [("Spaceship Command", 5)],
    "Strategic Cruisers": [("Spaceship Command", 5)],
    "Exhumers": [("Mining Barge", 5), ("Astrogeology", 5)],
    "Mining Barge": [("Mining", 4), ("Astrogeology", 3), ("Industry", 4)],
    "Transport Ships": [("Spaceship Command", 4)],
    "Marauders": [("Spaceship Command", 5), ("Advanced Weapon Upgrades", 5)],
    "Black Ops": [("Spaceship Command", 5)],
    "Freighters": [("Spaceship Command", 4), ("Advanced Industry", 3)],
    "Jump Freighters": [("Freighters", 3), ("Jump Drive Operation", 5)],
    "Capital Industrial Ships": [("Capital Ships", 1), ("Mining Barge", 5)],

    # ── Electronic Systems ───────────────────────────────
    "Propulsion Jamming": [("CPU Management", 1), ("Navigation", 2)],
    "Weapon Disruption": [("CPU Management", 3), ("Electronic Warfare", 3)],
    "Sensor Linking": [("CPU Management", 3), ("Electronic Warfare", 3)],
    "Target Painting": [("CPU Management", 3)],
    "Long Range Targeting": [("CPU Management", 2)],
    "Signature Analysis": [("CPU Management", 1)],
    "Cloaking": [("CPU Management", 4)],

    # ── Scanning ─────────────────────────────────────────
    "Astrometric Rangefinding": [("Astrometrics", 3)],
    "Astrometric Pinpointing": [("Astrometrics", 3)],
    "Astrometric Acquisition": [("Astrometrics", 3)],
    "Survey": [("CPU Management", 1)],
    "Archaeology": [("Survey", 3)],
    "Hacking": [("CPU Management", 3)],

    # ── Trade ────────────────────────────────────────────
    "Retail": [("Trade", 2)],
    "Wholesale": [("Retail", 5), ("Trade", 4)],
    "Tycoon": [("Wholesale", 5), ("Trade", 5)],
    "Accounting": [("Trade", 4)],
    "Broker Relations": [("Trade", 2)],
    "Marketing": [("Trade", 3)],
    "Daytrading": [("Trade", 4)],
    "Margin Trading": [("Trade", 4), ("Accounting", 4)],
    "Contracting": [("Social", 1)],
    "Corporation Contracting": [("Contracting", 3)],

    # ── Production ───────────────────────────────────────
    "Advanced Industry": [("Industry", 3)],
    "Mass Production": [("Industry", 3)],
    "Advanced Mass Production": [("Mass Production", 5)],
    "Supply Chain Management": [("Mass Production", 5), ("Advanced Industry", 3)],

    # ── Science ──────────────────────────────────────────
    "Research": [("Science", 1)],
    "Metallurgy": [("Science", 1)],
    "Laboratory Operation": [("Science", 1)],
    "Advanced Laboratory Operation": [("Laboratory Operation", 5)],
    "Cybernetics": [("Science", 3)],
    "Infomorph Psychology": [("Science", 1)],
    "Advanced Infomorph Psychology": [("Infomorph Psychology", 5)],
    "Biology": [("Science", 2)],
    "Neurotoxin Control": [("Biology", 4)],
    "Neurotoxin Recovery": [("Biology", 4)],

    # ── Mining / Resource ────────────────────────────────
    "Astrogeology": [("Mining", 4)],
    "Gas Cloud Harvesting": [("Mining", 2)],
    "Ice Harvesting": [("Mining", 4)],
    "Deep Core Mining": [("Mining", 5), ("Astrogeology", 5)],
    "Mining Upgrades": [("Mining", 3)],
    "Reprocessing Efficiency": [("Reprocessing", 3)],

    # ── Rigging ──────────────────────────────────────────
    "Armor Rigging": [("Jury Rigging", 3)],
    "Shield Rigging": [("Jury Rigging", 3)],
    "Astronautics Rigging": [("Jury Rigging", 3)],
    "Drones Rigging": [("Jury Rigging", 3)],
    "Electronic Superiority Rigging": [("Jury Rigging", 3)],
    "Projectile Weapon Rigging": [("Jury Rigging", 3)],
    "Energy Weapon Rigging": [("Jury Rigging", 3)],
    "Hybrid Weapon Rigging": [("Jury Rigging", 3)],
    "Launcher Rigging": [("Jury Rigging", 3)],

    # ── Social ───────────────────────────────────────────
    "Connections": [("Social", 3)],
    "Negotiation": [("Social", 2)],
    "Security Connections": [("Social", 3)],
    "Mining Connections": [("Social", 3)],
    "Distribution Connections": [("Social", 3)],
    "Diplomacy": [("Social", 3)],
    "Criminal Connections": [("Social", 3)],
    "Fast Talk": [("Social", 4)],

    # ── Fleet Support ────────────────────────────────────
    "Wing Command": [("Leadership", 5)],
    "Fleet Command": [("Wing Command", 5)],
    "Armored Command": [("Leadership", 1)],
    "Shield Command": [("Leadership", 1)],
    "Skirmish Command": [("Leadership", 1)],
    "Information Command": [("Leadership", 1)],
    "Mining Foreman": [("Leadership", 1), ("Mining", 3)],
    "Armored Command Specialist": [("Armored Command", 5)],
    "Shield Command Specialist": [("Shield Command", 5)],
    "Skirmish Command Specialist": [("Skirmish Command", 5)],
    "Information Command Specialist": [("Information Command", 5)],
    "Mining Director": [("Mining Foreman", 5)],
    "Command Burst Specialist": [("Leadership", 5)],

    # ── Planet Management ────────────────────────────────
    "Advanced Planetology": [("Planetology", 4)],
    "Command Center Upgrades": [("Planetology", 1)],
    "Interplanetary Consolidation": [("Planetology", 1)],
    "Remote Sensing": [("Planetology", 1)],
}


def get_prerequisites(skill_name: str) -> list:
    """Return direct prerequisites: [(skill_name, level), ...]"""
    return PREREQUISITES.get(skill_name, [])


def resolve_prerequisites(skill_name: str, target_level: int,
                          existing_entries: list) -> list:
    """
    Recursively resolve all prerequisites for a skill at a target level.
    Returns a flat, dependency-ordered list of (skill_name, level) tuples
    that need to be added.

    existing_entries: list of {"name": str, "level": int} already in the plan.
    """
    # Set of (name, level) already planned
    planned = {(e["name"], e["level"]) for e in existing_entries}

    needed = []
    visited = set()

    def _resolve(name, level):
        """Recursively add prerequisites before the skill itself."""
        key = (name, level)
        if key in visited:
            return
        visited.add(key)

        # First, resolve prerequisites for this skill
        prereqs = PREREQUISITES.get(name, [])
        for prereq_name, prereq_level in prereqs:
            # We need the prerequisite at `prereq_level`.
            # Add all levels 1..prereq_level for the prerequisite
            for lvl in range(1, prereq_level + 1):
                if (prereq_name, lvl) not in planned:
                    _resolve(prereq_name, lvl)

        # Now add this skill at this level (if not already planned)
        if key not in planned:
            needed.append(key)
            planned.add(key)

    # Resolve prerequisites for each level up to target
    for lvl in range(1, target_level + 1):
        _resolve(skill_name, lvl)

    return needed
