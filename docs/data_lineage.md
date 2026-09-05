# SpillTrace — Data Lineage

This document describes how a displayed candidate vessel can be traced back to raw AIS data.

## Example candidate

- `spill_id`: `SPILL_DEMO_001`
- `mmsi`: example `366921080`
- `candidate_id`: backend-generated UUID (not shown in this file)

## Lineage chain

From UI to raw source:

1. **UI evidence panel**
   - Shows:
     - `total_score`
     - `score_components`
     - `ais_completeness`
     - `track_continuity`
     - `gap_stats`
     - `track_start_utc`, `track_end_utc`
   - All values are computed from persisted candidate rows and AIS quality metrics.

2. **Candidate persistence layer**
   - Table: `vessel_candidates`
   - Contains:
     - `spill_id`, `mmsi`
     - `total_score`, `score_components` (JSON)
     - `ais_completeness`, `track_continuity`
     - `evidence_json`
     - `scoring_version`
   - Each row is linked to a specific spill event.

3. **AIS track / position source**
   - Table: `ais_positions` (PostGIS)
   - Geometry: `geometry(Point, 4326)`
   - Key fields:
     - `mmsi`
     - `observed_at` (UTC)
     - `sog_knots`, `cog_degrees`, `heading_degrees`
   - Candidate scores are derived from aggregates over these positions (e.g., gap statistics, time bounds).

4. **Cleaned Parquet**
   - Path: `data/ais/cleaned/ais_sample_10000_cleaned.parquet`
   - Produced by: `data/etl/load_ais_data.py`
   - Contains one row per cleaned AIS observation.
   - Used as the input for loading `ais_positions`.

5. **Raw AIS source**
   - Path: `data/ais/ais_sample_10000.csv`
   - Original columns include:
     - `base_date_time`
     - `mmsi`
     - `lat`, `lon`
     - `sog`, `cog`, `heading`
   - This file is immutable and excluded from Git due to size.

6. **ETL quality report**
   - Path: `data/ais/reports/ais_sample_10000_quality_report.json`
   - Contains:
     - Input/cleaned row counts
     - Duplicate and invalid-record counts
     - Time range and geographic bounds
     - Gap statistics
   - Extended scenario-aware report:
     - `data/ais/reports/ais_sample_10000_quality_report_with_scenario.json`

7. **Frontend track payload**
   - Path: `data/ais/reports/vessel_tracks_frontend.geojson`
   - Format: GeoJSON `FeatureCollection`
   - Each `Feature`:
     - `geometry`: `LineString` with `[longitude, latitude]` coordinates
     - `properties`:
       - `mmsi`
       - `timestamps_utc`
       - `speed_knots`
       - `course_degrees`
       - `heading_degrees`
       - `ais_completeness`, `track_continuity`
       - `gap_count`, `max_gap_seconds`
       - `source_file`
       - `data_mode`
   - Used by the map to render vessel tracks.

## Compatibility and blocking behavior

- If SAR/AIS temporal, geographic, CRS, or environmental compatibility fails:
  - `compatibility_status` is set to `BLOCKED`.
  - No candidate rows are inserted for that spill.
  - The candidate endpoint returns HTTP 409 with explicit blocking reasons.
- The current development subset (`ais_sample_10000.csv`) is explicitly marked as incompatible with `SPILL_TEST3_001` and must not be used for attribution.

## Notes

- All timestamps are in UTC ISO-8601 format.
- MMSI is always treated as a string.
- GeoJSON coordinates are always `[longitude, latitude]` in EPSG:4326.
- No synthetic AIS records are created; gaps are reported, not interpolated.