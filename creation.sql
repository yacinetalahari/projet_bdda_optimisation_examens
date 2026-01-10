CREATE TABLE departements (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE formations (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    dept_id INT NOT NULL,
    nb_modules INT CHECK (nb_modules BETWEEN 6 AND 9),
    FOREIGN KEY (dept_id) REFERENCES departements(id) ON DELETE CASCADE
);

CREATE TABLE etudiants (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    formation_id INT NOT NULL,
    promo INT,
    FOREIGN KEY (formation_id) REFERENCES formations(id)
);

CREATE TABLE professeurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    dept_id INT NOT NULL,
    specialite VARCHAR(100),
    nb_surveillance INT DEFAULT 0,
    FOREIGN KEY (dept_id) REFERENCES departements(id)
);

CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150),
    credits INT CHECK (credits BETWEEN 2 AND 6),
    formation_id INT NOT NULL,
    pre_req_id INT,
    FOREIGN KEY (formation_id) REFERENCES formations(id),
    FOREIGN KEY (pre_req_id) REFERENCES modules(id)
);

CREATE TABLE salles (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50),
    capacite INT CHECK (
        (type='salle' AND capacite <= 20)
        OR (type='amphi' AND capacite >= 50)
    ),
    type VARCHAR(10) CHECK (type IN ('salle','amphi')),
    batiment VARCHAR(50)
);

CREATE TABLE inscriptions (
    etudiant_id INT,
    module_id INT,
    note NUMERIC(4,2),
    PRIMARY KEY (etudiant_id, module_id),
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

CREATE TABLE examens (
    id SERIAL PRIMARY KEY,
    module_id INT NOT NULL,
    prof_id INT NOT NULL,
    salle_id INT NOT NULL,
    date_heure TIMESTAMP NOT NULL,
    duree_minutes INT CHECK (duree_minutes IN (60,90,120)),
    FOREIGN KEY (module_id) REFERENCES modules(id),
    FOREIGN KEY (prof_id) REFERENCES professeurs(id),
    FOREIGN KEY (salle_id) REFERENCES salles(id)
);
