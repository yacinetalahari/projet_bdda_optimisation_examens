<<<<<<< HEAD
README will be added later 
=======
# Exam Scheduler
1. **Prerequisites**: Ensure Python and PostgreSQL are installed.
2. **Install Deps**: `pip install -r requirements.txt`
3. **Setup DB**: Create a database named `exam_scheduler`.
4. **Import Schema**: Run `psql -U postgres -d exam_scheduler -f creation.sql` then `contrainte.sql`.
5. **Optimize**: Run `psql -U postgres -d exam_scheduler -f optimization.sql` (Password: `yassinopostgresql`).
6. **Gen Data**: Run `python data.py` to populate the database with mock data.
7. **Run App**: Execute `streamlit run app.py` and open the URL shown.
8. **Usage**: Go to "Administration" > "Générer" to build the schedule.
9. **View**: Go to "Consultation" to see individual timetables.
>>>>>>> 617c0f47 (fonctionnement updated)
