import os
import urllib.request


class FileDownloader:
    def __init__(self):
        """
        Initialize the FileDownloader class.
        """
        # The FileDownloader class doesn't need initial parameters in this case
        pass

    def download_file(self, url, destination_folder):
        """
        Download a file from the given URL and save it to the specified destination folder.

        Args:
            url (str): The URL of the file to be downloaded.
            destination_folder (str): The folder where the downloaded file will be saved.

        Returns:
            str: The full path to the downloaded file.
        """
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
        """
        Extract the file name from a given URL.

        Args:
            url (str): The URL from which to extract the file name.

        Returns:
            str: The extracted file name.
        Raises:
            ValueError: If the file name cannot be extracted from the URL.
        """
        # Attempt to extract the file name from the URL
        try:
            file_name = url.split("/")[-1]
            return file_name
        except IndexError:
            # Handle the case where the URL format is unexpected
            raise ValueError("Unable to extract file name from the URL")

    def rename_file(self, old_path, new_name):
        """
        Rename a file located at the old path to the new name.

        Args:
            old_path (str): The current path of the file.
            new_name (str): The new name for the file.

        Returns:
            str: The full path to the renamed file.
        """
        # Rename the downloaded file
        new_path = os.path.join(os.path.dirname(old_path), new_name)

        os.rename(old_path, new_path)

        print(f"File renamed to: {new_path}")
        return new_path
