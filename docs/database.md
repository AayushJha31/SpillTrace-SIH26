# SpillTrace Database Documentation

## Purpose

SpillTrace uses PostgreSQL with PostGIS to store oil-spill investigation
metadata, SAR image metadata, cleaned AIS vessel positions, and later
vessel-candidate ranking results.

AIS outputs support an evidence-based vessel-candidate investigation workflow.
They are not proof of legal responsibility or confirmation that a vessel caused
a spill.

## Local Database Setup

Database engine:

- PostgreSQL
- PostGIS
- Docker Compose service name: `db`
- Docker container name: `spilltrace-db`
- Database name: `spilltrace`
- Database user: `spilltrace`
- Local host port: `5432`

Start the local database:

```bash
docker compose up -d db
```

Check the local database container:

```bash
docker compose ps
```

Connect through PostgreSQL CLI:

```bash
docker compose exec db psql -U spilltrace -d spilltrace
```

## PostGIS

PostGIS is enabled using:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

PostGIS provides geometry storage, spatial indexing, distance operations,
GeoJSON conversion, and geographic filtering.

## Coordinate Reference System

AIS positions use:

- Geometry type: `geometry(Point, 4326)`
- CRS: EPSG:4326 / WGS 84
- X coordinate: longitude
- Y coordinate: latitude

Correct PostGIS point construction:

```sql
ST_SetSRID(
    ST_MakePoint(longitude, latitude),
    4326
)
```

Correct GeoJSON coordinate order:

```json
[longitude, latitude]
```

Do not reverse coordinate order to `[latitude, longitude]`.

## Schema

### spill_events

Stores the primary metadata for one spill investigation.

Important fields:

- `id`
- `detected_at`
- `region_name`
- `status`
- `source`
- `model_version`
- `confidence`
- `created_at`
- `updated_at`

The `status` value is limited to:

- `detected`
- `processing`
- `completed`
- `failed`
- `reviewed`

### spill_images

Stores metadata and storage references for real SAR image files.

Important fields:

- `spill_id`
- `storage_uri`
- `original_filename`
- `acquisition_time`
- `crs_epsg`
- `width`
- `height`
- `band_count`
- `bounds`
- `metadata`

`bounds` is stored as:

```sql
geometry(Polygon, 4326)
```

The actual SAR image binary is not stored inside PostgreSQL. The database
stores a real file URI/path and metadata.

### ais_positions

Stores cleaned, validated AIS vessel observations.

Important fields:

- `mmsi`
- `observed_at`
- `latitude`
- `longitude`
- `position`
- `sog_knots`
- `cog_degrees`
- `heading_degrees`
- `vessel_type`
- `source_file`
- `source_row_number`
- `quality_flags`
- `ingested_at`

The `position` field is stored as:

```sql
geometry(Point, 4326)
```

Constraints enforce:

- MMSI between `100000000` and `999999999`
- Latitude between `-90` and `90`
- Longitude between `-180` and `180`
- Non-negative speed over ground
- Course and heading between `0` and `< 360`
- Unique AIS observation by MMSI, timestamp, latitude, and longitude

### vessel_candidates

Stores vessel candidates associated with one spill event.

Important fields:

- `spill_id`
- `mmsi`
- `rank`
- `score`
- `score_components`
- `ais_completeness`
- `track_continuity`
- `uncertainty`
- `evidence`
- `scoring_version`

`score_components`, `uncertainty`, and `evidence` use `JSONB` so that
the exact scoring and drift contracts can be finalized with the backend and
ML/drift teams.

## Indexes

Current indexes include:

- `idx_spill_events_detected_at`
- `idx_spill_events_status`
- `idx_spill_images_spill_id`
- `idx_spill_images_acquisition_time`
- `idx_spill_images_bounds_gist`
- `idx_ais_positions_position_gist`
- `idx_ais_positions_mmsi_observed_at`
- `idx_ais_positions_observed_at`
- `idx_ais_positions_quality_flags_gin`
- `idx_vessel_candidates_spill_rank`
- `idx_vessel_candidates_mmsi`

