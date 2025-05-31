#!/usr/bin/env python3
"""
Exploration Client for Genshin Impact using genshin.py library.
Fetches exploration data including world progress, exploration percentages, and more.
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

try:
    import genshin
except ImportError:
    print("genshin.py library not found. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "genshin"])
    import genshin

class ExplorationClient:
    """
    Client for fetching Genshin Impact exploration data using genshin.py library.
    
    Features:
    - World exploration progress
    - Region exploration percentages
    - Reputation levels
    - Offering levels
    - Statue of Seven levels
    - Teapot (Serenitea Pot) data
    """
    
    def __init__(self, cookies: Optional[Dict[str, Any]] = None):
        """
        Initialize the exploration client.
        
        Args:
            cookies: HoYoLAB cookies containing ltuid and ltoken
        """
        self.cookies = cookies or {}
        self.client = None
        
    def set_cookies(self, ltuid: int, ltoken: str, cookie_token: Optional[str] = None):
        """Set authentication cookies for HoYoLAB API."""
        self.cookies = {
            "ltuid": ltuid,
            "ltoken": ltoken
        }
        if cookie_token:
            self.cookies["cookie_token"] = cookie_token
            
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.cookies:
            raise ValueError("No cookies provided. Use set_cookies() or provide cookies in constructor.")
        
        self.client = genshin.Client(self.cookies)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.close()
    
    async def get_exploration_data(self, uid: int) -> Dict[str, Any]:
        """
        Get comprehensive exploration data for a user.
        
        Args:
            uid: Genshin Impact UID
            
        Returns:
            Dictionary containing exploration data
        """
        try:
            if not self.client:
                raise ValueError("Client not initialized. Use async context manager.")
            
            # Get user stats which includes exploration data
            user_data = await self.client.get_genshin_user(uid)
            
            # Process exploration data
            exploration_data = {
                "uid": uid,
                "fetched_at": datetime.utcnow().isoformat(),
                "player_info": {
                    "nickname": user_data.info.nickname,
                    "level": user_data.info.level,
                    "world_level": user_data.info.world_level,
                    "achievement_count": user_data.stats.achievements,
                    "active_days": user_data.stats.days_active,
                    "characters": user_data.stats.characters,
                    "spiral_abyss": user_data.stats.spiral_abyss,
                    "avatar_icon": getattr(user_data.info, 'icon', None)
                },
                "exploration": {
                    "total_chests_opened": user_data.stats.chests,
                    "total_waypoints_unlocked": user_data.stats.waypoints,
                    "total_domains_unlocked": user_data.stats.domains,
                    "anemoculi": user_data.stats.anemoculi,
                    "geoculi": user_data.stats.geoculi,
                    "electroculi": user_data.stats.electroculi,
                    "dendroculi": getattr(user_data.stats, 'dendroculi', 0),
                    "hydroculi": getattr(user_data.stats, 'hydroculi', 0),
                    "pyroculi": getattr(user_data.stats, 'pyroculi', 0),
                },
                "world_explorations": [],
                "teapot": None
            }
            
            # Process world explorations (regions)
            if hasattr(user_data, 'explorations') and user_data.explorations:
                for exploration in user_data.explorations:
                    region_data = {
                        "id": exploration.id,
                        "name": exploration.name,
                        "type": exploration.type,
                        "level": exploration.level,
                        "exploration_percentage": exploration.explored,
                        "icon": exploration.icon,
                        "inner_icon": getattr(exploration, 'inner_icon', None),
                        "background_image": getattr(exploration, 'background_image', None),
                        "cover": getattr(exploration, 'cover', None),
                        "map_url": getattr(exploration, 'map_url', None),
                        "offerings": []
                    }
                    
                    # Add offering data if available
                    if hasattr(exploration, 'offerings') and exploration.offerings:
                        for offering in exploration.offerings:
                            offering_data = {
                                "name": offering.name,
                                "level": offering.level,
                                "icon": offering.icon
                            }
                            region_data["offerings"].append(offering_data)
                    
                    exploration_data["world_explorations"].append(region_data)
            
            # Get teapot data if available
            try:
                teapot_data = await self.client.get_genshin_teapot(uid)
                if teapot_data:
                    exploration_data["teapot"] = {
                        "level": teapot_data.level,
                        "comfort": teapot_data.comfort,
                        "items": teapot_data.items,
                        "comfort_name": teapot_data.comfort_name,
                        "comfort_icon": getattr(teapot_data, 'comfort_icon', None)
                    }
            except Exception as e:
                print(f"Could not fetch teapot data: {str(e)}")
                exploration_data["teapot"] = None
            
            return exploration_data
            
        except genshin.DataNotPublic:
            return {
                "error": "User data is not public. The user needs to make their profile public on HoYoLAB.",
                "uid": uid
            }
        except genshin.AccountNotFound:
            return {
                "error": "Account not found. Please check the UID.",
                "uid": uid
            }
        except Exception as e:
            return {
                "error": f"Failed to fetch exploration data: {str(e)}",
                "uid": uid
            }
    
    async def get_detailed_exploration(self, uid: int) -> Dict[str, Any]:
        """
        Get detailed exploration data including notes and additional info.
        
        Args:
            uid: Genshin Impact UID
            
        Returns:
            Dictionary containing detailed exploration data
        """
        try:
            # Get basic exploration data
            exploration_data = await self.get_exploration_data(uid)
            
            if "error" in exploration_data:
                return exploration_data
            
            # Try to get real-time notes (resin, expeditions, etc.)
            try:
                notes = await self.client.get_genshin_notes(uid)
                exploration_data["real_time_notes"] = {
                    "current_resin": notes.current_resin,
                    "max_resin": notes.max_resin,
                    "resin_recovery_time": notes.resin_recovery_time.isoformat() if notes.resin_recovery_time else None,
                    "completed_commissions": notes.completed_commissions,
                    "max_commissions": notes.max_commissions,
                    "claimed_commission_reward": notes.claimed_commission_reward,
                    "remaining_resin_discounts": notes.remaining_resin_discounts,
                    "max_resin_discounts": notes.max_resin_discounts,
                    "current_expedition_num": notes.current_expedition_num,
                    "max_expeditions": notes.max_expeditions,
                    "expeditions": [
                        {
                            "character_icon": exp.character.icon,
                            "character_name": exp.character.name,
                            "status": exp.status,
                            "remaining_time": exp.remaining_time.isoformat() if exp.remaining_time else None
                        }
                        for exp in notes.expeditions
                    ],
                    "current_realm_currency": getattr(notes, 'current_realm_currency', 0),
                    "max_realm_currency": getattr(notes, 'max_realm_currency', 0),
                    "realm_currency_recovery_time": getattr(notes, 'realm_currency_recovery_time', None)
                }
            except Exception as e:
                print(f"Could not fetch real-time notes: {str(e)}")
                exploration_data["real_time_notes"] = None
            
            return exploration_data
            
        except Exception as e:
            return {
                "error": f"Failed to fetch detailed exploration data: {str(e)}",
                "uid": uid
            }
    
    async def get_exploration_summary(self, uid: int) -> Dict[str, Any]:
        """
        Get a summary of exploration progress.
        
        Args:
            uid: Genshin Impact UID
            
        Returns:
            Dictionary containing exploration summary
        """
        try:
            exploration_data = await self.get_exploration_data(uid)
            
            if "error" in exploration_data:
                return exploration_data
            
            # Calculate summary statistics
            total_regions = len(exploration_data["world_explorations"])
            fully_explored_regions = sum(1 for region in exploration_data["world_explorations"] 
                                       if region["exploration_percentage"] >= 100)
            
            average_exploration = (
                sum(region["exploration_percentage"] for region in exploration_data["world_explorations"]) 
                / total_regions if total_regions > 0 else 0
            )
            
            total_oculi = (
                exploration_data["exploration"]["anemoculi"] +
                exploration_data["exploration"]["geoculi"] +
                exploration_data["exploration"]["electroculi"] +
                exploration_data["exploration"]["dendroculi"] +
                exploration_data["exploration"]["hydroculi"] +
                exploration_data["exploration"]["pyroculi"]
            )
            
            summary = {
                "uid": uid,
                "player_nickname": exploration_data["player_info"]["nickname"],
                "adventure_rank": exploration_data["player_info"]["level"],
                "world_level": exploration_data["player_info"]["world_level"],
                "summary": {
                    "total_regions": total_regions,
                    "fully_explored_regions": fully_explored_regions,
                    "average_exploration_percentage": round(average_exploration, 2),
                    "total_chests_opened": exploration_data["exploration"]["total_chests_opened"],
                    "total_waypoints": exploration_data["exploration"]["total_waypoints_unlocked"],
                    "total_domains": exploration_data["exploration"]["total_domains_unlocked"],
                    "total_oculi_collected": total_oculi,
                    "achievements": exploration_data["player_info"]["achievement_count"],
                    "active_days": exploration_data["player_info"]["active_days"]
                },
                "regions": [
                    {
                        "name": region["name"],
                        "exploration_percentage": region["exploration_percentage"],
                        "level": region["level"]
                    }
                    for region in exploration_data["world_explorations"]
                ],
                "fetched_at": exploration_data["fetched_at"]
            }
            
            return summary
            
        except Exception as e:
            return {
                "error": f"Failed to generate exploration summary: {str(e)}",
                "uid": uid
            }

# Convenience functions for easy usage
async def get_user_exploration(uid: int, ltuid: int, ltoken: str, cookie_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get exploration data for a user.
    
    Args:
        uid: Genshin Impact UID
        ltuid: HoYoLAB user ID
        ltoken: HoYoLAB login token
        cookie_token: Optional cookie token for additional features
        
    Returns:
        Dictionary containing exploration data
    """
    async with ExplorationClient() as client:
        client.set_cookies(ltuid, ltoken, cookie_token)
        return await client.get_exploration_data(uid)

