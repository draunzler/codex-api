# Genshin Impact Personal Assistant API

A comprehensive FastAPI backend for Genshin Impact players featuring AI-powered assistance, automatic data updates, and intelligent recommendations.

## Features

- **🚀 Fully Automated Data Fetching**: No cookies required! Just set up Character Showcase in-game
- **User Profile Management**: Create and manage Genshin Impact player profiles
- **Real-time Character Builds**: Automatically fetch your latest character builds, artifacts, weapons
- **Mathematical Damage Calculations**: Precise damage analysis using real game formulas
- **AI-Powered Build Analysis**: Get optimal character builds using Gemini AI
- **Build Recommendations**: Find the best builds using Google CSE and AI analysis
- **Farming Route Optimization**: Get optimized farming routes for materials
- **Intelligent Assistant**: Ask questions and get contextual answers about the game

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Enka Network API**: Automated character data fetching (no cookies required!)
- **MongoDB Atlas**: Cloud database for storing user data and cache
- **Mathematical Engine**: Custom damage calculation system using real game formulas
- **Google Gemini**: AI model for damage calculations and recommendations
- **Google Custom Search**: For finding the latest build guides and strategies
- **APScheduler**: Background task scheduling for data management

## Setup Instructions

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.8+ with MongoDB (for local development)
- Google Cloud API key (for Gemini)
- Google Custom Search Engine ID and API key

### 🐋 Docker Deployment (Recommended)

#### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd genshin-lm-api
   ```

2. **Set up environment variables**
   ```bash
   cp docker-env-example .env
   # Edit .env file with your API keys
   ```

3. **Start the application**
   ```bash
   # Development environment (with hot reload)
   ./docker-run.sh dev
   
   # OR Production environment
   ./docker-run.sh prod
   
   # OR Production with Nginx reverse proxy
   ./docker-run.sh prod-nginx
   ```

#### Docker Commands

```bash
# Development environment
./docker-run.sh dev          # Start with hot reload and debugging tools

# Production environments
./docker-run.sh prod         # Start production environment
./docker-run.sh prod-nginx   # Start with Nginx reverse proxy

# Management
./docker-run.sh tools        # Start only database and management tools
./docker-run.sh stop         # Stop all containers
./docker-run.sh clean        # Remove all containers and volumes
./docker-run.sh logs         # View container logs
./docker-run.sh status       # Show container status
```

#### Available Services

**Development Environment:**
- API: http://localhost:8000/docs
- Redis Commander: http://localhost:8082
- MongoDB Atlas: https://cloud.mongodb.com

**Production Environment:**
- API: http://localhost:8000/docs
- With Nginx: http://localhost/docs

### 🐍 Local Python Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd genshin-lm-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   
   Create a `.env` file in the root directory:
   ```env
   # MongoDB Atlas Configuration
   MONGODB_URL=mongodb+srv://draunzler:<db_password>@test.nmxzjdn.mongodb.net/
   MONGODB_PASSWORD=your_actual_mongodb_password
   DATABASE_NAME=genshin_assistant

   # Google Gemini API
   GOOGLE_API_KEY=your_google_api_key_here

   # Google Custom Search Engine
   GOOGLE_CSE_ID=your_cse_id_here
   GOOGLE_CSE_API_KEY=your_cse_api_key_here

   # Redis Configuration (optional, for advanced caching)
   REDIS_URL=redis://localhost:6379

   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

4. **Set up MongoDB Atlas**
   
   Make sure you have:
   - Created a MongoDB Atlas account
   - Set up your cluster
   - Added your IP address to the whitelist
   - Set the correct password in your `.env` file

