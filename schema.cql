-- Create keyspace if not exists
CREATE KEYSPACE IF NOT EXISTS tochly
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
AND durable_writes = true;

USE tochly;

-- Chat rooms
CREATE TABLE IF NOT EXISTS chat_rooms (
    team_id text,
    room_id text,
    created_at timestamp,
    user1_id text,
    user2_id text,
    PRIMARY KEY (team_id, room_id)
) WITH CLUSTERING ORDER BY (room_id ASC)
  AND bloom_filter_fp_chance = 0.01
  AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
  AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
  AND compression = {'class': 'org.apache.cassandra.io.compress.LZ4Compressor'};

-- Direct messages
CREATE TABLE IF NOT EXISTS direct_messages (
    room_id text,
    message_id timeuuid,
    attachment_url text,
    content text,
    file_name text,
    file_size int,
    message_type text,
    mime_type text,
    receiver_id text,
    sender_id text,
    timestamp timestamp,
    PRIMARY KEY (room_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC)
  AND bloom_filter_fp_chance = 0.01
  AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
  AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
  AND compression = {'class': 'org.apache.cassandra.io.compress.LZ4Compressor'};

-- Group members
CREATE TABLE IF NOT EXISTS group_members (
    group_id uuid,
    user_id text,
    group_name text,
    joined_at timestamp,
    PRIMARY KEY (group_id, user_id)
) WITH CLUSTERING ORDER BY (user_id ASC)
  AND bloom_filter_fp_chance = 0.01
  AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
  AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
  AND compression = {'class': 'org.apache.cassandra.io.compress.LZ4Compressor'};

-- Group messages
CREATE TABLE IF NOT EXISTS group_messages (
    group_id uuid,
    message_id timeuuid,
    content text,
    created_at timestamp,
    sender_id text,
    PRIMARY KEY (group_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC)
  AND bloom_filter_fp_chance = 0.01
  AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
  AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
  AND compression = {'class': 'org.apache.cassandra.io.compress.LZ4Compressor'};

-- User chats by user
CREATE TABLE IF NOT EXISTS user_chats_by_user (
    team_id text,
    user_id text,
    room_id text,
    created_at timestamp,
    last_message text,
    last_message_timestamp timestamp,
    last_message_type text,
    last_read timestamp,
    participant_id text,
    PRIMARY KEY ((team_id, user_id), room_id)
) WITH CLUSTERING ORDER BY (room_id DESC)
  AND bloom_filter_fp_chance = 0.01
  AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
  AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy'}
  AND compression = {'class': 'org.apache.cassandra.io.compress.LZ4Compressor'};

-- Prekeys by user device
CREATE TABLE IF NOT EXISTS prekeys_by_user_device (
    user_id text,
    device_id uuid,
    identity_key text,
    last_updated timestamp,
    registration_id int,
    signature text,
    signed_at timestamp,
    signed_prekey text,
    signed_prekey_id int,
    PRIMARY KEY (user_id, device_id)
) WITH CLUSTERING ORDER BY (device_id ASC);

-- One-time prekeys by user device
CREATE TABLE IF NOT EXISTS one_time_prekeys_by_user_device (
    user_id text,
    device_id uuid,
    prekey_id int,
    prekey text,
    used boolean,
    uploaded_at timestamp,
    PRIMARY KEY ((user_id, device_id), prekey_id)
) WITH CLUSTERING ORDER BY (prekey_id ASC);

-- Index for one-time prekeys
CREATE INDEX IF NOT EXISTS idx_used_prekey
ON one_time_prekeys_by_user_device (used);
