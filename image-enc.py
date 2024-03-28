import base64
from PIL import Image
import json
import os 
import os
import platform
import time
from tqdm import tqdm

def clear_console():
    system = platform.system()
    if system == 'Windows':
        os.system('cls')
    elif system == 'Linux' or system == 'Darwin':  # Darwin is for macOS
        os.system('clear')
    else:
        # Fallback option for unknown systems
        print('\n' * 100)  # Print new lines to simulate clearing the console

def zip_to_base64(zip_filename):
    with open(zip_filename, "rb") as file:
        zip_data = file.read()
        encoded_zip = base64.b64encode(zip_data)
    return encoded_zip.decode()

def base64_to_binary(base64_data):
    decoded_data = base64.b64decode(base64_data)
    binary_data = ''.join(format(byte, '08b') for byte in decoded_data)
    return binary_data

def binary_to_image(binary_data, image_width=100, filename='binary_image_generated.png'):
    # Add padding to ensure complete image
    padding = image_width - (len(binary_data) % image_width)
    binary_data += '0' * padding

    # Calculate image dimensions
    image_height = len(binary_data) // image_width

    # Create image from binary data
    image = Image.new('1', (image_width, image_height))  # '1' for 1-bit pixels, black and white
    pixels = image.load()
    for i in range(image.width):
        for j in range(image.height):
            pixel_index = j * image_width + i
            if pixel_index < len(binary_data):
                pixel_value = int(binary_data[pixel_index])
                pixels[i, j] = pixel_value * 255  # Set pixel value (0 or 1) to black or white

    # Save image
    image.save(filename)
    return filename  # Return the filename of the generated image

def image_to_binary(image_file, threshold=128):
    # Open image file
    image = Image.open(image_file)

    # Convert image to binary data
    binary_data = ''
    pixels = list(image.getdata())
    for pixel in pixels:
        binary_data += '1' if pixel >= threshold else '0'

    return binary_data.rstrip('0')  # Remove padding after decoding

def binary_to_base64(binary_data):
    binary_data_padded = binary_data + '0' * (8 - len(binary_data) % 8)  # Pad binary data if needed
    byte_array = [int(binary_data_padded[i:i+8], 2) for i in range(0, len(binary_data_padded), 8)]
    encoded_data = base64.b64encode(bytes(byte_array))
    return encoded_data.decode()

def print_ascii_art():
    print("""

                                                   
                                                                - BY AR 
                                                                    Github @https://github.com/aritralegndery """)

def main():
    clear_console()
    while True:
        print_ascii_art()
        print("Welcome to the Secret File Encoder & Decoder!")
        print("Menu:")
        print("1. Encode a Secret File into an Image")
        print("2. Decode a Secret File from an Image")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ")
        if choice == '1':
            zip_filename = input("Enter the name of the secret file (e.g., 'secret.zip'): ")
            image_filename = input("Enter the name for the output image file (e.g., 'secret_image.png'): ")
            print("Encoding...")
            time.sleep(1)
            base64_data = zip_to_base64(zip_filename)
            binary_data = base64_to_binary(base64_data)
            image_filename = binary_to_image(binary_data, filename=image_filename)
            print(f"Secret file encoded, image generated, and saved as '{image_filename}'.")
            time.sleep(2)
            clear_console()
        elif choice == '2':
            image_file = input("Enter the name of the image file containing the secret (e.g., 'secret_image.png'): ")
            output_filename = input("Enter the name for the output secret file (e.g., 'recreated_secret.zip'): ")
            print("Decoding...")
            time.sleep(1)
            binary_data = image_to_binary(image_file)
            base64_data = binary_to_base64(binary_data)
            with open(output_filename, 'wb') as f:
                f.write(base64.b64decode(base64_data))
            print("Image decoded, secret file recreated, and saved.")
            time.sleep(2)
            clear_console()
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
