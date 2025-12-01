# Protein Data Analysis Backend

A comprehensive backend system for querying and analyzing protein data using MongoDB and Neo4j databases.

## Features

### Core Functionality
- **Document Storage**: MongoDB for complex protein data with flexible querying
- **Graph Database**: Neo4j for protein similarity networks and relationships
- **Protein Graph Construction**: Jaccard similarity-based graph using domain composition
- **Label Propagation**: Automatic protein function annotation using graph algorithms
- **Data Import**: Support for various protein data formats (UniProt, GAF, custom)

### API Endpoints

#### Protein Management (`/proteins`)
- `GET /proteins/` - Search proteins with filters
- `GET /proteins/{protein_id}` - Get specific protein
- `POST /proteins/` - Create new protein
- `GET /proteins/{protein_id}/domains` - Get protein domains
- `GET /proteins/{protein_id}/similar` - Find similar proteins

#### Graph Operations (`/graph`)
- `GET /graph/search` - Search proteins in graph
- `GET /graph/{protein_id}/neighbors` - Get protein neighborhood
- `POST /graph/build` - Build protein similarity graph
- `GET /graph/statistics` - Get graph statistics
- `GET /graph/domain-analysis` - Analyze domain distribution

#### Statistics (`/statistics`)
- `GET /statistics/database` - MongoDB statistics
- `GET /statistics/graph` - Neo4j statistics  
- `GET /statistics/overview` - Comprehensive overview
- `GET /statistics/annotation-coverage` - Annotation coverage analysis

#### Annotation (`/annotation`)
- `POST /annotation/propagate` - Perform label propagation
- `GET /annotation/evaluate/{attribute}` - Evaluate propagation quality
- `GET /annotation/statistics/{attribute}` - Annotation statistics

#### Data Import (`/import`)
- `POST /import/proteins` - Import protein data
- `POST /import/domains` - Import domain annotations
- `POST /import/go-annotations` - Import GO annotations
- `POST /import/generate-sample` - Generate sample data

## Quick Start

### Using Docker (Recommended)

1. **Start all services:**
```bash
docker-compose up -d
```

2. **Access the API:**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- MongoDB: localhost:27017
- Neo4j Browser: http://localhost:7474

### Manual Setup

1. **Install dependencies:**
```bash
pip install -e .
```

2. **Start databases:**
```bash
# MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Neo4j
docker run -d -p 7474:7474 -p 7687:7687 --name neo4j \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.14
```

3. **Run the API:**
```bash
uvicorn main:app --reload
```

## Data Models

### Protein
```python
{
    "protein_id": "P12345",
    "name": "Sample Protein",
    "description": "A sample protein for testing",
    "sequence": "ACDEFGHIKLMNPQRSTVWY...",
    "length": 250,
    "taxonomy_id": "9606",
    "taxonomy_name": "Homo sapiens",
    "status": "reviewed|unreviewed",
    "ec_numbers": ["1.1.1.1", "2.2.2.2"],
    "go_terms": ["GO:0008150", "GO:0003674"],
    "domains": [
        {"domain_id": "IPR000123", "domain_name": "Kinase domain"}
    ]
}
```

### Graph Construction
The protein graph is built using Jaccard similarity on domain composition:

```
Jaccard(A, B) = |Domains(A) ∩ Domains(B)| / |Domains(A) ∪ Domains(B)|
```

### Label Propagation
Automatic function annotation using neighborhood-based label propagation:
1. Identify labeled and unlabeled proteins
2. Propagate labels through graph edges
3. Converge based on similarity thresholds
4. Update protein annotations

## Usage Examples

### Search Proteins
```bash
curl "http://localhost:8000/proteins/?query=kinase&limit=10"
```

### Build Protein Graph
```bash
curl -X POST "http://localhost:8000/graph/build?min_similarity=0.1"
```

### Get Protein Neighborhood
```bash
curl "http://localhost:8000/graph/P12345/neighbors?depth=2"
```

### Perform Label Propagation
```bash
curl -X POST "http://localhost:8000/annotation/propagate" \
  -H "Content-Type: application/json" \
  -d '{
    "attribute": "ec",
    "max_iterations": 100,
    "threshold": 0.01
  }'
```

### Import Sample Data
```bash
curl -X POST "http://localhost:8000/import/generate-sample?num_proteins=1000"
```

## Configuration

Environment variables (`.env` file):
```env
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=protein_db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Processing
JACCARD_THRESHOLD=0.1
MAX_PROTEINS_FOR_GRAPH=10000
```

## Architecture

```
├── app/
│   ├── models/          # Pydantic data models
│   ├── services/        # Business logic services
│   ├── routers/         # FastAPI route handlers
│   └── utils/           # Utility functions
├── docker-compose.yml   # Multi-container setup
├── Dockerfile          # Backend container
├── .env               # Environment configuration
└── main.py            # FastAPI application
```

## Technologies

- **FastAPI**: Modern, fast web framework for APIs
- **MongoDB**: Document database for protein data
- **Neo4j**: Graph database for protein networks
- **Pydantic**: Data validation and serialization
- **Motor**: Async MongoDB driver
- **Docker**: Containerization

## Performance Considerations

- Graph construction uses efficient domain indexing
- Batch processing for large datasets
- Async/await for concurrent operations
- Configurable similarity thresholds
- Pagination for large result sets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the NoSQL Protein Data Analysis coursework.