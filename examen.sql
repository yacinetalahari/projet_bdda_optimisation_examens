

CREATE TABLE departements (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE formations (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    dept_id INT NOT NULL,
    nb_modules INT CHECK (nb_modules > 0),
    CONSTRAINT fk_formation_dept
        FOREIGN KEY (dept_id) REFERENCES departements(id)
        ON DELETE CASCADE
);

CREATE TABLE etudiants (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    formation_id INT NOT NULL,
    promo INT NOT NULL,
    CONSTRAINT fk_etudiant_formation
        FOREIGN KEY (formation_id) REFERENCES formations(id)
);

CREATE TABLE professeurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    specialite VARCHAR(100),
    CONSTRAINT fk_prof_dept
        FOREIGN KEY (dept_id) REFERENCES departements(id)
);

CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    credits INT CHECK (credits > 0),
    formation_id INT NOT NULL,
    pre_req_id INT,
    CONSTRAINT fk_module_formation
        FOREIGN KEY (formation_id) REFERENCES formations(id),
    CONSTRAINT fk_module_prereq
        FOREIGN KEY (pre_req_id) REFERENCES modules(id)
);

CREATE TABLE inscriptions (
    etudiant_id INT NOT NULL,
    module_id INT NOT NULL,
    note NUMERIC(4,2),
    PRIMARY KEY (etudiant_id, module_id),
    CONSTRAINT fk_insc_etudiant
        FOREIGN KEY (etudiant_id) REFERENCES etudiants(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_insc_module
        FOREIGN KEY (module_id) REFERENCES modules(id)
        ON DELETE CASCADE
);

CREATE TABLE salles (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    capacite INT CHECK (capacite > 0),
    type VARCHAR(20) CHECK (type IN ('salle', 'amphi')),
    batiment VARCHAR(50)
);

CREATE TABLE examens (
    id SERIAL PRIMARY KEY,
    module_id INT NOT NULL,
    prof_id INT NOT NULL,
    salle_id INT NOT NULL,
    date_heure TIMESTAMP NOT NULL,
    duree_minutes INT CHECK (duree_minutes > 0),

    CONSTRAINT fk_exam_module
        FOREIGN KEY (module_id) REFERENCES modules(id),

    CONSTRAINT fk_exam_prof
        FOREIGN KEY (prof_id) REFERENCES professeurs(id),

    CONSTRAINT fk_exam_salle
        FOREIGN KEY (salle_id) REFERENCES salles(id)
);



SELECT COUNT(*) FROM etudiants;


SELECT e.id, DATE(ex.date_heure), COUNT(*) 
FROM etudiants e
JOIN inscriptions i ON i.etudiant_id = e.id
JOIN examens ex ON ex.module_id = i.module_id
GROUP BY e.id, DATE(ex.date_heure)
HAVING COUNT(*) > 1;

SELECT e.id, DATE(ex.date_heure), COUNT(*) 
FROM etudiants e
JOIN inscriptions i ON i.etudiant_id = e.id
JOIN examens ex ON ex.module_id = i.module_id
GROUP BY e.id, DATE(ex.date_heure)
HAVING COUNT(*) > 1;


SELECT COUNT(*)
FROM (
    SELECT prof_id, DATE(date_heure)
    FROM examens
    GROUP BY prof_id, DATE(date_heure)
    HAVING COUNT(*) > 3
) t;

SELECT COUNT(*) FROM examens;

SELECT f.nom, COUNT(e.id)
FROM formations f
JOIN etudiants e ON e.formation_id = f.id
GROUP BY f.nom;


SELECT s.nom,
       COUNT(i.etudiant_id)::float / s.capacite * 100 AS taux_occupation
FROM examens ex
JOIN salles s ON s.id = ex.salle_id
JOIN inscriptions i ON i.module_id = ex.module_id
GROUP BY s.nom, s.capacite;


SELECT p.nom, COUNT(ex.id)
FROM professeurs p
JOIN examens ex ON ex.prof_id = p.id
GROUP BY p.nom;




SELECT e.id, DATE(ex.date_heure), COUNT(*) 
FROM etudiants e
JOIN inscriptions i ON i.etudiant_id = e.id
JOIN examens ex ON ex.module_id = i.module_id
GROUP BY e.id, DATE(ex.date_heure)
HAVING COUNT(*) > 1;


