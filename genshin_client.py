import aiohttp
import asyncio
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from database import UserProfile, CharacterData

# Load profile picture mappings from pfps.json
def load_profile_picture_mappings() -> Dict[str, str]:
    """Load profile picture ID to icon path mappings from pfps.json."""
    try:
        pfps_path = os.path.join(".enka_py", "assets", "pfps.json")
        with open(pfps_path, 'r', encoding='utf-8') as f:
            pfps_data = json.load(f)
        
        # Convert to simple ID -> iconPath mapping
        mappings = {}
        for pfp_id, pfp_data in pfps_data.items():
            if isinstance(pfp_data, dict) and "iconPath" in pfp_data:
                mappings[pfp_id] = pfp_data["iconPath"]
        
        return mappings
    except Exception as e:
        print(f"Error loading profile picture mappings: {e}")
        return {}

# Load character icon mappings from characters.json
def load_character_icon_mappings() -> Dict[str, str]:
    """Load character avatar ID to side icon name mappings from characters.json."""
    try:
        characters_path = os.path.join(".enka_py", "assets", "characters.json")
        with open(characters_path, 'r', encoding='utf-8') as f:
            characters_data = json.load(f)
        
        # Convert to simple avatarId -> SideIconName mapping
        mappings = {}
        for avatar_id, char_data in characters_data.items():
            if isinstance(char_data, dict) and "SideIconName" in char_data:
                mappings[avatar_id] = char_data["SideIconName"]
        
        return mappings
    except Exception as e:
        print(f"Error loading character icon mappings: {e}")
        return {}

# Load the mappings at module level
PROFILE_PICTURE_MAPPINGS = load_profile_picture_mappings()
CHARACTER_ICON_MAPPINGS = load_character_icon_mappings()

# Avatar ID to Character Name mapping (Updated with accurate mappings)
AVATAR_ID_TO_NAME = {
    10000002: "Kamisato Ayaka",
    10000003: "Jean",
    10000005: "Traveler",
    10000006: "Lisa",
    10000007: "Traveler",
    10000014: "Barbara",
    10000015: "Kaeya",
    10000016: "Diluc",
    10000020: "Razor",
    10000021: "Amber",
    10000022: "Venti",
    10000023: "Xiangling",
    10000024: "Beidou",
    10000025: "Xingqiu",
    10000026: "Xiao",
    10000027: "Ningguang",
    10000029: "Klee",
    10000030: "Zhongli",
    10000031: "Fischl",
    10000032: "Bennett",
    10000033: "Tartaglia",
    10000034: "Noelle",
    10000035: "Qiqi",
    10000036: "Chongyun",
    10000037: "Ganyu",
    10000038: "Albedo",
    10000039: "Diona",
    10000041: "Mona",
    10000042: "Keqing",
    10000043: "Sucrose",
    10000044: "Xinyan",
    10000045: "Rosaria",
    10000046: "Hu Tao",
    10000047: "Kaedehara Kazuha",
    10000048: "Yanfei",
    10000049: "Yoimiya",
    10000050: "Thoma",
    10000051: "Eula",
    10000052: "Raiden Shogun",
    10000053: "Sayu",
    10000054: "Sangonomiya Kokomi",
    10000055: "Gorou",
    10000056: "Kujou Sara",
    10000057: "Arataki Itto",
    10000058: "Yae Miko",
    10000059: "Shikanoin Heizou",
    10000060: "Yelan",
    10000061: "Kirara",
    10000062: "Aloy",
    10000063: "Shenhe",
    10000064: "Yun Jin",
    10000065: "Kuki Shinobu",
    10000066: "Kamisato Ayato",
    10000067: "Collei",
    10000068: "Dori",
    10000069: "Tighnari",
    10000070: "Nilou",
    10000071: "Cyno",
    10000072: "Candace",
    10000073: "Nahida",
    10000074: "Layla",
    10000075: "Wanderer",
    10000076: "Faruzan",
    10000077: "Yaoyao",
    10000078: "Alhaitham",
    10000079: "Dehya",
    10000080: "Mika",
    10000081: "Kaveh",
    10000082: "Baizhu",
    10000083: "Lynette",
    10000084: "Lyney",
    10000085: "Freminet",
    10000086: "Wriothesley",
    10000087: "Neuvillette",
    10000088: "Charlotte",
    10000089: "Furina",
    10000090: "Chevreuse",
    10000091: "Navia",
    10000092: "Gaming",
    10000093: "Xianyun",
    10000094: "Chiori",
    10000095: "Sigewinne",
    10000096: "Arlecchino",
    10000097: "Sethos",
    10000098: "Clorinde",
    10000099: "Emilie",
    10000100: "Kachina",
    10000101: "Kinich",
    10000102: "Mualani",
    10000103: "Xilonen",
    10000104: "Chasca",
    10000105: "Ororon",
    10000106: "Mavuika",
    10000107: "Citlali",
    10000108: "Lan Yan",
    10000109: "Yumemizuki Mizuki",
    10000110: "Iansan",
    10000111: "Varesa",
    10000112: "Escoffier",
    10000113: "Ifa",
}