The spatial GIST index supports geometry-based spatial queries and future map
operations. The B-tree time index supports time-window filtering. The
MMSI/time index supports vessel track ordering and lookup.

## AIS Source Files

The AIS directory contains two related files:

```text
data/ais/ais-2025-01-08.csv.zst
data/ais/ais_sample_10000.csv
```

`ais-2025-01-08.csv.zst` is the original compressed AIS source file. It must
remain immutable and is the source of truth for full-scale ingestion.

`ais_sample_10000.csv` is a 10,000-row development subset copied from the
original source file. It is used for local ETL development, database-load
testing, query testing, and debugging.

The development subset must not be described as complete AIS coverage.

## AIS ETL Pipeline

ETL scripts:

```text
data/etl/profile_ais_data.py
data/etl/load_ais_data.py
data/etl/load_ais_to_postgis.py
```

Pipeline flow:

1. Read `ais_sample_10000.csv`.
2. Map source fields to SpillTrace canonical fields.
3. Convert `base_date_time` to UTC `observed_at`.
4. Validate MMSI.
5. Validate latitude and longitude.
6. Preserve optional navigation fields when available.
7. Remove duplicate MMSI/timestamp/longitude/latitude observations.
8. Sort cleaned data by MMSI and timestamp.
9. Write cleaned data to Parquet.
10. Create a JSON data-quality report.
11. Load cleaned records into PostGIS.
12. Generate `geometry(Point, 4326)` from longitude and latitude.

Output artifacts:

```text
data/ais/cleaned/ais_sample_10000_cleaned.parquet
data/ais/reports/ais_sample_10000_quality_report.json
```

## Day 2 Data-Quality Results

Development input:

```text
data/ais/ais_sample_10000.csv
```

Measured results:

| Metric | Result |
|---|---:|
| Input records | 10,000 |
| Valid records before deduplication | 10,000 |
| Invalid timestamps | 0 |
| Invalid MMSIs | 0 |
| Invalid latitude values | 0 |
| Invalid longitude values | 0 |
| Duplicate observations removed | 23 |
| Cleaned AIS records | 9,977 |
| Unique MMSIs | 6,890 |
| First UTC timestamp | 2025-01-08 00:00:00+00 |
| Last UTC timestamp | 2025-01-08 18:49:10+00 |
| Median inter-message gap | 71 seconds |
| 95th-percentile inter-message gap | 101 seconds |
| Maximum observed gap | 67,750 seconds |

The maximum gap should not be interpreted as complete track continuity because
the development dataset contains only a 10,000-row subset of the original AIS
source file. No AIS interpolation was performed.

## PostGIS Load Verification

The cleaned Parquet file loaded into `ais_positions` with:

| Verification | Result |
|---|---:|
| Rows loaded | 9,977 |
| Unique MMSIs loaded | 6,890 |
| Invalid geometry count | 0 |
| Longitude/latitude geometry mismatches | 0 |

## Vessel Query

Reusable SQL query file:

```text
data/queries/vessels_within_50km.sql
```

The query finds vessel MMSIs observed within 50 km of a supplied point during
a UTC time window.

The distance condition is:

```sql
ST_DWithin(
    position::geography,
    query_point::geography,
    50000
)
```

`50000` is in meters and represents 50 km.

Parameters required by the backend:

```text
:longitude
:latitude
:time_start_utc
:time_end_utc
```

The backend must use safely bound SQL parameters. Do not construct SQL by
string concatenation.

## Day 2 Query Baseline

A test used a real AIS point from the loaded development subset:

```text
Longitude: -90.01582
Latitude: 29.86105
Time window: 2025-01-08 00:00:00+00 to 2025-01-08 00:10:00+00
Radius: 50 km
```

Measured query result:

| Metric | Result |
|---|---:|
| Vessel MMSIs returned | 350 |
| Matching AIS positions | 635 |
| Execution time | 53.849 ms |
| Time/index scan used | `idx_ais_positions_mmsi_observed_at` |

The query used the B-tree index for the timestamp filter. The PostGIS geometry
GIST index was not selected for this test because the query converts geometry
to geography for geodesic distance calculation.

