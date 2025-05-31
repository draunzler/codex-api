from typing import Dict, List, Any, Optional
from database import Cache
import json


class MaterialsDatabase:
    """Database for character materials and upgrade requirements."""
    
    def __init__(self):
        # Character ascension materials mapping
        self.character_materials = {
            # Pyro Characters
            "Hu Tao": {
                "ascension_materials": [
                    "Agnidus Agate",
                    "Juvenile Jade",
                    "Silk Flower",
                    "Whopperflower Nectar"
                ],
                "talent_materials": [
                    "Teachings of Diligence",
                    "Guide to Diligence", 
                    "Philosophies of Diligence",
                    "Shard of a Foul Legacy",
                    "Crown of Insight"
                ],
                "weekly_boss": "Childe",
                "local_specialty": "Silk Flower",
                "common_material": "Whopperflower Nectar"
            },
            "Diluc": {
                "ascension_materials": [
                    "Agnidus Agate",
                    "Everflame Seed",
                    "Small Lamp Grass",
                    "Recruit's Insignia"
                ],
                "talent_materials": [
                    "Teachings of Resistance",
                    "Guide to Resistance",
                    "Philosophies of Resistance", 
                    "Dvalin's Plume",
                    "Crown of Insight"
                ],
                "weekly_boss": "Stormterror",
                "local_specialty": "Small Lamp Grass",
                "common_material": "Recruit's Insignia"
            },
            
            # Hydro Characters
            "Childe": {
                "ascension_materials": [
                    "Varunada Lazurite",
                    "Cleansing Heart",
                    "Starconch",
                    "Recruit's Insignia"
                ],
                "talent_materials": [
                    "Teachings of Freedom",
                    "Guide to Freedom",
                    "Philosophies of Freedom",
                    "Shard of a Foul Legacy",
                    "Crown of Insight"
                ],
                "weekly_boss": "Childe",
                "local_specialty": "Starconch",
                "common_material": "Recruit's Insignia"
            },
            "Xingqiu": {
                "ascension_materials": [
                    "Varunada Lazurite",
                    "Cleansing Heart",
                    "Silk Flower",
                    "Damaged Mask"
                ],
                "talent_materials": [
                    "Teachings of Gold",
                    "Guide to Gold",
                    "Philosophies of Gold",
                    "Tail of Boreas",
                    "Crown of Insight"
                ],
                "weekly_boss": "Andrius",
                "local_specialty": "Silk Flower",
                "common_material": "Damaged Mask"
            },
            
            # Cryo Characters
            "Ganyu": {
                "ascension_materials": [
                    "Shivada Jade",
                    "Hoarfrost Core",
                    "Qingxin",
                    "Whopperflower Nectar"
                ],
                "talent_materials": [
                    "Teachings of Diligence",
                    "Guide to Diligence",
                    "Philosophies of Diligence",
                    "Shadow of the Warrior",
                    "Crown of Insight"
                ],
                "weekly_boss": "Childe",
                "local_specialty": "Qingxin",
                "common_material": "Whopperflower Nectar"
            },
            "Ayaka": {
                "ascension_materials": [
                    "Shivada Jade",
                    "Perpetual Heart",
                    "Sakura Bloom",
                    "Handguard"
                ],
                "talent_materials": [
                    "Teachings of Elegance",
                    "Guide to Elegance",
                    "Philosophies of Elegance",
                    "Bloodjade Branch",
                    "Crown of Insight"
                ],
                "weekly_boss": "Azhdaha",
                "local_specialty": "Sakura Bloom",
                "common_material": "Handguard"
            },
            
            # Electro Characters
            "Raiden Shogun": {
                "ascension_materials": [
                    "Vajrada Amethyst",
                    "Storm Beads",
                    "Naku Weed",
                    "Handguard"
                ],
                "talent_materials": [
                    "Teachings of Light",
                    "Guide to Light",
                    "Philosophies of Light",
                    "Molten Moment",
                    "Crown of Insight"
                ],
                "weekly_boss": "La Signora",
                "local_specialty": "Naku Weed",
                "common_material": "Handguard"
            },
            "Fischl": {
                "ascension_materials": [
                    "Vajrada Amethyst",
                    "Lightning Prism",
                    "Small Lamp Grass",
                    "Arrowhead"
                ],
                "talent_materials": [
                    "Teachings of Ballad",
                    "Guide to Ballad",
                    "Philosophies of Ballad",
                    "Spirit Locket of Boreas",
                    "Crown of Insight"
                ],
                "weekly_boss": "Andrius",
                "local_specialty": "Small Lamp Grass",
                "common_material": "Arrowhead"
            },
            
            # Anemo Characters
            "Venti": {
                "ascension_materials": [
                    "Vayuda Turquoise",
                    "Hurricane Seed",
                    "Cecilia",
                    "Slime Condensate"
                ],
                "talent_materials": [
                    "Teachings of Ballad",
                    "Guide to Ballad",
                    "Philosophies of Ballad",
                    "Tail of Boreas",
                    "Crown of Insight"
                ],
                "weekly_boss": "Andrius",
                "local_specialty": "Cecilia",
                "common_material": "Slime Condensate"
            },
            "Kazuha": {
                "ascension_materials": [
                    "Vayuda Turquoise",
                    "Marionette Core",
                    "Sea Ganoderma",
                    "Treasure Hoarder Insignia"
                ],
                "talent_materials": [
                    "Teachings of Diligence",
                    "Guide to Diligence",
                    "Philosophies of Diligence",
                    "Gilded Scale",
                    "Crown of Insight"
                ],
                "weekly_boss": "Azhdaha",
                "local_specialty": "Sea Ganoderma",
                "common_material": "Treasure Hoarder Insignia"
            },
            
            # Geo Characters
            "Zhongli": {
                "ascension_materials": [
                    "Prithiva Topaz",
                    "Basalt Pillar",
                    "Cor Lapis",
                    "Slime Condensate"
                ],
                "talent_materials": [
                    "Teachings of Gold",
                    "Guide to Gold",
                    "Philosophies of Gold",
                    "Tusk of Monoceros Caeli",
                    "Crown of Insight"
                ],
                "weekly_boss": "Childe",
                "local_specialty": "Cor Lapis",
                "common_material": "Slime Condensate"
            },
            "Albedo": {
                "ascension_materials": [
                    "Prithiva Topaz",
                    "Basalt Pillar",
                    "Cecilia",
                    "Divining Scroll"
                ],
                "talent_materials": [
                    "Teachings of Ballad",
                    "Guide to Ballad",
                    "Philosophies of Ballad",
                    "Tusk of Monoceros Caeli",
                    "Crown of Insight"
                ],
                "weekly_boss": "Childe",
                "local_specialty": "Cecilia",
                "common_material": "Divining Scroll"
            }
        }
        
        # Material locations mapping
        self.material_locations = {
            # Local Specialties
            "Silk Flower": {
                "region": "Liyue",
                "locations": ["Liyue Harbor", "Wangshu Inn"],
                "respawn_time": "48 hours",
                "total_nodes": 18
            },
            "Qingxin": {
                "region": "Liyue", 
                "locations": ["High peaks in Liyue", "Jueyun Karst"],
                "respawn_time": "48 hours",
                "total_nodes": 10
            },
            "Cor Lapis": {
                "region": "Liyue",
                "locations": ["Mt. Hulao", "Guyun Stone Forest", "Mt. Tianheng"],
                "respawn_time": "48 hours",
                "total_nodes": 10
            },
            "Cecilia": {
                "region": "Mondstadt",
                "locations": ["Starsnatch Cliff"],
                "respawn_time": "48 hours", 
                "total_nodes": 8
            },
            "Small Lamp Grass": {
                "region": "Mondstadt",
                "locations": ["Wolvendom", "Springvale"],
                "respawn_time": "48 hours",
                "total_nodes": 15
            },
            "Starconch": {
                "region": "Liyue",
                "locations": ["Yaoguang Shoal", "Guyun Stone Forest beaches"],
                "respawn_time": "48 hours",
                "total_nodes": 12
            },
            "Naku Weed": {
                "region": "Inazuma",
                "locations": ["Yashiori Island", "Kannazuka"],
                "respawn_time": "48 hours",
                "total_nodes": 20
            },
            "Sakura Bloom": {
                "region": "Inazuma", 
                "locations": ["Narukami Island", "Mt. Yougou"],
                "respawn_time": "48 hours",
                "total_nodes": 15
            },
            "Sea Ganoderma": {
                "region": "Inazuma",
                "locations": ["Guyun Stone Forest", "Liyue coastlines"],
                "respawn_time": "48 hours",
                "total_nodes": 18
            },
            
            # Boss Materials
            "Juvenile Jade": {
                "boss": "Primo Geovishap",
                "location": "Tianqiu Valley",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Cleansing Heart": {
                "boss": "Rhodeia of Loch",
                "location": "Liyue",
                "cost": "40 Resin", 
                "respawn": "Weekly reset"
            },
            "Hurricane Seed": {
                "boss": "Anemo Hypostasis",
                "location": "Mondstadt",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Lightning Prism": {
                "boss": "Electro Hypostasis", 
                "location": "Mondstadt",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Hoarfrost Core": {
                "boss": "Cryo Regisvine",
                "location": "Dragonspine",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Everflame Seed": {
                "boss": "Pyro Regisvine",
                "location": "Liyue",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Basalt Pillar": {
                "boss": "Geo Hypostasis",
                "location": "Liyue",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Marionette Core": {
                "boss": "Maguu Kenki",
                "location": "Inazuma",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Perpetual Heart": {
                "boss": "Perpetual Mechanical Array",
                "location": "Inazuma",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            },
            "Storm Beads": {
                "boss": "Thunder Manifestation",
                "location": "Inazuma",
                "cost": "40 Resin",
                "respawn": "Weekly reset"
            }
        }
    
    async def get_character_materials(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Get all materials needed for a character."""
        try:
            # Check cache first
            cache_key = f"character_materials_{character_name}"
            cached_data = await Cache.get(cache_key)
            if cached_data:
                return cached_data
            
            if character_name not in self.character_materials:
                return None
            
            materials = self.character_materials[character_name]
            
            # Add location information for each material
            detailed_materials = {
                "character": character_name,
                "ascension_materials": [],
                "talent_materials": [],
                "weekly_boss": materials["weekly_boss"],
                "farming_summary": {
                    "daily_farmable": [],
                    "weekly_limited": [],
                    "domain_materials": []
                }
            }
            
            # Process ascension materials
            for material in materials["ascension_materials"]:
                if material in self.material_locations:
                    location_info = self.material_locations[material]
                    detailed_materials["ascension_materials"].append({
                        "name": material,
                        "location_info": location_info
                    })
                    
                    if "boss" in location_info:
                        detailed_materials["farming_summary"]["weekly_limited"].append(material)
                    else:
                        detailed_materials["farming_summary"]["daily_farmable"].append(material)
            
            # Process talent materials
            for material in materials["talent_materials"]:
                detailed_materials["talent_materials"].append({
                    "name": material,
                    "type": self._get_material_type(material)
                })
                
                if "Teachings" in material or "Guide" in material or "Philosophies" in material:
                    detailed_materials["farming_summary"]["domain_materials"].append(material)
            
            # Cache for 24 hours
            await Cache.set(cache_key, detailed_materials, ttl=86400)
            
            return detailed_materials
            
        except Exception as e:
            print(f"Error getting character materials: {str(e)}")
            return None
    
    def _get_material_type(self, material: str) -> str:
        """Determine the type of material."""
        if "Teachings" in material:
            return "talent_book_bronze"
        elif "Guide" in material:
            return "talent_book_silver"
        elif "Philosophies" in material:
            return "talent_book_gold"
        elif "Crown" in material:
            return "crown"
        else:
            return "weekly_boss_material"
    
    async def get_farming_route_for_character(self, character_name: str) -> Dict[str, Any]:
        """Get optimized farming route for a specific character."""
        try:
            materials = await self.get_character_materials(character_name)
            if not materials:
                return {"error": "Character not found"}
            
            farming_route = {
                "character": character_name,
                "daily_route": {
                    "description": "Materials you can farm daily",
                    "items": []
                },
                "weekly_route": {
                    "description": "Weekly boss and domain materials",
                    "items": []
                },
                "estimated_time": {
                    "daily": "30-45 minutes",
                    "weekly": "15-20 minutes"
                },
                "priority_order": []
            }
            
            # Add daily farmable materials
            for material in materials["ascension_materials"]:
                if material["name"] in materials["farming_summary"]["daily_farmable"]:
                    farming_route["daily_route"]["items"].append({
                        "material": material["name"],
                        "location": material["location_info"]["locations"],
                        "nodes": material["location_info"].get("total_nodes", "Unknown"),
                        "respawn": material["location_info"]["respawn_time"]
                    })
            
            # Add weekly materials
            farming_route["weekly_route"]["items"].append({
                "boss": materials["weekly_boss"],
                "materials": [mat for mat in materials["talent_materials"] 
                           if self._get_material_type(mat["name"]) == "weekly_boss_material"]
            })
            
            # Set priority order
            farming_route["priority_order"] = [
                "1. Weekly boss (for talent materials)",
                "2. World bosses (for ascension gems)",
                "3. Local specialties (daily farming)",
                "4. Talent domains (Tuesday/Friday/Sunday)",
                "5. Common materials (from enemies)"
            ]
            
            return farming_route
            
        except Exception as e:
            print(f"Error creating farming route: {str(e)}")
            return {"error": str(e)}
    
    async def get_materials_by_region(self, region: str) -> Dict[str, Any]:
        """Get all materials available in a specific region."""
        try:
            region_materials = {
                "region": region,
                "local_specialties": [],
                "bosses": [],
                "domains": []
            }
            
            for material, info in self.material_locations.items():
                if info.get("region", "").lower() == region.lower():
                    if "boss" in info:
                        region_materials["bosses"].append({
                            "material": material,
                            "boss": info["boss"],
                            "location": info["location"]
                        })
                    else:
                        region_materials["local_specialties"].append({
                            "material": material,
                            "locations": info["locations"],
                            "nodes": info.get("total_nodes", "Unknown")
                        })
            
            return region_materials
            
        except Exception as e:
            print(f"Error getting region materials: {str(e)}")
            return {"error": str(e)}


# Singleton instance
materials_db = MaterialsDatabase() 