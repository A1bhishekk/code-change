import requests

url = "https://github.com/bratsche/pango/raw/4de30e5500eaeb49f4bf0b7a07f718e149a2ed5e/pango/glyphstring.c"
response = requests.get(url)

if response.status_code == 200:
    with open("glyphstring.c", "wb") as file:
        file.write(response.content)
    print("File downloaded and saved as glyphstring.c")
else:
    print("Failed to download the file.")
