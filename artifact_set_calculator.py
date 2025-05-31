"""
Artifact Set Bonus Calculator

This module calculates artifact set bonuses (2-piece and 4-piece effects) 
based on equipped artifacts and applies them to character stats.

Based on: https://genshin-impact.fandom.com/wiki/Artifact/Sets
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ArtifactSetBonus:
    """Represents an artifact set bonus effect."""
    set_name: str
    pieces_required: int  # 2 or 4
    bonus_type: str  # "stat", "conditional", "special"
    stat_bonuses: Dict[str, float]  # Direct stat bonuses
    conditional_effects: Dict[str, Any]  # Conditional effects
    description: str

class ArtifactSetCalculator:
    """Calculate artifact set bonuses and apply them to character stats."""
    
    # Comprehensive artifact set bonuses database
    ARTIFACT_SET_BONUSES = {
        # Gladiator's Finale
        "gladiator's finale": [
            ArtifactSetBonus(
                "Gladiator's Finale", 2, "stat",
                {"atk_percent": 18.0}, {},
                "ATK +18%"
            ),
            ArtifactSetBonus(
                "Gladiator's Finale", 4, "conditional",
                {}, {"normal_attack_dmg": 35.0, "weapon_types": ["sword", "claymore", "polearm"]},
                "If the wielder uses a Sword, Claymore or Polearm, increases Normal Attack DMG by 35%"
            )
        ],
        
        # Wanderer's Troupe
        "wanderer's troupe": [
            ArtifactSetBonus(
                "Wanderer's Troupe", 2, "stat",
                {"elemental_mastery": 80}, {},
                "Elemental Mastery +80"
            ),
            ArtifactSetBonus(
                "Wanderer's Troupe", 4, "conditional",
                {}, {"charged_attack_dmg": 35.0, "weapon_types": ["catalyst", "bow"]},
                "If the wielder uses a Catalyst or Bow, increases Charged Attack DMG by 35%"
            )
        ],
        
        # Crimson Witch of Flames
        "crimson witch of flames": [
            ArtifactSetBonus(
                "Crimson Witch of Flames", 2, "stat",
                {"pyro_dmg_bonus": 15.0}, {},
                "Pyro DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Crimson Witch of Flames", 4, "conditional",
                {}, {
                    "overloaded_vaporize_melt_dmg": 40.0,
                    "pyro_dmg_bonus_stacks": {"max_stacks": 3, "per_stack": 7.5, "duration": 10}
                },
                "Increases Overloaded, Burning, and Burgeon DMG by 40%. Increases Vaporize and Melt DMG by 15%. Using Elemental Skill increases the 2-Piece Set Bonus by 50% of its starting value for 10s. Max 3 stacks."
            )
        ],
        
        # Viridescent Venerer
        "viridescent venerer": [
            ArtifactSetBonus(
                "Viridescent Venerer", 2, "stat",
                {"anemo_dmg_bonus": 15.0}, {},
                "Anemo DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Viridescent Venerer", 4, "conditional",
                {}, {
                    "swirl_dmg": 60.0,
                    "elemental_res_shred": {"value": 40.0, "duration": 10, "elements": ["pyro", "hydro", "electro", "cryo"]}
                },
                "Increases Swirl DMG by 60%. Decreases opponent's Elemental RES to the element infused in the Swirl by 40% for 10s."
            )
        ],
        
        # Noblesse Oblige
        "noblesse oblige": [
            ArtifactSetBonus(
                "Noblesse Oblige", 2, "stat",
                {"elemental_burst_dmg": 20.0}, {},
                "Elemental Burst DMG +20%"
            ),
            ArtifactSetBonus(
                "Noblesse Oblige", 4, "conditional",
                {}, {"team_atk_buff": {"value": 20.0, "duration": 12}},
                "Using an Elemental Burst increases all party members' ATK by 20% for 12s. This effect cannot stack."
            )
        ],
        
        # Bloodstained Chivalry
        "bloodstained chivalry": [
            ArtifactSetBonus(
                "Bloodstained Chivalry", 2, "stat",
                {"physical_dmg_bonus": 25.0}, {},
                "Physical DMG +25%"
            ),
            ArtifactSetBonus(
                "Bloodstained Chivalry", 4, "conditional",
                {}, {"charged_attack_stamina": {"reduction": 100.0, "duration": 10}},
                "After defeating an opponent, increases Charged Attack DMG by 50%, and reduces its Stamina cost to 0 for 10s."
            )
        ],
        
        # Maiden Beloved
        "maiden beloved": [
            ArtifactSetBonus(
                "Maiden Beloved", 2, "stat",
                {"healing_bonus": 15.0}, {},
                "Character Healing Effectiveness +15%"
            ),
            ArtifactSetBonus(
                "Maiden Beloved", 4, "conditional",
                {}, {"team_healing_bonus": {"value": 20.0, "duration": 10}},
                "Using an Elemental Skill or Burst increases healing received by all party members by 20% for 10s."
            )
        ],
        
        # Archaic Petra
        "archaic petra": [
            ArtifactSetBonus(
                "Archaic Petra", 2, "stat",
                {"geo_dmg_bonus": 15.0}, {},
                "Geo DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Archaic Petra", 4, "conditional",
                {}, {"crystallize_shield_bonus": 150.0, "elemental_dmg_bonus": 35.0},
                "Upon obtaining an Elemental Shard created through a Crystallize Reaction, all party members gain 35% DMG Bonus for that particular element for 10s."
            )
        ],
        
        # Retracing Bolide
        "retracing bolide": [
            ArtifactSetBonus(
                "Retracing Bolide", 2, "stat",
                {"shield_strength": 35.0}, {},
                "Shield Strength +35%"
            ),
            ArtifactSetBonus(
                "Retracing Bolide", 4, "conditional",
                {}, {"normal_charged_attack_dmg": 40.0, "requires_shield": True},
                "While protected by a shield, gain an additional 40% Normal and Charged Attack DMG."
            )
        ],
        
        # Thundersoother
        "thundersoother": [
            ArtifactSetBonus(
                "Thundersoother", 2, "stat",
                {"electro_res": 40.0}, {},
                "Electro RES increased by 40%"
            ),
            ArtifactSetBonus(
                "Thundersoother", 4, "conditional",
                {}, {"electro_affected_dmg": 35.0},
                "Increases DMG against opponents affected by Electro by 35%."
            )
        ],
        
        # Lavawalker
        "lavawalker": [
            ArtifactSetBonus(
                "Lavawalker", 2, "stat",
                {"pyro_res": 40.0}, {},
                "Pyro RES increased by 40%"
            ),
            ArtifactSetBonus(
                "Lavawalker", 4, "conditional",
                {}, {"pyro_affected_dmg": 35.0},
                "Increases DMG against opponents affected by Pyro by 35%."
            )
        ],
        
        # Heart of Depth
        "heart of depth": [
            ArtifactSetBonus(
                "Heart of Depth", 2, "stat",
                {"hydro_dmg_bonus": 15.0}, {},
                "Hydro DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Heart of Depth", 4, "conditional",
                {}, {
                    "normal_charged_attack_dmg": 30.0,
                    "trigger": "elemental_skill",
                    "duration": 15
                },
                "After using Elemental Skill, increases Normal Attack and Charged Attack DMG by 30% for 15s."
            )
        ],
        
        # Blizzard Strayer
        "blizzard strayer": [
            ArtifactSetBonus(
                "Blizzard Strayer", 2, "stat",
                {"cryo_dmg_bonus": 15.0}, {},
                "Cryo DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Blizzard Strayer", 4, "conditional",
                {}, {
                    "crit_rate_frozen": 20.0,
                    "crit_rate_cryo_affected": 20.0,
                    "additional_crit_rate": 20.0
                },
                "When a character attacks an opponent affected by Cryo, their CRIT Rate is increased by 20%. If the opponent is Frozen, CRIT Rate is increased by an additional 20%."
            )
        ],
        
        # Tenacity of the Millelith
        "tenacity of the millelith": [
            ArtifactSetBonus(
                "Tenacity of the Millelith", 2, "stat",
                {"hp_percent": 20.0}, {},
                "HP +20%"
            ),
            ArtifactSetBonus(
                "Tenacity of the Millelith", 4, "conditional",
                {}, {
                    "team_atk_buff": {"value": 20.0, "duration": 3},
                    "team_shield_strength": {"value": 30.0, "duration": 3},
                    "trigger": "elemental_skill_hit"
                },
                "When an Elemental Skill hits an opponent, the ATK of all nearby party members is increased by 20% and their Shield Strength is increased by 30% for 3s."
            )
        ],
        
        # Pale Flame
        "pale flame": [
            ArtifactSetBonus(
                "Pale Flame", 2, "stat",
                {"physical_dmg_bonus": 25.0}, {},
                "Physical DMG +25%"
            ),
            ArtifactSetBonus(
                "Pale Flame", 4, "conditional",
                {}, {
                    "atk_percent_stacks": {"max_stacks": 2, "per_stack": 9.0, "duration": 7},
                    "physical_dmg_bonus_full": 25.0,
                    "trigger": "elemental_skill_hit"
                },
                "When an Elemental Skill hits an opponent, ATK is increased by 9% for 7s. Max 2 stacks. When you have 2 stacks, the 2-set effect is increased by 100%."
            )
        ],
        
        # Shimenawa's Reminiscence
        "shimenawa's reminiscence": [
            ArtifactSetBonus(
                "Shimenawa's Reminiscence", 2, "stat",
                {"atk_percent": 18.0}, {},
                "ATK +18%"
            ),
            ArtifactSetBonus(
                "Shimenawa's Reminiscence", 4, "conditional",
                {}, {
                    "normal_charged_plunge_dmg": 50.0,
                    "energy_cost": 15,
                    "duration": 10,
                    "trigger": "cast_elemental_burst"
                },
                "When casting an Elemental Burst, if the character has 15 or more Energy, they lose 15 Energy and Normal/Charged/Plunging Attack DMG is increased by 50% for 10s."
            )
        ],
        
        # Emblem of Severed Fate
        "emblem of severed fate": [
            ArtifactSetBonus(
                "Emblem of Severed Fate", 2, "stat",
                {"energy_recharge": 20.0}, {},
                "Energy Recharge +20%"
            ),
            ArtifactSetBonus(
                "Emblem of Severed Fate", 4, "conditional",
                {}, {
                    "elemental_burst_dmg_from_er": {"conversion_rate": 0.25, "max_bonus": 75.0}
                },
                "Increases Elemental Burst DMG by 25% of Energy Recharge. A maximum of 75% bonus DMG can be obtained in this way."
            )
        ],
        
        # Husk of Opulent Dreams
        "husk of opulent dreams": [
            ArtifactSetBonus(
                "Husk of Opulent Dreams", 2, "stat",
                {"def_percent": 30.0}, {},
                "DEF +30%"
            ),
            ArtifactSetBonus(
                "Husk of Opulent Dreams", 4, "conditional",
                {}, {
                    "def_geo_dmg_stacks": {
                        "max_stacks": 4,
                        "def_per_stack": 6.0,
                        "geo_dmg_per_stack": 6.0,
                        "duration": 12,
                        "trigger": "geo_damage_or_off_field"
                    }
                },
                "A character equipped with this Artifact set will obtain the Curiosity effect in the following conditions: When on the field, the character gains 1 stack after hitting an opponent with a Geo attack, triggering a maximum of once every 0.3s. When off the field, the character gains 1 stack every 3s. Curiosity can stack up to 4 times, each providing 6% DEF and a 6% Geo DMG Bonus."
            )
        ],
        
        # Ocean-Hued Clam
        "ocean-hued clam": [
            ArtifactSetBonus(
                "Ocean-Hued Clam", 2, "stat",
                {"healing_bonus": 15.0}, {},
                "Healing Bonus +15%"
            ),
            ArtifactSetBonus(
                "Ocean-Hued Clam", 4, "conditional",
                {}, {
                    "sea_foam_damage": {"max_damage": 30000, "duration": 3},
                    "healing_to_damage": True
                },
                "When the character equipping this artifact set heals a character in the party, a Sea-Dyed Foam will appear for 3 seconds, accumulating the amount of HP recovered from healing. At the end of the duration, the Sea-Dyed Foam will explode, dealing DMG to nearby opponents based on 90% of the accumulated healing. Max 30,000 DMG."
            )
        ],
        
        # Vermillion Hereafter
        "vermillion hereafter": [
            ArtifactSetBonus(
                "Vermillion Hereafter", 2, "stat",
                {"atk_percent": 18.0}, {},
                "ATK +18%"
            ),
            ArtifactSetBonus(
                "Vermillion Hereafter", 4, "conditional",
                {}, {
                    "atk_percent_stacks": {"max_stacks": 4, "per_stack": 10.0, "duration": 16},
                    "trigger": "elemental_burst_then_normal_charged_plunge"
                },
                "After using an Elemental Burst, this character will gain the Nascent Light effect, increasing their ATK by 8% for 16s. When the character's HP decreases, their ATK will further increase by 10%. This further increase can occur this way maximum of 4 times."
            )
        ],
        
        # Echoes of an Offering
        "echoes of an offering": [
            ArtifactSetBonus(
                "Echoes of an Offering", 2, "stat",
                {"atk_percent": 18.0}, {},
                "ATK +18%"
            ),
            ArtifactSetBonus(
                "Echoes of an Offering", 4, "conditional",
                {}, {
                    "normal_attack_dmg_chance": {"chance": 36.0, "dmg_bonus": 70.0},
                    "trigger": "normal_attack"
                },
                "When Normal Attacks hit opponents, there is a 36% chance that it will trigger Valley Rite, which will increase Normal Attack DMG by 70% of ATK."
            )
        ],
        
        # Deepwood Memories
        "deepwood memories": [
            ArtifactSetBonus(
                "Deepwood Memories", 2, "stat",
                {"dendro_dmg_bonus": 15.0}, {},
                "Dendro DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Deepwood Memories", 4, "conditional",
                {}, {
                    "dendro_res_shred": {"value": 30.0, "duration": 8},
                    "trigger": "elemental_skill_or_burst"
                },
                "After Elemental Skills or Bursts hit opponents, the targets' Dendro RES will be decreased by 30% for 8s. Max 1 stack."
            )
        ],
        
        # Gilded Dreams
        "gilded dreams": [
            ArtifactSetBonus(
                "Gilded Dreams", 2, "stat",
                {"elemental_mastery": 80}, {},
                "Elemental Mastery +80"
            ),
            ArtifactSetBonus(
                "Gilded Dreams", 4, "conditional",
                {}, {
                    "em_from_different_elements": {"per_character": 50, "max_bonus": 150},
                    "atk_from_same_element": {"per_character": 14.0, "max_bonus": 42.0},
                    "duration": 8,
                    "trigger": "elemental_reaction"
                },
                "Within 8s of triggering an Elemental Reaction, the character equipping this will obtain buffs based on the Elemental Type of the other party members: Each party member whose Elemental Type is the same as the equipping character will grant 14% ATK. Each party member whose Elemental Type is different from the equipping character will grant 50 Elemental Mastery. Max 3 stacks."
            )
        ],
        
        # Desert Pavilion Chronicle
        "desert pavilion chronicle": [
            ArtifactSetBonus(
                "Desert Pavilion Chronicle", 2, "stat",
                {"anemo_dmg_bonus": 15.0}, {},
                "Anemo DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Desert Pavilion Chronicle", 4, "conditional",
                {}, {
                    "charged_attack_speed": 10.0,
                    "normal_charged_plunge_dmg": 40.0,
                    "trigger": "charged_attack_hit",
                    "duration": 15
                },
                "When Charged Attacks hit opponents, the equipping character's Normal Attack SPD will increase by 10% while Normal, Charged, and Plunging Attack DMG will increase by 40% for 15s."
            )
        ],
        
        # Flower of Paradise Lost
        "flower of paradise lost": [
            ArtifactSetBonus(
                "Flower of Paradise Lost", 2, "stat",
                {"elemental_mastery": 80}, {},
                "Elemental Mastery +80"
            ),
            ArtifactSetBonus(
                "Flower of Paradise Lost", 4, "conditional",
                {}, {
                    "bloom_reaction_dmg": 40.0,
                    "hyperbloom_burgeon_dmg": 40.0,
                    "bloom_dmg_bonus_from_em": {"conversion_rate": 0.25, "max_bonus": 100.0}
                },
                "The equipping character's Bloom, Hyperbloom, and Burgeon reaction DMG are increased by 40%. Additionally, after the equipping character triggers Bloom, Hyperbloom, or Burgeon, they will gain another 25% bonus to the effect mentioned prior. Each stack of this lasts 10s. Max 4 stacks simultaneously."
            )
        ],
        
        # Nymph's Dream
        "nymph's dream": [
            ArtifactSetBonus(
                "Nymph's Dream", 2, "stat",
                {"hydro_dmg_bonus": 15.0}, {},
                "Hydro DMG Bonus +15%"
            ),
            ArtifactSetBonus(
                "Nymph's Dream", 4, "conditional",
                {}, {
                    "normal_charged_plunge_dmg": 30.0,
                    "duration": 8,
                    "trigger": "elemental_skill_or_burst_hit"
                },
                "After Normal, Charged, and Plunging Attacks, Elemental Skills, and Elemental Bursts hit opponents, 1 stack of Mirage will be gained for 8s. Max 3 stacks. For 1/2/3 stacks, ATK will be increased by 7%/16%/25%. For 1/2/3 stacks, Hydro DMG will be increased by 4%/9%/15%."
            )
        ],
        
        # Vourukasha's Glow
        "vourukasha's glow": [
            ArtifactSetBonus(
                "Vourukasha's Glow", 2, "stat",
                {"hp_percent": 20.0}, {},
                "HP +20%"
            ),
            ArtifactSetBonus(
                "Vourukasha's Glow", 4, "conditional",
                {}, {
                    "elemental_skill_burst_dmg": 10.0,
                    "max_stacks": 5,
                    "per_stack": 8.0,
                    "trigger": "elemental_skill_or_burst",
                    "duration": 14
                },
                "Elemental Skill and Elemental Burst DMG will be increased by 10%. After the equipping character takes DMG, the aforementioned DMG Bonus is increased by 80% for 5s. This effect can be triggered once every 0.8s. Max 5 stacks."
            )
        ],
        
        # Golden Troupe
        "golden troupe": [
            ArtifactSetBonus(
                "Golden Troupe", 2, "stat",
                {"elemental_skill_dmg": 20.0}, {},
                "Elemental Skill DMG +20%"
            ),
            ArtifactSetBonus(
                "Golden Troupe", 4, "conditional",
                {}, {
                    "elemental_skill_dmg_off_field": 25.0,
                    "elemental_skill_dmg_on_field": 25.0,
                    "trigger": "field_status"
                },
                "Increases Elemental Skill DMG by 25%. Additionally, when not on the field, Elemental Skill DMG will be further increased by 25%. This effect will be cleared 2s after taking the field."
            )
        ],
        
        # Marechaussee Hunter
        "marechaussee hunter": [
            ArtifactSetBonus(
                "Marechaussee Hunter", 2, "stat",
                {"normal_charged_attack_dmg": 15.0}, {},
                "Normal and Charged Attack DMG +15%"
            ),
            ArtifactSetBonus(
                "Marechaussee Hunter", 4, "conditional",
                {}, {
                    "crit_rate_stacks": {"max_stacks": 5, "per_stack": 12.0, "duration": 5},
                    "trigger": "hp_change"
                },
                "When current HP increases or decreases, CRIT Rate will be increased by 12% for 5s. Max 3 stacks."
            )
        ],
        
        # Song of Days Past
        "song of days past": [
            ArtifactSetBonus(
                "Song of Days Past", 2, "stat",
                {"healing_bonus": 15.0}, {},
                "Healing Bonus +15%"
            ),
            ArtifactSetBonus(
                "Song of Days Past", 4, "conditional",
                {}, {
                    "team_geo_dmg_bonus": 10.0,
                    "geo_dmg_bonus_stacks": {"max_stacks": 6, "per_stack": 4.0, "duration": 6},
                    "trigger": "healing"
                },
                "When the equipping character heals a party member, the Yearning effect will be created for 6s, which records the total amount of healing provided. When the duration expires, the Yearning effect will be transformed into the \"Waves of Days Past\" effect: When your active party member hits an opponent with a Normal Attack, Charged Attack, Plunging Attack, Elemental Skill, or Elemental Burst, the DMG dealt will be increased by 8% of the total healing amount recorded by the Yearning effect. The \"Waves of Days Past\" effect is removed after it has taken effect 5 times or after 10s. A single instance of the Yearning effect can record up to 15,000 healing, and only a single instance can exist at once, but it can record the healing from multiple equipping characters. Equipping characters on the field can trigger this effect even when not on the field."
            )
        ],
        
        # Nighttime Whispers in the Echoing Woods
        "nighttime whispers in the echoing woods": [
            ArtifactSetBonus(
                "Nighttime Whispers in the Echoing Woods", 2, "stat",
                {"atk_percent": 18.0}, {},
                "ATK +18%"
            ),
            ArtifactSetBonus(
                "Nighttime Whispers in the Echoing Woods", 4, "conditional",
                {}, {
                    "geo_dmg_bonus": 20.0,
                    "crystallize_shield_bonus": 150.0,
                    "trigger": "geo_elemental_skill"
                },
                "After using an Elemental Skill, gain 20% Geo DMG Bonus for 10s. While under a shield created by the Crystallize reaction, the above effect will be increased by 150%, and this additional increase disappears 1s after that shield is lost."
            )
        ],
        
        # Fragment of Harmonic Whimsy
        "fragment of harmonic whimsy": [
            ArtifactSetBonus(
                "Fragment of Harmonic Whimsy", 2, "stat",
                {"atk_percent": 18.0}, {},
                "ATK +18%"
            ),
            ArtifactSetBonus(
                "Fragment of Harmonic Whimsy", 4, "conditional",
                {}, {
                    "bond_of_life_value": 25.0,
                    "normal_charged_plunge_dmg": 18.0,
                    "trigger": "bond_of_life"
                },
                "When the value of a Bond of Life increases or decreases, this character deals 18% increased DMG for 6s. Max 3 stacks."
            )
        ],
        
        # Unfinished Reverie
        "unfinished reverie": [
            ArtifactSetBonus(
                "Unfinished Reverie", 2, "stat",
                {"atk_percent": 18.0}, {},
                "ATK +18%"
            ),
            ArtifactSetBonus(
                "Unfinished Reverie", 4, "conditional",
                {}, {
                    "burning_dmg": 40.0,
                    "atk_percent_from_burning": 50.0,
                    "trigger": "burning_reaction"
                },
                "After leaving combat for 2s, DMG dealt by Burning is increased by 40%. When a Burning reaction is triggered, the equipping character's ATK is increased by 50% for 8s."
            )
        ]
    }
    
    def __init__(self):
        """Initialize the artifact set calculator."""
        pass
    
    def analyze_equipped_sets(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze equipped artifacts and determine active set bonuses.
        
        Args:
            artifacts: List of equipped artifacts
            
        Returns:
            Dictionary containing set analysis and active bonuses
        """
        try:
            # Count artifacts by set
            set_counts = {}
            for artifact in artifacts:
                set_name = artifact.get("setName", "").lower()
                if set_name and set_name != "unknown":
                    set_counts[set_name] = set_counts.get(set_name, 0) + 1
            
            # Determine active set bonuses
            active_bonuses = []
            set_bonus_effects = {}
            
            for set_name, count in set_counts.items():
                if set_name in self.ARTIFACT_SET_BONUSES:
                    set_bonuses = self.ARTIFACT_SET_BONUSES[set_name]
                    
                    for bonus in set_bonuses:
                        if count >= bonus.pieces_required:
                            active_bonuses.append({
                                "set_name": bonus.set_name,
                                "pieces": f"{bonus.pieces_required}-piece",
                                "description": bonus.description,
                                "bonus_type": bonus.bonus_type,
                                "stat_bonuses": bonus.stat_bonuses,
                                "conditional_effects": bonus.conditional_effects
                            })
                            
                            # Store effects for stat calculation
                            set_key = f"{set_name}_{bonus.pieces_required}pc"
                            set_bonus_effects[set_key] = bonus
            
            return {
                "set_counts": set_counts,
                "active_bonuses": active_bonuses,
                "set_bonus_effects": set_bonus_effects,
                "total_active_sets": len(active_bonuses)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing artifact sets: {str(e)}")
            return {
                "set_counts": {},
                "active_bonuses": [],
                "set_bonus_effects": {},
                "total_active_sets": 0
            }
    
    def apply_set_bonuses_to_stats(
        self, 
        base_stats: Dict[str, float], 
        set_analysis: Dict[str, Any],
        character_info: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        Apply artifact set bonuses to character stats.
        
        Args:
            base_stats: Base character stats
            set_analysis: Result from analyze_equipped_sets
            character_info: Additional character info for conditional effects
            
        Returns:
            Updated stats with set bonuses applied
        """
        try:
            updated_stats = base_stats.copy()
            applied_effects = []
            
            for bonus_data in set_analysis.get("active_bonuses", []):
                # Apply direct stat bonuses
                stat_bonuses = bonus_data.get("stat_bonuses", {})
                for stat_name, bonus_value in stat_bonuses.items():
                    if stat_name in updated_stats:
                        updated_stats[stat_name] += bonus_value
                        applied_effects.append(f"{bonus_data['set_name']} {bonus_data['pieces']}: +{bonus_value} {stat_name}")
                
                # Handle conditional effects (simplified implementation)
                conditional_effects = bonus_data.get("conditional_effects", {})
                if conditional_effects and character_info:
                    conditional_bonuses = self._evaluate_conditional_effects(
                        conditional_effects, character_info
                    )
                    
                    for stat_name, bonus_value in conditional_bonuses.items():
                        if stat_name in updated_stats:
                            updated_stats[stat_name] += bonus_value
                            applied_effects.append(f"{bonus_data['set_name']} {bonus_data['pieces']} (conditional): +{bonus_value} {stat_name}")
            
            return {
                "stats": updated_stats,
                "applied_effects": applied_effects
            }
            
        except Exception as e:
            logger.error(f"Error applying set bonuses: {str(e)}")
            return {
                "stats": base_stats,
                "applied_effects": []
            }
    
    def _evaluate_conditional_effects(
        self, 
        conditional_effects: Dict[str, Any], 
        character_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Evaluate conditional effects based on character info.
        
        This is a simplified implementation. In a full implementation,
        you would need to track combat state, buffs, etc.
        """
        bonuses = {}
        
        try:
            weapon_type = character_info.get("weapon_type", "").lower()
            
            # Gladiator's Finale 4pc
            if "normal_attack_dmg" in conditional_effects:
                weapon_types = conditional_effects.get("weapon_types", [])
                if weapon_type in weapon_types:
                    bonuses["normal_attack_dmg"] = conditional_effects["normal_attack_dmg"]
            
            # Wanderer's Troupe 4pc
            if "charged_attack_dmg" in conditional_effects:
                weapon_types = conditional_effects.get("weapon_types", [])
                if weapon_type in weapon_types:
                    bonuses["charged_attack_dmg"] = conditional_effects["charged_attack_dmg"]
            
            # Blizzard Strayer 4pc (assume optimal conditions)
            if "crit_rate_frozen" in conditional_effects:
                # Assume fighting frozen enemies for maximum benefit
                bonuses["crit_rate"] = conditional_effects["crit_rate_frozen"] + conditional_effects.get("additional_crit_rate", 0)
            
            # Emblem of Severed Fate 4pc
            if "elemental_burst_dmg_from_er" in conditional_effects:
                energy_recharge = character_info.get("energy_recharge", 100.0)
                conversion_rate = conditional_effects["elemental_burst_dmg_from_er"]["conversion_rate"]
                max_bonus = conditional_effects["elemental_burst_dmg_from_er"]["max_bonus"]
                
                er_bonus = min((energy_recharge - 100.0) * conversion_rate, max_bonus)
                if er_bonus > 0:
                    bonuses["elemental_burst_dmg"] = er_bonus
            
            # Add more conditional effect evaluations as needed
            
        except Exception as e:
            logger.error(f"Error evaluating conditional effects: {str(e)}")
        
        return bonuses
    
    def get_set_recommendations(self, character_name: str, character_element: str) -> List[Dict[str, Any]]:
        """
        Get artifact set recommendations for a character.
        
        Args:
            character_name: Character name
            character_element: Character element
            
        Returns:
            List of recommended artifact sets
        """
        recommendations = []
        
        try:
            # Element-specific recommendations
            element_sets = {
                "pyro": ["crimson witch of flames", "lavawalker", "shimenawa's reminiscence"],
                "hydro": ["heart of depth", "nymph's dream", "gilded dreams"],
                "electro": ["thundering fury", "thundersoother", "gilded dreams"],
                "cryo": ["blizzard strayer", "shimenawa's reminiscence"],
                "anemo": ["viridescent venerer", "desert pavilion chronicle"],
                "geo": ["archaic petra", "husk of opulent dreams", "nighttime whispers in the echoing woods"],
                "dendro": ["deepwood memories", "gilded dreams", "flower of paradise lost"]
            }
            
            # Universal sets
            universal_sets = [
                "gladiator's finale",
                "wanderer's troupe", 
                "noblesse oblige",
                "emblem of severed fate",
                "shimenawa's reminiscence"
            ]
            
            # Get element-specific sets
            element_specific = element_sets.get(character_element.lower(), [])
            
            # Combine recommendations
            all_recommendations = element_specific + universal_sets
            
            # Create recommendation objects
            for set_name in all_recommendations[:6]:  # Top 6 recommendations
                if set_name in self.ARTIFACT_SET_BONUSES:
                    set_bonuses = self.ARTIFACT_SET_BONUSES[set_name]
                    recommendations.append({
                        "set_name": set_name.title(),
                        "priority": "High" if set_name in element_specific else "Medium",
                        "bonuses": [
                            {
                                "pieces": f"{bonus.pieces_required}-piece",
                                "description": bonus.description
                            }
                            for bonus in set_bonuses
                        ]
                    })
            
        except Exception as e:
            logger.error(f"Error getting set recommendations: {str(e)}")
        
        return recommendations

# Global artifact set calculator instance
artifact_set_calculator = ArtifactSetCalculator() 