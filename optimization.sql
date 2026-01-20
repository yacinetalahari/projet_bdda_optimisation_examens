-- Index pour accélérer les jointures sur les inscriptions
CREATE INDEX IF NOT EXISTS idx_inscriptions_etudiant ON inscriptions(etudiant_id);
CREATE INDEX IF NOT EXISTS idx_inscriptions_module ON inscriptions(module_id);

-- Index partiel sur les salles pour filtrer rapidement par capacité/type
CREATE INDEX IF NOT EXISTS idx_salles_amphi ON salles(capacite) WHERE type = 'amphi';
CREATE INDEX IF NOT EXISTS idx_salles_salle ON salles(capacite) WHERE type = 'salle';

-- Index sur les examens pour vérifier les conflits de date
CREATE INDEX IF NOT EXISTS idx_examens_date ON examens(date_heure);
CREATE INDEX IF NOT EXISTS idx_examens_prof ON examens(prof_id);

-- Procédure pour nettoyer le planning actuel
CREATE OR REPLACE PROCEDURE clear_planning()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE examens RESTART IDENTITY CASCADE;
END;
$$;
