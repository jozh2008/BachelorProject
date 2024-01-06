import os
import urllib.request

class FileDownloader:
    def __init__(self, url, destination_folder):
        self.url = url
        self.destination_folder = destination_folder

    def download_file(self):
        # Create the destination folder if it doesn't exist
        os.makedirs(self.destination_folder, exist_ok=True)

        # Extract the file name from the URL
        file_name = self.extract_file_name()

        # Construct the full path to the destination file
        destination_path = os.path.join(self.destination_folder, file_name)

        # Download the file
        urllib.request.urlretrieve(self.url, destination_path)

        print(f"File downloaded to: {destination_path}")
        return destination_path

    def extract_file_name(self):
        # Attempt to extract the file name from the URL
        try:
            file_name = self.url.split("/")[-1]
            return file_name
        except IndexError:
            # Handle the case where the URL format is unexpected
            raise ValueError("Unable to extract file name from the URL")


# Example usage:
# url = "https://training.galaxyproject.org/training-material/topics/metagenomics/tutorials/metatranscriptomics/workflows/main_workflow.ga"
# destination_folder = "Workflow"
# file_downloader = FileDownloader(url, destination_folder)
# downloaded_file_path = file_downloader.download_file()
