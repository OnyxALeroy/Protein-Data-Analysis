import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, TEXT

from app.models import Annotation, AnnotationType, Domain, Protein, ProteinSearch

load_dotenv()


class MongoDBService:
    def __init__(self):
        self.client = None
        self.database = None
        self.proteins_collection = None
        self.domains_collection = None
        self.annotations_collection = None

    async def connect(self):
        """Initialize MongoDB connection"""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "protein_db")

        self.client = AsyncIOMotorClient(mongodb_url)
        self.database = self.client[db_name]
        self.proteins_collection = self.database.proteins
        self.domains_collection = self.database.domains
        self.annotations_collection = self.database.annotations

        await self._create_indexes()

    async def _create_indexes(self):
        """Create necessary indexes for performance"""
        if (
            self.proteins_collection is None
            or self.domains_collection is None
            or self.annotations_collection is None
        ):
            raise Exception("MongoDB not connected")

        await self.proteins_collection.create_index(
            [("protein_id", ASCENDING)], unique=True
        )
        await self.proteins_collection.create_index(
            [("name", TEXT), ("description", TEXT)]
        )
        await self.proteins_collection.create_index([("ec_numbers", ASCENDING)])
        await self.proteins_collection.create_index([("go_terms", ASCENDING)])
        await self.proteins_collection.create_index([("taxonomy_id", ASCENDING)])
        await self.proteins_collection.create_index([("status", ASCENDING)])

        await self.domains_collection.create_index([("protein_id", ASCENDING)])
        await self.domains_collection.create_index([("domain_id", ASCENDING)])

        await self.annotations_collection.create_index([("protein_id", ASCENDING)])
        await self.annotations_collection.create_index([("annotation_type", ASCENDING)])
        await self.annotations_collection.create_index(
            [("annotation_value", ASCENDING)]
        )

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

    async def insert_protein(self, protein: Protein) -> str:
        """Insert a new protein into the database"""
        if (
            self.proteins_collection is None
            or self.domains_collection is None
            or self.annotations_collection is None
        ):
            raise Exception("MongoDB not connected")

        protein_dict = protein.model_dump(exclude_unset=True)

        result = await self.proteins_collection.insert_one(protein_dict)

        if protein.domains:
            domain_docs = [
                {"protein_id": protein.protein_id, **domain.model_dump()}
                for domain in protein.domains
            ]
            await self.domains_collection.insert_many(domain_docs)

        if protein.annotations:
            annotation_docs = [
                {"protein_id": protein.protein_id, **annotation.model_dump()}
                for annotation in protein.annotations
            ]
            await self.annotations_collection.insert_many(annotation_docs)

        return str(result.inserted_id)

    async def get_protein_by_id(self, protein_id: str) -> Optional[Protein]:
        """Get a protein by its ID"""
        if (
            self.proteins_collection is None
            or self.domains_collection is None
            or self.annotations_collection is None
        ):
            raise Exception("MongoDB not connected")

        protein_doc = await self.proteins_collection.find_one(
            {"protein_id": protein_id}
        )

        if not protein_doc:
            return None

        domains = await self.domains_collection.find(
            {"protein_id": protein_id}
        ).to_list(length=None)
        annotations = await self.annotations_collection.find(
            {"protein_id": protein_id}
        ).to_list(length=None)

        protein_doc["domains"] = [Domain(**domain) for domain in domains]
        protein_doc["annotations"] = [
            Annotation(**annotation) for annotation in annotations
        ]

        return Protein(**protein_doc)

    async def search_proteins(self, search: ProteinSearch) -> List[Protein]:
        """Search proteins based on various criteria"""
        if (
            self.proteins_collection is None
            or self.domains_collection is None
            or self.annotations_collection is None
        ):
            raise Exception("MongoDB not connected")

        query = {}

        if search.protein_id:
            query["protein_id"] = {"$regex": search.protein_id, "$options": "i"}

        if search.name:
            query["name"] = {"$regex": search.name, "$options": "i"}

        if search.ec_numbers:
            query["ec_numbers"] = {"$in": search.ec_numbers}

        if search.go_terms:
            query["go_terms"] = {"$in": search.go_terms}

        if search.taxonomy_id:
            query["taxonomy_id"] = search.taxonomy_id

        if search.status:
            query["status"] = search.status

        if search.query:
            query["$text"] = {"$search": search.query}

        cursor = (
            self.proteins_collection.find(query).skip(search.offset).limit(search.limit)
        )
        proteins_docs = await cursor.to_list(length=None)

        proteins = []
        for doc in proteins_docs:
            domains = await self.domains_collection.find(
                {"protein_id": doc["protein_id"]}
            ).to_list(length=None)
            annotations = await self.annotations_collection.find(
                {"protein_id": doc["protein_id"]}
            ).to_list(length=None)

            doc["domains"] = [Domain(**domain) for domain in domains]
            doc["annotations"] = [
                Annotation(**annotation) for annotation in annotations
            ]

            proteins.append(Protein(**doc))

        return proteins

    async def get_all_proteins_for_graph(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all proteins with their domains for graph construction"""
        if self.proteins_collection is None or self.domains_collection is None:
            raise Exception("MongoDB not connected")

        query = {}
        projection = {
            "protein_id": 1,
            "name": 1,
            "status": 1,
            "ec_numbers": 1,
            "go_terms": 1,
        }

        cursor = self.proteins_collection.find(query, projection)
        if limit:
            cursor = cursor.limit(limit)

        proteins = await cursor.to_list(length=None)

        for protein in proteins:
            domains = await self.domains_collection.find(
                {"protein_id": protein["protein_id"]}, {"domain_id": 1}
            ).to_list(length=None)
            protein["domains"] = [d["domain_id"] for d in domains]

        return proteins

    async def get_protein_domains(self, protein_id: str) -> List[str]:
        """Get domain IDs for a specific protein"""
        if self.domains_collection is None:
            raise Exception("MongoDB not connected")

        domains = await self.domains_collection.find(
            {"protein_id": protein_id}, {"domain_id": 1}
        ).to_list(length=None)

        return [d["domain_id"] for d in domains]

    async def update_protein_annotations(
        self, protein_id: str, annotations: List[Annotation]
    ) -> bool:
        """Update protein annotations"""
        if self.proteins_collection is None or self.annotations_collection is None:
            raise Exception("MongoDB not connected")

        result = await self.annotations_collection.delete_many(
            {"protein_id": protein_id}
        )

        if annotations:
            annotation_docs = [
                {"protein_id": protein_id, **annotation.model_dump()}
                for annotation in annotations
            ]
            await self.annotations_collection.insert_many(annotation_docs)

        update_data = {
            "updated_at": datetime.utcnow(),
            "ec_numbers": [
                ann.annotation_value
                for ann in annotations
                if ann.annotation_type == AnnotationType.EC
            ],
            "go_terms": [
                ann.annotation_value
                for ann in annotations
                if ann.annotation_type == AnnotationType.GO
            ],
        }

        result = await self.proteins_collection.update_one(
            {"protein_id": protein_id}, {"$set": update_data}
        )

        return result.modified_count > 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        if (
            self.proteins_collection is None
            or self.domains_collection is None
            or self.annotations_collection is None
        ):
            raise Exception("MongoDB not connected")

        total_proteins = await self.proteins_collection.count_documents({})
        reviewed_proteins = await self.proteins_collection.count_documents(
            {"status": "reviewed"}
        )
        unreviewed_proteins = await self.proteins_collection.count_documents(
            {"status": "unreviewed"}
        )

        proteins_with_ec = await self.proteins_collection.count_documents(
            {"ec_numbers.0": {"$exists": True}}
        )
        proteins_with_go = await self.proteins_collection.count_documents(
            {"go_terms.0": {"$exists": True}}
        )
        proteins_with_domains = await self.domains_collection.distinct("protein_id")
        proteins_with_domains_count = len(proteins_with_domains)

        total_domains = await self.domains_collection.count_documents({})
        total_annotations = await self.annotations_collection.count_documents({})

        return {
            "total_proteins": total_proteins,
            "reviewed_proteins": reviewed_proteins,
            "unreviewed_proteins": unreviewed_proteins,
            "proteins_with_ec": proteins_with_ec,
            "proteins_with_go": proteins_with_go,
            "proteins_with_domains": proteins_with_domains_count,
            "total_domains": total_domains,
            "total_annotations": total_annotations,
        }


mongodb_service = MongoDBService()
