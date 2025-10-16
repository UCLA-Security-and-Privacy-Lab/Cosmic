import cv2
import numpy as np
import os
import argparse

def segment_image_grid(image_path, segment_height, output_dir=None):
    """
    Segment an image into horizontal strips of a specified height.
    
    Parameters:
    - image_path: Path to the input image
    - segment_height: Height for each segment
    - output_dir: Directory to save the segmented images (if None, segments aren't saved)
    
    Returns:
    - List of image segments as numpy arrays
    """
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image at {image_path}")
    
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Create output directory if it doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    segments = []
    
    # Iterate through the image in horizontal strips
    for y in range(0, height, segment_height):
        # Handle edge cases (when segment goes beyond image boundaries)
        end_y = min(y + segment_height, height)
        
        # Extract the segment (full width)
        segment = image[y:end_y, 0:width]
        
        # Check if this is the last segment and its height is less than segment_height
        if y + segment_height >= height and end_y - y < segment_height and segments:
            # Combine with the previous segment
            last_segment = segments.pop()
            combined_height = last_segment.shape[0] + segment.shape[0]
            combined_segment = np.vstack([last_segment, segment])
            segments.append(combined_segment)
            
            # Update the last saved segment if output directory is provided
            if output_dir:
                segment_name = f"segment_{len(segments)-1}.jpg"
                cv2.imwrite(os.path.join(output_dir, segment_name), combined_segment)
        else:
            segments.append(segment)
            
            # Save the segment if output directory is provided
            if output_dir:
                segment_name = f"segment_{len(segments)-1}.jpg"
                cv2.imwrite(os.path.join(output_dir, segment_name), segment)
    
    return segments

def parse_args():
    parser = argparse.ArgumentParser(description='Segment images from a folder into horizontal strips.')
    parser.add_argument('--input_folder', type=str, required=True, help='Path to the folder containing input images')
    # parser.add_argument('--segment_height', type=int, default=720, help='Height of each segment in pixels')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    input_folder = args.input_folder
    segment_height = 720
    
    # Create output directory in parent folder
    output_folder = os.path.join(os.path.dirname(input_folder), 'segmented_images')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Process all images in the input folder
    for image_file in os.listdir(input_folder):
        if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_image = os.path.join(input_folder, image_file)
            # Create subfolder for each image's segments
        
            image_output_folder = os.path.join(output_folder, os.path.splitext(image_file)[0])
            if not os.path.exists(image_output_folder):
                os.makedirs(image_output_folder)
            print(image_output_folder)
            segments = segment_image_grid(input_image, segment_height, image_output_folder)
            # print(f"Image {image_file} segmented into {len(segments)} horizontal strips of height {segment_height}")