from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserCreateRequest(BaseModel):
    """Request model for creating a new user profile."""
    uid: int = Field(..., description="Genshin Impact UID", ge=100000000, le=999999999)


class UserResponse(BaseModel):
    """Response model for user profile data."""
    uid: int
    nickname: str
    level: int
    signature: Optional[str] = None
    achievements: int
    days_active: int
    characters_count: int
    spiral_abyss: Optional[Dict[str, Any]] = None
    explorations: List[Dict[str, Any]]
    stats: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_fetch: datetime


class CharacterResponse(BaseModel):
    """Response model for character data."""
    id: int  # avatarId from Enka Network
    name: str
    element: Optional[str] = "Unknown"
    rarity: Optional[int] = 5
    level: int
    friendship: int
    constellation: int
    weapon: Optional[Dict[str, Any]] = None
    artifacts: List[Dict[str, Any]]
    talents: Optional[List[Dict[str, Any]]] = None
    stats: Optional[Dict[str, Any]] = None
    icon_url: Optional[str] = None
    local_icon_available: bool = False


class DamageCalculationRequest(BaseModel):
    """Request model for damage calculation."""
    uid: int
    character_name: str
    team_composition: List[str] = Field(..., max_items=4)
    enemy_type: str = Field(default="Standard", description="Type of enemy for calculation")


class DamageCalculationResponse(BaseModel):
    """Response model for damage calculation."""
    character: str
    team: List[str]
    enemy_type: str
    calculation: str
    summary: Dict[str, Any]


class MechanicalDamageRequest(BaseModel):
    """Request model for mechanical damage calculation."""
    uid: int
    character_name: str
    team_composition: List[str] = Field(..., max_items=4, description="Team members including the main character")
    enemy_level: int = Field(default=90, ge=1, le=100, description="Enemy level")
    enemy_resistances: Optional[Dict[str, float]] = Field(default=None, description="Custom enemy resistances")
    talent_levels: Optional[Dict[str, int]] = Field(default=None, description="Custom talent levels")


class MechanicalDamageResponse(BaseModel):
    """Response model for mechanical damage calculation."""
    character: Dict[str, Any]
    team_composition: List[str]
    base_damage: Dict[str, Any]
    reaction_damage: Dict[str, Any]
    team_buffs: List[Dict[str, Any]]
    stats_comparison: Dict[str, Any]
    enemy_info: Dict[str, Any]
    calculation_metadata: Dict[str, Any]


class BuildRecommendationRequest(BaseModel):
    """Request model for build recommendations."""
    character_name: str
    uid: Optional[int] = None
    include_current_build: bool = Field(default=False, description="Include current build analysis")


class BuildRecommendationResponse(BaseModel):
    """Response model for build recommendations."""
    character: str
    recommendations: str
    sources: List[str]
    current_build_analysis: Optional[Dict[str, Any]] = None


class QuestionRequest(BaseModel):
    """Request model for general questions."""
    question: str = Field(..., min_length=1, max_length=500)
    uid: Optional[int] = None
    include_context: bool = Field(default=True, description="Include user data as context")


class QuestionResponse(BaseModel):
    """Response model for question answers."""
    question: str
    answer: str
    context_used: bool
    character_data_used: bool = False
    characters_analyzed: int = 0
    error: Optional[str] = None


class FarmingRouteRequest(BaseModel):
    """Request model for farming route optimization."""
    materials: List[str] = Field(..., min_items=1, max_items=10)
    uid: Optional[int] = None


class FarmingRouteResponse(BaseModel):
    """Response model for farming routes."""
    materials: List[str]
    route: str
    sources: List[str]


class MapMarker(BaseModel):
    """Individual map marker for frontend integration."""
    id: str
    name: str
    type: str  # "local_specialty", "boss", "domain", "enemy", "chest"
    coordinates: Dict[str, float]  # {"x": float, "y": float, "z": float}
    region: str
    description: str
    icon_url: Optional[str] = None
    respawn_time: Optional[str] = None
    resin_cost: Optional[int] = None
    quantity_available: Optional[int] = None
    farming_notes: Optional[str] = None


class FarmingLocation(BaseModel):
    """Farming location with multiple markers."""
    location_name: str
    region: str
    material_type: str
    markers: List[MapMarker]
    total_nodes: int
    estimated_time: str
    best_route_order: List[str]  # Order of marker IDs for optimal farming
    tips: List[str]


