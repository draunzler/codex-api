from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import settings


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None


db = MongoDB()


async def connect_to_mongo():
    """Create database connection."""
    # Replace password placeholder with actual password
    mongodb_url = settings.mongodb_url.replace("<db_password>", settings.mongodb_password)
    
    db.client = AsyncIOMotorClient(mongodb_url)
    db.database = db.client[settings.database_name]
    
    # Test the connection
    try:
        await db.client.admin.command('ping')
        print(f"✅ Connected to MongoDB Atlas: {settings.database_name}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        raise
    
    # Create indexes
    await create_indexes()


async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")


async def create_indexes():
    """Create database indexes for better performance."""
    # User profiles index
    await db.database.users.create_index([("uid", ASCENDING)], unique=True)
    await db.database.users.create_index([("created_at", ASCENDING)])
    
    # Character data index within user documents
    await db.database.users.create_index([("characters.avatarId", ASCENDING)])
    await db.database.users.create_index([("characters.updated_at", ASCENDING)])
    
    # Character icons index
    await db.database.character_icons.create_index([("character_id", ASCENDING)], unique=True)
    await db.database.character_icons.create_index([("element", ASCENDING)])
    await db.database.character_icons.create_index([("quality_type", ASCENDING)])
    
    # Cache index
    await db.database.cache.create_index([("key", ASCENDING)], unique=True)
    await db.database.cache.create_index([("expires_at", ASCENDING)])


# Database Models
class UserProfile:
    """User profile model."""
    
    @staticmethod
    async def create(uid: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile."""
        user_data = {
            "uid": uid,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_fetch": datetime.utcnow(),
            "profile_data": data,
            "characters": [],  # Store characters in user document
            "settings": {
                "notifications_enabled": True,
                "auto_update": True
            }
        }
        
        await db.database.users.insert_one(user_data)
        return user_data
    
    @staticmethod
    async def get(uid: int) -> Optional[Dict[str, Any]]:
        """Get user profile by UID."""
        return await db.database.users.find_one({"uid": uid})
    
    @staticmethod
    async def update(uid: int, data: Dict[str, Any]) -> bool:
        """Update user profile data."""
        result = await db.database.users.update_one(
            {"uid": uid},
            {
                "$set": {
                    "profile_data": data,
                    "updated_at": datetime.utcnow(),
                    "last_fetch": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_characters(uid: int, characters: List[Dict[str, Any]]) -> bool:
        """Update user's character collection."""
        result = await db.database.users.update_one(
            {"uid": uid},
            {
                "$set": {
                    "characters": characters,
                    "updated_at": datetime.utcnow(),
                    "last_fetch": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    async def get_all_for_update() -> List[Dict[str, Any]]:
        """Get all users that need profile updates."""
        # Get users where auto_update is enabled
        cursor = db.database.users.find({"settings.auto_update": True})
        return await cursor.to_list(length=None)


class CharacterData:
    """Character data model - now stored within user documents."""
    
    @staticmethod
    async def save_character(uid: int, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update a single character in user's collection."""
        avatar_id = character_data.get("avatarId")
        if not avatar_id:
            raise ValueError("Character data must include avatarId")
        
        # Add timestamp
        character_data["updated_at"] = datetime.utcnow()
        
        # Update or insert character in user's characters array
        result = await db.database.users.update_one(
            {"uid": uid, "characters.avatarId": avatar_id},
            {"$set": {"characters.$": character_data}},
        )
        
        # If character doesn't exist, add it to the array
        if result.matched_count == 0:
            await db.database.users.update_one(
                {"uid": uid},
                {"$push": {"characters": character_data}},
                upsert=True
            )
        
        return character_data
    
    @staticmethod
    async def save_all_characters(uid: int, characters: List[Dict[str, Any]], merge_characters: bool = True) -> bool:
        """
        Save all characters for a user.
        
        Args:
            uid: User ID
            characters: List of character data
            merge_characters: Whether to merge with existing characters (True) or replace all (False)
        """
        if merge_characters:
            return await CharacterData.save_characters_merge(uid, characters)
        else:
            return await CharacterData.save_all_characters_replace(uid, characters)
    
    @staticmethod
    async def save_characters_merge(uid: int, new_characters: List[Dict[str, Any]]) -> bool:
        """
        Merge new characters with existing ones.
        - Updates existing characters if they match by avatarId
        - Adds new characters that don't exist
        - Preserves existing characters that aren't in the new list
        """
        # Add timestamps to all new characters
        for char in new_characters:
            char["updated_at"] = datetime.utcnow()
        
        # Ensure user exists - use upsert to avoid duplicate key errors
        user = await UserProfile.get(uid)
        if not user:
            # Create user with basic profile data using upsert
            basic_profile = {
                "uid": uid, 
                "nickname": "Unknown",
                "level": 1,
                "signature": "",
                "worldLevel": 0,
                "nameCardId": 0,
                "finishAchievementNum": 0,
                "towerFloorIndex": 0,
                "towerLevelIndex": 0,
                "showAvatarInfoList": [],
                "profilePicture": {},
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            # Use upsert to avoid duplicate key errors
            await db.database.users.update_one(
                {"uid": uid},
                {
                    "$setOnInsert": {
                        "uid": uid,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "last_fetch": datetime.utcnow(),
                        "profile_data": basic_profile,
                        "characters": [],
                        "settings": {
                            "notifications_enabled": True,
                            "auto_update": True
                        }
                    }
                },
                upsert=True
            )
        
        # Get existing characters to merge with
        existing_characters = await CharacterData.get_all_user_characters(uid)
        existing_avatar_ids = {char.get("avatarId") for char in existing_characters if char.get("avatarId")}
        
        # Create a map of new characters by avatarId for easy lookup
        new_chars_by_id = {char.get("avatarId"): char for char in new_characters if char.get("avatarId")}
        
        # Start with existing characters
        merged_characters = []
        
        # Update existing characters if they're in the new list, otherwise keep them as-is
        for existing_char in existing_characters:
            avatar_id = existing_char.get("avatarId")
            if avatar_id in new_chars_by_id:
                # Update with new data
                merged_characters.append(new_chars_by_id[avatar_id])
                print(f"Updated existing character: {existing_char.get('name', 'Unknown')} (ID: {avatar_id})")
            else:
                # Keep existing character
                merged_characters.append(existing_char)
                print(f"Preserved existing character: {existing_char.get('name', 'Unknown')} (ID: {avatar_id})")
        
        # Add completely new characters that don't exist yet
        for new_char in new_characters:
            avatar_id = new_char.get("avatarId")
            if avatar_id not in existing_avatar_ids:
                merged_characters.append(new_char)
                print(f"Added new character: {new_char.get('name', 'Unknown')} (ID: {avatar_id})")
        
        # Update the characters array with merged data
        result = await db.database.users.update_one(
            {"uid": uid},
            {
                "$set": {
                    "characters": merged_characters,
                    "updated_at": datetime.utcnow(),
                    "last_fetch": datetime.utcnow()
                }
            }
        )
        
        print(f"Character merge completed for UID {uid}: {len(existing_characters)} existing + {len(new_characters)} new = {len(merged_characters)} total")
        return result.modified_count > 0 or result.upserted_id is not None
    
    @staticmethod
    async def save_all_characters_replace(uid: int, characters: List[Dict[str, Any]]) -> bool:
        """Save all characters for a user (replaces existing characters - legacy method)."""
        # Add timestamps to all characters
        for char in characters:
            char["updated_at"] = datetime.utcnow()
        
        # Ensure user exists - use upsert to avoid duplicate key errors
        user = await UserProfile.get(uid)
        if not user:
            # Create user with basic profile data using upsert
            basic_profile = {
                "uid": uid, 
                "nickname": "Unknown",
                "level": 1,
                "signature": "",
                "worldLevel": 0,
                "nameCardId": 0,
                "finishAchievementNum": 0,
                "towerFloorIndex": 0,
                "towerLevelIndex": 0,
                "showAvatarInfoList": [],
                "profilePicture": {},
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            # Use upsert to avoid duplicate key errors
            await db.database.users.update_one(
                {"uid": uid},
                {
                    "$setOnInsert": {
                        "uid": uid,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "last_fetch": datetime.utcnow(),
                        "profile_data": basic_profile,
                        "characters": [],
                        "settings": {
                            "notifications_enabled": True,
                            "auto_update": True
                        }
                    }
                },
                upsert=True
            )

        # Update characters array (complete replacement)
        result = await db.database.users.update_one(
            {"uid": uid},
            {
                "$set": {
                    "characters": characters,
                    "updated_at": datetime.utcnow(),
                    "last_fetch": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    @staticmethod
    async def get_character(uid: int, avatar_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific character by avatar ID."""
        user = await db.database.users.find_one(
            {"uid": uid, "characters.avatarId": avatar_id},
            {"characters.$": 1}
        )
        
        if user and "characters" in user and user["characters"]:
            return user["characters"][0]
        return None
    
    @staticmethod
    async def get_character_by_name(uid: int, character_name: str) -> Optional[Dict[str, Any]]:
        """Get a character by name (requires character name mapping)."""
        user = await db.database.users.find_one({"uid": uid})
        if not user or "characters" not in user:
            return None
        
        # Search through characters for matching name
        for char in user["characters"]:
            # This would need character name mapping from avatar ID
            # For now, we'll use a simple approach
            if "name" in char and char["name"].lower() == character_name.lower():
                return char
        
        return None
    
    @staticmethod
    async def get_all_user_characters(uid: int) -> List[Dict[str, Any]]:
        """Get all characters for a user."""
        user = await db.database.users.find_one({"uid": uid})
        if user and "characters" in user:
            return user["characters"]
        return []


class Cache:
    """Cache model for storing temporary data."""
    
    @staticmethod
    async def set(key: str, value: Any, ttl: int = 3600) -> None:
        """Set cache value with TTL in seconds."""
        expires_at = datetime.utcnow().timestamp() + ttl
        await db.database.cache.update_one(
            {"key": key},
            {
                "$set": {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Get cache value if not expired."""
        doc = await db.database.cache.find_one({"key": key})
        if doc and doc["expires_at"] > datetime.utcnow().timestamp():
            return doc["value"]
        return None
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete cache entry."""
        result = await db.database.cache.delete_one({"key": key})
        return result.deleted_count > 0
    
    @staticmethod
    async def cleanup_expired() -> int:
        """Clean up expired cache entries."""
        result = await db.database.cache.delete_many(
            {"expires_at": {"$lt": datetime.utcnow().timestamp()}}
        )
        return result.deleted_count


class CharacterIcon:
    """Character icon model for storing character metadata and icon information."""
    
    @staticmethod
    async def save_character_icon(character_id: str, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update character icon data."""
        icon_data = {
            "character_id": character_id,
            "side_icon_name": character_data.get("SideIconName"),
            "namecard_icon": character_data.get("NamecardIcon"),
            "element": character_data.get("Element"),
            "quality_type": character_data.get("QualityType"),
            "weapon_type": character_data.get("WeaponType"),
            "name_text_map_hash": character_data.get("NameTextMapHash"),
            "costumes": character_data.get("Costumes", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.database.character_icons.update_one(
            {"character_id": character_id},
            {"$set": icon_data},
            upsert=True
        )
        
        return icon_data
    
    @staticmethod
    async def get_character_icon(character_id: str) -> Optional[Dict[str, Any]]:
        """Get character icon data by character ID."""
        return await db.database.character_icons.find_one({"character_id": character_id})
    
    @staticmethod
    async def get_all_character_icons() -> List[Dict[str, Any]]:
        """Get all character icon data."""
        cursor = db.database.character_icons.find({})
        return await cursor.to_list(length=None)
    
    @staticmethod
    async def get_character_count() -> int:
        """Get total count of characters in database."""
        return await db.database.character_icons.count_documents({}) 