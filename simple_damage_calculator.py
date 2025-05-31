"""
Simple Damage Calculator inspired by Akasha.cv and GI Damage Calculator

This module provides clean, accurate damage calculations using the official
Genshin Impact damage formulas from the wiki without unnecessary complexity.

Official Formula: Damage = Base DMG × Base DMG Multiplier × (1 + Additive Base DMG Bonus) × (1 + DMG Bonus) × DEF Multiplier × RES Multiplier
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
        """Calculate defense multiplier using official formula."""
        enemy_def = self.level * 5 + 500
        character_def_ignore = character_level * 5 + 500
        
        # Apply defense reduction
        effective_def = enemy_def * (1 - self.def_reduction / 100)
        
        return character_def_ignore / (character_def_ignore + effective_def)
    
    def get_resistance_multiplier(self, damage_type: str) -> float:
        """Calculate resistance multiplier using official formula."""
        if damage_type == "physical":
            base_res = self.physical_res
            res_reduction = self.res_reduction.get("physical", 0.0)
        else:
            base_res = self.elemental_res.get(damage_type, 10.0)
            res_reduction = self.res_reduction.get(damage_type, 0.0)
        
        # Apply resistance reduction
        effective_res = base_res - res_reduction
        
        # Official resistance formula
        if effective_res < 0:
            return 1 - effective_res / 200  # Negative resistance formula
        elif effective_res < 75:
            return 1 - effective_res / 100
        else:
            return 1 / (4 * effective_res / 100 + 1)

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
        """Calculate amplifying reaction multiplier (Vaporize, Melt)."""
        reaction_type = reaction_data.reaction_type.lower()
        
        # Base multipliers
        if reaction_type == "vaporize":
            if reaction_data.trigger_element == "pyro":  # Pyro triggers on Hydro
                base_multiplier = 1.5
            else:  # Hydro triggers on Pyro
                base_multiplier = 2.0
        elif reaction_type == "melt":
            if reaction_data.trigger_element == "pyro":  # Pyro triggers on Cryo
                base_multiplier = 2.0
            else:  # Cryo triggers on Pyro
                base_multiplier = 1.5
        else:
            return 1.0
        
        # EM bonus for amplifying reactions
        em_bonus = (2.78 * reaction_data.elemental_mastery) / (reaction_data.elemental_mastery + 1400)
        
        return base_multiplier * (1 + em_bonus + reaction_data.reaction_bonus / 100)
    
    def calculate_transformative_reaction_damage(self, reaction_data: ReactionData) -> float:
        """Calculate transformative reaction damage (Overloaded, Electrocharged, etc.)."""
        reaction_type = reaction_data.reaction_type.lower()
        
        if reaction_type not in self.TRANSFORMATIVE_REACTION_MULTIPLIERS:
            return 0.0
        
        # Level multiplier
        level_multiplier = self.TRANSFORMATIVE_LEVEL_MULTIPLIERS.get(
            reaction_data.character_level, 1446.85
        )
        
        # Reaction multiplier
        reaction_multiplier = self.TRANSFORMATIVE_REACTION_MULTIPLIERS[reaction_type]
        
        # EM bonus for transformative reactions
        em_bonus = (16 * reaction_data.elemental_mastery) / (reaction_data.elemental_mastery + 2000)
        
        return level_multiplier * reaction_multiplier * (1 + em_bonus + reaction_data.reaction_bonus / 100)

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
        Calculate damage for a single hit using official Genshin formula.
        
        Official Formula: Damage = Base DMG × Base DMG Multiplier × (1 + Additive Base DMG Bonus) × (1 + DMG Bonus) × DEF Multiplier × RES Multiplier
        """
        
        # Step 1: Calculate Base DMG
        scaling_value = self.get_scaling_attribute_value(character_stats, scaling_attribute)
        base_dmg = scaling_value * (talent_multiplier / 100)
        
        # Step 2: Base DMG Multiplier (for amplifying reactions)
        base_dmg_multiplier = 1.0
        if reaction_data and reaction_data.reaction_type.lower() in ["vaporize", "melt"]:
            base_dmg_multiplier = self.calculate_amplifying_reaction_multiplier(reaction_data)
        
        # Step 3: Additive Base DMG Bonus (flat damage additions)
        additive_base_dmg_bonus = character_stats.additive_base_dmg / scaling_value if scaling_value > 0 else 0
        
        # Step 4: DMG Bonus (elemental/physical damage bonuses)
        if ability_type in ["normal_attack", "charged_attack", "plunge_attack"] and damage_element == "physical":
            dmg_bonus = character_stats.physical_dmg_bonus / 100
        else:
            dmg_bonus = character_stats.elemental_dmg_bonus / 100
        
        # Step 5: DEF Multiplier
        def_multiplier = enemy_stats.get_defense_multiplier(character_stats.level)
        
        # Step 6: RES Multiplier
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
        
        # Critical hit calculations
        crit_multiplier = 1 + (character_stats.crit_dmg / 100)
        average_crit_multiplier = 1 + (character_stats.crit_rate / 100) * (character_stats.crit_dmg / 100)
        
        # Final damage values
        non_crit_damage = final_damage
        crit_damage = final_damage * crit_multiplier
        average_damage = final_damage * average_crit_multiplier
        
        # Add transformative reaction damage if applicable
        transformative_damage = 0.0
        if reaction_data and reaction_data.reaction_type.lower() in self.TRANSFORMATIVE_REACTION_MULTIPLIERS:
            transformative_damage = self.calculate_transformative_reaction_damage(reaction_data)
        
        return {
            "non_crit": non_crit_damage,
            "crit": crit_damage,
            "average": average_damage,
            "transformative_damage": transformative_damage,
            "total_average": average_damage + transformative_damage,
            # Breakdown for analysis
            "base_dmg": base_dmg,
            "base_dmg_multiplier": base_dmg_multiplier,
            "additive_base_dmg_bonus": additive_base_dmg_bonus,
            "dmg_bonus": dmg_bonus,
            "def_multiplier": def_multiplier,
            "res_multiplier": res_multiplier,
            "scaling_value": scaling_value,
            "scaling_attribute": scaling_attribute,
            "talent_multiplier": talent_multiplier,
            "crit_rate": character_stats.crit_rate,
            "crit_dmg": character_stats.crit_dmg
        }

    def calculate_character_damage(
        self,
        character_name: str,
        character_stats: CharacterStats,
        enemy_stats: EnemyStats,
        reactions: List[str] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive damage for a character using official formulas."""
        
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
        
        results = {
            "character_name": character_name,
            "element": element,
            "character_stats": {
                "total_atk": character_stats.total_atk,
                "total_hp": character_stats.total_hp,
                "total_def": character_stats.total_def,
                "crit_rate": character_stats.crit_rate,
                "crit_dmg": character_stats.crit_dmg,
                "elemental_mastery": character_stats.elemental_mastery,
                "elemental_dmg_bonus": character_stats.elemental_dmg_bonus,
                "physical_dmg_bonus": character_stats.physical_dmg_bonus
            },
            "damage_breakdown": {}
        }
        
        # Calculate damage for each ability
        abilities = [
            ("normal_attack", talent_multipliers.normal_attack[0], "normal_attack"),
            ("charged_attack", talent_multipliers.charged_attack, "charged_attack"),
            ("elemental_skill", talent_multipliers.elemental_skill, "elemental_skill"),
            ("elemental_burst", talent_multipliers.elemental_burst, "elemental_burst")
        ]
        
        for ability_name, multiplier, ability_type in abilities:
            # Determine damage element (physical for normal attacks unless specified otherwise)
            damage_element = element if ability_type in ["elemental_skill", "elemental_burst"] else "physical"
            
            damage_result = self.calculate_single_hit_damage(
                character_stats, 
                enemy_stats, 
                multiplier, 
                ability_type,
                talent_multipliers.scaling_attribute,
                damage_element
            )
            results["damage_breakdown"][ability_name] = damage_result
            
            # Calculate with reactions if provided
            if reactions:
                results["damage_breakdown"][f"{ability_name}_reactions"] = {}
                for reaction in reactions:
                    # Create reaction data
                    reaction_data = ReactionData(
                        reaction_type=reaction,
                        trigger_element=element,
                        aura_element="hydro" if reaction.lower() == "vaporize" else "pyro",  # Simplified
                        character_level=character_stats.level,
                        elemental_mastery=character_stats.elemental_mastery
                    )
                    
                    reaction_damage = self.calculate_single_hit_damage(
                        character_stats, 
                        enemy_stats, 
                        multiplier, 
                        ability_type,
                        talent_multipliers.scaling_attribute,
                        damage_element,
                        reaction_data
                    )
                    results["damage_breakdown"][f"{ability_name}_reactions"][reaction] = reaction_damage
        
        return results
    
    def calculate_team_damage_with_buffs(
        self,
        main_dps_name: str,
        team_composition: List[str],
        character_stats: CharacterStats,
        enemy_stats: EnemyStats,
        reactions: List[str] = None
    ) -> Dict[str, Any]:
        """Calculate team damage with buffs and synergies."""
        
        # Calculate base damage without buffs
        base_damage = self.calculate_character_damage(
            main_dps_name, character_stats, enemy_stats, reactions
        )
        
        # Apply team buffs (simplified implementation)
        buffed_stats = CharacterStats(
            level=character_stats.level,
            base_atk=character_stats.base_atk,
            flat_atk=character_stats.flat_atk,
            atk_percent=character_stats.atk_percent,
            base_hp=character_stats.base_hp,
            flat_hp=character_stats.flat_hp,
            hp_percent=character_stats.hp_percent,
            base_def=character_stats.base_def,
            flat_def=character_stats.flat_def,
            def_percent=character_stats.def_percent,
            crit_rate=character_stats.crit_rate,
            crit_dmg=character_stats.crit_dmg,
            elemental_mastery=character_stats.elemental_mastery,
            elemental_dmg_bonus=character_stats.elemental_dmg_bonus,
            physical_dmg_bonus=character_stats.physical_dmg_bonus,
            energy_recharge=character_stats.energy_recharge,
            healing_bonus=character_stats.healing_bonus,
            additive_base_dmg=character_stats.additive_base_dmg
        )
        
        # Apply team buffs based on team composition
        team_buffs = self.calculate_team_buffs(team_composition, main_dps_name)
        
        # Apply buffs to stats
        buffed_stats.flat_atk += team_buffs.get("flat_atk", 0)
        buffed_stats.atk_percent += team_buffs.get("atk_percent", 0)
        buffed_stats.elemental_dmg_bonus += team_buffs.get("elemental_dmg_bonus", 0)
        buffed_stats.elemental_mastery += team_buffs.get("elemental_mastery", 0)
        buffed_stats.crit_rate += team_buffs.get("crit_rate", 0)
        
        # Apply resistance reductions to enemy
        buffed_enemy = EnemyStats(
            level=enemy_stats.level,
            elemental_res=enemy_stats.elemental_res.copy(),
            physical_res=enemy_stats.physical_res,
            def_reduction=enemy_stats.def_reduction,
            res_reduction=enemy_stats.res_reduction.copy()
        )
        
        # Apply VV shred and other resistance reductions
        for element in buffed_enemy.res_reduction:
            buffed_enemy.res_reduction[element] += team_buffs.get("res_reduction", 0)
        
        # Calculate buffed damage
        buffed_damage = self.calculate_character_damage(
            main_dps_name, buffed_stats, buffed_enemy, reactions
        )
        
        return {
            "main_dps": main_dps_name,
            "team_composition": team_composition,
            "base_damage": base_damage,
            "team_buffs": team_buffs,
            "buffed_damage": buffed_damage,
            "damage_increase": self.calculate_damage_increase(base_damage, buffed_damage)
        }
    
    def calculate_team_buffs(self, team_composition: List[str], main_dps: str) -> Dict[str, float]:
        """Calculate team buffs based on composition."""
        buffs = {
            "flat_atk": 0,
            "atk_percent": 0,
            "elemental_dmg_bonus": 0,
            "elemental_mastery": 0,
            "crit_rate": 0,
            "res_reduction": 0
        }
        
        # Simplified team buff calculations
        for character in team_composition:
            character_lower = character.lower()
            
            # Bennett buffs
            if character_lower == "bennett":
                buffs["flat_atk"] += 1200  # Approximate Bennett buff
            
            # Kazuha buffs
            elif character_lower == "kazuha":
                buffs["elemental_dmg_bonus"] += 40  # VV + EM sharing
                buffs["res_reduction"] += 40  # VV shred
            
            # Sucrose buffs
            elif character_lower == "sucrose":
                buffs["elemental_mastery"] += 200  # EM sharing
                buffs["res_reduction"] += 40  # VV shred
            
            # Zhongli buffs
            elif character_lower == "zhongli":
                buffs["res_reduction"] += 20  # Universal shred
        
        # Elemental resonance buffs
        elements = [self.get_character_element(char) for char in team_composition]
        element_counts = {element: elements.count(element) for element in set(elements)}
        
        # Pyro resonance
        if element_counts.get("pyro", 0) >= 2:
            buffs["atk_percent"] += 25
        
        # Cryo resonance
        if element_counts.get("cryo", 0) >= 2:
            buffs["crit_rate"] += 15
        
        # Dendro resonance
        if element_counts.get("dendro", 0) >= 2:
            buffs["elemental_mastery"] += 50
        
        return buffs
    
    def calculate_damage_increase(self, base_damage: Dict, buffed_damage: Dict) -> Dict[str, Dict[str, float]]:
        """Calculate damage increase percentage."""
        increase = {}
        
        for ability in base_damage["damage_breakdown"]:
            if ability in buffed_damage["damage_breakdown"]:
                base_avg = base_damage["damage_breakdown"][ability]["average"]
                buffed_avg = buffed_damage["damage_breakdown"][ability]["average"]
                
                increase[ability] = {
                    "base_average": base_avg,
                    "buffed_average": buffed_avg,
                    "increase_percent": ((buffed_avg - base_avg) / base_avg * 100) if base_avg > 0 else 0
                }
        
        return increase

    def analyze_team_reactions(self, team_composition: List[str], main_dps: str) -> Dict[str, Any]:
        """
        Automatically analyze possible elemental reactions based on team composition.
        
        Args:
            team_composition: List of character names in the team
            main_dps: Main DPS character name
            
        Returns:
            Dictionary containing reaction analysis and recommendations
        """
        # Get elements for each character
        team_elements = {}
        for character in team_composition:
            element = self.get_character_element(character)
            team_elements[character] = element
        
        main_dps_element = team_elements.get(main_dps, "unknown")
        
        # Define reaction combinations
        reaction_combinations = {
            # Amplifying reactions (multiplicative)
            "vaporize": [
                {"trigger": "pyro", "aura": "hydro", "multiplier": 1.5},
                {"trigger": "hydro", "aura": "pyro", "multiplier": 2.0}
            ],
            "melt": [
                {"trigger": "pyro", "aura": "cryo", "multiplier": 2.0},
                {"trigger": "cryo", "aura": "pyro", "multiplier": 1.5}
            ],
            # Transformative reactions (additive)
            "overloaded": [
                {"trigger": "pyro", "aura": "electro"},
                {"trigger": "electro", "aura": "pyro"}
            ],
            "electrocharged": [
                {"trigger": "hydro", "aura": "electro"},
                {"trigger": "electro", "aura": "hydro"}
            ],
            "superconduct": [
                {"trigger": "cryo", "aura": "electro"},
                {"trigger": "electro", "aura": "cryo"}
            ],
            "frozen": [
                {"trigger": "cryo", "aura": "hydro"},
                {"trigger": "hydro", "aura": "cryo"}
            ],
            # Swirl reactions
            "swirl": [
                {"trigger": "anemo", "aura": "pyro"},
                {"trigger": "anemo", "aura": "hydro"},
                {"trigger": "anemo", "aura": "electro"},
                {"trigger": "anemo", "aura": "cryo"}
            ],
            # Crystallize reactions
            "crystallize": [
                {"trigger": "geo", "aura": "pyro"},
                {"trigger": "geo", "aura": "hydro"},
                {"trigger": "geo", "aura": "electro"},
                {"trigger": "geo", "aura": "cryo"}
            ],
            # Dendro reactions
            "bloom": [
                {"trigger": "hydro", "aura": "dendro"}
            ],
            "burning": [
                {"trigger": "pyro", "aura": "dendro"}
            ],
            "quicken": [
                {"trigger": "electro", "aura": "dendro"}
            ],
            "spread": [
                {"trigger": "dendro", "aura": "electro"}
            ],
            "hyperbloom": [
                {"trigger": "electro", "aura": "bloom_seed"}
            ],
            "burgeon": [
                {"trigger": "pyro", "aura": "bloom_seed"}
            ]
        }
        
        # Analyze possible reactions
        possible_reactions = []
        reaction_priority = {}
        
        # Get unique elements in team
        unique_elements = list(set(team_elements.values()))
        unique_elements = [elem for elem in unique_elements if elem != "unknown"]
        
        # Check each reaction type
        for reaction_name, combinations in reaction_combinations.items():
            for combo in combinations:
                trigger_elem = combo["trigger"]
                aura_elem = combo["aura"]
                
                # Check if both elements are present in team
                trigger_chars = [char for char, elem in team_elements.items() if elem == trigger_elem]
                aura_chars = [char for char, elem in team_elements.items() if elem == aura_elem]
                
                if trigger_chars and aura_chars:
                    # Determine reaction viability
                    viability_score = 0
                    
                    # Higher score if main DPS can trigger the reaction
                    if main_dps in trigger_chars:
                        viability_score += 50
                    elif main_dps in aura_chars:
                        viability_score += 30
                    else:
                        viability_score += 10
                    
                    # Higher score for amplifying reactions
                    if reaction_name in ["vaporize", "melt"]:
                        viability_score += 30
                        multiplier = combo.get("multiplier", 1.0)
                    else:
                        viability_score += 10
                        multiplier = 1.0
                    
                    # Higher score for more reliable element application
                    reliable_applicators = {
                        "hydro": ["xingqiu", "yelan", "kokomi", "mona"],
                        "pyro": ["xiangling", "bennett", "thoma"],
                        "electro": ["fischl", "beidou", "raiden shogun"],
                        "cryo": ["diona", "rosaria", "kaeya"],
                        "anemo": ["kazuha", "sucrose", "venti"],
                        "dendro": ["nahida", "collei", "dendro mc"]
                    }
                    
                    # Check for reliable applicators
                    reliable_aura = any(char.lower() in reliable_applicators.get(aura_elem, []) 
                                      for char in aura_chars)
                    reliable_trigger = any(char.lower() in reliable_applicators.get(trigger_elem, []) 
                                         for char in trigger_chars)
                    
                    if reliable_aura:
                        viability_score += 20
                    if reliable_trigger:
                        viability_score += 15
                    
                    reaction_info = {
                        "reaction": reaction_name,
                        "trigger_element": trigger_elem,
                        "aura_element": aura_elem,
                        "trigger_characters": trigger_chars,
                        "aura_characters": aura_chars,
                        "viability_score": viability_score,
                        "multiplier": multiplier,
                        "type": "amplifying" if reaction_name in ["vaporize", "melt"] else "transformative",
                        "description": self._get_reaction_description(reaction_name, trigger_elem, aura_elem)
                    }
                    
                    possible_reactions.append(reaction_info)
                    
                    # Track highest priority for each reaction type
                    if reaction_name not in reaction_priority or viability_score > reaction_priority[reaction_name]["viability_score"]:
                        reaction_priority[reaction_name] = reaction_info
        
        # Sort reactions by viability score
        possible_reactions.sort(key=lambda x: x["viability_score"], reverse=True)
        
        # Get top recommended reactions
        recommended_reactions = []
        seen_reactions = set()
        
        for reaction in possible_reactions:
            if reaction["reaction"] not in seen_reactions and len(recommended_reactions) < 3:
                recommended_reactions.append(reaction["reaction"])
                seen_reactions.add(reaction["reaction"])
        
        # Analyze team synergy for reactions
        team_synergy = self._analyze_reaction_synergy(team_elements, main_dps_element)
        
        return {
            "team_composition": team_composition,
            "main_dps": main_dps,
            "main_dps_element": main_dps_element,
            "team_elements": team_elements,
            "possible_reactions": possible_reactions,
            "recommended_reactions": recommended_reactions,
            "reaction_priority": reaction_priority,
            "team_synergy": team_synergy,
            "elemental_coverage": {
                "elements_present": unique_elements,
                "element_count": len(unique_elements),
                "reaction_potential": len(possible_reactions) > 0,
                "amplifying_reactions": len([r for r in possible_reactions if r["type"] == "amplifying"]),
                "transformative_reactions": len([r for r in possible_reactions if r["type"] == "transformative"])
            }
        }
    
    def _get_reaction_description(self, reaction_name: str, trigger_elem: str, aura_elem: str) -> str:
        """Get description for a reaction."""
        descriptions = {
            "vaporize": f"{trigger_elem.title()} triggers Vaporize on {aura_elem.title()} aura",
            "melt": f"{trigger_elem.title()} triggers Melt on {aura_elem.title()} aura",
            "overloaded": f"{trigger_elem.title()} + {aura_elem.title()} creates Overloaded explosion",
            "electrocharged": f"{trigger_elem.title()} + {aura_elem.title()} creates Electrocharged DoT",
            "superconduct": f"{trigger_elem.title()} + {aura_elem.title()} creates Superconduct (reduces Physical RES)",
            "frozen": f"{trigger_elem.title()} + {aura_elem.title()} freezes enemies",
            "swirl": f"Anemo swirls {aura_elem.title()} element",
            "crystallize": f"Geo crystallizes {aura_elem.title()} for shields",
            "bloom": f"Hydro + Dendro creates Dendro Cores",
            "burning": f"Pyro + Dendro creates Burning DoT",
            "quicken": f"Electro + Dendro creates Quicken state",
            "spread": f"Dendro triggers Spread on Quicken",
            "hyperbloom": f"Electro triggers Hyperbloom on Dendro Cores",
            "burgeon": f"Pyro triggers Burgeon on Dendro Cores"
        }
        return descriptions.get(reaction_name, f"{reaction_name.title()} reaction")
    
    def _analyze_reaction_synergy(self, team_elements: Dict[str, str], main_dps_element: str) -> Dict[str, Any]:
        """Analyze team synergy for elemental reactions."""
        synergy_score = 0
        synergy_notes = []
        
        elements = list(team_elements.values())
        unique_elements = list(set(elements))
        
        # Element diversity bonus
        if len(unique_elements) >= 3:
            synergy_score += 20
            synergy_notes.append("Good elemental diversity for multiple reaction options")
        elif len(unique_elements) == 2:
            synergy_score += 15
            synergy_notes.append("Focused dual-element synergy")
        
        # Check for optimal reaction setups
        if "pyro" in elements and "hydro" in elements:
            synergy_score += 25
            synergy_notes.append("Vaporize reaction potential (high damage multiplier)")
        
        if "pyro" in elements and "cryo" in elements:
            synergy_score += 25
            synergy_notes.append("Melt reaction potential (high damage multiplier)")
        
        if "anemo" in elements and len(unique_elements) >= 2:
            synergy_score += 20
            synergy_notes.append("Anemo support for Swirl reactions and VV shred")
        
        if "dendro" in elements:
            dendro_synergies = 0
            if "hydro" in elements:
                dendro_synergies += 1
                synergy_notes.append("Bloom reaction potential")
            if "electro" in elements:
                dendro_synergies += 1
                synergy_notes.append("Quicken/Spread reaction potential")
            if "pyro" in elements:
                dendro_synergies += 1
                synergy_notes.append("Burning reaction potential")
            
            synergy_score += dendro_synergies * 10
        
        # Elemental resonance bonus
        element_counts = {elem: elements.count(elem) for elem in set(elements)}
        for element, count in element_counts.items():
            if count >= 2:
                synergy_score += 10
                synergy_notes.append(f"{element.title()} resonance active")
        
        return {
            "synergy_score": min(100, synergy_score),
            "synergy_notes": synergy_notes,
            "element_diversity": len(unique_elements),
            "resonance_active": any(count >= 2 for count in element_counts.values())
        }

# Global calculator instance
damage_calculator = SimpleDamageCalculator() 