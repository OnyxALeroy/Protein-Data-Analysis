db = db.getSiblingDB('protein_db');

db.createCollection('proteins');
db.createCollection('domains');
db.createCollection('annotations');

db.proteins.createIndex({ "protein_id": 1 }, { unique: true });
db.proteins.createIndex({ "name": "text", "description": "text" });
db.proteins.createIndex({ "ec_numbers": 1 });
db.proteins.createIndex({ "go_terms": 1 });
db.proteins.createIndex({ "taxonomy_id": 1 });

db.domains.createIndex({ "protein_id": 1 });
db.domains.createIndex({ "domain_id": 1 });

db.annotations.createIndex({ "protein_id": 1 });
db.annotations.createIndex({ "annotation_type": 1 });
db.annotations.createIndex({ "annotation_value": 1 });

print('Database initialized successfully');