class DailyFarmingRoute(BaseModel):
    """Daily farming route structure."""
    route_name: str
    total_estimated_time: str
    locations: List[FarmingLocation]
    route_order: List[str]  # Order of location names
    preparation_tips: List[str]


class WeeklyFarmingRoute(BaseModel):
    """Weekly farming route structure."""
    route_name: str
    weekly_bosses: List[Dict[str, Any]]
    domains: List[Dict[str, Any]]
    total_resin_cost: int
    schedule_recommendations: Dict[str, List[str]]  # Day -> activities


class EnhancedFarmingRouteResponse(BaseModel):
    """Enhanced response model for farming routes with frontend integration."""
    materials: List[str]
    uid: Optional[int] = None
    
    # Map integration data
    map_markers: List[MapMarker]
    farming_locations: List[FarmingLocation]
    
    # Route structures
    daily_routes: List[DailyFarmingRoute]
    weekly_routes: List[WeeklyFarmingRoute]
    
    # Frontend integration helpers
    hoyolab_map_config: Dict[str, Any]
    custom_marker_injection: Dict[str, Any]
    
    # Summary information
    summary: Dict[str, Any]
    optimization_tips: List[str]
    estimated_completion_time: Dict[str, str]
    
    # Original data for backward compatibility
    route_description: str
    sources: List[str]


class ExplorationResponse(BaseModel):
    """Response model for exploration progress."""
    regions: Dict[str, Dict[str, Any]]
    average_exploration: float
    total_regions: int


class ExplorationDataResponse(BaseModel):
    """Response model for detailed exploration data."""
    uid: int
    fetched_at: str
    player_info: Dict[str, Any]
    exploration: Dict[str, Any]
    world_explorations: List[Dict[str, Any]]
    teapot: Optional[Dict[str, Any]] = None
    real_time_notes: Optional[Dict[str, Any]] = None


class ExplorationSummaryResponse(BaseModel):
    """Response model for exploration summary."""
    uid: int
    player_nickname: str
    adventure_rank: int
    world_level: int
    summary: Dict[str, Any]
    regions: List[Dict[str, Any]]
    fetched_at: str


class ExplorationCredentialsRequest(BaseModel):
    """Request model for setting exploration credentials."""
    ltuid: int = Field(..., description="HoYoLAB user ID")
    ltoken: str = Field(..., description="HoYoLAB login token")
    cookie_token: Optional[str] = Field(None, description="Optional cookie token for additional features")


class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""
    running: bool
    next_update: Optional[datetime]
    update_interval_hours: int
    jobs: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response model."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


# Setup Instructions Response
class SetupInstructionsResponse(BaseModel):
    title: str
    steps: List[str]
    benefits: List[str]
    limitations: List[str]


class RefreshStatusResponse(BaseModel):
    """Response model for refresh status."""
    uid: int
    status: str  # idle, starting, fetching, processing, completed, error
    message: str
    progress: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    last_fetch: Optional[datetime] = None


