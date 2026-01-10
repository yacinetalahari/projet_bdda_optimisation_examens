CREATE OR REPLACE FUNCTION check_exam_etudiant()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM inscriptions i
        JOIN examens e ON e.module_id = i.module_id
        WHERE i.etudiant_id IN (
            SELECT etudiant_id
            FROM inscriptions
            WHERE module_id = NEW.module_id
        )
        AND DATE(e.date_heure) = DATE(NEW.date_heure)
    ) THEN
        RAISE EXCEPTION 'Conflit étudiant';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_exam_etudiant
BEFORE INSERT ON examens
FOR EACH ROW EXECUTE FUNCTION check_exam_etudiant();

CREATE OR REPLACE FUNCTION check_exam_prof()
RETURNS TRIGGER AS $$
BEGIN
    IF (
        SELECT COUNT(*) FROM examens
        WHERE prof_id = NEW.prof_id
        AND DATE(date_heure) = DATE(NEW.date_heure)
    ) >= 3 THEN
        RAISE EXCEPTION 'Professeur dépasse 3 examens/jour';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_exam_prof
BEFORE INSERT ON examens
FOR EACH ROW EXECUTE FUNCTION check_exam_prof();
