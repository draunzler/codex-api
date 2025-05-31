#!/usr/bin/env python3
"""
Debug script to help identify and fix the duplicate key error issue.
"""

import asyncio
from genshin_client import genshin_client
from database import UserProfile, CharacterData

async def debug_user_data(uid: int):
    """Debug user data operations."""
    
    print(f"=== Debugging UID: {uid} ===")
    
    # Check if user already exists in database
    try:
        existing_user = await UserProfile.get(uid)
        if existing_user:
            print(f"✓ User {uid} already exists in database")
            print(f"  - Nickname: {existing_user.get('nickname', 'Unknown')}")
            print(f"  - Level: {existing_user.get('level', 'Unknown')}")
            print(f"  - Last updated: {existing_user.get('updated_at', 'Unknown')}")
        else:
            print(f"✗ User {uid} does not exist in database")
    except Exception as e:
        print(f"✗ Error checking existing user: {str(e)}")
    
    # Check character data
    try:
        characters = await CharacterData.get_all_user_characters(uid)
        if characters:
            print(f"✓ Found {len(characters)} characters for user {uid}")
        else:
            print(f"✗ No characters found for user {uid}")
    except Exception as e:
        print(f"✗ Error checking character data: {str(e)}")
    
    print("\n=== Attempting to fetch fresh data ===")
    
    # Try to fetch fresh data
    async with genshin_client:
        result = await genshin_client.fetch_user_data(uid)
        
        if "error" in result:
            print(f"✗ Error fetching data: {result['error']}")
        else:
            print(f"✓ Successfully fetched data")
            print(f"  - Characters: {result.get('character_count', 0)}")
            print(f"  - Player info: {result.get('player_info', {}).get('nickname', 'Unknown')}")

async def test_upsert_directly(uid: int):
    """Test the upsert functionality directly."""
    
    print(f"\n=== Testing upsert for UID: {uid} ===")
    
    # Create test profile data
    test_profile = {
        "uid": uid,
        "nickname": "Test User",
        "level": 60,
        "signature": "Test signature",
        "worldLevel": 8,
        "nameCardId": 210001,
        "finishAchievementNum": 500,
        "towerFloorIndex": 12,
        "towerLevelIndex": 3,
        "showAvatarInfoList": [],
        "profilePicture": {},
        "fetched_at": "2025-01-27T12:00:00.000Z"
    }
    
    async with genshin_client:
        result = await genshin_client._upsert_user_profile(uid, test_profile)
        if result:
            print(f"✓ Upsert successful for UID: {uid}")
        else:
            print(f"✗ Upsert failed for UID: {uid}")

async def cleanup_user(uid: int):
    """Clean up user data for testing."""
    
    print(f"\n=== Cleaning up UID: {uid} ===")
    
    try:
        # Note: You'll need to implement delete methods in your database classes
        # This is just a placeholder
        print(f"Would delete user {uid} and all associated data")
        print("(Delete methods not implemented - manual cleanup required)")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

async def main():
    """Main debug function."""
    
    # Test UID that's causing issues
    uid = 897297195
    
    # Debug the current state
    await debug_user_data(uid)
    
    # Test upsert directly
    await test_upsert_directly(uid)
    
    # Uncomment to clean up for testing
    # await cleanup_user(uid)

if __name__ == "__main__":
    asyncio.run(main()) 