Do not add additional indexes until testing the full original AIS file and
reviewing actual `EXPLAIN (ANALYZE, BUFFERS)` results.

## Deferred Work

The following work is outside Day 1–2 scope:

- Full original `.csv.zst` ingestion.
- Drift corridor ingestion.
- Backward/forward drift integration.
- AIS interpolation for only approved short gaps.
- Candidate scoring implementation.
- Candidate ranking API endpoint.
- Full FastAPI database integration.
- Production-scale table partitioning.
- Automated satellite-data ingestion.


### Automated ETL tests

AIS ETL unit tests were added in:

```text
tests/test_ais_etl.py
```

Run command:

```cmd
python -m pytest tests\test_ais_etl.py -v
```

Result:

```text
5 passed
```

The tests use temporary test-only fixtures and do not modify the real AIS source file, cleaned Parquet output, PostGIS database, dashboard data, or scenario evidence.

Validated behaviors:

- Required-field validation rejects invalid timestamps, MMSIs, latitudes, and longitudes.
- Duplicate AIS observations are removed using `(mmsi, observed_at, latitude, longitude)`.
- Row conservation is verified:

  ```text
  input rows = rejected required-field rows + duplicate rows removed + cleaned rows
  ```

- MMSI is preserved as an integer-compatible identifier in the cleaned output.
- `observed_at` is timezone-aware and uses UTC.
- Cleaned AIS output is sorted by `mmsi`, then `observed_at`.
- Per-vessel time-gap statistics are calculated.
- Source-file and source-row lineage fields are preserved.
- GeoJSON point coordinate convention is `[longitude, latitude]`.
- Missing required columns produce a controlled `ValueError`.

### Real cleaned Parquet validation

Validation script:

```text
data/etl/validate_cleaned_ais_parquet.py
```

Run command:

```cmd
python data\etl\validate_cleaned_ais_parquet.py
```

Validation artifact:

```text
data/ais/reports/ais_sample_10000_parquet_validation.json
```

Verified real-data results:

| Check | Result |
|---|---:|
| Input AIS rows | 10,000 |
| Cleaned Parquet rows | 9,977 |
| Duplicate observations removed during ETL | 23 |
| Remaining duplicate observation groups in Parquet | 0 |
| Unique MMSIs | 6,890 |
| First timestamp UTC | 2025-01-08 00:00:00+00:00 |
| Last timestamp UTC | 2025-01-08 18:49:10+00:00 |
| Geographic longitude bounds | -159.35849 to -63.85972 |
| Geographic latitude bounds | 14.54614 to 49.65558 |
| Null `observed_at` values | 0 |
| Null MMSI values | 0 |
| Null latitude values | 0 |
| Null longitude values | 0 |
| Invalid MMSIs | 0 |
| Invalid latitudes | 0 |
| Invalid longitudes | 0 |
| MMSI/time ordering violations | 0 |

Parquet schema validation confirms:

```text
mmsi        BIGINT
observed_at TIMESTAMP WITH TIME ZONE
latitude    DOUBLE
longitude   DOUBLE
```

The DuckDB validation session explicitly uses UTC:

```python
connection.execute("SET TimeZone='UTC'")
```

This prevents a developer machine’s local timezone from changing timestamps written into the validation report.

### Scenario compatibility limitation

The local AIS development dataset covers only:

```text
2025-01-08T00:00:00Z to 2025-01-08T18:49:10Z
```

The supplied `SPILL_TEST3_001` drift-origin window is:

```text
2026-09-01T10:00:00Z to 2026-09-01T14:00:00Z
```

Therefore, `data/ais/ais_sample_10000.csv` and its cleaned Parquet output are incompatible with `SPILL_TEST3_001` for real vessel attribution.

The local AIS sample remains valid for ETL development, tests, PostGIS loading, and spatial-query development only. It must not be used as scenario evidence, and timestamps or vessel positions must not be modified to force compatibility.

For `SPILL_TEST3_001`, vessel candidate ranking remains blocked until a real AIS source with verified temporal and geographic coverage is available. The supplied drift run is also labelled:

```text
Analyst Parameter-Driven Scenario Simulation
```

