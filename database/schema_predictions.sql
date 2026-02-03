CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    upcoming_match_id UUID REFERENCES upcoming_matches(id) ON DELETE CASCADE,

    model_version TEXT,              -- "xgb_service_v1"
    engine_used TEXT,                -- "ml" / "heuristic"

    p_serve_p1 NUMERIC(4,3),
    p_serve_p2 NUMERIC(4,3),

    p_match_p1 NUMERIC(4,3),
    p_match_p2 NUMERIC(4,3),

    p_2_0 NUMERIC(4,3),
    p_2_1 NUMERIC(4,3),

    avg_total_games NUMERIC(5,2),

    surface TEXT,
    tournament TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    CONSTRAINT unique_prediction_snapshot UNIQUE (
        upcoming_match_id,
        model_version,
        created_at -- This might be too granular for uniqueness if created_at changes. 
                   -- Usually we want one per run or time window. 
                   -- But the user suggested this constraint. 
                   -- I'll keep it as suggested but uniqueness logic in code (fetch existing).
    )
);
