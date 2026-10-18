from dataclasses import dataclass


@dataclass(frozen=True)
class SpatialRelation:
    horizontal_gap: float
    vertical_gap: float
    is_right_of: bool
    is_nearby: bool


def compare_boxes(
    label_box: list[int],
    value_box: list[int],
    max_distance: float = 40,
) -> SpatialRelation:
    lx1, ly1, lx2, ly2 = label_box
    vx1, vy1, vx2, vy2 = value_box

    horizontal_gap = max(0, vx1 - lx2)
    vertical_gap = max(0, max(ly1, vy1) - min(ly2, vy2))

    is_right_of = vx1 >= lx2
    is_nearby = (
        horizontal_gap <= max_distance
        and vertical_gap <= max_distance
    )

    return SpatialRelation(
        horizontal_gap=horizontal_gap,
        vertical_gap=vertical_gap,
        is_right_of=is_right_of,
        is_nearby=is_nearby,
    )