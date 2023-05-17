"""
Reverse engineering of Google Bard
"""
from moviepy.video.VideoClip import TextClip
from moviepy.video.tools.subtitles import SubtitlesClip
from whisper.utils import write_srt
import whisper
from noneprompt import InputPrompt, ListPrompt, Choice
import openai
from bing_image_downloader import downloader
from moviepy.editor import *
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.fx.all import volumex

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx.all import resize
import moviepy.editor as mp
import pytube
import os
import argparse
from rich.traceback import install
import asyncio

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
import argparse
import json
import random
import re
import string
import os
import sys

import requests
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.markdown import Markdown

# Import either speak or speak2 from the custom_voice modules based on the user input


from feautures.custom_voice import speak


def __create_session() -> PromptSession:
    return PromptSession(history=InMemoryHistory())


def __create_completer(commands: list, pattern_str: str = "$") -> WordCompleter:
    return WordCompleter(words=commands, pattern=re.compile(pattern_str))


def __get_input(
    session: PromptSession = None,
    completer: WordCompleter = None,
    key_bindings: KeyBindings = None,
) -> str:
    """
    Multiline input function.
    """
    return (
        session.prompt(
            completer=completer,
            multiline=True,
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=key_bindings,
        )
        if session
        else prompt(multiline=True)
    )


class Chatbot:
    """
    A class to interact with Google Bard.
    Parameters
        session_id: str
            The __Secure-1PSID cookie.
    """

    __slots__ = [
        "headers",
        "_reqid",
        "SNlM0e",
        "conversation_id",
        "response_id",
        "choice_id",
        "session",
    ]

    def __init__(self, session_id):
        headers = {
            "Host": "bard.google.com",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://bard.google.com",
            "Referer": "https://bard.google.com/",
        }
        self._reqid = int("".join(random.choices(string.digits, k=4)))
        self.conversation_id = ""
        self.response_id = ""
        self.choice_id = ""
        self.session = requests.Session()
        self.session.headers = headers
        self.session.cookies.set("__Secure-1PSID", session_id)
        self.SNlM0e = self.__get_snlm0e()

    def __get_snlm0e(self):
        resp = self.session.get(url="https://bard.google.com/", timeout=10)
        # Find "SNlM0e":"<ID>"
        if resp.status_code != 200:
            raise Exception("Could not get Google Bard")
        SNlM0e = re.search(r"SNlM0e\":\"(.*?)\"", resp.text).group(1)
        return SNlM0e

    def ask(self, message: str) -> dict:
        """
        Send a message to Google Bard and return the response.
        :param message: The message to send to Google Bard.
        :return: A dict containing the response from Google Bard.
        """
        # url params
        params = {
            "bl": "boq_assistant-bard-web-server_20230419.00_p1",
            "_reqid": str(self._reqid),
            "rt": "c",
        }

        # message arr -> data["f.req"]. Message is double json stringified
        message_struct = [
            [message],
            None,
            [self.conversation_id, self.response_id, self.choice_id],
        ]
        data = {
            "f.req": json.dumps([None, json.dumps(message_struct)]),
            "at": self.SNlM0e,
        }

        # do the request!
        resp = self.session.post(
            "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
            params=params,
            data=data,
            timeout=120,
        )

        chat_data = json.loads(resp.content.splitlines()[3])[0][2]
        if not chat_data:
            return {"content": f"Google Bard encountered an error: {resp.content}."}
        json_chat_data = json.loads(chat_data)
        results = {
            "content": json_chat_data[0][0],
            "conversation_id": json_chat_data[1][0],
            "response_id": json_chat_data[1][1],
            "factualityQueries": json_chat_data[3],
            "textQuery": json_chat_data[2][0] if json_chat_data[2] is not None else "",
            "choices": [{"id": i[0], "content": i[1]} for i in json_chat_data[4]],
        }
        self.conversation_id = results["conversation_id"]
        self.response_id = results["response_id"]
        self.choice_id = results["choices"][0]["id"]
        self._reqid += 100000
        return results


