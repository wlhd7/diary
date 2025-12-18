CREATE TABLE IF NOT EXISTS `diary` (
    `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(150) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tags table and many-to-many association to diary entries
CREATE TABLE IF NOT EXISTS `tags` (
    `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `parent_id` BIGINT NULL,
    CONSTRAINT `fk_tags_parent` FOREIGN KEY (`parent_id`) REFERENCES `tags` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `diary_tags` (
    `diary_id` BIGINT NOT NULL,
    `tag_id` BIGINT NOT NULL,
    PRIMARY KEY (`diary_id`, `tag_id`),
    CONSTRAINT `fk_diary_tags_diary` FOREIGN KEY (`diary_id`) REFERENCES `diary` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_diary_tags_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Closure table mapping diary entries to tags including ancestor tags (if tag hierarchy used).
-- This lets queries filter entries by tag name while respecting tag parent relationships.
CREATE TABLE IF NOT EXISTS `diary_tags_closure` (
    `diary_id` BIGINT NOT NULL,
    `tag_id` BIGINT NOT NULL,
    PRIMARY KEY (`diary_id`, `tag_id`),
    CONSTRAINT `fk_diary_tags_closure_diary` FOREIGN KEY (`diary_id`) REFERENCES `diary` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_diary_tags_closure_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Persistent search history and counts
CREATE TABLE IF NOT EXISTS `search_history` (
    `term` VARCHAR(255) NOT NULL PRIMARY KEY,
    `count` BIGINT NOT NULL DEFAULT 0,
    `last_searched` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Convenience views
-- `diary_with_tags` presents diary rows with a comma-separated `tags` column
CREATE OR REPLACE VIEW `diary_with_tags` AS
SELECT d.id, d.title, d.content, d.created_at,
       GROUP_CONCAT(t.name SEPARATOR ',') AS tags
FROM diary d
LEFT JOIN diary_tags dt ON dt.diary_id = d.id
LEFT JOIN tags t ON t.id = dt.tag_id
GROUP BY d.id;

-- `tags_with_usage` presents tags with their direct usage counts and optional parent
CREATE OR REPLACE VIEW `tags_with_usage` AS
SELECT t.id, t.name, t.parent_id AS parent_id, COUNT(dt.diary_id) AS usage_count
FROM tags t
LEFT JOIN diary_tags dt ON dt.tag_id = t.id
GROUP BY t.id;