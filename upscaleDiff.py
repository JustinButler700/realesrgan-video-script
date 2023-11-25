# Justin Butler 11/24/2023
from PIL import Image, ImageChops, ImageFilter
import subprocess

# This is a test python script.
# The idea of this, is to save compute in the AI upscaling process by only upscaling
#  the difference between two frames of animation, rather than the whole frame.

# For Example:  Someone smiles between frame 1 and frame 2.
# Then This will output a png of a smile as changed_region.png
# Then changed_region.png will be upscaled.
# Then upscaled_changed_region.png will be appended onto the original frame which will
# Produce a result which looks like frame 2\.

# Open the two images you want to compare
image1 = Image.open("image1.jpg").convert("RGBA")
image2 = Image.open("image2.jpg").convert("RGBA")

# Ensure the images have the same size
if image1.size != image2.size:
    raise ValueError("The images must have the same dimensions")

# Get the absolute difference between the two images
diff_image = ImageChops.difference(image1, image2)

# Convert the difference image to grayscale
diff_image = diff_image.convert("L")

# Set a threshold for what is considered a significant difference 
threshold = 30

# Create a mask where differences are above the threshold
diff_mask = diff_image.point(lambda p: p > threshold and 255)

# Define the radius for dilation
radius = 9  # Adjust this value as needed

# Apply dilation to the difference mask to include a larger area around differences
dilated_diff_mask = diff_mask.filter(ImageFilter.MaxFilter(size=radius))

# Ensure both images have the same mode and alpha channel
image1 = image1.convert("RGBA")
changed_region = Image.new("RGBA", image2.size, (0, 0, 0, 0))
changed_region.paste(image2, mask=dilated_diff_mask)
# Save the result as a PNG file
changed_region.save("changed_region.png")

# Execute the external script
subprocess.run(["./realesrgan-ncnn-vulkan", "-i", "changed_region.png", "-o", "output1.png", "-n", "realesr-animevideov3"])

# Open the output image from the external script
output_image = Image.open("output1.png").convert("RGBA")

# Resize the output image to match the size of image1
output_image = output_image.resize(image1.size)

# Create a new image with the changed region blended on top of image1 using the resized output image
image1_composite_alpha = Image.alpha_composite(image1, output_image)
image1_composite_alpha.save("image1_composite_alpha.png")
