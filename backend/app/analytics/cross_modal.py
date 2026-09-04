import time
from typing import Dict, Any, List, Optional
from shapely.geometry import box

from app.domain.models import EvidenceRelationship, EvidenceItem, AssetModality
from app.services.relationship_engine import ImageRelationshipEngine

class CrossModalAnalyzer:
    """
    Computes deterministic spatial intersections of evidence regions returned by different specialist tools.
    """
    def __init__(self):
        self.relationship_engine = ImageRelationshipEngine()

    def compare_evidence(self, optical_evidence: EvidenceItem, sar_evidence: EvidenceItem) -> Dict[str, Any]:
        """
        Determines the relationship between optical and SAR evidence by intersecting their spatial artifacts.
        """
        # If either has no artifacts, we cannot spatially agree on a region.
        if not optical_evidence.spatial_artifacts and not sar_evidence.spatial_artifacts:
            # Maybe they both agree there is NO change/signal?
            if optical_evidence.metrics.get("region_count", 0) == 0 and sar_evidence.metrics.get("region_count", 0) == 0:
                return {
                    "relationship": EvidenceRelationship.AGREEMENT,
                    "metrics": {"iou": 1.0, "intersection_area": 0.0},
                    "explanation": "Both modalities report no significant regions.",
                    "provenance": ["AGREEMENT: Both optical and SAR detected 0 regions."]
                }
            return {
                "relationship": EvidenceRelationship.INCONCLUSIVE,
                "metrics": {"iou": 0.0, "intersection_area": 0.0},
                "explanation": "Insufficient spatial artifacts for comparison.",
                "provenance": ["INCONCLUSIVE: No spatial regions returned by one or both modalities."]
            }

        if not optical_evidence.spatial_artifacts:
            return {
                "relationship": EvidenceRelationship.DISAGREEMENT, # or COMPLEMENTARY based on context
                "metrics": {"iou": 0.0, "intersection_area": 0.0},
                "explanation": "SAR detected regions, but Optical detected none.",
                "provenance": ["DISAGREEMENT: Optical regions=0, SAR regions>0."]
            }

        if not sar_evidence.spatial_artifacts:
            return {
                "relationship": EvidenceRelationship.DISAGREEMENT,
                "metrics": {"iou": 0.0, "intersection_area": 0.0},
                "explanation": "Optical detected regions, but SAR detected none.",
                "provenance": ["DISAGREEMENT: Optical regions>0, SAR regions=0."]
            }

        # Compare top region from each for this demo, or aggregate all bounding boxes
        # We will create a MultiPolyon or single large polygon bounds for simplicity
        opt_geom = self._merge_bboxes(optical_evidence.spatial_artifacts)
        sar_geom = self._merge_bboxes(sar_evidence.spatial_artifacts)

        intersection = opt_geom.intersection(sar_geom)
        union = opt_geom.union(sar_geom)

        intersection_area = intersection.area
        union_area = union.area
        iou = intersection_area / union_area if union_area > 0 else 0.0

        provenance = [
            f"Optical geometry area (pixel squared): {opt_geom.area}",
            f"SAR geometry area (pixel squared): {sar_geom.area}",
            f"Intersection area: {intersection_area}",
            f"Union area: {union_area}",
            f"IoU: {iou:.4f}"
        ]

        if iou > 0.1:
            relationship = EvidenceRelationship.AGREEMENT
            explanation = "Significant spatial overlap exists between optical and SAR evidence regions."
            provenance.append("AGREEMENT: IoU > 0.1")
        elif iou > 0.0:
            relationship = EvidenceRelationship.COMPLEMENTARY
            explanation = "Minor spatial overlap. Signals are largely adjacent or disjoint."
            provenance.append("COMPLEMENTARY: 0 < IoU <= 0.1")
        else:
            relationship = EvidenceRelationship.DISAGREEMENT
            explanation = "Evidence regions are completely disjoint."
            provenance.append("DISAGREEMENT: IoU == 0")

        return {
            "relationship": relationship,
            "metrics": {
                "iou": iou,
                "intersection_area": intersection_area,
                "optical_area": opt_geom.area,
                "sar_area": sar_geom.area
            },
            "explanation": explanation,
            "provenance": provenance
        }

    def _merge_bboxes(self, artifacts: List[Dict[str, Any]]):
        """
        Creates a Shapely geometry representing the union of all bounding boxes in the artifact list.
        Using pixel coordinates (row, col) as (y, x).
        """
        from shapely.ops import unary_union
        polys = []
        for a in artifacts:
            if "bbox" in a:
                b = a["bbox"]
                # Create box: (minx, miny, maxx, maxy) -> (col_min, row_min, col_max, row_max)
                polys.append(box(b.get("col_min", 0), b.get("row_min", 0), 
                                 b.get("col_max", 0), b.get("row_max", 0)))
        if not polys:
            return box(0,0,0,0)
        return unary_union(polys)