if __name__ == "__main__":
    print(
        """
        Bard - A command-line interface to Google's Bard (https://bard.google.com/)
        Repo: github.com/acheong08/Bard

        Enter `alt+enter` or `esc+enter` to send a message.
        """,
    )
    console = Console()
    if os.getenv("BARD_QUICK"):
        session = os.getenv("BARD_SESSION")
        if not session:
            print("BARD_SESSION environment variable not set.")
            sys.exit(1)
        chatbot = Chatbot(session)
        # Join arguments into a single string
        MESSAGE = " ".join(sys.argv[1:])
        console.print(Markdown(chatbot.ask(MESSAGE)["content"]))
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--session",
        help="__Secure-1PSID cookie.",
        type=str,
        # Set the default PSID key here
        default="WgjYtRiUJt_JGxeSHfxa4Ul-uQ_XFnIG_o-A_cO1ZD4azWBOcpWgMnkdiTX-pWhnl7hgUA."
    )
    args = parser.parse_args()

    chatbot = Chatbot(args.session)
    prompt_session = __create_session()
    completions = __create_completer(["!exit", "!reset"])

    try:
        while True:
            console.print("You:")
            user_prompt = __get_input(
                session=prompt_session, completer=completions)
            console.print()
            if user_prompt == "!exit":
                break
            elif user_prompt == "!reset":
                chatbot.conversation_id = ""
                chatbot.response_id = ""
                chatbot.choice_id = ""
                continue
            print("Google Bard:")
            response = chatbot.ask(user_prompt)
            console.print(Markdown(response["content"]))
            print()

            top = input("images:")
            option = int(input("1 for g 2 for b:"))
            fish = input("output:")

            print("Please choose the video dimensions:")
            print("1. VIDEO_WIDTH = 854, VIDEO_HEIGHT = 480")
            print("2. VIDEO_WIDTH = 480, VIDEO_HEIGHT = 854")
            choice = input("Enter your choice (1 or 2): ")
            limit = int(input("limit of images :"))

            cd = response["content"]
            cop = f"{cd}"
            cop = cop.split('\n', 1)[1]
            cp = re.sub(r'[^\w\s]', '', cop)

            speak(cp)
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

                # Set the duration of each image

                # Set the path to the music file
            MUSIC_PATH = "data.mp3"
            # Replace spaces in title with hyphens
            # Download images of cats
            # Download images of cats
            from pygoogle_image import image as pi

            # Set the directory path to the folder containing the images
            import PIL

            IMAGE_PATHS = []
            if option == 1:
                for element in top.split(','):

                    pi.download(keywords=f'{element}', limit=limit)

                    # Replace spaces in title with hyphens
                    dog = element.replace(" ", "_")
                    folder_path = f"images/{dog}/"
                    if not os.path.exists(folder_path):
                        continue
                        # Get the file paths to all the images in the folder except the first two
                    for f in os.listdir(folder_path):
                        if f.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            image_path = os.path.join(folder_path, f)
                            with PIL.Image.open(image_path) as img:
                                width, height = img.size
                                if width > 80 and height > 36:
                                    IMAGE_PATHS.append(image_path)

            elif option == 2:
                for element in top.split(','):

                    downloader.download(f"{element}", limit=limit, output_dir="images",
                                        adult_filter_off=True, force_replace=False)

                    folder_path = f"images/{element}/"
                    if not os.path.exists(folder_path):
                        continue
                        # Get the file paths to all the images in the folder
                    image_paths = [os.path.join(folder_path, f) for f in os.listdir(
                        folder_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                    # Add the image paths to the list
                    IMAGE_PATHS += image_paths
            else:
                print("Invalid option entered. Please enter either 1 or 2.")

            num_images = len(IMAGE_PATHS)
            audio_clip = AudioFileClip(MUSIC_PATH)
            audio_duration = audio_clip.duration
            IMAGE_DURATION = audio_duration / num_images

            # Create a list of video clips
            # Set the blur amount
            # Create a list of video clips
            video_clips = []
            for image_path in IMAGE_PATHS:
                # Create an image clip for the current image
                image_clip = ImageClip(image_path)
                # Calculate the new height based on the aspect ratio of the original image
                new_height = int(
                    VIDEO_WIDTH / image_clip.w * image_clip.h)
                # Resize the image to fit the video dimensions without black bars
                image_clip = image_clip.resize(
                    (VIDEO_WIDTH, new_height))
                image_clip = image_clip.set_position(
                    ("center", "center"))
                image_clip = image_clip.set_duration(IMAGE_DURATION)

                # Create a black background clip
                bg_clip = ColorClip(
                    (VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0))
                bg_clip = bg_clip.set_duration(IMAGE_DURATION)

                # Combine the image clip with the background clip
                video_clip = CompositeVideoClip([bg_clip, image_clip])

                # Append the video clip to the list
                video_clips.append(video_clip)

                # Concatenate the video clips in a loop until the audio ends

            # Concatenate the video clips in a loop until the audio ends
             # Concatenate the video clips in a loop until the audio ends
            audio_clip = AudioFileClip(MUSIC_PATH)
            audio_duration = audio_clip.duration
            final_clip = concatenate_videoclips(
                video_clips, method="compose", bg_color=(0, 0, 0))
            final_clip = final_clip.set_duration(
                audio_duration).loop(duration=audio_duration)

            # Set the audio file for the final video clip
            final_clip = final_clip.set_audio(
                audio_clip.set_duration(final_clip.duration))

            # Set the audio file for the final video clip
            # Set the desired output file name
            filename = f"{fish}.mp4"

            # Check if the file already exists
            if os.path.isfile(filename):
                # If it does, add a number to the filename to create a unique name
                basename, extension = os.path.splitext(filename)
                i = 1
                while os.path.isfile(f"{basename}_{i}{extension}"):
                    i += 1
                filename = f"{basename}_{i}{extension}"

                # Write the video file with the updated filename
            final_clip.write_videofile(filename, fps=30)
            FONT = "Muroslant.otf"
            input_path = f"{fish}.mp4"
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
            final.write_videofile(final_path, fps=orig_video.fps)
            file_names = [f"{filename}"]
            for file_name in file_names:
                if os.path.exists(file_name):
                    os.remove(file_name)
                    print(f"File '{file_name}' deleted successfully.")
                else:
                    print(f"File '{file_name}' does not exist.")

    except KeyboardInterrupt:
        print("Exiting...")
