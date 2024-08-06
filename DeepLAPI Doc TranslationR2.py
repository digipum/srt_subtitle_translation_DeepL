import deepl
import requests
import time
import os
import shlex

auth_key = "DEEPLAPI KEY"  # Replace with your actual API key
translator = deepl.Translator(auth_key)

def count_characters(file_path):
    """Counts the number of characters in a text file.

    Args:
        file_path (str): The path to the text file.

    Returns:
        int: The number of characters in the file.

    Raises:
        FileNotFoundError: If the file is not found.
    """

    try:
        with open(file_path, "r") as file:
            return len(file.read())
    except FileNotFoundError:
        raise FileNotFoundError("File not found: {}".format(file_path))
    
# Function to upload and translate a document
def translate_document(file_path, target_lang, glossary_id=None):
    url = "https://api-free.deepl.com/v2/document"  # Adjust for Pro API if needed
    headers = {"Authorization": f"DeepL-Auth-Key {auth_key}"}

    with open(file_path, "rb") as file:
        files = {"file": file}
        data = {"target_lang": target_lang}
        if glossary_id:
            data["glossary_id"] = glossary_id

        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Raise an exception for error responses

        return response.json()

def check_translation_status(document_id, document_key):
    url = f"https://api-free.deepl.com/v2/document/{document_id}"  # Adjust for Pro API if needed
    headers = {"Authorization": f"DeepL-Auth-Key {auth_key}", "Content-Type": "application/json"}
    data = {"document_key": document_key}

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    return response.json()

def download_translated_document(document_id, document_key):
    url = f"https://api-free.deepl.com/v2/document/{document_id}/result"  # Adjust for Pro API if needed
    headers = {"Authorization": f"DeepL-Auth-Key {auth_key}", "Content-Type": "application/json"}
    data = {"document_key": document_key}

    DEFAULT_OUTPUT_DIR = os.getcwd() #Current directory
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

        # Get input file path to determine output directory
    input_filepath = os.path.abspath(os.path.join(".", file_path))  # Use relative path
    output_dirpath = os.path.dirname(input_filepath)


    # Construct output filename
    _, file_extension = os.path.splitext(file_path)
    output_filename = f"{os.path.basename(file_path)}_translated{file_extension}"

    with open(os.path.join(output_dirpath or DEFAULT_OUTPUT_DIR, output_filename), "wb") as file:
        file.write(response.content)

    return output_filename  # Return the saved filename for informative messages

DIRECT_SEND_LIMIT = 50000
# Example usage
while True:
    file_path = input("Enter the path to the document you want to translate (or 'q' to quit): ")

    if file_path.lower() == "q":
        break

    # Remove backslashes from the path
    file_path = file_path.replace('\\ ', ' ').strip()  # Replace backslashes with empty strings

    print (file_path)

    try:
        character_count = count_characters(file_path)

        if character_count <= DIRECT_SEND_LIMIT:
            # Read text directly and send without uploading
            with open(file_path, "r") as file:
                text = file.read()

                target_lang = input(f" {character_count} Enter the target language code (e.g., EN-US, KO, DE): ")

                #Additional Options
                preserve_formatting = True
                split_sentences = True

                options = {
                    #"preserve_formatting" : preserve_formatting,
                    #"split_sentences" : split_sentences
}

                translation = translator.translate_text(text, target_lang=target_lang, **options)

                # Get file name and extension separate
                file_name, file_extension = os.path.splitext(file_path)

                # Create new file name with "_translated" suffix
                new_file_path = f"{file_name}_{target_lang}{file_extension}"

                # Write translated text to the new file
                with open(new_file_path, "w") as output_file:
                    output_file.write(translation.text)

                print(f"Translated text written to: {new_file_path}")



        try:
            # Extract filename and directory from input path
            filename, _ = os.path.splitext(os.path.basename(file_path))
            output_path = os.path.join(os.path.dirname(file_path), f"{filename}_output{_}")

            target_lang = input("Enter the target language code (e.g., EN-US, KO, DE): ")

            document_info = translate_document(file_path, target_lang)
            document_id = document_info["document_id"]
            document_key = document_info["document_key"]


    
            # Use document_id and document_key to query translation status and download the translated document
            while True:
                status = check_translation_status(document_id, document_key)
                print(f"Translation status: {status['status']}")

                if status["status"] == "done":
                    translated_filename = download_translated_document(document_id, document_key)
                    print(f"Translated document saved to: {translated_filename}")
                    break
                elif status["status"] in ("queued", "translating"):
                    seconds_remaining = status.get("seconds_remaining", None)
                    if seconds_remaining:
                        print(f"Estimated time remaining: {seconds_remaining} seconds")
                    else:
                        print("Waiting for translation to start...")
                else:
                    print("Translation failed:", status.get("error_message", "Unknown error"))
                    break

                time.sleep(5)  # Check status every 5 seconds

        except (FileNotFoundError, ValueError) as e:
            print(e)

    except FileNotFoundError:
        print("File not found. Please enter a valid file path.")
