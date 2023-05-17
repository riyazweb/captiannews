import os
import pytube
import moviepy.editor as mp
from moviepy.video.fx.all import resize
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

from moviepy.audio.fx.all import volumex
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.all import resize
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.tools.subtitles import SubtitlesClip
from whisper.utils import write_srt
import whisper
from moviepy.editor import ImageClip


import yt_dlp


def download_video(video_link, filename):
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'outtmpl': f'{filename}.%(ext)s',
        # 'postprocessors': [{
        #     'key': 'FFmpegVideoConvertor',
        #     'preferedformat': 'mp4',
        # }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_link])


video_link = input("Enter the video URL: ")


output = input("Enter the out: ")

start_time = int(
    input("Enter the start time (in seconds) for the video segment: "))
choice = input("Enter your choice (1 or 2): ")


filename = f'{output}'


video_filename = f"{output}.webm"
download_video(video_link, filename)


print(f"Video saved as {video_filename}")

# Set the dimensions of the video
if choice == "1":
    VIDEO_WIDTH = 854
    VIDEO_HEIGHT = 480
    print("You chose VIDEO_WIDTH = 854 and VIDEO_HEIGHT = 480")
elif choice == "2":
    VIDEO_WIDTH = 480
    VIDEO_HEIGHT = 854
    print("You chose VIDEO_WIDTH = 480 and VIDEO_HEIGHT = 854")
else:
    print("Invalid choice. Please enter 1 or 2.")

# Split the video into 60-second segments and process each segment
# Split the video into 60-second segments and process each segment
video_clip = VideoFileClip(video_filename)
video_duration = video_clip.duration
for i in range(0, int(video_duration)-start_time, 60):
    start = i + start_time
    end = min(start + 60, video_duration)
    video_segment = video_clip.subclip(start, end)
    # do something with the video segment

    #

    # Resize the segment clip
    resized_clip = resize(
        video_segment, width=1150)

    # Create a blank clip with the target dimensions
    background_clip = ColorClip((VIDEO_WIDTH, VIDEO_HEIGHT), color=[
                                0, 0, 0], duration=resized_clip.duration)

    # Place the resized video clip at the center of the blank clip
    x_pos = (VIDEO_WIDTH - resized_clip.w) / 2
    y_pos = (VIDEO_HEIGHT - resized_clip.h) / 2
    video_clip_centered = CompositeVideoClip(
        [background_clip, resized_clip.set_pos((x_pos, y_pos))])

    # Combine the image clips and video clip
    final_clip = CompositeVideoClip([video_clip_centered])

    # Concatenate the voice clip and video clip audio
    final_audio_clip = mp.concatenate_audioclips([video_segment.audio])

    # Combine the video clip and audio clip
    final_clip = final_clip.set_audio(final_audio_clip)

    # Save the final video file

    # Check if the file already exists
    output_filename = f'{output}.mp4'
    # Check if the file already exists
    if os.path.isfile(output_filename):
        # If it does, add a number to the filename to create a unique name
        basename, extension = os.path.splitext(output_filename)
        i = 1
        while os.path.isfile(f"{basename}_{i}{extension}"):
            i += 1
        output_filename = f"{basename}_{i}{extension}"

    final_clip.write_videofile(output_filename)
    FONT = "Muroslant.otf"
    input_path = f"{output}.mp4"
    print("Transcribing audio...")
    model = whisper.load_model("base")
    result = model.transcribe(input_path, verbose=False)

    subtitle_path = os.path.splitext(input_path)[0] + ".srt"
    with open(subtitle_path, "w", encoding="utf-8") as srt_file:
        write_srt(result["segments"], file=srt_file)

    print("Generating subtitles...")
    orig_video = VideoFileClip(input_path)

    def generator(txt): return TextClip(txt,
                                        font=FONT if FONT else "Courier",
                                        fontsize=48,
                                        color='white',
                                        size=orig_video.size,
                                        method='caption',
                                        align='center',)
    subs = SubtitlesClip(subtitle_path, generator)

    print("Compositing final video...")
    final = CompositeVideoClip(
        [orig_video, subs.set_position('center', 'middle')])
    final_path = os.path.splitext(input_path)[0] + "_final.mp4"
    if os.path.isfile(final_path):
        # If it does, add a number to the filename to create a unique name
        basename, extension = os.path.splitext(final_path)
        i = 1
        while os.path.isfile(f"{basename}_{i}{extension}"):
            i += 1
        final_path = f"{basename}_{i}{extension}"
    final.write_videofile(final_path, fps=orig_video.fps)

    file_names = [f"{output_filename}"]

    for file_name in file_names:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"File '{file_name}' deleted successfully.")
        else:
            print(f"File '{file_name}' does not exist.")
