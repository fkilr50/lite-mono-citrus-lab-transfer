import argparse
import os
from pathlib import Path

import cv2
import numpy as np
from rosbags.highlevel import AnyReader

# Strict topic filtering: extract only these two topics.
LEFT_RGB_TOPIC = "/zed2i/zed_node/left/image_rect_color"
DEPTH_TOPIC = "/zed2i/zed_node/depth/depth_registered"
ALLOWED_TOPICS = {LEFT_RGB_TOPIC, DEPTH_TOPIC}
SCRIPT_ROOT = Path(__file__).resolve().parent


def decode_sensor_image(msg):
    """Decode sensor_msgs/Image into a numpy array without altering numeric values."""
    encoding = msg.encoding.lower()
    height = int(msg.height)
    width = int(msg.width)
    step = int(msg.step)
    data = bytes(msg.data)

    encoding_map = {
        "rgb8": (np.uint8, 3),
        "bgr8": (np.uint8, 3),
        "rgba8": (np.uint8, 4),
        "bgra8": (np.uint8, 4),
        "mono8": (np.uint8, 1),
        "mono16": (np.uint16, 1),
        "16uc1": (np.uint16, 1),
        "16sc1": (np.int16, 1),
        "32fc1": (np.float32, 1),
    }

    if encoding not in encoding_map:
        raise RuntimeError(f"Unsupported image encoding: {msg.encoding}")

    dtype, channels = encoding_map[encoding]
    itemsize = np.dtype(dtype).itemsize
    elems_per_row = step // itemsize
    expected_elems = elems_per_row * height

    flat = np.frombuffer(data, dtype=dtype)
    if flat.size < expected_elems:
        raise RuntimeError(
            f"Image payload too short for {encoding}: got {flat.size} elems, expected {expected_elems}."
        )

    flat = flat[:expected_elems].reshape(height, elems_per_row)
    if channels == 1:
        img = flat[:, :width]
    else:
        img = flat[:, : width * channels].reshape(height, width, channels)

    # ROS image endianness is part of the message metadata.
    if int(msg.is_bigendian) == 1 and img.dtype.itemsize > 1:
        img = img.byteswap().newbyteorder()

    return img, encoding


def write_rgb_png(msg, output_filepath):
    """Save left RGB image strictly as lossless PNG."""
    img, encoding = decode_sensor_image(msg)

    if encoding == "rgb8":
        rgb_array = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif encoding == "rgba8":
        rgb_array = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif encoding == "bgra8":
        rgb_array = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif encoding == "bgr8":
        rgb_array = img
    else:
        raise RuntimeError(
            f"Left RGB topic has non-RGB encoding {msg.encoding}; expected rgb8/bgr8/rgba8/bgra8."
        )

    cv2.imwrite(f"{output_filepath}.png", rgb_array)


def write_depth_npz(msg, output_filepath):
    """Save depth map as raw numeric array without scaling/normalization."""
    depth_array, _ = decode_sensor_image(msg)
    if depth_array.dtype not in (np.float32, np.float64, np.uint16):
        raise RuntimeError(
            f"Depth dtype {depth_array.dtype} is unsupported; expected float32/float64/uint16."
        )
    np.savez_compressed(f"{output_filepath}.npz", arr_0=depth_array)


def output_path(output_folder, bag_name, topic, timestamp_ns):
    topic_folder = os.path.join(output_folder, topic.replace("/", "_").strip("_"))
    os.makedirs(topic_folder, exist_ok=True)
    filename_prefix = bag_name.replace(".", "_")
    output_filename = f"{filename_prefix}_{timestamp_ns}"
    return os.path.join(topic_folder, output_filename)


def extract_data_from_bag(bag_path, output_folder):
    with AnyReader([Path(bag_path)]) as reader:
        connections = [conn for conn in reader.connections if conn.topic in ALLOWED_TOPICS]

        if not connections:
            print(f"  No matching topics found in {os.path.basename(bag_path)}")
            return

        count = 0
        for connection, timestamp_ns, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, connection.msgtype)
            out = output_path(output_folder, os.path.basename(bag_path), connection.topic, timestamp_ns)

            if connection.topic == LEFT_RGB_TOPIC:
                write_rgb_png(msg, out)
            elif connection.topic == DEPTH_TOPIC:
                write_depth_npz(msg, out)
            
            count += 1
            if count % 50 == 0:
                print(f"    Extracted {count} messages...", end="\r")
        print(f"    Finished extracting {count} messages.          ")

def filter_rosbags(src_folder, prefixes_of_interest):
    rosbags_of_interest = []
    if not os.path.exists(src_folder):
        return []
    for filename in os.listdir(src_folder):
        for prefix in prefixes_of_interest:
            if filename.startswith(prefix) and filename.endswith(".bag"):
                rosbags_of_interest.append(filename)
                break
    return rosbags_of_interest


def resolve_local_path(path_str):
    path = Path(path_str)
    if path.is_absolute():
        return path
    return SCRIPT_ROOT / path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract data from rosbags.")
    parser.add_argument("src_folder", help="Source folder containing rosbags")
    parser.add_argument("output_folder", help="Output folder to save extracted data")
    args = parser.parse_args()

    src_folder = resolve_local_path(args.src_folder)
    output_folder = resolve_local_path(args.output_folder)

    # Keep original dataset naming convention: only process bag files starting with 'zed'.
    rosbag_prefixes_of_interest = ["zed"]
    rosbags_to_process = filter_rosbags(str(src_folder), rosbag_prefixes_of_interest)
    rosbags_to_process.sort()

    if not rosbags_to_process:
        print(f"No ZED bags found in {src_folder}")
        exit(1)

    print(f"Found {len(rosbags_to_process)} ZED bags to process.")

    for idx, bag_name in enumerate(rosbags_to_process, start=1):
        print(f"[{idx}/{len(rosbags_to_process)}] Processing bag: {bag_name}")
        
        # Skip check: if the first few frames of this bag already exist, skip it.
        prefix = bag_name.replace(".", "_")
        rgb_dir = os.path.join(str(output_folder), "zed2i_zed_node_left_image_rect_color")
        if os.path.exists(rgb_dir):
            existing = [f for f in os.listdir(rgb_dir) if f.startswith(prefix)]
            if len(existing) > 50:
                print(f"  Skipping (found {len(existing)} existing files).")
                continue

        bag_path = os.path.join(str(src_folder), bag_name)
        try:
            extract_data_from_bag(bag_path, str(output_folder))
        except Exception as e:
            print(f"  Error processing {bag_name}: {e}")
