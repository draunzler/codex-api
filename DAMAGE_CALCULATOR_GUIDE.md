# Genshin Impact Damage Calculator API Guide

## Overview

This API provides comprehensive damage calculations for Genshin Impact characters using official game formulas. The calculator is inspired by Akasha.cv and provides clean, accurate damage analysis with team synergies and elemental reactions.

## Key Features

- **Official Damage Formulas**: Uses the exact damage calculation formulas from Genshin Impact
- **Character Stats Extraction**: Automatically extracts stats from your character database
- **Team Buff Analysis**: Calculates team buffs, synergies, and elemental resonance
- **Elemental Reactions**: Supports all reaction types (Vaporize, Melt, Overloaded, etc.)
- **🆕 Automatic Reaction Detection**: Analyzes team composition and automatically suggests optimal reactions
- **Build Quality Assessment**: Evaluates character builds and provides recommendations
- **Rotation Guides**: Generates optimal skill rotation recommendations

## Official Damage Formula

The calculator uses the official Genshin Impact damage formula:

**Damage = Base DMG × Base DMG Multiplier × (1 + Additive Base DMG Bonus) × (1 + DMG Bonus) × DEF Multiplier × RES Multiplier**

Where:
1. **Base DMG** = Scaling Attribute × Talent Multiplier
2. **Base DMG Multiplier** = Amplifying reaction multiplier (Vaporize/Melt)
3. **Additive Base DMG Bonus** = Flat damage additions
4. **DMG Bonus** = Elemental/Physical damage bonuses
5. **DEF Multiplier** = Defense calculation
6. **RES Multiplier** = Resistance calculation

## API Endpoints

### 1. Single Character Damage Calculation

**Endpoint**: `POST /damage/character`

Calculate damage for a single character without team buffs.

```json
{
  "uid": 123456789,
  "character_name": "Neuvillette",
  "enemy_level": 90,
  "enemy_resistances": {
    "hydro": 10.0,
    "physical": 10.0
  },
  "reactions": ["vaporize"],
  "team_composition": ["Neuvillette", "Xiangling", "Bennett", "Kazuha"]
}
```

**🆕 New Feature**: If you provide `team_composition` but no `reactions`, the API will automatically analyze the team and suggest the best reactions!

**Response**:
```json
{
  "character_name": "Neuvillette",
  "element": "hydro",
  "character_stats": {
    "total_atk": 2847,
    "crit_rate": 40.0,
    "crit_dmg": 236.1,
    "elemental_dmg_bonus": 61.6,
    "build_quality": "Very Good"
  },
  "damage_breakdown": {
    "normal_attack": {
      "non_crit": 12543,
      "crit": 35421,
      "average": 23982
    },
    "elemental_skill": {
      "non_crit": 18765,
      "crit": 53012,
      "average": 35889
    },
    "elemental_burst": {
      "non_crit": 28934,
      "crit": 81756,
      "average": 55345
    }
  },
  "reaction_analysis": {
    "recommended_reactions": ["vaporize", "swirl"],
    "team_synergy": {
      "synergy_score": 85,
      "synergy_notes": [
        "Vaporize reaction potential (high damage multiplier)",
        "Anemo support for Swirl reactions and VV shred"
      ]
    }
  },
  "auto_detected_reactions": true
}
```

### 2. Team Damage Calculation

**Endpoint**: `POST /damage/team`

Calculate damage for a team composition with buffs and synergies.

```json
{
  "uid": 123456789,
  "main_dps": "Neuvillette",
  "team_composition": ["Neuvillette", "Xiangling", "Bennett", "Kazuha"],
  "enemy_level": 90
}
```

**🆕 Enhanced**: Now automatically analyzes team reactions and applies them if no reactions are specified!

**Response**:
```json
{
  "main_dps": "Neuvillette",
  "team_composition": ["Neuvillette", "Xiangling", "Bennett", "Kazuha"],
  "main_dps_damage": {
    "damage_breakdown": {
      "elemental_burst": {
        "average": 55345
      }
    }
  },
  "team_buffs": {
    "flat_atk": 1200,
    "elemental_dmg_bonus": 40,
    "res_reduction": 60
  },
  "buffed_damage": {
    "damage_breakdown": {
      "elemental_burst": {
        "average": 89234
      }
    },
    "damage_increase": {
      "elemental_burst": {
        "base_average": 55345,
        "buffed_average": 89234,
        "increase_percent": 61.2
      }
    }
  },
  "reaction_analysis": {
    "recommended_reactions": ["vaporize", "swirl"],
    "possible_reactions": [
      {
        "reaction": "vaporize",
        "trigger_element": "pyro",
        "aura_element": "hydro",
        "viability_score": 95,
        "multiplier": 1.5,
        "type": "amplifying",
        "description": "Pyro triggers Vaporize on Hydro aura"
      }
    ],
    "team_synergy": {
      "synergy_score": 85,
      "synergy_notes": [
        "Vaporize reaction potential (high damage multiplier)",
        "Anemo support for Swirl reactions and VV shred",
        "Pyro resonance active"
      ]
    }
  },
  "reactions_used": ["vaporize", "swirl"],
  "auto_detected_reactions": true
}
```

### 3. 🆕 Reaction Analysis

**Endpoint**: `POST /analyze/reactions`

Analyze possible elemental reactions based on team composition without full damage calculations.

```json
{
  "team_composition": ["Neuvillette", "Xiangling", "Bennett", "Kazuha"],
  "main_dps": "Neuvillette"
}
```

