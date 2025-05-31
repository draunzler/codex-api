"""
Bond of Life System

This module implements the Bond of Life mechanic from Genshin Impact.
Bond of Life prevents healing and can be used by certain characters and artifacts
to gain damage bonuses or other effects.

Based on: https://genshin-impact.fandom.com/wiki/Bond_of_Life

IMPORTANT: Only Arlecchino and Clorinde have Bond of Life mechanics in their kits.
Bond of Life is a combat mechanic that prevents healing, applied to a character by some 
enemy, weapon, or talent effects. The max value is 200% of a character's Max HP.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BondOfLifeState:
    """Represents the current Bond of Life state for a character."""
    current_value: float  # Current Bond of Life value (% of Max HP)
    max_value: float = 200.0  # Maximum Bond of Life value (200% of Max HP)
    is_active: bool = False  # Whether Bond of Life is currently active
    source: str = ""  # Source of the Bond of Life (character ability, artifact, etc.)
    duration_remaining: float = 0.0  # Duration remaining (if applicable)
    
    @property
    def value_percentage(self) -> float:
        """Get Bond of Life value as percentage of max HP."""
        return min(self.current_value, self.max_value)
    
    @property
    def is_at_max(self) -> bool:
        """Check if Bond of Life is at maximum value."""
        return self.current_value >= self.max_value
    
    def can_heal(self) -> bool:
        """Check if character can be healed (Bond of Life blocks healing)."""
        return not self.is_active or self.current_value <= 0

@dataclass
class BondOfLifeEffect:
    """Represents an effect that triggers based on Bond of Life state."""
    effect_type: str  # "damage_bonus", "stat_bonus", "special"
    trigger_condition: str  # "on_gain", "on_lose", "while_active", "on_change"
    value: float  # Effect value
    duration: float = 0.0  # Effect duration (0 = permanent while condition is met)
    max_stacks: int = 1  # Maximum stacks
    description: str = ""

class BondOfLifeSystem:
    """Manages Bond of Life mechanics and effects."""
    
    # Characters that can generate Bond of Life (ONLY Arlecchino and Clorinde)
    BOND_OF_LIFE_CHARACTERS = {
        "arlecchino": {
            "source": "elemental_skill",
            "generation_method": "blood_debt_directive",
            "max_value": 145.0,  # % of Max HP (based on talent scaling)
            "conversion_to_atk": 0.0074,  # ATK bonus per 1% of Max HP in Bond of Life
            "description": "Arlecchino's Elemental Skill applies Blood-Debt Directive, creating Bond of Life. Provides ATK bonus based on Bond of Life value.",
            "special_mechanics": [
                "Blood-Debt Directive marks enemies and creates Bond of Life",
                "ATK bonus scales with Bond of Life value",
                "Normal Attacks can absorb Blood-Debt Directive for damage",
                "Bond of Life prevents healing but provides significant ATK boost"
            ]
        },
        "clorinde": {
            "source": "elemental_skill",
            "generation_method": "hunter_vigil",
            "max_value": 200.0,  # Standard max value
            "damage_bonus_scaling": True,  # Clorinde gains damage bonuses based on Bond of Life
            "description": "Clorinde can generate and utilize Bond of Life through her Elemental Skill mechanics.",
            "special_mechanics": [
                "Hunter's Vigil state can generate Bond of Life",
                "Damage bonuses scale with Bond of Life value",
                "Pistol and Sword stances interact with Bond of Life differently",
                "Bond of Life enhances her combat effectiveness"
            ]
        }
    }
    
    # Artifact sets that interact with Bond of Life
    BOND_OF_LIFE_ARTIFACTS = {
        "fragment of harmonic whimsy": {
            "effect_type": "damage_bonus",
            "trigger": "bond_of_life_change",
            "damage_bonus": 18.0,  # % damage bonus per stack
            "max_stacks": 3,
            "duration": 6.0,
            "description": "When Bond of Life value increases or decreases, deals 18% increased DMG for 6s. Max 3 stacks.",
            "synergy_note": "The only artifact set specifically designed for Bond of Life mechanics"
        }
    }
    
    def __init__(self):
        """Initialize the Bond of Life system."""
        pass
    
    def create_bond_of_life(
        self, 
        character_name: str, 
        source: str, 
        value: float,
        max_hp: float
    ) -> BondOfLifeState:
        """
        Create a new Bond of Life state for a character.
        
        Args:
            character_name: Name of the character
            source: Source of the Bond of Life
            value: Bond of Life value (% of Max HP)
            max_hp: Character's maximum HP
            
        Returns:
            BondOfLifeState object
        """
        try:
            # Get character-specific Bond of Life data
            char_data = self.BOND_OF_LIFE_CHARACTERS.get(character_name.lower(), {})
            
            # Calculate actual Bond of Life value (capped at character-specific or global max)
            max_value = char_data.get("max_value", 200.0)
            actual_value = min(value, max_value)
            
            return BondOfLifeState(
                current_value=actual_value,
                max_value=max_value,
                is_active=actual_value > 0,
                source=source,
                duration_remaining=0.0  # Most Bond of Life effects are permanent until cleared
            )
            
        except Exception as e:
            logger.error(f"Error creating Bond of Life: {str(e)}")
            return BondOfLifeState(current_value=0.0, is_active=False)
    
    def apply_healing_to_bond_of_life(
        self, 
        bond_state: BondOfLifeState, 
        healing_amount: float
    ) -> Tuple[BondOfLifeState, float]:
        """
        Apply healing to Bond of Life (healing is absorbed by Bond of Life).
        
        Args:
            bond_state: Current Bond of Life state
            healing_amount: Amount of healing to apply
            
        Returns:
            Tuple of (updated_bond_state, actual_healing_received)
        """
        try:
            if not bond_state.is_active or bond_state.current_value <= 0:
                # No Bond of Life active, healing works normally
                return bond_state, healing_amount
            
            # Bond of Life absorbs healing equal to its base value
            absorbed_healing = min(healing_amount, bond_state.current_value)
            remaining_healing = healing_amount - absorbed_healing
            
            # Reduce Bond of Life value by the healing amount absorbed
            new_value = max(0.0, bond_state.current_value - absorbed_healing)
            
            updated_state = BondOfLifeState(
                current_value=new_value,
                max_value=bond_state.max_value,
                is_active=new_value > 0,
                source=bond_state.source,
                duration_remaining=bond_state.duration_remaining
            )
            
            return updated_state, remaining_healing
            
        except Exception as e:
            logger.error(f"Error applying healing to Bond of Life: {str(e)}")
            return bond_state, healing_amount
    
    def calculate_bond_of_life_effects(
        self, 
        character_name: str,
        bond_state: BondOfLifeState,
        character_stats: Dict[str, float],
        equipped_artifacts: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate effects from Bond of Life state.
        
        Args:
            character_name: Name of the character
            bond_state: Current Bond of Life state
            character_stats: Character's current stats
            equipped_artifacts: List of equipped artifact set names
            
        Returns:
            Dictionary containing Bond of Life effects
        """
        try:
            effects = {
                "stat_bonuses": {},
                "damage_bonuses": {},
                "special_effects": {},
                "healing_blocked": bond_state.is_active,
                "bond_value_percentage": bond_state.value_percentage
            }
            
            if not bond_state.is_active:
                return effects
            
            # Character-specific Bond of Life effects
            char_data = self.BOND_OF_LIFE_CHARACTERS.get(character_name.lower(), {})
            
            if char_data:
                # Arlecchino's ATK bonus from Bond of Life
                if character_name.lower() == "arlecchino" and "conversion_to_atk" in char_data:
                    max_hp = character_stats.get("total_hp", 15000)
                    bond_hp_value = (bond_state.current_value / 100.0) * max_hp
                    atk_bonus = bond_hp_value * char_data["conversion_to_atk"]
                    effects["stat_bonuses"]["flat_atk"] = atk_bonus
                
                # Clorinde's damage bonus from Bond of Life
                elif character_name.lower() == "clorinde" and "damage_bonus_scaling" in char_data:
                    max_hp = character_stats.get("total_hp", 15000)
                    bond_hp_value = (bond_state.current_value / 100.0) * max_hp
                    # Clorinde's damage scaling is more complex - simplified here
                    damage_bonus_percentage = min(bond_state.current_value * 0.5, 50.0)  # Example scaling
                    effects["damage_bonuses"]["elemental_skill_dmg"] = damage_bonus_percentage
                    effects["damage_bonuses"]["normal_attack_dmg"] = damage_bonus_percentage * 0.5
            
            # Artifact set effects
            if equipped_artifacts:
                for artifact_set in equipped_artifacts:
                    artifact_data = self.BOND_OF_LIFE_ARTIFACTS.get(artifact_set.lower(), {})
                    
                    if artifact_data:
                        # Fragment of Harmonic Whimsy
                        if artifact_set.lower() == "fragment of harmonic whimsy":
                            # Assume Bond of Life has changed recently for damage bonus
                            damage_bonus = artifact_data["damage_bonus"] * artifact_data["max_stacks"]
                            effects["damage_bonuses"]["normal_charged_plunge_dmg"] = damage_bonus
                            effects["special_effects"]["fragment_stacks"] = artifact_data["max_stacks"]
            
            return effects
            
        except Exception as e:
            logger.error(f"Error calculating Bond of Life effects: {str(e)}")
            return {
                "stat_bonuses": {},
                "damage_bonuses": {},
                "special_effects": {},
                "healing_blocked": False,
                "bond_value_percentage": 0.0
            }
    
    def simulate_bond_of_life_combat(
        self,
        character_name: str,
        initial_bond_value: float,
        character_stats: Dict[str, float],
        combat_duration: float = 20.0
    ) -> Dict[str, Any]:
        """
        Simulate Bond of Life effects during combat.
        
        Args:
            character_name: Name of the character
            initial_bond_value: Initial Bond of Life value (% of Max HP)
            character_stats: Character's stats
            combat_duration: Duration of combat simulation
            
        Returns:
            Dictionary containing simulation results
        """
        try:
            # Check if character has Bond of Life mechanics
            char_data = self.BOND_OF_LIFE_CHARACTERS.get(character_name.lower(), {})
            if not char_data:
                return {
                    "error": f"{character_name} does not have Bond of Life mechanics",
                    "available_characters": ["Arlecchino", "Clorinde"]
                }
            
            max_hp = character_stats.get("total_hp", 15000)
            
            # Create initial Bond of Life state
            bond_state = self.create_bond_of_life(
                character_name, "simulation", initial_bond_value, max_hp
            )
            
            # Calculate effects
            effects = self.calculate_bond_of_life_effects(
                character_name, bond_state, character_stats
            )
            
            # Simulate healing absorption over combat duration
            total_healing_blocked = 0.0
            healing_events = []
            
            # Simulate realistic healing events during combat
            if combat_duration >= 5.0:
                healing_events.append(800)  # Small heal at 5s
            if combat_duration >= 10.0:
                healing_events.append(1500)  # Medium heal at 10s
            if combat_duration >= 15.0:
                healing_events.append(1200)  # Another heal at 15s
            if combat_duration >= 20.0:
                healing_events.append(2000)  # Large heal at 20s
            
            current_bond_state = bond_state
            healing_log = []
            
            for i, healing in enumerate(healing_events):
                old_value = current_bond_state.current_value
                current_bond_state, actual_healing = self.apply_healing_to_bond_of_life(
                    current_bond_state, healing
                )
                healing_blocked = healing - actual_healing
                total_healing_blocked += healing_blocked
                
                healing_log.append({
                    "time": f"{(i+1)*5}s",
                    "healing_attempted": healing,
                    "healing_received": actual_healing,
                    "healing_blocked": healing_blocked,
                    "bond_before": old_value,
                    "bond_after": current_bond_state.current_value
                })
            
            # Character-specific analysis
            character_analysis = {}
            if character_name.lower() == "arlecchino":
                atk_bonus = effects.get("stat_bonuses", {}).get("flat_atk", 0)
                character_analysis = {
                    "atk_bonus_gained": atk_bonus,
                    "atk_bonus_percentage": (atk_bonus / character_stats.get("total_atk", 2000)) * 100,
                    "optimal_strategy": "Maintain Bond of Life for maximum ATK bonus",
                    "risk_assessment": "High risk, high reward - no healing available"
                }
            elif character_name.lower() == "clorinde":
                skill_dmg_bonus = effects.get("damage_bonuses", {}).get("elemental_skill_dmg", 0)
                character_analysis = {
                    "skill_damage_bonus": skill_dmg_bonus,
                    "stance_optimization": "Use Bond of Life in both Pistol and Sword stances",
                    "optimal_strategy": "Coordinate Bond of Life with skill rotations",
                    "risk_assessment": "Moderate risk - enhanced damage with careful timing"
                }
            
            return {
                "character_name": character_name,
                "character_has_bond_of_life": True,
                "initial_bond_value": initial_bond_value,
                "final_bond_value": current_bond_state.current_value,
                "bond_effects": effects,
                "total_healing_blocked": total_healing_blocked,
                "combat_duration": combat_duration,
                "bond_cleared": not current_bond_state.is_active,
                "healing_log": healing_log,
                "character_analysis": character_analysis,
                "simulation_notes": [
                    f"Bond of Life started at {initial_bond_value:.1f}% of Max HP",
                    f"Bond of Life ended at {current_bond_state.current_value:.1f}% of Max HP",
                    f"Total healing blocked: {total_healing_blocked:.0f} HP",
                    "Bond of Life prevents all healing until cleared",
                    f"Max Bond of Life for {character_name}: {char_data.get('max_value', 200.0)}% of Max HP"
                ],
                "wiki_reference": "https://genshin-impact.fandom.com/wiki/Bond_of_Life"
            }
            
        except Exception as e:
            logger.error(f"Error simulating Bond of Life combat: {str(e)}")
            return {"error": str(e)}
    
    def get_bond_of_life_recommendations(self, character_name: str) -> Dict[str, Any]:
        """
        Get recommendations for using Bond of Life effectively.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Dictionary containing recommendations
        """
        try:
            char_data = self.BOND_OF_LIFE_CHARACTERS.get(character_name.lower(), {})
            
            if not char_data:
                return {
                    "has_bond_of_life": False,
                    "recommendations": [
                        "This character does not have Bond of Life mechanics",
                        "Only Arlecchino and Clorinde have Bond of Life in their kits",
                        "Bond of Life can still be applied by certain enemies or effects"
                    ]
                }
            
            recommendations = []
            artifact_recommendations = []
            
            # Character-specific recommendations
            if character_name.lower() == "arlecchino":
                recommendations.extend([
                    "Use Elemental Skill to apply Blood-Debt Directive for significant ATK bonus",
                    "Higher HP builds increase the ATK bonus from Bond of Life conversion",
                    "Avoid healing when Bond of Life is active to maintain the ATK bonus",
                    "Use Normal Attacks to absorb Blood-Debt Directive for massive damage",
                    "Bond of Life value can reach up to 145% of Max HP with Arlecchino",
                    "The ATK bonus scales at 0.74% per 1% of Max HP in Bond of Life",
                    "Plan rotations around maintaining Bond of Life for maximum DPS"
                ])
                artifact_recommendations.extend([
                    "Fragment of Harmonic Whimsy (4pc) - THE Bond of Life artifact set, provides damage bonus when Bond of Life changes",
                    "Gladiator's Finale (4pc) - Strong alternative for Normal Attack focus",
                    "Crimson Witch of Flames (4pc) - Pyro damage bonus for elemental builds",
                    "Shimenawa's Reminiscence (4pc) - Alternative for charged attack builds"
                ])
            
            elif character_name.lower() == "clorinde":
                recommendations.extend([
                    "Use Elemental Skill to enter Hunter's Vigil and generate Bond of Life",
                    "Bond of Life enhances damage output in both Pistol and Sword stances",
                    "Time healing carefully to maintain Bond of Life when needed for damage",
                    "Coordinate Bond of Life usage with skill rotations for optimal DPS",
                    "Higher HP builds can increase Bond of Life effectiveness",
                    "Master stance switching to maximize Bond of Life benefits"
                ])
                artifact_recommendations.extend([
                    "Fragment of Harmonic Whimsy (4pc) - THE Bond of Life artifact set, synergizes perfectly with her mechanics",
                    "Thundering Fury (4pc) - Electro damage and skill cooldown reduction",
                    "Gladiator's Finale (4pc) - Normal Attack damage bonus for both stances",
                    "Golden Troupe (4pc) - Elemental Skill damage bonus alternative"
                ])
            
            # General Bond of Life recommendations (applies to both characters)
            recommendations.extend([
                "Bond of Life blocks ALL healing until cleared by healing equal to its value",
                "Plan combat carefully when Bond of Life is active - no healing available",
                "Use Statue of The Seven to instantly clear Bond of Life if needed",
                "Bond of Life can stack up to 200% of Max HP (145% for Arlecchino)",
                "Some artifact sets provide significant bonuses when Bond of Life is active",
                "Consider team composition - avoid healers when maintaining Bond of Life",
                "Emergency healing sources (food, statues) can clear Bond of Life instantly"
            ])
            
            return {
                "has_bond_of_life": True,
                "character_data": char_data,
                "recommendations": recommendations,
                "artifact_recommendations": artifact_recommendations,
                "max_bond_value": char_data.get("max_value", 200.0),
                "generation_method": char_data.get("generation_method", "unknown"),
                "special_mechanics": char_data.get("special_mechanics", []),
                "wiki_reference": "https://genshin-impact.fandom.com/wiki/Bond_of_Life"
            }
            
        except Exception as e:
            logger.error(f"Error getting Bond of Life recommendations: {str(e)}")
            return {"error": str(e)}

# Global Bond of Life system instance
bond_of_life_system = BondOfLifeSystem() 