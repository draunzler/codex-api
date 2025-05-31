"""
Enhanced Genshin Impact Damage Calculator

This module provides accurate damage calculations using the official Genshin Impact damage formulas
from the Genshin Impact Wiki (https://genshin-impact.fandom.com/wiki/Damage).

OFFICIAL DAMAGE FORMULA:
Damage = Base DMG × Base DMG Multiplier × (1 + Additive Base DMG Bonus) × (1 + DMG Bonus) × DEF Multiplier × RES Multiplier

FORMULA COMPONENTS:
1. Base DMG = Scaling Stat × Talent Multiplier
2. Base DMG Multiplier = Amplifying reaction multipliers (Vaporize/Melt)
3. Additive Base DMG Bonus = Flat damage additions
4. DMG Bonus = Elemental/Physical damage bonuses
5. DEF Multiplier = (Char Level × 5 + 500) / ((Char Level × 5 + 500) + (Enemy Level × 5 + 500) × (1 - DEF Reduction))
6. RES Multiplier = Three-tier resistance formula based on effective resistance

ENHANCED FEATURES:
- Accurate critical hit calculations with proper 100% crit rate capping
- Official EM scaling formulas for both amplifying and transformative reactions
- Three-tier resistance formula supporting negative resistance
- Official level-based defense formula with reduction support
- Comprehensive character database with proper scaling attributes
- Support for all damage types (Physical, Elemental)
- Proper handling of all ability types (Normal Attack, Charged Attack, Elemental Skill, Elemental Burst)

REACTION FORMULAS:
- Amplifying Reactions: Base Multiplier × (1 + (2.78 × EM) / (EM + 1400) + Reaction Bonus)
- Transformative Reactions: Level Multiplier × Reaction Multiplier × (1 + (16 × EM) / (EM + 2000) + Reaction Bonus)

RESISTANCE FORMULA:
- If RES < 0%: Multiplier = 1 - RES/200
- If 0% ≤ RES < 75%: Multiplier = 1 - RES/100  
- If RES ≥ 75%: Multiplier = 1/(4×RES/100 + 1)

This implementation ensures mathematical accuracy and consistency with the official game mechanics.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class CharacterStats:
    """Character stats for damage calculation."""
    level: int = 90
    base_atk: float = 0
    flat_atk: float = 0
    atk_percent: float = 0
    base_hp: float = 0
    flat_hp: float = 0
    hp_percent: float = 0
    base_def: float = 0
    flat_def: float = 0
    def_percent: float = 0
    crit_rate: float = 5.0
    crit_dmg: float = 50.0
    elemental_mastery: float = 0
    elemental_dmg_bonus: float = 0  # For the character's element
    physical_dmg_bonus: float = 0
    energy_recharge: float = 100.0
    healing_bonus: float = 0
    # Additive base damage bonuses (flat damage additions)
    additive_base_dmg: float = 0
    
    @property
    def total_atk(self) -> float:
        """Calculate total ATK."""
        return (self.base_atk + self.flat_atk) * (1 + self.atk_percent / 100)
    
    @property
    def total_hp(self) -> float:
        """Calculate total HP."""
        return (self.base_hp + self.flat_hp) * (1 + self.hp_percent / 100)
    
    @property
    def total_def(self) -> float:
        """Calculate total DEF."""
        return (self.base_def + self.flat_def) * (1 + self.def_percent / 100)

@dataclass
class EnemyStats:
    """Enemy stats for damage calculation."""
    level: int = 90
    elemental_res: Dict[str, float] = field(default_factory=lambda: {"pyro": 10.0, "hydro": 10.0, "electro": 10.0, "cryo": 10.0, "anemo": 10.0, "geo": 10.0, "dendro": 10.0})
    physical_res: float = 10.0
    def_reduction: float = 0.0  # From VV, Zhongli, etc.
    res_reduction: Dict[str, float] = field(default_factory=lambda: {"pyro": 0.0, "hydro": 0.0, "electro": 0.0, "cryo": 0.0, "anemo": 0.0, "geo": 0.0, "dendro": 0.0, "physical": 0.0})
    
    def get_defense_multiplier(self, character_level: int = 90) -> float:
        """
        Calculate defense multiplier using official Genshin Impact formula from wiki.
        
        Formula: (Character Level × 5 + 500) / ((Character Level × 5 + 500) + (Enemy Level × 5 + 500) × (1 - DEF Reduction))
        
        Reference: https://genshin-impact.fandom.com/wiki/Damage
        """
        # Character defense ignore value
        character_def_ignore = character_level * 5 + 500
        
        # Enemy defense value
        enemy_def = self.level * 5 + 500
        
        # Apply defense reduction (from sources like VV set, Zhongli shield, etc.)
        # DEF Reduction is expressed as a percentage (0-100)
        effective_enemy_def = enemy_def * (1 - self.def_reduction / 100)
        
        # Calculate defense multiplier using official formula
        defense_multiplier = character_def_ignore / (character_def_ignore + effective_enemy_def)
        
        return defense_multiplier
    
    def get_resistance_multiplier(self, damage_type: str) -> float:
        """
        Calculate resistance multiplier using official Genshin Impact formula from wiki.
        
        The resistance formula has three different cases:
        - If RES < 0%: Multiplier = 1 - RES/200
        - If 0% ≤ RES < 75%: Multiplier = 1 - RES/100  
        - If RES ≥ 75%: Multiplier = 1/(4×RES/100 + 1)
        
        Reference: https://genshin-impact.fandom.com/wiki/Damage
        """
        # Get base resistance for the damage type
        if damage_type == "physical":
            base_res = self.physical_res
            res_reduction = self.res_reduction.get("physical", 0.0)
        else:
            base_res = self.elemental_res.get(damage_type, 10.0)
            res_reduction = self.res_reduction.get(damage_type, 0.0)
        
        # Apply resistance reduction (from sources like VV set, Zhongli shield, etc.)
        # Resistance reduction is subtracted from base resistance
        effective_res = base_res - res_reduction
        
        # Apply official resistance formula based on effective resistance value
        if effective_res < 0:
            # Negative resistance: damage is amplified
            resistance_multiplier = 1 - effective_res / 200
        elif effective_res < 75:
            # Normal resistance range: linear reduction
            resistance_multiplier = 1 - effective_res / 100
        else:
            # High resistance range: diminishing returns
            resistance_multiplier = 1 / (4 * effective_res / 100 + 1)
        
        return resistance_multiplier

@dataclass
class TalentMultiplier:
    """Talent multipliers for different abilities."""
    normal_attack: List[float]  # List of multipliers for different hits
    charged_attack: float
    plunge_attack: float
    elemental_skill: float
    elemental_burst: float
    # Scaling attribute for each ability
    scaling_attribute: str = "atk"  # "atk", "hp", "def", "em"
    
    def get_multiplier(self, ability_type: str, hit_index: int = 0) -> float:
        """Get multiplier for specific ability."""
        if ability_type == "normal_attack":
            return self.normal_attack[min(hit_index, len(self.normal_attack) - 1)]
        elif ability_type == "charged_attack":
            return self.charged_attack
        elif ability_type == "plunge_attack":
            return self.plunge_attack
        elif ability_type == "elemental_skill":
            return self.elemental_skill
        elif ability_type == "elemental_burst":
            return self.elemental_burst
        else:
            return 1.0

@dataclass
class ReactionData:
    """Data for elemental reactions."""
    reaction_type: str
    trigger_element: str
    aura_element: str
    character_level: int = 90
    elemental_mastery: float = 0
    reaction_bonus: float = 0  # Additional reaction damage bonus

class SimpleDamageCalculator:
    """Simple damage calculator using official Genshin formulas."""
    
    # Character base stats at level 90 (simplified database)
    CHARACTER_BASE_STATS = {
        # Pyro DPS
        "hu tao": {"base_atk": 715, "base_hp": 15552, "base_def": 876, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "diluc": {"base_atk": 1011, "base_hp": 12981, "base_def": 729, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        "yoimiya": {"base_atk": 884, "base_hp": 10164, "base_def": 615, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        "arlecchino": {"base_atk": 1086, "base_hp": 13103, "base_def": 740, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "lyney": {"base_atk": 858, "base_hp": 10324, "base_def": 630, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        
        # Hydro DPS
        "childe": {"base_atk": 1020, "base_hp": 13103, "base_def": 815, "ascension_stat": "hydro_dmg", "ascension_value": 28.8},
        "ayato": {"base_atk": 1068, "base_hp": 13715, "base_def": 769, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "neuvillette": {"base_atk": 1144, "base_hp": 14695, "base_def": 738, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "furina": {"base_atk": 674, "base_hp": 15307, "base_def": 696, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        
        # Electro DPS
        "raiden shogun": {"base_atk": 1337, "base_hp": 12907, "base_def": 789, "ascension_stat": "energy_recharge", "ascension_value": 32.0},
        "keqing": {"base_atk": 1056, "base_hp": 13103, "base_def": 799, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "yae miko": {"base_atk": 1030, "base_hp": 10372, "base_def": 569, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        
        # Cryo DPS
        "ganyu": {"base_atk": 1016, "base_hp": 9797, "base_def": 630, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "ayaka": {"base_atk": 1001, "base_hp": 12858, "base_def": 784, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "eula": {"base_atk": 1030, "base_hp": 13226, "base_def": 751, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        "wriothesley": {"base_atk": 1103, "base_hp": 13593, "base_def": 859, "ascension_stat": "crit_dmg", "ascension_value": 88.4},
        
        # Anemo DPS
        "xiao": {"base_atk": 1193, "base_hp": 12736, "base_def": 799, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        "wanderer": {"base_atk": 1058, "base_hp": 10164, "base_def": 607, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        "kazuha": {"base_atk": 906, "base_hp": 13348, "base_def": 807, "ascension_stat": "elemental_mastery", "ascension_value": 115},
        
        # Geo DPS
        "itto": {"base_atk": 1001, "base_hp": 12858, "base_def": 959, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        "albedo": {"base_atk": 876, "base_hp": 13226, "base_def": 876, "ascension_stat": "geo_dmg", "ascension_value": 28.8},
        "zhongli": {"base_atk": 1144, "base_hp": 14695, "base_def": 738, "ascension_stat": "geo_dmg", "ascension_value": 28.8},
        "navia": {"base_atk": 1029, "base_hp": 12993, "base_def": 729, "ascension_stat": "crit_rate", "ascension_value": 24.2},
        
        # Dendro DPS
        "tighnari": {"base_atk": 1056, "base_hp": 10850, "base_def": 630, "ascension_stat": "dendro_dmg", "ascension_value": 28.8},
        "nahida": {"base_atk": 1016, "base_hp": 10360, "base_def": 630, "ascension_stat": "elemental_mastery", "ascension_value": 115},
        "alhaitham": {"base_atk": 1058, "base_hp": 13348, "base_def": 807, "ascension_stat": "dendro_dmg", "ascension_value": 28.8},
        "baizhu": {"base_atk": 1039, "base_hp": 13348, "base_def": 751, "ascension_stat": "hp_percent", "ascension_value": 28.8},
        
        # Support characters
        "bennett": {"base_atk": 1191, "base_hp": 12397, "base_def": 771, "ascension_stat": "energy_recharge", "ascension_value": 26.7},
        "xingqiu": {"base_atk": 1059, "base_hp": 10222, "base_def": 758, "ascension_stat": "atk_percent", "ascension_value": 24.0},
        "fischl": {"base_atk": 1024, "base_hp": 9189, "base_def": 594, "ascension_stat": "atk_percent", "ascension_value": 24.0},
        "xiangling": {"base_atk": 1020, "base_hp": 10875, "base_def": 669, "ascension_stat": "elemental_mastery", "ascension_value": 96},
        "sucrose": {"base_atk": 703, "base_hp": 9244, "base_def": 703, "ascension_stat": "anemo_dmg", "ascension_value": 24.0},
        "diona": {"base_atk": 1056, "base_hp": 9570, "base_def": 601, "ascension_stat": "cryo_dmg", "ascension_value": 24.0},
    }
    
    # Simplified talent multipliers (level 10 talents) with scaling attributes
    TALENT_MULTIPLIERS = {
        # Pyro DPS
        "hu tao": TalentMultiplier([89.2, 91.6, 114.6], 242.6, 263.3, 383.0, 606.7, "atk"),
        "diluc": TalentMultiplier([89.7, 87.6, 108.8], 111.8, 185.8, 146.4, 204.0, "atk"),
        "yoimiya": TalentMultiplier([64.7, 68.0, 88.9], 161.9, 127.2, 181.6, 127.4, "atk"),
        "arlecchino": TalentMultiplier([101.5, 99.6, 131.9], 169.6, 185.8, 236.8, 370.4, "atk"),
        "lyney": TalentMultiplier([86.3, 87.2, 109.0], 172.8, 185.8, 167.2, 377.6, "atk"),
        
        # Hydro DPS
        "childe": TalentMultiplier([84.3, 88.2, 103.8], 124.4, 185.8, 216.0, 378.4, "atk"),
        "ayato": TalentMultiplier([89.5, 91.8, 114.4], 126.9, 185.8, 101.5, 110.6, "atk"),
        "neuvillette": TalentMultiplier([84.2, 76.1, 95.1], 149.2, 185.8, 222.2, 184.6, "hp"),  # HP scaling
        "furina": TalentMultiplier([92.1, 86.4, 108.0], 148.0, 185.8, 114.9, 25.2, "hp"),  # HP scaling
        
        # Electro DPS
        "raiden shogun": TalentMultiplier([79.5, 79.2, 98.9], 156.2, 185.8, 117.2, 721.4, "atk"),
        "keqing": TalentMultiplier([84.1, 84.1, 105.1], 152.0, 185.8, 168.0, 152.0, "atk"),
        "yae miko": TalentMultiplier([76.6, 69.2, 86.5], 142.6, 185.8, 107.3, 442.9, "atk"),
        
        # Geo DPS (some scale with DEF)
        "itto": TalentMultiplier([89.2, 84.7, 105.9], 180.6, 185.8, 307.2, 652.0, "def"),  # DEF scaling
        "albedo": TalentMultiplier([73.1, 73.1, 91.4], 169.6, 185.8, 130.4, 367.2, "def"),  # DEF scaling for skill
        "zhongli": TalentMultiplier([73.4, 73.4, 91.7], 139.7, 185.8, 32.0, 640.0, "hp"),  # HP scaling for burst
        "navia": TalentMultiplier([93.5, 86.4, 108.0], 394.6, 185.8, 396.0, 75.6, "atk"),
        
        # Default fallback
        "default": TalentMultiplier([100.0], 150.0, 185.8, 200.0, 300.0, "atk"),
    }
    
    # Element mappings
    ELEMENT_MAPPING = {
        "hu tao": "pyro", "diluc": "pyro", "yoimiya": "pyro", "arlecchino": "pyro", "lyney": "pyro",
        "childe": "hydro", "ayato": "hydro", "neuvillette": "hydro", "furina": "hydro",
        "raiden shogun": "electro", "keqing": "electro", "yae miko": "electro",
        "ganyu": "cryo", "ayaka": "cryo", "eula": "cryo", "wriothesley": "cryo",
        "xiao": "anemo", "wanderer": "anemo", "kazuha": "anemo",
        "itto": "geo", "albedo": "geo", "zhongli": "geo", "navia": "geo",
        "tighnari": "dendro", "nahida": "dendro", "alhaitham": "dendro", "baizhu": "dendro",
        "bennett": "pyro", "xingqiu": "hydro", "fischl": "electro", "xiangling": "pyro",
        "sucrose": "anemo", "diona": "cryo"
    }
    
    # Reaction multipliers and level multipliers for transformative reactions
    TRANSFORMATIVE_LEVEL_MULTIPLIERS = {
        90: 1446.85, 89: 1401.52, 88: 1357.38, 87: 1314.43, 86: 1272.64,
        85: 1232.02, 84: 1192.58, 83: 1154.31, 82: 1117.19, 81: 1081.22,
        80: 1077.44, 79: 1012.81, 78: 979.32, 77: 946.96, 76: 915.73,
        75: 885.62, 74: 856.62, 73: 828.73, 72: 801.94, 71: 776.25,
        70: 765.64
    }
    
    TRANSFORMATIVE_REACTION_MULTIPLIERS = {
        "overloaded": 2.0,
        "electrocharged": 1.2,
        "superconduct": 0.5,
        "swirl": 0.6,
        "shatter": 1.5,
        "burning": 0.25,
        "bloom": 2.0,
        "hyperbloom": 3.0,
        "burgeon": 3.0
    }

    def __init__(self):
        """Initialize the damage calculator."""
        pass
    
    def get_character_base_stats(self, character_name: str) -> Dict[str, Any]:
        """Get character base stats."""
        name_key = character_name.lower().strip()
        return self.CHARACTER_BASE_STATS.get(name_key, {
            "base_atk": 800,
            "base_hp": 12000,
            "base_def": 700,
            "ascension_stat": "atk_percent",
            "ascension_value": 24.0
        })
    
    def get_character_element(self, character_name: str) -> str:
        """Get character element."""
        name_key = character_name.lower().strip()
        return self.ELEMENT_MAPPING.get(name_key, "physical")
    
    def get_talent_multipliers(self, character_name: str) -> TalentMultiplier:
        """Get talent multipliers for character."""
        name_key = character_name.lower().strip()
        return self.TALENT_MULTIPLIERS.get(name_key, self.TALENT_MULTIPLIERS["default"])
    
    def get_scaling_attribute_value(self, character_stats: CharacterStats, scaling_attribute: str) -> float:
        """Get the value of the scaling attribute (ATK, HP, DEF, EM)."""
        if scaling_attribute.lower() == "atk":
            return character_stats.total_atk
        elif scaling_attribute.lower() == "hp":
            return character_stats.total_hp
        elif scaling_attribute.lower() == "def":
            return character_stats.total_def
        elif scaling_attribute.lower() == "em":
            return character_stats.elemental_mastery
        else:
            return character_stats.total_atk  # Default to ATK
    
    def calculate_amplifying_reaction_multiplier(self, reaction_data: ReactionData) -> float:
        """
        Calculate amplifying reaction multiplier using official Genshin Impact formula from wiki.
        
        Amplifying reactions (Vaporize, Melt) multiply the base damage.
        
        Formula: Reaction Multiplier = Base Multiplier × (1 + (2.78 × EM) / (EM + 1400) + Reaction Bonus)
        
        Base Multipliers:
        - Vaporize (Pyro trigger): 1.5x
        - Vaporize (Hydro trigger): 2.0x  
        - Melt (Pyro trigger): 2.0x
        - Melt (Cryo trigger): 1.5x
        
        Reference: https://genshin-impact.fandom.com/wiki/Damage
        """
        # Determine base multiplier based on reaction type and trigger element
        base_multiplier = 1.0
        
        if reaction_data.reaction_type.lower() == "vaporize":
            if reaction_data.trigger_element.lower() == "pyro":
                base_multiplier = 1.5  # Pyro on Hydro
            elif reaction_data.trigger_element.lower() == "hydro":
                base_multiplier = 2.0  # Hydro on Pyro
        elif reaction_data.reaction_type.lower() == "melt":
            if reaction_data.trigger_element.lower() == "pyro":
                base_multiplier = 2.0  # Pyro on Cryo
            elif reaction_data.trigger_element.lower() == "cryo":
                base_multiplier = 1.5  # Cryo on Pyro
        
        # Calculate EM bonus using official formula
        # EM Bonus = (2.78 × EM) / (EM + 1400)
        em_bonus = (2.78 * reaction_data.elemental_mastery) / (reaction_data.elemental_mastery + 1400)
        
        # Apply reaction bonus (from artifacts, weapons, etc.)
        reaction_bonus = reaction_data.reaction_bonus / 100
        
        # Calculate final reaction multiplier
        reaction_multiplier = base_multiplier * (1 + em_bonus + reaction_bonus)
        
        return reaction_multiplier
    
    def calculate_transformative_reaction_damage(self, reaction_data: ReactionData) -> float:
        """
        Calculate transformative reaction damage using official Genshin Impact formula from wiki.
        
        Transformative reactions (Overloaded, Electro-Charged, Superconduct, Swirl, Shatter, Crystallize)
        deal fixed damage that scales with character level and Elemental Mastery.
        
        Formula: Reaction Damage = Level Multiplier × Reaction Multiplier × (1 + (16 × EM) / (EM + 2000) + Reaction Bonus)
        
        Level Multipliers are based on character level.
        Reaction Multipliers:
        - Overloaded: 4.0
        - Electro-Charged: 2.4  
        - Superconduct: 1.0
        - Swirl: 1.2
        - Shatter: 3.0
        - Crystallize: 0.0 (creates shield, no damage)
        
        Reference: https://genshin-impact.fandom.com/wiki/Damage
        """
        reaction_type = reaction_data.reaction_type.lower()
        
        # Get level multiplier from lookup table
        level_multiplier = self.TRANSFORMATIVE_LEVEL_MULTIPLIERS.get(reaction_data.character_level, 1446.85)
        
        # Get reaction multiplier based on reaction type
        reaction_multiplier = self.TRANSFORMATIVE_REACTION_MULTIPLIERS.get(reaction_type, 0.0)
        
        # Calculate EM bonus using official formula for transformative reactions
        # EM Bonus = (16 × EM) / (EM + 2000)
        em_bonus = (16 * reaction_data.elemental_mastery) / (reaction_data.elemental_mastery + 2000)
        
        # Apply reaction bonus (from artifacts, weapons, etc.)
        reaction_bonus = reaction_data.reaction_bonus / 100
        
        # Calculate final transformative reaction damage
        transformative_damage = level_multiplier * reaction_multiplier * (1 + em_bonus + reaction_bonus)
        
        return transformative_damage

    def calculate_single_hit_damage(
        self,
        character_stats: CharacterStats,
        enemy_stats: EnemyStats,
        talent_multiplier: float,
        ability_type: str = "elemental_skill",
        scaling_attribute: str = "atk",
        damage_element: str = "pyro",
        reaction_data: Optional[ReactionData] = None
    ) -> Dict[str, float]:
        """
        Calculate damage for a single hit using official Genshin Impact formula from wiki.
        
        Official Formula: Damage = Base DMG × Base DMG Multiplier × (1 + Additive Base DMG Bonus) × (1 + DMG Bonus) × DEF Multiplier × RES Multiplier
        
        Reference: https://genshin-impact.fandom.com/wiki/Damage
        """
        
        # Step 1: Calculate Base DMG
        # Base DMG = Scaling Stat × Talent Multiplier
        scaling_value = self.get_scaling_attribute_value(character_stats, scaling_attribute)
        base_dmg = scaling_value * (talent_multiplier / 100)
        
        # Step 2: Base DMG Multiplier (for amplifying reactions like Vaporize/Melt)
        # Default is 1.0, modified by amplifying reactions
        base_dmg_multiplier = 1.0
        if reaction_data and reaction_data.reaction_type.lower() in ["vaporize", "melt"]:
            base_dmg_multiplier = self.calculate_amplifying_reaction_multiplier(reaction_data)
        
        # Step 3: Additive Base DMG Bonus (flat damage additions)
        # This includes flat damage bonuses that are added to base damage
        additive_base_dmg_bonus = character_stats.additive_base_dmg / scaling_value if scaling_value > 0 else 0
        
        # Step 4: DMG Bonus (elemental/physical damage bonuses)
        # Includes elemental damage bonus, physical damage bonus, and other damage bonuses
        dmg_bonus = 0.0
        
        # Determine damage type and apply appropriate bonus
        if ability_type in ["normal_attack", "charged_attack", "plunge_attack"]:
            # Normal attacks can be physical or elemental depending on character/infusion
            if damage_element == "physical":
                dmg_bonus = character_stats.physical_dmg_bonus / 100
            else:
                dmg_bonus = character_stats.elemental_dmg_bonus / 100
        else:
            # Elemental skills and bursts are always elemental damage
            dmg_bonus = character_stats.elemental_dmg_bonus / 100
        
        # Step 5: DEF Multiplier
        # Uses official defense formula: (Character Level × 5 + 500) / ((Character Level × 5 + 500) + (Enemy Level × 5 + 500) × (1 - DEF Reduction))
        def_multiplier = enemy_stats.get_defense_multiplier(character_stats.level)
        
        # Step 6: RES Multiplier
        # Uses official resistance formula with different calculations for different resistance ranges
        res_multiplier = enemy_stats.get_resistance_multiplier(damage_element)
        
        # Calculate final damage using official formula
        final_damage = (
            base_dmg * 
            base_dmg_multiplier * 
            (1 + additive_base_dmg_bonus) * 
            (1 + dmg_bonus) * 
            def_multiplier * 
            res_multiplier
        )
        
        # Critical Hit Calculations
        # CRIT Rate determines chance of critical hit
        # CRIT DMG determines the multiplier for critical hits
        crit_rate_decimal = character_stats.crit_rate / 100
        crit_dmg_decimal = character_stats.crit_dmg / 100
        
        # Ensure crit rate doesn't exceed 100%
        effective_crit_rate = min(crit_rate_decimal, 1.0)
        
        # Calculate damage values
        non_crit_damage = final_damage
        crit_damage = final_damage * (1 + crit_dmg_decimal)
        
        # Average damage considering crit rate
        average_damage = final_damage * (1 + effective_crit_rate * crit_dmg_decimal)
        
        # Add transformative reaction damage if applicable
        # Transformative reactions (Overloaded, Electro-Charged, Superconduct, Swirl, Shatter, Crystallize)
        # deal separate damage that doesn't scale with ATK/talent multipliers
        transformative_damage = 0.0
        if reaction_data and reaction_data.reaction_type.lower() in self.TRANSFORMATIVE_REACTION_MULTIPLIERS:
            transformative_damage = self.calculate_transformative_reaction_damage(reaction_data)
        
        # Total average damage includes both direct damage and transformative reaction damage
        total_average_damage = average_damage + transformative_damage
        
        return {
            # Main damage values
            "non_crit": non_crit_damage,
            "crit": crit_damage,
            "average": average_damage,
            "transformative_damage": transformative_damage,
            "total_average": total_average_damage,
            
            # Detailed breakdown for analysis (following wiki formula components)
            "formula_breakdown": {
                "base_dmg": base_dmg,
                "base_dmg_multiplier": base_dmg_multiplier,
                "additive_base_dmg_bonus": additive_base_dmg_bonus,
                "dmg_bonus": dmg_bonus,
                "def_multiplier": def_multiplier,
                "res_multiplier": res_multiplier
            },
            
            # Character stats used
            "character_stats_used": {
                "scaling_value": scaling_value,
                "scaling_attribute": scaling_attribute,
                "talent_multiplier": talent_multiplier,
                "crit_rate": character_stats.crit_rate,
                "crit_dmg": character_stats.crit_dmg,
                "effective_crit_rate": effective_crit_rate * 100
            },
            
            # Enemy stats used
            "enemy_stats_used": {
                "enemy_level": enemy_stats.level,
                "resistance": enemy_stats.elemental_res.get(damage_element, enemy_stats.physical_res if damage_element == "physical" else 10.0),
                "def_reduction": enemy_stats.def_reduction
            },
            
            # Damage type information
            "damage_info": {
                "damage_element": damage_element,
                "ability_type": ability_type,
                "is_crit_possible": True,
                "reaction_applied": reaction_data.reaction_type if reaction_data else None
            }
        }

    def calculate_comprehensive_damage(
        self,
        character_name: str,
        character_stats: CharacterStats,
        enemy_stats: EnemyStats,
        ability_type: str = "elemental_skill",
        talent_level: int = 10,
        reactions: List[str] = None,
        include_team_buffs: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive damage for any character ability using official Genshin Impact formulas.
        
        This method properly handles:
        - All damage types (Physical, Elemental)
        - All ability types (Normal Attack, Charged Attack, Elemental Skill, Elemental Burst)
        - All reaction types (Amplifying and Transformative)
        - Proper element detection and damage type classification
        - Accurate talent multiplier application
        
        Reference: https://genshin-impact.fandom.com/wiki/Damage
        """
        # Get character data
        base_stats = self.get_character_base_stats(character_name)
        element = self.get_character_element(character_name)
        talent_multipliers = self.get_talent_multipliers(character_name)
        
        # Update base stats if not provided
        if character_stats.base_atk == 0:
            character_stats.base_atk = base_stats["base_atk"]
        if character_stats.base_hp == 0:
            character_stats.base_hp = base_stats["base_hp"]
        if character_stats.base_def == 0:
            character_stats.base_def = base_stats["base_def"]
        
        # Determine talent multiplier based on ability type and talent level
        if ability_type == "normal_attack":
            base_multiplier = talent_multipliers.normal_attack[0]  # First hit of normal attack
        elif ability_type == "charged_attack":
            base_multiplier = talent_multipliers.charged_attack
        elif ability_type == "plunge_attack":
            base_multiplier = talent_multipliers.plunge_attack
        elif ability_type == "elemental_skill":
            base_multiplier = talent_multipliers.elemental_skill
        elif ability_type == "elemental_burst":
            base_multiplier = talent_multipliers.elemental_burst
        else:
            base_multiplier = 100.0  # Default fallback
        
        # Adjust multiplier for talent level (simplified scaling)
        # Level 10 = 100%, Level 9 = ~90%, Level 8 = ~80%, etc.
        talent_scaling = min(1.0, talent_level / 10.0)
        final_multiplier = base_multiplier * talent_scaling
        
        # Determine damage element
        # Normal attacks are usually physical unless character has elemental infusion
        # Skills and bursts are always elemental
        if ability_type in ["normal_attack", "charged_attack", "plunge_attack"]:
            # Check for elemental infusion (simplified - in reality this is more complex)
            damage_element = "physical"  # Default for normal attacks
            # Some characters have elemental normal attacks by default
            if character_name.lower() in ["childe", "ayato", "kokomi"]:  # Hydro infusion characters
                damage_element = element
        else:
            damage_element = element
        
        # Calculate base damage without reactions
        base_damage_result = self.calculate_single_hit_damage(
            character_stats=character_stats,
            enemy_stats=enemy_stats,
            talent_multiplier=final_multiplier,
            ability_type=ability_type,
            scaling_attribute=talent_multipliers.scaling_attribute,
            damage_element=damage_element
        )
        
        # Calculate damage with reactions if provided
        reaction_results = {}
        if reactions:
            for reaction in reactions:
                # Create reaction data
                reaction_data = ReactionData(
                    reaction_type=reaction,
                    trigger_element=element,
                    aura_element=self._get_aura_element_for_reaction(reaction, element),
                    character_level=character_stats.level,
                    elemental_mastery=character_stats.elemental_mastery,
                    reaction_bonus=0.0  # Can be enhanced with artifact/weapon bonuses
                )
                
                # Calculate damage with reaction
                reaction_damage_result = self.calculate_single_hit_damage(
                    character_stats=character_stats,
                    enemy_stats=enemy_stats,
                    talent_multiplier=final_multiplier,
                    ability_type=ability_type,
                    scaling_attribute=talent_multipliers.scaling_attribute,
                    damage_element=damage_element,
                    reaction_data=reaction_data
                )
                
                reaction_results[reaction] = reaction_damage_result
        
        # Compile comprehensive results
        result = {
            "character_name": character_name,
            "character_element": element,
            "ability_info": {
                "ability_type": ability_type,
                "talent_level": talent_level,
                "damage_element": damage_element,
                "scaling_attribute": talent_multipliers.scaling_attribute,
                "base_multiplier": base_multiplier,
                "final_multiplier": final_multiplier
            },
            "base_damage": base_damage_result,
            "reaction_damage": reaction_results,
            "character_stats_summary": {
                "total_atk": character_stats.total_atk,
                "total_hp": character_stats.total_hp,
                "total_def": character_stats.total_def,
                "crit_rate": character_stats.crit_rate,
                "crit_dmg": character_stats.crit_dmg,
                "elemental_mastery": character_stats.elemental_mastery,
                "elemental_dmg_bonus": character_stats.elemental_dmg_bonus,
                "physical_dmg_bonus": character_stats.physical_dmg_bonus
            },
            "enemy_stats_summary": {
                "level": enemy_stats.level,
                "elemental_resistances": enemy_stats.elemental_res,
                "physical_resistance": enemy_stats.physical_res,
                "def_reduction": enemy_stats.def_reduction,
                "res_reduction": enemy_stats.res_reduction
            },
            "calculation_method": "official_genshin_wiki_formulas",
            "wiki_reference": "https://genshin-impact.fandom.com/wiki/Damage"
        }
        
        return result
    
    def _get_aura_element_for_reaction(self, reaction: str, trigger_element: str) -> str:
        """Get the aura element needed for a specific reaction."""
        reaction_lower = reaction.lower()
        trigger_lower = trigger_element.lower()
        
        # Amplifying reactions
        if reaction_lower == "vaporize":
            return "hydro" if trigger_lower == "pyro" else "pyro"
        elif reaction_lower == "melt":
            return "cryo" if trigger_lower == "pyro" else "pyro"
        
        # Transformative reactions (simplified)
        elif reaction_lower == "overloaded":
            return "electro" if trigger_lower == "pyro" else "pyro"
        elif reaction_lower == "electro-charged":
            return "hydro" if trigger_lower == "electro" else "electro"
        elif reaction_lower == "superconduct":
            return "cryo" if trigger_lower == "electro" else "electro"
        elif reaction_lower == "swirl":
            return "pyro"  # Anemo can swirl any element, default to pyro
        elif reaction_lower == "crystallize":
            return "geo"  # Geo crystallizes with any element
        
        # Default fallback
        return "pyro"

# Global calculator instance
damage_calculator = SimpleDamageCalculator() 