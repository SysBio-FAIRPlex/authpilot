import csv
from app.database import Base, engine, SessionLocal
from app.models.person import Person
from app.models.synthetic_dataset import SyntheticDataset
from google.cloud import bigquery

# I'm arbitrarily choosing people with ID <= 1500 to be in PD
MAX_PD_ID = 1500

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

    print("Querying BQ for initial data...")
    sync_bigquery_to_sqlite()
    print("BigQuery data loaded into SQLite.")

    print("Loading Synthetic Dataset from CSV...")
    load_synthetic_data_to_sqlite()
    print("Synthetic CSV data loaded into SQLite")

def sync_bigquery_to_sqlite():
    session = SessionLocal()
    bq_client = bigquery.Client()

    # This sql is pretty wild. First, it gets each person's latest diagnosis.
    # I call this the ranked_conditions (because the diagnosis is a condition_occurrence concept)
    # Then, it joins that with demographics data available in the person table.
    # But person table only has concept IDs, so we join with the concept table to get
    # human readable strings.
    query = f"""
    WITH ranked_conditions AS (
      SELECT
        co.person_id,
        c.concept_name AS diagnosis_name,
        ROW_NUMBER() OVER (PARTITION BY co.person_id ORDER BY co.condition_start_date DESC) AS rn
      FROM `data-development-440922.sysbio_synth_omop.condition_occurrence` co
      JOIN `data-development-440922.sysbio_synth_omop.concept` c
        ON co.condition_concept_id = c.concept_id
    )
    SELECT
      p.person_id,
      gender.concept_name AS gender,
      p.year_of_birth,
      race.concept_name AS race,
      ethnicity.concept_name AS ethnicity,
      rc.diagnosis_name
    FROM ranked_conditions rc
    JOIN `data-development-440922.sysbio_synth_omop.person` p
      ON rc.person_id = p.person_id
    LEFT JOIN `data-development-440922.sysbio_synth_omop.concept` gender
      ON p.gender_concept_id = gender.concept_id
    LEFT JOIN `data-development-440922.sysbio_synth_omop.concept` race
      ON p.race_concept_id = race.concept_id
    LEFT JOIN `data-development-440922.sysbio_synth_omop.concept` ethnicity
      ON p.ethnicity_concept_id = ethnicity.concept_id
    WHERE rc.rn = 1
    AND p.person_id <= {MAX_PD_ID}
    """

    result = bq_client.query(query).result()

    for row in result:
        pc = Person(
            person_id=row["person_id"],
            gender=row["gender"],
            year_of_birth=row["year_of_birth"],
            race=row["race"],
            ethnicity=row["ethnicity"],
            diagnosis_name=row["diagnosis_name"]
        )
        session.merge(pc)
    session.commit()
    session.close()

def load_synthetic_data_to_sqlite():
  session = SessionLocal()
  with open("synthetic_dataset.csv", newline='', encoding='utf-8') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
          dataset = SyntheticDataset(
              ID=row["ID"],
              dataset=row["dataset"],
              status=row["status"],
              sex=row["sex"],
              age_at_sampling=int(row["age_at_sampling"]) if row["age_at_sampling"] else None,
              age_at_death=int(row["age_at_death"]) if row["age_at_death"] else None,
              APOE4_compund_genotype=int(row["APOE4_compund_genotype"]) if row["APOE4_compund_genotype"] else None,
              time_from_baseline=float(row["time_from_baseline"]) if row["time_from_baseline"] else None,
              repository_link=row["repository_link"]
          )
          session.add(dataset)
      session.commit()

if __name__ == "__main__":
    init_db()
