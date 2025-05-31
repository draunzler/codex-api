"""
Team Buff Calculator for Genshin Impact

This module calculates team buffs and synergies for team compositions,
inspired by the team analysis features of Akasha.cv and GI Damage Calculator.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TeamBuff:
    """Represents a team buff."""
    source: str  # Character providing the buff
    buff_type: str  # Type of buff (atk_percent, elemental_dmg, etc.)
    value: float  # Buff value
    duration: float  # Buff duration in seconds
    conditions: List[str]  # Conditions to activate buff
    uptime: float = 100.0  # Uptime percentage

@dataclass
class TeamComposition:
    """Represents a team composition."""
    main_dps: str
    sub_dps: Optional[str] = None
    support1: Optional[str] = None
    support2: Optional[str] = None
    
    @property
    def all_characters(self) -> List[str]:
        """Get all characters in the team."""
        chars = [self.main_dps]
        for char in [self.sub_dps, self.support1, self.support2]:
            if char:
                chars.append(char)
        return chars

class TeamBuffCalculator:
    """Calculate team buffs and synergies."""
    
    # Character elements
    CHARACTER_ELEMENTS = {
        "hu tao": "pyro", "diluc": "pyro", "yoimiya": "pyro", "arlecchino": "pyro", "lyney": "pyro",
        "bennett": "pyro", "xiangling": "pyro", "amber": "pyro", "thoma": "pyro", "xinyan": "pyro",
        
        "childe": "hydro", "ayato": "hydro", "neuvillette": "hydro", "furina": "hydro",
        "xingqiu": "hydro", "mona": "hydro", "kokomi": "hydro", "barbara": "hydro", "candace": "hydro",
        
        "raiden shogun": "electro", "keqing": "electro", "yae miko": "electro", "fischl": "electro",
        "beidou": "electro", "razor": "electro", "lisa": "electro", "kuki shinobu": "electro",
        
        "ganyu": "cryo", "ayaka": "cryo", "eula": "cryo", "wriothesley": "cryo", "diona": "cryo",
        "chongyun": "cryo", "rosaria": "cryo", "kaeya": "cryo", "qiqi": "cryo", "shenhe": "cryo",
        
        "xiao": "anemo", "wanderer": "anemo", "kazuha": "anemo", "venti": "anemo", "sucrose": "anemo",
        "jean": "anemo", "sayu": "anemo", "heizou": "anemo", "faruzan": "anemo",
        
        "itto": "geo", "albedo": "geo", "zhongli": "geo", "navia": "geo", "noelle": "geo",
        "ningguang": "geo", "gorou": "geo", "yun jin": "geo", "chiori": "geo",
        
        "tighnari": "dendro", "nahida": "dendro", "alhaitham": "dendro", "baizhu": "dendro",
        "collei": "dendro", "yaoyao": "dendro", "kaveh": "dendro", "kirara": "dendro"
    }
    
    # Character-specific buffs
    CHARACTER_BUFFS = {
        # Pyro supports
        "bennett": [
            TeamBuff("Bennett", "atk_flat", 1200, 12, ["burst_active"], 80),
            TeamBuff("Bennett", "pyro_dmg_bonus", 15, 12, ["c6_active"], 80)
        ],
        "xiangling": [
            TeamBuff("Xiangling", "pyro_dmg_bonus", 15, 8, ["c1_active"], 60)
        ],
        
        # Hydro supports
        "xingqiu": [
            TeamBuff("Xingqiu", "hydro_res_reduction", 15, 15, ["burst_active"], 90),
            TeamBuff("Xingqiu", "damage_reduction", 20, 15, ["c2_active"], 90)
        ],
        "mona": [
            TeamBuff("Mona", "damage_bonus", 60, 5, ["burst_active"], 30)
        ],
        "kokomi": [
            TeamBuff("Kokomi", "healing", 100, 12, ["burst_active"], 70)
        ],
        
        # Electro supports
        "fischl": [
            TeamBuff("Fischl", "electro_dmg_bonus", 20, 10, ["oz_active"], 80)
        ],
        "raiden shogun": [
            TeamBuff("Raiden Shogun", "burst_dmg_bonus", 27, 7, ["burst_active"], 40),
            TeamBuff("Raiden Shogun", "energy_recharge", 30, 25, ["skill_active"], 95)
        ],
        
        # Cryo supports
        "diona": [
            TeamBuff("Diona", "shield_strength", 75, 12, ["shield_active"], 85),
            TeamBuff("Diona", "movement_speed", 10, 12, ["c2_active"], 85)
        ],
        "shenhe": [
            TeamBuff("Shenhe", "cryo_dmg_bonus", 15, 10, ["skill_active"], 70),
            TeamBuff("Shenhe", "cryo_res_reduction", 15, 6, ["burst_active"], 40)
        ],
        
        # Anemo supports
        "kazuha": [
            TeamBuff("Kazuha", "elemental_dmg_bonus", 40, 8, ["swirl_active"], 80),
            TeamBuff("Kazuha", "elemental_res_reduction", 40, 8, ["vv_active"], 80)
        ],
        "venti": [
            TeamBuff("Venti", "energy_recharge", 15, 6, ["burst_active"], 50),
            TeamBuff("Venti", "elemental_res_reduction", 40, 8, ["vv_active"], 80)
        ],
        "sucrose": [
            TeamBuff("Sucrose", "elemental_mastery", 200, 8, ["skill_burst_active"], 70),
            TeamBuff("Sucrose", "elemental_res_reduction", 40, 8, ["vv_active"], 80)
        ],
        
        # Geo supports
        "zhongli": [
            TeamBuff("Zhongli", "shield_strength", 100, 20, ["shield_active"], 95),
            TeamBuff("Zhongli", "all_res_reduction", 20, 20, ["shield_active"], 95)
        ],
        "albedo": [
            TeamBuff("Albedo", "elemental_mastery", 125, 10, ["burst_active"], 60)
        ],
        "gorou": [
            TeamBuff("Gorou", "geo_dmg_bonus", 25, 12, ["skill_active"], 80),
            TeamBuff("Gorou", "def_bonus", 438, 12, ["skill_active"], 80)
        ],
        
        # Dendro supports
        "nahida": [
            TeamBuff("Nahida", "elemental_mastery", 250, 15, ["skill_active"], 90),
            TeamBuff("Nahida", "dendro_res_reduction", 30, 8, ["burst_active"], 60)
        ],
        "baizhu": [
            TeamBuff("Baizhu", "shield_strength", 50, 14, ["skill_active"], 75),
            TeamBuff("Baizhu", "dendro_dmg_bonus", 25, 14, ["c2_active"], 75)
        ]
    }
    
    # Elemental resonances
    ELEMENTAL_RESONANCES = {
        "pyro": TeamBuff("Pyro Resonance", "atk_percent", 25, 0, ["2_pyro_characters"], 100),
        "hydro": TeamBuff("Hydro Resonance", "hp_percent", 25, 0, ["2_hydro_characters"], 100),
        "electro": TeamBuff("Electro Resonance", "energy_recharge", 100, 0, ["2_electro_characters"], 100),
        "cryo": TeamBuff("Cryo Resonance", "crit_rate", 15, 0, ["2_cryo_characters"], 100),
        "anemo": TeamBuff("Anemo Resonance", "movement_speed", 10, 0, ["2_anemo_characters"], 100),
        "geo": TeamBuff("Geo Resonance", "shield_strength", 15, 0, ["2_geo_characters"], 100),
        "dendro": TeamBuff("Dendro Resonance", "elemental_mastery", 50, 0, ["2_dendro_characters"], 100)
    }
    
    def __init__(self):
        """Initialize the team buff calculator."""
        pass
    
    def get_character_element(self, character_name: str) -> str:
        """Get character element."""
        return self.CHARACTER_ELEMENTS.get(character_name.lower(), "unknown")
    
    def get_character_buffs(self, character_name: str) -> List[TeamBuff]:
        """Get buffs provided by a character."""
        return self.CHARACTER_BUFFS.get(character_name.lower(), [])
    
    def calculate_elemental_resonance(self, team: TeamComposition) -> List[TeamBuff]:
        """Calculate elemental resonance buffs."""
        elements = [self.get_character_element(char) for char in team.all_characters]
        element_counts = {}
        
        for element in elements:
            if element != "unknown":
                element_counts[element] = element_counts.get(element, 0) + 1
        
        resonance_buffs = []
        for element, count in element_counts.items():
            if count >= 2 and element in self.ELEMENTAL_RESONANCES:
                resonance_buffs.append(self.ELEMENTAL_RESONANCES[element])
        
        return resonance_buffs
    
    def calculate_team_buffs(self, team: TeamComposition, main_dps_element: str = None) -> Dict[str, Any]:
        """Calculate all team buffs for a composition."""
        if not main_dps_element:
            main_dps_element = self.get_character_element(team.main_dps)
        
        all_buffs = []
        
        # Get buffs from each team member
        for character in team.all_characters:
            if character != team.main_dps:  # Don't include main DPS's own buffs
                character_buffs = self.get_character_buffs(character)
                all_buffs.extend(character_buffs)
        
        # Add elemental resonance
        resonance_buffs = self.calculate_elemental_resonance(team)
        all_buffs.extend(resonance_buffs)
        
        # Categorize buffs
        categorized_buffs = {
            "attack_buffs": [],
            "damage_buffs": [],
            "defensive_buffs": [],
            "utility_buffs": [],
            "elemental_buffs": []
        }
        
        total_multipliers = {
            "atk_percent": 0,
            "atk_flat": 0,
            "elemental_dmg_bonus": 0,
            "crit_rate": 0,
            "crit_dmg": 0,
            "elemental_mastery": 0,
            "damage_bonus": 0
        }
        
        for buff in all_buffs:
            # Categorize buff
            if buff.buff_type in ["atk_percent", "atk_flat"]:
                categorized_buffs["attack_buffs"].append(buff)
                total_multipliers[buff.buff_type] += buff.value * (buff.uptime / 100)
            elif buff.buff_type in ["elemental_dmg_bonus", "damage_bonus", "burst_dmg_bonus"]:
                categorized_buffs["damage_buffs"].append(buff)
                if buff.buff_type == "elemental_dmg_bonus":
                    total_multipliers["elemental_dmg_bonus"] += buff.value * (buff.uptime / 100)
                else:
                    total_multipliers["damage_bonus"] += buff.value * (buff.uptime / 100)
            elif buff.buff_type in ["shield_strength", "damage_reduction", "healing"]:
                categorized_buffs["defensive_buffs"].append(buff)
            elif buff.buff_type in ["movement_speed", "energy_recharge"]:
                categorized_buffs["utility_buffs"].append(buff)
            elif buff.buff_type in ["elemental_mastery", "crit_rate", "crit_dmg"]:
                categorized_buffs["elemental_buffs"].append(buff)
                if buff.buff_type in total_multipliers:
                    total_multipliers[buff.buff_type] += buff.value * (buff.uptime / 100)
        
        # Calculate team synergy score
        synergy_score = self.calculate_synergy_score(team, all_buffs)
        
        return {
            "team_composition": team.all_characters,
            "main_dps": team.main_dps,
            "main_dps_element": main_dps_element,
            "total_buffs": len(all_buffs),
            "categorized_buffs": categorized_buffs,
            "total_multipliers": total_multipliers,
            "synergy_score": synergy_score,
            "elemental_coverage": self.analyze_elemental_coverage(team),
            "recommended_rotation": self.generate_rotation_guide(team)
        }
    
    def calculate_synergy_score(self, team: TeamComposition, buffs: List[TeamBuff]) -> float:
        """Calculate team synergy score (0-100)."""
        base_score = 50.0
        
        # Element diversity bonus
        elements = set(self.get_character_element(char) for char in team.all_characters)
        if len(elements) == 4:
            base_score += 15  # Rainbow team
        elif len(elements) == 2:
            base_score += 10  # Dual element synergy
        
        # Buff quantity and quality
        buff_score = min(len(buffs) * 3, 25)  # Max 25 points from buffs
        base_score += buff_score
        
        # Role coverage (simplified)
        roles_covered = 0
        if any("atk" in buff.buff_type for buff in buffs):
            roles_covered += 1  # ATK buffer
        if any("shield" in buff.buff_type or "healing" in buff.buff_type for buff in buffs):
            roles_covered += 1  # Defensive support
        if any("elemental" in buff.buff_type for buff in buffs):
            roles_covered += 1  # Elemental support
        
        base_score += roles_covered * 3
        
        return min(100.0, base_score)
    
    def analyze_elemental_coverage(self, team: TeamComposition) -> Dict[str, Any]:
        """Analyze elemental coverage of the team."""
        elements = [self.get_character_element(char) for char in team.all_characters]
        unique_elements = set(elements)
        
        coverage = {
            "elements_present": list(unique_elements),
            "element_count": len(unique_elements),
            "has_anemo": "anemo" in unique_elements,
            "has_geo": "geo" in unique_elements,
            "reaction_potential": len(unique_elements) >= 2,
            "shield_breaking": any(elem in unique_elements for elem in ["pyro", "electro", "geo"]),
            "crowd_control": any(elem in unique_elements for elem in ["anemo", "cryo", "hydro"])
        }
        
        return coverage
    
    def generate_rotation_guide(self, team: TeamComposition) -> List[str]:
        """Generate a basic rotation guide for the team."""
        rotation = []
        
        # Basic rotation logic
        for character in team.all_characters:
            element = self.get_character_element(character)
            
            if character == team.main_dps:
                rotation.append(f"{character}: Main DPS rotation (Skill → Burst → Normal Attacks)")
            elif element == "anemo":
                rotation.insert(0, f"{character}: Use Skill for VV shred")
            elif character.lower() == "bennett":
                rotation.insert(-1 if rotation else 0, f"{character}: Use Burst for ATK buff")
            elif element in ["hydro", "electro", "cryo"]:
                rotation.insert(-1 if rotation else 0, f"{character}: Apply element for reactions")
            else:
                rotation.append(f"{character}: Use Skill/Burst for support")
        
        return rotation

# Global team buff calculator instance
team_buff_calculator = TeamBuffCalculator() 