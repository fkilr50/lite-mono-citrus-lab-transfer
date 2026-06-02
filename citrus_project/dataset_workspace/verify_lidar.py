import numpy as np
import open3d as o3d
import os

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Replace with the exact filename of ONE of your extracted LiDAR npz files
lidar_file = os.path.join(
    SCRIPT_ROOT,
    "extracted_lidar",
    "velodyne_points",
    "base_2023-07-18-14-26-48_0_bag_1689715609165443992.npz",
)


def view_pointcloud_o3d(file_path):
    print("--- Loading True 1:1 LiDAR Point Cloud ---")

    # Load the compressed numpy archive
    data = np.load(file_path)["arr_0"]

    # Extract X, Y, Z
    pts_3d = data[:, :3]

    # Create an Open3D PointCloud object
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts_3d)

    # Optional: Color the points based on their height (Z-axis)
    # so trees stand out from the ground
    z_vals = pts_3d[:, 2]
    z_normalized = (z_vals - np.min(z_vals)) / (np.max(z_vals) - np.min(z_vals))

    # Apply a colormap (Blue for ground, Red/Yellow for high trees)
    import matplotlib.pyplot as plt

    cmap = plt.get_cmap("jet")
    colors = cmap(z_normalized)[:, :3]  # Drop the alpha channel
    pcd.colors = o3d.utility.Vector3dVector(colors)

    # Render the 3D environment
    print("Controls:")
    print(" - Left Click & Drag: Rotate camera")
    print(" - Right Click & Drag: Pan camera")
    print(" - Scroll Wheel: Zoom")
    o3d.visualization.draw_geometries(
        [pcd], window_name="Open3D LiDAR Viewer (1:1 Scale)", width=1280, height=720
    )


if __name__ == "__main__":
    if not os.path.exists(lidar_file):
        print(f"Error: Could not find {lidar_file}")
    else:
        view_pointcloud_o3d(lidar_file)