5. **Run the application**
   ```bash
   python start.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Key Endpoints

#### User Management
- `POST /users` - Create a new user profile
- `GET /users/{uid}` - Get user profile data
- `PUT /users/{uid}/refresh` - Manually refresh user data
- `POST /users/{uid}/refresh-force` - Force refresh bypassing cooldown
- `GET /users/{uid}/refresh-status` - Check refresh progress

#### Characters
- `GET /characters/setup-instructions` - **NEW!** Get hybrid setup instructions
- `GET /users/{uid}/characters/hybrid` - **NEW!** Get ALL characters (automated + manual)
- `POST /characters/add-manually` - **NEW!** Add characters not in showcase
- `GET /characters/template` - **NEW!** Get template for manual character input
- `GET /users/{uid}/characters` - Get showcased characters only (automated)
- `GET /users/{uid}/characters/{character_name}` - Get specific character details

#### Exploration
- `GET /users/{uid}/exploration` - Get exploration progress for all regions

#### AI Assistant
- `POST /ai/character-analysis` - **NEW!** Advanced character analysis using mathematical formulas
- `POST /ai/team-recommendation` - **NEW!** Specialized team recommendations for any character
- `POST /ai/team-synergy` - **NEW!** Analyze team composition synergy and effectiveness
- `POST /ai/question` - **ENHANCED!** Ask any Genshin question with intelligent character detection
- `POST /ai/build-recommendation` - Get build recommendations with damage analysis
- `POST /ai/farming-route` - Get farming route optimization

#### System
- `GET /system/scheduler` - Get scheduler status
- `GET /health` - Health check

#### Character Refresh Behavior

**NEW!** The refresh endpoints now support intelligent character merging:

- **`merge_characters=true` (default)**: Preserves existing characters and adds/updates new ones
  - ✅ Keeps characters not in current Enka showcase
  - ✅ Updates existing characters with fresh data
  - ✅ Adds new characters from showcase
  - ✅ Perfect for maintaining character history

- **`merge_characters=false`**: Completely replaces character list (legacy behavior)
  - ⚠️ Removes characters not in current showcase
  - ⚠️ May lose manually added characters
  - ✅ Provides clean slate if needed

**Usage Examples:**
```bash
# Merge new characters with existing ones (recommended)
PUT /users/123456789/refresh?merge_characters=true

# Replace all characters with current showcase only
PUT /users/123456789/refresh?merge_characters=false

# Force refresh with merge
POST /users/123456789/refresh-force?merge_characters=true
```

## Usage Examples

### 🚀 Quick Start

The API is now ready to use! Simply start the server and begin making requests:

```bash
# Start the API server
python start.py

# Or using Docker
./docker-run.sh dev
```

The API provides:
- Universal damage calculation for ANY character
- Hybrid character data approach (automated + manual)
- Mathematical build analysis and optimization
- AI-powered recommendations
- Complete character roster management

### Creating a User Profile

```bash
curl -X POST "http://localhost:8000/users" \
     -H "Content-Type: application/json" \
     -d '{"uid": 123456789}'
```

### 🚀 **HYBRID APPROACH: Complete Character Coverage (Recommended)**

**The Problem**: Enka Network only provides data for characters in your Character Showcase (max 8 characters).

**The Solution**: Hybrid approach combining automation + manual input for COMPLETE coverage!

**Step 1: Set up Character Showcase for your TOP 8 characters**
```bash
# Get hybrid setup instructions
curl -X GET "http://localhost:8000/characters/setup-instructions"
```

**Step 2: Create user profile (automatically fetches showcase data)**
```bash
curl -X POST "http://localhost:8000/users" \
     -H "Content-Type: application/json" \
     -d '{"uid": 123456789}'
```

**Step 3: Get ALL characters using hybrid approach**
```bash
# Get complete character roster (automated + manual)
curl -X GET "http://localhost:8000/users/123456789/characters/hybrid"
```

**Step 4: Add remaining characters manually**
```bash
# Get template for manual input
curl -X GET "http://localhost:8000/characters/template"

# Add characters not in showcase
curl -X POST "http://localhost:8000/characters/add-manually" \
     -H "Content-Type: application/json" \
     -d '{
       "uid": 123456789,
       "name": "Character Name",
       "element": "Pyro",
       "level": 90,
       "constellation": 2,
       "weapon": {...},
       "artifacts": [...],
       "talents": [...]
     }'
