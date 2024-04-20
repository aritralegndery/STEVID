#from __future__ import print_function
###sike
from PIL import Image
import binascii
from tqdm import tqdm
from bitstring import BitArray

# for creating gifs
import imageio

# for file stuff
import os
import sys

# for deleting folders
from shutil import rmtree

four_k = (3840, 2160)
HD = (1920, 1080)

# encoding...
# 0 is black pixel, white is 1
import cv2
import os



# writes a gif in parent_folder made up of all its sorted .png files
def make_gif(parent_folder, fname):
    items = os.listdir(parent_folder)
    png_filenames = []
    for elem in items:
        if elem.find(".png") != -1:
            png_filenames.append(elem)

    sorted_png = []
    while True:
        lowest = 10000000
        lowest_idx = -1
        for p in png_filenames:
            val = int(p.split("-")[1].split(".")[0])
            if lowest_idx == -1 or val < lowest:
                lowest = val
                lowest_idx = png_filenames.index(p)
        sorted_png.append(png_filenames[lowest_idx])
        del png_filenames[lowest_idx]
        if len(png_filenames) == 0:
            break
    png_filenames = sorted_png

    with imageio.get_writer(fname + ".gif", mode='I', duration=0.1) as writer:
        for filename in png_filenames:
            image = imageio.imread(parent_folder + "/" + filename)
            writer.append_data(image)
    return fname + ".gif"


# provided a list of pixels, writes it out as an image
# with the specified resolution
def pixels_2_png(pixels, fname, reso=(3840, 2160)):
    img = Image.new('RGB', reso)
    img.putdata(list(tqdm(pixels, desc="Processing pixels", total=len(pixels))))
    img.save(fname)
    print("pixels_2_png: Saved %d pixels to %s" % (len(pixels), fname))


# provided a filename, reads the png and returns a list of pixels
def png_2_pixels(fname):
    im = Image.open(fname)
    pixel_list = []
    pixels = im.load()
    width, height = im.size
    total_pixels = width * height
    for row in tqdm(range(height), desc="Reading pixels", total=height):
        for col in range(width):
            pixel_list.append(pixels[col, row])
    print("png_2_pixels: Read %d pixels from %s" % (len(pixel_list), fname))
    return pixel_list


# writes out the bits as binary to a file
def bits_2_file(bits, fname):
    with open(fname, 'wb') as f:
        idx = 0
        inc = 8
        total_bits = len(bits)
        with tqdm(total=total_bits, desc="Writing Bits to File", unit="bit") as pbar:
            while True:
                char = ''.join(bits[idx:idx + inc])
                f.write(bytes([int(char, 2)]))
                idx += inc
                pbar.update(inc)
                if idx >= total_bits:
                    break
    print("bits_2_file: Wrote %d bits to %s" % (total_bits, fname))

def file_2_bits(fname):
    bits = []
    try:
        with open(fname, "rb") as f:
            total_bytes = os.path.getsize(fname)
            with tqdm(total=total_bytes, desc="Converting File to Bits", unit="byte") as pbar:
                byte = f.read(1)
                while byte:
                    cur_bits = bin(ord(byte))[2:]
                    while len(cur_bits) < 8:
                        cur_bits = "0" + cur_bits
                    for b in cur_bits:
                        bits.append(b)
                    byte = f.read(1)
                    pbar.update(1)
    except FileNotFoundError:
        print("Error: File '{}' not found.".format(fname))
    except PermissionError:
        print("Error: Permission denied to access file '{}'.".format(fname))
    except Exception as e:
        print("An error occurred while reading the file '{}': {}".format(fname, str(e)))
    else:
        print("file_2_bits: Read {} bits from {}".format(len(bits), fname))
    return bits


# converts a list of 0/1 bits to pixels

def bits_2_pixels(bits):
    pixels = []

    with tqdm(total=len(bits), desc="Converting Bits to Pixels", unit="bit") as pbar:
        for b in bits:
            pixels.append((0, 0, 0) if b == '0' else (255, 255, 255))
            pbar.update(1)

    print("bits_2_pixels: Converted %d bits to %d pixels" % (len(bits), len(pixels)))
    return pixels


def pixels_2_bits(pixels):
    bits = []

    with tqdm(total=len(pixels), desc="Converting Pixels to Bits", unit="pixel") as pbar:
        for p in pixels:
            if p == (0, 0, 0):
                bits.append('0')
            else:
                bits.append('1')
            pbar.update(1)

    print("pixels_2_bits: Converted %d pixels to %d bits" % (len(pixels), len(bits)))
    return bits


# adds the file name header to the list of bits
def add_header(bits, fname):
    # filename encoded as ascii --> binary
    fname_bitstr = bin(int(binascii.hexlify(fname.encode()), 16))

    # extra 2 bytes (16 bits) before header tells how long header is (in bits)
    fname_bitstr_length_bitstr = "{0:b}".format(len(fname_bitstr) - 2)

    while len(fname_bitstr_length_bitstr) < 16:
        fname_bitstr_length_bitstr = "0" + fname_bitstr_length_bitstr

    # length header to tell how long the rest of the header is, as
    # well as the header itself
    fname_headers = fname_bitstr_length_bitstr + fname_bitstr[2:]

    # converting the string header to a list
    header_list = []
    for char in fname_headers:
        header_list.append(char)

    # secondary header after filename to tell how many bits the payload is
    # length of secondary header is 64 bits to allow for massive payload sizes
    payload_length_header = "{0:b}".format(len(bits))

    while len(payload_length_header) < 64:
        payload_length_header = "0" + payload_length_header

    # append the secondary header to the main header
    for char in payload_length_header:
        header_list.append(char)

    total_header_length = len(header_list)

    # append the original bits onto the header and return
    header_list.extend(bits)
    return header_list


