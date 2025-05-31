"""
Character Stats Extractor

This module extracts character stats from database data and converts them
to the format required by the simple damage calculator.

Enhanced with artifact set bonuses and Bond of Life mechanics.
"""

from typing import Dict, Any, Optional, List
import logging
from simple_damage_calculator import CharacterStats, damage_calculator

logger = logging.getLogger(__name__)

class CharacterStatsExtractor:
    """Extract character stats from database data."""
    
    def __init__(self):
        """Initialize the stats extractor."""
        pass
    
    def extract_stats_from_database(self, character_data: Dict[str, Any], character_name: str) -> CharacterStats:
        """
        Extract CharacterStats from database character data.
        
        Args:
            character_data: Raw character data from database
            character_name: Character name for fallback data
            
        Returns:
            CharacterStats object ready for damage calculation
        """
        try:
            # Get character base data for fallbacks
            base_data = damage_calculator.get_character_base_stats(character_name)
            element = damage_calculator.get_character_element(character_name)
            
            # Extract basic info
            level = character_data.get("level", 90)
            
            # Extract stats from the stats field
            stats = character_data.get("stats", {})
            
            # Base stats (character + weapon)
            base_atk = stats.get("base_atk", base_data.get("base_atk", 800))
            base_hp = stats.get("base_hp", base_data.get("base_hp", 12000))
            base_def = stats.get("base_def", base_data.get("base_def", 700))
            
            # Flat stats
            flat_atk = stats.get("atk", 0)  # This might be total ATK, need to calculate flat
            flat_hp = stats.get("hp", 0)
            flat_def = stats.get("def", 0)
            
            # Percentage stats
            atk_percent = stats.get("atk_percent", 0)
            hp_percent = stats.get("hp_percent", 0)
            def_percent = stats.get("def_percent", 0)
            
            # Critical stats - these are TOTAL values that already include ascension bonuses
            crit_rate = stats.get("crit_rate", 5.0)
            crit_dmg = stats.get("crit_dmg", 50.0)
            
            # Other stats
            elemental_mastery = stats.get("elemental_mastery", 0)
            energy_recharge = stats.get("energy_recharge", 100.0)
            
            # Elemental damage bonuses
            elemental_dmg_bonus = self._get_elemental_damage_bonus(stats, element)
            physical_dmg_bonus = stats.get("physical_dmg_bonus", 0)
            
            # Handle total ATK calculation
            total_atk = stats.get("total_atk", 0)
            if total_atk > 0:
                # If we have total ATK, calculate flat ATK
                calculated_total = (base_atk + flat_atk) * (1 + atk_percent / 100)
                if abs(calculated_total - total_atk) > 50:  # Significant difference
                    # Recalculate flat ATK to match total
                    if atk_percent > 0:
                        flat_atk = (total_atk / (1 + atk_percent / 100)) - base_atk
                    else:
                        flat_atk = total_atk - base_atk
            
            # Create base character stats
            character_stats = CharacterStats(
                level=level,
                base_atk=base_atk,
                flat_atk=max(0, flat_atk),  # Ensure non-negative
                atk_percent=atk_percent,
                base_hp=base_hp,
                flat_hp=max(0, flat_hp),
                hp_percent=hp_percent,
                base_def=base_def,
                flat_def=max(0, flat_def),
                def_percent=def_percent,
                crit_rate=min(100.0, max(0.0, crit_rate)),  # Cap between 0-100%
                crit_dmg=max(0.0, crit_dmg),
                elemental_mastery=max(0.0, elemental_mastery),
                elemental_dmg_bonus=elemental_dmg_bonus,
                physical_dmg_bonus=physical_dmg_bonus,
                energy_recharge=energy_recharge
            )
            
            # Apply artifact set bonuses
            artifacts = character_data.get("artifacts", [])
            if artifacts:
                character_stats = self._apply_artifact_set_bonuses(
                    character_stats, artifacts, character_name, element
                )
            
            # Apply Bond of Life effects if applicable
            character_stats = self._apply_bond_of_life_effects(
                character_stats, character_name, artifacts
            )
            
            return character_stats
            
        except Exception as e:
            logger.error(f"Error extracting stats for {character_name}: {str(e)}")
            # Return fallback stats
            return self._get_fallback_stats(character_name)
    
    def _apply_artifact_set_bonuses(
        self, 
        character_stats: CharacterStats, 
        artifacts: List[Dict[str, Any]], 
        character_name: str,
        element: str
    ) -> CharacterStats:
        """Apply artifact set bonuses to character stats."""
        try:
            from artifact_set_calculator import artifact_set_calculator
            
            # Analyze equipped artifact sets
            set_analysis = artifact_set_calculator.analyze_equipped_sets(artifacts)
            
            if set_analysis["total_active_sets"] == 0:
                return character_stats
            
            # Convert CharacterStats to dict for processing
            stats_dict = {
                "atk_percent": character_stats.atk_percent,
                "hp_percent": character_stats.hp_percent,
                "def_percent": character_stats.def_percent,
                "crit_rate": character_stats.crit_rate,
                "crit_dmg": character_stats.crit_dmg,
                "elemental_mastery": character_stats.elemental_mastery,
                "elemental_dmg_bonus": character_stats.elemental_dmg_bonus,
                "physical_dmg_bonus": character_stats.physical_dmg_bonus,
                "energy_recharge": character_stats.energy_recharge,
                "healing_bonus": character_stats.healing_bonus,
                # Element-specific damage bonuses
                f"{element}_dmg_bonus": character_stats.elemental_dmg_bonus,
                "pyro_dmg_bonus": 0.0,
                "hydro_dmg_bonus": 0.0,
                "electro_dmg_bonus": 0.0,
                "cryo_dmg_bonus": 0.0,
                "anemo_dmg_bonus": 0.0,
                "geo_dmg_bonus": 0.0,
                "dendro_dmg_bonus": 0.0,
                # Damage type bonuses
                "normal_attack_dmg": 0.0,
                "charged_attack_dmg": 0.0,
                "elemental_skill_dmg": 0.0,
                "elemental_burst_dmg": 0.0,
                "normal_charged_attack_dmg": 0.0,
                "normal_charged_plunge_dmg": 0.0,
                "shield_strength": 0.0
            }
            
            # Set current element damage bonus
            stats_dict[f"{element}_dmg_bonus"] = character_stats.elemental_dmg_bonus
            
            # Get weapon type for conditional effects
            weapon_data = artifacts[0] if artifacts else {}  # This should come from weapon data
            character_info = {
                "weapon_type": "sword",  # Default, should be extracted from actual weapon data
                "energy_recharge": character_stats.energy_recharge,
                "character_name": character_name,
                "element": element
            }
            
            # Apply set bonuses
            bonus_result = artifact_set_calculator.apply_set_bonuses_to_stats(
                stats_dict, set_analysis, character_info
            )
            
            updated_stats = bonus_result["stats"]
            
            # Update character stats with bonuses
            character_stats.atk_percent = updated_stats.get("atk_percent", character_stats.atk_percent)
            character_stats.hp_percent = updated_stats.get("hp_percent", character_stats.hp_percent)
            character_stats.def_percent = updated_stats.get("def_percent", character_stats.def_percent)
            character_stats.crit_rate = min(100.0, updated_stats.get("crit_rate", character_stats.crit_rate))
            character_stats.crit_dmg = updated_stats.get("crit_dmg", character_stats.crit_dmg)
            character_stats.elemental_mastery = updated_stats.get("elemental_mastery", character_stats.elemental_mastery)
            character_stats.energy_recharge = updated_stats.get("energy_recharge", character_stats.energy_recharge)
            character_stats.healing_bonus = updated_stats.get("healing_bonus", character_stats.healing_bonus)
            
            # Update elemental damage bonus (use the highest applicable bonus)
            element_dmg_key = f"{element}_dmg_bonus"
            if element_dmg_key in updated_stats:
                character_stats.elemental_dmg_bonus = updated_stats[element_dmg_key]
            
            # Store additional damage bonuses for later use in damage calculation
            character_stats.additive_base_dmg = updated_stats.get("normal_attack_dmg", 0.0)
            
            # Add artifact set info to character stats for reference
            if not hasattr(character_stats, 'artifact_set_info'):
                character_stats.artifact_set_info = {
                    "active_sets": [bonus["set_name"] + " " + bonus["pieces"] for bonus in set_analysis["active_bonuses"]],
                    "applied_effects": bonus_result.get("applied_effects", [])
                }
            
            return character_stats
            
        except Exception as e:
            logger.error(f"Error applying artifact set bonuses: {str(e)}")
            return character_stats
    
    def _apply_bond_of_life_effects(
        self, 
        character_stats: CharacterStats, 
        character_name: str,
        artifacts: List[Dict[str, Any]]
    ) -> CharacterStats:
        """Apply Bond of Life effects to character stats."""
        try:
            from bond_of_life_system import bond_of_life_system
            
            # Check if character has Bond of Life mechanics
            bond_recommendations = bond_of_life_system.get_bond_of_life_recommendations(character_name)
            
            if not bond_recommendations.get("has_bond_of_life", False):
                return character_stats
            
            # For calculation purposes, assume Bond of Life is active at a reasonable value
            # In a real implementation, this would come from current game state
            bond_value = 50.0  # Assume 50% of Max HP as Bond of Life for calculation
            
            # Create Bond of Life state
            bond_state = bond_of_life_system.create_bond_of_life(
                character_name, "calculation", bond_value, character_stats.total_hp
            )
            
            # Get equipped artifact set names
            artifact_sets = []
            if artifacts:
                set_counts = {}
                for artifact in artifacts:
                    set_name = artifact.get("setName", "").lower()
                    if set_name:
                        set_counts[set_name] = set_counts.get(set_name, 0) + 1
                
                # Add sets with 4 pieces
                for set_name, count in set_counts.items():
                    if count >= 4:
                        artifact_sets.append(set_name)
            
            # Calculate Bond of Life effects
            bond_effects = bond_of_life_system.calculate_bond_of_life_effects(
                character_name, bond_state, {
                    "total_hp": character_stats.total_hp,
                    "total_atk": character_stats.total_atk
                }, artifact_sets
            )
            
            # Apply stat bonuses from Bond of Life
            stat_bonuses = bond_effects.get("stat_bonuses", {})
            if "flat_atk" in stat_bonuses:
                character_stats.flat_atk += stat_bonuses["flat_atk"]
            if "crit_rate" in stat_bonuses:
                character_stats.crit_rate = min(100.0, character_stats.crit_rate + stat_bonuses["crit_rate"])
            
            # Store Bond of Life info for reference
            if not hasattr(character_stats, 'bond_of_life_info'):
                character_stats.bond_of_life_info = {
                    "has_bond_of_life": True,
                    "assumed_value": bond_value,
                    "effects": bond_effects,
                    "recommendations": bond_recommendations.get("recommendations", [])
                }
            
            return character_stats
            
        except Exception as e:
            logger.error(f"Error applying Bond of Life effects: {str(e)}")
            return character_stats
    
    def _get_elemental_damage_bonus(self, stats: Dict[str, Any], element: str) -> float:
        """Get elemental damage bonus for the character's element."""
        element_key = f"{element}_dmg_bonus"
        return stats.get(element_key, 0.0)
    
    def _get_fallback_stats(self, character_name: str) -> CharacterStats:
        """Get fallback stats when extraction fails."""
        base_data = damage_calculator.get_character_base_stats(character_name)
        
        # Apply ascension stat
        ascension_stat = base_data.get("ascension_stat", "atk_percent")
        ascension_value = base_data.get("ascension_value", 24.0)
        
        crit_rate = 5.0
        crit_dmg = 50.0
        atk_percent = 0.0
        elemental_mastery = 0.0
        elemental_dmg_bonus = 0.0
        
        if ascension_stat == "crit_rate":
            crit_rate += ascension_value
        elif ascension_stat == "crit_dmg":
            crit_dmg += ascension_value
        elif ascension_stat == "atk_percent":
            atk_percent += ascension_value
        elif ascension_stat == "elemental_mastery":
            elemental_mastery += ascension_value
        elif ascension_stat.endswith("_dmg"):
            elemental_dmg_bonus += ascension_value
        
        return CharacterStats(
            level=90,
            base_atk=base_data.get("base_atk", 800),
            flat_atk=311,  # Typical 5-star weapon flat ATK
            atk_percent=atk_percent + 46.6,  # Typical ATK% sands
            base_hp=base_data.get("base_hp", 12000),
            flat_hp=4780,  # Typical flower flat HP
            hp_percent=0.0,
            base_def=base_data.get("base_def", 700),
            flat_def=0.0,
            def_percent=0.0,
            crit_rate=crit_rate + 31.1,  # Typical crit rate circlet
            crit_dmg=crit_dmg + 62.2,  # Typical crit dmg circlet
            elemental_mastery=elemental_mastery,
            elemental_dmg_bonus=elemental_dmg_bonus + 46.6,  # Typical elemental goblet
            physical_dmg_bonus=0.0
        )
    
    def get_character_build_summary(self, character_stats: CharacterStats) -> Dict[str, Any]:
        """Get a summary of the character build."""
        summary = {
            "total_atk": character_stats.total_atk,
            "total_hp": character_stats.total_hp,
            "total_def": character_stats.total_def,
            "crit_rate": character_stats.crit_rate,
            "crit_dmg": character_stats.crit_dmg,
            "crit_ratio": character_stats.crit_dmg / character_stats.crit_rate if character_stats.crit_rate > 0 else 0,
            "elemental_mastery": character_stats.elemental_mastery,
            "elemental_dmg_bonus": character_stats.elemental_dmg_bonus,
            "energy_recharge": character_stats.energy_recharge,
            "build_quality": self._assess_build_quality(character_stats)
        }
        
        # Add artifact set info if available
        if hasattr(character_stats, 'artifact_set_info'):
            summary["artifact_sets"] = character_stats.artifact_set_info["active_sets"]
            summary["set_effects"] = character_stats.artifact_set_info["applied_effects"]
        
        # Add Bond of Life info if available
        if hasattr(character_stats, 'bond_of_life_info'):
            summary["bond_of_life"] = {
                "has_bond_of_life": character_stats.bond_of_life_info["has_bond_of_life"],
                "assumed_value": character_stats.bond_of_life_info["assumed_value"],
                "effects_applied": len(character_stats.bond_of_life_info["effects"]["stat_bonuses"]) > 0
            }
        
        return summary
    
    def _assess_build_quality(self, stats: CharacterStats) -> str:
        """Assess the quality of the character build."""
        score = 0
        
        # ATK assessment
        if stats.total_atk >= 2500:
            score += 2
        elif stats.total_atk >= 2000:
            score += 1
        
        # Crit ratio assessment
        crit_ratio = stats.crit_dmg / stats.crit_rate if stats.crit_rate > 0 else 0
        if 1.8 <= crit_ratio <= 2.2:  # Optimal ratio
            score += 2
        elif 1.5 <= crit_ratio <= 2.5:  # Good ratio
            score += 1
        
        # Crit rate assessment
        if stats.crit_rate >= 70:
            score += 2
        elif stats.crit_rate >= 50:
            score += 1
        
        # Crit damage assessment
        if stats.crit_dmg >= 150:
            score += 2
        elif stats.crit_dmg >= 120:
            score += 1
        
        # Elemental damage bonus assessment
        if stats.elemental_dmg_bonus >= 60:
            score += 1
        
        # Artifact set bonus (if available)
        if hasattr(stats, 'artifact_set_info') and stats.artifact_set_info["active_sets"]:
            score += 1
        
        # Bond of Life bonus (if available and beneficial)
        if hasattr(stats, 'bond_of_life_info') and stats.bond_of_life_info["has_bond_of_life"]:
            score += 1
        
        # Convert score to quality rating
        if score >= 9:
            return "Perfect"
        elif score >= 8:
            return "Excellent"
        elif score >= 6:
            return "Very Good"
        elif score >= 4:
            return "Good"
        elif score >= 2:
            return "Average"
        else:
            return "Needs Improvement"

# Global stats extractor instance
stats_extractor = CharacterStatsExtractor() 