
-- Habilitar RLS en upcoming_matches
ALTER TABLE upcoming_matches ENABLE ROW LEVEL SECURITY;

-- Borrar política anterior si existe
DROP POLICY IF EXISTS "Public Read Upcoming" ON upcoming_matches;

-- Permitir lectura a TODOS (incluyendo anon y authenticated)
CREATE POLICY "Public Read Upcoming" ON upcoming_matches
FOR SELECT USING (true);

-- Verificar
SELECT count(*) as matches_count FROM upcoming_matches;
