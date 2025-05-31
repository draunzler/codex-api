#!/usr/bin/env python3
"""
Character Icon Service for Genshin Impact API
Handles saving and serving character icons using data from .enka_py/assets/characters.json
"""

import json
import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

class CharacterIconService:
    def __init__(self, assets_path: str = ".enka_py/assets", icons_dir: str = "character_icons"):
        self.assets_path = Path(assets_path)
        self.characters_file = self.assets_path / "characters.json"
        self.icons_dir = Path(icons_dir)
        self.base_icon_url = "https://enka.network/ui/"
        self.characters_data = {}
        
        # Create icons directory if it doesn't exist
        self.icons_dir.mkdir(exist_ok=True)
        
        # Load characters data
        self._load_characters_data()
    
    def _load_characters_data(self):
        """Load character data from characters.json file."""
        try:
            if self.characters_file.exists():
                with open(self.characters_file, 'r', encoding='utf-8') as f:
                    self.characters_data = json.load(f)
                print(f"Loaded {len(self.characters_data)} characters from {self.characters_file}")
            else:
                print(f"Characters file not found: {self.characters_file}")
        except Exception as e:
            print(f"Error loading characters data: {str(e)}")
    
    def get_character_icon_name(self, character_id: str) -> Optional[str]:
        """Get the icon name for a character by ID."""
        character_data = self.characters_data.get(character_id)
        if character_data:
            return character_data.get("SideIconName")
        return None
    
    def get_character_info(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get complete character information by ID."""
        character_data = self.characters_data.get(character_id)
        if character_data:
            return {
                "id": character_id,
                "icon_name": character_data.get("SideIconName"),
                "element": character_data.get("Element"),
                "weapon_type": character_data.get("WeaponType"),
                "quality": character_data.get("QualityType"),
                "namecard_icon": character_data.get("NamecardIcon"),
                "costumes": character_data.get("Costumes", {})
            }
        return None
    
    def get_icon_url(self, icon_name: str) -> str:
        """Convert icon name to full URL."""
        if not icon_name:
            return ""
        return f"{self.base_icon_url}{icon_name}.png"
    
    def get_local_icon_path(self, icon_name: str) -> Path:
        """Get local file path for an icon."""
        return self.icons_dir / f"{icon_name}.png"
    
    async def download_icon(self, icon_name: str, force_redownload: bool = False) -> Optional[str]:
        """Download a character icon and save it locally."""
        if not icon_name:
            return None
        
        local_path = self.get_local_icon_path(icon_name)
        
        # Check if file already exists and we're not forcing redownload
        if local_path.exists() and not force_redownload:
            print(f"Icon already exists: {local_path}")
            return str(local_path)
        
        icon_url = self.get_icon_url(icon_name)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(icon_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Save the icon
                        with open(local_path, 'wb') as f:
                            f.write(content)
                        
                        print(f"Downloaded icon: {icon_name} -> {local_path}")
                        return str(local_path)
                    else:
                        print(f"Failed to download icon {icon_name}: HTTP {response.status}")
                        return None
        
        except Exception as e:
            print(f"Error downloading icon {icon_name}: {str(e)}")
            return None
    
    async def download_character_icon(self, character_id: str, force_redownload: bool = False) -> Optional[str]:
        """Download icon for a specific character by ID."""
        icon_name = self.get_character_icon_name(character_id)
        if icon_name:
            return await self.download_icon(icon_name, force_redownload)
        else:
            print(f"No icon found for character ID: {character_id}")
            return None
    
    async def download_all_character_icons(self, force_redownload: bool = False) -> Dict[str, str]:
        """Download icons for all characters."""
        results = {}
        
        print(f"Starting download of {len(self.characters_data)} character icons...")
        
        # Create semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent downloads
        
        async def download_with_semaphore(char_id: str):
            async with semaphore:
                return await self.download_character_icon(char_id, force_redownload)
        
        # Create tasks for all downloads
        tasks = []
        for character_id in self.characters_data.keys():
            task = download_with_semaphore(character_id)
            tasks.append((character_id, task))
        
        # Execute all downloads
        for character_id, task in tasks:
            try:
                result = await task
                if result:
                    results[character_id] = result
                    print(f"✅ {character_id}: {result}")
                else:
                    print(f"❌ {character_id}: Failed")
            except Exception as e:
                print(f"❌ {character_id}: Error - {str(e)}")
        
        print(f"Download complete! {len(results)}/{len(self.characters_data)} icons downloaded successfully.")
        return results
    
    def get_character_by_name(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Find character by name (requires text_map.json for name resolution)."""
        # This would require loading text_map.json to resolve name hashes
        # For now, return None - can be implemented if needed
        return None
    
    def list_available_characters(self) -> Dict[str, Dict[str, Any]]:
        """List all available characters with their basic info."""
        result = {}
        for char_id, char_data in self.characters_data.items():
            result[char_id] = {
                "icon_name": char_data.get("SideIconName"),
                "element": char_data.get("Element"),
                "weapon_type": char_data.get("WeaponType"),
                "quality": char_data.get("QualityType")
            }
        return result
    
    def get_icon_file_path(self, character_id: str) -> Optional[str]:
        """Get the local file path for a character's icon if it exists."""
        icon_name = self.get_character_icon_name(character_id)
        if icon_name:
            local_path = self.get_local_icon_path(icon_name)
            if local_path.exists():
                return str(local_path)
        return None

# Example usage functions
async def download_specific_character_icon(character_id: str):
    """Download icon for a specific character."""
    service = CharacterIconService()
    result = await service.download_character_icon(character_id)
    if result:
        print(f"Icon saved to: {result}")
        return result
    else:
        print(f"Failed to download icon for character {character_id}")
        return None

async def download_all_icons():
    """Download all character icons."""
    service = CharacterIconService()
    results = await service.download_all_character_icons()
    return results

def get_character_icon_info(character_id: str):
    """Get character icon information."""
    service = CharacterIconService()
    return service.get_character_info(character_id)

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        service = CharacterIconService()
        
        # Get first available character for demonstration
        characters = service.list_available_characters()
        if not characters:
            print("No characters found in characters.json")
            return
        
        # Use first character as example
        first_char_id = list(characters.keys())[0]
        first_char_info = characters[first_char_id]
        
        print(f"=== Downloading Icon for Character {first_char_id} ===")
        result = await service.download_character_icon(first_char_id)
        print(f"Character {first_char_id} icon: {result}")
        
        # Example: Get character info
        print(f"\n=== Character Info for {first_char_id} ===")
        char_info = service.get_character_info(first_char_id)
        print(f"Character info: {char_info}")
        
        # Example: List first 5 characters
        print("\n=== Available Characters (first 5) ===")
        for i, (char_id, info) in enumerate(characters.items()):
            if i >= 5:
                break
            print(f"{char_id}: {info['icon_name']} ({info['element']})")
    
    asyncio.run(main()) 