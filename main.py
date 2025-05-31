from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import asyncio
import os
import json

# MongoDB ObjectId handling
from bson import ObjectId

def custom_json_encoder(obj):
    """Custom JSON encoder to handle MongoDB ObjectId and datetime objects."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
        return str(obj)
    elif str(type(obj)).startswith("<class 'bson."):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class CustomJSONResponse(JSONResponse):
    """Custom JSONResponse that handles MongoDB ObjectId."""
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=custom_json_encoder,
        ).encode("utf-8")

from config import settings
from database import connect_to_mongo, close_mongo_connection, UserProfile, CharacterData, Cache
from genshin_client import genshin_client
from ai_assistant import ai_assistant
from scheduler import scheduler
from materials import materials_db
from exploration_client import ExplorationClient, get_user_exploration, get_exploration_summary
from models import (
    UserCreateRequest, UserResponse, CharacterResponse,
    BuildRecommendationRequest, BuildRecommendationResponse,
    QuestionRequest, QuestionResponse,
    FarmingRouteRequest, FarmingRouteResponse, EnhancedFarmingRouteResponse,
    ExplorationResponse, ExplorationDataResponse, ExplorationSummaryResponse,
    ExplorationCredentialsRequest, SchedulerStatusResponse, SuccessResponse,
    SetupInstructionsResponse, ManualCharacterRequest, RefreshStatusResponse,
    SimpleDamageRequest, SimpleDamageResponse,
    TeamDamageRequest, TeamDamageResponse,
    UserProfileResponse
)
from character_icon_service import CharacterIconService
from farming_route_service import farming_route_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add after the imports section
import json
import os

# Weapon name resolution utility
def load_text_map():
    """Load the text map for resolving nameTextMapHash to actual names."""
    try:
        text_map_path = os.path.join(".enka_py", "assets", "text_map.json")
        if os.path.exists(text_map_path):
            with open(text_map_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load text map: {str(e)}")
    return {}

# Global text map cache
_text_map_cache = None

def get_text_map():
    """Get cached text map or load it."""
    global _text_map_cache
    if _text_map_cache is None:
        _text_map_cache = load_text_map()
    return _text_map_cache

def resolve_weapon_name(weapon_data: Dict[str, Any]) -> str:
    """Resolve weapon name from nameTextMapHash or fallback to existing name."""
    try:
        # Check if we already have a resolved name
        if "name" in weapon_data and weapon_data["name"]:
            return weapon_data["name"]
        
        # Try to resolve from nameTextMapHash
        name_hash = weapon_data.get("nameTextMapHash")
        if name_hash:
            text_map = get_text_map()
            resolved_name = text_map.get(str(name_hash))
            if resolved_name:
                return resolved_name
        
        # Fallback to weapon ID or unknown
        weapon_id = weapon_data.get("itemId", weapon_data.get("id", "Unknown"))
        return f"Weapon_{weapon_id}"
        
    except Exception as e:
        logger.warning(f"Error resolving weapon name: {str(e)}")
        return "Unknown Weapon"

def get_weapon_details(weapon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get comprehensive weapon details with proper name resolution."""
    try:
        weapon_name = resolve_weapon_name(weapon_data)
        
        # Extract weapon stats
        weapon_stats = weapon_data.get("flat", {})
        base_atk = weapon_stats.get("baseAttack", 0)
        
        # Get weapon type from weapon data
        weapon_type = "unknown"
        weapon_type_id = weapon_data.get("weaponType", 0)
        
        # Map weapon type IDs to names (common Genshin weapon types)
        weapon_type_map = {
            1: "sword",
            2: "claymore", 
            3: "polearm",
            4: "bow",
            5: "catalyst"
        }
        weapon_type = weapon_type_map.get(weapon_type_id, "unknown")
        
        # Get substat information
        sub_stat = {}
        weapon_props = weapon_stats.get("weaponStats", [])
        for prop in weapon_props:
            prop_type = prop.get("appendPropId", "")
            prop_value = prop.get("statValue", 0)
            
            # Map common stat types
            stat_type_map = {
                "FIGHT_PROP_ATTACK_PERCENT": "attack_percent",
                "FIGHT_PROP_ELEMENT_MASTERY": "elemental_mastery", 
                "FIGHT_PROP_CHARGE_EFFICIENCY": "energy_recharge",
                "FIGHT_PROP_CRITICAL": "crit_rate",
                "FIGHT_PROP_CRITICAL_HURT": "crit_dmg",
                "FIGHT_PROP_HP_PERCENT": "hp_percent",
                "FIGHT_PROP_DEFENSE_PERCENT": "def_percent"
            }
            
            if prop_type in stat_type_map:
                sub_stat = {
                    "type": stat_type_map[prop_type],
                    "value": prop_value
                }
                break
        
        return {
            "name": weapon_name,
            "type": weapon_type,
            "level": weapon_data.get("level", 1),
            "refinement": weapon_data.get("affixLevel", 1),
            "base_atk": base_atk,
            "sub_stat": sub_stat,
            "rarity": weapon_data.get("rankLevel", 3),
            "ascension": weapon_data.get("promoteLevel", 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting weapon details: {str(e)}")
        return {
            "name": "Unknown Weapon",
            "type": "unknown",
            "level": 1,
            "refinement": 1,
            "base_atk": 0,
            "sub_stat": {},
            "rarity": 3,
            "ascension": 0
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await connect_to_mongo()
    await scheduler.start()
    # Initialize character icon service
    icon_service = CharacterIconService()
    # Mount static files for serving icons
    if not os.path.exists("character_icons"):
        os.makedirs("character_icons")
    app.mount("/icons", StaticFiles(directory="character_icons"), name="icons")
    yield
    # Shutdown
    await scheduler.stop()
    await close_mongo_connection()


app = FastAPI(
    title="Genshin Impact Personal Assistant API",
    description="A comprehensive API for Genshin Impact players with AI-powered assistance",
    version="1.0.0",
    lifespan=lifespan
)

# Configure custom JSON encoder for MongoDB ObjectId
app.default_response_class = CustomJSONResponse

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use configurable origins from settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize character icon service
icon_service = CharacterIconService()

# Mount static files for serving icons
if not os.path.exists("character_icons"):
    os.makedirs("character_icons")
app.mount("/icons", StaticFiles(directory="character_icons"), name="icons")


# User Management Endpoints
@app.post("/users", response_model=SuccessResponse, tags=["Users"])
async def create_user_profile(request: UserCreateRequest, background_tasks: BackgroundTasks):
    """Create a new user profile and fetch initial data."""
    try:
        # Check if user already exists
        existing_user = await UserProfile.get(request.uid)
        if existing_user:
            raise HTTPException(status_code=400, detail="User profile already exists")
        
        # Fetch user data from Genshin API
        # This will automatically create/update the user profile via _upsert_user_profile
        async with genshin_client:
            user_data = await genshin_client.fetch_user_data(request.uid)
        
        # Check if fetch was successful
        if "error" in user_data:
            raise HTTPException(status_code=400, detail=f"Failed to fetch user data: {user_data['error']}")
        
        # Extract player info for response
        player_info = user_data.get("player_info", {})
        
        return SuccessResponse(
            message=f"User profile created successfully for UID {request.uid}",
            data={
                "uid": request.uid, 
                "nickname": player_info.get("nickname", "Unknown"),
                "level": player_info.get("level", 0),
                "character_count": user_data.get("character_count", 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{uid}", response_model=UserProfileResponse, tags=["Users"])
async def get_user_profile(uid: int):
    """Get user profile data without character details. Use /users/{uid}/characters for character data."""
    try:
        user = await UserProfile.get(uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        characters = user.get("characters", [])
        
        # Profile data is now clean - character-related fields are excluded at source
        profile_data = user["profile_data"].copy()
        
        # Return only profile data (without character details) and character count
        return UserProfileResponse(
            profile_data=profile_data,
            character_count=len(characters)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/{uid}/refresh", response_model=SuccessResponse, tags=["Users"])
async def refresh_user_data(uid: int, background_tasks: BackgroundTasks, force: bool = False, merge_characters: bool = True):
    """
    Manually refresh user data from Enka Network.
    
    Args:
        uid: User ID to refresh
        force: Force refresh even if data is recent (default: False)
        merge_characters: Merge new characters with existing ones instead of replacing (default: True)
                         - True: Preserves existing characters, updates/adds new ones
                         - False: Completely replaces character list with new data
        
    Returns:
        Success response with refresh status
    """
    try:
        user = await UserProfile.get(uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if refresh is needed (unless forced)
        if not force:
            last_fetch = user.get("last_fetch")
            if last_fetch:
                time_since_fetch = datetime.utcnow() - last_fetch
                if time_since_fetch.total_seconds() < 300:  # 5 minutes cooldown
                    raise HTTPException(
                        status_code=429, 
                        detail=f"Data was refreshed recently. Please wait {300 - int(time_since_fetch.total_seconds())} seconds or use force=true"
                    )
        
        # Start background refresh
        background_tasks.add_task(perform_user_refresh, uid, merge_characters)
        
        return SuccessResponse(
            message=f"Refresh started for user {uid}. Check /users/{uid}/refresh-status for progress.",
            data={
                "uid": uid,
                "refresh_started": True,
                "merge_characters": merge_characters,
                "status_endpoint": f"/users/{uid}/refresh-status"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{uid}/refresh-status", response_model=RefreshStatusResponse, tags=["Users"])
async def get_refresh_status(uid: int):
    """Get the current refresh status for a user."""
    try:
        # Check cache for refresh status
        status_key = f"refresh_status_{uid}"
        status = await Cache.get(status_key)
        
        if not status:
            # No active refresh, check last fetch time
            user = await UserProfile.get(uid)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return RefreshStatusResponse(
                uid=uid,
                status="idle",
                message="No active refresh in progress",
                last_fetch=user.get("last_fetch")
            )
        
        return RefreshStatusResponse(
            uid=uid,
            **status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def perform_user_refresh(uid: int, merge_characters: bool = True):
    """
    Background task to perform user data refresh.
    
    Args:
        uid: User ID to refresh
        merge_characters: Merge new characters with existing ones instead of replacing
    """
    status_key = f"refresh_status_{uid}"
    
    try:
        # Set initial status
        await Cache.set(status_key, {
            "status": "starting",
            "message": "Initializing refresh...",
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0
        }, ttl=600)  # 10 minutes TTL
        
        # Update status: Fetching data
        await Cache.set(status_key, {
            "status": "fetching",
            "message": "Fetching data from Enka Network...",
            "started_at": datetime.utcnow().isoformat(),
            "progress": 25
        }, ttl=600)
        
        # Fetch fresh data using genshin_client directly
        async with genshin_client:
            fresh_data = await genshin_client.fetch_user_data(uid, merge_characters=merge_characters)
        
        if "error" in fresh_data:
            await Cache.set(status_key, {
                "status": "error",
                "message": f"Failed to fetch data: {fresh_data['error']}",
                "error": fresh_data['error'],
                "completed_at": datetime.utcnow().isoformat(),
                "progress": 0
            }, ttl=600)
            return
        
        # Update status: Processing data
        await Cache.set(status_key, {
            "status": "processing",
            "message": "Processing and saving data...",
            "started_at": datetime.utcnow().isoformat(),
            "progress": 75
        }, ttl=600)
        
        # The fetch_user_data already processes and saves the data
        # But let's verify it was saved correctly
        updated_user = await UserProfile.get(uid)
        if not updated_user:
            raise Exception("Failed to verify user data after refresh")
        
        # Get character count for status
        characters = await CharacterData.get_all_user_characters(uid)
        character_count = len(characters)
        
        # Update status: Complete
        merge_mode = "merged" if merge_characters else "replaced"
        await Cache.set(status_key, {
            "status": "completed",
            "message": f"Refresh completed successfully. {merge_mode.capitalize()} {character_count} characters.",
            "completed_at": datetime.utcnow().isoformat(),
            "progress": 100,
            "data": {
                "character_count": character_count,
                "merge_mode": merge_mode,
                "nickname": fresh_data.get("player_info", {}).get("nickname", "Unknown"),
                "level": fresh_data.get("player_info", {}).get("level", 0)
            }
        }, ttl=600)
        
    except Exception as e:
        # Update status: Error
        await Cache.set(status_key, {
            "status": "error",
            "message": f"Refresh failed: {str(e)}",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
            "progress": 0
        }, ttl=600)


@app.post("/users/{uid}/refresh-force", response_model=SuccessResponse, tags=["Users"])
async def force_refresh_user_data(uid: int, background_tasks: BackgroundTasks, merge_characters: bool = True):
    """
    Force refresh user data, bypassing cooldown restrictions.
    
    Args:
        uid: User ID to refresh
        merge_characters: Merge new characters with existing ones instead of replacing (default: True)
                         - True: Preserves existing characters, updates/adds new ones
                         - False: Completely replaces character list with new data
    
    Use this when you need to refresh data immediately regardless of when it was last updated.
    """
    try:
        user = await UserProfile.get(uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Start background refresh with force=True
        background_tasks.add_task(perform_user_refresh, uid, merge_characters)
        
        return SuccessResponse(
            message=f"Force refresh started for user {uid}. Check /users/{uid}/refresh-status for progress.",
            data={
                "uid": uid,
                "force_refresh": True,
                "refresh_started": True,
                "merge_characters": merge_characters,
                "status_endpoint": f"/users/{uid}/refresh-status"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{uid}/raw", tags=["Users"])
async def get_user_raw_data(uid: int):
    """Get raw user data exactly as stored in database."""
    try:
        user = await UserProfile.get(uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return complete raw data from database
        return {
            "uid": user["uid"],
            "profile_data": user["profile_data"],
            "characters": user.get("characters", []),
            "settings": user.get("settings", {}),
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "last_fetch": user["last_fetch"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Character Endpoints
@app.get("/users/{uid}/characters", response_model=List[CharacterResponse], tags=["Characters"])
async def get_user_characters(uid: int):
    """Get all characters for a user."""
    try:
        characters = await CharacterData.get_all_user_characters(uid)
        
        # Return character data exactly as stored in database with icon info
        result = []
        for char in characters:
            character_id = str(char.get("avatarId", 0))
            
            # Get icon information
            icon_name = icon_service.get_character_icon_name(character_id)
            icon_url = icon_service.get_icon_url(icon_name) if icon_name else None
            local_icon_path = icon_service.get_icon_file_path(character_id)
            
            char_response = CharacterResponse(
                id=char.get("avatarId", 0),
                name=char.get("name", "Unknown"),
                element=char.get("element", "Unknown"),
                rarity=char.get("rarity", 5),
                level=char.get("level", 1),
                friendship=char.get("friendship", 10),
                constellation=char.get("constellation", 0),
                weapon=char.get("weapon", {}),
                artifacts=char.get("artifacts", []),
                talents=char.get("talents", []),
                stats=char.get("stats", {}),
                icon_url=icon_url,
                local_icon_available=local_icon_path is not None
            )
            result.append(char_response)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{uid}/characters/{character_name}", response_model=CharacterResponse, tags=["Characters"])
async def get_character_details(uid: int, character_name: str):
    """Get detailed information for a specific character."""
    try:
        # Get character from database instead of fetching fresh data
        character = await CharacterData.get_character_by_name(uid, character_name)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Return character data exactly as stored in database
        return CharacterResponse(
            id=character.get("avatarId", 0),
            name=character.get("name", "Unknown"),
            element=character.get("element", "Unknown"),
            rarity=character.get("rarity", 5),
            level=character.get("level", 1),
            friendship=character.get("friendship", 10),
            constellation=character.get("constellation", 0),
            weapon=character.get("weapon"),
            artifacts=character.get("artifacts", []),
            talents=character.get("talents", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{uid}/characters/raw", tags=["Characters"])
async def get_user_characters_raw(uid: int):
    """Get raw character data exactly as stored in database."""
    try:
        characters = await CharacterData.get_all_user_characters(uid)
        
        # Return complete raw character data from database
        return {
            "uid": uid,
            "characters": characters,
            "character_count": len(characters)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{uid}/characters/{character_name}/raw", tags=["Characters"])
async def get_character_raw_data(uid: int, character_name: str):
    """Get raw character data exactly as stored in database."""
    try:
        character = await CharacterData.get_character_by_name(uid, character_name)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Return complete raw character data from database
        return {
            "uid": uid,
            "character": character
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/characters/setup-instructions", response_model=SetupInstructionsResponse, tags=["Characters"])
async def get_setup_instructions():
    """Get instructions for setting up Character Showcase for automated data fetching."""
    try:
        instructions = genshin_client.get_setup_instructions()
        return instructions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{uid}/characters/hybrid", tags=["Characters"])
async def get_all_characters_hybrid(uid: int):
    """
    Get ALL characters using hybrid approach:
    - Automated data from Character Showcase (up to 8 characters)
    - Manual data for additional characters
    
    This solves the limitation of only getting showcased characters!
    """
    try:
        # Get characters from database instead of fetching fresh data
        characters = await CharacterData.get_all_user_characters(uid)
        
        # Separate automated vs manual characters based on data completeness
        automated_characters = []
        manual_characters = []
        
        for char in characters:
            # Characters with full artifact data are likely from automated showcase
            if char.get("artifacts") and len(char.get("artifacts", [])) >= 4:
                automated_characters.append(char)
            else:
                manual_characters.append(char)
        
        return {
            "uid": uid,
            "total_characters": len(characters),
            "automated_characters": {
                "count": len(automated_characters),
                "characters": automated_characters
            },
            "manual_characters": {
                "count": len(manual_characters),
                "characters": manual_characters
            },
            "all_characters": characters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/characters/add-manually", response_model=SuccessResponse, tags=["Characters"])
async def add_character_manually(request: ManualCharacterRequest):
    """
    Add character data manually for characters not in your showcase.
    
    Use this to get COMPLETE character coverage beyond the 8-character showcase limit.
    """
    try:
        # Convert request to dictionary
        character_data = request.dict()
        
        # Add the character
        result = await genshin_client.add_character_manually(request.uid, character_data)
        
        return SuccessResponse(
            message=f"Character {request.name} added successfully for UID {request.uid}",
            data={"avatarId": result.get("avatarId"), "name": result.get("name")}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/characters/template", tags=["Characters"])
async def get_character_template():
    """Get a template for manual character data input."""
    try:
        template = genshin_client.create_character_template()
        
        instructions = """
        HYBRID APPROACH - Best of Both Worlds:
        
        1. Set up Character Showcase for your TOP 8 characters (automated)
        2. Use this template to add remaining characters manually
        3. Get COMPLETE character coverage with minimal effort
        
        Template Usage:
        1. Fill in all required fields (name, element, level, etc.)
        2. Add weapon data with base attack and substats
        3. Add all 5 artifacts with main stats and substats
        4. Include talent levels
        5. POST this data to /characters/add-manually
        
        Benefits:
        ✅ Automated data for your main characters
        ✅ Manual input for complete roster coverage
        ✅ Same mathematical accuracy for all characters
        ✅ No character limit restrictions
        """
        
        return {
            "template": template,
            "instructions": instructions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Exploration Endpoints
@app.get("/users/{uid}/exploration", response_model=ExplorationResponse, tags=["Exploration"])
async def get_exploration_progress(uid: int):
    """Get exploration progress for all regions (legacy endpoint)."""
    try:
        exploration_data = await genshin_client.get_exploration_progress(uid)
        
        return ExplorationResponse(
            regions=exploration_data["regions"],
            average_exploration=exploration_data["average_exploration"],
            total_regions=exploration_data["total_regions"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/exploration/detailed/{uid}", response_model=ExplorationDataResponse, tags=["Exploration"])
async def get_detailed_exploration_data(uid: int, credentials: ExplorationCredentialsRequest):
    """
    Get detailed exploration data using HoYoLAB API.
    
    Requires HoYoLAB cookies (ltuid and ltoken) which can be obtained from:
    1. Go to hoyolab.com
    2. Login to your account
    3. Press F12 -> Application -> Cookies -> https://www.hoyolab.com
    4. Copy ltuid and ltoken values
    """
    try:
        async with ExplorationClient() as client:
            client.set_cookies(credentials.ltuid, credentials.ltoken, credentials.cookie_token)
            
            exploration_data = await client.get_detailed_exploration(uid)
            
            if "error" in exploration_data:
                raise HTTPException(status_code=400, detail=exploration_data["error"])
            
            return ExplorationDataResponse(**exploration_data)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exploration data: {str(e)}")


@app.post("/exploration/summary/{uid}", response_model=ExplorationSummaryResponse, tags=["Exploration"])
async def get_exploration_summary_endpoint(uid: int, credentials: ExplorationCredentialsRequest):
    """
    Get exploration summary using HoYoLAB API.
    
    Provides a concise overview of exploration progress including:
    - Total regions and fully explored count
    - Average exploration percentage
    - Chest, waypoint, and domain counts
    - Oculi collection progress
    """
    try:
        summary = await get_exploration_summary(
            uid, 
            credentials.ltuid, 
            credentials.ltoken, 
            credentials.cookie_token
        )
        
        if "error" in summary:
            raise HTTPException(status_code=400, detail=summary["error"])
        
        return ExplorationSummaryResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exploration summary: {str(e)}")


@app.get("/exploration/instructions", tags=["Exploration"])
async def get_exploration_setup_instructions():
    """Get instructions for setting up HoYoLAB cookies for exploration data access."""
    return {
        "title": "HoYoLAB Cookie Setup for Exploration Data",
        "description": "To access detailed exploration data, you need to provide your HoYoLAB authentication cookies.",
        "steps": [
            "1. Go to https://hoyolab.com in your browser",
            "2. Login to your HoYoVerse/miHoYo account",
            "3. Press F12 to open Developer Tools",
            "4. Go to Application tab -> Cookies -> https://www.hoyolab.com",
            "5. Find and copy the values for 'ltuid' and 'ltoken'",
            "6. Optionally copy 'cookie_token' for additional features",
            "7. Use these values in the exploration API endpoints"
        ],
        "requirements": [
            "Your HoYoLAB profile must be set to public",
            "The target UID's profile must also be public",
            "Cookies are valid for several months but may need refreshing"
        ],
        "security_notes": [
            "Never share your cookies with untrusted sources",
            "These cookies provide access to your HoYoLAB account",
            "Consider using a secondary account for API access"
        ],
        "data_available": [
            "World exploration percentages by region",
            "Oculi collection progress (Anemoculi, Geoculi, etc.)",
            "Chest, waypoint, and domain counts",
            "Serenitea Pot (Teapot) information",
            "Real-time notes (resin, expeditions, commissions)",
            "Reputation and offering levels"
        ]
    }


# AI Assistant Endpoints
@app.post("/damage/character", response_model=SimpleDamageResponse, tags=["Damage Calculator"])
async def calculate_character_damage(request: SimpleDamageRequest):
    """
    Calculate damage for a single character without team buffs.
    
    This endpoint provides clean, accurate damage calculations inspired by Akasha.cv:
    - Uses standard Genshin Impact damage formulas
    - Extracts character stats from your database
    - Calculates damage for all abilities (Normal, Skill, Burst)
    - No elemental reactions (single character only)
    - No team buffs - pure character performance
    - Raw damage calculations only
    """
    try:
        from simple_damage_calculator import damage_calculator, EnemyStats
        from character_stats_extractor import stats_extractor
        from database import CharacterData
        
        # Get character data from database
        character_data = await CharacterData.get_character_by_name(request.uid, request.character_name)
        if not character_data:
            raise HTTPException(status_code=404, detail="Character not found in your account")
        
        # Extract character stats
        character_stats = stats_extractor.extract_stats_from_database(character_data, request.character_name)
        
        # Set up enemy stats
        character_element = damage_calculator.get_character_element(request.character_name)
        
        # Create elemental resistance dictionary
        elemental_resistances = {
            "pyro": 10.0, "hydro": 10.0, "electro": 10.0, "cryo": 10.0,
            "anemo": 10.0, "geo": 10.0, "dendro": 10.0
        }
        
        # Update with specific resistances if provided
        if request.enemy_resistances:
            for element in elemental_resistances:
                if element in request.enemy_resistances:
                    elemental_resistances[element] = request.enemy_resistances[element]
        
        enemy_stats = EnemyStats(
            level=request.enemy_level,
            elemental_res=elemental_resistances,
            physical_res=request.enemy_resistances.get("physical", 10.0) if request.enemy_resistances else 10.0,
            def_reduction=0.0  # No team buffs for single character
        )
        
        # No reactions for single character damage calculation
        reactions_to_use = []
        
        # Calculate damage
        damage_result = damage_calculator.calculate_character_damage(
            character_name=request.character_name,
            character_stats=character_stats,
            enemy_stats=enemy_stats,
            reactions=reactions_to_use
        )
        
        # Get build summary
        build_summary = stats_extractor.get_character_build_summary(character_stats)
        
        # Return clean response focused on single character damage
        return SimpleDamageResponse(
            character_name=damage_result["character_name"],
            element=damage_result["element"],
            character_stats=build_summary,
            damage_breakdown=damage_result["damage_breakdown"],
            enemy_info={
                "level": enemy_stats.level,
                "elemental_resistance": enemy_stats.elemental_res,
                "physical_resistance": enemy_stats.physical_res,
                "defense_multiplier": enemy_stats.get_defense_multiplier(character_stats.level)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in character damage calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Damage calculation failed: {str(e)}")


@app.post("/damage/team", response_model=TeamDamageResponse, tags=["Damage Calculator"])
async def calculate_team_damage(request: TeamDamageRequest):
    """
    Calculate damage for a team composition with buffs and synergies.
    
    This endpoint provides comprehensive team damage analysis inspired by Akasha.cv:
    - Calculates main DPS damage without buffs
    - Analyzes team buffs and synergies
    - Applies team buffs to calculate buffed damage
    - Provides team synergy score and elemental coverage
    - Generates optimal rotation guide
    - **Automatically analyzes and applies elemental reactions** based on team composition
    - Easy to use - just specify main DPS and team members
    """
    try:
        from simple_damage_calculator import damage_calculator, EnemyStats
        from character_stats_extractor import stats_extractor
        from team_buff_calculator import team_buff_calculator, TeamComposition
        from database import CharacterData
        
        # Validate team composition
        if request.main_dps not in request.team_composition:
            raise HTTPException(status_code=400, detail="Main DPS must be included in team composition")
        
        # Get main DPS character data
        main_dps_data = await CharacterData.get_character_by_name(request.uid, request.main_dps)
        if not main_dps_data:
            raise HTTPException(status_code=404, detail=f"Main DPS character '{request.main_dps}' not found in your account")
        
        # Extract main DPS stats
        main_dps_stats = stats_extractor.extract_stats_from_database(main_dps_data, request.main_dps)
        main_dps_element = damage_calculator.get_character_element(request.main_dps)
        
        # Automatically analyze team reactions
        reaction_analysis = damage_calculator.analyze_team_reactions(request.team_composition, request.main_dps)
        
        # Use automatically detected reactions
        reactions_to_use = reaction_analysis["recommended_reactions"]
        
        # Set up enemy stats (base)
        # Create elemental resistance dictionary
        base_elemental_resistances = {
            "pyro": 10.0, "hydro": 10.0, "electro": 10.0, "cryo": 10.0,
            "anemo": 10.0, "geo": 10.0, "dendro": 10.0
        }
        
        # Update with specific resistances if provided
        if request.enemy_resistances:
            for element in base_elemental_resistances:
                if element in request.enemy_resistances:
                    base_elemental_resistances[element] = request.enemy_resistances[element]
        
        base_enemy_stats = EnemyStats(
            level=request.enemy_level,
            elemental_res=base_elemental_resistances,
            physical_res=request.enemy_resistances.get("physical", 10.0) if request.enemy_resistances else 10.0,
            def_reduction=0.0
        )
        
        # Calculate base damage (no team buffs)
        base_damage_result = damage_calculator.calculate_character_damage(
            character_name=request.main_dps,
            character_stats=main_dps_stats,
            enemy_stats=base_enemy_stats,
            reactions=reactions_to_use
        )
        
        # Set up team composition
        team_members = [char for char in request.team_composition if char != request.main_dps]
        team_comp = TeamComposition(
            main_dps=request.main_dps,
            sub_dps=team_members[0] if len(team_members) > 0 else None,
            support1=team_members[1] if len(team_members) > 1 else None,
            support2=team_members[2] if len(team_members) > 2 else None
        )
        
        # Calculate team buffs
        team_buffs_result = team_buff_calculator.calculate_team_buffs(team_comp, main_dps_element)
        
        # Apply team buffs to character stats
        buffed_stats = main_dps_stats
        total_multipliers = team_buffs_result["total_multipliers"]
        
        # Apply ATK buffs
        if total_multipliers["atk_percent"] > 0:
            buffed_stats.atk_percent += total_multipliers["atk_percent"]
        if total_multipliers["atk_flat"] > 0:
            buffed_stats.flat_atk += total_multipliers["atk_flat"]
        
        # Apply damage buffs
        if total_multipliers["elemental_dmg_bonus"] > 0:
            buffed_stats.elemental_dmg_bonus += total_multipliers["elemental_dmg_bonus"]
        
        # Apply crit buffs
        if total_multipliers["crit_rate"] > 0:
            buffed_stats.crit_rate += total_multipliers["crit_rate"]
        if total_multipliers["crit_dmg"] > 0:
            buffed_stats.crit_dmg += total_multipliers["crit_dmg"]
        
        # Apply EM buffs
        if total_multipliers["elemental_mastery"] > 0:
            buffed_stats.elemental_mastery += total_multipliers["elemental_mastery"]
        
        # Apply resistance reduction to enemy
        buffed_elemental_resistances = base_elemental_resistances.copy()
        
        # Check for VV shred (40% resistance reduction)
        has_vv_shred = any("res_reduction" in buff.buff_type for buffs in team_buffs_result["categorized_buffs"].values() for buff in buffs)
        if has_vv_shred:
            # Apply VV shred to the main DPS element
            buffed_elemental_resistances[main_dps_element] -= 40.0
        
        # Check for Zhongli shred (20% universal resistance reduction)
        has_zhongli_shred = any("zhongli" in buff.source.lower() for buffs in team_buffs_result["categorized_buffs"].values() for buff in buffs)
        zhongli_def_reduction = 20.0 if has_zhongli_shred else 0.0
        
        buffed_enemy_stats = EnemyStats(
            level=request.enemy_level,
            elemental_res=buffed_elemental_resistances,
            physical_res=base_enemy_stats.physical_res,
            def_reduction=zhongli_def_reduction
        )
        
        # Calculate buffed damage
        buffed_damage_result = damage_calculator.calculate_character_damage(
            character_name=request.main_dps,
            character_stats=buffed_stats,
            enemy_stats=buffed_enemy_stats,
            reactions=reactions_to_use
        )
        
        # Get build summaries
        base_build_summary = stats_extractor.get_character_build_summary(main_dps_stats)
        buffed_build_summary = stats_extractor.get_character_build_summary(buffed_stats)
        
        # Enhanced response with reaction analysis
        response_data = TeamDamageResponse(
            main_dps=request.main_dps,
            team_composition=request.team_composition,
            main_dps_damage={
                "character_name": base_damage_result["character_name"],
                "element": base_damage_result["element"],
                "character_stats": base_build_summary,
                "damage_breakdown": base_damage_result["damage_breakdown"]
            },
            team_buffs=team_buffs_result,
            buffed_damage={
                "character_name": buffed_damage_result["character_name"],
                "element": buffed_damage_result["element"],
                "character_stats": buffed_build_summary,
                "damage_breakdown": buffed_damage_result["damage_breakdown"],
                "damage_increase": {
                    ability: {
                        "base_average": base_damage_result["damage_breakdown"][ability]["average"],
                        "buffed_average": buffed_damage_result["damage_breakdown"][ability]["average"],
                        "increase_percent": ((buffed_damage_result["damage_breakdown"][ability]["average"] / base_damage_result["damage_breakdown"][ability]["average"]) - 1) * 100 if base_damage_result["damage_breakdown"][ability]["average"] > 0 else 0
                    }
                    for ability in ["normal_attack", "charged_attack", "elemental_skill", "elemental_burst"]
                    if ability in base_damage_result["damage_breakdown"] and ability in buffed_damage_result["damage_breakdown"]
                }
            },
            team_synergy_score=team_buffs_result["synergy_score"],
            elemental_coverage=team_buffs_result["elemental_coverage"],
            rotation_guide=team_buffs_result["recommended_rotation"],
            calculation_method="team_akasha_inspired_with_auto_reactions"
        )
        
        # Add reaction analysis to the response
        response_dict = response_data.dict()
        response_dict["reaction_analysis"] = reaction_analysis
        response_dict["reactions_used"] = reactions_to_use
        response_dict["auto_detected_reactions"] = True
        
        return response_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in team damage calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Team damage calculation failed: {str(e)}")


@app.post("/ai/farming-route", response_model=FarmingRouteResponse, tags=["AI Assistant"])
async def get_farming_route(request: FarmingRouteRequest):
    """Get optimized farming routes for materials."""
    try:
        result = await ai_assistant.get_farming_route(request.materials, request.uid)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return FarmingRouteResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/farming-route-enhanced", response_model=EnhancedFarmingRouteResponse, tags=["AI Assistant"])
async def get_enhanced_farming_route(request: FarmingRouteRequest):
    """
    Get enhanced farming routes with HoYoLAB interactive map integration.
    
    This endpoint provides:
    - Structured map markers with coordinates for frontend integration
    - Custom marker injection scripts for HoYoLAB interactive map
    - Optimized daily and weekly farming routes
    - Frontend-ready data structures for easy consumption
    - Complete farming location details with respawn timers
    """
    try:
        result = await farming_route_service.generate_enhanced_farming_route(
            request.materials, 
            request.uid
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Materials and Farming Endpoints
@app.get("/materials/character/{character_name}", tags=["Materials"])
async def get_character_materials(character_name: str):
    """Get all materials needed for a character's ascension and talents."""
    try:
        materials = await materials_db.get_character_materials(character_name)
        if not materials:
            raise HTTPException(status_code=404, detail="Character not found")
        
        return materials
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/materials/farming-route/{character_name}", tags=["Materials"])
async def get_character_farming_route(character_name: str):
    """Get optimized farming route for a specific character."""
    try:
        route = await materials_db.get_farming_route_for_character(character_name)
        if "error" in route:
            raise HTTPException(status_code=404, detail=route["error"])
        
        return route
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/materials/region/{region}", tags=["Materials"])
async def get_materials_by_region(region: str):
    """Get all materials available in a specific region."""
    try:
        materials = await materials_db.get_materials_by_region(region)
        if "error" in materials:
            raise HTTPException(status_code=404, detail=materials["error"])
        
        return materials
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Endpoints
@app.get("/system/scheduler", response_model=SchedulerStatusResponse, tags=["System"])
async def get_scheduler_status():
    """Get scheduler status and information."""
    try:
        status = scheduler.get_scheduler_status()
        return SchedulerStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Genshin Impact Assistant API is running"}


@app.get("/api/endpoints", tags=["System"])
async def get_api_endpoints_info():
    """Get information about all available API endpoints and their data sources."""
    return {
        "title": "Genshin Impact API Endpoints",
        "description": "Complete list of available endpoints and their data sources",
        "user_endpoints": {
            "/users/{uid}": {
                "description": "Get user profile with transformed data for frontend compatibility",
                "data_source": "Database (transformed)",
                "response_model": "UserResponse"
            },
            "/users/{uid}/raw": {
                "description": "Get raw user data exactly as stored in database",
                "data_source": "Database (raw)",
                "response_model": "Raw JSON"
            },
            "/users/{uid}/refresh": {
                "description": "Manually refresh user data from Enka Network (background processing)",
                "data_source": "Enka Network API",
                "response_model": "SuccessResponse",
                "features": ["Background processing", "Progress tracking", "5-minute cooldown", "Force option", "Character merge/replace option"],
                "parameters": {
                    "force": "bool - Force refresh even if data is recent (default: False)",
                    "merge_characters": "bool - Merge new characters with existing ones instead of replacing (default: True)"
                }
            },
            "/users/{uid}/refresh-force": {
                "description": "Force refresh user data, bypassing cooldown restrictions",
                "data_source": "Enka Network API", 
                "response_model": "SuccessResponse",
                "features": ["Bypasses cooldown", "Background processing", "Progress tracking", "Character merge/replace option"],
                "parameters": {
                    "merge_characters": "bool - Merge new characters with existing ones instead of replacing (default: True)"
                }
            },
            "/users/{uid}/refresh-status": {
                "description": "Get current refresh status and progress",
                "data_source": "Cache + Database",
                "response_model": "RefreshStatusResponse",
                "features": ["Real-time status", "Progress percentage", "Error details"]
            }
        },
        "character_endpoints": {
            "/users/{uid}/characters": {
                "description": "Get all characters with transformed data for frontend compatibility",
                "data_source": "Database (transformed)",
                "response_model": "List[CharacterResponse]"
            },
            "/users/{uid}/characters/raw": {
                "description": "Get raw character data exactly as stored in database",
                "data_source": "Database (raw)",
                "response_model": "Raw JSON"
            },
            "/users/{uid}/characters/{character_name}": {
                "description": "Get specific character with transformed data",
                "data_source": "Database (transformed)",
                "response_model": "CharacterResponse"
            },
            "/users/{uid}/characters/{character_name}/raw": {
                "description": "Get raw data for specific character",
                "data_source": "Database (raw)",
                "response_model": "Raw JSON"
            },
            "/users/{uid}/characters/hybrid": {
                "description": "Get characters separated by automated vs manual data",
                "data_source": "Database (categorized)",
                "response_model": "Hybrid JSON"
            }
        },
        "data_structure": {
            "database_storage": {
                "user_document": {
                    "uid": "int",
                    "profile_data": "Enka Network player info (raw)",
                    "characters": "Array of character data (raw)",
                    "settings": "User preferences",
                    "created_at": "datetime",
                    "updated_at": "datetime",
                    "last_fetch": "datetime"
                },
                "character_data": {
                    "avatarId": "Enka Network character ID",
                    "name": "Character name",
                    "element": "Character element",
                    "level": "Character level",
                    "friendship": "Friendship level",
                    "constellation": "Constellation level",
                    "weapon": "Weapon data (raw)",
                    "artifacts": "Artifact data (raw)",
                    "talents": "Talent data (raw)",
                    "stats": "Fight properties (raw)",
                    "updated_at": "datetime"
                }
            }
        },
        "recommendations": {
            "frontend_usage": [
                "Use /raw endpoints for complete data access",
                "Use regular endpoints for simplified frontend integration",
                "Raw data preserves all original field names from Enka Network",
                "Transformed data uses consistent naming for UI components"
            ],
            "character_refresh_behavior": {
                "merge_characters=true": [
                    "Preserves existing characters that aren't in the new data",
                    "Updates existing characters if they match by avatarId",
                    "Adds new characters that don't exist yet",
                    "Ideal for maintaining character history and manual additions"
                ],
                "merge_characters=false": [
                    "Completely replaces the character list with new data",
                    "Removes any characters not in the current Enka showcase",
                    "Legacy behavior - use only if you want a clean slate",
                    "May lose manually added characters or characters not in showcase"
                ]
            }
        },
        "ai_assistant_endpoints": {
            "/ai/question": {
                "description": "Ask the AI assistant any Genshin Impact question with enhanced analysis",
                "data_source": "AI + Database + Google Search",
                "response_model": "QuestionResponse",
                "features": ["Enhanced character detection", "Team composition analysis", "Personalized responses", "Mathematical accuracy"],
                "enhanced_capabilities": [
                    "Comprehensive character name recognition (all regions)",
                    "Intelligent question pattern detection",
                    "Player roster analysis for team building",
                    "Context-aware responses with character data",
                    "Specialized team composition assistance"
                ]
            },
            "/ai/team-recommendation": {
                "description": "Get specialized team recommendations for a specific character",
                "data_source": "AI + Player Roster + Meta Analysis",
                "response_model": "TeamRecommendationResponse",
                "features": ["Personalized team building", "Multiple composition options", "Role analysis", "Rotation guides"],
                "parameters": {
                    "character_name": "string - Character to build team around (required)",
                    "uid": "int - Player UID for personalized recommendations (optional)",
                    "content_type": "string - Content type: general, abyss, domain, boss (optional)"
                }
            },
            "/ai/team-synergy": {
                "description": "Analyze synergy and effectiveness of a team composition",
                "data_source": "AI + Character Builds + Mathematical Analysis",
                "response_model": "TeamSynergyResponse", 
                "features": ["Elemental reaction analysis", "Role distribution evaluation", "Numerical scoring", "Optimization suggestions"],
                "parameters": {
                    "team_composition": "array - List of 2-4 character names (required)",
                    "uid": "int - Player UID for build-specific analysis (optional)"
                }
            },
            "/ai/character-analysis": {
                "description": "Comprehensive character analysis with mathematical formulas",
                "data_source": "AI + Damage Calculators + Build Analysis",
                "response_model": "CharacterAnalysisResponse",
                "features": ["Mathematical damage calculations", "Build efficiency scoring", "Investment priorities", "Action plans"]
            },
            "/ai/build-recommendation": {
                "description": "Get AI-powered build recommendations with damage analysis",
                "data_source": "AI + Google Search + Mathematical Analysis",
                "response_model": "BuildRecommendationResponse",
                "features": ["Meta build analysis", "Artifact optimization", "Weapon recommendations", "Investment guidance"]
            }
        },
        "damage_calculator_endpoints": {
            "/damage/character": {
                "description": "Calculate damage for a single character without team buffs",
                "data_source": "Mathematical Engine + Character Database",
                "response_model": "SimpleDamageResponse",
                "features": ["Real game formulas", "Universal character support", "Precise calculations", "Build analysis"]
            },
            "/damage/team": {
                "description": "Calculate team damage with buffs and elemental reactions",
                "data_source": "Mathematical Engine + Team Analysis + Character Database",
                "response_model": "TeamDamageResponse",
                "features": ["Auto reaction detection", "Team buff analysis", "Rotation optimization", "Synergy scoring"]
            }
        }
    }


# Character Icon Endpoints
@app.get("/characters", tags=["Character Icons"])
async def list_all_characters():
    """Get list of all available characters with their basic info."""
    try:
        characters = icon_service.list_available_characters()
        return {
            "total_characters": len(characters),
            "characters": characters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/characters/{character_id}/info", tags=["Character Icons"])
async def get_character_info(character_id: str):
    """Get detailed information for a specific character."""
    try:
        character_info = icon_service.get_character_info(character_id)
        if not character_info:
            raise HTTPException(status_code=404, detail="Character not found")
        return character_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/characters/{character_id}/icon", tags=["Character Icons"])
async def get_character_icon(character_id: str):
    """Get character icon file. Downloads if not available locally."""
    try:
        # Check if icon exists locally
        local_path = icon_service.get_icon_file_path(character_id)
        
        if local_path and os.path.exists(local_path):
            return FileResponse(
                local_path,
                media_type="image/png",
                filename=f"character_{character_id}.png"
            )
        
        # Download icon if not available
        downloaded_path = await icon_service.download_character_icon(character_id)
        if downloaded_path and os.path.exists(downloaded_path):
            return FileResponse(
                downloaded_path,
                media_type="image/png",
                filename=f"character_{character_id}.png"
            )
        
        raise HTTPException(status_code=404, detail="Character icon not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/characters/{character_id}/download-icon", tags=["Character Icons"])
async def download_character_icon(character_id: str, background_tasks: BackgroundTasks, force_redownload: bool = False):
    """Download character icon in the background."""
    try:
        character_info = icon_service.get_character_info(character_id)
        if not character_info:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Add download task to background
        background_tasks.add_task(icon_service.download_character_icon, character_id, force_redownload)
        
        return {
            "message": f"Download started for character {character_id}",
            "character_info": character_info,
            "force_redownload": force_redownload
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/characters/download-all-icons", tags=["Character Icons"])
async def download_all_character_icons(background_tasks: BackgroundTasks, force_redownload: bool = False):
    """Download all character icons in the background."""
    try:
        total_characters = len(icon_service.characters_data)
        
        # Add download task to background
        background_tasks.add_task(icon_service.download_all_character_icons, force_redownload)
        
        return {
            "message": f"Download started for all {total_characters} character icons",
            "total_characters": total_characters,
            "force_redownload": force_redownload,
            "status": "Download running in background"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/characters/{character_id}/icon-url", tags=["Character Icons"])
async def get_character_icon_url(character_id: str):
    """Get the direct URL to character icon on Enka Network."""
    try:
        icon_name = icon_service.get_character_icon_name(character_id)
        if not icon_name:
            raise HTTPException(status_code=404, detail="Character not found")
        
        icon_url = icon_service.get_icon_url(icon_name)
        local_path = icon_service.get_icon_file_path(character_id)
        
        return {
            "character_id": character_id,
            "icon_name": icon_name,
            "remote_url": icon_url,
            "local_available": local_path is not None,
            "local_path": local_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/characters/icons/status", tags=["Character Icons"])
async def get_icons_download_status():
    """Get status of downloaded character icons."""
    try:
        total_characters = len(icon_service.characters_data)
        downloaded_count = 0
        missing_icons = []
        
        for character_id in icon_service.characters_data.keys():
            local_path = icon_service.get_icon_file_path(character_id)
            if local_path:
                downloaded_count += 1
            else:
                missing_icons.append(character_id)
        
        return {
            "total_characters": total_characters,
            "downloaded_count": downloaded_count,
            "missing_count": len(missing_icons),
            "download_percentage": round((downloaded_count / total_characters) * 100, 2),
            "missing_character_ids": missing_icons[:10],  # Show first 10 missing
            "all_downloaded": downloaded_count == total_characters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI Assistant Endpoints (keep the useful ones)
@app.post("/ai/character-analysis", tags=["AI Assistant"])
async def get_comprehensive_character_analysis(request: Dict[str, Any]):
    """
    Get comprehensive character analysis using AI + damage calculators.
    
    **Powered by Enhanced AI Assistant:**
    - Mathematical damage calculations using actual Genshin formulas
    - Artifact set bonus analysis and recommendations
    - Bond of Life mechanics evaluation
    - Team synergy and reaction optimization
    - Build efficiency scoring and improvement suggestions
    - Investment priority recommendations
    
    This endpoint combines the power of AI reasoning with mathematical precision 
    for the most comprehensive character analysis available.
    """
    try:
        # Validate request
        if "uid" not in request or "character_name" not in request:
            raise HTTPException(status_code=400, detail="uid and character_name are required")
        
        uid = request["uid"]
        character_name = request["character_name"]
        team_composition = request.get("team_composition", [character_name])
        
        # Get character data
        from database import CharacterData
        character_data = await CharacterData.get_character_by_name(uid, character_name)
        if not character_data:
            raise HTTPException(status_code=404, detail="Character not found in your account")
        
        # Get comprehensive analysis using enhanced AI assistant
        analysis_result = await ai_assistant.analyze_character_build_advanced(character_name, character_data, uid)
        
        # Get damage calculation with team context
        damage_result = await ai_assistant.calculate_damage(character_data, team_composition, "Standard")
        
        # Get build recommendations
        build_recommendations = await ai_assistant.get_build_recommendation(character_name, uid, True)
        
        # Combine all analyses
        comprehensive_analysis = {
            "character_name": character_name,
            "uid": uid,
            "team_composition": team_composition,
            "current_build_analysis": analysis_result,
            "damage_calculations": damage_result,
            "build_recommendations": build_recommendations,
            "analysis_summary": {
                "overall_rating": analysis_result.get("current_stats", {}).get("crit_rate", 0) + analysis_result.get("current_stats", {}).get("crit_dmg", 0),
                "primary_strengths": analysis_result.get("build_analysis", {}).get("strengths", []),
                "improvement_areas": analysis_result.get("build_analysis", {}).get("weaknesses", []),
                "damage_potential": damage_result.get("summary", {}).get("max_single_hit", 0),
                "team_synergy": damage_result.get("summary", {}).get("team_synergy_score", 0)
            },
            "ai_insights": "This analysis combines mathematical precision with AI reasoning for optimal character optimization.",
            "calculation_method": "enhanced_ai_with_damage_calculators"
        }
        
        return comprehensive_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive character analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/ai/build-recommendation", response_model=BuildRecommendationResponse, tags=["AI Assistant"])
async def get_build_recommendation(request: BuildRecommendationRequest):
    """
    Get AI-powered build recommendations for a character with comprehensive damage analysis.
    
    **Enhanced with Damage Calculators:**
    - Uses actual Genshin Impact damage formulas
    - Integrates artifact set bonuses and effects
    - Analyzes Bond of Life mechanics for applicable characters
    - Provides team synergy recommendations
    - Calculates optimal stat targets
    - Includes current build analysis if UID provided
    
    This endpoint now provides mathematical accuracy combined with AI insights for the best possible recommendations.
    """
    try:
        result = await ai_assistant.get_build_recommendation(
            request.character_name, 
            request.uid, 
            request.include_current_build
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return BuildRecommendationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/question", response_model=QuestionResponse, tags=["AI Assistant"])
async def ask_question(request: QuestionRequest):
    """
    Ask the AI assistant any Genshin Impact related question with enhanced analysis capabilities.
    
    **Enhanced with Damage Calculators:**
    - Access to comprehensive damage calculation systems
    - Artifact set bonus analysis
    - Bond of Life mechanics understanding
    - Team synergy and reaction analysis
    - Mathematical accuracy for build recommendations
    
    The AI can now provide more accurate and detailed responses about character builds, 
    team compositions, and damage optimization using actual game formulas.
    """
    try:
        result = await ai_assistant.answer_question(
            request.question, 
            request.uid if request.include_context else None
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return QuestionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/reactions", tags=["Team Analysis"])
async def analyze_team_reactions(request: Dict[str, Any]):
    """
    Analyze possible elemental reactions based on team composition.
    
    This endpoint is for **analysis and educational purposes only**. The damage calculation
    endpoints (/damage/character and /damage/team) automatically detect and apply optimal
    reactions based on team composition.
    
    This endpoint provides:
    - All possible reactions with viability scores
    - Recommended reactions for optimal damage
    - Team synergy analysis for reactions
    - Character role analysis for reaction setups
    - Detailed descriptions of each reaction
    
    Perfect for team building and understanding reaction potential.
    """
    try:
        from simple_damage_calculator import damage_calculator
        
        # Validate request
        if "team_composition" not in request:
            raise HTTPException(status_code=400, detail="team_composition is required")
        
        team_composition = request["team_composition"]
        main_dps = request.get("main_dps")
        
        # If no main DPS specified, use the first character
        if not main_dps:
            main_dps = team_composition[0] if team_composition else None
        
        if not main_dps:
            raise HTTPException(status_code=400, detail="At least one character must be specified")
        
        # Validate team composition
        if len(team_composition) < 2:
            raise HTTPException(status_code=400, detail="At least 2 characters needed for reaction analysis")
        
        if len(team_composition) > 4:
            raise HTTPException(status_code=400, detail="Maximum 4 characters allowed")
        
        # Analyze reactions
        reaction_analysis = damage_calculator.analyze_team_reactions(team_composition, main_dps)
        
        # Add additional analysis
        analysis_summary = {
            "team_composition": team_composition,
            "main_dps": main_dps,
            "total_possible_reactions": len(reaction_analysis["possible_reactions"]),
            "recommended_reactions": reaction_analysis["recommended_reactions"],
            "top_reaction": reaction_analysis["possible_reactions"][0] if reaction_analysis["possible_reactions"] else None,
            "team_synergy_score": reaction_analysis["team_synergy"]["synergy_score"],
            "elemental_coverage": reaction_analysis["elemental_coverage"],
            "analysis_notes": []
        }
        
        # Generate analysis notes
        if reaction_analysis["elemental_coverage"]["amplifying_reactions"] > 0:
            analysis_summary["analysis_notes"].append("Team has amplifying reaction potential (Vaporize/Melt) for high damage multipliers")
        
        if reaction_analysis["elemental_coverage"]["transformative_reactions"] > 0:
            analysis_summary["analysis_notes"].append("Team has transformative reaction potential for additional damage and utility")
        
        if "anemo" in reaction_analysis["team_elements"].values():
            analysis_summary["analysis_notes"].append("Anemo character present - can trigger Swirl reactions and provide VV resistance shred")
        
        if reaction_analysis["team_synergy"]["resonance_active"]:
            analysis_summary["analysis_notes"].append("Elemental resonance active for additional team bonuses")
        
        if reaction_analysis["elemental_coverage"]["element_count"] >= 3:
            analysis_summary["analysis_notes"].append("High elemental diversity provides multiple reaction options and flexibility")
        
        return {
            "analysis_summary": analysis_summary,
            "detailed_analysis": reaction_analysis,
            "usage_tips": {
                "optimal_reactions": reaction_analysis["recommended_reactions"][:2],
                "reaction_priority": "Focus on amplifying reactions (Vaporize/Melt) for main DPS damage",
                "team_rotation": "Apply aura element first, then trigger with main DPS for consistent reactions",
                "elemental_mastery": "Increase EM on reaction triggers for higher reaction damage" if reaction_analysis["elemental_coverage"]["transformative_reactions"] > 0 else "EM less important for amplifying reactions, focus on ATK/Crit"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reaction analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reaction analysis failed: {str(e)}")


@app.post("/analyze/artifact-sets", tags=["Character Analysis"])
async def analyze_artifact_sets(request: Dict[str, Any]):
    """
    Analyze artifact sets and their bonuses for a character.
    
    This endpoint provides comprehensive artifact set analysis:
    - Identifies active 2-piece and 4-piece set bonuses
    - Calculates stat bonuses from artifact sets
    - Provides set recommendations for the character
    - Shows conditional effects and their requirements
    - Evaluates set synergy with character abilities
    
    Perfect for optimizing artifact builds and understanding set effects.
    """
    try:
        from artifact_set_calculator import artifact_set_calculator
        from simple_damage_calculator import damage_calculator
        
        # Validate request
        if "artifacts" not in request:
            raise HTTPException(status_code=400, detail="artifacts field is required")
        
        artifacts = request["artifacts"]
        character_name = request.get("character_name", "Unknown")
        
        # Analyze equipped sets
        set_analysis = artifact_set_calculator.analyze_equipped_sets(artifacts)
        
        # Get character element for recommendations
        element = damage_calculator.get_character_element(character_name)
        
        # Get set recommendations
        recommendations = artifact_set_calculator.get_set_recommendations(character_name, element)
        
        # Calculate stat bonuses (simplified)
        base_stats = {
            "atk_percent": 0.0,
            "hp_percent": 0.0,
            "def_percent": 0.0,
            "crit_rate": 5.0,
            "crit_dmg": 50.0,
            "elemental_mastery": 0.0,
            "energy_recharge": 100.0,
            "elemental_dmg_bonus": 0.0,
            "physical_dmg_bonus": 0.0,
            "healing_bonus": 0.0
        }
        
        character_info = {
            "weapon_type": request.get("weapon_type", "sword"),
            "energy_recharge": 100.0,
            "character_name": character_name,
            "element": element
        }
        
        bonus_result = artifact_set_calculator.apply_set_bonuses_to_stats(
            base_stats, set_analysis, character_info
        )
        
        return {
            "character_name": character_name,
            "element": element,
            "set_analysis": {
                "equipped_sets": set_analysis["set_counts"],
                "active_bonuses": set_analysis["active_bonuses"],
                "total_active_sets": set_analysis["total_active_sets"]
            },
            "stat_bonuses": {
                "applied_bonuses": bonus_result["stats"],
                "applied_effects": bonus_result["applied_effects"]
            },
            "recommendations": recommendations,
            "analysis_notes": [
                f"Found {set_analysis['total_active_sets']} active set bonuses",
                f"Applied {len(bonus_result['applied_effects'])} stat effects",
                "Conditional effects assume optimal combat conditions",
                "Set recommendations are based on character element and role"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing artifact sets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing artifact sets: {str(e)}")

@app.post("/analyze/bond-of-life", tags=["Character Analysis"])
async def analyze_bond_of_life(request: Dict[str, Any]):
    """
    Analyze Bond of Life mechanics for a character.
    
    This endpoint provides comprehensive Bond of Life analysis:
    - Checks if character has Bond of Life abilities
    - Calculates stat bonuses from Bond of Life
    - Simulates Bond of Life effects in combat
    - Shows interaction with artifact sets
    - Provides usage recommendations and strategies
    
    Essential for characters like Arlecchino, Gaming, and Xianyun who use Bond of Life.
    """
    try:
        from bond_of_life_system import bond_of_life_system
        
        # Validate request
        if "character_name" not in request:
            raise HTTPException(status_code=400, detail="character_name field is required")
        
        character_name = request["character_name"]
        bond_value = request.get("bond_value", 50.0)  # Default 50% of Max HP
        character_stats = request.get("character_stats", {
            "total_hp": 15000,
            "total_atk": 2000,
            "energy_recharge": 100.0
        })
        
        # Get Bond of Life recommendations
        recommendations = bond_of_life_system.get_bond_of_life_recommendations(character_name)
        
        if not recommendations.get("has_bond_of_life", False):
            return {
                "character_name": character_name,
                "has_bond_of_life": False,
                "message": "This character does not have Bond of Life mechanics",
                "recommendations": recommendations.get("recommendations", [])
            }
        
        # Create Bond of Life state
        bond_state = bond_of_life_system.create_bond_of_life(
            character_name, "analysis", bond_value, character_stats["total_hp"]
        )
        
        # Calculate effects
        equipped_artifacts = request.get("equipped_artifacts", [])
        bond_effects = bond_of_life_system.calculate_bond_of_life_effects(
            character_name, bond_state, character_stats, equipped_artifacts
        )
        
        # Simulate combat
        combat_simulation = bond_of_life_system.simulate_bond_of_life_combat(
            character_name, bond_value, character_stats
        )
        
        return {
            "character_name": character_name,
            "has_bond_of_life": True,
            "bond_state": {
                "current_value": bond_state.current_value,
                "max_value": bond_state.max_value,
                "value_percentage": bond_state.value_percentage,
                "is_active": bond_state.is_active,
                "can_heal": bond_state.can_heal()
            },
            "effects": bond_effects,
            "combat_simulation": combat_simulation,
            "recommendations": recommendations,
            "usage_tips": [
                "Bond of Life blocks ALL healing until cleared",
                "Higher HP builds increase Bond of Life benefits",
                "Some artifact sets provide bonuses with Bond of Life",
                "Plan combat rotations around Bond of Life timing",
                "Use Statue of The Seven to instantly clear if needed"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing Bond of Life: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing Bond of Life: {str(e)}")

@app.get("/info/artifact-sets", tags=["Game Information"])
async def get_artifact_sets_info():
    """
    Get comprehensive information about all artifact sets.
    
    This endpoint provides detailed information about:
    - All available artifact sets and their bonuses
    - 2-piece and 4-piece effects for each set
    - Conditional effects and their requirements
    - Element-specific set recommendations
    - Set synergies and combinations
    
    Perfect reference for artifact farming and build planning.
    """
    try:
        from artifact_set_calculator import artifact_set_calculator
        
        all_sets = {}
        
        for set_name, bonuses in artifact_set_calculator.ARTIFACT_SET_BONUSES.items():
            set_info = {
                "name": set_name.title(),
                "bonuses": []
            }
            
            for bonus in bonuses:
                bonus_info = {
                    "pieces_required": bonus.pieces_required,
                    "bonus_type": bonus.bonus_type,
                    "description": bonus.description,
                    "stat_bonuses": bonus.stat_bonuses,
                    "conditional_effects": bonus.conditional_effects
                }
                set_info["bonuses"].append(bonus_info)
            
            all_sets[set_name] = set_info
        
        # Get element-specific recommendations
        element_recommendations = {
            "pyro": artifact_set_calculator.get_set_recommendations("diluc", "pyro"),
            "hydro": artifact_set_calculator.get_set_recommendations("childe", "hydro"),
            "electro": artifact_set_calculator.get_set_recommendations("raiden", "electro"),
            "cryo": artifact_set_calculator.get_set_recommendations("ganyu", "cryo"),
            "anemo": artifact_set_calculator.get_set_recommendations("venti", "anemo"),
            "geo": artifact_set_calculator.get_set_recommendations("zhongli", "geo"),
            "dendro": artifact_set_calculator.get_set_recommendations("nahida", "dendro")
        }
        
        return {
            "total_sets": len(all_sets),
            "artifact_sets": all_sets,
            "element_recommendations": element_recommendations,
            "usage_notes": [
                "2-piece bonuses are always active when you have 2+ pieces",
                "4-piece bonuses require exactly 4 pieces of the same set",
                "Conditional effects may require specific combat conditions",
                "Some sets work better with certain weapon types",
                "Mix and match 2-piece bonuses for flexible builds"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting artifact sets info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting artifact sets info: {str(e)}")

@app.get("/info/bond-of-life", tags=["Game Information"])
async def get_bond_of_life_info():
    """
    Get comprehensive information about Bond of Life mechanics.
    
    This endpoint provides detailed information about:
    - Characters that can generate Bond of Life
    - How Bond of Life affects healing and combat
    - Artifact sets that interact with Bond of Life
    - Strategies for using Bond of Life effectively
    - Character-specific Bond of Life mechanics
    
    Essential reference for understanding this unique mechanic.
    """
    try:
        from bond_of_life_system import bond_of_life_system
        
        # Get all Bond of Life characters
        characters_info = {}
        for char_name, char_data in bond_of_life_system.BOND_OF_LIFE_CHARACTERS.items():
            recommendations = bond_of_life_system.get_bond_of_life_recommendations(char_name)
            characters_info[char_name] = {
                "character_data": char_data,
                "recommendations": recommendations.get("recommendations", []),
                "artifact_recommendations": recommendations.get("artifact_recommendations", [])
            }
        
        # Get artifact interactions
        artifact_interactions = bond_of_life_system.BOND_OF_LIFE_ARTIFACTS
        
        return {
            "overview": {
                "description": "Bond of Life is a mechanic that prevents healing while providing various benefits",
                "max_value": "200% of Max HP (character-specific limits may apply)",
                "healing_interaction": "Bond of Life absorbs all healing until cleared",
                "clearing_methods": ["Natural decay", "Statue of The Seven", "Character abilities"]
            },
            "characters": characters_info,
            "artifact_interactions": artifact_interactions,
            "general_mechanics": [
                "Bond of Life prevents ALL healing while active",
                "Value is expressed as percentage of Max HP",
                "Some characters gain bonuses based on Bond of Life value",
                "Certain artifact sets provide additional effects",
                "Can be strategically used for damage optimization"
            ],
            "strategic_tips": [
                "Plan combat rotations around Bond of Life timing",
                "Higher HP builds increase potential benefits",
                "Consider team composition for healing alternatives",
                "Use Bond of Life for damage phases, clear for safety",
                "Some characters convert Bond of Life to offensive stats"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting Bond of Life info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting Bond of Life info: {str(e)}")

@app.post("/ai/team-recommendation", tags=["AI Assistant"])
async def get_team_recommendation_endpoint(request: Dict[str, Any]):
    """
    Get specialized team recommendations for a specific character.
    
    **Enhanced Team Building Assistant:**
    - Analyzes player's available character roster
    - Provides multiple team composition options
    - Explains character roles and synergies
    - Includes rotation guides and investment priorities
    - Tailored for different content types (Abyss, domains, bosses)
    
    Perfect for questions like "give me a good team for Chasca" or "best team comp for Spiral Abyss".
    """
    try:
        # Validate request
        if "character_name" not in request:
            raise HTTPException(status_code=400, detail="character_name is required")
        
        character_name = request["character_name"]
        uid = request.get("uid")
        content_type = request.get("content_type", "general")
        
        # Get team recommendations using enhanced AI assistant
        result = await ai_assistant.get_team_recommendation(character_name, uid, content_type)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in team recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Team recommendation failed: {str(e)}")


@app.post("/ai/team-synergy", tags=["AI Assistant"])
async def analyze_team_synergy_endpoint(request: Dict[str, Any]):
    """
    Analyze the synergy and effectiveness of a team composition.
    
    **Comprehensive Team Analysis:**
    - Evaluates elemental reactions and resonance
    - Assesses role distribution and energy management
    - Provides rotation guides and optimization tips
    - Scores team effectiveness across multiple criteria
    - Identifies strengths, weaknesses, and improvement areas
    
    Perfect for analyzing existing teams or comparing different compositions.
    """
    try:
        # Validate request
        if "team_composition" not in request:
            raise HTTPException(status_code=400, detail="team_composition is required")
        
        team_composition = request["team_composition"]
        uid = request.get("uid")
        
        if not isinstance(team_composition, list) or len(team_composition) < 2 or len(team_composition) > 4:
            raise HTTPException(status_code=400, detail="team_composition must be a list of 2-4 character names")
        
        # Analyze team synergy using enhanced AI assistant
        result = await ai_assistant.analyze_team_synergy(team_composition, uid)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in team synergy analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Team synergy analysis failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    ) 