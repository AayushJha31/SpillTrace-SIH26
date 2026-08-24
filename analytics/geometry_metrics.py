import numpy as np
from PIL import Image


def calculate_slick_geometry(mask_path, pixel_size_m=10):
    """
    Calculate oil-slick geometry from a binary segmentation mask.

    Parameters
    ----------
    mask_path : str
        Path to binary mask image.
        Slick pixels should be non-zero.

    pixel_size_m : float
        Ground resolution of one pixel in metres.

    Returns
    -------
    dict
        Slick area in m² and km²,
        centroid coordinates in pixel units,
        perimeter in metres.
    """

    # Load mask
    mask = np.array(Image.open(mask_path))

    # Convert to binary mask
    mask = mask > 0

    # Number of slick pixels
    slick_pixels = np.sum(mask)

    # -------------------------
    # 1. SLICK AREA
    # -------------------------
    pixel_area_m2 = pixel_size_m ** 2
    area_m2 = slick_pixels * pixel_area_m2
    area_km2 = area_m2 / 1_000_000

    # -------------------------
    # 2. CENTROID
    # -------------------------
    rows, cols = np.where(mask)

    if len(rows) == 0:
        raise ValueError("Mask contains no slick pixels.")

    centroid_row = np.mean(rows)
    centroid_col = np.mean(cols)

    # -------------------------
    # 3. PERIMETER
    # -------------------------
    # Count exposed edges of slick pixels.
    # Each exposed edge represents one pixel-size boundary.

    padded = np.pad(mask, 1, mode="constant", constant_values=False)

    exposed_edges = (
    (~padded[:-2, 1:-1]).astype(np.int32) +
    (~padded[2:, 1:-1]).astype(np.int32) +
    (~padded[1:-1, :-2]).astype(np.int32) +
    (~padded[1:-1, 2:]).astype(np.int32)
) * mask

    perimeter_pixels = np.sum(exposed_edges)
    perimeter_m = perimeter_pixels * pixel_size_m

    return {
        "slick_pixels": int(slick_pixels),
        "area_m2": float(area_m2),
        "area_km2": float(area_km2),
        "centroid_row": float(centroid_row),
        "centroid_col": float(centroid_col),
        "perimeter_m": float(perimeter_m)
    }


if __name__ == "__main__":

    # Example usage
    mask_path = "data/masks/example_mask.png"

    results = calculate_slick_geometry(
        mask_path,
        pixel_size_m=10
    )

    print("Slick Geometry")
    print("-------------------------")

    for key, value in results.items():
        print(f"{key}: {value}")