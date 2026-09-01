/*
Find vessels within 50 km of a supplied point during a UTC time window.

Use real values only.

Coordinate order:
ST_MakePoint(longitude, latitude)

Distance unit:
50000 meters = 50 km

For backend use, replace:
:longitude
:latitude
:time_start_utc
:time_end_utc

with safely bound query parameters.
*/

SELECT
    p.mmsi,

    MIN(p.observed_at) AS first_seen_utc,

    MAX(p.observed_at) AS last_seen_utc,

    COUNT(*) AS position_count,

    ROUND(
        MIN(
            ST_Distance(
                p.position::geography,
                ST_SetSRID(
                    ST_MakePoint(
                        :longitude,
                        :latitude
                    ),
                    4326
                )::geography
            )
        )::numeric,
        2
    ) AS minimum_distance_meters

FROM ais_positions AS p

WHERE p.observed_at >= :time_start_utc

  AND p.observed_at < :time_end_utc

  AND ST_DWithin(
      p.position::geography,
      ST_SetSRID(
          ST_MakePoint(
              :longitude,
              :latitude
          ),
          4326
      )::geography,
      50000
  )

GROUP BY p.mmsi

ORDER BY minimum_distance_meters ASC;