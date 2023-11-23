import subprocess
import argparse
import os
import shutil
from PIL import Image
import imagehash
# To run this script, install all the imports. then do run python3 myScript.py -i VIDEOT_TITLE.mp4

# (can be realesr-animevideov3 | realesrgan-x4plus | realesrgan-x4plus-anime | realesrnet-x4plus)
# Fastest for anime is normally (realesr-animevideov3 with a 2x upscale factor.)
CURRENT_MODEL = 'realesr-animevideov3'
# Needs to be set to 4 for x4plus.
UPSCALE_FACTOR = "2"
# I'm just expirementing here. set this to default=1:2:2
THREAD_COUNT = '1:2:2' #f'{os.cpu_count()}:2:2'

def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.returncode, result.stdout, result.stderr

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()

# Used to determine if the last frame is the same as the current frame. 
# If the frames are the same, we skip rendering it, and copy the last frame instead.
def dhash_image(file_path):
    # Open the image and convert it to grayscale
    img = Image.open(file_path).convert('L')
    
    # Resize the image to a fixed size (e.g., 8x8) to create a hash
    img_hash = imagehash.dhash(img, hash_size=8)
    
    return str(img_hash)

# Helper function used to get frame rate automatically.
def calculate_framerate(frame_rate_str):
    # Example input: '640x480x1199/50'
    parts = frame_rate_str.split('x')

    if len(parts) == 3:
        fps_str = parts[2]
    else:
        raise ValueError("Unexpected format for frame rate string")

    fps_numerator, fps_denominator = fps_str.split('/')
    fps = int(fps_numerator) / int(fps_denominator)

    return fps

def get_video_metadata(input_video):
    ffprobe_command = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=avg_frame_rate,width,height', '-of', 'csv=s=x:p=0',
        input_video
    ]
    result = subprocess.run(ffprobe_command, capture_output=True, text=True, check=True)
    
    # Extracting the frame rate string from the output
    frame_rate_str = result.stdout.strip().split('\n')[0]
    
    # Calculate the frame rate
    fps = calculate_framerate(frame_rate_str)

    return str(fps)

def upscale_frame(input_frame, output_frame):
    #time ./realesrgan-ncnn-vulkan -i tmp_frames -o out_frames -n realesr-animevideov3 -s 2 -f jpg
    realesrgan_command = [
        './realesrgan-ncnn-vulkan', '-i', input_frame, '-o', output_frame,
        '-n', CURRENT_MODEL, '-s', UPSCALE_FACTOR, '-f', 'jpg'  
    ]
    _, realesrgan_stdout, realesrgan_stderr = run_command(realesrgan_command)

def main():
    parser = argparse.ArgumentParser(
        description='Process input and generate output video using ffmpeg and realesrgan-ncnn-vulkan.')
    parser.add_argument('-i', '--input', required=True,
                        help='Input video file')

    args = parser.parse_args()

    # Step 1: Create temporary directories
    print("Creating temporary directories...")
    # Remove any old directories from last rendering.
    run_command(['rm', '-rf', 'output.mp4'])
    run_command(['rm', '-rf', 'tmp_frames'])
    run_command(['rm', '-rf', 'out_frames'])
    #create new frame directory
    run_command(['mkdir', 'tmp_frames'])

    # Step 2: Extract frames from input video using ffmpeg
    print("Extracting frames from input video...")
    ffmpeg_command = [
        'ffmpeg', '-i', args.input, '-qscale:v', '1', '-qmin', '1', '-qmax', '1', '-vsync', '0',
        'tmp_frames/frame%08d.jpg'
    ]
    run_command(ffmpeg_command)

    # Step 3: Create output directory
    print("Creating output directory...")
    run_command(['mkdir', 'out_frames'])

    # Initialize variables for duplicate frame check
    previous_hash = None
    previous_output_frame = None

    # Step 4: Run realesrgan-ncnn-vulkan
    print("Running realesrgan-ncnn-vulkan...")
    frames_input = len(os.listdir('tmp_frames'))
    for i, input_frame in enumerate(sorted(os.listdir('tmp_frames'))):
        output_frame = os.path.join('out_frames', input_frame)

        # Check for duplicates using image hashing
        current_hash = dhash_image(os.path.join('tmp_frames', input_frame))

        # Check if the current input frame is the same as the previous
        if previous_hash and current_hash == previous_hash:
            shutil.copyfile(previous_output_frame, output_frame)
        else:
            # Upscale the current input frame
            upscale_frame(os.path.join('tmp_frames', input_frame), output_frame)
    
        # Update previous hash and output frame
        previous_hash = current_hash
        previous_output_frame = output_frame

        print_progress_bar(i + 1, frames_input, prefix='Progress (Upscaling):', suffix='Complete', length=50)

    # Step 5: Set the Framerate of the video we will render.
    print("Getting video metadata...")
    video_metadata = get_video_metadata(args.input)
    framerate = video_metadata  # Assuming the framerate is the first value returned

    # Step 6: Generate output video using ffmpeg with the obtained framerate
    print("Generating output video using ffmpeg...")
    frames_output = len(os.listdir('out_frames'))
    for i, frame in enumerate(os.listdir('out_frames')):
        print_progress_bar(i + 1, frames_output,
                        prefix='Progress (Generating Video):', suffix='Complete', length=50)

    final_ffmpeg_command = [
        'ffmpeg', '-framerate', framerate, '-i', 'out_frames/frame%08d.jpg', '-i', args.input,
        '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'copy', '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p', 'output.mp4'
    ]

    run_command(final_ffmpeg_command)

if __name__ == '__main__':
    main()