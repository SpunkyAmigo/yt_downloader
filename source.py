from yt_downloader import get_download_tasks_from_json, run_download_tasks


def main():
    tasks = get_download_tasks_from_json("configuration.json")
    results = run_download_tasks(tasks, max_workers=10)
    for result in results:
        print(result)
    print("Downloads completed.")


if __name__ == "__main__":
    main()