```

**Why Hybrid Approach?**
- ✅ **Automated data for your main 8 characters**
- ✅ **Manual input for unlimited additional characters**
- ✅ **Complete character coverage with minimal effort**
- ✅ **Real-time updates for showcased characters**
- ✅ **Same mathematical accuracy for all characters**
- ✅ **No privacy concerns or authentication needed**

### 🆕 Universal Character Analysis (Mathematical Formulas)

**Analyze ANY character using actual Genshin Impact damage formulas:**

```bash
curl -X POST "http://localhost:8000/ai/analyze-character" \
     -H "Content-Type: application/json" \
     -d '{
       "uid": 123456789,
       "character_name": "Any Character Name",
       "team_composition": ["Character", "Bennett", "Xingqiu", "Zhongli"],
       "enemy_type": "Boss"
     }'
```

**What you get:**
- **Universal damage calculations** using real game formulas for ANY character
- **Build efficiency analysis** with specific ratings (Crit Value, Attack Rating, etc.)
- **Prioritized action plan** for optimization
- **AI-powered recommendations** based on mathematical analysis
- **Works for ALL characters** - no character-specific code needed

**Example Response:**
```json
{
  "character": "Any Character",
  "summary": {
    "overall_rating": "67.3/100",
    "build_efficiency": "Needs Improvement",
    "crit_value": "142.5",
    "total_attack": "1847",
    "primary_damage_source": "elemental_burst"
  },
  "action_plan": [
    {
      "step": 1,
      "priority": "HIGH",
      "category": "Critical Stats",
      "action": "Increase Crit Rate. Current ratio is 1:3.2, aim for 1:2",
      "expected_improvement": "15-25% damage increase"
    }
  ]
}
```

### 🆕 Enhanced Team Composition Assistant

**Perfect for questions like "among the characters that I have, give me a good team for Chasca":**

```bash
# Get personalized team recommendations
curl -X POST "http://localhost:8000/ai/team-recommendation" \
     -H "Content-Type: application/json" \
     -d '{
       "character_name": "Chasca",
       "uid": 123456789,
       "content_type": "abyss"
     }'

# Ask natural language questions
curl -X POST "http://localhost:8000/ai/question" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "among the characters that I have, give me a good team for chasca",
       "uid": 123456789,
       "include_context": true
     }'

# Analyze existing team synergy
curl -X POST "http://localhost:8000/ai/team-synergy" \
     -H "Content-Type: application/json" \
     -d '{
       "team_composition": ["Chasca", "Bennett", "Xiangling", "Kazuha"],
       "uid": 123456789
     }'
```

**What you get:**
- **Personalized team recommendations** using YOUR available characters
- **Multiple team options** (meta, budget, fun alternatives)
- **Detailed role explanations** and synergy analysis
- **Rotation guides** and gameplay tips
- **Investment priorities** and optimization suggestions
- **Content-specific recommendations** (Abyss, domains, bosses)

**Enhanced AI Understanding:**
- ✅ Recognizes ALL character names (Mondstadt to Natlan)
- ✅ Understands team composition terminology
- ✅ Analyzes your character roster automatically
- ✅ Provides practical, actionable advice
- ✅ No more "I can only help with Genshin Impact questions" errors!

### Getting Damage Calculation

```bash
curl -X POST "http://localhost:8000/ai/damage-calculation" \
     -H "Content-Type: application/json" \
     -d '{
       "uid": 123456789,
       "character_name": "Hu Tao",
       "team_composition": ["Hu Tao", "Xingqiu", "Zhongli", "Albedo"],
       "enemy_type": "Boss"
     }'
```

### Getting Build Recommendations

```bash
curl -X POST "http://localhost:8000/ai/build-recommendation" \
     -H "Content-Type: application/json" \
     -d '{
       "character_name": "Ganyu",
       "uid": 123456789,
       "include_current_build": true
     }'
