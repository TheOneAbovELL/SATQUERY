from app.domain.models import ImageAsset, ImageRelationshipAssessment, RelationshipType, AlignmentStatus, BoundingBox
from typing import List
from shapely.geometry import box
import rasterio.warp

class ImageRelationshipEngine:
    def assess(self, assets: List[ImageAsset]) -> ImageRelationshipAssessment:
        assessment = ImageRelationshipAssessment(
            relationship_types=[],
            alignment_status=AlignmentStatus.UNKNOWN
        )
        
        if len(assets) != 2:
            assessment.notes.append("Relationship engine currently supports exactly 2 assets.")
            assessment.relationship_types.append(RelationshipType.UNKNOWN)
            return assessment
            
        a1, a2 = assets[0], assets[1]
        
        # Determine temporal / modality
        if a1.acquisition_time and a2.acquisition_time and a1.acquisition_time != a2.acquisition_time:
            assessment.is_temporally_distinct = True
            assessment.relationship_types.append(RelationshipType.TEMPORAL_PAIR)
            
        if a1.modality != a2.modality and a1.modality != "UNKNOWN" and a2.modality != "UNKNOWN":
            assessment.is_cross_modal = True
            assessment.relationship_types.append(RelationshipType.CROSS_MODAL_PAIR)
            
        if not a1.geospatial_bounds or not a2.geospatial_bounds or not a1.crs or not a2.crs:
            assessment.notes.append("Missing geospatial bounds or CRS in one or both images.")
            assessment.alignment_status = AlignmentStatus.INCOMPATIBLE
            return assessment

        # Overlap analysis using Shapely
        try:
            b1 = a1.geospatial_bounds
            b2 = a2.geospatial_bounds
            geom1 = box(b1.min_x, b1.min_y, b1.max_x, b1.max_y)
            geom2 = box(b2.min_x, b2.min_y, b2.max_x, b2.max_y)

            if a1.crs != a2.crs:
                w, s, e, n = rasterio.warp.transform_bounds(
                    a2.crs, a1.crs, b2.min_x, b2.min_y, b2.max_x, b2.max_y
                )
                geom2 = box(w, s, e, n)

            intersection = geom1.intersection(geom2)
            
            if intersection.is_empty:
                assessment.relationship_types.append(RelationshipType.NON_OVERLAPPING)
                assessment.alignment_status = AlignmentStatus.INCOMPATIBLE
            else:
                area1 = geom1.area
                area2 = geom2.area
                inter_area = intersection.area
                
                assessment.overlap_percentage_a = (inter_area / area1) * 100
                assessment.overlap_percentage_b = (inter_area / area2) * 100
                
                minx, miny, maxx, maxy = intersection.bounds
                assessment.intersection_bounds_wgs84 = BoundingBox(
                    min_x=minx, min_y=miny, max_x=maxx, max_y=maxy
                )
                
                if assessment.overlap_percentage_a > 95 and assessment.overlap_percentage_b > 95:
                    assessment.relationship_types.append(RelationshipType.SPATIALLY_OVERLAPPING)
                else:
                    assessment.relationship_types.append(RelationshipType.PARTIALLY_OVERLAPPING)

                if a1.crs == a2.crs and a1.transform and a2.transform and a1.dimensions == a2.dimensions:
                    t1, t2 = a1.transform, a2.transform
                    is_aligned = all(abs(t1[i] - t2[i]) < 1e-6 for i in range(6))
                    if is_aligned:
                        assessment.alignment_status = AlignmentStatus.ALIGNED
                    else:
                        assessment.alignment_status = AlignmentStatus.REQUIRES_REGISTRATION
                else:
                    assessment.alignment_status = AlignmentStatus.REQUIRES_REGISTRATION
                    
        except Exception as e:
            assessment.notes.append(f"Spatial overlap analysis failed: {str(e)}")
            assessment.alignment_status = AlignmentStatus.UNKNOWN

        if not assessment.relationship_types:
            assessment.relationship_types.append(RelationshipType.SINGLE)

        return assessment
