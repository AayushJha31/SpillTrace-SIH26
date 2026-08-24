import numpy as np
from PIL import Image
from geometry_metrics import calculate_slick_geometry


# 2 x 2 square mask
# Pixel size = 10 m
#
# 1 1
# 1 1
#
# Expected:
# Area = 4 × 100 = 400 m²
# Centroid = (0.5, 0.5)
# Perimeter = 8 × 10 = 80 m

mask = np.array([
    [1, 1],
    [1, 1]
], dtype=np.uint8)

mask_path = "test_mask.png"

Image.fromarray(mask).save(mask_path)


results = calculate_slick_geometry(
    mask_path,
    pixel_size_m=10
)

print("Geometry Test Results")
print("---------------------")

for key, value in results.items():
    print(f"{key}: {value}")


# Validation
assert results["slick_pixels"] == 4
assert results["area_m2"] == 400
assert results["area_km2"] == 0.0004
assert results["centroid_row"] == 0.5
assert results["centroid_col"] == 0.5
assert results["perimeter_m"] == 80

print("\nALL TESTS PASSED")