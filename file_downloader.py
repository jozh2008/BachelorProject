import os
import urllib.request

class FileDownloader:
    def __init__(self):
        # The FileDownloader class doesn't need initial parameters in this case
        pass

    def download_file(self, url, destination_folder):
        # Create the destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)

        # Extract the file name from the URL
        file_name = self.extract_file_name(url)

        # Construct the full path to the destination file
        destination_path = os.path.join(destination_folder, file_name)

        # Download the file
        urllib.request.urlretrieve(url, destination_path)

        print(f"File downloaded to: {destination_path}")
        return destination_path

    def extract_file_name(self, url):
        # Attempt to extract the file name from the URL
        try:
            file_name = url.split("/")[-1]
            return file_name
        except IndexError:
            # Handle the case where the URL format is unexpected
            raise ValueError("Unable to extract file name from the URL")

    def rename_file(self, old_path, new_name):
        # Rename the downloaded file
        new_path = os.path.join(os.path.dirname(old_path), new_name)

        os.rename(old_path, new_path)

        print(f"File renamed to: {new_path}")
        return new_path