import numpy as np
from PIL import Image, ImageOps
import cv2
from copy import deepcopy
from typing import Tuple
# from matplotlib import pyplot as plt

import gc

import logging
print = logging.info


class Plot():
    def __init__(self):
        pass

    def title(self, string):
        pass

    def imshow(self, img, cmap=''):
        pass

    def show(self):
        pass


plt = Plot()


def rgb_image_from_file(fname: str) -> Image.Image:
    img = Image.open(fname)
    img = img.convert('RGB')
    return img


def image_to_grayscale(rgb_img: Image.Image) -> np.ndarray:
    img = rgb_img.convert('L')
    return np.asarray(img, dtype=np.uint8)


def detection_blur(first_thresh: np.ndarray, blur_mode: int) -> np.ndarray:
    match blur_mode:
        case 0:
            blurred = cv2.GaussianBlur(first_thresh, (1, 1), 0)
        case 1:
            blurred = cv2.GaussianBlur(first_thresh, (3, 3), 0)
        case 2:
            blurred = cv2.GaussianBlur(first_thresh, (5, 5), 0)
        case 3:
            blurred = cv2.GaussianBlur(first_thresh, (1, 1), 1)
        case 4:
            blurred = cv2.GaussianBlur(first_thresh, (3, 3), 3)
        case 5:
            blurred = cv2.GaussianBlur(first_thresh, (5, 5), 5)
        case 6:
            blurred = cv2.GaussianBlur(first_thresh, (7, 7), 7)
        case 7:
            blurred = cv2.GaussianBlur(first_thresh, (9, 9), 9)
        case 8:
            blurred = cv2.GaussianBlur(first_thresh, (5, 5), 3)
        case 9:
            blurred = cv2.GaussianBlur(first_thresh, (3, 3), 7)
        case 10:
            blurred = cv2.GaussianBlur(first_thresh, (1, 1), 3)
        case 11:
            blurred = cv2.GaussianBlur(first_thresh, (3, 3), 5)
        case 12:
            blurred = cv2.GaussianBlur(first_thresh, (3, 3), 1)
        case 13:
            blurred = cv2.GaussianBlur(first_thresh, (5, 5), 1)
        case 14:
            blurred = deepcopy(first_thresh)
        case _:
            raise NoMoreBlurException("No more blur modes to test.")
    return blurred


def recognition_blur(first_thresh: np.ndarray) -> np.ndarray:
    # blurred = cv2.GaussianBlur(first_thresh, (7, 7), 5)  # a moderate amount of blur
    # blurred = cv2.GaussianBlur(first_thresh, (9, 9), 10)  # increased blur intensity.
    blurred = cv2.GaussianBlur(first_thresh, (1, 1), 0)  # decreased blur intensity.
    return blurred


