from aiogram.types import video
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import *
import os


def parse_time(time_str):
    """
    Convert time string to seconds
    Supports formats:
    - HH:MM:SS
    - MM:SS
    - SS
    """
    parts = time_str.split(":")
    if len(parts) == 3:
        # HH:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        # MM:SS
        return int(parts[0]) * 60 + float(parts[1])
    else:
        # SS
        return float(parts[0])


def cropvideo(video_path, timecodes, id) -> str:
    print(f"Cropping {video_path}")
    print(timecodes)

    try:
        # Parse start and end times
        startingtime = timecodes.split(";")[0]
        endingtime = timecodes.split(";")[1]

        # Load video to get total duration
        with VideoFileClip(video_path) as video:
            total_duration = video.duration

            # Convert timecodes to seconds
            start_seconds = parse_time(startingtime)
            end_seconds = parse_time(endingtime)

            # Validate timecodes
            if (
                start_seconds < 0
                or end_seconds > total_duration
                or start_seconds >= end_seconds
            ):
                raise ValueError(
                    f"Invalid timecodes. Video duration is {total_duration:.2f} seconds."
                )

            # Crop video
            croppedvideo = video.subclip(start_seconds, end_seconds)

            # Save cropped video
            output_path = f"./vids/output/{id}.mp4"
            croppedvideo.write_videofile(output_path)

    except Exception as e:
        print(f"Crop error: {e}")
        raise

    # Close clips and remove input video
    os.remove(video_path)
    return output_path


def speedupvideo(video_path, speed, id):
    output_path = f"./vids/output/{id}.mp4"
    spedupvideo = VideoFileClip(video_path).fx(vfx.speedx, speed)
    spedupvideo.write_videofile(output_path)
    spedupvideo.close()
    return output_path