# Fight Prop Map for stats (from Enka Network documentation)
FIGHT_PROP_MAP = {
    1: "base_hp",
    2: "hp",
    3: "hp_percent", 
    4: "base_atk",
    5: "atk",
    6: "atk_percent",
    7: "base_def", 
    8: "def",
    9: "def_percent",
    10: "base_spd",
    11: "spd_percent",
    20: "crit_rate",
    22: "crit_dmg", 
    23: "energy_recharge",
    26: "healing_bonus",
    27: "incoming_healing_bonus",
    28: "elemental_mastery",
    29: "physical_res",
    30: "physical_dmg_bonus",
    40: "pyro_dmg_bonus",
    41: "electro_dmg_bonus",
    42: "hydro_dmg_bonus", 
    43: "dendro_dmg_bonus",
    44: "anemo_dmg_bonus",
    45: "geo_dmg_bonus",
    46: "cryo_dmg_bonus",
    50: "pyro_res",
    51: "electro_res",
    52: "hydro_res",
    53: "dendro_res", 
    54: "anemo_res",
    55: "geo_res",
    56: "cryo_res",
    70: "pyro_energy_cost",
    71: "electro_energy_cost",
    72: "hydro_energy_cost",
    73: "dendro_energy_cost",
    74: "anemo_energy_cost",
    75: "cryo_energy_cost",
    76: "geo_energy_cost",
    77: "maximum_special_energy",
    78: "special_energy_cost",
    80: "cooldown_reduction",
    81: "shield_strength",
    1000: "current_pyro_energy",
    1001: "current_electro_energy", 
    1002: "current_hydro_energy",
    1003: "current_dendro_energy",
    1004: "current_anemo_energy",
    1005: "current_cryo_energy",
    1006: "current_geo_energy",
    1007: "current_special_energy",
    1010: "current_hp",
    2000: "max_hp",
    2001: "atk",
    2002: "def", 
    2003: "spd",
    3025: "elemental_reaction_crit_rate",
    3026: "elemental_reaction_crit_dmg",
    3027: "overloaded_crit_rate",
    3028: "overloaded_crit_dmg",
    3029: "swirl_crit_rate",
    3030: "swirl_crit_dmg",
    3031: "electro_charged_crit_rate",
    3032: "electro_charged_crit_dmg",
    3033: "superconduct_crit_rate",
    3034: "superconduct_crit_dmg",
    3035: "burn_crit_rate",
    3036: "burn_crit_dmg",
    3037: "frozen_shattered_crit_rate",
    3038: "frozen_shattered_crit_dmg",
    3039: "bloom_crit_rate",
    3040: "bloom_crit_dmg",
    3041: "burgeon_crit_rate",
    3042: "burgeon_crit_dmg",
    3043: "hyperbloom_crit_rate",
    3044: "hyperbloom_crit_dmg",
    3045: "base_elemental_reaction_crit_rate",
    3046: "base_elemental_reaction_crit_dmg"
}

# Equipment type mapping
EQUIP_TYPE_MAP = {
    "EQUIP_BRACER": "flower",
    "EQUIP_NECKLACE": "feather", 
    "EQUIP_SHOES": "sands",
    "EQUIP_RING": "goblet",
    "EQUIP_DRESS": "circlet"
}