def rgb_image_to_inverse_thresholded_grayscale(rgb_image: Image.Image, purpose: str = 'detect', blur_mode: int = 0, debug: bool = False):
    # my solution to this section

    threshold, first_thresh = cv2.threshold(image_to_grayscale(rgb_image), 0.0, 255.0, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    first_thresh = first_thresh.astype(np.uint8)

    # otsu's method find a midrange average by averaging the most and the least (+ other math opts probably)
    # the inv_binary_threshold just makes a black and white image with black in the background to threshold at 50% with white in the background instead

    if debug:
        print(f'first threshold: {threshold}')

    if purpose == 'detect':
        blurred = detection_blur(first_thresh, blur_mode)
    else:
        blurred = recognition_blur(first_thresh)

    # threshold, second_thresh = cv2.threshold(first_thresh, 0.0, 255.0, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # I have 0 clue why I made it blurred just to not use it?? I need to use blur, sometimes I'm stupid.
    threshold, second_thresh = cv2.threshold(blurred, 0.0, 255.0, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    second_thresh = second_thresh.astype(np.uint8)

    if debug:
        print(f'second threshold: {threshold}')

    # make sure it's actually an inverted mostly-black black-and-white image:
    if np.average(second_thresh) > (255.0/2.1):
        second_thresh = 255.0 - second_thresh

    second_thresh = np.asarray(second_thresh, dtype=np.uint8)

    if debug:  # simply because sometimes it's annoying.
        plt.title('blurred first step')
        plt.imshow(blurred, cmap='Greys')
        plt.show()
        plt.title('double thresholded inverse blurred')
        plt.imshow(second_thresh, cmap='Greys')
        plt.show()

    return second_thresh


def rectangle_contours_from_inverse_thresholded_image(thresholded_img: np.ndarray, debug: bool = False) -> list:
    # find contours makes modifications to the image, so I'm giving it a copy.
    # only works on opencv version > 4 because otherwise the [0] will return the modified image.
    # contours = cv2.findContours(deepcopy(thresholded_img), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]  # this returns the outer ones but sometimes depending on the colors can get weird and not work.
    # contours = cv2.findContours(deepcopy(thresholded_img), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)[0]  # this returns all of the simpler ones
    contours = cv2.findContours(deepcopy(thresholded_img), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]  # this returns ALL of them, I think it's better but I'm afraid of the implications on a busy screen.

    w, h = np.shape(thresholded_img)[0:2]

    rectangles = [(0, 0, w, h)]
    if debug:
        print(f'Base rectangle: The image itself: {list(rectangles[0])}')
    for c in contours:
        # get the information of the contour box
        x, y, w, h = cv2.boundingRect(c)
        # if (w*h) > 49:  # larger area than a 7 x 7 square
        # if (w*h) > 1024:  # larger area than a 32 x 32 square
        # if (w*h) > 4096:  # larger area than a 64 x 64 square
        if (w*h) > 8192:  # larger area than a roughly 90 x 90 square
            # needs to be large enough to filter out to compensate for all of the contours found.
            # rectangles.append(cv2.boundingRect(c))
            rectangles.append((x, y, w, h))
            if debug:
                print(f'New rectangle: {(x, y, w, h)}')

    return rectangles


class BadImageException(Exception):
    pass


class NoMoreBlurException(Exception):
    pass


def largest_square_bounding_from_list_of_rectangles(rectangles: list, debug: bool = False) -> tuple:
    # find (almost) square looking boxes out of the contours
    squares = []
    for r in rectangles:
        w = r[2]
        h = r[3]
        # if w > 0.9*h and w < 1.1*h:  # 10% is too much, changing it to only 7%
        # if (w > (0.93*h)) and (w < (1.07*h)):
        # if w > 0.9*h and w < 1.1*h:  # I felt like 7% is too little.
        # if w > 0.85*h and w < 1.15*h:  # I think up to 15% will be okay
        if 1.15*h > w > 0.85*h:  # does this work? I have no clue.
            squares.append(r)
    if squares == []:
        raise BadImageException("Your image didn't have any shapes almost resembling a square or a grid.\nThis could be an issue of too-similarly colored edges on the boxes, or a low quality image.")
    largest_square = max(squares, key=lambda s: s[2])
    if debug:
        x, y, w, h = largest_square
        print(f"x: {x}   y: {y}   width: {w}   height : {h}")
    return largest_square


def ensure_square_boundary(semisquare_boundary: tuple) -> Tuple[int, int, int, int]:  # makes it fully equal if they're off by a tiny bit
    x, y, w, h = semisquare_boundary
    delta = abs(w-h)
    ratio = max([delta/w, delta/h])
    if ratio < 0.1:  # this is just in case a rectangle gets passed to it for some reason
        # w = int((((3*w)+h)/4))
        w = int((((w+h)/2)))
        h = w
    else:
        print("NOT A SQUARE?! BLASPHEMY!")
        return (-1, -1, -1, -1)
    return (x, y, w, h)


def rgb_to_bgr(rgb_img: np.ndarray) -> np.ndarray:
    return np.array(rgb_img, dtype=np.uint8)[:, :, ::-1].copy()


def draw_boundary_to_new_mask(bounding_rectangle: tuple, rgb_original_img: np.ndarray) -> np.ndarray:
    bgr_img = rgb_to_bgr(rgb_original_img)
    x, y, w, h = bounding_rectangle
    mask = np.ones(bgr_img.shape[:2], dtype=np.uint8) * 255
    cv2.rectangle(mask, (x, y), (x+w, y+h), (0, 0, 255), -1)
    return mask


def debug_draw_mask_to_original_image(mask: np.ndarray, rgb_original_img: np.ndarray) -> None:
    bgr_img = rgb_to_bgr(rgb_original_img)
    res_final = cv2.bitwise_and(bgr_img, bgr_img, mask=cv2.bitwise_not(mask))
    final_img = cv2.cvtColor(res_final, cv2.COLOR_BGR2RGB)
    plt.title('the grid mask on the original image')
    plt.imshow(rgb_original_img)
    plt.imshow(mask)
    plt.imshow(final_img)
    plt.show()


def extract_square_boundary_to_image(square_bounding: tuple, rgb_original_img: Image.Image) -> Image.Image:
    x, y, w, h = square_bounding
    # square = np.asarray(rgb_original_img, dtype=np.uint8)[y:y+h, x:x+h]
    square = np.asarray(rgb_original_img, dtype=np.uint8)[y:y+h, x:x+w]
    square = Image.fromarray(square)
    return square


def split_square_to_81(square_image: Image.Image) -> list:
    image = np.asarray(square_image, dtype=np.uint8)
    # side = square_image.shape[0]
    side = image.shape[0]
    tile_side = side / 9  # don't round yet. use round() after multiplying, to be accurate.
    tiles = []
    for j in range(0, 9):
        for i in range(0, 9):
            i_s, i_e = i, i+1
            j_s, j_e = j, j+1
            ys = round(tile_side * j_s)
            ye = round(tile_side * j_e)
            xs = round(tile_side * i_s)
            xe = round(tile_side * i_e)
            tiles.append(image[ys:ye, xs:xe])
    return tiles


def remove_border_pixels(grayscale_image: np.ndarray, margin_percent=5) -> np.ndarray:
    img_arr = np.asarray(grayscale_image, dtype=np.uint8)
    side = width = height = img_arr.shape[0]
    margin = round(margin_percent*side/100)
    crop_box = (margin, margin, width - (2 * margin), height - (2 * margin))
    gray = Image.fromarray(img_arr)
    borderless_img = gray.crop(crop_box)
    return np.asarray(borderless_img, dtype=np.uint8)


def resize_tile(grayscale_tile: np.ndarray) -> np.ndarray:
    tile = Image.fromarray(grayscale_tile, mode='L')
    tiny_tile = tile.resize((28, 28), Image.LANCZOS)
    return np.asarray(tiny_tile, dtype=np.uint8)


def clean_tile(grayscale_tile: np.ndarray) -> np.ndarray:
    borderless_tile: np.ndarray = remove_border_pixels(grayscale_tile, margin_percent=7)
    resized_borderless: np.ndarray = resize_tile(borderless_tile)
    return resized_borderless


def rectangles_to_square_image(rectangle_boxes: list, rgb_image: Image.Image, debug: bool = False) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    boundingbox_square = largest_square_bounding_from_list_of_rectangles(rectangle_boxes, debug=debug)
    corrected_boundary = ensure_square_boundary(boundingbox_square)  # ensures that width and height are the exact same number, takes an average weighted more towards the bigger guy
    square_image = extract_square_boundary_to_image(corrected_boundary, rgb_image)
    # print(f'bb: {boundingbox_square}\ncorrected: {corrected_boundary} \n image shape: {np.shape(square_image)}\n\n')
    return (square_image, corrected_boundary)


def debug_display_rectangles(rectangle_boxes: list, rgb_image):
    c = 1
    t = len(rectangle_boxes)
    for b in rectangle_boxes:
        print(f' {c:{"0"}>3} / {t:{"0"}>3} :   { ", ".join( [str(i) for i in b] ) } ')  # this is horrible lol
        rectangular_mask = draw_boundary_to_new_mask(b, rgb_image)
        debug_draw_mask_to_original_image(rectangular_mask, rgb_image)
        c += 1


def process_image_file_to_list_of_polished_np_tiles(filename: str, debug: bool = False, more_debug: bool = False) -> list:
    rgb_image = rgb_image_from_file(filename)

    blurmode = 0
    success = False
    # bad_image = False
    finish = False
    # most_rectangles = []
    most_count = 0
    # best_mode = -1

    largest_square = (0, 0, 0, 0)
    largest_square_image = np.ndarray([], dtype=np.uint8)
    # largest_square_rectangles = []
    # largest_square_mode = -1
    while not finish:
        try:
            thresholded_grayscale_image = rgb_image_to_inverse_thresholded_grayscale(rgb_image, purpose='detect', blur_mode=blurmode, debug=debug)
            rectangle_boxes = rectangle_contours_from_inverse_thresholded_image(thresholded_grayscale_image, debug=debug)
            count = len(rectangle_boxes)
            if count == max(most_count, count):
                most_count = count
                # most_rectangles = deepcopy(rectangle_boxes)
                # best_mode = deepcopy(blurmode)
            square_image, square_properties = rectangles_to_square_image(rectangle_boxes, rgb_image, debug=more_debug)
            # x, y, w, h = square_properties
            w, h = square_properties[2:4]
            if w > largest_square[2] and (h == w):
                largest_square = deepcopy(square_properties)
                largest_square_image = np.asarray(square_image, dtype=np.uint8)  # I'm fairly certain acts like deepcopy
                # largest_square_image = deepcopy(square_image)
                # largest_square_rectangles = deepcopy(rectangle_boxes)
                # largest_square_mode = deepcopy(blurmode)
            success = True
        except BadImageException:
            # if debug:
            #     print(f"Blur mode {blurmode} failed. Trying another.")
            pass
        except NoMoreBlurException:
            blurmode -= 1
            finish = True
            # if debug:
            #     print("Ran out of blur modes.")
        finally:
            blurmode += 1

    if not success:
        # if debug:
        #     print(f"Unsuccessful. Displaying the most amount of rectangles ({most_count}) that was acquired during mode {best_mode}")
        #     debug_display_rectangles(most_rectangles, rgb_image)
        raise BadImageException("Your image didn't have any shapes almost resembling a square or a grid.\nThis could be an issue of too-similarly colored edges on the boxes, or a low quality image.")

    # if debug:
    #     print(f"At least one grid was recognised using blur mode(s) {largest_square_mode} and {best_mode}! Woo hoo!")

    # if debug and more_debug:
    #     print(f"*Most* rectangles found but not necessarily the biggest square in them: Mode {largest_square_mode}")
    #     debug_display_rectangles(most_rectangles, rgb_image)
    #     print(f"*Biggest* square found but not necessarily the most rectangles in them: Mode {largest_square_mode}")
    #     debug_display_rectangles(largest_square_rectangles, rgb_image)

    # if debug:
    #     plt.title("Largest recognised square in all of the image:")
    #     plt.imshow(largest_square_image)
    #     plt.show()
    #     square_mask = draw_boundary_to_new_mask(largest_square, rgb_image)
    #     debug_draw_mask_to_original_image(square_mask, rgb_image)

    grid = Image.fromarray(largest_square_image)
    inverse_clean_grid = rgb_image_to_inverse_thresholded_grayscale(grid, purpose='recognise', debug=debug)
    borderless_inverse_clean_grid = Image.fromarray(remove_border_pixels(inverse_clean_grid, margin_percent=1.3))
    # mind this one ^, it's literally a percentage. so 50 is 50%=0.5
    tiles: list = split_square_to_81(borderless_inverse_clean_grid)
    clean_tiles: list = list(map(clean_tile, tiles))

    return clean_tiles


# If I face more memory issues:
# 1. lower the size of the numbers/ files
# 2. lower the size of this image
# This is both slow and ugly.
def generate_grid(tiles: list, size: tuple, mostly_black: bool = False) -> Image.Image:
    picture_dictionary = {}
    directory = 'numbers/'
    side = 0
    border_thick = 5
    thicker_edge = round(border_thick * 1.6)

    checked_side = False
    for n in range(0, 10):
        key = f'{n}.png'
        image = Image.open(directory+key)
        # image = ImageOps.expand(image, border=border_thick*4, fill='white')
        # image = ImageOps.expand(image, border=border_thick*3, fill='white')
        image = ImageOps.expand(image, border=border_thick*3, fill=255)
        # this is a cool pattern but it looks freaky so i'll remove it.
        if not checked_side:
            side = image.width + 20
            checked_side = True
        picture_dictionary.update({key: image})

    gc.collect()

    initial_size = (side*9, side*9)
    print(f"size before resize: {initial_size}")
    image: Image.Image = Image.new('RGB', initial_size)

    for i, n in enumerate(tiles):
        row = i // 9
        col = i % 9
        c_tile = picture_dictionary[f'{n}.png']

        new_tile = np.asarray(c_tile, dtype=np.uint8)[:, :, [2, 1, 0]]  # BGR mode for CV2

        # cv2.copyMakeBorder order: top bottom left right

        # the order of the white borders first and then the black ones matters.
        # the final image will still look like a square, but any corners that should be black, will be black.
        # otherwise it'll make the corners white and cause a dotted-line situation on the grid, which would look odd
        mark_edge = [False, False, False, False]
        if (col % 3 == 2) and (col != 8):
            mark_edge[3] = True
            # right

        elif (col % 3 == 0) and (col != 0):
            mark_edge[2] = True
            # left

        if (row % 3 == 2) and (row != 8):
            mark_edge[1] = True
            # bottom

        elif (row % 3 == 0) and (row != 0):
            mark_edge[0] = True
            # top

        black_edges = [thicker_edge if mark else 0 for mark in mark_edge]
        white_edges = [0 if mark else thicker_edge for mark in mark_edge]

        new_tile = cv2.copyMakeBorder(new_tile,   white_edges[0], white_edges[1], white_edges[2], white_edges[3],   cv2.BORDER_CONSTANT, value=(255, 255, 255))
        new_tile = cv2.copyMakeBorder(new_tile,   black_edges[0], black_edges[1], black_edges[2], black_edges[3],   cv2.BORDER_CONSTANT, value=(0, 0, 0))

        new_tile = Image.fromarray(new_tile[:, :, [2, 1, 0]])  # Back to RGB mode for Pillow

        # add a black border around individual numbers
        # new_tile = ImageOps.expand(new_tile, border=border_thick, fill='black')
        new_tile = ImageOps.expand(new_tile, border=border_thick, fill=0)

        new_tile = new_tile.resize((side, side), Image.LANCZOS)

        image.paste(new_tile, (col*side, row*side))

        del new_tile
        del mark_edge
        del black_edges
        del white_edges

    del picture_dictionary
    gc.collect()

    # image = ImageOps.expand(image, border=thicker_edge, fill='black')
    image = ImageOps.expand(image, border=thicker_edge, fill=0)
    image = image.resize(size, Image.LANCZOS)
    if mostly_black:
        image = ImageOps.invert(image)
    return image


def write_solved_grid_to_image(new_file_name: str, filename: str, tile_list: list) -> Tuple[Tuple[int, int, int, int], Image.Image, Image.Image, bool]:
    org_rgb_image: Image.Image = rgb_image_from_file(filename)
    rgb_image = deepcopy(org_rgb_image)
    blurmode = 0
    success = False
    # bad_image = False
    finish = False
    # most_rectangles = []
    most_count = 0
    # most_mode = -1
    largest_square = (0, 0, 0, 0)
    largest_square_image = np.ndarray([], dtype=np.uint8)
    # largest_square_rectangles = []
    # largest_square_mode = -1
    while not finish:
        try:
            thresholded_grayscale_image = rgb_image_to_inverse_thresholded_grayscale(rgb_image, purpose='detect', blur_mode=blurmode)
            rectangle_boxes = rectangle_contours_from_inverse_thresholded_image(thresholded_grayscale_image)
            count = len(rectangle_boxes)
            if count == max(most_count, count):
                most_count = count
                # most_rectangles = deepcopy(rectangle_boxes)
                # most_mode = blurmode
            square_image, square_properties = rectangles_to_square_image(rectangle_boxes, rgb_image)
            w = square_properties[2]
            if w > largest_square[2]:
                largest_square = deepcopy(square_properties)
                largest_square_image = np.asarray(square_image, dtype=np.uint8)  # I'm fairly certain acts like deepcopy
                # largest_square_image = deepcopy(square_image)
                # largest_square_rectangles = deepcopy(rectangle_boxes)
                # largest_square_mode = deepcopy(blurmode)
            success = True
        except BadImageException:
            pass
        except NoMoreBlurException:
            blurmode -= 1
            finish = True
        finally:
            blurmode += 1
    gc.collect()
    if not success:
        raise BadImageException("Your image didn't have any shapes almost resembling a square or a grid.\nThis could be an issue of too-similarly colored edges on the boxes, or a low quality image.")
    grid = largest_square_image
    mostly_black = False
    if np.average(grid) < (255.0/2.1):
        mostly_black = True
    # grid_size = (1080, 1080)
    grid_size = (512, 512)
    solved_grid = generate_grid(tile_list, grid_size, False)
    solved_grid.save(new_file_name)
    return (largest_square, solved_grid, org_rgb_image, mostly_black)


def write_solved_grid_to_original_image(new_file_name: str, largest_square: tuple, solved_grid: Image.Image, org_rgb_image: Image.Image, mostly_black):
    x, y, w, h = largest_square

    solved_grid = solved_grid.resize((w, h), Image.LANCZOS)

    if mostly_black:
        solved_grid = ImageOps.invert(solved_grid)

    solved_grid_np = np.asarray(deepcopy(solved_grid), dtype=np.uint8).copy()
    solved_image_np = np.asarray(deepcopy(org_rgb_image), dtype=np.uint8).copy()
    solved_image_np[y:y+h, x:x+w] = solved_grid_np

    solved_image = Image.fromarray(solved_image_np)
    solved_image.save(new_file_name)
    gc.collect()
    return deepcopy(solved_image)


def main() -> None:
    filename = 'screenshot.png'

    tile_images = process_image_file_to_list_of_polished_np_tiles(filename=filename, debug=True, more_debug=False)
    print(len(tile_images))

    grid_image_file_name = 'grid_solved.png'
    test_tiles = [(((i % 9)+(i // 9)) % 10) for i in range(1, 82)]
    square_properties, solved_grid_image, original_image, is_mostly_black = write_solved_grid_to_image(new_file_name=grid_image_file_name, filename=filename, tile_list=test_tiles)

    solved_image_file_name = 'screenshot_solved.png'
    solved_image = write_solved_grid_to_original_image(new_file_name=solved_image_file_name, largest_square=square_properties, solved_grid=solved_grid_image, org_rgb_image=original_image, mostly_black=is_mostly_black)
    plt.imshow(solved_image)
    plt.show()


if __name__ == '__main__':
    main()