**Response**:
```json
{
  "analysis_summary": {
    "team_composition": ["Neuvillette", "Xiangling", "Bennett", "Kazuha"],
    "main_dps": "Neuvillette",
    "total_possible_reactions": 6,
    "recommended_reactions": ["vaporize", "swirl"],
    "top_reaction": {
      "reaction": "vaporize",
      "viability_score": 95,
      "multiplier": 1.5,
      "type": "amplifying"
    },
    "team_synergy_score": 85,
    "analysis_notes": [
      "Team has amplifying reaction potential (Vaporize/Melt) for high damage multipliers",
      "Anemo character present - can trigger Swirl reactions and provide VV resistance shred",
      "Elemental resonance active for additional team bonuses"
    ]
  },
  "detailed_analysis": {
    "possible_reactions": [
      {
        "reaction": "vaporize",
        "trigger_element": "pyro",
        "aura_element": "hydro",
        "trigger_characters": ["Xiangling", "Bennett"],
        "aura_characters": ["Neuvillette"],
        "viability_score": 95,
        "multiplier": 1.5,
        "type": "amplifying",
        "description": "Pyro triggers Vaporize on Hydro aura"
      },
      {
        "reaction": "swirl",
        "trigger_element": "anemo",
        "aura_element": "hydro",
        "trigger_characters": ["Kazuha"],
        "aura_characters": ["Neuvillette"],
        "viability_score": 80,
        "type": "transformative",
        "description": "Anemo swirls Hydro element"
      }
    ]
  },
  "usage_tips": {
    "optimal_reactions": ["vaporize", "swirl"],
    "reaction_priority": "Focus on amplifying reactions (Vaporize/Melt) for main DPS damage",
    "team_rotation": "Apply aura element first, then trigger with main DPS for consistent reactions",
    "elemental_mastery": "EM less important for amplifying reactions, focus on ATK/Crit"
  }
}
```

## How Automatic Reaction Detection Works

The system analyzes your team composition and:

1. **Identifies Elements**: Maps each character to their element
2. **Checks Combinations**: Looks for all possible elemental reaction combinations
3. **Scores Viability**: Rates each reaction based on:
   - Main DPS involvement (higher score if main DPS triggers)
   - Reaction type (amplifying reactions get higher scores)
   - Character reliability (known good applicators get bonuses)
4. **Recommends Top Reactions**: Suggests the 2-3 most viable reactions
5. **Analyzes Synergy**: Evaluates overall team elemental synergy

## Reaction Scoring System

- **Main DPS Trigger**: +50 points
- **Main DPS Aura**: +30 points
- **Other Character**: +10 points
- **Amplifying Reaction**: +30 points
- **Transformative Reaction**: +10 points
- **Reliable Applicator**: +15-20 points

## Supported Reactions

### Amplifying Reactions (Multiplicative)
- **Vaporize**: Pyro + Hydro (1.5x or 2.0x multiplier)
- **Melt**: Pyro + Cryo (1.5x or 2.0x multiplier)

### Transformative Reactions (Additive)
- **Overloaded**: Pyro + Electro
- **Electrocharged**: Hydro + Electro
- **Superconduct**: Cryo + Electro
- **Swirl**: Anemo + any element
- **Crystallize**: Geo + any element

### Dendro Reactions
- **Bloom**: Hydro + Dendro
- **Burning**: Pyro + Dendro
- **Quicken**: Electro + Dendro
- **Spread**: Dendro + Quicken
- **Hyperbloom**: Electro + Bloom Seeds
- **Burgeon**: Pyro + Bloom Seeds

## Character Scaling Types

The calculator properly handles different scaling attributes:

### ATK Scaling Characters
- **Pyro**: Hu Tao, Diluc, Yoimiya, Arlecchino, Lyney
- **Hydro**: Childe, Ayato
- **Electro**: Raiden Shogun, Keqing, Yae Miko
- **Cryo**: Ganyu, Ayaka, Eula, Wriothesley
- **Anemo**: Xiao, Wanderer
- **Geo**: Navia
- **Dendro**: Tighnari, Alhaitham

### HP Scaling Characters
- **Hydro**: Neuvillette, Furina
- **Geo**: Zhongli (Burst)

### DEF Scaling Characters
- **Geo**: Itto, Albedo (Skill)

### EM Scaling Characters
- **Anemo**: Kazuha (Swirl damage)
- **Dendro**: Nahida (some abilities)

## Usage Examples

### Example 1: Auto-Detect Reactions for Neuvillette Team
```bash
curl -X POST "http://localhost:8000/damage/character" \
-H "Content-Type: application/json" \
-d '{
  "uid": 123456789,
  "character_name": "Neuvillette",
  "team_composition": ["Neuvillette", "Xiangling", "Bennett", "Kazuha"]
}'
```

### Example 2: Team Analysis with Auto-Reactions
```bash
curl -X POST "http://localhost:8000/damage/team" \
-H "Content-Type: application/json" \
-d '{
  "uid": 123456789,
  "main_dps": "Neuvillette",
  "team_composition": ["Neuvillette", "Xiangling", "Bennett", "Kazuha"]
}'
```

### Example 3: Pure Reaction Analysis
```bash
curl -X POST "http://localhost:8000/analyze/reactions" \
-H "Content-Type: application/json" \
-d '{
  "team_composition": ["Hu Tao", "Xingqiu", "Zhongli", "Kazuha"],
  "main_dps": "Hu Tao"
}'
```

## Benefits of Automatic Reaction Detection

1. **Simplified Usage**: No need to manually specify reactions
2. **Optimal Recommendations**: AI suggests the best reactions for your team
3. **Educational**: Learn about reaction synergies and team building
4. **Accurate Calculations**: Uses the most viable reactions for realistic damage estimates
5. **Team Building Aid**: Helps evaluate team compositions before building

This feature makes the damage calculator much more user-friendly while providing educational insights into elemental reaction mechanics! 