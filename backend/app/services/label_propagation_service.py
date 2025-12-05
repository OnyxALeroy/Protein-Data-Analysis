import logging
import random
from collections import Counter, defaultdict
from typing import Any, Dict, List

from app.models import LabelPropagationRequest, LabelPropagationResult
from app.services.mongodb_service import mongodb_service
from app.services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)


class LabelPropagationService:
    def __init__(self):
        self.convergence_threshold = 0.01

    async def propagate_labels(
        self, request: LabelPropagationRequest
    ) -> LabelPropagationResult:
        """Perform label propagation for protein function annotation"""
        logger.info(f"Starting label propagation for {request.attribute}")

        proteins_data = await neo4j_service.get_proteins_for_label_propagation(
            request.attribute
        )
        logger.info(f"Retrieved {len(proteins_data)} proteins for propagation")

        if not proteins_data:
            raise ValueError("No proteins found for label propagation")

        protein_graph = self._build_graph(proteins_data)
        initial_labels = self._extract_initial_labels(proteins_data, request.attribute)

        logger.info(
            f"Found {len([p for p in proteins_data if p['labels']])} proteins with initial labels"
        )

        final_labels, iterations, converged = self._label_propagation(
            protein_graph, initial_labels, request.max_iterations, request.threshold
        )

        confidence_scores = self._calculate_confidence_scores(
            final_labels, initial_labels
        )

        await self._update_protein_labels(final_labels, request.attribute)

        annotated_count = len([p for p in final_labels.values() if p])

        result = LabelPropagationResult(
            iterations_completed=iterations,
            converged=converged,
            annotated_proteins=annotated_count,
            confidence_scores=confidence_scores,
            predicted_labels=final_labels,
        )

        logger.info(
            f"Label propagation completed: {iterations} iterations, {annotated_count} proteins annotated"
        )
        return result

    def _build_graph(self, proteins_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build adjacency list from protein data"""
        graph = {}

        for protein in proteins_data:
            protein_id = protein["protein_id"]
            neighbors = protein.get("neighbors", [])
            graph[protein_id] = neighbors

        return graph

    def _extract_initial_labels(
        self, proteins_data: List[Dict[str, Any]], attribute: str
    ) -> Dict[str, List[str]]:
        """Extract initial labels from proteins"""
        initial_labels = {}

        for protein in proteins_data:
            protein_id = protein["protein_id"]
            labels = protein.get("labels", [])
            initial_labels[protein_id] = labels if labels else []

        return initial_labels

    def _label_propagation(
        self,
        graph: Dict[str, List[str]],
        initial_labels: Dict[str, List[str]],
        max_iterations: int,
        threshold: float,
    ) -> tuple:
        """Perform label propagation algorithm"""
        proteins = list(graph.keys())
        current_labels = {p: set(labels) for p, labels in initial_labels.items()}

        for iteration in range(max_iterations):
            new_labels = {}
            changes = 0

            for protein in proteins:
                neighbors = graph[protein]

                if not neighbors:
                    new_labels[protein] = current_labels[protein]
                    continue

                neighbor_labels = defaultdict(int)

                for neighbor in neighbors:
                    if neighbor in current_labels and current_labels[neighbor]:
                        for label in current_labels[neighbor]:
                            neighbor_labels[label] += 1

                if neighbor_labels:
                    most_common_labels = [
                        label
                        for label, count in sorted(
                            neighbor_labels.items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )
                    ]
                    new_label_set = set(most_common_labels)
                else:
                    new_label_set = current_labels[protein]

                if current_labels[protein] != new_label_set:
                    changes += 1

                new_labels[protein] = new_label_set

            convergence_rate = changes / len(proteins)
            logger.info(
                f"Iteration {iteration + 1}: {changes} proteins changed labels ({convergence_rate:.4f})"
            )

            if convergence_rate < threshold:
                logger.info(f"Convergence reached after {iteration + 1} iterations")
                return (
                    {p: list(labels) for p, labels in new_labels.items()},
                    iteration + 1,
                    True,
                )

            current_labels = new_labels

        logger.info(f"Max iterations ({max_iterations}) reached without convergence")
        return (
            {p: list(labels) for p, labels in current_labels.items()},
            max_iterations,
            False,
        )

    def _calculate_confidence_scores(
        self, final_labels: Dict[str, List[str]], initial_labels: Dict[str, List[str]]
    ) -> Dict[str, float]:
        """Calculate confidence scores for predicted labels"""
        confidence_scores = {}

        for protein_id, labels in final_labels.items():
            if not labels:
                confidence_scores[protein_id] = 0.0
                continue

            if initial_labels.get(protein_id):
                confidence_scores[protein_id] = 1.0
            else:
                confidence_scores[protein_id] = 0.5

        return confidence_scores

    async def _update_protein_labels(
        self, final_labels: Dict[str, List[str]], attribute: str
    ):
        """Update protein labels in both databases"""
        for protein_id, labels in final_labels.items():
            await neo4j_service.update_protein_labels(protein_id, labels, attribute)

            protein = await mongodb_service.get_protein_by_id(protein_id)
            if protein:
                from app.models import Annotation, AnnotationType

                new_annotations = []
                for label in labels:
                    if attribute == "ec":
                        new_annotations.append(
                            Annotation(
                                annotation_type=AnnotationType.EC,
                                annotation_value=label,
                                evidence="label_propagation",
                            )
                        )
                    elif attribute == "go":
                        new_annotations.append(
                            Annotation(
                                annotation_type=AnnotationType.GO,
                                annotation_value=label,
                                evidence="label_propagation",
                            )
                        )

                await mongodb_service.update_protein_annotations(
                    protein_id, new_annotations
                )

    async def evaluate_propagation_quality(self, attribute: str) -> Dict[str, Any]:
        """Evaluate the quality of label propagation results"""
        proteins_data = await neo4j_service.get_proteins_for_label_propagation(
            attribute
        )

        initially_annotated = [p for p in proteins_data if p["labels"]]

        if not initially_annotated:
            return {"error": "No initially annotated proteins found for evaluation"}

        holdout_size = max(1, len(initially_annotated) // 5)
        holdout_proteins = random.sample(initially_annotated, holdout_size)

        modified_data = proteins_data.copy()
        for protein in holdout_proteins:
            for p in modified_data:
                if p["protein_id"] == protein["protein_id"]:
                    p["original_labels"] = p["labels"].copy()
                    p["labels"] = []
                    break

        graph = self._build_graph(modified_data)
        initial_labels = self._extract_initial_labels(modified_data, attribute)

        final_labels, _, _ = self._label_propagation(graph, initial_labels, 100, 0.01)

        correct_predictions = 0
        total_predictions = 0

        for protein in holdout_proteins:
            protein_id = protein["protein_id"]
            original_labels = set(protein["original_labels"])
            predicted_labels = set(final_labels.get(protein_id, []))

            if predicted_labels:
                total_predictions += 1
                if original_labels & predicted_labels:
                    correct_predictions += 1

        accuracy = (
            correct_predictions / total_predictions if total_predictions > 0 else 0
        )
        coverage = total_predictions / len(holdout_proteins)

        return {
            "holdout_size": len(holdout_proteins),
            "accuracy": accuracy,
            "coverage": coverage,
            "correct_predictions": correct_predictions,
            "total_predictions": total_predictions,
        }

    async def get_propagation_statistics(self, attribute: str) -> Dict[str, Any]:
        """Get statistics about label propagation for a specific attribute"""
        proteins_data = await neo4j_service.get_proteins_for_label_propagation(
            attribute
        )

        total_proteins = len(proteins_data)
        annotated_proteins = len([p for p in proteins_data if p["labels"]])
        unannotated_proteins = total_proteins - annotated_proteins

        all_labels = []
        for protein in proteins_data:
            all_labels.extend(protein.get("labels", []))

        label_counts = Counter(all_labels)
        most_common_labels = label_counts.most_common(10)

        avg_labels_per_protein = (
            len(all_labels) / annotated_proteins if annotated_proteins > 0 else 0
        )

        return {
            "attribute": attribute,
            "total_proteins": total_proteins,
            "annotated_proteins": annotated_proteins,
            "unannotated_proteins": unannotated_proteins,
            "annotation_rate": annotated_proteins / total_proteins
            if total_proteins > 0
            else 0,
            "unique_labels": len(label_counts),
            "most_common_labels": most_common_labels,
            "average_labels_per_protein": avg_labels_per_protein,
        }


label_propagation_service = LabelPropagationService()
