# YouTube video or audio downloader

## Installation

Tested on python 3.9

```bash
pip install -r requirements.txt
```

## Configuration

Create a `configuration.json`.

Example `configuration.json` file.

```json
{
  "defaults": {
    "quality": "highest",
    "only_audio": true,
    "target_dir": "./downloads"
  },
  "urls": [
    "https://www.youtube.com/watch?v=Fbcvu-ShANk",
    "https://www.youtube.com/watch?v=f0bNPpqAy-M",
    "https://www.youtube.com/watch?v=GUhb3MUA6PY"
  ]
}
```

## Running the script

```bash
python source.py
```

### What happens when you run the example source script

1. It would get configuration from `configuration.json`.
2. It would create the folders for `target_dir`.
3. Start downloads for the urls.
4. 10 parallel downloads at a time.
5. Audio files are downloaded as `mp3`.
6. As the files are downloaded they are appended to the `downloads.txt`.
7. The result is printed in `main()`.

### What if my configuration file is not right?

Make sure it follows the json or yaml format which you prefer.

The most important part is the urls. If that is empty then there will be no downloads.

And if the defaults are not right, it will not be an issue because further the defaults are hardcoded to the following:

```json
{
    "quality": "highest",
    "only_audio": true,
    "target_dir": "./downloads"
}
```

## Extra files

- `all_links.txt`: These are links of all the videos from https://www.youtube.com/@US_FDA/streams
- `downloads.txt`: The urls whose files are downloaded are appended here.