# takes in the bits, decodes the header into a filename.
# returns the filename, as well as the rest of the bits
# after the header section
def decode_header(bits):
    # helper function, converts a binary string (eg. '10101') to ASCII characters
    def decode_binary_string(s):
        return ''.join(chr(int(s[i * 8:i * 8 + 8], 2)) for i in range(len(s) // 8))

    # first 16 bits store the length of the filename (in bits)
    fname_length_binstr = ''.join(bits[:16])

    # converting filename length to integer
    fname_length = int(fname_length_binstr, 2)

    # next fname_length bits are the ASCII filename
    fname_binstr = ''.join(bits[16:16 + fname_length])
    fname_binstr = "0" + fname_binstr

    # convert the fname bitstring to ASCII
    fname = decode_binary_string(fname_binstr)

    # now need to decode the size of the payload
    payload_length_binstr = ''.join(bits[16 + fname_length:16 + fname_length + 64])

    # convert the payload length to integer
    payload_length = int(payload_length_binstr, 2)

    return fname, bits[16 + fname_length + 64:16 + fname_length + 64 + payload_length]


# provided two lists of bits, ensures both are identical,
# if not, reports the difference
def test_bit_similarity(bits1, bits2):
    if len(bits1) != len(bits2):
        print("Bit lengths are not the same!")
        return
    for b1, b2 in zip(bits1, bits2):
        if b1 != b2:
            print("Bits are not the same!")
            return
    print("Bits are identical")


# provided a relative path, deletes the folder then creates new version
# under the same name
def clear_folder(relative_path):
    try:
        rmtree(relative_path)
        
    except:
        print("WARNING: Could not locate /temp directory.")

    for i in range(10):
        try:
            os.mkdir(relative_path)
            break
        except:
            continue


# - provided a source file, encodes it into a .gif video
# - all .png's created in the process are held in the /temp directory
def encode(src, res=four_k):
    bits = file_2_bits(src)
    bits = add_header(bits, src.split("/")[-1])
    pixels = bits_2_pixels(bits)

    # get the total number of pixels in a single image
    pixels_per_image = res[0] * res[1]

    # get the number of images required to hold entire file
    num_imgs = int(len(pixels) / pixels_per_image) + 1

    print("encode: Encoding will require %d .png frames" % num_imgs)

    # filename without any path specifiers
    name_clean = src.split("/")[-1]

    # clear the /temp folder
    #clear_folder("temp")

    # create each of the png's
    for i in range(num_imgs):
        cur_temp_name = "temp/" + name_clean + "-" + str(i) + ".png"
        cur_start_idx = i * pixels_per_image
        cur_span = min(pixels_per_image, len(pixels) - cur_start_idx)
        cur_pixels = pixels[cur_start_idx:cur_start_idx + cur_span]
        pixels_2_png(cur_pixels, cur_temp_name)
        if cur_span < pixels_per_image:
            break

    # create gif from png sequence
    gif_name = make_gif("temp", name_clean)
    return gif_name


# - provided a source .gif, decodes it back into the original file
def decode(src):
    # helper function to allow for iteration over .png's inside .gif
    def iter_frames(im):
        try:
            i = 0
            while 1:
                im.seek(i)
                imframe = im.copy()
                imframe = imframe.convert('RGB')
                yield imframe
                i += 1
        except EOFError:
            pass

    # load .gif
    im = Image.open(src)

    # save each frame individually
    saved_frames = []
    for i, frame in enumerate(iter_frames(im)):
        cur_frame = "temp/frame-%d.png" % i
        saved_frames.append(cur_frame)
        frame.save(cur_frame, **frame.info)

    print("decode: Identified %d .png frames" % len(saved_frames))

    # convert each png to pixels
    pixels = []
    for s in saved_frames:
        cur_pixels = png_2_pixels(s)
        pixels.extend(cur_pixels)

    # convert all pixels to bits
    bits = pixels_2_bits(pixels)

    # decode the filename
    fname, bits = decode_header(bits)

    # write out the file
    bits_2_file(bits, fname.split(".")[0] + "-recovered." + fname.split(".")[1])


# test to ensure that conversion works and the original file is recoverable.
# only uses a single .png image (input file must be < 1MB)
def conversion_test():
    src_f = "data/test.jpg"
    src_f_cln = "test.jpg"
    img_f = "data/image.png"

    # converting file to png...
    test_f_bits = file_2_bits(src_f)
    orig_bits = test_f_bits
    test_f_bits = add_header(test_f_bits, src_f_cln)
    pixels = bits_2_pixels(test_f_bits)
    pixels_2_png(pixels, img_f)

    # converting png back to file...
    pixels = png_2_pixels(img_f)
    bits = pixels_2_bits(pixels)
    fname, bits = decode_header(bits)
    bits_2_file(bits, src_f.split(".")[0] + "-copy." + src_f_cln.split(".")[1])

    # testing to see if recovered bits are identical to original
    test_bit_similarity(orig_bits, bits)


def main():
    #encode("input.zip")
    
    
    #clear_folder("temp")
    decode('output_gif.zip.gif')

    #conversion_test()


if __name__ == '__main__':
    main()
