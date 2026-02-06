-- ============================================================================
-- TravelAssist - Attraction Table Creation Script
-- ============================================================================
-- This script creates the travel_assist table for storing attraction data
-- with vector search and geospatial capabilities.
--
-- Schema aligns with: src/data/data_loader.py (load_csv)
--
-- Columns:
--   - id: Primary key, auto-increment
--   - attraction_name: Name of the attraction (VARCHAR 1024)
--   - address_text: Full address text (LONGTEXT)
--   - address: Geographic point, WGS84 (POINT/GEOMETRY)
--   - intro: Introduction/description (LONGTEXT)
--   - intro_vec: Embedding of intro for semantic search (VECTOR 1024)
--   - img_url: URL to attraction image (VARCHAR 1024)
--   - score: Attraction score (INT, e.g. 0-100)
--   - season: Bit flags for recommended seasons (1=spring, 2=summer, 4=autumn, 8=winter)
--   - ticket: Ticket information (JSON, nullable)
--
-- Indexes:
--   - address_idx: Spatial index on address for geo queries
--   - intro_vidx: Vector index (HNSW, L2, vsag) for similarity search
-- ============================================================================


CREATE TABLE IF NOT EXISTS `travel_assist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `attraction_name` varchar(1024) NOT NULL,
  `address_text` longtext NOT NULL,
  `address` point NOT NULL /*!80003 SRID 4326 */,
  `intro` longtext NOT NULL,
  `intro_vec` VECTOR(384) NOT NULL,
  `img_url` varchar(1024) NOT NULL,
  `score` int(11) NOT NULL,
  `season` int(11) NOT NULL,
  `ticket` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  VECTOR KEY `intro_vidx` (`intro_vec`) WITH (DISTANCE=L2, TYPE=HNSW, LIB=VSAG, M=16, EF_CONSTRUCTION=200, EF_SEARCH=64) BLOCK_SIZE 16384,
  SPATIAL KEY `address_idx` (`address`) BLOCK_SIZE 16384 LOCAL
) COMMENT='Travel attractions with vector and geo search';
