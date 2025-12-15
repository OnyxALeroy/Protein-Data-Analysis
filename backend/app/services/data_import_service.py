import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.models import Annotation, AnnotationType, Domain, Protein, ProteinStatus
from app.services.mongodb_service import mongodb_service

logger = logging.getLogger(__name__)


class DataImportService:
    def __init__(self):
        self.supported_formats = [".csv", ".tsv", ".txt"]

    async def import_protein_data(
        self, file_path: str, data_format: str = "uniprot"
    ) -> Dict[str, Any]:
        """Import protein data from file"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            if data_format == "uniprot":
                return await self._import_uniprot_format(path)
            elif data_format == "custom":
                return await self._import_custom_format(path)
            else:
                raise ValueError(f"Unsupported format: {data_format}")

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise

    async def _import_uniprot_format(self, file_path: Path) -> Dict[str, Any]:
        """Import data in UniProt-like format"""
        proteins = []

        if file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        elif file_path.suffix in [".tsv", ".txt"]:
            df = pd.read_csv(file_path, sep="\t")
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        required_columns = ["Entry", "Protein names"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        for _, row in df.iterrows():
            protein = Protein(
                protein_id=str(row["Entry"]),
                name=str(row.get("Protein names", "")),
                description=str(row.get("description", "")),
                sequence=str(row.get("sequence", "")),
                length=int(row.get("length", 0))
                if pd.notna(row.get("length"))
                else None,
                taxonomy_id=str(row.get("taxonomy_id", ""))
                if pd.notna(row.get("taxonomy_id"))
                else None,
                taxonomy_name=str(row.get("taxonomy_name", ""))
                if pd.notna(row.get("taxonomy_name"))
                else None,
                status=ProteinStatus.REVIEWED
                if str(row.get("status", "")).lower() == "reviewed"
                else ProteinStatus.UNREVIEWED,
                ec_numbers=self._parse_list_field(row.get("EC number", "")),
                go_terms=self._parse_list_field(row.get("go_terms", "")),
            )

            if "domains" in df.columns and pd.notna(row["domains"]):
                domain_ids = self._parse_list_field(row["domains"])
                protein.domains = [
                    Domain(domain_id=domain_id) for domain_id in domain_ids
                ]

            proteins.append(protein)

        return await self._batch_insert_proteins(proteins)

    async def _import_custom_format(self, file_path: Path) -> Dict[str, Any]:
        """Import data from custom format"""
        proteins = []

        with open(file_path, "r") as f:
            current_protein = None

            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith(">"):
                    if current_protein:
                        proteins.append(current_protein)

                    header = line[1:].split("|")
                    protein_id = (
                        header[0] if len(header) > 0 else f"protein_{len(proteins)}"
                    )
                    name = header[1] if len(header) > 1 else ""

                    current_protein = Protein(
                        protein_id=protein_id,
                        name=name,
                        status=ProteinStatus.UNREVIEWED,
                    )

                elif current_protein and line.startswith("EC:"):
                    ec_numbers = line[3:].strip().split(";")
                    current_protein.ec_numbers = [
                        ec.strip() for ec in ec_numbers if ec.strip()
                    ]

                elif current_protein and line.startswith("GO:"):
                    go_terms = line[3:].strip().split(";")
                    current_protein.go_terms = [
                        go.strip() for go in go_terms if go.strip()
                    ]

                elif current_protein and line.startswith("Domains:"):
                    domain_ids = line[8:].strip().split(";")
                    current_protein.domains = [
                        Domain(domain_id=domain.strip())
                        for domain in domain_ids
                        if domain.strip()
                    ]

                elif current_protein and line.startswith("Sequence:"):
                    current_protein.sequence = line[9:].strip()
                    current_protein.length = len(current_protein.sequence)

            if current_protein:
                proteins.append(current_protein)

        return await self._batch_insert_proteins(proteins)

    def _parse_list_field(self, value: Any) -> List[str]:
        """Parse list field from various formats"""
        if pd.isna(value) or value == "":
            return []

        if isinstance(value, str):
            if ";" in value:
                return [item.strip() for item in value.split(";") if item.strip()]
            elif "," in value:
                return [item.strip() for item in value.split(",") if item.strip()]
            elif "|" in value:
                return [item.strip() for item in value.split("|") if item.strip()]
            else:
                return [value.strip()] if value.strip() else []

        return [str(value)] if value else []

    async def _batch_insert_proteins(
        self, proteins: List[Protein], batch_size: int = 100
    ) -> Dict[str, Any]:
        """Insert proteins in batches"""
        total_proteins = len(proteins)
        inserted_count = 0
        failed_count = 0
        failed_proteins = []

        logger.info(f"Starting batch insert of {total_proteins} proteins")

        for i in range(0, total_proteins, batch_size):
            batch = proteins[i : i + batch_size]

            for protein in batch:
                try:
                    await mongodb_service.insert_protein(protein)
                    inserted_count += 1
                except Exception as e:
                    failed_count += 1
                    failed_proteins.append(
                        {"protein_id": protein.protein_id, "error": str(e)}
                    )
                    logger.warning(
                        f"Failed to insert protein {protein.protein_id}: {str(e)}"
                    )

            if (i + batch_size) % 1000 == 0:
                logger.info(f"Processed {i + batch_size}/{total_proteins} proteins")

        result = {
            "total_proteins": total_proteins,
            "inserted_count": inserted_count,
            "failed_count": failed_count,
            "success_rate": inserted_count / total_proteins
            if total_proteins > 0
            else 0,
            "failed_proteins": failed_proteins[:10],
        }

        logger.info(
            f"Batch insert completed: {inserted_count}/{total_proteins} proteins inserted"
        )
        return result

    async def import_domain_annotations(self, file_path: str) -> Dict[str, Any]:
        """Import domain annotations from protein2ipr format"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            protein_domains = defaultdict(list)

            with open(path, "r") as f:
                for line in f:
                    if line.startswith("#"):
                        continue

                    parts = line.strip().split("\t")
                    if len(parts) >= 3:
                        protein_id = parts[0]
                        domain_id = parts[1]
                        domain_name = parts[2] if len(parts) > 2 else ""

                        protein_domains[protein_id].append(
                            {"domain_id": domain_id, "domain_name": domain_name}
                        )

            updated_count = 0
            for protein_id, domains in protein_domains.items():
                try:
                    protein = await mongodb_service.get_protein_by_id(protein_id)
                    if protein:
                        protein.domains = [Domain(**domain) for domain in domains]
                        await mongodb_service.insert_protein(protein)
                        updated_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to update domains for {protein_id}: {str(e)}"
                    )

            return {
                "total_proteins_with_domains": len(protein_domains),
                "updated_count": updated_count,
            }

        except Exception as e:
            logger.error(f"Domain import failed: {str(e)}")
            raise

    async def import_go_annotations(self, file_path: str) -> Dict[str, Any]:
        """Import GO annotations from GAF format"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            protein_annotations = defaultdict(list)

            with open(path, "r") as f:
                for line in f:
                    if line.startswith("!"):
                        continue

                    parts = line.strip().split("\t")
                    if len(parts) >= 5:
                        protein_id = parts[1]
                        go_term = parts[4]
                        evidence = parts[6] if len(parts) > 6 else ""

                        protein_annotations[protein_id].append(
                            {
                                "annotation_type": AnnotationType.GO,
                                "annotation_value": go_term,
                                "evidence": evidence,
                            }
                        )

            updated_count = 0
            for protein_id, annotations in protein_annotations.items():
                try:
                    protein = await mongodb_service.get_protein_by_id(protein_id)
                    if protein:
                        protein.annotations = [Annotation(**ann) for ann in annotations]
                        protein.go_terms = [
                            ann["annotation_value"] for ann in annotations
                        ]
                        await mongodb_service.insert_protein(protein)
                        updated_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to update GO annotations for {protein_id}: {str(e)}"
                    )

            return {
                "total_proteins_with_go": len(protein_annotations),
                "updated_count": updated_count,
            }

        except Exception as e:
            logger.error(f"GO annotation import failed: {str(e)}")
            raise

    async def generate_sample_data(self, num_proteins: int = 1000) -> Dict[str, Any]:
        """Generate sample protein data for testing"""
        import random

        sample_domains = [f"IPR{str(i).zfill(6)}" for i in range(1, 101)]
        sample_ec_numbers = [
            f"1.{i}.{j}.{k}"
            for i in range(1, 4)
            for j in range(1, 10)
            for k in range(1, 10)
        ]
        sample_go_terms = [f"GO:{str(836742 + i)}" for i in range(1, 101)]

        proteins = []

        for i in range(num_proteins):
            protein_id = f"SAMPLE_{str(i).zfill(6)}"
            name = f"Sample protein {i}"

            num_domains = random.randint(1, 8)
            domains = random.sample(sample_domains, num_domains)

            num_ec = random.randint(0, 3)
            ec_numbers = random.sample(sample_ec_numbers, num_ec) if num_ec > 0 else []

            num_go = random.randint(0, 5)
            go_terms = random.sample(sample_go_terms, num_go) if num_go > 0 else []

            sequence = "".join(
                random.choices("ACDEFGHIKLMNPQRSTVWY", k=random.randint(50, 500))
            )

            protein = Protein(
                protein_id=protein_id,
                name=name,
                description=f"Generated sample protein {i} for testing purposes",
                sequence=sequence,
                length=len(sequence),
                taxonomy_id="9606",
                taxonomy_name="Homo sapiens",
                status=ProteinStatus.REVIEWED
                if random.random() > 0.7
                else ProteinStatus.UNREVIEWED,
                ec_numbers=ec_numbers,
                go_terms=go_terms,
                domains=[Domain(domain_id=domain) for domain in domains],
            )

            proteins.append(protein)

        return await self._batch_insert_proteins(proteins)


data_import_service = DataImportService()
