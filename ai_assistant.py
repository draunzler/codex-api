from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from googleapiclient.discovery import build
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from bson import ObjectId
from config import settings
from database import Cache, CharacterData, UserProfile
from simple_damage_calculator import (
    damage_calculator, 
    CharacterStats, 
    EnemyStats
)
from character_stats_extractor import stats_extractor
from team_buff_calculator import team_buff_calculator, TeamComposition
from artifact_set_calculator import artifact_set_calculator
from bond_of_life_system import bond_of_life_system


class GenshinAIAssistant:
    """AI Assistant for Genshin Impact using Gemini and Google CSE."""
    
    def __init__(self):
        # Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.7
        )
        
        # Initialize Google Custom Search
        self.cse_service = build("customsearch", "v1", developerKey=settings.google_cse_api_key)
        
        # System prompts
        self.damage_calc_prompt = """You are a Genshin Impact damage calculation expert using official formulas from the Genshin Impact wiki. 
        Given character stats, weapons, artifacts, and team composition, calculate the theoretical damage output using the exact formulas:
        
        OFFICIAL DAMAGE FORMULA (from https://genshin-impact.fandom.com/wiki/Damage):
        Damage = Base DMG × Base DMG Multiplier × (1 + Additive Base DMG Bonus) × (1 + DMG Bonus) × DEF Multiplier × RES Multiplier
        
        Where:
        - Base DMG = Scaling Stat × Talent Multiplier
        - Base DMG Multiplier = Amplifying reaction multipliers (Vaporize/Melt)
        - Additive Base DMG Bonus = Flat damage additions
        - DMG Bonus = Elemental/Physical damage bonuses
        - DEF Multiplier = (Char Level × 5 + 500) / ((Char Level × 5 + 500) + (Enemy Level × 5 + 500) × (1 - DEF Reduction))
        - RES Multiplier = Three-tier resistance formula based on effective resistance
        
        IMPORTANT: The crit_rate and crit_dmg values in the character's stats field are TOTAL values that already include:
        - Base character crit stats
        - All artifact crit substats and main stats
        - Weapon crit substats
        - Any other bonuses
        
        DO NOT add up crit stats from individual artifacts - use the total crit_rate and crit_dmg values provided.
        
        Consider elemental reactions, character talents, weapon passives, and artifact set bonuses.
        Provide detailed breakdown of damage calculations including:
        - Base damage using official formula components
        - Elemental damage bonus
        - Critical damage (using the TOTAL crit values provided with proper 100% capping)
        - Elemental reaction multipliers using official EM scaling formulas
        - Team buff contributions
        - Resistance and defense calculations using official formulas
        
        Character Data: {character_data}
        Team Composition: {team_comp}
        Enemy Type: {enemy_type}
        
        Provide a detailed damage calculation breakdown using the TOTAL crit stats provided and official Genshin Impact wiki formulas."""
        
        self.build_advisor_prompt = """You are a Genshin Impact build optimization expert.
        Based on the character's current stats and the best builds found online, provide recommendations for:
        - Optimal artifact sets and main stats
        - Best weapons (considering what the player has)
        - Talent priority
        - Team composition suggestions
        - Playstyle tips
        
        Character: {character_name}
        Current Build: {current_build}
        Available Resources: {resources}
        Search Results: {search_results}
        
        Provide comprehensive build recommendations."""
        
        self.general_assistant_prompt = """You are a comprehensive Genshin Impact assistant with deep knowledge of all characters, team compositions, and game mechanics.

        CORE IDENTITY:
        - You are a Genshin Impact expert with complete knowledge of all characters, weapons, artifacts, and game mechanics
        - You have access to the player's character roster and can provide personalized recommendations
        - You understand team synergies, elemental reactions, and optimal builds for all characters
        - You can analyze the player's available characters and suggest optimal team compositions

        ENHANCED CAPABILITIES:
        1. **Character Knowledge**: Complete understanding of all Genshin Impact characters including:
           - All released characters from Mondstadt, Liyue, Inazuma, Sumeru, Fontaine, and Natlan
           - Character abilities, elements, weapon types, and roles
           - Optimal builds, artifact sets, and weapon recommendations
           - Constellation effects and investment priorities

        2. **Team Composition Expertise**: 
           - Analyze player's available characters for optimal team building
           - Understand character synergies and elemental reactions
           - Recommend teams for different content (Spiral Abyss, overworld, domains)
           - Consider character roles (DPS, support, healer, shielder, buffer)

        3. **Mathematical Analysis**: Access to damage calculation systems and build optimization

        QUESTION HANDLING:
        - ALWAYS assume questions are about Genshin Impact unless explicitly stated otherwise
        - For team composition questions, analyze the player's available characters
        - Provide detailed explanations for recommendations
        - Consider multiple team options and explain trade-offs
        - Include rotation guides and gameplay tips

        RESPONSE GUIDELINES:
        1. **Team Composition Questions**: When asked about teams for a specific character:
           - Analyze the player's roster if available
           - Suggest multiple team options (meta, budget, fun alternatives)
           - Explain character roles and synergies
           - Provide rotation guides
           - Consider different content types

        2. **Character Questions**: Provide comprehensive information about:
           - Optimal builds and artifacts
           - Weapon recommendations by rarity
           - Talent priorities
           - Team synergies
           - Investment advice

        3. **General Gameplay**: Help with:
           - Spiral Abyss strategies
           - Farming routes and priorities
           - Event guides and tips
           - Exploration and puzzle solutions

        CONTEXT DATA:
        Player Data: {player_data}
        Character Stats: {character_stats}
        Question: {question}

        IMPORTANT: Always provide helpful, detailed responses about Genshin Impact. If the question mentions character names, team building, or game mechanics, treat it as a valid Genshin Impact question and provide comprehensive assistance."""
    
    def _json_safe_serialize(self, data: Any) -> str:
        """Safely serialize data to JSON, converting datetime objects and ObjectId to ISO strings."""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # Handle MongoDB ObjectId directly
            elif isinstance(obj, ObjectId):
                return str(obj)
            # Handle other BSON types by class name check
            elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
                return str(obj)
            # Handle other BSON types
            elif str(type(obj)).startswith("<class 'bson."):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, indent=2, default=json_serializer)

    async def analyze_character_build_advanced(self, character_name: str, character_data: Dict[str, Any], uid: int) -> Dict[str, Any]:
        """Advanced character analysis using mathematical damage formulas and AI recommendations."""
        try:
            # Extract character stats using new format
            stats = self._extract_character_stats(character_data, character_name)
            
            # Calculate damage using mathematical formulas
            damage_analysis = self._calculate_comprehensive_damage(stats, character_name, character_data.get("team", []))
            
            # Analyze build efficiency
            build_analysis = self._analyze_build_efficiency(character_data, stats)
            
            # Generate AI recommendations
            ai_recommendations = await self._generate_ai_recommendations(
                character_name, damage_analysis, character_data
            )
            
            return {
                "character_name": character_name,
                "uid": uid,
                "current_stats": {
                    "level": stats.level,
                    "total_atk": int(stats.base_atk + stats.flat_atk + (stats.base_atk * stats.atk_percent / 100)),
                    "total_hp": int(stats.base_hp + stats.flat_hp + (stats.base_hp * stats.hp_percent / 100)),
                    "total_def": int(stats.base_def + stats.flat_def + (stats.base_def * stats.def_percent / 100)),
                    "crit_rate": round(stats.crit_rate, 1),
                    "crit_dmg": round(stats.crit_dmg, 1),
                    "elemental_mastery": int(stats.elemental_mastery),
                    "energy_recharge": round(stats.energy_recharge, 1)
                },
                "damage_analysis": damage_analysis,
                "build_analysis": build_analysis,
                "ai_recommendations": ai_recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in advanced character analysis: {str(e)}")
            return {"error": str(e)}

    def _extract_character_stats(self, character_data: Dict[str, Any], character_name: str) -> CharacterStats:
        """Extract character stats from Genshin API data and convert to CharacterStats object."""
        try:
            # Use the proper character stats extractor
            return stats_extractor.extract_stats_from_database(character_data, character_name)
        except Exception as e:
            print(f"Error extracting character stats: {str(e)}")
            # Return fallback stats
            return CharacterStats(
                level=character_data.get("level", 90),
                base_atk=damage_calculator.get_character_base_stats(character_name).get("base_atk", 800),
                flat_atk=311,  # Typical weapon flat ATK
                atk_percent=46.6,  # Typical ATK% sands
                crit_rate=31.1,  # Typical crit rate circlet
                crit_dmg=62.2,  # Typical crit dmg circlet
                elemental_mastery=0,
                elemental_dmg_bonus=46.6,  # Typical elemental goblet
                physical_dmg_bonus=0
            )
    
    def _extract_talent_data(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract talent data from character data."""
        talents_data = character_data.get("talents", [])
        
        # Extract talent levels
        normal_level = 1
        skill_level = 1
        burst_level = 1
        
        for talent in talents_data:
            talent_type = talent.get("type", "").lower()
            level = talent.get("level", 1)
            
            if "normal" in talent_type or "attack" in talent_type:
                normal_level = level
            elif "skill" in talent_type:
                skill_level = level
            elif "burst" in talent_type:
                burst_level = level
        
        # Return talent levels as a simple dictionary
        return {
            "normal_attack": normal_level,
            "elemental_skill": skill_level,
            "elemental_burst": burst_level
        }

    def _calculate_comprehensive_damage(self, character_stats: CharacterStats, character_name: str, team_comp: List[str]) -> Dict[str, Any]:
        """Calculate comprehensive damage using the enhanced damage calculator system with official Genshin Impact formulas."""
        try:
            # Set up enemy stats for calculation (standard level 90 enemy)
            enemy_stats = EnemyStats(
                level=90,
                elemental_res={
                    "pyro": 10.0, "hydro": 10.0, "electro": 10.0, "cryo": 10.0,
                    "anemo": 10.0, "geo": 10.0, "dendro": 10.0
                },
                physical_res=10.0,
                def_reduction=0.0,
                res_reduction={
                    "pyro": 0.0, "hydro": 0.0, "electro": 0.0, "cryo": 0.0,
                    "anemo": 0.0, "geo": 0.0, "dendro": 0.0, "physical": 0.0
                }
            )
            
            # Analyze team reactions if team provided
            reactions = []
            if len(team_comp) > 1:
                reaction_analysis = damage_calculator.analyze_team_reactions(team_comp, character_name)
                reactions = reaction_analysis.get("recommended_reactions", [])
            
            # Calculate comprehensive damage for all abilities using official wiki formulas
            damage_results = {}
            
            # Calculate damage for each ability type using the enhanced comprehensive method
            ability_types = ["normal_attack", "charged_attack", "elemental_skill", "elemental_burst"]
            
            for ability_type in ability_types:
                try:
                    # Use the enhanced comprehensive damage calculation with official formulas
                    ability_damage = damage_calculator.calculate_comprehensive_damage(
                        character_name=character_name,
                        character_stats=character_stats,
                        enemy_stats=enemy_stats,
                        ability_type=ability_type,
                        talent_level=10,  # Assume level 10 talents for optimal calculation
                        reactions=reactions
                    )
                    
                    damage_results[ability_type] = ability_damage
                    
                except Exception as e:
                    print(f"Error calculating {ability_type} damage with enhanced formulas: {str(e)}")
                    # Fallback to basic calculation if enhanced method fails
                    try:
                        fallback_damage = damage_calculator.calculate_character_damage(
                            character_name=character_name,
                            character_stats=character_stats,
                            enemy_stats=enemy_stats,
                            reactions=reactions
                        )
                        damage_results[ability_type] = {
                            "base_damage": fallback_damage.get("damage_breakdown", {}).get(ability_type, {}),
                            "calculation_method": "fallback_basic"
                        }
                    except Exception as fallback_error:
                        print(f"Fallback calculation also failed for {ability_type}: {str(fallback_error)}")
                        damage_results[ability_type] = {
                            "error": f"Could not calculate {ability_type} damage",
                            "base_damage": {"average": 0, "crit": 0, "non_crit": 0}
                        }
            
            # Calculate team buffs if applicable
            team_buffs = {}
            if len(team_comp) > 1:
                try:
                    team_members = [char for char in team_comp if char != character_name]
                    team_composition = TeamComposition(
                        main_dps=character_name,
                        sub_dps=team_members[0] if len(team_members) > 0 else None,
                        support1=team_members[1] if len(team_members) > 1 else None,
                        support2=team_members[2] if len(team_members) > 2 else None
                    )
                    
                    character_element = damage_calculator.get_character_element(character_name)
                    team_buffs = team_buff_calculator.calculate_team_buffs(team_composition, character_element)
                except Exception as e:
                    print(f"Error calculating team buffs: {str(e)}")
                    team_buffs = {"error": "Could not calculate team buffs"}
            
            # Create comprehensive damage analysis with enhanced information
            return {
                "damage_breakdown": damage_results,
                "character_element": damage_calculator.get_character_element(character_name),
                "team_buffs": team_buffs,
                "reactions_used": reactions,
                "calculation_method": "official_genshin_wiki_formulas",
                "wiki_reference": "https://genshin-impact.fandom.com/wiki/Damage",
                "formula_accuracy": "Uses exact formulas from official Genshin Impact wiki",
                "damage_formula_components": {
                    "base_dmg": "Scaling Stat × Talent Multiplier",
                    "base_dmg_multiplier": "Amplifying reaction multipliers (Vaporize/Melt)",
                    "additive_base_dmg_bonus": "Flat damage additions",
                    "dmg_bonus": "Elemental/Physical damage bonuses",
                    "def_multiplier": "(Char Level × 5 + 500) / ((Char Level × 5 + 500) + (Enemy Level × 5 + 500) × (1 - DEF Reduction))",
                    "res_multiplier": "Resistance formula with three cases based on effective resistance"
                },
                "enhanced_features": {
                    "crit_calculations": "Proper crit rate capping at 100% and accurate average damage",
                    "reaction_formulas": "Official EM scaling formulas for both amplifying and transformative reactions",
                    "resistance_handling": "Three-tier resistance formula with negative resistance support",
                    "defense_calculation": "Official level-based defense formula with reduction support"
                }
            }
            
        except Exception as e:
            print(f"Error in comprehensive damage calculation: {str(e)}")
            return {
                "error": f"Could not calculate damage using official formulas: {str(e)}",
                "damage_breakdown": {},
                "character_element": "Unknown",
                "calculation_method": "failed_official_formulas"
            }

    def _analyze_build_efficiency(self, character_data: Dict[str, Any], character_stats: CharacterStats) -> Dict[str, Any]:
        """Analyze build efficiency using artifact sets and Bond of Life systems."""
        try:
            analysis = {
                "artifact_analysis": {},
                "bond_of_life_analysis": {},
                "stat_efficiency": {},
                "recommendations": []
            }
            
            # Analyze artifact sets
            artifacts = character_data.get("artifacts", [])
            if artifacts:
                try:
                    set_analysis = artifact_set_calculator.analyze_equipped_sets(artifacts)
                    analysis["artifact_analysis"] = {
                        "active_sets": set_analysis.get("set_counts", {}),
                        "active_bonuses": set_analysis.get("active_bonuses", []),
                        "total_sets": set_analysis.get("total_active_sets", 0),
                        "efficiency_score": min(100, set_analysis.get("total_active_sets", 0) * 25)
                    }
                except Exception as e:
                    print(f"Error analyzing artifact sets: {str(e)}")
                    analysis["artifact_analysis"] = {"error": "Could not analyze artifact sets"}
            
            # Analyze Bond of Life if applicable
            character_name = character_data.get("name", "Unknown")
            try:
                bond_recommendations = bond_of_life_system.get_bond_of_life_recommendations(character_name)
                if bond_recommendations.get("has_bond_of_life", False):
                    analysis["bond_of_life_analysis"] = {
                        "has_bond_of_life": True,
                        "recommendations": bond_recommendations.get("recommendations", []),
                        "artifact_synergy": bond_recommendations.get("artifact_recommendations", [])
                    }
                else:
                    analysis["bond_of_life_analysis"] = {"has_bond_of_life": False}
            except Exception as e:
                print(f"Error analyzing Bond of Life: {str(e)}")
                analysis["bond_of_life_analysis"] = {"error": "Could not analyze Bond of Life"}
            
            # Analyze stat efficiency
            crit_value = character_stats.crit_rate * 2 + character_stats.crit_dmg
            analysis["stat_efficiency"] = {
                "crit_value": round(crit_value, 1),
                "crit_ratio": round(character_stats.crit_dmg / character_stats.crit_rate, 1) if character_stats.crit_rate > 0 else 0,
                "total_atk": int(character_stats.total_atk),
                "elemental_mastery": int(character_stats.elemental_mastery),
                "energy_recharge": round(character_stats.energy_recharge, 1)
            }
            
            # Generate recommendations based on analysis
            recommendations = []
            
            # Crit ratio recommendations
            crit_ratio = analysis["stat_efficiency"]["crit_ratio"]
            if crit_ratio > 2.5:
                recommendations.append({
                    "category": "Crit Stats",
                    "priority": "HIGH",
                    "action": "Increase CRIT Rate - ratio too high",
                    "current_value": f"{crit_ratio:.1f}:1",
                    "target_value": "2:1 ratio"
                })
            elif crit_ratio < 1.5:
                recommendations.append({
                    "category": "Crit Stats", 
                    "priority": "HIGH",
                    "action": "Increase CRIT DMG - ratio too low",
                    "current_value": f"{crit_ratio:.1f}:1",
                    "target_value": "2:1 ratio"
                })
            
            # Crit rate recommendations
            if character_stats.crit_rate < 50:
                recommendations.append({
                    "category": "Crit Rate",
                    "priority": "MEDIUM",
                    "action": "Increase CRIT Rate for consistency",
                    "current_value": f"{character_stats.crit_rate:.1f}%",
                    "target_value": "60-70%"
                })
            
            # Artifact set recommendations
            if analysis["artifact_analysis"].get("total_sets", 0) < 2:
                recommendations.append({
                    "category": "Artifact Sets",
                    "priority": "HIGH", 
                    "action": "Complete artifact set bonuses",
                    "current_value": f"{analysis['artifact_analysis'].get('total_sets', 0)} sets",
                    "target_value": "2+ complete sets"
                })
            
            analysis["recommendations"] = recommendations
            
            return analysis
            
        except Exception as e:
            print(f"Error in build efficiency analysis: {str(e)}")
            return {
                "error": f"Could not analyze build efficiency: {str(e)}",
                "artifact_analysis": {},
                "bond_of_life_analysis": {},
                "stat_efficiency": {},
                "recommendations": []
            }

    def _calculate_artifact_stats(self, artifacts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total stats from artifacts using new Enka format."""
        total_stats = {
            "flat_atk": 0, "atk_percent": 0, "flat_hp": 0, "hp_percent": 0,
            "flat_def": 0, "def_percent": 0, "crit_rate": 0, "crit_dmg": 0,
            "elemental_mastery": 0, "energy_recharge": 0, "healing_bonus": 0,
            "pyro_dmg": 0, "hydro_dmg": 0, "electro_dmg": 0, "cryo_dmg": 0,
            "anemo_dmg": 0, "geo_dmg": 0, "dendro_dmg": 0, "physical_dmg": 0
        }
        
        for artifact in artifacts:
            # Process main stat
            main_stat = artifact.get("mainStat", {})
            if main_stat:
                stat_name = self._normalize_stat_name(main_stat.get("name", ""))
                stat_value = main_stat.get("value", 0)
                if stat_name in total_stats:
                    total_stats[stat_name] += stat_value
            
            # Process substats
            sub_stats = artifact.get("subStats", [])
            for sub_stat in sub_stats:
                stat_name = self._normalize_stat_name(sub_stat.get("name", ""))
                stat_value = sub_stat.get("value", 0)
                if stat_name in total_stats:
                    total_stats[stat_name] += stat_value
        
        return total_stats
    
    def _calculate_weapon_stats(self, weapon: Dict[str, Any]) -> Dict[str, float]:
        """Calculate stats from weapon using new Enka format."""
        weapon_stats = {
            "base_atk": 0, "atk_percent": 0, "crit_rate": 0, "crit_dmg": 0,
            "elemental_mastery": 0, "energy_recharge": 0, "hp_percent": 0,
            "def_percent": 0, "physical_dmg": 0
        }
        
        if not weapon:
            return weapon_stats
        
        # Get base attack
        weapon_stats["base_atk"] = weapon.get("baseAttack", 0)
        
        # Get sub stat
        sub_stat = weapon.get("subStat", {})
        if sub_stat:
            stat_name = self._normalize_stat_name(sub_stat.get("name", ""))
            stat_value = sub_stat.get("value", 0)
            if stat_name in weapon_stats:
                weapon_stats[stat_name] = stat_value
        
        return weapon_stats
    
    def _normalize_stat_name(self, stat_name: str) -> str:
        """Normalize stat names from Enka format to internal format."""
        stat_mapping = {
            "HP": "flat_hp",
            "HP%": "hp_percent",
            "ATK": "flat_atk", 
            "ATK%": "atk_percent",
            "DEF": "flat_def",
            "DEF%": "def_percent",
            "CRIT Rate": "crit_rate",
            "CRIT DMG": "crit_dmg",
            "Elemental Mastery": "elemental_mastery",
            "Energy Recharge": "energy_recharge",
            "Healing Bonus": "healing_bonus",
            "Pyro DMG Bonus": "pyro_dmg",
            "Hydro DMG Bonus": "hydro_dmg",
            "Electro DMG Bonus": "electro_dmg",
            "Cryo DMG Bonus": "cryo_dmg",
            "Anemo DMG Bonus": "anemo_dmg",
            "Geo DMG Bonus": "geo_dmg",
            "Dendro DMG Bonus": "dendro_dmg",
            "Physical DMG Bonus": "physical_dmg"
        }
        
        return stat_mapping.get(stat_name, stat_name.lower().replace(" ", "_"))

    async def _generate_ai_recommendations(self, character_name: str, 
                                         analysis: Dict[str, Any],
                                         character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered recommendations based on mathematical analysis."""
        
        # Create a comprehensive prompt with the mathematical analysis
        prompt = f"""
        Based on the detailed mathematical damage analysis for {character_name}, provide comprehensive build optimization recommendations.
        
        IMPORTANT: The crit_rate and crit_dmg values shown are TOTAL values that already include all sources:
        - Base character stats + artifacts + weapon + bonuses
        - Do NOT suggest adding individual artifact crit values together
        
        MATHEMATICAL ANALYSIS RESULTS:
        {self._json_safe_serialize(analysis)}
        
        CURRENT CHARACTER DATA:
        {self._json_safe_serialize(character_data)}
        
        Please provide:
        1. **Priority Improvements**: What should the player focus on first for maximum damage gain?
        2. **Artifact Optimization**: Specific artifact main stats and substat priorities
        3. **Weapon Recommendations**: Best weapons for this build and playstyle
        4. **Team Synergy**: How this character fits in team compositions
        5. **Damage Rotation**: Optimal skill rotation for maximum DPS
        6. **Investment Priority**: What to upgrade first (talents, artifacts, weapon)
        7. **Expected Improvements**: Quantified damage increases from each recommendation
        
        Format your response as a structured guide that's easy to follow.
        """
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return {
                "recommendations": response.content,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            raise Exception(f"Failed to generate AI recommendations: {str(e)}")

    def _create_analysis_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a concise summary of the analysis."""
        if "error" in analysis:
            return {"error": analysis["error"]}
        
        build_analysis = analysis.get("build_analysis", {})
        damage_breakdown = analysis.get("damage_breakdown", {})
        summary = analysis.get("summary", {})
        
        # Get normal attack damage as primary metric
        na_damage = damage_breakdown.get("normal_attack", {})
        
        return {
            "overall_rating": summary.get("overall_rating", "0/100"),
            "crit_value": summary.get("crit_value", "0"),
            "total_attack": summary.get("total_attack", "0"),
            "average_na_damage": f"{na_damage.get('average', 0):.0f}",
            "crit_na_damage": f"{na_damage.get('crit', 0):.0f}",
            "primary_issues": len(analysis.get("recommendations", [])),
            "build_efficiency": summary.get("build_efficiency", "Unknown"),
            "primary_damage_source": summary.get("primary_damage_source", "unknown")
        }

    def _create_action_plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a prioritized action plan based on the analysis."""
        if "error" in analysis:
            return []
        
        recommendations = analysis.get("recommendations", [])
        action_plan = []
        
        for i, rec in enumerate(recommendations[:5]):  # Top 5 recommendations
            action_plan.append({
                "step": i + 1,
                "priority": rec.get("priority", "MEDIUM"),
                "category": rec.get("category", "General"),
                "action": rec.get("action", rec.get("recommendation", "")),
                "expected_improvement": rec.get("expected_improvement", "Unknown"),
                "current_value": rec.get("current_value", "N/A")
            })
        
        return action_plan

    async def calculate_damage(self, character_data: Dict[str, Any], 
                             team_comp: List[str], 
                             enemy_type: str = "Standard") -> Dict[str, Any]:
        """Calculate theoretical damage for a character using comprehensive damage calculators."""
        try:
            character_name = character_data.get("name", "Unknown")
            
            # Check cache
            cache_key = f"damage_calc_{character_name}_{'-'.join(team_comp)}_{enemy_type}"
            cached_result = await Cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Extract character stats using the stats extractor
            character_stats = stats_extractor.extract_stats_from_database(character_data, character_name)
            
            # Set up enemy stats based on enemy type
            enemy_level = 90 if enemy_type.lower() in ["boss", "elite"] else 85
            enemy_resistances = {
                "pyro": 10.0, "hydro": 10.0, "electro": 10.0, "cryo": 10.0,
                "anemo": 10.0, "geo": 10.0, "dendro": 10.0
            }
            
            # Adjust resistances based on enemy type
            if enemy_type.lower() == "boss":
                # Bosses typically have higher resistances
                for element in enemy_resistances:
                    enemy_resistances[element] = 25.0
            elif enemy_type.lower() == "elite":
                # Elite enemies have moderate resistances
                for element in enemy_resistances:
                    enemy_resistances[element] = 15.0
            
            enemy_stats = EnemyStats(
                level=enemy_level,
                elemental_res=enemy_resistances,
                physical_res=10.0,
                def_reduction=0.0
            )
            
            # Analyze team reactions
            reactions = []
            team_analysis = {}
            if len(team_comp) > 1:
                reaction_analysis = damage_calculator.analyze_team_reactions(team_comp, character_name)
                reactions = reaction_analysis.get("recommended_reactions", [])
                team_analysis = {
                    "possible_reactions": reaction_analysis.get("possible_reactions", []),
                    "team_synergy": reaction_analysis.get("team_synergy", {}),
                    "elemental_coverage": reaction_analysis.get("elemental_coverage", {})
                }
            
            # Calculate base damage (no team buffs)
            base_damage_result = damage_calculator.calculate_character_damage(
                character_name=character_name,
                character_stats=character_stats,
                enemy_stats=enemy_stats,
                reactions=reactions
            )
            
            # Calculate team buffs if team composition provided
            team_buffs_result = {}
            buffed_damage_result = None
            
            if len(team_comp) > 1:
                try:
                    # Set up team composition
                    team_members = [char for char in team_comp if char != character_name]
                    team_composition = TeamComposition(
                        main_dps=character_name,
                        sub_dps=team_members[0] if len(team_members) > 0 else None,
                        support1=team_members[1] if len(team_members) > 1 else None,
                        support2=team_members[2] if len(team_members) > 2 else None
                    )
                    
                    character_element = damage_calculator.get_character_element(character_name)
                    team_buffs_result = team_buff_calculator.calculate_team_buffs(team_composition, character_element)
                    
                    # Apply team buffs to character stats
                    buffed_stats = character_stats
                    total_multipliers = team_buffs_result.get("total_multipliers", {})
                    
                    # Apply buffs (simplified application)
                    if total_multipliers.get("atk_percent", 0) > 0:
                        buffed_stats.atk_percent += total_multipliers["atk_percent"]
                    if total_multipliers.get("elemental_dmg_bonus", 0) > 0:
                        buffed_stats.elemental_dmg_bonus += total_multipliers["elemental_dmg_bonus"]
                    if total_multipliers.get("crit_rate", 0) > 0:
                        buffed_stats.crit_rate += total_multipliers["crit_rate"]
                    if total_multipliers.get("crit_dmg", 0) > 0:
                        buffed_stats.crit_dmg += total_multipliers["crit_dmg"]
                    
                    # Calculate buffed damage
                    buffed_damage_result = damage_calculator.calculate_character_damage(
                        character_name=character_name,
                        character_stats=buffed_stats,
                        enemy_stats=enemy_stats,
                        reactions=reactions
                    )
                    
                except Exception as e:
                    print(f"Error calculating team buffs: {str(e)}")
                    team_buffs_result = {"error": "Could not calculate team buffs"}
            
            # Analyze artifact sets
            artifact_analysis = {}
            artifacts = character_data.get("artifacts", [])
            if artifacts:
                try:
                    set_analysis = artifact_set_calculator.analyze_equipped_sets(artifacts)
                    artifact_analysis = {
                        "active_sets": set_analysis.get("set_counts", {}),
                        "active_bonuses": set_analysis.get("active_bonuses", []),
                        "total_sets": set_analysis.get("total_active_sets", 0)
                    }
                except Exception as e:
                    print(f"Error analyzing artifacts: {str(e)}")
                    artifact_analysis = {"error": "Could not analyze artifacts"}
            
            # Build comprehensive result
            result = {
                "character": character_name,
                "team": team_comp,
                "enemy_type": enemy_type,
                "base_damage": {
                    "damage_breakdown": base_damage_result.get("damage_breakdown", {}),
                    "element": base_damage_result.get("element", "Unknown"),
                    "total_stats": {
                        "total_atk": int(character_stats.total_atk),
                        "crit_rate": round(character_stats.crit_rate, 1),
                        "crit_dmg": round(character_stats.crit_dmg, 1),
                        "elemental_mastery": int(character_stats.elemental_mastery)
                    }
                },
                "team_analysis": team_analysis,
                "team_buffs": team_buffs_result,
                "buffed_damage": buffed_damage_result.get("damage_breakdown", {}) if buffed_damage_result else None,
                "artifact_analysis": artifact_analysis,
                "enemy_info": {
                    "level": enemy_stats.level,
                    "type": enemy_type,
                    "resistances": enemy_stats.elemental_res
                },
                "calculation_method": "comprehensive_mathematical_formulas",
                "summary": self._create_damage_summary(base_damage_result, buffed_damage_result, team_buffs_result)
            }
            
            # Cache for 6 hours (shorter than before since this is more dynamic)
            await Cache.set(cache_key, result, ttl=21600)
            
            return result
            
        except Exception as e:
            print(f"Error calculating damage: {str(e)}")
            raise Exception(f"Failed to calculate damage: {str(e)}")
    
    def _create_damage_summary(self, base_damage: Dict[str, Any], buffed_damage: Dict[str, Any] = None, team_buffs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a summary of damage calculations."""
        try:
            base_breakdown = base_damage.get("damage_breakdown", {})
            
            # Find highest damage ability
            max_damage = 0
            best_ability = "normal_attack"
            
            for ability, data in base_breakdown.items():
                if isinstance(data, dict) and "average" in data:
                    if data["average"] > max_damage:
                        max_damage = data["average"]
                        best_ability = ability
            
            summary = {
                "primary_damage_source": best_ability,
                "max_single_hit": int(max_damage),
                "element": base_damage.get("element", "Unknown"),
                "has_team_buffs": buffed_damage is not None,
                "team_synergy_score": team_buffs.get("synergy_score", 0) if team_buffs else 0
            }
            
            # Add damage increase if buffed damage available
            if buffed_damage and best_ability in buffed_damage.get("damage_breakdown", {}):
                buffed_max = buffed_damage["damage_breakdown"][best_ability].get("average", 0)
                if max_damage > 0:
                    damage_increase = ((buffed_max / max_damage) - 1) * 100
                    summary["damage_increase_percent"] = round(damage_increase, 1)
                    summary["buffed_max_damage"] = int(buffed_max)
            
            return summary
            
        except Exception as e:
            print(f"Error creating damage summary: {str(e)}")
            return {"error": "Could not create summary"}

    async def get_build_recommendation(self, character_name: str, uid: Optional[int] = None, include_current_build: bool = False) -> Dict[str, Any]:
        """Get comprehensive character build recommendations using damage calculators."""
        try:
            # Get character data if UID provided
            current_build_analysis = None
            character_data = None
            
            if uid and include_current_build:
                try:
                    character_data = await CharacterData.get_character_by_name(uid, character_name)
                    if character_data:
                        current_build_analysis = await self.analyze_character_build_advanced(character_name, character_data, uid)
                except Exception as e:
                    print(f"Error getting current build: {str(e)}")
            
            # Search for build guides
            search_results = await self._search_character_builds(character_name)
            
            # Get character element for recommendations
            character_element = damage_calculator.get_character_element(character_name)
            
            # Get artifact set recommendations
            artifact_recommendations = artifact_set_calculator.get_set_recommendations(character_name, character_element)
            
            # Get Bond of Life recommendations if applicable
            bond_of_life_recommendations = bond_of_life_system.get_bond_of_life_recommendations(character_name)
            
            # Calculate theoretical optimal stats for comparison
            optimal_stats = self._calculate_optimal_stats(character_name, character_element)
            
            # Generate comprehensive recommendations
            recommendations = {
                "character_name": character_name,
                "element": character_element,
                "artifact_recommendations": {
                    "primary_sets": artifact_recommendations.get("recommended_sets", [])[:3],
                    "alternative_sets": artifact_recommendations.get("alternative_sets", [])[:2],
                    "main_stats": {
                        "sands": artifact_recommendations.get("main_stats", {}).get("sands", ["ATK%"]),
                        "goblet": artifact_recommendations.get("main_stats", {}).get("goblet", [f"{character_element.title()} DMG%"]),
                        "circlet": artifact_recommendations.get("main_stats", {}).get("circlet", ["CRIT Rate%", "CRIT DMG%"])
                    },
                    "substat_priority": artifact_recommendations.get("substat_priority", ["CRIT Rate%", "CRIT DMG%", "ATK%", "Elemental Mastery"])
                },
                "weapon_recommendations": self._get_weapon_recommendations(character_name, character_element),
                "talent_priority": self._get_talent_priority(character_name),
                "team_synergies": self._get_team_synergies(character_name, character_element),
                "optimal_stats": optimal_stats,
                "bond_of_life": bond_of_life_recommendations if bond_of_life_recommendations.get("has_bond_of_life") else None,
                "build_variants": self._get_build_variants(character_name, character_element),
                "investment_priority": self._get_investment_priority(character_name),
                "current_build_analysis": current_build_analysis,
                "sources": [result["link"] for result in search_results[:3]],
                "calculation_method": "comprehensive_with_damage_calculators"
            }
            
            # Generate AI-enhanced recommendations
            ai_enhanced_recommendations = await self._generate_ai_enhanced_recommendations(
                character_name, recommendations, search_results
            )
            
            # Combine all recommendations
            final_result = {
                "character": character_name,
                "recommendations": ai_enhanced_recommendations,
                "detailed_analysis": recommendations,
                "sources": [result["link"] for result in search_results[:3]],
                "current_build_analysis": current_build_analysis
            }
            
            # Cache for 12 hours
            cache_key = f"enhanced_build_advice_{character_name}_{uid if uid else 'general'}"
            await Cache.set(cache_key, final_result, ttl=43200)
            
            return final_result
            
        except Exception as e:
            print(f"Error getting enhanced build recommendation: {str(e)}")
            raise Exception(f"Failed to get build recommendations: {str(e)}")
    
    def _calculate_optimal_stats(self, character_name: str, element: str) -> Dict[str, Any]:
        """Calculate optimal stat targets for a character based on element and general principles."""
        try:
            # Base optimal stats for most characters
            optimal_stats = {
                "crit_rate": 70.0,  # Target 70% crit rate
                "crit_dmg": 140.0,  # Target 140% crit damage
                "atk_percent": 50.0,  # Target 50% ATK bonus from artifacts
                "elemental_mastery": 100.0,  # Base EM target
                "energy_recharge": 120.0,  # Base ER target
                "elemental_dmg_bonus": 46.6  # Goblet main stat
            }
            
            # Element-based adjustments (more general approach)
            element_lower = element.lower()
            
            # Anemo characters typically focus on EM for Swirl reactions
            if element_lower == "anemo":
                optimal_stats["elemental_mastery"] = 800.0
                optimal_stats["crit_rate"] = 50.0
                optimal_stats["crit_dmg"] = 100.0
            
            # Dendro characters often benefit from EM for reactions
            elif element_lower == "dendro":
                optimal_stats["elemental_mastery"] = 600.0
            
            # Geo characters may benefit from DEF scaling (some characters)
            elif element_lower == "geo":
                optimal_stats["def_percent"] = 30.0
            
            return {
                "targets": optimal_stats,
                "priority_order": ["CRIT Rate%", "CRIT DMG%", "ATK%", "Elemental Mastery", "Energy Recharge%"],
                "notes": f"General optimal stat targets for {character_name} ({element} element)",
                "element_focus": element_lower,
                "customization_note": "These are general targets. Specific characters may have different optimal builds based on their kit and role."
            }
            
        except Exception as e:
            print(f"Error calculating optimal stats: {str(e)}")
            return {"error": "Could not calculate optimal stats"}
    
    def _get_weapon_recommendations(self, character_name: str, element: str) -> Dict[str, List[str]]:
        """Get general weapon recommendations based on element and weapon type."""
        # General weapon recommendations by rarity
        weapon_recommendations = {
            "5_star": ["Signature weapons", "Universal 5-star options", "Element-matching weapons"],
            "4_star": ["Event weapons", "Craftable options", "Gacha 4-star weapons"],
            "3_star": ["F2P options", "Early game weapons"]
        }
        
        # Add element-specific notes
        element_notes = {
            "pyro": "Focus on ATK% and CRIT substats",
            "hydro": "Consider EM for reaction teams",
            "electro": "Energy Recharge often important",
            "cryo": "CRIT Rate valuable for Cryo resonance",
            "anemo": "Elemental Mastery for Swirl damage",
            "geo": "ATK% or DEF% depending on character",
            "dendro": "Elemental Mastery for reaction damage"
        }
        
        weapon_recommendations["element_focus"] = element_notes.get(element.lower(), "Standard DPS stats")
        weapon_recommendations["general_advice"] = "Check character's scaling stats and team role for optimal weapon choice"
        
        return weapon_recommendations
    
    def _get_talent_priority(self, character_name: str) -> Dict[str, Any]:
        """Get general talent leveling priority."""
        # Default priority for most DPS characters
        priority = ["Elemental Burst", "Elemental Skill", "Normal Attack"]
        
        return {
            "priority_order": priority,
            "general_advice": [
                "Level the talent that contributes most to your character's role",
                "DPS characters: Focus on their main damage source first",
                "Support characters: Prioritize utility talents (usually Burst or Skill)",
                "Check character's kit to determine which talent scales best"
            ],
            "investment_levels": {
                "minimum": "Level 6 for all important talents",
                "recommended": "Level 8 for main damage talents",
                "optimal": "Level 9-10 for main DPS characters"
            }
        }
    
    def _get_team_synergies(self, character_name: str, element: str) -> Dict[str, List[str]]:
        """Get general team synergy recommendations based on element."""
        synergies = {
            "elemental_resonance": [],
            "reaction_partners": [],
            "support_options": [],
            "general_advice": []
        }
        
        element_lower = element.lower()
        
        # Element-based synergies
        if element_lower == "pyro":
            synergies["elemental_resonance"] = ["Pyro Resonance: +25% ATK"]
            synergies["reaction_partners"] = ["Hydro (Vaporize)", "Cryo (Melt)", "Electro (Overloaded)"]
        elif element_lower == "hydro":
            synergies["elemental_resonance"] = ["Hydro Resonance: +25% HP"]
            synergies["reaction_partners"] = ["Pyro (Vaporize)", "Electro (Electro-Charged)", "Cryo (Freeze)"]
        elif element_lower == "electro":
            synergies["elemental_resonance"] = ["Electro Resonance: Energy generation"]
            synergies["reaction_partners"] = ["Hydro (Electro-Charged)", "Pyro (Overloaded)", "Cryo (Superconduct)"]
        elif element_lower == "cryo":
            synergies["elemental_resonance"] = ["Cryo Resonance: +15% CRIT Rate"]
            synergies["reaction_partners"] = ["Hydro (Freeze)", "Pyro (Melt)", "Electro (Superconduct)"]
        elif element_lower == "anemo":
            synergies["elemental_resonance"] = ["Anemo Resonance: Reduced stamina consumption"]
            synergies["reaction_partners"] = ["Any element (Swirl)", "VV artifact set for resistance shred"]
        elif element_lower == "geo":
            synergies["elemental_resonance"] = ["Geo Resonance: +15% DMG, +15% Shield Strength"]
            synergies["reaction_partners"] = ["Crystallize shields with any element"]
        elif element_lower == "dendro":
            synergies["elemental_resonance"] = ["Dendro Resonance: EM and reaction bonuses"]
            synergies["reaction_partners"] = ["Electro (Quicken)", "Hydro (Bloom)", "Pyro (Burning)"]
        
        synergies["general_advice"] = [
            "Consider team roles: DPS, Sub-DPS, Support, Healer",
            "Energy management is crucial for burst-dependent characters",
            "Elemental reactions can significantly increase damage",
            "Shield or healing support recommended for survivability"
        ]
        
        return synergies
    
    def _get_build_variants(self, character_name: str, element: str) -> List[Dict[str, Any]]:
        """Get general build variants based on element and common roles."""
        variants = []
        
        element_lower = element.lower()
        
        # DPS variant (common for most characters)
        variants.append({
            "name": "Main DPS",
            "focus": "Maximum damage output",
            "artifacts": ["Element-specific damage sets", "Universal DPS sets"],
            "main_stats": {"sands": "ATK%", "goblet": f"{element} DMG%", "circlet": "CRIT Rate/DMG"},
            "description": "Focused on personal damage and field time"
        })
        
        # Support variant (if applicable)
        if element_lower in ["anemo", "geo", "dendro"]:
            variants.append({
                "name": "Support",
                "focus": "Team utility and reactions",
                "artifacts": ["Element-specific support sets", "Energy Recharge sets"],
                "main_stats": {"sands": "ER% or EM", "goblet": f"{element} DMG% or EM", "circlet": "CRIT or EM"},
                "description": "Focused on supporting team and enabling reactions"
            })
        
        # Elemental Mastery variant (for reaction-focused builds)
        if element_lower in ["anemo", "dendro", "electro"]:
            variants.append({
                "name": "Elemental Mastery",
                "focus": "Reaction damage",
                "artifacts": ["EM-focused sets", "Reaction damage sets"],
                "main_stats": {"sands": "EM", "goblet": "EM", "circlet": "EM"},
                "description": "Maximizes elemental reaction damage"
            })
        
        return variants
    
    def _get_investment_priority(self, character_name: str) -> List[Dict[str, str]]:
        """Get investment priority order for a character."""
        return [
            {"priority": "HIGH", "item": "Weapon Level 90", "reason": "Highest ATK increase"},
            {"priority": "HIGH", "item": "Artifact Main Stats", "reason": "Major stat increases"},
            {"priority": "MEDIUM", "item": "Talent Levels 8+", "reason": "Significant damage increase"},
            {"priority": "MEDIUM", "item": "Artifact Substats", "reason": "Fine-tuning optimization"},
            {"priority": "LOW", "item": "Constellation", "reason": "Luxury upgrades"}
        ]
    
    async def _generate_ai_enhanced_recommendations(self, character_name: str, recommendations: Dict[str, Any], search_results: List[Dict[str, Any]]) -> str:
        """Generate AI-enhanced recommendations using the LLM."""
        try:
            enhanced_prompt = f"""You are a Genshin Impact build optimization expert. Based on the comprehensive analysis and current meta information, provide detailed build recommendations for {character_name}.

Character Analysis:
{self._json_safe_serialize(recommendations)}

Latest Build Guides:
{self._json_safe_serialize(search_results[:2])}

Provide a comprehensive build guide including:
1. Optimal artifact sets and why they work
2. Main stat and substat priorities
3. Weapon recommendations by rarity
4. Talent leveling order
5. Team composition suggestions
6. Common mistakes to avoid
7. Investment priority order

Make the recommendations practical and explain the reasoning behind each choice."""

            response = await self.llm.ainvoke([HumanMessage(content=enhanced_prompt)])
            return response.content
            
        except Exception as e:
            print(f"Error generating AI recommendations: {str(e)}")
            return f"Comprehensive build recommendations for {character_name} based on current meta analysis."

    async def _search_character_builds(self, character_name: str) -> List[Dict[str, Any]]:
        """Search for character build guides using Google Custom Search."""
        try:
            # Search for character build guides
            search_query = f"Genshin Impact {character_name} build guide artifacts weapons"
            
            search_results = self.cse_service.list(
                q=search_query,
                cx=settings.google_cse_id,
                num=5
            ).execute()
            
            results = []
            for item in search_results.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("displayLink", "")
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching for character builds: {str(e)}")
            # Return fallback results
            return [
                {
                    "title": f"{character_name} Build Guide",
                    "link": "https://genshin-impact.fandom.com",
                    "snippet": f"Comprehensive {character_name} build guide with artifacts and weapons",
                    "source": "genshin-impact.fandom.com"
                }
            ]

    async def answer_question(self, question: str, uid: Optional[int] = None) -> Dict[str, Any]:
        """
        Answer Genshin Impact related questions using AI with enhanced analysis capabilities.
        
        This method now has access to:
        - Comprehensive damage calculation systems
        - Artifact set bonus analysis
        - Bond of Life mechanics understanding
        - Team synergy and reaction analysis
        - Mathematical accuracy for build recommendations
        - Thorough web search before answering
        - Complete character data from database
        """
        try:
            # Enhanced Genshin Impact question detection
            if not self._is_genshin_question(question):
                return {
                    "question": question,
                    "answer": "I can only help with Genshin Impact related questions. Please ask about characters, builds, teams, artifacts, weapons, or gameplay mechanics.",
                    "context_used": False,
                    "character_data_used": False,
                    "characters_analyzed": 0,
                    "web_search_performed": False
                }
            
            # Get comprehensive user data if UID provided
            player_data = {}
            character_stats = {}
            available_characters = []
            full_character_data = {}
            
            if uid:
                try:
                    from database import UserProfile, CharacterData
                    user = await UserProfile.get(uid)
                    if user:
                        player_data = {
                            "profile": user.get("profile_data", {}),
                            "character_count": len(user.get("characters", [])),
                            "uid": uid
                        }
                        
                        # Get comprehensive character data for context
                        characters = await CharacterData.get_all_user_characters(uid)
                        character_stats = {}
                        available_characters = []
                        full_character_data = {}
                        
                        for char in characters:
                            char_name = char.get("name", "Unknown")
                            available_characters.append(char_name)
                            
                            # Store full character data for detailed analysis
                            full_character_data[char_name] = char
                            
                            # Create comprehensive character summary
                            weapon_info = char.get("weapon", {})
                            artifacts = char.get("artifacts", [])
                            talents = char.get("talents", [])
                            stats = char.get("stats", {})
                            
                            character_stats[char_name] = {
                                "name": char_name,
                                "avatarId": char.get("avatarId", 0),
                                "element": char.get("element", "Unknown"),
                                "rarity": char.get("rarity", 5),
                                "level": char.get("level", 1),
                                "ascension": char.get("ascension", 0),
                                "constellation": char.get("constellation", 0),
                                "friendship": char.get("friendship", 1),
                                "weapon": {
                                    "name": weapon_info.get("name", "Unknown"),
                                    "type": weapon_info.get("weaponType", "Unknown"),
                                    "level": weapon_info.get("level", 1),
                                    "refinement": weapon_info.get("refinement", 1),
                                    "rarity": weapon_info.get("rarity", 3),
                                    "baseAttack": weapon_info.get("baseAttack", 0),
                                    "subStat": weapon_info.get("subStat", {})
                                },
                                "artifacts": {
                                    "count": len(artifacts),
                                    "sets": self._analyze_artifact_sets(artifacts),
                                    "main_stats": self._extract_artifact_main_stats(artifacts)
                                },
                                "talents": {
                                    "count": len([t for t in talents if t.get("type") == "skill"]),
                                    "levels": self._extract_talent_levels(talents)
                                },
                                "stats": {
                                    "total_hp": stats.get("current_hp", stats.get("max_hp", 0)),
                                    "total_atk": stats.get("atk", 0) + stats.get("base_atk", 0),
                                    "total_def": stats.get("def", 0) + stats.get("base_def", 0),
                                    "crit_rate": stats.get("crit_rate", 5.0),
                                    "crit_dmg": stats.get("crit_dmg", 50.0),
                                    "elemental_mastery": stats.get("elemental_mastery", 0),
                                    "energy_recharge": stats.get("energy_recharge", 100.0),
                                    "elemental_dmg_bonus": self._get_elemental_dmg_bonus(stats, char.get("element", "Unknown"))
                                }
                            }
                        
                        # Add character roster summary to player data
                        player_data["available_characters"] = available_characters
                        player_data["character_details"] = character_stats
                        player_data["full_character_data"] = full_character_data
                        
                except Exception as e:
                    print(f"Error getting user data: {str(e)}")
            
            # Enhanced context for team composition questions
            team_context = ""
            if any(phrase in question.lower() for phrase in ["team for", "good team", "team comp", "characters i have", "among the characters"]):
                if available_characters:
                    team_context = f"""
                    
                    PLAYER'S AVAILABLE CHARACTERS:
                    {', '.join(available_characters)}
                    
                    DETAILED CHARACTER ANALYSIS:
                    {self._json_safe_serialize(character_stats)}
                    
                    TEAM BUILDING INSTRUCTIONS:
                    - Prioritize characters from the player's roster
                    - Suggest multiple team options using available characters
                    - If the player doesn't have optimal characters, suggest alternatives from their roster
                    - Explain why each character is chosen and their role in the team
                    - Provide rotation guides and synergy explanations
                    - Consider character levels, constellations, and weapon quality
                    - Analyze artifact sets and stat distributions for team synergy
                    """
                else:
                    team_context = """
                    
                    NOTE: Player's character roster not available. Provide general team recommendations and mention that having specific characters would be ideal.
                    """
            
            # ENHANCED WEB SEARCH - Search thoroughly before answering
            search_results = []
            character_mentioned = None
            
            try:
                # Extract character name from question for targeted search
                question_lower = question.lower()
                
                # Get character names dynamically from database if available
                dynamic_character_names = available_characters if available_characters else []
                
                # Fallback character list (only used if no database access)
                fallback_character_names = [
                    "amber", "kaeya", "lisa", "barbara", "razor", "xiangling", "beidou",
                    "xingqiu", "ningguang", "fischl", "bennett", "noelle", "chongyun",
                    "sucrose", "jean", "diluc", "qiqi", "mona", "keqing", "venti", "klee",
                    "albedo", "rosaria", "eula", "mika", "zhongli", "tartaglia", "childe",
                    "xinyan", "ganyu", "xiao", "hu tao", "hutao", "yanfei", "baizhu", "yaoyao",
                    "kazuha", "kaedehara kazuha", "ayaka", "kamisato ayaka", "yoimiya",
                    "sayu", "raiden shogun", "raiden", "ei", "kokomi", "sangonomiya kokomi",
                    "gorou", "sara", "kujou sara", "itto", "arataki itto", "yae miko",
                    "yae", "heizou", "shikanoin heizou", "shinobu", "kuki shinobu",
                    "ayato", "kamisato ayato", "kirara", "tighnari", "collei", "dori", 
                    "nilou", "cyno", "candace", "nahida", "layla", "faruzan", "wanderer",
                    "scaramouche", "alhaitham", "dehya", "kaveh", "lynette", "lyney", 
                    "freminet", "neuvillette", "wriothesley", "charlotte", "furina", 
                    "chevreuse", "navia", "gaming", "xianyun", "chiori", "arlecchino", 
                    "sethos", "clorinde", "sigewinne", "emilie", "kachina", "mualani", 
                    "kinich", "xilonen", "chasca", "ororon", "mavuika", "citlali"
                ]
                
                # Use dynamic character names first, then fallback
                all_character_names = dynamic_character_names + [name for name in fallback_character_names if name not in dynamic_character_names]
                
                # Find mentioned character
                for char_name in all_character_names:
                    if char_name.lower() in question_lower:
                        character_mentioned = char_name
                        break
                
                # Perform multiple targeted searches for comprehensive information
                search_queries = []
                
                if character_mentioned:
                    # Character-specific searches
                    search_queries.extend([
                        f"Genshin Impact {character_mentioned} best team composition 2024",
                        f"Genshin Impact {character_mentioned} build guide artifacts weapons",
                        f"Genshin Impact {character_mentioned} meta teams spiral abyss"
                    ])
                else:
                    # General searches based on question content
                    if any(word in question_lower for word in ["team", "comp", "synergy"]):
                        search_queries.extend([
                            f"Genshin Impact {question} team composition guide",
                            f"Genshin Impact best teams 2024 meta"
                        ])
                    elif any(word in question_lower for word in ["build", "artifact", "weapon"]):
                        search_queries.extend([
                            f"Genshin Impact {question} build guide",
                            f"Genshin Impact artifact recommendations 2024"
                        ])
                    else:
                        search_queries.extend([
                            f"Genshin Impact {question}",
                            f"Genshin Impact guide {question}"
                        ])
                
                # Perform searches (limit to avoid rate limits)
                for search_query in search_queries[:3]:  # Limit to 3 searches
                    try:
                        search_response = self.cse_service.list(
                            q=search_query,
                            cx=settings.google_cse_id,
                            num=3  # Get 3 results per search
                        ).execute()
                        
                        for item in search_response.get("items", []):
                            search_results.append({
                                "title": item.get("title", ""),
                                "snippet": item.get("snippet", ""),
                                "link": item.get("link", ""),
                                "source": item.get("displayLink", ""),
                                "search_query": search_query
                            })
                    except Exception as search_error:
                        print(f"Error in search query '{search_query}': {str(search_error)}")
                        continue
                
            except Exception as e:
                print(f"Error in web search: {str(e)}")
            
            # Create comprehensive context for the AI
            enhanced_context = f"""
            You are a comprehensive Genshin Impact expert with access to mathematical damage calculators, 
            artifact analysis systems, and complete knowledge of all characters and team compositions.
            
            SPECIAL CAPABILITIES:
            - Mathematical damage calculations using actual game formulas
            - Artifact set bonus analysis and optimization
            - Bond of Life mechanics for characters like Arlecchino, Gaming, and Xianyun
            - Team synergy and elemental reaction optimization
            - Character-specific build recommendations with stat targets
            - Access to player's complete character roster with detailed stats
            
            CURRENT CONTEXT:
            - Question Type: {"Team Composition" if any(phrase in question.lower() for phrase in ["team", "comp", "characters"]) else "General Genshin"}
            - Player Data Available: {"Yes" if uid else "No"}
            - Character Roster Available: {"Yes" if available_characters else "No"}
            - Characters Available: {len(available_characters)} characters
            - Web Search Performed: {"Yes" if search_results else "No"}
            - Search Results Found: {len(search_results)} results
            
            {team_context}
            
            COMPREHENSIVE WEB SEARCH RESULTS:
            {self._json_safe_serialize(search_results) if search_results else "No web search results available"}
            
            INSTRUCTIONS:
            1. Use the web search results to provide up-to-date information
            2. Prioritize information from reputable Genshin Impact sources
            3. Combine web search data with player's character roster for personalized advice
            4. Provide specific, actionable recommendations based on current meta
            5. Include rotation guides, stat priorities, and team synergies
            6. Consider character constellations, weapon refinements, and artifact quality
            """
            
            # Generate AI response using the enhanced prompt
            prompt_template = ChatPromptTemplate.from_template(self.general_assistant_prompt)
            formatted_prompt = prompt_template.format(
                player_data=self._json_safe_serialize(player_data),
                character_stats=self._json_safe_serialize(character_stats),
                question=question
            )
            
            # Combine enhanced context with formatted prompt
            full_prompt = f"{enhanced_context}\n\n{formatted_prompt}"
            
            response = await self.llm.ainvoke([HumanMessage(content=full_prompt)])
            
            return {
                "question": question,
                "answer": response.content,
                "context_used": uid is not None and bool(player_data),
                "character_data_used": uid is not None and bool(character_stats),
                "characters_analyzed": len(character_stats) if character_stats else 0,
                "available_characters": available_characters if available_characters else [],
                "team_context_provided": bool(team_context.strip()),
                "web_search_performed": bool(search_results),
                "search_results_count": len(search_results),
                "character_mentioned": character_mentioned,
                "search_sources": list(set([result.get("source", "") for result in search_results])) if search_results else []
            }
            
        except Exception as e:
            print(f"Error answering question: {str(e)}")
            raise Exception(f"Failed to answer question: {str(e)}")

    def _analyze_artifact_sets(self, artifacts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze artifact sets from character data."""
        set_counts = {}
        for artifact in artifacts:
            set_name = artifact.get("setName", "Unknown")
            if set_name != "Unknown":
                set_counts[set_name] = set_counts.get(set_name, 0) + 1
        return set_counts

    def _extract_artifact_main_stats(self, artifacts: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract main stats from artifacts."""
        main_stats = {}
        for artifact in artifacts:
            artifact_type = artifact.get("type", "unknown")
            main_stat = artifact.get("mainStat", {})
            main_stats[artifact_type] = main_stat.get("name", "Unknown")
        return main_stats

    def _extract_talent_levels(self, talents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract talent levels from character data."""
        talent_levels = {}
        skill_count = 0
        for talent in talents:
            if talent.get("type") == "skill":
                skill_count += 1
                if skill_count == 1:
                    talent_levels["normal_attack"] = talent.get("level", 1)
                elif skill_count == 2:
                    talent_levels["elemental_skill"] = talent.get("level", 1)
                elif skill_count == 3:
                    talent_levels["elemental_burst"] = talent.get("level", 1)
        return talent_levels

    def _get_elemental_dmg_bonus(self, stats: Dict[str, Any], element: str) -> float:
        """Get elemental damage bonus for the character's element."""
        element_lower = element.lower()
        dmg_bonus_key = f"{element_lower}_dmg_bonus"
        return stats.get(dmg_bonus_key, 0.0)

    def _is_genshin_question(self, question: str) -> bool:
        """Check if a question is related to Genshin Impact with comprehensive detection."""
        
        # Basic Genshin Impact keywords
        genshin_keywords = [
            "genshin", "character", "artifact", "weapon", "team", "build", "damage",
            "element", "reaction", "talent", "constellation", "ascension", "material",
            "domain", "abyss", "spiral", "resin", "primogem", "wish", "banner",
            "pyro", "hydro", "electro", "cryo", "anemo", "geo", "dendro",
            "vaporize", "melt", "freeze", "electro-charged", "overloaded", "superconduct",
            "swirl", "crystallize", "burning", "bloom", "hyperbloom", "burgeon", "quicken",
            "aggravate", "spread", "crit", "atk", "def", "hp", "em", "er", "healing",
            "shield", "burst", "skill", "normal attack", "charged attack", "plunge",
            "teyvat", "mondstadt", "liyue", "inazuma", "sumeru", "fontaine", "natlan",
            "archon", "vision", "fatui", "harbinger", "traveler", "paimon"
        ]
        
        # Comprehensive character names (fallback list - will be supplemented by database data)
        fallback_character_names = [
            # Mondstadt
            "amber", "kaeya", "lisa", "barbara", "razor", "xiangling", "beidou",
            "xingqiu", "ningguang", "fischl", "bennett", "noelle", "chongyun",
            "sucrose", "jean", "diluc", "qiqi", "mona", "keqing", "venti", "klee",
            "albedo", "rosaria", "eula", "mika",
            
            # Liyue
            "zhongli", "tartaglia", "childe", "xinyan", "ganyu", "xiao", "hu tao",
            "hutao", "yanfei", "baizhu", "yaoyao",
            
            # Inazuma
            "kazuha", "kaedehara kazuha", "ayaka", "kamisato ayaka", "yoimiya",
            "sayu", "raiden shogun", "raiden", "ei", "kokomi", "sangonomiya kokomi",
            "gorou", "sara", "kujou sara", "itto", "arataki itto", "yae miko",
            "yae", "heizou", "shikanoin heizou", "shinobu", "kuki shinobu",
            "ayato", "kamisato ayato", "kirara",
            
            # Sumeru
            "tighnari", "collei", "dori", "nilou", "cyno", "candace", "nahida",
            "layla", "faruzan", "wanderer", "scaramouche", "alhaitham", "dehya",
            "kaveh",
            
            # Fontaine
            "lynette", "lyney", "freminet", "neuvillette", "wriothesley",
            "charlotte", "furina", "chevreuse", "navia", "gaming", "xianyun",
            "chiori", "arlecchino", "sethos", "clorinde", "sigewinne", "emilie",
            
            # Natlan
            "kachina", "mualani", "kinich", "xilonen", "chasca", "ororon",
            "mavuika", "citlali", "lan yan", "lanyan",
            
            # Other/Special
            "aloy", "traveler", "aether", "lumine"
        ]
        
        # Weapon names (common ones)
        weapon_names = [
            "skyward", "primordial", "staff of homa", "homa", "mistsplitter",
            "thundering pulse", "polar star", "redhorn", "itto weapon",
            "freedom sworn", "elegy", "aqua simulacra", "hunter's path",
            "key of khaj-nisut", "light of foliar incision", "baizhu weapon",
            "tome of eternal flow", "cashflow supervision", "crane's echoing call",
            "uraku misugiri", "absolution", "peak patrol song"
        ]
        
        # Artifact set names
        artifact_sets = [
            "gladiator", "wanderer", "noblesse", "bloodstained", "viridescent",
            "maiden beloved", "thundering fury", "thundersoother", "lavawalker",
            "crimson witch", "blizzard strayer", "heart of depth", "tenacity",
            "pale flame", "shimenawa", "emblem", "husk", "ocean hued clam",
            "vermillion hereafter", "echoes", "deepwood", "gilded dreams",
            "flower of paradise", "desert pavilion", "vourukasha", "marechaussee",
            "golden troupe", "song of days past", "nighttime whispers",
            "fragment of harmonic whimsy", "unfinished reverie", "scroll of hero",
            "obsidian codex"
        ]
        
        # Team composition keywords
        team_keywords = [
            "team comp", "team composition", "synergy", "support", "dps", "sub dps",
            "healer", "shielder", "buffer", "debuffer", "enabler", "driver",
            "hypercarry", "quickswap", "rotation", "national team", "international",
            "freeze team", "melt team", "vape team", "taser", "soup", "bloom team"
        ]
        
        # Combine all keywords (character names will be added dynamically)
        all_keywords = genshin_keywords + fallback_character_names + weapon_names + artifact_sets + team_keywords
        
        question_lower = question.lower()
        
        # Check for direct keyword matches
        if any(keyword.lower() in question_lower for keyword in all_keywords):
            return True
        
        # Check for common Genshin Impact question patterns
        genshin_patterns = [
            "good team for",
            "best build for",
            "which character",
            "who should i",
            "what artifact",
            "which weapon",
            "team recommendation",
            "build guide",
            "talent priority",
            "constellation worth",
            "should i pull",
            "is it worth",
            "farming route",
            "material farm",
            "spiral abyss",
            "floor 12",
            "36 star",
            "damage calculation",
            "crit ratio",
            "stat priority",
            "investment priority",
            "characters i have",
            "my characters",
            "roster",
            "pull for",
            "skip banner",
            "meta team",
            "f2p friendly",
            "low investment"
        ]
        
        # Check for pattern matches
        if any(pattern in question_lower for pattern in genshin_patterns):
            return True
        
        # Additional context clues that suggest Genshin Impact
        context_clues = [
            "among the characters",
            "characters that i have",
            "my roster",
            "team for",
            "good with",
            "synergizes with",
            "works well with",
            "best support for",
            "who pairs with"
        ]
        
        if any(clue in question_lower for clue in context_clues):
            return True
        
        return False

    async def get_team_recommendation(self, character_name: str, uid: Optional[int] = None, content_type: str = "general") -> Dict[str, Any]:
        """
        Get specialized team recommendations for a specific character.
        
        Args:
            character_name: The main character to build a team around
            uid: User ID to get available characters
            content_type: Type of content (general, abyss, domain, boss)
        """
        try:
            # Get user's available characters if UID provided
            available_characters = []
            character_details = {}
            full_character_data = {}
            
            if uid:
                try:
                    from database import CharacterData
                    characters = await CharacterData.get_all_user_characters(uid)
                    available_characters = [char.get("name", "Unknown") for char in characters]
                    
                    for char in characters:
                        char_name = char.get("name", "Unknown")
                        full_character_data[char_name] = char
                        
                        # Create detailed character analysis
                        weapon_info = char.get("weapon", {})
                        artifacts = char.get("artifacts", [])
                        talents = char.get("talents", [])
                        stats = char.get("stats", {})
                        
                        character_details[char_name] = {
                            "name": char_name,
                            "avatarId": char.get("avatarId", 0),
                            "element": char.get("element", "Unknown"),
                            "rarity": char.get("rarity", 5),
                            "level": char.get("level", 1),
                            "ascension": char.get("ascension", 0),
                            "constellation": char.get("constellation", 0),
                            "friendship": char.get("friendship", 1),
                            "weapon": {
                                "name": weapon_info.get("name", "Unknown"),
                                "type": weapon_info.get("weaponType", "Unknown"),
                                "level": weapon_info.get("level", 1),
                                "refinement": weapon_info.get("refinement", 1),
                                "rarity": weapon_info.get("rarity", 3),
                                "baseAttack": weapon_info.get("baseAttack", 0),
                                "subStat": weapon_info.get("subStat", {})
                            },
                            "artifacts": {
                                "count": len(artifacts),
                                "sets": self._analyze_artifact_sets(artifacts),
                                "main_stats": self._extract_artifact_main_stats(artifacts)
                            },
                            "talents": {
                                "count": len([t for t in talents if t.get("type") == "skill"]),
                                "levels": self._extract_talent_levels(talents)
                            },
                            "stats": {
                                "total_hp": stats.get("current_hp", stats.get("max_hp", 0)),
                                "total_atk": stats.get("atk", 0) + stats.get("base_atk", 0),
                                "total_def": stats.get("def", 0) + stats.get("base_def", 0),
                                "crit_rate": stats.get("crit_rate", 5.0),
                                "crit_dmg": stats.get("crit_dmg", 50.0),
                                "elemental_mastery": stats.get("elemental_mastery", 0),
                                "energy_recharge": stats.get("energy_recharge", 100.0),
                                "elemental_dmg_bonus": self._get_elemental_dmg_bonus(stats, char.get("element", "Unknown"))
                            },
                            "build_quality": self._assess_build_quality(char)
                        }
                except Exception as e:
                    print(f"Error getting character data: {str(e)}")
            
            # Perform comprehensive web search for team recommendations
            search_results = []
            try:
                search_queries = [
                    f"Genshin Impact {character_name} best team composition 2024",
                    f"Genshin Impact {character_name} meta teams spiral abyss",
                    f"Genshin Impact {character_name} {content_type} team guide"
                ]
                
                for search_query in search_queries:
                    try:
                        search_response = self.cse_service.list(
                            q=search_query,
                            cx=settings.google_cse_id,
                            num=3
                        ).execute()
                        
                        for item in search_response.get("items", []):
                            search_results.append({
                                "title": item.get("title", ""),
                                "snippet": item.get("snippet", ""),
                                "link": item.get("link", ""),
                                "source": item.get("displayLink", ""),
                                "search_query": search_query
                            })
                    except Exception as search_error:
                        print(f"Error in search query '{search_query}': {str(search_error)}")
                        continue
            except Exception as e:
                print(f"Error in web search: {str(e)}")
            
            # Create specialized team building prompt
            team_prompt = f"""You are a Genshin Impact team composition expert with access to comprehensive character data and current meta information. Provide detailed team recommendations for {character_name} as the main character.

CHARACTER FOCUS: {character_name}
CONTENT TYPE: {content_type}
AVAILABLE CHARACTERS: {', '.join(available_characters) if available_characters else "Provide general recommendations"}

COMPREHENSIVE CHARACTER DATABASE:
{self._json_safe_serialize(character_details) if character_details else "No specific character data available"}

CURRENT META INFORMATION FROM WEB SEARCH:
{self._json_safe_serialize(search_results) if search_results else "No web search results available"}

TEAM BUILDING REQUIREMENTS:
1. **Primary Team Options**: Provide 3-4 different team compositions using available characters
2. **Character Roles**: Explain each character's role in the team (DPS, Sub-DPS, Support, Healer, etc.)
3. **Synergy Analysis**: Explain why these characters work well together (elemental reactions, buffs, etc.)
4. **Rotation Guide**: Provide basic rotation for each team
5. **Alternative Options**: If player doesn't have optimal characters, suggest alternatives from their roster
6. **Content Optimization**: Tailor recommendations for {content_type} content
7. **Build Analysis**: Consider character levels, constellations, weapons, and artifact sets
8. **Investment Priority**: Recommend which characters to prioritize for upgrades

TEAM COMPOSITION FORMAT:
For each team, provide:
- Team Name/Type (e.g., "Vaporize Team", "Freeze Team", "National Team")
- Character List with specific roles
- Synergy explanation with elemental reaction analysis
- Basic rotation (skill order and timing)
- Pros and cons for {content_type} content
- Investment requirements and priorities
- Alternative character options from available roster

PRIORITIZATION GUIDELINES:
- Use characters from the player's available roster when possible
- Consider character build quality and investment levels
- Explain why each character is chosen over alternatives
- Provide budget alternatives if meta characters aren't available
- Consider constellation requirements and weapon dependencies
- Mention artifact set priorities and stat requirements

CONTENT-SPECIFIC CONSIDERATIONS:
- For Spiral Abyss: Focus on high DPS, energy management, and survivability
- For Domains: Consider elemental advantages and shield breaking
- For Bosses: Emphasize sustained damage and survivability
- For General: Balance between damage, utility, and ease of use

Provide detailed, practical team recommendations that the player can actually implement with their available characters."""

            response = await self.llm.ainvoke([HumanMessage(content=team_prompt)])
            
            return {
                "character_focus": character_name,
                "content_type": content_type,
                "available_characters": available_characters,
                "character_count": len(available_characters),
                "team_recommendations": response.content,
                "personalized": bool(available_characters),
                "web_search_performed": bool(search_results),
                "search_results_count": len(search_results),
                "build_analysis_included": bool(character_details),
                "meta_information_used": bool(search_results)
            }
            
        except Exception as e:
            print(f"Error getting team recommendations: {str(e)}")
            return {"error": str(e)}

    def _assess_build_quality(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the build quality of a character based on their stats and equipment."""
        try:
            stats = character_data.get("stats", {})
            weapon = character_data.get("weapon", {})
            artifacts = character_data.get("artifacts", [])
            
            # Calculate crit value
            crit_rate = stats.get("crit_rate", 5.0)
            crit_dmg = stats.get("crit_dmg", 50.0)
            crit_value = crit_rate * 2 + crit_dmg
            
            # Assess weapon quality
            weapon_level = weapon.get("level", 1)
            weapon_rarity = weapon.get("rarity", 3)
            weapon_score = (weapon_level / 90) * weapon_rarity * 20
            
            # Assess artifact quality
            artifact_count = len(artifacts)
            artifact_score = (artifact_count / 5) * 100
            
            # Overall build score
            overall_score = (crit_value * 0.4) + (weapon_score * 0.3) + (artifact_score * 0.3)
            
            # Determine build quality rating
            if overall_score >= 80:
                quality_rating = "Excellent"
            elif overall_score >= 60:
                quality_rating = "Good"
            elif overall_score >= 40:
                quality_rating = "Average"
            else:
                quality_rating = "Needs Improvement"
            
            return {
                "overall_score": round(overall_score, 1),
                "quality_rating": quality_rating,
                "crit_value": round(crit_value, 1),
                "weapon_score": round(weapon_score, 1),
                "artifact_score": round(artifact_score, 1),
                "recommendations": self._get_build_improvement_suggestions(character_data, overall_score)
            }
            
        except Exception as e:
            print(f"Error assessing build quality: {str(e)}")
            return {"error": "Could not assess build quality"}

    def _get_build_improvement_suggestions(self, character_data: Dict[str, Any], overall_score: float) -> List[str]:
        """Get specific suggestions for improving a character's build."""
        suggestions = []
        
        try:
            stats = character_data.get("stats", {})
            weapon = character_data.get("weapon", {})
            artifacts = character_data.get("artifacts", [])
            
            # Crit ratio suggestions
            crit_rate = stats.get("crit_rate", 5.0)
            crit_dmg = stats.get("crit_dmg", 50.0)
            crit_ratio = crit_dmg / crit_rate if crit_rate > 0 else 0
            
            if crit_ratio > 2.5:
                suggestions.append("Increase CRIT Rate - current ratio is too high")
            elif crit_ratio < 1.5:
                suggestions.append("Increase CRIT DMG - current ratio is too low")
            
            if crit_rate < 50:
                suggestions.append("Aim for 60-70% CRIT Rate for consistency")
            
            # Weapon suggestions
            weapon_level = weapon.get("level", 1)
            if weapon_level < 80:
                suggestions.append("Level weapon to 80/90 for significant ATK increase")
            
            # Artifact suggestions
            if len(artifacts) < 5:
                suggestions.append("Equip all 5 artifact pieces for maximum stats")
            
            if overall_score < 60:
                suggestions.append("Focus on artifact main stats before optimizing substats")
            
            return suggestions
            
        except Exception as e:
            print(f"Error generating build suggestions: {str(e)}")
            return ["Unable to generate specific suggestions"]

    async def analyze_team_synergy(self, team_composition: List[str], uid: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze the synergy of a given team composition with comprehensive character data.
        
        Args:
            team_composition: List of character names in the team
            uid: User ID to get character build details
        """
        try:
            if len(team_composition) < 2 or len(team_composition) > 4:
                return {"error": "Team must have 2-4 characters"}
            
            # Get comprehensive character details if UID provided
            character_builds = {}
            full_character_data = {}
            
            if uid:
                try:
                    from database import CharacterData
                    for char_name in team_composition:
                        char_data = await CharacterData.get_character_by_name(uid, char_name)
                        if char_data:
                            full_character_data[char_name] = char_data
                            
                            # Create detailed character analysis
                            weapon_info = char_data.get("weapon", {})
                            artifacts = char_data.get("artifacts", [])
                            talents = char_data.get("talents", [])
                            stats = char_data.get("stats", {})
                            
                            character_builds[char_name] = {
                                "name": char_name,
                                "avatarId": char_data.get("avatarId", 0),
                                "element": char_data.get("element", "Unknown"),
                                "rarity": char_data.get("rarity", 5),
                                "level": char_data.get("level", 1),
                                "ascension": char_data.get("ascension", 0),
                                "constellation": char_data.get("constellation", 0),
                                "friendship": char_data.get("friendship", 1),
                                "weapon": {
                                    "name": weapon_info.get("name", "Unknown"),
                                    "type": weapon_info.get("weaponType", "Unknown"),
                                    "level": weapon_info.get("level", 1),
                                    "refinement": weapon_info.get("refinement", 1),
                                    "rarity": weapon_info.get("rarity", 3),
                                    "baseAttack": weapon_info.get("baseAttack", 0),
                                    "subStat": weapon_info.get("subStat", {})
                                },
                                "artifacts": {
                                    "count": len(artifacts),
                                    "sets": self._analyze_artifact_sets(artifacts),
                                    "main_stats": self._extract_artifact_main_stats(artifacts)
                                },
                                "talents": {
                                    "count": len([t for t in talents if t.get("type") == "skill"]),
                                    "levels": self._extract_talent_levels(talents)
                                },
                                "stats": {
                                    "total_hp": stats.get("current_hp", stats.get("max_hp", 0)),
                                    "total_atk": stats.get("atk", 0) + stats.get("base_atk", 0),
                                    "total_def": stats.get("def", 0) + stats.get("base_def", 0),
                                    "crit_rate": stats.get("crit_rate", 5.0),
                                    "crit_dmg": stats.get("crit_dmg", 50.0),
                                    "elemental_mastery": stats.get("elemental_mastery", 0),
                                    "energy_recharge": stats.get("energy_recharge", 100.0),
                                    "elemental_dmg_bonus": self._get_elemental_dmg_bonus(stats, char_data.get("element", "Unknown"))
                                },
                                "build_quality": self._assess_build_quality(char_data)
                            }
                except Exception as e:
                    print(f"Error getting character builds: {str(e)}")
            
            # Perform web search for team synergy information
            search_results = []
            try:
                team_name = " ".join(team_composition)
                search_queries = [
                    f"Genshin Impact {team_name} team synergy analysis",
                    f"Genshin Impact team composition {' '.join(team_composition[:2])} guide",
                    f"Genshin Impact meta team analysis 2024"
                ]
                
                for search_query in search_queries:
                    try:
                        search_response = self.cse_service.list(
                            q=search_query,
                            cx=settings.google_cse_id,
                            num=2
                        ).execute()
                        
                        for item in search_response.get("items", []):
                            search_results.append({
                                "title": item.get("title", ""),
                                "snippet": item.get("snippet", ""),
                                "link": item.get("link", ""),
                                "source": item.get("displayLink", ""),
                                "search_query": search_query
                            })
                    except Exception as search_error:
                        print(f"Error in search query '{search_query}': {str(search_error)}")
                        continue
            except Exception as e:
                print(f"Error in web search: {str(e)}")
            
            # Create comprehensive synergy analysis prompt
            synergy_prompt = f"""Analyze the team synergy for this Genshin Impact team composition with access to comprehensive character data and current meta information:

TEAM COMPOSITION: {', '.join(team_composition)}

COMPREHENSIVE CHARACTER BUILD DATA:
{self._json_safe_serialize(character_builds) if character_builds else "No specific build data available"}

CURRENT META INFORMATION FROM WEB SEARCH:
{self._json_safe_serialize(search_results) if search_results else "No web search results available"}

ANALYSIS REQUIREMENTS:
1. **Elemental Synergy**: Analyze elemental reactions, resonance, and elemental coverage
2. **Role Distribution**: Evaluate DPS, Sub-DPS, support, healer, shielder role balance
3. **Energy Management**: Assess energy generation, requirements, and particle flow
4. **Rotation Flow**: Suggest optimal rotation order with skill/burst timing
5. **Strengths**: Identify team's main advantages and power spikes
6. **Weaknesses**: Point out potential issues, gaps, or vulnerabilities
7. **Improvement Suggestions**: Recommend optimizations for builds and gameplay
8. **Content Suitability**: Rate effectiveness for different content types
9. **Investment Analysis**: Evaluate current investment levels and priorities
10. **Meta Relevance**: Compare with current meta teams and alternatives

MATHEMATICAL ANALYSIS:
- Use damage calculation principles for DPS assessment
- Consider buff/debuff stacking, duration, and uptime
- Evaluate elemental reaction potential and damage multipliers
- Assess survivability through shields, healing, and damage mitigation
- Calculate energy requirements and generation efficiency

SCORING SYSTEM:
Provide numerical scores (1-10) for:
- Overall Synergy: How well characters work together
- Damage Potential: Maximum damage output capability
- Survivability: Team's ability to survive challenging content
- Ease of Use: How simple the team is to play effectively
- Versatility: Effectiveness across different content types
- Investment Efficiency: Value relative to investment required

BUILD QUALITY ASSESSMENT:
- Analyze individual character build quality and optimization
- Identify characters that need investment priority
- Suggest specific artifact, weapon, and talent improvements
- Consider constellation effects and their impact on team performance

CONTENT-SPECIFIC ANALYSIS:
- Spiral Abyss: DPS checks, energy management, survivability
- Domains: Elemental advantages, shield breaking, efficiency
- Overworld: Exploration utility, resource efficiency, comfort
- Co-op: Role clarity, support capabilities, team coordination

Provide a comprehensive analysis that helps the player understand their team's potential, current performance level, and specific steps to optimize it."""

            response = await self.llm.ainvoke([HumanMessage(content=synergy_prompt)])
            
            return {
                "team_composition": team_composition,
                "team_size": len(team_composition),
                "synergy_analysis": response.content,
                "character_builds_analyzed": bool(character_builds),
                "characters_with_data": len(character_builds),
                "web_search_performed": bool(search_results),
                "search_results_count": len(search_results),
                "meta_information_used": bool(search_results),
                "build_quality_assessed": bool(character_builds),
                "comprehensive_analysis": True
            }
            
        except Exception as e:
            print(f"Error analyzing team synergy: {str(e)}")
            return {"error": str(e)}


# Singleton instance
ai_assistant = GenshinAIAssistant() 