```

## 🧮 Universal Mathematical Damage System

The character analysis uses **actual Genshin Impact damage formulas** to provide precise calculations and recommendations for ANY character.

### Damage Formula

```
Damage = Talent% × ATK × (1 + DMG%) × Crit × (1 - RES) × DEF × Reaction × Other
```

**Components:**
- **Talent%**: Character talent multiplier (works with any character's abilities)
- **ATK**: Total Attack = (Base ATK + Weapon ATK) × (1 + ATK%) + Flat ATK
- **DMG%**: Elemental/Physical damage bonus
- **Crit**: 1 + (Crit DMG% / 100) when crit hits
- **RES**: Enemy resistance multiplier
- **DEF**: Defense multiplier based on levels
- **Reaction**: Elemental reaction multiplier (Vaporize, Melt, etc.)
- **Other**: Additional multipliers (buffs, weapon passives, etc.)

### Universal Optimization Metrics

- **Crit Value (CV)**: Crit Rate × 2 + Crit DMG
- **Optimal Crit Ratio**: 1:2 (Crit Rate : Crit DMG)
- **Build Rating**: Weighted score based on CV, ATK, and stat efficiency
- **Universal Benchmarks**: Works for any character regardless of element or weapon type

### Key Features

- **Universal Calculator**: One system works for ALL characters
- **No Character-Specific Code**: Automatically adapts to any character
- **Extensible**: Easy to add new mechanics without character-specific implementations
- **Mathematical Accuracy**: Uses real game formulas for precise calculations

## Architecture

### Core Components

1. **Database Layer** (`database.py`)
   - MongoDB connection management
   - User profile and character data models
   - Caching system

2. **Genshin Client** (`genshin_client.py`)
   - Wrapper around genshin.py library
   - Data fetching and caching
   - Character and exploration data management

3. **AI Assistant** (`ai_assistant.py`)
   - Gemini AI integration for damage calculations
   - Google CSE for build recommendations
   - Intelligent question answering

4. **Scheduler** (`scheduler.py`)
   - Automatic data updates every 4 hours
   - Background task management
   - Cache cleanup

5. **API Layer** (`main.py`)
   - FastAPI application
   - Request/response handling
   - Error management

### Data Flow

1. User creates profile → Fetch initial data from Genshin API
2. Scheduler runs every 4 hours → Updates all user data automatically
3. AI requests → Use cached character data + external APIs for recommendations
4. All data cached in MongoDB for performance

## Configuration

### Update Interval

The default update interval is 4 hours. You can modify this in the `.env` file:

```env
UPDATE_INTERVAL=4  # Hours between automatic updates
```

### Caching

The application uses MongoDB for caching with configurable TTL:
- User data: 1 hour
- Exploration data: 2 hours
- AI responses: 24 hours (damage calc) / 7 days (build recommendations)

## Error Handling

The API includes comprehensive error handling:
- Input validation using Pydantic models
- Graceful handling of Genshin API errors
- Detailed error responses with timestamps
- Automatic retry logic for failed updates

## Performance Considerations

- **Caching**: Aggressive caching to minimize API calls
- **Batch Processing**: User updates processed in batches
- **Rate Limiting**: Built-in delays to respect API limits
- **Background Tasks**: Non-blocking operations for better UX

## Security Notes

- Configure CORS appropriately for production
- Use environment variables for all sensitive data
- Consider implementing authentication for production use
- Monitor API usage to prevent abuse

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the error logs
3. Create an issue in the repository

## Roadmap

- [ ] Real-time notifications for events
- [ ] Advanced team composition analysis
- [ ] Integration with more Genshin Impact tools
- [ ] Mobile app support
- [ ] Multi-language support 

**🆕 Enhanced AI Features:**
- **Intelligent Question Detection**: Recognizes ALL character names and Genshin terminology
- **Team Composition Expert**: Analyzes your roster for optimal team building
- **Personalized Recommendations**: Uses your available characters for practical advice
- **Mathematical Accuracy**: Powered by real damage calculation formulas 