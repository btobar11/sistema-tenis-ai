-- PASO 1: Copia todo este código
-- PASO 2: Ve a https://supabase.com/dashboard/project/hexpbbbsqkgowbrrorjt/sql/new
-- PASO 3: Pégalo y dale a "RUN"

-- 1. Eliminar restricción vieja si existe (para evitar errores)
ALTER TABLE prediction_snapshots
DROP CONSTRAINT IF EXISTS fk_upcoming_match;

-- 2. Crear la conexión correcta (Foreign Key)
ALTER TABLE prediction_snapshots
ADD CONSTRAINT fk_upcoming_match
FOREIGN KEY (upcoming_match_id)
REFERENCES upcoming_matches(id)
ON DELETE CASCADE;

-- 3. Asegurar permisos de lectura (RLS)
ALTER TABLE prediction_snapshots ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public Read Snapshots" ON prediction_snapshots;
CREATE POLICY "Public Read Snapshots" ON prediction_snapshots FOR SELECT USING (true);

-- 4. Verificar que funcionó (El resultado debería ser "Success" o una tabla vacía sin error)
SELECT count(*) as snapshots_count FROM prediction_snapshots;
