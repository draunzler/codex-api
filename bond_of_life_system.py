"""
Bond of Life System

This module implements the Bond of Life mechanic from Genshin Impact.
Bond of Life prevents healing and can be used by certain characters and artifacts
to gain damage bonuses or other effects.

Based on: https://genshin-impact.fandom.com/wiki/Bond_of_Life
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
    
    # Characters that can generate Bond of Life
    BOND_OF_LIFE_CHARACTERS = {
        "arlecchino": {
            "source": "elemental_skill",
            "generation_method": "blood_debt_directive",
            "max_value": 145.0,  # % of Max HP
            "conversion_to_atk": 0.0074,  # ATK bonus per 1% of Max HP in Bond of Life
            "description": "Arlecchino's Elemental Skill applies Blood-Debt Directive, creating Bond of Life"
        },
        "xianyun": {
            "source": "constellation",
            "generation_method": "c6_effect",
            "max_value": 40.0,
            "damage_bonus": 0.004,  # Damage bonus per 1% of Max HP in Bond of Life
            "description": "Xianyun's C6 can create Bond of Life for team members"
        },
        "gaming": {
            "source": "elemental_burst",
            "generation_method": "suanni_beast_within",
            "max_value": 50.0,
            "damage_bonus": 1.6,  # Damage bonus per 1000 HP of Bond of Life
            "description": "Gaming's Elemental Burst can create Bond of Life"
        }
    }
    
    # Artifact sets that interact with Bond of Life
    BOND_OF_LIFE_ARTIFACTS = {
        "fragment of harmonic whimsy": {
            "effect_type": "damage_bonus",
            "trigger": "bond_of_life_change",
            "damage_bonus": 18.0,  # % damage bonus
            "max_stacks": 3,
            "duration": 6.0,
            "description": "When Bond of Life value increases or decreases, deals 18% increased DMG for 6s. Max 3 stacks."
        },
        "marechaussee hunter": {
            "effect_type": "crit_rate_bonus",
            "trigger": "hp_change",
            "crit_rate_bonus": 12.0,  # % crit rate bonus per stack
            "max_stacks": 3,
            "duration": 5.0,
            "description": "When current HP increases or decreases, CRIT Rate increased by 12% for 5s. Max 3 stacks."
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
            
            # Calculate actual Bond of Life value
            actual_value = min(value, char_data.get("max_value", 200.0))
            
            return BondOfLifeState(
                current_value=actual_value,
                max_value=char_data.get("max_value", 200.0),
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
            
            # Bond of Life absorbs healing
            absorbed_healing = min(healing_amount, bond_state.current_value)
            remaining_healing = healing_amount - absorbed_healing
            
            # Reduce Bond of Life value
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
                
                # Gaming's damage bonus from Bond of Life
                elif character_name.lower() == "gaming" and "damage_bonus" in char_data:
                    max_hp = character_stats.get("total_hp", 15000)
                    bond_hp_value = (bond_state.current_value / 100.0) * max_hp
                    damage_bonus = (bond_hp_value / 1000.0) * char_data["damage_bonus"]
                    effects["damage_bonuses"]["elemental_burst_dmg"] = damage_bonus
                
                # Xianyun's damage bonus from Bond of Life
                elif character_name.lower() == "xianyun" and "damage_bonus" in char_data:
                    max_hp = character_stats.get("total_hp", 15000)
                    bond_hp_value = (bond_state.current_value / 100.0) * max_hp
                    damage_bonus = bond_hp_value * char_data["damage_bonus"]
                    effects["damage_bonuses"]["all_dmg"] = damage_bonus
            
            # Artifact set effects
            if equipped_artifacts:
                for artifact_set in equipped_artifacts:
                    artifact_data = self.BOND_OF_LIFE_ARTIFACTS.get(artifact_set.lower(), {})
                    
                    if artifact_data:
                        # Fragment of Harmonic Whimsy
                        if artifact_set.lower() == "fragment of harmonic whimsy":
                            # Assume Bond of Life has changed recently for damage bonus
                            effects["damage_bonuses"]["normal_charged_plunge_dmg"] = artifact_data["damage_bonus"]
                            effects["special_effects"]["fragment_stacks"] = artifact_data["max_stacks"]
                        
                        # Marechaussee Hunter (triggers on HP changes, including Bond of Life)
                        elif artifact_set.lower() == "marechaussee hunter":
                            # Assume HP has changed recently for crit rate bonus
                            crit_bonus = artifact_data["crit_rate_bonus"] * artifact_data["max_stacks"]
                            effects["stat_bonuses"]["crit_rate"] = crit_bonus
            
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
            max_hp = character_stats.get("total_hp", 15000)
            
            # Create initial Bond of Life state
            bond_state = self.create_bond_of_life(
                character_name, "simulation", initial_bond_value, max_hp
            )
            
            # Calculate effects
            effects = self.calculate_bond_of_life_effects(
                character_name, bond_state, character_stats
            )
            
            # Simulate healing absorption
            total_healing_blocked = 0.0
            healing_events = [500, 1000, 750, 1200]  # Simulated healing events
            
            for healing in healing_events:
                bond_state, actual_healing = self.apply_healing_to_bond_of_life(
                    bond_state, healing
                )
                total_healing_blocked += (healing - actual_healing)
            
            return {
                "character_name": character_name,
                "initial_bond_value": initial_bond_value,
                "final_bond_value": bond_state.current_value,
                "bond_effects": effects,
                "total_healing_blocked": total_healing_blocked,
                "combat_duration": combat_duration,
                "bond_cleared": not bond_state.is_active,
                "simulation_notes": [
                    f"Bond of Life started at {initial_bond_value:.1f}% of Max HP",
                    f"Bond of Life ended at {bond_state.current_value:.1f}% of Max HP",
                    f"Total healing blocked: {total_healing_blocked:.0f} HP",
                    "Bond of Life prevents all healing until cleared"
                ]
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
                    "recommendations": ["This character does not have Bond of Life mechanics"]
                }
            
            recommendations = []
            artifact_recommendations = []
            
            # Character-specific recommendations
            if character_name.lower() == "arlecchino":
                recommendations.extend([
                    "Use Elemental Skill to apply Blood-Debt Directive for ATK bonus",
                    "Higher HP builds increase the ATK bonus from Bond of Life",
                    "Avoid healing when Bond of Life is active to maintain ATK bonus",
                    "Use Normal Attacks to absorb Blood-Debt Directive for damage"
                ])
                artifact_recommendations.extend([
                    "Fragment of Harmonic Whimsy (4pc) - Damage bonus when Bond of Life changes",
                    "Marechaussee Hunter (4pc) - Crit Rate bonus from HP changes"
                ])
            
            elif character_name.lower() == "gaming":
                recommendations.extend([
                    "Use Elemental Burst to create Bond of Life for damage bonus",
                    "Higher HP builds increase the damage bonus potential",
                    "Time healing carefully to maintain Bond of Life when needed"
                ])
            
            elif character_name.lower() == "xianyun":
                recommendations.extend([
                    "C6 effect creates Bond of Life for team members",
                    "Coordinate with team for optimal Bond of Life usage",
                    "Consider team HP builds for maximum effect"
                ])
            
            # General Bond of Life recommendations
            recommendations.extend([
                "Bond of Life blocks ALL healing until cleared",
                "Plan combat carefully when Bond of Life is active",
                "Use Statue of The Seven to instantly clear Bond of Life if needed",
                "Some artifact sets provide bonuses when Bond of Life is active"
            ])
            
            return {
                "has_bond_of_life": True,
                "character_data": char_data,
                "recommendations": recommendations,
                "artifact_recommendations": artifact_recommendations,
                "max_bond_value": char_data.get("max_value", 200.0),
                "generation_method": char_data.get("generation_method", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error getting Bond of Life recommendations: {str(e)}")
            return {"error": str(e)}

# Global Bond of Life system instance
bond_of_life_system = BondOfLifeSystem() 