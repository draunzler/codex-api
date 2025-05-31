#!/usr/bin/env python3
"""
Script to save character icons from .enka_py/assets/characters.json to the database.
This will process all 112+ characters and store their icon metadata.
"""

import asyncio
import json
import os
from datetime import datetime
from database import connect_to_mongo, close_mongo_connection, CharacterIcon


async def load_characters_data():
    """Load characters data from the JSON file."""
    characters_file = ".enka_py/assets/characters.json"
    
    if not os.path.exists(characters_file):
        raise FileNotFoundError(f"Characters file not found: {characters_file}")
    
    with open(characters_file, 'r', encoding='utf-8') as f:
        return json.load(f)


async def save_character_icons():
    """Process and save all character icons to the database."""
    print("🔄 Loading character data from .enka_py/assets/characters.json...")
    
    try:
        # Load characters data
        characters_data = await load_characters_data()
        total_characters = len(characters_data)
        
        print(f"📊 Found {total_characters} characters to process")
        
        # Connect to database
        print("🔗 Connecting to MongoDB...")
        await connect_to_mongo()
        
        # Process each character
        saved_count = 0
        skipped_count = 0
        
        for character_id, character_data in characters_data.items():
            try:
                # Save character icon data
                await CharacterIcon.save_character_icon(character_id, character_data)
                saved_count += 1
                
                # Print progress every 10 characters
                if saved_count % 10 == 0:
                    print(f"✅ Processed {saved_count}/{total_characters} characters...")
                
            except Exception as e:
                print(f"❌ Error processing character {character_id}: {str(e)}")
                skipped_count += 1
                continue
        
        # Final summary
        print(f"\n🎉 Character icon processing complete!")
        print(f"✅ Successfully saved: {saved_count} characters")
        print(f"❌ Skipped due to errors: {skipped_count} characters")
        print(f"📊 Total processed: {saved_count + skipped_count}/{total_characters}")
        
        # Verify database count
        db_count = await CharacterIcon.get_character_count()
        print(f"🗄️  Characters in database: {db_count}")
        
        # Show some sample data
        print(f"\n📋 Sample character data:")
        sample_characters = await CharacterIcon.get_all_character_icons()
        for i, char in enumerate(sample_characters[:5]):  # Show first 5
            element = char.get('element', 'Unknown')
            quality = char.get('quality_type', 'Unknown')
            weapon = char.get('weapon_type', 'Unknown')
            print(f"  {i+1}. ID: {char['character_id']} | Element: {element} | Quality: {quality} | Weapon: {weapon}")
        
        if len(sample_characters) > 5:
            print(f"  ... and {len(sample_characters) - 5} more characters")
        
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        return False
    
    finally:
        # Close database connection
        await close_mongo_connection()
        print("🔌 Database connection closed")
    
    return True


async def main():
    """Main function to run the character icon saving process."""
    print("🚀 Starting character icon import process...")
    print("=" * 60)
    
    success = await save_character_icons()
    
    print("=" * 60)
    if success:
        print("✅ Character icon import completed successfully!")
    else:
        print("❌ Character icon import failed!")
    
    return success


if __name__ == "__main__":
    # Run the script
    result = asyncio.run(main())
    exit(0 if result else 1) 