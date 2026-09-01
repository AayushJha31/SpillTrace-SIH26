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