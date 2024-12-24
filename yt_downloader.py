import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal, Optional, Union

import yaml
import yt_dlp

__all__ = [
    "yt_downloader",
    "yt_audio_downloader",
    "yt_video_downloader",
    "run_download_tasks",
    "get_download_tasks_from_json",
    "get_download_tasks_from_yaml",
]


def yt_downloader(
    url: str,
    target_dir: Union[str, Path],
    only_audio: bool = False,
    quality: Literal["highest", "lowest"] = "highest",
    title: Optional[str] = None,
) -> Path:
    """
    Download video or audio from YouTube.

    Returns:
        Path: Path to the downloaded file

    Raises:
        ValueError: If the URL is invalid or empty
        Exception: For download-related errors
    """
    # Input validation
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    # Create target directories if they don't exist
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Prepare yt-dlp options
    ydl_opts = _prepare_download_options(target_dir, only_audio, quality, title)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info_dict = ydl.extract_info(url, download=True)

            # Multiple methods to find downloaded files
            downloaded_files = []

            # Method 1: Check requested_downloads
            if info_dict.get("requested_downloads"):
                downloaded_files = [
                    Path(download["filepath"])
                    for download in info_dict["requested_downloads"]
                    if "filepath" in download
                ]

            # Method 2: List files in target directory
            if not downloaded_files:
                downloaded_files = list(target_dir.glob("*"))

            # Method 3: Use filename from info_dict
            if not downloaded_files and "filename" in info_dict:
                potential_file = target_dir / info_dict["filename"]
                if potential_file.exists():
                    downloaded_files = [potential_file]

            # Validate and return the first downloaded file
            if not downloaded_files:
                raise Exception("No files were downloaded")

            # Find the most recently modified file if multiple exist
            if len(downloaded_files) > 1:
                downloaded_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            return downloaded_files[0]

    except Exception as e:
        raise Exception(f"Error downloading {url}: {str(e)}")


def _prepare_download_options(
    target_dir: Path,
    only_audio: bool,
    quality: Literal["highest", "lowest"],
    title: Optional[str] = None,
) -> dict:
    """
    Prepare download options for yt-dlp.

    Returns:
        dict: Configuration options for yt-dlp
    """

    config = dict()

    # Retry and timeout options
    config["retries"] = 10  # Number of retries for each download
    config["fragment_retries"] = 10  # Number of retries for each fragment
    config["socket_timeout"] = 30  # Timeout in seconds
    config["ignoreerrors"] = True  # Continue on download errors
    config["continuedl"] = True  # Continue partial downloads

    if only_audio:
        config["format"] = "bestaudio" if quality == "highest" else "worstaudio"
        config["outtmpl"] = (
            str(target_dir / f"{title}.%(ext)s")
            if title
            else str(target_dir / "%(title)s.%(ext)s")
        )
        config["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
        config["extract_audio"] = True
        config["keepvideo"] = False
    else:
        # Specify a single format to prevent multiple downloads
        config["format"] = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
            if quality == "highest"
            else "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]"
        )
        config["outtmpl"] = (
            str(target_dir / f"{title}.mp4")
            if title
            else str(target_dir / "%(title)s.mp4")
        )
        config["postprocessors"] = [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ]

    config["writesubtitles"] = False
    config["writeautomaticsub"] = False

    return config


def yt_audio_downloader(
    url: str,
    target_dir: str,
    quality: Literal["highest", "lowest"] = "highest",
    title: Optional[str] = None,
) -> Path:
    try:
        return yt_downloader(
            url,
            target_dir,
            only_audio=True,
            quality=quality,
            title=title,
        )
    except Exception as e:
        raise Exception(f"Error downloading {url}: {str(e)}")


def yt_video_downloader(
    url: str,
    target_dir: str,
    quality: Literal["highest", "lowest"] = "highest",
    title: Optional[str] = None,
) -> Path:
    try:
        return yt_downloader(
            url,
            target_dir,
            only_audio=False,
            quality=quality,
            title=title,
        )
    except Exception as e:
        raise Exception(f"Error downloading {url}: {str(e)}")


def _unified_download_tasks(download_config: dict) -> list[dict]:
    defaults = download_config.get(
        "defaults",
        {
            "quality": "lowest",
            "only_audio": False,
            "target_dir": "./downloads",
        },
    )
    urls = download_config.get("urls", [])

    # Process URLs into task dictionaries using defaults
    url_tasks = [{**defaults, "url": url} for url in urls]

    return url_tasks


def get_download_tasks_from_json(config_file: str = "configuration.json") -> list[dict]:
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return []

    return _unified_download_tasks(config)


def get_download_tasks_from_yaml(config_file: str = "configuration.yaml") -> list[dict]:
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return []

    return _unified_download_tasks(config)


def run_download_tasks(download_tasks: list[dict], max_workers: int = 10) -> list[dict]:
    """
    Download videos or audio from YouTube in parallel.
    """

    def download_task(task):
        try:
            result = {
                "url": task["url"],
                "path": yt_downloader(
                    url=task["url"],
                    target_dir=task.get("target_dir", "./downloads"),
                    only_audio=task.get("only_audio", True),
                    quality=task.get("quality", "highest"),
                    title=task.get("title"),
                ),
            }
            # Append successful download URL to 'downloads.txt'
            with open("downloads.txt", "a", encoding="utf-8") as f:
                f.write(f"{task['url']}\n")
            return result
        except Exception as e:
            return {"url": task["url"], "error": str(e)}

    # Limit the number of workers to the number of tasks
    max_workers = min(max_workers, len(download_tasks))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(download_task, download_tasks))
    return results
