-- Independent, sanitized fixture of the deployed v3 layout (including INTEGER
-- inode affinity). Keep this frozen when the production schema evolves.
PRAGMA user_version = 3;
CREATE TABLE media (
    id INTEGER PRIMARY KEY, path TEXT UNIQUE,
    added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_dir BOOLEAN DEFAULT 0,
    byte_size INTEGER DEFAULT 0, favorite INTEGER NOT NULL DEFAULT 0,
    weight REAL, artist TEXT, type TEXT NOT NULL,
    inode INTEGER, mtime INTEGER, device TEXT
);
CREATE TABLE presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT, group_id TEXT NOT NULL,
    name TEXT NOT NULL, media_id INTEGER, zoom REAL NOT NULL,
    pan_x INTEGER NOT NULL, pan_y INTEGER NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0, hotkey TEXT,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
    UNIQUE (media_id, name), CHECK (is_default IN (0,1))
);
CREATE TABLE tags (
    media_id INTEGER, tag TEXT,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE,
    UNIQUE (media_id, tag)
);
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, media_id INTEGER NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, text TEXT NOT NULL, seq INTEGER,
    FOREIGN KEY (media_id) REFERENCES media(id) ON DELETE CASCADE
);
CREATE TABLE bookmarks (
    path TEXT NOT NULL, time_ms INTEGER NOT NULL, PRIMARY KEY (path, time_ms)
);
CREATE TABLE variants (
    base_id INTEGER NOT NULL, variant_id INTEGER NOT NULL UNIQUE,
    rank INTEGER DEFAULT 0,
    FOREIGN KEY (base_id) REFERENCES media(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES media(id) ON DELETE CASCADE
);
CREATE INDEX idx_presets_group ON presets(group_id);
CREATE INDEX idx_tags_tag ON tags(tag);
CREATE INDEX idx_comments_media ON comments(media_id);
CREATE INDEX idx_variants_base ON variants(base_id);
CREATE UNIQUE INDEX idx_variants_rank ON variants(base_id, rank);

INSERT INTO media VALUES
    (10, 'C:\Collection\portrait.png', '2024-01-02 03:04:05', 0, 456, 1, 0.75, 'Artist', 'image', 123, 1704164645, NULL),
    (20, 'C:\Collection\portrait_v1.png', 1704164646, 0, 789, 0, NULL, NULL, 'image', 'i:340282366920938463463374607431768211455', 1704164646, 'd:99'),
    (30, 'C:\Collection', NULL, 1, 0, 0, NULL, NULL, 'dir', NULL, NULL, NULL);
INSERT INTO comments(id, media_id, created, text, seq) VALUES
    (5, 10, '2024-02-03 01:02:03', 'First line
Second line — café 日本語', 8),
    (9, 10, '2024-01-01 00:00:00', '  preserve whitespace  ', 2),
    (12, 20, NULL, '', NULL),
    (80, 10, '2024-01-01 00:00:00', 'deleted high-water mark', 99);
DELETE FROM comments WHERE id=80;
INSERT INTO presets VALUES
    (7, 'shared-group', 'Portrait crop', 10, 1.875, -123, 456, 1, 'Ctrl+2'),
    (8, 'shared-group', 'Portrait crop', 20, 1.875, -123, 456, 1, 'Ctrl+2'),
    (11, 'legacy-folder-group', 'Folder default', NULL, 0.625, 15, -8, 1, NULL),
    (14, 'alternate', 'Detail', 10, 3.125, 5, -6, 0, NULL),
    (90, 'deleted', 'Deleted preset', 10, 1.0, 0, 0, 0, NULL);
DELETE FROM presets WHERE id=90;
INSERT INTO tags VALUES (10, 'portrait'), (20, 'reference');
INSERT INTO variants VALUES (10, 20, 1);
INSERT INTO bookmarks VALUES ('C:\Collection\portrait.png', 1250);

-- Unknown extension data must also survive baseline adoption.
CREATE TABLE extension_notes (id INTEGER PRIMARY KEY, payload TEXT);
INSERT INTO extension_notes VALUES (1, 'retain extension data');
CREATE TRIGGER keep_extension_notes BEFORE DELETE ON extension_notes
BEGIN SELECT RAISE(ABORT, 'extension notes are protected'); END;
