"""
Enhanced Farming Route Service for Frontend Integration
Provides structured data for HoYoLAB interactive map integration and custom marker injection
"""

from typing import Dict, List, Any, Optional
from models import (
    MapMarker, FarmingLocation, DailyFarmingRoute, 
    WeeklyFarmingRoute, EnhancedFarmingRouteResponse
)
import json


class FarmingRouteService:
    """Service for generating enhanced farming routes with frontend integration support."""
    
    def __init__(self):
        # Comprehensive material location database with coordinates
        self.material_locations = {
            # Mondstadt Local Specialties
            "Cecilia": {
                "region": "Mondstadt",
                "type": "local_specialty",
                "respawn_time": "48 hours",
                "markers": [
                    {
                        "id": "cecilia_001",
                        "name": "Cecilia Garden Area",
                        "coordinates": {"x": -1234.5, "y": 123.4, "z": 567.8},
                        "quantity": 3,
                        "notes": "Near the Cecilia Garden domain"
                    },
                    {
                        "id": "cecilia_002", 
                        "name": "Starsnatch Cliff Peak",
                        "coordinates": {"x": -1456.7, "y": 234.5, "z": 678.9},
                        "quantity": 5,
                        "notes": "Highest point of Starsnatch Cliff"
                    }
                ]
            },
            "Small Lamp Grass": {
                "region": "Mondstadt",
                "type": "local_specialty",
                "respawn_time": "48 hours",
                "markers": [
                    {
                        "id": "lamp_grass_001",
                        "name": "Wolvendom Area",
                        "coordinates": {"x": -2345.6, "y": 345.6, "z": 789.0},
                        "quantity": 8,
                        "notes": "Around the Wolvendom area, near electro crystals"
                    },
                    {
                        "id": "lamp_grass_002",
                        "name": "Springvale Outskirts",
                        "coordinates": {"x": -2567.8, "y": 456.7, "z": 890.1},
                        "quantity": 7,
                        "notes": "South of Springvale village"
                    }
                ]
            },
            
            # Liyue Local Specialties
            "Cor Lapis": {
                "region": "Liyue",
                "type": "local_specialty", 
                "respawn_time": "48 hours",
                "markers": [
                    {
                        "id": "cor_lapis_001",
                        "name": "Mt. Hulao Peak",
                        "coordinates": {"x": 1234.5, "y": 567.8, "z": 901.2},
                        "quantity": 4,
                        "notes": "On the mountain peaks, look for orange glow"
                    },
                    {
                        "id": "cor_lapis_002",
                        "name": "Guyun Stone Forest",
                        "coordinates": {"x": 1456.7, "y": 678.9, "z": 012.3},
                        "quantity": 6,
                        "notes": "On the stone pillars and cliffs"
                    },
                    {
                        "id": "cor_lapis_003",
                        "name": "Mt. Tianheng",
                        "coordinates": {"x": 1678.9, "y": 789.0, "z": 123.4},
                        "quantity": 3,
                        "notes": "Near Liyue Harbor, on the mountain"
                    }
                ]
            },
            "Silk Flower": {
                "region": "Liyue",
                "type": "local_specialty",
                "respawn_time": "48 hours",
                "markers": [
                    {
                        "id": "silk_flower_001",
                        "name": "Liyue Harbor Terrace",
                        "coordinates": {"x": 1890.1, "y": 901.2, "z": 234.5},
                        "quantity": 9,
                        "notes": "On the upper terraces of Liyue Harbor"
                    },
                    {
                        "id": "silk_flower_002",
                        "name": "Wangshu Inn Balcony",
                        "coordinates": {"x": 2012.3, "y": 123.4, "z": 345.6},
                        "quantity": 9,
                        "notes": "On the balconies and around the inn"
                    }
                ]
            },
            "Qingxin": {
                "region": "Liyue",
                "type": "local_specialty",
                "respawn_time": "48 hours",
                "markers": [
                    {
                        "id": "qingxin_001",
                        "name": "Jueyun Karst Peaks",
                        "coordinates": {"x": 2234.5, "y": 345.6, "z": 456.7},
                        "quantity": 6,
                        "notes": "On the highest peaks in Jueyun Karst"
                    },
                    {
                        "id": "qingxin_002",
                        "name": "Guyun Stone Forest Heights",
                        "coordinates": {"x": 2456.7, "y": 567.8, "z": 678.9},
                        "quantity": 4,
                        "notes": "On top of the stone pillars"
                    }
                ]
            },
            
            # Inazuma Local Specialties
            "Naku Weed": {
                "region": "Inazuma",
                "type": "local_specialty",
                "respawn_time": "48 hours",
                "markers": [
                    {
                        "id": "naku_weed_001",
                        "name": "Yashiori Island Battlefield",
                        "coordinates": {"x": 3234.5, "y": 678.9, "z": 789.0},
                        "quantity": 12,
                        "notes": "In areas affected by electro, purple glow"
                    },
                    {
                        "id": "naku_weed_002",
                        "name": "Kannazuka Furnace",
                        "coordinates": {"x": 3456.7, "y": 789.0, "z": 890.1},
                        "quantity": 8,
                        "notes": "Around the Mikage Furnace area"
                    }
                ]
            },
            "Sakura Bloom": {
                "region": "Inazuma",
                "type": "local_specialty",
                "respawn_time": "48 hours",
                "markers": [
                    {
                        "id": "sakura_bloom_001",
                        "name": "Grand Narukami Shrine",
                        "coordinates": {"x": 3678.9, "y": 890.1, "z": 901.2},
                        "quantity": 8,
                        "notes": "Around the Sacred Sakura tree"
                    },
                    {
                        "id": "sakura_bloom_002",
                        "name": "Mt. Yougou Slopes",
                        "coordinates": {"x": 3890.1, "y": 012.3, "z": 123.4},
                        "quantity": 7,
                        "notes": "On the slopes leading to the shrine"
                    }
                ]
            }
        }
        
        # Boss locations with coordinates
        self.boss_locations = {
            "Anemo Hypostasis": {
                "region": "Mondstadt",
                "coordinates": {"x": -1000.0, "y": 200.0, "z": 500.0},
                "resin_cost": 40,
                "materials": ["Hurricane Seed", "Vayuda Turquoise"],
                "respawn": "Immediate after defeat"
            },
            "Electro Hypostasis": {
                "region": "Mondstadt", 
                "coordinates": {"x": -1500.0, "y": 300.0, "z": 600.0},
                "resin_cost": 40,
                "materials": ["Lightning Prism", "Vajrada Amethyst"],
                "respawn": "Immediate after defeat"
            },
            "Geo Hypostasis": {
                "region": "Liyue",
                "coordinates": {"x": 2000.0, "y": 400.0, "z": 700.0},
                "resin_cost": 40,
                "materials": ["Basalt Pillar", "Prithiva Topaz"],
                "respawn": "Immediate after defeat"
            },
            "Cryo Regisvine": {
                "region": "Dragonspine",
                "coordinates": {"x": -500.0, "y": 100.0, "z": 800.0},
                "resin_cost": 40,
                "materials": ["Hoarfrost Core", "Shivada Jade"],
                "respawn": "Immediate after defeat"
            },
            "Pyro Regisvine": {
                "region": "Liyue",
                "coordinates": {"x": 1500.0, "y": 250.0, "z": 900.0},
                "resin_cost": 40,
                "materials": ["Everflame Seed", "Agnidus Agate"],
                "respawn": "Immediate after defeat"
            }
        }
        
        # Domain locations
        self.domain_locations = {
            "Cecilia Garden": {
                "region": "Mondstadt",
                "coordinates": {"x": -1200.0, "y": 150.0, "z": 400.0},
                "resin_cost": 20,
                "materials": ["Teachings of Resistance", "Guide to Resistance", "Philosophies of Resistance"],
                "schedule": ["Tuesday", "Friday", "Sunday"]
            },
            "Forsaken Rift": {
                "region": "Mondstadt",
                "coordinates": {"x": -1800.0, "y": 350.0, "z": 650.0},
                "resin_cost": 20,
                "materials": ["Teachings of Freedom", "Guide to Freedom", "Philosophies of Freedom"],
                "schedule": ["Monday", "Thursday", "Sunday"]
            },
            "Taishan Mansion": {
                "region": "Liyue",
                "coordinates": {"x": 1800.0, "y": 300.0, "z": 550.0},
                "resin_cost": 20,
                "materials": ["Teachings of Prosperity", "Guide to Prosperity", "Philosophies of Prosperity"],
                "schedule": ["Monday", "Thursday", "Sunday"]
            }
        }
    
    async def generate_enhanced_farming_route(self, materials: List[str], uid: Optional[int] = None) -> EnhancedFarmingRouteResponse:
        """Generate enhanced farming route with frontend integration data."""
        
        # Analyze requested materials
        material_analysis = self._analyze_materials(materials)
        
        # Generate map markers
        map_markers = self._generate_map_markers(material_analysis)
        
        # Create farming locations
        farming_locations = self._create_farming_locations(material_analysis)
        
        # Generate daily routes
        daily_routes = self._generate_daily_routes(farming_locations)
        
        # Generate weekly routes
        weekly_routes = self._generate_weekly_routes(material_analysis)
        
        # Create HoYoLAB map configuration
        hoyolab_config = self._create_hoyolab_map_config(map_markers)
        
        # Create custom marker injection data
        marker_injection = self._create_marker_injection_data(map_markers)
        
        # Generate summary and optimization tips
        summary = self._generate_summary(material_analysis, daily_routes, weekly_routes)
        optimization_tips = self._generate_optimization_tips(material_analysis)
        
        # Estimate completion times
        completion_times = self._estimate_completion_times(daily_routes, weekly_routes)
        
        return EnhancedFarmingRouteResponse(
            materials=materials,
            uid=uid,
            map_markers=map_markers,
            farming_locations=farming_locations,
            daily_routes=daily_routes,
            weekly_routes=weekly_routes,
            hoyolab_map_config=hoyolab_config,
            custom_marker_injection=marker_injection,
            summary=summary,
            optimization_tips=optimization_tips,
            estimated_completion_time=completion_times,
            route_description=self._generate_route_description(daily_routes, weekly_routes),
            sources=["HoYoLAB Interactive Map", "Genshin Impact Wiki", "Community Farming Guides"]
        )
    
    def _analyze_materials(self, materials: List[str]) -> Dict[str, Any]:
        """Analyze requested materials and categorize them."""
        analysis = {
            "local_specialties": [],
            "boss_materials": [],
            "domain_materials": [],
            "common_materials": [],
            "regions_needed": set(),
            "total_materials": len(materials)
        }
        
        for material in materials:
            # Check if it's a local specialty
            if material in self.material_locations:
                analysis["local_specialties"].append(material)
                analysis["regions_needed"].add(self.material_locations[material]["region"])
            
            # Check boss materials
            for boss, boss_data in self.boss_locations.items():
                if material in boss_data["materials"]:
                    analysis["boss_materials"].append({
                        "material": material,
                        "boss": boss,
                        "data": boss_data
                    })
                    analysis["regions_needed"].add(boss_data["region"])
            
            # Check domain materials
            for domain, domain_data in self.domain_locations.items():
                if material in domain_data["materials"]:
                    analysis["domain_materials"].append({
                        "material": material,
                        "domain": domain,
                        "data": domain_data
                    })
                    analysis["regions_needed"].add(domain_data["region"])
        
        analysis["regions_needed"] = list(analysis["regions_needed"])
        return analysis
    
    def _generate_map_markers(self, analysis: Dict[str, Any]) -> List[MapMarker]:
        """Generate map markers for all farming locations."""
        markers = []
        
        # Local specialty markers
        for material in analysis["local_specialties"]:
            material_data = self.material_locations[material]
            for marker_data in material_data["markers"]:
                marker = MapMarker(
                    id=marker_data["id"],
                    name=f"{material} - {marker_data['name']}",
                    type="local_specialty",
                    coordinates=marker_data["coordinates"],
                    region=material_data["region"],
                    description=f"Farm {material} here. {marker_data.get('notes', '')}",
                    icon_url=f"/icons/materials/{material.lower().replace(' ', '_')}.png",
                    respawn_time=material_data["respawn_time"],
                    quantity_available=marker_data.get("quantity", 1),
                    farming_notes=marker_data.get("notes", "")
                )
                markers.append(marker)
        
        # Boss markers
        for boss_material in analysis["boss_materials"]:
            boss = boss_material["boss"]
            boss_data = boss_material["data"]
            marker = MapMarker(
                id=f"boss_{boss.lower().replace(' ', '_')}",
                name=f"{boss} Boss",
                type="boss",
                coordinates=boss_data["coordinates"],
                region=boss_data["region"],
                description=f"Defeat {boss} for {', '.join(boss_data['materials'])}",
                icon_url=f"/icons/bosses/{boss.lower().replace(' ', '_')}.png",
                respawn_time=boss_data["respawn"],
                resin_cost=boss_data["resin_cost"],
                farming_notes=f"Drops: {', '.join(boss_data['materials'])}"
            )
            markers.append(marker)
        
        # Domain markers
        for domain_material in analysis["domain_materials"]:
            domain = domain_material["domain"]
            domain_data = domain_material["data"]
            marker = MapMarker(
                id=f"domain_{domain.lower().replace(' ', '_')}",
                name=f"{domain} Domain",
                type="domain",
                coordinates=domain_data["coordinates"],
                region=domain_data["region"],
                description=f"Farm talent materials at {domain}",
                icon_url=f"/icons/domains/{domain.lower().replace(' ', '_')}.png",
                respawn_time="Always available",
                resin_cost=domain_data["resin_cost"],
                farming_notes=f"Available: {', '.join(domain_data['schedule'])}"
            )
            markers.append(marker)
        
        return markers
    
    def _create_farming_locations(self, analysis: Dict[str, Any]) -> List[FarmingLocation]:
        """Create structured farming locations."""
        locations = []
        
        # Group markers by location for local specialties
        for material in analysis["local_specialties"]:
            material_data = self.material_locations[material]
            
            # Create markers for this material
            location_markers = []
            for marker_data in material_data["markers"]:
                marker = MapMarker(
                    id=marker_data["id"],
                    name=f"{material} - {marker_data['name']}",
                    type="local_specialty",
                    coordinates=marker_data["coordinates"],
                    region=material_data["region"],
                    description=f"Farm {material} here",
                    respawn_time=material_data["respawn_time"],
                    quantity_available=marker_data.get("quantity", 1)
                )
                location_markers.append(marker)
            
            # Calculate total nodes and route order
            total_nodes = sum(marker.quantity_available or 1 for marker in location_markers)
            route_order = [marker.id for marker in location_markers]
            
            location = FarmingLocation(
                location_name=f"{material} Farming Route",
                region=material_data["region"],
                material_type="local_specialty",
                markers=location_markers,
                total_nodes=total_nodes,
                estimated_time="15-20 minutes",
                best_route_order=route_order,
                tips=[
                    f"Respawns every {material_data['respawn_time']}",
                    "Use interactive map to mark collected nodes",
                    "Consider co-op for faster collection"
                ]
            )
            locations.append(location)
        
        return locations
    
    def _generate_daily_routes(self, locations: List[FarmingLocation]) -> List[DailyFarmingRoute]:
        """Generate optimized daily farming routes."""
        if not locations:
            return []
        
        # Group locations by region for efficient routing
        region_groups = {}
        for location in locations:
            if location.region not in region_groups:
                region_groups[location.region] = []
            region_groups[location.region].append(location)
        
        daily_routes = []
        for region, region_locations in region_groups.items():
            route = DailyFarmingRoute(
                route_name=f"{region} Daily Farming Route",
                total_estimated_time=f"{len(region_locations) * 20} minutes",
                locations=region_locations,
                route_order=[loc.location_name for loc in region_locations],
                preparation_tips=[
                    "Bring a character with movement abilities",
                    "Use portable waypoints for efficiency",
                    "Check respawn timers before starting",
                    "Consider using interactive map markers"
                ]
            )
            daily_routes.append(route)
        
        return daily_routes
    
    def _generate_weekly_routes(self, analysis: Dict[str, Any]) -> List[WeeklyFarmingRoute]:
        """Generate weekly farming routes for bosses and domains."""
        weekly_routes = []
        
        if analysis["boss_materials"] or analysis["domain_materials"]:
            # Calculate total resin cost
            total_resin = 0
            bosses = []
            domains = []
            
            for boss_material in analysis["boss_materials"]:
                boss_data = boss_material["data"]
                total_resin += boss_data["resin_cost"]
                bosses.append({
                    "name": boss_material["boss"],
                    "materials": boss_data["materials"],
                    "resin_cost": boss_data["resin_cost"],
                    "region": boss_data["region"]
                })
            
            for domain_material in analysis["domain_materials"]:
                domain_data = domain_material["data"]
                domains.append({
                    "name": domain_material["domain"],
                    "materials": domain_data["materials"],
                    "resin_cost": domain_data["resin_cost"],
                    "schedule": domain_data["schedule"],
                    "region": domain_data["region"]
                })
            
            # Create schedule recommendations
            schedule = {
                "Monday": [],
                "Tuesday": [],
                "Wednesday": [],
                "Thursday": [],
                "Friday": [],
                "Saturday": [],
                "Sunday": []
            }
            
            for domain in domains:
                for day in domain["schedule"]:
                    schedule[day].append(f"{domain['name']} - {domain['materials'][0]}")
            
            for boss in bosses:
                schedule["Monday"].append(f"{boss['name']} Boss")
            
            route = WeeklyFarmingRoute(
                route_name="Weekly Resin Activities",
                weekly_bosses=bosses,
                domains=domains,
                total_resin_cost=total_resin,
                schedule_recommendations=schedule
            )
            weekly_routes.append(route)
        
        return weekly_routes
    
    def _create_hoyolab_map_config(self, markers: List[MapMarker]) -> Dict[str, Any]:
        """Create configuration for HoYoLAB interactive map integration."""
        return {
            "map_url": "https://act.hoyolab.com/ys/app/interactive-map/index.html",
            "integration_method": "custom_markers",
            "marker_categories": {
                "local_specialty": {
                    "color": "#4CAF50",
                    "icon": "specialty",
                    "priority": 1
                },
                "boss": {
                    "color": "#F44336", 
                    "icon": "boss",
                    "priority": 2
                },
                "domain": {
                    "color": "#2196F3",
                    "icon": "domain", 
                    "priority": 3
                }
            },
            "total_markers": len(markers),
            "regions_covered": list(set(marker.region for marker in markers)),
            "javascript_injection": {
                "marker_data": [
                    {
                        "id": marker.id,
                        "name": marker.name,
                        "type": marker.type,
                        "coordinates": marker.coordinates,
                        "region": marker.region,
                        "description": marker.description,
                        "icon_url": marker.icon_url,
                        "respawn_time": marker.respawn_time,
                        "resin_cost": marker.resin_cost,
                        "quantity": marker.quantity_available,
                        "notes": marker.farming_notes
                    } for marker in markers
                ]
            }
        }
    
    def _create_marker_injection_data(self, markers: List[MapMarker]) -> Dict[str, Any]:
        """Create data structure for custom marker injection into HoYoLAB map."""
        return {
            "injection_script": """
            // Custom Genshin Farming Route Markers
            function injectCustomMarkers(markerData) {
                const customMarkers = markerData;
                
                // Create custom marker layer
                const customLayer = L.layerGroup();
                
                customMarkers.forEach(marker => {
                    const customIcon = L.divIcon({
                        className: `custom-marker marker-${marker.type}`,
                        html: `
                            <div class="marker-content">
                                <img src="${marker.icon_url}" alt="${marker.name}" />
                                <span class="marker-label">${marker.name}</span>
                            </div>
                        `,
                        iconSize: [30, 30],
                        iconAnchor: [15, 30]
                    });
                    
                    const markerInstance = L.marker([marker.coordinates.y, marker.coordinates.x], {
                        icon: customIcon
                    }).bindPopup(`
                        <div class="custom-popup">
                            <h3>${marker.name}</h3>
                            <p><strong>Region:</strong> ${marker.region}</p>
                            <p><strong>Type:</strong> ${marker.type}</p>
                            <p>${marker.description}</p>
                            ${marker.respawn_time ? `<p><strong>Respawn:</strong> ${marker.respawn_time}</p>` : ''}
                            ${marker.resin_cost ? `<p><strong>Resin Cost:</strong> ${marker.resin_cost}</p>` : ''}
                            ${marker.quantity ? `<p><strong>Quantity:</strong> ${marker.quantity}</p>` : ''}
                            ${marker.notes ? `<p><strong>Notes:</strong> ${marker.notes}</p>` : ''}
                        </div>
                    `);
                    
                    customLayer.addLayer(markerInstance);
                });
                
                // Add to map
                customLayer.addTo(map);
                
                // Add layer control
                L.control.layers(null, {
                    'Farming Route Markers': customLayer
                }).addTo(map);
            }
            
            // CSS for custom markers
            const customCSS = `
                .custom-marker {
                    background: transparent;
                    border: none;
                }
                
                .marker-content {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                }
                
                .marker-content img {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    border: 2px solid #fff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }
                
                .marker-label {
                    font-size: 10px;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 2px 4px;
                    border-radius: 3px;
                    margin-top: 2px;
                    white-space: nowrap;
                }
                
                .marker-local_specialty .marker-content img {
                    border-color: #4CAF50;
                }
                
                .marker-boss .marker-content img {
                    border-color: #F44336;
                }
                
                .marker-domain .marker-content img {
                    border-color: #2196F3;
                }
                
                .custom-popup {
                    min-width: 200px;
                }
                
                .custom-popup h3 {
                    margin: 0 0 10px 0;
                    color: #333;
                }
                
                .custom-popup p {
                    margin: 5px 0;
                    font-size: 12px;
                }
            `;
            
            // Inject CSS
            const style = document.createElement('style');
            style.textContent = customCSS;
            document.head.appendChild(style);
            """,
            "marker_data": [
                {
                    "id": marker.id,
                    "name": marker.name,
                    "type": marker.type,
                    "coordinates": marker.coordinates,
                    "region": marker.region,
                    "description": marker.description,
                    "icon_url": marker.icon_url or f"/icons/materials/default.png",
                    "respawn_time": marker.respawn_time,
                    "resin_cost": marker.resin_cost,
                    "quantity": marker.quantity_available,
                    "notes": marker.farming_notes
                } for marker in markers
            ],
            "usage_instructions": [
                "1. Open HoYoLAB Interactive Map in your browser",
                "2. Open browser developer tools (F12)",
                "3. Go to Console tab",
                "4. Copy and paste the injection_script",
                "5. Call injectCustomMarkers(marker_data) with the provided marker_data",
                "6. Custom farming route markers will appear on the map",
                "7. Use the layer control to toggle marker visibility"
            ]
        }
    
    def _generate_summary(self, analysis: Dict[str, Any], daily_routes: List[DailyFarmingRoute], weekly_routes: List[WeeklyFarmingRoute]) -> Dict[str, Any]:
        """Generate farming route summary."""
        total_resin = sum(route.total_resin_cost for route in weekly_routes)
        
        return {
            "total_materials": analysis["total_materials"],
            "regions_involved": len(analysis["regions_needed"]),
            "daily_locations": len(daily_routes),
            "weekly_activities": len(weekly_routes),
            "total_weekly_resin": total_resin,
            "farming_efficiency": "High" if total_resin < 200 else "Medium" if total_resin < 400 else "Low",
            "estimated_days_to_complete": max(7, total_resin // 160 * 7),  # Based on daily resin
            "regions_needed": analysis["regions_needed"]
        }
    
    def _generate_optimization_tips(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization tips for farming."""
        tips = [
            "Use the HoYoLAB interactive map with custom markers for efficient routing",
            "Mark collected nodes to track respawn timers",
            "Consider co-op farming for faster collection",
            "Use characters with movement abilities (Kazuha, Venti, etc.)",
            "Place portable waypoints near farming clusters"
        ]
        
        if len(analysis["regions_needed"]) > 2:
            tips.append("Focus on one region per day to minimize travel time")
        
        if analysis["boss_materials"]:
            tips.append("Prioritize weekly bosses early in the week for talent materials")
        
        if analysis["domain_materials"]:
            tips.append("Check domain schedules and farm on appropriate days")
        
        return tips
    
    def _estimate_completion_times(self, daily_routes: List[DailyFarmingRoute], weekly_routes: List[WeeklyFarmingRoute]) -> Dict[str, str]:
        """Estimate completion times for different activities."""
        daily_time = sum(int(route.total_estimated_time.split()[0]) for route in daily_routes)
        weekly_time = len(weekly_routes) * 30  # Estimate 30 min per weekly route
        
        return {
            "daily_farming": f"{daily_time} minutes",
            "weekly_activities": f"{weekly_time} minutes", 
            "total_per_week": f"{daily_time * 3 + weekly_time} minutes",  # Assume farming 3 days per week
            "recommended_schedule": "Farm local specialties every 2 days, do weekly activities on Monday"
        }
    
    def _generate_route_description(self, daily_routes: List[DailyFarmingRoute], weekly_routes: List[WeeklyFarmingRoute]) -> str:
        """Generate human-readable route description."""
        description = "Enhanced Farming Route with Interactive Map Integration\n\n"
        
        if daily_routes:
            description += "Daily Routes:\n"
            for route in daily_routes:
                description += f"- {route.route_name}: {route.total_estimated_time}\n"
                for location in route.locations:
                    description += f"  • {location.location_name} ({location.total_nodes} nodes)\n"
        
        if weekly_routes:
            description += "\nWeekly Activities:\n"
            for route in weekly_routes:
                description += f"- {route.route_name}: {route.total_resin_cost} resin\n"
                for boss in route.weekly_bosses:
                    description += f"  • {boss['name']} Boss ({boss['resin_cost']} resin)\n"
                for domain in route.domains:
                    description += f"  • {domain['name']} Domain ({', '.join(domain['schedule'])})\n"
        
        description += "\nUse the provided map markers and injection script for optimal farming experience!"
        
        return description


# Singleton instance
farming_route_service = FarmingRouteService() 