async def get_exploration_summary(uid: int, ltuid: int, ltoken: str, cookie_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get exploration summary for a user.
    
    Args:
        uid: Genshin Impact UID
        ltuid: HoYoLAB user ID
        ltoken: HoYoLAB login token
        cookie_token: Optional cookie token for additional features
        
    Returns:
        Dictionary containing exploration summary
    """
    async with ExplorationClient() as client:
        client.set_cookies(ltuid, ltoken, cookie_token)
        return await client.get_exploration_summary(uid)

# Example usage
if __name__ == "__main__":
    async def main():
        # Example usage - replace with your actual credentials
        LTUID = 119480035  # Your HoYoLAB user ID
        LTOKEN = "your_ltoken_here"  # Your HoYoLAB login token
        UID = 710785423  # Target Genshin Impact UID
        
        print("🌍 Fetching exploration data...")
        
        try:
            # Get exploration summary
            summary = await get_exploration_summary(UID, LTUID, LTOKEN)
            
            if "error" in summary:
                print(f"❌ Error: {summary['error']}")
                return
            
            print(f"\n📊 Exploration Summary for {summary['player_nickname']} (AR {summary['adventure_rank']})")
            print("=" * 60)
            print(f"🗺️  Total Regions: {summary['summary']['total_regions']}")
            print(f"✅ Fully Explored: {summary['summary']['fully_explored_regions']}")
            print(f"📈 Average Exploration: {summary['summary']['average_exploration_percentage']}%")
            print(f"📦 Total Chests: {summary['summary']['total_chests_opened']}")
            print(f"🗿 Total Oculi: {summary['summary']['total_oculi_collected']}")
            print(f"🏆 Achievements: {summary['summary']['achievements']}")
            
            print(f"\n🌎 Region Details:")
            for region in summary['regions']:
                print(f"  • {region['name']}: {region['exploration_percentage']}% (Level {region['level']})")
            
            # Get detailed exploration data
            print(f"\n🔍 Fetching detailed exploration data...")
            detailed = await get_user_exploration(UID, LTUID, LTOKEN)
            
            if "error" not in detailed and detailed.get("teapot"):
                teapot = detailed["teapot"]
                print(f"\n🏠 Serenitea Pot:")
                print(f"  • Level: {teapot['level']}")
                print(f"  • Comfort: {teapot['comfort']} ({teapot['comfort_name']})")
                print(f"  • Items: {teapot['items']}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Run the example
    asyncio.run(main()) 