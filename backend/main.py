import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import annotation, data_import, graph, proteins, statistics
from app.services.mongodb_service import mongodb_service
from app.services.neo4j_service import neo4j_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await mongodb_service.connect()
    await neo4j_service.connect()
    print("✅ Database connections established")

    yield

    # Shutdown
    await mongodb_service.disconnect()
    await neo4j_service.disconnect()
    print("✅ Database connections closed")


app = FastAPI(
    title="Protein Data Analysis API",
    description="Backend for querying and analyzing protein data using MongoDB and Neo4j",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(proteins.router)
app.include_router(graph.router)
app.include_router(statistics.router)
app.include_router(annotation.router)
app.include_router(data_import.router)


@app.get("/")
async def root():
    return {
        "message": "Protein Data Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "proteins": "/proteins",
            "graph": "/graph",
            "statistics": "/statistics",
            "annotation": "/annotation",
            "import": "/import",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        if mongodb_service.proteins_collection is None:
            raise Exception("MongoDB not connected")
        await mongodb_service.proteins_collection.count_documents({})
        mongo_status = "healthy"
    except Exception as _:
        mongo_status = "unhealthy"

    try:
        # Test Neo4j connection
        if neo4j_service.driver is None:
            raise Exception("Neo4j not connected")
        async with neo4j_service.driver.session() as session:
            await session.run("RETURN 1")
        neo4j_status = "healthy"
    except Exception as _:
        neo4j_status = "unhealthy"

    return {
        "status": "healthy"
        if mongo_status == "healthy" and neo4j_status == "healthy"
        else "degraded",
        "mongodb": mongo_status,
        "neo4j": neo4j_status,
    }


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level="info")