class GenshinClient:
    """
    Enhanced Genshin Impact API client for Enka Network integration.
    
    Features:
    - Direct Enka Network API integration
    - Proper handling of Enka response format
    - Character data storage in user collections
    - Comprehensive stat parsing
    """
    
    def __init__(self):
        self.base_url = "https://enka.network/api"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _convert_icon_to_url(self, icon_name: str) -> str:
        """Convert icon name to full Enka Network URL."""
        if not icon_name:
            return ""
        
        # Remove any existing URL prefix if present
        if icon_name.startswith("http"):
            return icon_name
            
        # Convert icon name to full URL
        base_icon_url = "https://enka.network/ui/"
        if not icon_name.endswith(".png"):
            icon_name += ".png"
            
        return f"{base_icon_url}{icon_name}"
    
    async def _download_icon(self, icon_url: str, save_path: str = "icons/") -> Optional[str]:
        """Download icon from URL and save to local path."""
        try:
            if not icon_url or not icon_url.startswith("http"):
                return None
                
            # Create directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)
            
            # Extract filename from URL
            filename = icon_url.split("/")[-1]
            if not filename.endswith(".png"):
                filename += ".png"
                
            file_path = os.path.join(save_path, filename)
            
            # Skip if file already exists
            if os.path.exists(file_path):
                return file_path
                
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(icon_url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    return file_path
                else:
                    print(f"Failed to download icon: {icon_url} (Status: {response.status})")
                    return None
                    
        except Exception as e:
            print(f"Error downloading icon {icon_url}: {str(e)}")
            return None
    
    def _process_icon_data(self, data: Dict[str, Any], download_icons: bool = False) -> Dict[str, Any]:
        """Process icon fields in data and convert to URLs, optionally download."""
        if not isinstance(data, dict):
            return data
            
        processed_data = data.copy()
        
        # Common icon fields to process
        icon_fields = [
            "icon", "iconName", "nameCardIcon", "profilePictureIcon",
            "weaponIcon", "artifactIcon", "characterIcon", "skillIcon"
        ]
        
        for field in icon_fields:
            if field in processed_data and processed_data[field]:
                icon_name = processed_data[field]
                icon_url = self._convert_icon_to_url(icon_name)
                processed_data[field] = icon_url
                
                # Optionally download the icon
                if download_icons and icon_url:
                    # Note: This would need to be called in an async context
                    # For now, we'll just convert to URL
                    pass
        
        return processed_data
    
    async def fetch_user_data(self, uid: int, merge_characters: bool = True) -> Dict[str, Any]:
        """
        Fetch user data from Enka Network API.
        
        Args:
            uid: User ID to fetch data for
            merge_characters: Whether to merge new characters with existing ones (True) or replace all (False)
        """
        try:
            print(f"Starting data fetch for UID: {uid} (merge_characters: {merge_characters})")
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/uid/{uid}"
            print(f"Fetching from URL: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Successfully fetched data from Enka Network for UID: {uid}")
                    
                    # Process the response
                    processed_data = await self._process_enka_response(uid, data, merge_characters)
                    return processed_data
                    
                elif response.status == 404:
                    return {"error": "User not found or profile not public"}
                elif response.status == 429:
                    return {"error": "Rate limit exceeded. Please try again later."}
                else:
                    return {"error": f"API error: {response.status}"}
                    
        except Exception as e:
            print(f"Error fetching user data for UID {uid}: {str(e)}")
            return {"error": str(e)}
    
    async def _process_enka_response(self, uid: int, data: Dict[str, Any], merge_characters: bool) -> Dict[str, Any]:
        """Process Enka Network response and save to database."""
        try:
            # Extract player info
            player_info = data.get("playerInfo", {})
            avatar_info_list = data.get("avatarInfoList", [])
            
            # Process player profile - exclude character-related fields
            profile_data = {
                "uid": uid,
                "nickname": player_info.get("nickname", "Unknown"),
                "level": player_info.get("level", 1),
                "signature": player_info.get("signature", ""),
                "worldLevel": player_info.get("worldLevel", 0),
                "nameCardId": player_info.get("nameCardId", 0),
                "finishAchievementNum": player_info.get("finishAchievementNum", 0),
                "towerFloorIndex": player_info.get("towerFloorIndex", 0),
                "towerLevelIndex": player_info.get("towerLevelIndex", 0),
                # Character-related fields excluded:
                # - showAvatarInfoList (character showcase)
                # - fetterCount (character friendship count)
                # - isShowAvatarTalent (character talent display setting)
                # - showNameCardIdList (some name cards are character-related)
                "profilePicture": player_info.get("profilePicture", {}),
                "theaterActIndex": player_info.get("theaterActIndex", 0),
                "theaterModeIndex": player_info.get("theaterModeIndex", 0),
                "theaterStarIndex": player_info.get("theaterStarIndex", 0),
                "towerStarIndex": player_info.get("towerStarIndex", 0),
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            # Process profile picture icon if present
            profile_picture = profile_data.get("profilePicture", {})
            if isinstance(profile_picture, dict):
                # Check for both "id" and "avatarId" fields for compatibility
                pfp_id = profile_picture.get("id") or profile_picture.get("avatarId")
                if pfp_id:
                    # Convert to string for mapping lookup
                    pfp_id_str = str(pfp_id)
                    
                    # Look up the icon path from the mappings
                    if pfp_id_str in PROFILE_PICTURE_MAPPINGS:
                        icon_path = PROFILE_PICTURE_MAPPINGS[pfp_id_str]
                        profile_picture["iconPath"] = icon_path
                        profile_picture["icon"] = self._convert_icon_to_url(icon_path)
                    else:
                        # Fallback for unmapped IDs
                        print(f"Profile picture ID {pfp_id} not found in mappings")
                        profile_picture["iconPath"] = f"UI_AvatarIcon_Unknown_{pfp_id}"
                        profile_picture["icon"] = self._convert_icon_to_url(f"UI_AvatarIcon_Unknown_{pfp_id}")
                    
                    profile_data["profilePicture"] = profile_picture
            
            # Process characters
            processed_characters = []
            for avatar_info in avatar_info_list:
                processed_char = await self._process_character_data(avatar_info)
                if processed_char:
                    processed_characters.append(processed_char)
            
            # Save to database
            # Update or create user profile with better error handling
            profile_saved = await self._upsert_user_profile(uid, profile_data)
            
            # Save all characters
            if processed_characters:
                try:
                    await CharacterData.save_all_characters(uid, processed_characters, merge_characters)
                    print(f"Saved {len(processed_characters)} characters for UID: {uid} (merge_characters: {merge_characters})")
                except Exception as char_error:
                    print(f"Error saving character data: {str(char_error)}")
                    # Continue processing even if character save fails
            
            return {
                "uid": uid,
                "player_info": profile_data,
                "characters": processed_characters,
                "character_count": len(processed_characters)
            }
            
        except Exception as e:
            print(f"Error processing Enka response: {str(e)}")
            return {"error": str(e)}
    
    async def _process_character_data(self, avatar_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual character data from Enka format."""
        try:
            avatar_id = avatar_info.get("avatarId")
            if not avatar_id:
                return None
            
            # Get character name from mapping
            character_name = AVATAR_ID_TO_NAME.get(avatar_id, f"Unknown_{avatar_id}")
            
            # Get character side icon name from mapping
            avatar_id_str = str(avatar_id)
            side_icon_name = CHARACTER_ICON_MAPPINGS.get(avatar_id_str, "")
            
            # Extract basic info
            prop_map = avatar_info.get("propMap", {})
            fight_prop_map = avatar_info.get("fightPropMap", {})
            equip_list = avatar_info.get("equipList", [])
            skill_level_map = avatar_info.get("skillLevelMap", {})
            talent_id_list = avatar_info.get("talentIdList", [])
            
            # Extract level and ascension
            level = int(prop_map.get("4001", {}).get("val", "1"))
            ascension = int(prop_map.get("1002", {}).get("val", "0"))
            
            # Process equipment (weapons and artifacts)
            weapon_data = None
            artifacts_data = []
            
            for equip in equip_list:
                flat = equip.get("flat", {})
                item_type = flat.get("itemType", "")
                
                if item_type == "ITEM_WEAPON":
                    weapon_data = self._process_weapon_data(equip)
                elif item_type == "ITEM_RELIQUARY":
                    artifact_data = self._process_artifact_data(equip)
                    if artifact_data:
                        artifacts_data.append(artifact_data)
            
            # Process talents
            talents_data = self._process_talents_data(skill_level_map, talent_id_list)
            
            # Process stats from fightPropMap
            stats_data = self._process_fight_props(fight_prop_map)
            
            # Get friendship level
            fetter_info = avatar_info.get("fetterInfo", {})
            friendship_level = fetter_info.get("expLevel", 10)
            
            # Determine element based on character name (basic mapping)
            element = self._get_character_element(character_name)
            
            # Compile character data
            character_data = {
                "avatarId": avatar_id,
                "name": character_name,
                "sideIconName": side_icon_name,
                "element": element,
                "rarity": 5,  # Default to 5-star, could be improved with proper mapping
                "level": level,
                "ascension": ascension,
                "friendship": friendship_level,
                "constellation": len(talent_id_list),
                "weapon": weapon_data,
                "artifacts": artifacts_data,
                "talents": talents_data,
                "stats": stats_data,
                "skillDepotId": avatar_info.get("skillDepotId"),
                "inherentProudSkillList": avatar_info.get("inherentProudSkillList", []),
                "updated_at": datetime.utcnow()
            }
            
            return character_data
            
        except Exception as e:
            print(f"Error processing character data: {str(e)}")
            return None
    
    def _get_character_element(self, character_name: str) -> str:
        """Get character element based on name. Updated with correct mappings from official sources."""
        element_map = {
            "Kamisato Ayaka": "Cryo",
            "Jean": "Anemo",
            "Traveler": "Anemo",  # Default, can be multiple
            "Lisa": "Electro",
            "Barbara": "Hydro",
            "Kaeya": "Cryo",
            "Diluc": "Pyro",
            "Razor": "Electro",
            "Amber": "Pyro",
            "Venti": "Anemo",
            "Xiangling": "Pyro",
            "Beidou": "Electro",
            "Xingqiu": "Hydro",
            "Xiao": "Anemo",
            "Ningguang": "Geo",
            "Klee": "Pyro",
            "Zhongli": "Geo",
            "Fischl": "Electro",
            "Bennett": "Pyro",
            "Tartaglia": "Hydro",
            "Noelle": "Geo",
            "Qiqi": "Cryo",
            "Chongyun": "Cryo",
            "Ganyu": "Cryo",
            "Albedo": "Geo",
            "Diona": "Cryo",
            "Mona": "Hydro",
            "Keqing": "Electro",
            "Sucrose": "Anemo",
            "Xinyan": "Pyro",
            "Rosaria": "Cryo",
            "Hu Tao": "Pyro",
            "Kaedehara Kazuha": "Anemo",
            "Yanfei": "Pyro",
            "Yoimiya": "Pyro",
            "Thoma": "Pyro",
            "Eula": "Cryo",
            "Raiden Shogun": "Electro",
            "Sayu": "Anemo",
            "Sangonomiya Kokomi": "Hydro",
            "Gorou": "Geo",
            "Kujou Sara": "Electro",
            "Arataki Itto": "Geo",
            "Yae Miko": "Electro",
            "Shikanoin Heizou": "Anemo",
            "Yelan": "Hydro",
            "Kirara": "Dendro",
            "Aloy": "Cryo",
            "Shenhe": "Cryo",
            "Yun Jin": "Geo",
            "Kuki Shinobu": "Electro",
            "Kamisato Ayato": "Hydro",
            "Collei": "Dendro",
            "Dori": "Electro",
            "Tighnari": "Dendro",
            "Nilou": "Hydro",
            "Cyno": "Electro",
            "Candace": "Hydro",
            "Nahida": "Dendro",
            "Layla": "Cryo",
            "Wanderer": "Anemo",
            "Faruzan": "Anemo",
            "Yaoyao": "Dendro",
            "Alhaitham": "Dendro",
            "Dehya": "Pyro",
            "Mika": "Cryo",
            "Kaveh": "Dendro",
            "Baizhu": "Dendro",
            "Lynette": "Anemo",
            "Lyney": "Pyro",
            "Freminet": "Cryo",
            "Wriothesley": "Cryo",
            "Neuvillette": "Hydro",
            "Charlotte": "Cryo",
            "Furina": "Hydro",
            "Chevreuse": "Pyro",
            "Navia": "Geo",
            "Gaming": "Pyro",
            "Xianyun": "Anemo",
            "Chiori": "Geo",
            "Sigewinne": "Hydro",
            "Arlecchino": "Pyro",
            "Sethos": "Electro",
            "Clorinde": "Electro",
            "Emilie": "Dendro",
            "Kachina": "Geo",
            "Kinich": "Dendro",
            "Mualani": "Hydro",
            "Xilonen": "Geo",
            "Chasca": "Anemo",
            "Ororon": "Electro",
            "Mavuika": "Pyro",
            "Citlali": "Cryo",
            "Lan Yan": "Anemo",
            "Yumemizuki Mizuki": "Anemo",
            "Iansan": "Electro",
            "Varesa": "Electro",
            "Escoffier": "Cryo",
            "Ifa": "Anemo",
        }
        
        return element_map.get(character_name, "Unknown")
    
    def _get_readable_name_from_hash(self, name_hash: str, item_type: str = "unknown") -> str:
        """Convert name hash to readable name. For now, return the hash as fallback."""
        # This would ideally use a text map database, but for now we'll return a placeholder
        # In a full implementation, you'd have a mapping of hash -> readable name
        if isinstance(name_hash, (int, str)) and str(name_hash).isdigit():
            return f"{item_type.title()} #{name_hash}"
        return str(name_hash)
    
    def _process_weapon_data(self, equip: Dict[str, Any]) -> Dict[str, Any]:
        """Process weapon data from equipment."""
        try:
            weapon = equip.get("weapon", {})
            flat = equip.get("flat", {})
            
            weapon_stats = flat.get("weaponStats", [])
            base_attack = 0
            sub_stat = None
            
            for stat in weapon_stats:
                prop_id = stat.get("appendPropId", "")
                value = stat.get("statValue", 0)
                
                if prop_id == "FIGHT_PROP_BASE_ATTACK":
                    base_attack = value
                else:
                    sub_stat = {
                        "name": self._get_readable_stat_name(prop_id),
                        "value": value
                    }
            
            # Get weapon name - handle hash
            weapon_name = flat.get("nameTextMapHash", "Unknown Weapon")
            readable_name = self._get_readable_name_from_hash(weapon_name, "weapon")
            
            # Get weapon icon and convert to URL
            weapon_icon = flat.get("icon", "")
            weapon_icon_url = self._convert_icon_to_url(weapon_icon) if weapon_icon else ""
            
            # Calculate refinement level from affixMap
            # affixMap contains weapon affix ID as key and refinement level - 1 as value
            # So value 0 = R1, value 1 = R2, value 4 = R5, etc.
            affix_map = weapon.get("affixMap", {})
            refinement_level = 1  # Default to R1
            if affix_map:
                # Get the first (and usually only) affix value and add 1
                refinement_level = list(affix_map.values())[0] + 1
            
            return {
                "itemId": equip.get("itemId"),
                "level": weapon.get("level", 1),
                "ascension": weapon.get("promoteLevel", 0),
                "refinement": refinement_level,
                "baseAttack": base_attack,
                "subStat": sub_stat,
                "name": readable_name,
                "icon": weapon_icon_url,
                "rarity": flat.get("rankLevel", 1),
                "weaponType": self._get_weapon_type_from_icon(flat.get("icon", ""))
            }
            
        except Exception as e:
            print(f"Error processing weapon data: {str(e)}")
            return {}
    
    def _process_artifact_data(self, equip: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process artifact data from equipment."""
        try:
            reliquary = equip.get("reliquary", {})
            flat = equip.get("flat", {})
            
            # Get artifact type
            equip_type = flat.get("equipType", "")
            artifact_type = EQUIP_TYPE_MAP.get(equip_type, "unknown")
            
            # Get main stat
            main_stat_data = flat.get("reliquaryMainstat", {})
            main_prop_id = main_stat_data.get("mainPropId", "")
            main_stat = {
                "name": self._get_readable_stat_name(main_prop_id),
                "value": main_stat_data.get("statValue", 0)
            }
            
            # Get substats
            substats = []
            for substat in flat.get("reliquarySubstats", []):
                append_prop_id = substat.get("appendPropId", "")
                substats.append({
                    "name": self._get_readable_stat_name(append_prop_id),
                    "value": substat.get("statValue", 0)
                })
            
            # Get set name - handle hash
            set_name = flat.get("setNameTextMapHash", "Unknown Set")
            readable_set_name = self._get_readable_name_from_hash(set_name, "artifact_set")
            
            # Get artifact icon and convert to URL
            artifact_icon = flat.get("icon", "")
            artifact_icon_url = self._convert_icon_to_url(artifact_icon) if artifact_icon else ""
            
            return {
                "itemId": equip.get("itemId"),
                "type": artifact_type,
                "level": reliquary.get("level", 0),
                "rarity": flat.get("rankLevel", 1),
                "setId": flat.get("setId"),
                "setName": readable_set_name,
                "icon": artifact_icon_url,
                "mainStat": main_stat,
                "subStats": substats
            }
            
        except Exception as e:
            print(f"Error processing artifact data: {str(e)}")
            return None
    
    def _process_talents_data(self, skill_level_map: Dict[str, Any], talent_id_list: List[int]) -> List[Dict[str, Any]]:
        """Process talent data."""
        talents = []
        
        # Process skill levels
        for skill_id, level in skill_level_map.items():
            talents.append({
                "skillId": skill_id,
                "level": level,
                "type": "skill"
            })
        
        # Process constellation talents
        for talent_id in talent_id_list:
            talents.append({
                "talentId": talent_id,
                "type": "constellation"
            })
        
        return talents
    
    def _process_fight_props(self, fight_prop_map: Dict[str, Any]) -> Dict[str, Any]:
        """Process fight properties into readable stats."""
        stats = {}
        
        for prop_id_str, value in fight_prop_map.items():
            try:
                prop_id = int(prop_id_str)
                if prop_id in FIGHT_PROP_MAP:
                    stat_name = FIGHT_PROP_MAP[prop_id]
                    
                    # Define which stats should be converted to percentages
                    percentage_stats = {
                        'hp_percent', 'atk_percent', 'def_percent', 'spd_percent',
                        'crit_rate', 'crit_dmg', 'energy_recharge', 'healing_bonus', 
                        'incoming_healing_bonus', 'physical_dmg_bonus',
                        'pyro_dmg_bonus', 'electro_dmg_bonus', 'hydro_dmg_bonus', 
                        'dendro_dmg_bonus', 'anemo_dmg_bonus', 'geo_dmg_bonus', 'cryo_dmg_bonus',
                        'pyro_res', 'electro_res', 'hydro_res', 'dendro_res', 
                        'anemo_res', 'geo_res', 'cryo_res', 'physical_res',
                        'cooldown_reduction', 'shield_strength',
                        'elemental_reaction_crit_rate', 'elemental_reaction_crit_dmg',
                        'overloaded_crit_rate', 'overloaded_crit_dmg',
                        'swirl_crit_rate', 'swirl_crit_dmg',
                        'electro_charged_crit_rate', 'electro_charged_crit_dmg',
                        'superconduct_crit_rate', 'superconduct_crit_dmg',
                        'burn_crit_rate', 'burn_crit_dmg',
                        'frozen_shattered_crit_rate', 'frozen_shattered_crit_dmg',
                        'bloom_crit_rate', 'bloom_crit_dmg',
                        'burgeon_crit_rate', 'burgeon_crit_dmg',
                        'hyperbloom_crit_rate', 'hyperbloom_crit_dmg',
                        'base_elemental_reaction_crit_rate', 'base_elemental_reaction_crit_dmg'
                    }
                    
                    # Convert percentage stats (multiply by 100)
                    if stat_name in percentage_stats:
                        stats[stat_name] = round(value * 100, 1)
                    else:
                        # Keep flat stats as-is, but round floats
                        stats[stat_name] = round(value, 1) if isinstance(value, float) else value
                        
            except (ValueError, TypeError):
                continue
        
        return stats
    
    def _get_readable_stat_name(self, prop_id: str) -> str:
        """Convert property ID to readable stat name."""
        stat_map = {
            "FIGHT_PROP_BASE_ATTACK": "Base ATK",
            "FIGHT_PROP_HP": "Flat HP",
            "FIGHT_PROP_ATTACK": "Flat ATK",
            "FIGHT_PROP_DEFENSE": "Flat DEF",
            "FIGHT_PROP_HP_PERCENT": "HP%",
            "FIGHT_PROP_ATTACK_PERCENT": "ATK%",
            "FIGHT_PROP_DEFENSE_PERCENT": "DEF%",
            "FIGHT_PROP_CRITICAL": "Crit RATE",
            "FIGHT_PROP_CRITICAL_HURT": "Crit DMG",
            "FIGHT_PROP_CHARGE_EFFICIENCY": "Energy Recharge",
            "FIGHT_PROP_HEAL_ADD": "Healing Bonus",
            "FIGHT_PROP_ELEMENT_MASTERY": "Elemental Mastery",
            "FIGHT_PROP_PHYSICAL_ADD_HURT": "Physical DMG Bonus",
            "FIGHT_PROP_FIRE_ADD_HURT": "Pyro DMG Bonus",
            "FIGHT_PROP_ELEC_ADD_HURT": "Electro DMG Bonus",
            "FIGHT_PROP_WATER_ADD_HURT": "Hydro DMG Bonus",
            "FIGHT_PROP_WIND_ADD_HURT": "Anemo DMG Bonus",
            "FIGHT_PROP_ICE_ADD_HURT": "Cryo DMG Bonus",
            "FIGHT_PROP_ROCK_ADD_HURT": "Geo DMG Bonus",
            "FIGHT_PROP_GRASS_ADD_HURT": "Dendro DMG Bonus",
            # Legacy mappings for backward compatibility
            "FIGHT_PROP_PYRO_ADD_HURT": "Pyro DMG Bonus",
            "FIGHT_PROP_ELECTRO_ADD_HURT": "Electro DMG Bonus",
            "FIGHT_PROP_HYDRO_ADD_HURT": "Hydro DMG Bonus",
            "FIGHT_PROP_DENDRO_ADD_HURT": "Dendro DMG Bonus",
            "FIGHT_PROP_ANEMO_ADD_HURT": "Anemo DMG Bonus",
            "FIGHT_PROP_GEO_ADD_HURT": "Geo DMG Bonus",
            "FIGHT_PROP_CRYO_ADD_HURT": "Cryo DMG Bonus",
            "FIGHT_PROP_HEALED_ADD": "Incoming Healing Bonus"
        }
        
        return stat_map.get(prop_id, prop_id)
    
    def _get_weapon_type_from_icon(self, icon: str) -> str:
        """Determine weapon type from icon name."""
        if "Sword" in icon:
            return "Sword"
        elif "Claymore" in icon:
            return "Claymore"
        elif "Pole" in icon:
            return "Polearm"
        elif "Bow" in icon:
            return "Bow"
        elif "Catalyst" in icon:
            return "Catalyst"
        else:
            return "Unknown"
    
    async def get_character_details(self, uid: int, character_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed character information by name."""
        try:
            character = await CharacterData.get_character_by_name(uid, character_name)
            return character
        except Exception as e:
            print(f"Error getting character details: {str(e)}")
            return None
    
    async def get_all_characters_hybrid(self, uid: int) -> Dict[str, Any]:
        """Get all characters using hybrid approach."""
        try:
            # First try to get from database
            characters = await CharacterData.get_all_user_characters(uid)
            
            if not characters:
                # If no characters in database, fetch from API
                fresh_data = await self.fetch_user_data(uid)
                if "characters" in fresh_data:
                    characters = fresh_data["characters"]
            
            return {
                "uid": uid,
                "characters": characters,
                "character_count": len(characters),
                "data_source": "hybrid"
            }
            
        except Exception as e:
            print(f"Error in hybrid character fetch: {str(e)}")
            return {"error": str(e)}
    
    async def add_character_manually(self, uid: int, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add character data manually."""
        try:
            # Generate avatar ID if not provided
            if "avatarId" not in character_data:
                character_data["avatarId"] = hash(character_data["name"]) % 100000
            
            # Set defaults
            defaults = {
                "level": 1,
                "ascension": 0,
                "friendship": 10,
                "constellation": 0,
                "weapon": None,
                "artifacts": [],
                "talents": [],
                "stats": {},
                "data_source": "manual_input"
            }
            
            for key, default_value in defaults.items():
                if key not in character_data:
                    character_data[key] = default_value
            
            # Save character
            await CharacterData.save_character(uid, character_data)
            
            return character_data
            
        except Exception as e:
            print(f"Error adding character manually: {str(e)}")
            raise
    
    def create_character_template(self) -> Dict[str, Any]:
        """Create a template for manual character input."""
        return {
            "name": "Character Name",
            "level": 90,
            "ascension": 6,
            "friendship": 10,
            "constellation": 0,
            "weapon": {
                "name": "Weapon Name",
                "level": 90,
                "ascension": 6,
                "refinement": 1,
                "baseAttack": 500,
                "subStat": {
                    "name": "CRIT Rate",
                    "value": 27.6
                }
            },
            "artifacts": [
                {
                    "type": "flower",
                    "level": 20,
                    "rarity": 5,
                    "setName": "Set Name",
                    "mainStat": {"name": "HP", "value": 4780},
                    "subStats": [
                        {"name": "CRIT Rate", "value": 10.5},
                        {"name": "CRIT DMG", "value": 21.0},
                        {"name": "ATK%", "value": 16.3},
                        {"name": "Energy Recharge", "value": 11.0}
                    ]
                }
                # Add templates for other artifact types
            ],
            "talents": [
                {"type": "normal_attack", "level": 10},
                {"type": "elemental_skill", "level": 10},
                {"type": "elemental_burst", "level": 10}
            ]
        }
    
    async def download_user_icons(self, uid: int, save_path: str = "icons/") -> Dict[str, Any]:
        """Download all icons for a user's data."""
        try:
            downloaded_icons = []
            failed_downloads = []
            
            # Get user data from database
            user_profile = await UserProfile.get(uid)
            characters = await CharacterData.get_all_user_characters(uid)
            
            if not user_profile and not characters:
                return {"error": "No user data found"}
            
            # Download profile picture icon
            if user_profile and "profilePicture" in user_profile:
                profile_pic = user_profile["profilePicture"]
                if isinstance(profile_pic, dict) and "icon" in profile_pic:
                    icon_url = profile_pic["icon"]
                    if icon_url and icon_url.startswith("http"):
                        result = await self._download_icon(icon_url, save_path)
                        if result:
                            downloaded_icons.append(result)
                        else:
                            failed_downloads.append(icon_url)
            
            # Download character icons (weapons and artifacts)
            for character in characters:
                # Download weapon icon
                if character.get("weapon") and character["weapon"].get("icon"):
                    weapon_icon = character["weapon"]["icon"]
                    if weapon_icon.startswith("http"):
                        result = await self._download_icon(weapon_icon, save_path)
                        if result:
                            downloaded_icons.append(result)
                        else:
                            failed_downloads.append(weapon_icon)
                
                # Download artifact icons
                if character.get("artifacts"):
                    for artifact in character["artifacts"]:
                        if artifact.get("icon"):
                            artifact_icon = artifact["icon"]
                            if artifact_icon.startswith("http"):
                                result = await self._download_icon(artifact_icon, save_path)
                                if result:
                                    downloaded_icons.append(result)
                                else:
                                    failed_downloads.append(artifact_icon)
            
            return {
                "uid": uid,
                "downloaded_icons": downloaded_icons,
                "failed_downloads": failed_downloads,
                "total_downloaded": len(downloaded_icons),
                "total_failed": len(failed_downloads)
            }
            
        except Exception as e:
            print(f"Error downloading user icons: {str(e)}")
            return {"error": str(e)}
    
    async def _upsert_user_profile(self, uid: int, profile_data: Dict[str, Any]) -> bool:
        """Upsert user profile with better error handling for duplicate keys."""
        try:
            from database import db
            
            # Use MongoDB's native upsert to avoid duplicate key errors completely
            user_document = {
                "uid": uid,
                "profile_data": profile_data,
                "updated_at": datetime.utcnow(),
                "last_fetch": datetime.utcnow()
            }
            
            # Use upsert operation - this will either update existing or create new
            result = await db.database.users.update_one(
                {"uid": uid},
                {
                    "$set": user_document,
                    "$setOnInsert": {
                        "created_at": datetime.utcnow(),
                        "characters": [],
                        "settings": {
                            "notifications_enabled": True,
                            "auto_update": True
                        }
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                print(f"Created new user profile for UID: {uid}")
            elif result.modified_count > 0:
                print(f"Updated existing user profile for UID: {uid}")
            else:
                print(f"User profile for UID: {uid} already up to date")
            
            return True
                
        except Exception as e:
            print(f"Database error while upserting user profile for UID {uid}: {str(e)}")
            return False


# Singleton instance
genshin_client = GenshinClient() 