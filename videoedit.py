from os.path import isfile
from aiogram.types import video
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import *
import os
import subprocess
import tempfile


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
        startingtime = timecodes.split(";")[0]
        endingtime = timecodes.split(";")[1]

        with VideoFileClip(video_path) as video:
            total_duration = video.duration

            start_seconds = parse_time(startingtime)
            end_seconds = parse_time(endingtime)

            if (
                start_seconds < 0
                or end_seconds > total_duration
                or start_seconds >= end_seconds
            ):
                raise ValueError(
                    f"Invalid timecodes. Video duration is {total_duration:.2f} seconds."
                )

            croppedvideo = video.subclip(start_seconds, end_seconds)

            output_path = f"./vids/output/{id}.mp4"
            croppedvideo.write_videofile(output_path)

    except Exception as e:
        print(f"Crop error: {e}")
        raise

    os.remove(video_path)
    return output_path


def speedupvideo(video_path, speed, id):
    output_path = f"./vids/output/{id}.mp4"
    spedupvideo = VideoFileClip(video_path).fx(vfx.speedx, speed)
    spedupvideo.write_videofile(output_path)
    spedupvideo.close()
    return output_path


def normalize_video(input_path, output_path, resolution, fps):
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-vf",
        f"scale={resolution[0]}:{resolution[1]}",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-y",
        output_path,
    ]
    subprocess.run(
        command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def mergevideos(videos_path, id):  # JESSE WE NEED TO WRAP JESSE
    output_path = f"./vids/output/{id}.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            videos_path[0],
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    width, height, fps_raw = probe.stdout.decode().splitlines()
    target_resolution = (int(width), int(height))
    num, den = map(int, fps_raw.split("/"))
    target_fps = num / den

    with tempfile.TemporaryDirectory() as tmpdir:
        normalized_paths = []
        for i, video in enumerate(videos_path):
            normalized = os.path.join(tmpdir, f"normalized_{i}.mp4")
            normalize_video(video, normalized, target_resolution, target_fps)
            normalized_paths.append(normalized)

        list_file_path = os.path.join(tmpdir, "concat_list.txt")
        with open(list_file_path, "w") as f:
            for path in normalized_paths:
                f.write(f"file '{path}'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file_path,
                "-c",
                "copy",
                output_path,
            ],
            check=True,
        )

    return output_path
