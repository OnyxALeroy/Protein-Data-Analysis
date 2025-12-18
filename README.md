# Protein Data Analysis Platform

A comprehensive full-stack platform for protein data analysis using MongoDB and Neo4j databases. This project implements a sophisticated protein similarity network with automated annotation propagation capabilities.

## Architecture Overview

### Backend (FastAPI + Python)
- **Document Storage**: MongoDB for complex protein data with flexible querying
- **Graph Database**: Neo4j for protein similarity networks and relationships
- **Protein Graph Construction**: Jaccard similarity-based graph using domain composition
- **Label Propagation**: Automatic protein function annotation using graph algorithms
- **Data Import**: Support for various protein data formats (UniProt, GAF, custom)

### Frontend (Vue.js 3 + Vite)
- **Protein Search**: Advanced filtering and pagination for protein exploration
- **Graph Visualization**: Interactive protein similarity network viewer
- **Annotation System**: Label propagation interface with quality evaluation
- **Statistics Dashboard**: Comprehensive database and network analytics
- **Data Import Tools**: User-friendly data upload and processing interface

## Features

### Core Functionality
- **Protein Management**: Search, filter, and retrieve detailed protein information
- **Similarity Graph**: Construct protein networks based on domain Jaccard similarity
- **Graph Operations**: Navigate protein neighborhoods and analyze network topology
- **Automated Annotation**: Propagate functional labels through graph edges
- **Statistical Analysis**: Database metrics and annotation coverage reports
- **Data Import Pipeline**: Process UniProt, GAF, and custom protein datasets

### API Endpoints

#### Protein Management (`/proteins`)
- `GET /proteins/` - Search proteins with filters and pagination
- `GET /proteins/{protein_id}` - Get specific protein details
- `POST /proteins/` - Create new protein entry
- `GET /proteins/{protein_id}/domains` - Retrieve protein domains
- `GET /proteins/{protein_id}/similar` - Find similar proteins

#### Graph Operations (`/graph`)
- `GET /graph/search` - Search proteins within graph structure
- `GET /graph/{protein_id}/neighbors` - Get protein neighborhood (configurable depth)
- `POST /graph/build` - Build protein similarity graph with threshold
- `GET /graph/statistics` - Graph topology and connectivity metrics
- `GET /graph/domain-analysis` - Domain distribution analysis

#### Statistics (`/statistics`)
- `GET /statistics/database` - MongoDB collection statistics
- `GET /statistics/graph` - Neo4j graph statistics
- `GET /statistics/overview` - Comprehensive system overview
- `GET /statistics/annotation-coverage` - Annotation completeness analysis

#### Annotation (`/annotation`)
- `POST /annotation/propagate` - Perform label propagation with parameters
- `GET /annotation/evaluate/{attribute}` - Evaluate propagation quality
- `GET /annotation/statistics/{attribute}` - Annotation distribution metrics

#### Data Import (`/import`)
- `POST /import/proteins` - Import protein datasets
- `POST /import/domains` - Import domain annotations
- `POST /import/go-annotations` - Import Gene Ontology annotations
- `POST /import/generate-sample` - Generate synthetic test data

### Frontend Features

#### Navigation & User Interface
- **Home**: Project overview and quick access to features
- **Proteins**: Searchable protein database with detailed views
- **Graph Build**: Interactive graph construction with parameter controls
- **Graph Neighbors**: Visual exploration of protein networks
- **Statistics**: Real-time dashboard of system metrics
- **Annotation**: Label propagation interface with results visualization
- **Data Import**: File upload and processing management

## Quick Start

### Using Docker (Recommended)

1. **Start all services:**
```bash
docker-compose up -d
```

2. **Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- MongoDB: localhost:27017
- Neo4j Browser: http://localhost:7474

### Manual Setup

#### Backend
```bash
cd backend
pip install -e .
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Databases
```bash
# MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Neo4j
docker run -d -p 7474:7474 -p 7687:7687 --name neo4j \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.14
```

## Data Models

### Protein Schema
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
Protein similarity graphs use Jaccard similarity on domain composition:

```
Jaccard(A, B) = |Domains(A) ∩ Domains(B)| / |Domains(A) ∪ Domains(B)|
```

Edges are created when similarity exceeds configurable threshold (default: 0.1).

### Label Propagation Algorithm
1. Identify labeled and unlabeled proteins in the graph
2. Propagate functional labels through weighted edges
3. Converge based on similarity thresholds and iteration limits
4. Update protein annotations with confidence scores

## Usage Examples

### API Usage
```bash
# Search proteins
curl "http://localhost:8000/proteins/?query=kinase&limit=10"

# Build similarity graph
curl -X POST "http://localhost:8000/graph/build?min_similarity=0.1"

# Get protein neighborhood
curl "http://localhost:8000/graph/P12345/neighbors?depth=2"

# Perform label propagation
curl -X POST "http://localhost:8000/annotation/propagate" \
  -H "Content-Type: application/json" \
  -d '{"attribute": "ec", "max_iterations": 100, "threshold": 0.01}'
```

## Configuration

Environment variables (.env file):
```env
# Database Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=protein_db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Processing Parameters
JACCARD_THRESHOLD=0.1
MAX_PROTEINS_FOR_GRAPH=10000
```

## Technology Stack

### Backend
- **FastAPI**: Modern, high-performance web framework
- **MongoDB**: Document database for flexible protein data storage
- **Neo4j**: Graph database for protein similarity networks
- **Pydantic**: Data validation and serialization
- **Motor**: Async MongoDB driver
- **Docker**: Containerization and orchestration

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **Vue Router**: Client-side routing
- **Vite**: Fast build tool and development server
- **Component-based Architecture**: Modular, reusable UI components

## Performance Considerations

- **Efficient Graph Construction**: Domain indexing and batch processing
- **Concurrent Operations**: Async/await for database operations
- **Memory Optimization**: Configurable similarity thresholds and batch sizes
- **Pagination**: Large dataset handling with cursor-based pagination
- **Resource Limits**: Docker memory constraints and monitoring

## Project Structure

```
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── models/         # Pydantic data models
│   │   ├── services/       # Business logic services
│   │   ├── routers/        # API route handlers
│   │   └── utils/          # Utility functions
│   ├── docker-compose.yml  # Multi-container setup
│   ├── Dockerfile         # Backend container
│   └── main.py           # FastAPI application entry
├── frontend/              # Vue.js application
│   ├── src/
│   │   ├── components/    # Reusable Vue components
│   │   ├── views/        # Page-level components
│   │   ├── router/       # Vue Router configuration
│   │   ├── services/     # API communication
│   │   └── assets/       # Static assets
│   ├── package.json      # Frontend dependencies
│   └── vite.config.js   # Vite configuration
├── data/                 # Dataset storage
└── docs/                # Documentation and reports
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with appropriate tests
4. Ensure code quality and documentation
5. Submit a pull request

## License

This project is part of the NoSQL Protein Data Analysis coursework.