because wind/current source metadata is unavailable. It must not be described as independently data-backed environmental drift evidence.



## Scenario compatibility checkpoint and schema extension

### Scenario manifest

Scenario manifest:

```text
data/manifests/scenario_manifest.json
```

Compatibility validator:

```text
data/etl/validate_scenario_compatibility.py
```

Generated compatibility report:

```text
data/manifests/scenario_compatibility_report.json
```

Run command:

```cmd
python data\etl\validate_scenario_compatibility.py
```

Computed result for `SPILL_TEST3_001`:

| Check | Result |
|---|---|
| Compatibility state | `insufficient_data` |
| Candidate ranking enabled | `false` |
| Expected candidate API status | `409` |
| AIS temporal overlap | `false` |
| SAR source/output CRS | `EPSG:4326` |
| GeoJSON coordinate order | `[longitude, latitude]` |
| Drift mode | `Analyst Parameter-Driven Scenario Simulation` |

Blocking reasons:

- `AIS_TEMPORAL_COVERAGE_MISMATCH`: Available development AIS data is dated 2025-01-08, while the required drift origin-time window is 2026-09-01T10:00:00Z to 2026-09-01T14:00:00Z.
- `ENVIRONMENTAL_FORCING_NOT_DATA_BACKED`: Wind/current values are analyst-parameter-driven and independently verifiable forcing-source metadata is unavailable.
- `PROTOTYPE_GEOREFERENCING_LIMITATION`: Supplied prototype geometry uses injected coordinates and must not be described as independently ground-truth-verified.

Safe behavior:

```text
Vessel attribution is unavailable for this scenario.
No vessel candidates have been generated.
```

The local 2025 AIS sample can be used for ETL, PostGIS loading, query development, and test validation only. It must not be used as evidence for `SPILL_TEST3_001`.

### Day 4 database migration

Migration file:

```text
data/migrations/002_day4_tracking_quality_audit.sql
```

Apply command:

```cmd
docker exec -i spilltrace-db psql -U spilltrace -d spilltrace < data\migrations\002_day4_tracking_quality_audit.sql
```

The migration adds the Day 4 tables without changing existing AIS rows:

| Table | Purpose |
|---|---|
| `vessel_tracks` | Stores real selected AIS track geometry as `geometry(LineString, 4326)`, time bounds, continuity/completeness fields, gap statistics, and source provenance |
| `data_quality_reports` | Stores quality-report references and calculated metrics for ETL, Parquet validation, scenario compatibility, SAR metadata, drift metadata, and future candidate ranking |
| `audit_events` | Stores traceable actual ETL, compatibility, filtering, and blocked-status events |

New indexes:

```text
idx_vessel_tracks_geometry_gist
idx_vessel_tracks_spill_time
idx_vessel_tracks_mmsi
idx_vessel_tracks_gap_statistics_gin
idx_data_quality_reports_spill_type
idx_data_quality_reports_status
idx_data_quality_reports_metrics_gin
idx_audit_events_spill_created_at
idx_audit_events_event_type
idx_audit_events_details_gin
```

Database verification after applying the migration:

- Required project tables exist: `spill_events`, `spill_images`, `ais_positions`, `vessel_tracks`, `vessel_candidates`, `data_quality_reports`, and `audit_events`.
- Existing real AIS development records remain unchanged: `ais_positions = 9,977`.
- No scenario records, vessel tracks, candidates, quality reports, or audit events were inserted during the schema migration.


## Selective AIS loading and vessel-track query benchmarks

### Selective Parquet-to-PostGIS loader

Updated loader:

```text
data/etl/load_ais_to_postgis.py
```

The loader now accepts explicit real-data spatial-temporal filters:

```text
--start-utc
--end-utc
--min-longitude
--max-longitude
--min-latitude
--max-latitude
```

It reads the cleaned Parquet source, selects only rows that fall within the requested UTC time range and EPSG:4326 bounding box, preserves source lineage, creates `geometry(Point, 4326)` with longitude first, and uses the existing unique constraint to avoid duplicate AIS observations.

Development validation command:

```cmd
python data\etl\load_ais_to_postgis.py --start-utc 2025-01-08T00:00:00Z --end-utc 2025-01-08T00:10:00Z --min-longitude -90.10000 --max-longitude -89.90000 --min-latitude 29.70000 --max-latitude 30.00000
```

Measured real-data result:

| Metric | Value |
|---|---:|
| Selected AIS positions | 228 |
| Selected unique MMSIs | 127 |
| Database rows before load | 9,977 |
| Database rows after load | 9,977 |
| Newly inserted rows | 0 |

The zero inserted rows are expected because all 9,977 observations from the local development Parquet had already been loaded. The loader remains safe and idempotent through the unique constraint on `(mmsi, observed_at, latitude, longitude)`.

This development subset is not evidence for `SPILL_TEST3_001`, which has an origin-time window in 2026.

### Vessel-track spatial-temporal query

Track query:

```text
data/queries/vessel_tracks_within_bounds.sql
```

The query:

- Filters AIS observations by UTC time range and EPSG:4326 bounds.
- Groups real positions by MMSI.
- Creates ordered `LineString` geometries using `ST_MakeLine(position ORDER BY observed_at)`.
- Returns tracks only where at least two real observations are available.
- Includes position count, time bounds, gap count, maximum gap, speed/course/heading, timestamps, and source-lineage values.
- Does not interpolate positions or generate artificial AIS tracks.

### Query benchmarks

Baseline benchmark:

```text
data/queries/benchmark_vessel_tracks_within_bounds.sql
```

Measured baseline result:

```text
Access method: Sequential scan on ais_positions
Planning time: 1.543 ms
Execution time: 11.453 ms
```

Index-aware benchmark:

```text
data/queries/benchmark_vessel_tracks_with_spatial_index.sql
```

The index-aware query uses an EPSG:4326 envelope and PostGIS spatial predicates:

```sql
a.position && p.query_bounds
AND ST_Intersects(a.position, p.query_bounds)
```

Measured index-aware result:

```text
Access method: Index Scan using idx_ais_positions_position_gist
Planning time: 23.027 ms
Execution time: 27.001 ms
```

Interpretation:

- The index-aware query successfully used `idx_ais_positions_position_gist`.
- The sequential scan was faster on the current 9,977-row development table because index traversal and spatial predicate overhead can exceed the cost of scanning a small table.
- The index-aware query should be retained for spatial/corridor filtering on larger real AIS subsets, where GiST index selectivity is more valuable.
- All measured timings are local-development benchmarks and must not be presented as production-scale performance claims.


### API-ready vessel-track GeoJSON export

Exporter:

```text
data/queries/export_vessel_tracks_geojson.py
```

The exporter returns selected real AIS tracks as a GeoJSON `FeatureCollection`, with one `LineString` Feature per MMSI containing at least two observations in the selected spatial-temporal window.

Development export command:

```cmd
python data\queries\export_vessel_tracks_geojson.py --start-utc 2025-01-08T00:00:00Z --end-utc 2025-01-08T00:10:00Z --min-longitude -90.10000 --max-longitude -89.90000 --min-latitude 29.70000 --max-latitude 30.00000
```

Generated local output:

```text
data/ais/reports/vessel_tracks_feature_collection.geojson
```

Feature-level fields include:

```text
mmsi
track_start_time
track_end_time
position_count
gap_count
max_gap_seconds
track_continuity
ais_completeness
source_file
positions
```

Each position record includes:

```text
observed_at
longitude
latitude
sog_knots
cog_degrees
heading_degrees
source_file
source_row_number
```

Output contract:

```text
Top-level type: FeatureCollection
Track feature type: Feature
Track geometry type: LineString
CRS: EPSG:4326
Coordinate order: [longitude, latitude]
Timestamp format: ISO 8601 UTC ending in Z
```

The generated output explicitly sets:

```text
candidate_ranking_enabled: false
compatibility_state: insufficient_data
```

The export is map/timeline development output only. It uses the real local AIS development dataset dated 2025-01-08 and must not be used as vessel-attribution evidence for `SPILL_TEST3_001`, whose origin-time window is in 2026.