# Manual Character Data Models (for hybrid approach)
class WeaponData(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    rarity: int
    level: int
    refinement: int = 1
    ascension: int = 6
    base_attack: int
    sub_stat: Optional[Dict[str, Any]] = None


class ArtifactData(BaseModel):
    id: Optional[int] = None
    name: str
    set_name: str
    rarity: int = 5
    level: int = 20
    pos: int  # 1=Flower, 2=Plume, 3=Sands, 4=Goblet, 5=Circlet
    main_stat: Dict[str, Any]
    sub_stats: List[Dict[str, Any]] = []


class TalentData(BaseModel):
    id: Optional[int] = None
    name: str
    level: int


class CharacterStatsData(BaseModel):
    base_hp: Optional[int] = None
    base_atk: Optional[int] = None
    base_def: Optional[int] = None
    total_hp: Optional[int] = None
    total_atk: Optional[int] = None
    total_def: Optional[int] = None
    crit_rate: float
    crit_dmg: float
    elemental_mastery: int = 0
    energy_recharge: float = 100.0
    pyro_dmg: float = 0
    hydro_dmg: float = 0
    electro_dmg: float = 0
    cryo_dmg: float = 0
    anemo_dmg: float = 0
    geo_dmg: float = 0
    dendro_dmg: float = 0
    physical_dmg: float = 0


class ManualCharacterRequest(BaseModel):
    uid: int
    name: str
    element: str  # Pyro, Hydro, Electro, Cryo, Anemo, Geo, Dendro
    rarity: int = 5
    level: int
    friendship: int = 10
    constellation: int = 0
    weapon: Optional[WeaponData] = None
    artifacts: List[ArtifactData] = []
    talents: List[TalentData] = []
    stats: Optional[CharacterStatsData] = None


class CharacterIconResponse(BaseModel):
    """Response model for character icon."""
    character: str
    icon_url: str
    element: str
    rarity: int


class AdvancedDamageRequest(BaseModel):
    """Request model for advanced mechanical damage calculation."""
    uid: int
    character_data: Dict[str, Any] = Field(..., description="Complete character stats and build data")
    team_composition: List[str] = Field(..., max_items=4, description="Team members including the main character")
    enemy_data: Dict[str, Any] = Field(default={}, description="Enemy stats and resistances")
    damage_scenarios: List[Dict[str, Any]] = Field(..., description="List of damage scenarios to calculate")


class AdvancedDamageResponse(BaseModel):
    """Response model for advanced mechanical damage calculation."""
    character_name: str
    team_composition: List[str]
    total_damage: float
    damage_scenarios: List[Dict[str, Any]]
    character_stats: Dict[str, Any]
    enemy_stats: Dict[str, Any]
    calculation_metadata: Dict[str, Any]
    error: Optional[str] = None


# Missing models that are imported in main.py
class CharacterRequest(BaseModel):
    """Request model for character operations."""
    uid: int
    character_name: str


class CharacterListResponse(BaseModel):
    """Response model for character list."""
    characters: List[CharacterResponse]
    total_count: int


class TeamRequest(BaseModel):
    """Request model for team operations."""
    uid: int
    team_name: str
    characters: List[str] = Field(..., max_items=4)


class TeamResponse(BaseModel):
    """Response model for team data."""
    team_name: str
    characters: List[str]
    synergy_score: Optional[float] = None


class TeamListResponse(BaseModel):
    """Response model for team list."""
    teams: List[TeamResponse]
    total_count: int


class ArtifactRequest(BaseModel):
    """Request model for artifact operations."""
    uid: int
    character_name: str
    artifact_type: Optional[str] = None


class ArtifactResponse(BaseModel):
    """Response model for artifact data."""
    artifacts: List[ArtifactData]
    character_name: str


class ArtifactListResponse(BaseModel):
    """Response model for artifact list."""
    artifacts: List[ArtifactData]
    total_count: int


class WeaponRequest(BaseModel):
    """Request model for weapon operations."""
    uid: int
    character_name: str
    weapon_type: Optional[str] = None


class WeaponResponse(BaseModel):
    """Response model for weapon data."""
    weapon: WeaponData
    character_name: str


class WeaponListResponse(BaseModel):
    """Response model for weapon list."""
    weapons: List[WeaponData]
    total_count: int


class CharacterAnalysisRequest(BaseModel):
    """Request model for character analysis."""
    uid: int
    character_name: str
    analysis_type: str = "comprehensive"


class CharacterAnalysisResponse(BaseModel):
    """Response model for character analysis."""
    character_name: str
    analysis: str
    recommendations: List[str]
    stats_breakdown: Dict[str, Any]


class MaterialRequest(BaseModel):
    """Request model for material operations."""
    character_name: str
    material_type: Optional[str] = None


class MaterialResponse(BaseModel):
    """Response model for material data."""
    character_name: str
    materials: List[Dict[str, Any]]
    farming_locations: List[str]


class MaterialListResponse(BaseModel):
    """Response model for material list."""
    materials: List[Dict[str, Any]]
    total_count: int


class CharacterIconRequest(BaseModel):
    """Request model for character icon operations."""
    character_name: str
    force_download: bool = False


class ComprehensiveTeamAnalysisRequest(BaseModel):
    """Request model for comprehensive team analysis with detailed parameters."""
    uid: int
    main_character: str = Field(..., description="Main DPS character name")
    team_composition: List[str] = Field(..., min_items=2, max_items=4, description="Complete team including main character")
    analysis_depth: str = Field(default="detailed", description="Analysis depth: basic, detailed, comprehensive")
    include_rotations: bool = Field(default=True, description="Include skill rotation analysis")
    include_artifacts: bool = Field(default=True, description="Include artifact set recommendations")
    include_weapons: bool = Field(default=True, description="Include weapon recommendations")
    include_constellations: bool = Field(default=True, description="Include constellation impact analysis")
    enemy_level: int = Field(default=90, ge=1, le=100, description="Target enemy level")
    enemy_type: str = Field(default="standard", description="Enemy type: standard, boss, elite")
    content_focus: str = Field(default="spiral_abyss", description="Content focus: spiral_abyss, overworld, domains")
    investment_level: str = Field(default="high", description="Investment level: low, medium, high, whale")
    reaction_priority: List[str] = Field(default=[], description="Preferred elemental reactions (for analysis preference only - optimal reactions are auto-detected)")
    playstyle_preference: str = Field(default="balanced", description="Playstyle: aggressive, balanced, defensive")
    budget_constraints: bool = Field(default=False, description="Consider F2P/budget constraints")
    include_alternatives: bool = Field(default=True, description="Include alternative character suggestions")


class ComprehensiveTeamAnalysisResponse(BaseModel):
    """Response model for comprehensive team analysis."""
    main_character: str
    team_composition: List[str]
    team_synergy_score: float = Field(..., ge=0, le=100, description="Overall team synergy score (0-100)")
    elemental_coverage: Dict[str, bool] = Field(..., description="Elemental coverage analysis")
    role_distribution: Dict[str, str] = Field(..., description="Role of each team member")
    damage_analysis: Dict[str, Any] = Field(..., description="Detailed damage calculations")
    rotation_guide: Dict[str, Any] = Field(..., description="Optimal skill rotation")
    artifact_recommendations: Dict[str, List[str]] = Field(..., description="Artifact sets per character")
    weapon_recommendations: Dict[str, List[str]] = Field(..., description="Weapon options per character")
    constellation_impact: Dict[str, Dict[str, Any]] = Field(..., description="Constellation effects analysis")
    team_buffs: List[Dict[str, Any]] = Field(..., description="All team buffs and synergies")
    weaknesses: List[str] = Field(..., description="Team weaknesses and counters")
    strengths: List[str] = Field(..., description="Team strengths and advantages")
    investment_priority: List[Dict[str, Any]] = Field(..., description="Investment priority order")
    alternative_characters: Dict[str, List[str]] = Field(..., description="Alternative character options")
    content_performance: Dict[str, str] = Field(..., description="Performance in different content")
    budget_analysis: Optional[Dict[str, Any]] = Field(None, description="F2P/budget considerations")
    advanced_tips: List[str] = Field(..., description="Advanced gameplay tips")
    meta_relevance: Dict[str, Any] = Field(..., description="Current meta relevance")


class UserProfileResponse(BaseModel):
    """Response model for complete user profile data in raw format."""
    profile_data: Dict[str, Any]
    character_count: int


# New Simplified Damage Calculation Models
class SimpleDamageRequest(BaseModel):
    """Request model for simple damage calculation."""
    uid: int
    character_name: str = Field(..., description="Character name")
    enemy_level: int = Field(default=90, ge=1, le=100, description="Enemy level")
    enemy_resistances: Optional[Dict[str, float]] = Field(default=None, description="Enemy resistances")


class SimpleDamageResponse(BaseModel):
    """Response model for simplified damage calculation."""
    character_name: str
    element: str
    character_stats: Dict[str, Any]
    damage_breakdown: Dict[str, Any]
    enemy_info: Dict[str, Any]
    calculation_method: str = "simple_akasha_inspired"


class TeamDamageRequest(BaseModel):
    """Request model for team damage calculation."""
    uid: int
    main_dps: str = Field(..., description="Main DPS character name")
    team_composition: List[str] = Field(..., min_items=2, max_items=4, description="Team members including main DPS")
    enemy_level: int = Field(default=90, ge=1, le=100, description="Enemy level")
    enemy_resistances: Optional[Dict[str, float]] = Field(default=None, description="Enemy resistances")


class TeamDamageResponse(BaseModel):
    """Response model for team damage calculation."""
    main_dps: str
    team_composition: List[str]
    main_dps_damage: Dict[str, Any]
    team_buffs: Dict[str, Any]
    buffed_damage: Dict[str, Any]
    team_synergy_score: float
    elemental_coverage: Dict[str, Any]
    rotation_guide: List[str]
    calculation_method: str = "team_akasha_inspired" 