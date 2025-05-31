// MongoDB initialization script for Genshin LM API
print('Starting MongoDB initialization...');

// Switch to the genshin_lm database
db = db.getSiblingDB('genshin_lm');

// Create users collection with updated schema
db.createCollection('users', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['uid', 'created_at', 'updated_at', 'profile_data', 'characters'],
            properties: {
                uid: {
                    bsonType: 'int',
                    minimum: 100000000,
                    maximum: 999999999,
                    description: 'Unique user identifier from Genshin Impact'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'User creation timestamp'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                last_fetch: {
                    bsonType: 'date',
                    description: 'Last data fetch timestamp'
                },
                profile_data: {
                    bsonType: 'object',
                    description: 'User profile information from Enka Network',
                    properties: {
                        nickname: { bsonType: 'string' },
                        level: { bsonType: 'int' },
                        signature: { bsonType: 'string' },
                        worldLevel: { bsonType: 'int' },
                        nameCardId: { bsonType: 'int' },
                        finishAchievementNum: { bsonType: 'int' },
                        towerFloorIndex: { bsonType: 'int' },
                        towerLevelIndex: { bsonType: 'int' }
                    }
                },
                characters: {
                    bsonType: 'array',
                    description: 'Array of character data from Enka Network',
                    items: {
                        bsonType: 'object',
                        required: ['avatarId', 'name', 'level'],
                        properties: {
                            avatarId: {
                                bsonType: 'int',
                                description: 'Character avatar ID from Enka Network'
                            },
                            name: {
                                bsonType: 'string',
                                description: 'Character name'
                            },
                            level: {
                                bsonType: 'int',
                                minimum: 1,
                                maximum: 90
                            },
                            ascension: {
                                bsonType: 'int',
                                minimum: 0,
                                maximum: 6
                            },
                            friendship: {
                                bsonType: 'int',
                                minimum: 1,
                                maximum: 10
                            },
                            constellation: {
                                bsonType: 'int',
                                minimum: 0,
                                maximum: 6
                            },
                            weapon: {
                                bsonType: 'object',
                                description: 'Weapon data'
                            },
                            artifacts: {
                                bsonType: 'array',
                                description: 'Array of artifact data'
                            },
                            talents: {
                                bsonType: 'array',
                                description: 'Array of talent data'
                            },
                            stats: {
                                bsonType: 'object',
                                description: 'Character stats from fightPropMap'
                            },
                            updated_at: {
                                bsonType: 'date',
                                description: 'Character data update timestamp'
                            }
                        }
                    }
                },
                settings: {
                    bsonType: 'object',
                    description: 'User preferences and settings',
                    properties: {
                        notifications_enabled: { bsonType: 'bool' },
                        auto_update: { bsonType: 'bool' }
                    }
                }
            }
        }
    }
});

// Create cache collection for temporary data
db.createCollection('cache', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['key', 'value', 'expires_at', 'created_at'],
            properties: {
                key: {
                    bsonType: 'string',
                    description: 'Cache key identifier'
                },
                value: {
                    description: 'Cached data (any type)'
                },
                expires_at: {
                    bsonType: 'double',
                    description: 'Expiration timestamp'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Cache creation timestamp'
                }
            }
        }
    }
});

// Create indexes for better performance
print('Creating indexes...');

// User collection indexes
db.users.createIndex({ "uid": 1 }, { unique: true });
db.users.createIndex({ "created_at": 1 });
db.users.createIndex({ "updated_at": 1 });
db.users.createIndex({ "characters.avatarId": 1 });
db.users.createIndex({ "characters.name": 1 });
db.users.createIndex({ "characters.updated_at": 1 });

// Cache collection indexes
db.cache.createIndex({ "key": 1 }, { unique: true });
db.cache.createIndex({ "expires_at": 1 });

print('MongoDB initialization completed successfully!');
print('Collections created:');
print('- users (with character data embedded)');
print('- cache');
print('Indexes created for optimal performance.');
print('Ready for Enka Network API integration!'); 