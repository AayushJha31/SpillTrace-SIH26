BEGIN;

ALTER TABLE vessel_candidates
    DROP CONSTRAINT IF EXISTS vessel_candidates_score_check;

ALTER TABLE vessel_candidates
    DROP CONSTRAINT IF EXISTS vessel_candidates_track_continuity_check;

COMMIT;