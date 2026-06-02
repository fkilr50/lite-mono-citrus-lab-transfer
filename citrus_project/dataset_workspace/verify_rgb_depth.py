import numpy as np
import cv2
import matplotlib.pyplot as plt
import os

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Put the exact filename of ONE of your extracted pairs here
rgb_file = os.path.join(
    SCRIPT_ROOT,
    "extracted_rgbd",
    "zed2i_zed_node_left_image_rect_color",
    "zed_2023-07-18-14-26-49_0_bag_1689715609331936216.png",
)
depth_file = os.path.join(
    SCRIPT_ROOT,
    "extracted_rgbd",
    "zed2i_zed_node_depth_depth_registered",
    "zed_2023-07-18-14-26-49_0_bag_1689715609131019192.npz",
)


def verify_pair(rgb_path, depth_path):
    print(f"--- Verifying Data Pair ---")

    # 1. Check the RGB Image
    img = cv2.imread(rgb_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    print(f"RGB Shape: {img.shape} | Data Type: {img.dtype}")

    # 2. Check the Depth Map
    # Load the compressed numpy archive
    depth_data = np.load(depth_path)
    # Extract the array (we told the script to save it as 'arr_0')
    depth_array = depth_data["arr_0"]

    print(f"Depth Shape: {depth_array.shape} | Data Type: {depth_array.dtype}")
    print(
        f"Depth Math: Min distance = {np.nanmin(depth_array):.2f}, Max distance = {np.nanmax(depth_array):.2f}"
    )

    # 3. Visual Verification
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.title("Left RGB")
    plt.imshow(img)
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.title("Depth Map (Heatmap)")
    # We use a colormap to translate the math into visual colors (e.g., close is dark, far is bright)
    plt.imshow(depth_array, cmap="magma")
    plt.axis("off")

    plt.tight_layout()
    plt.show()


verify_pair(rgb_file, depth_file)
