import numpy as np
from PIL import Image, ImageOps
import cv2
from copy import deepcopy
# from matplotlib import pyplot as plt

import gc

import logging
print = logging.info


class plot():
    def __init__(self):
        pass
    def title(self, string):
        pass
    def imshow(self, img, cmap=''):
        pass
    def show(self):
        pass
plt = plot()


# def grayscale_to_binary(image: np.ndarray, debug: bool = False, thresh: float = 0.3):
#     valuearr = np.asanyarray(image, dtype=np.uint8)
#     fractionarr = valuearr / 255.0  # it's a black and white image so the numbers are 0-255, so if I divide by this, it's gonna be 0-1
#     treshholded = np.where(fractionarr > thresh, 1.0, 0.0)
#     if debug:
#         treshhold_img = treshholded * 255.0
#         plt.imshow(treshhold_img, cmap='Greys')
#         plt.show()
#     return treshholded


def rgb_image_from_file(fname: str, debug: bool = False) -> Image.Image:
    img = Image.open(fname)
    img = img.convert('RGB')
    if debug:
        plt.imshow(img)
        plt.show()
    return img


def image_to_grayscale(rgb_img: np.ndarray, debug: bool = False):
    img = rgb_img.convert('L')
    if debug:
        plt.imshow(img, cmap='Greys')
        plt.show()
    return np.asarray(img, dtype=np.uint8)


def detection_blur(firstthresh: np.ndarray, blurdiff: int) -> np.ndarray:
    match blurdiff:
        case 0:
            blurred = cv2.GaussianBlur(firstthresh, (1, 1), 0)
        case 1:
            blurred = cv2.GaussianBlur(firstthresh, (3, 3), 1)
        case 2:
            blurred = cv2.GaussianBlur(firstthresh, (5, 5), 3)
        case 3:
            blurred = cv2.GaussianBlur(firstthresh, (7, 7), 8)
        case 4:
            blurred = cv2.GaussianBlur(firstthresh, (9, 9), 9)
        case 5:
            blurred = cv2.GaussianBlur(firstthresh, (3, 3), 2)
        case 6:
            blurred = cv2.GaussianBlur(firstthresh, (1, 1), 1)
        case 7:
            blurred = deepcopy(firstthresh)
        case _:
            raise NoMoreBlurException("No more blur modes to test.")
    return blurred


def recognition_blur(firstthresh: np.ndarray) -> np.ndarray:
    # blurred = cv2.GaussianBlur(firstthresh, (7, 7), 5)  # a moderate amount of blur
    # blurred = cv2.GaussianBlur(firstthresh, (9, 9), 10)  # increased blur intensity.
    blurred = cv2.GaussianBlur(firstthresh, (1, 1), 0)  # decreased blur intensity.
    return blurred


def rgb_image_to_inverse_treshholded_grayscale(rgb_image: np.ndarray, purpose: str = 'detect', blurdiff: int = 0, debug: bool = False, moredebug: bool = False):
    # my solution to this section
    
    # firstthresh = grayscale_to_binary(image_to_grayscale(debug=True), debug=True, thresh=0.7) * 255.0
    # image_to_grayscale returns black in bg and white in fg
    
    threshhold, firstthresh = cv2.threshold(image_to_grayscale(rgb_image), 0.0, 255.0, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # otsu's method find a midrange average by averaging the most and the least (+ other math opts probably)
    # the inv_binary_threshhold just makes a black and white image with black in the background to threshhold at 50% with white in the background instead
    # much better than my grayscale_to_binary function, so I won't use that any longer.
    
    if purpose == 'detect':
        blurred = detection_blur(firstthresh, blurdiff)
        if debug:
            print("detection blur")
    else:
        blurred = recognition_blur(firstthresh)
        if debug:
            print("recognition blur")

    # threshhold, secondthresh = cv2.threshold(firstthresh, 0.0, 255.0, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # I have 0 clue why I made it blurred just to not use it?? I need to use blur, sometimes I'm stupid.
    threshhold, secondthresh = cv2.threshold(blurred, 0.0, 255.0, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # make sure it's actually an inverted mostly-black black-and-white image:
    if np.average(secondthresh) > (255.0/2.1):
        secondthresh = 255.0 - secondthresh
    
    secondthresh = np.asarray(secondthresh, dtype=np.uint8)

    if debug and moredebug:  # simply because sometimes it's annoying.
        plt.title('blurred first step')
        plt.imshow(blurred, cmap='Greys')
        plt.show()
        plt.title('double threshholded inversed blurred')
        plt.imshow(secondthresh, cmap='Greys')
        plt.show()
    
    return secondthresh


def rectangle_contours_from_inverse_threshholded_image(threshholded_img: np.ndarray, debug: bool = False) -> list:
    # find contours makes modifications to the image, so I'm giving it a copy.
    # only works on opencv version > 4 because otherwise the [0] will return the modified image.
    # contours = cv2.findContours(deepcopy(threshholded_img), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]  # this returns the outer ones but sometimes depending on the colors can get weird and not work.
    # contours = cv2.findContours(deepcopy(threshholded_img), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)[0]  # this returns all of the simpler ones
    contours = cv2.findContours(deepcopy(threshholded_img), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]  # this returns ALL of them, I think it's better but I'm afraid of the implications on a busy screen.
    
    w, h = np.shape(threshholded_img)[0:2]
    
    if debug:
        print(f"Count of contours: {len(contours)}")
    
    rectangles = [(0, 0, w, h)]
    for c in contours:
        # get the information of the contour box
        x, y, w, h = cv2.boundingRect(c)
        # if (w*h) > 49:  # larger area than a 7 x 7 square
        # if (w*h) > 1024:  # larger area than a 32 x 32 square
        # if (w*h) > 4096:  # larger area than a 64 x 64 square
        if (w*h) > 8192:  # larger area than a rougly 90 x 90 square
            # needs to be large enough to filter out to compensate for all of the contours found.
            rectangles.append(cv2.boundingRect(c))
    if debug:
        print(f"Count of rectangles: {len(rectangles)}")
        print(rectangles)
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
        if w > 0.9*h and w < 1.1*h:  # i felt like 7% is too little.
            squares.append(r)
    if squares == []:
        raise BadImageException("Your image didn't have any shapes almost resembling a square or a grid.\nThis could be an issue of too-similarly colored edges on the boxes, or a low quality image.")
    largest_square = max(squares, key=lambda s: s[2])
    if debug:
        x, y, w, h = largest_square
        print(f"x: {x}   y: {y}   width: {w}   height : {h}")
    return largest_square


def ensure_square_boundary(semisqaure_boundary: tuple) -> tuple:  # makes it fully equal if they're off by a tiny bit
    x, y, w, h = semisqaure_boundary
    delta = abs(w-h)
    ratio = max([delta/w, delta/h])
    if ratio < 0.1:  # this is just in case a rectangle gets passed to it for some reason
        # w = max([w, h])  # increase the lower one, because it's easier to read with wall noise than to read half a digit
        # why not make it their average
        # and im pretty confident in myself, lets average it twice.
        w = int((((3*h)+w)/2))
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


def extract_square_boundary_to_image(square_bounding: tuple, rgb_original_img: np.ndarray, debug: bool = True) -> np.ndarray:
    x, y, w, h = square_bounding
    square = np.asarray(rgb_original_img, dtype=np.uint8)[y:y+h, x:x+h]
    square = Image.fromarray(square)
    if debug:
        plt.title('a recognised large square grid')
        plt.imshow(square)
        plt.show()
    return square


def split_square_to_81(square_image: Image.Image) -> list:
    image = np.asarray(square_image, dtype=np.uint8)
    side = square_image.shape[0]
    tileside = side / 9  # don't round yet. use round() after multiplying, to be accurate.
    tiles = []
    for j in range(0, 9):
        for i in range(0, 9):
            i_s, i_e = i, i+1
            j_s, j_e = j, j+1
            ys = round(tileside * j_s)
            ye = round(tileside * j_e)
            xs = round(tileside * i_s)
            xe = round(tileside * i_e)
            tiles.append(image[ys:ye, xs:xe])
    return tiles


def remove_border_pixels(grayscale_image: np.ndarray, margin_percent=5) -> np.ndarray:
    imgarr = np.asarray(grayscale_image, dtype=np.uint8)
    side = width = height = imgarr.shape[0]
    margin = round(margin_percent*side/100)
    cropbox = (margin, margin, width - (2 * margin), height - (2 * margin))
    gray = Image.fromarray(imgarr)
    borderless_img = gray.crop(cropbox)
    return np.asarray(borderless_img, dtype=np.uint8)


def resize_tile(grayscale_tile: np.ndarray) -> np.ndarray:
    tile = Image.fromarray(grayscale_tile, mode='L')
    tinytile = tile.resize((28, 28), Image.LANCZOS)
    return np.asarray(tinytile, dtype=np.uint8)


def clean_tile(grayscale_tile: np.ndarray) -> np.ndarray:
    borderless_tile: np.ndarray = remove_border_pixels(grayscale_tile, margin_percent=7)
    resized_borderless: np.ndarray = resize_tile(borderless_tile)
    return resized_borderless


def rectangles_to_square_image(rectangle_boxes: list, rgb_image: np.ndarray, debug: bool = False) -> tuple:
    boundingbox_square = largest_square_bounding_from_list_of_rectangles(rectangle_boxes, debug=debug)
    corrected_boundary = ensure_square_boundary(boundingbox_square)  # ensures that width and height are the exact same number, by expanding the smaller one (if they're close to the shape of a square)
    square_image = extract_square_boundary_to_image(corrected_boundary, rgb_image, debug=debug)
    print('bb: {boundingbox_square}\ncorrected: {corrected_boundary}\nimgshape: {np.shape(square_image)}\n\n')
    return (square_image, corrected_boundary)


def debug_display_rectangles(rectangle_boxes: list, rgb_image, IWANTMOREDEBUG: bool = False):
    c = 1
    t = len(rectangle_boxes)
    for b in rectangle_boxes:
        print(f' {c:{"0"}>3} / {t:{"0"}>3} :   { ", ".join( [str(i) for i in b] ) } ' )  # this is horrible lol
        rectangular_mask = draw_boundary_to_new_mask(b, rgb_image)
        debug_draw_mask_to_original_image(rectangular_mask, rgb_image)
        c += 1


def process_image_file_to_list_of_polished_np_tiles(filename: str, debug: bool = False, moredebug: bool = False, mostdebug: bool = False, IWANTMOREDEBUG: bool = False) -> list:
    rgb_image = rgb_image_from_file(filename)
    
    blurmode = 0
    success = False
    badimage = False
    finish = False
    most_rects = []
    most_count = 0
    best_mode = -1

    largest_square = (0, 0, 0, 0)
    largest_square_image = np.ndarray([],dtype=np.uint8)
    largest_suqare_rectangles = []
    largest_square_mode = -1
    while not finish:
        try:
            threshholded_grayscale_image = rgb_image_to_inverse_treshholded_grayscale(rgb_image, purpose='detect', blurdiff=blurmode, debug=debug, moredebug=moredebug)
            rectangle_boxes = rectangle_contours_from_inverse_threshholded_image(threshholded_grayscale_image, debug=debug)
            count = len(rectangle_boxes)
            if count == max(most_count, count):
                most_count = count
                most_rects = deepcopy(rectangle_boxes)
                best_mode = deepcopy(blurmode)
            square_image, square_properties = rectangles_to_square_image(rectangle_boxes, rgb_image, debug=mostdebug)
            x, y, w, h = square_properties
            if w > largest_square[2] and (h == w):
                largest_square = deepcopy(square_properties)
                largest_square_image = deepcopy(square_image)
                largest_square_rectangles = deepcopy(rectangle_boxes)
                largest_square_mode = deepcopy(blurmode)
            success = True
        except BadImageException:
            if debug:
                print(f"Blur mode {blurmode} failed. Trying another.")
        except NoMoreBlurException:
            blurmode -= 1
            finish = True
            if debug:
                print("Ran out of blur modes.")
        finally:
            blurmode += 1
    
    if not success:
        if debug:
            print(f"Unsuccessful. Displaying the most amount of rectangles ({most_count}) that was accuired during mode {best_mode}")    
            debug_display_rectangles(most_rects, rgb_image, IWANTMOREDEBUG)
        raise BadImageException("Your image didn't have any shapes almost resembling a square or a grid.\nThis could be an issue of too-similarly colored edges on the boxes, or a low quality image.")

    if debug:
        print(f"At least one grid was recognised using blur mode(s) {largest_square_mode} and {best_mode}! Woo hoo!")
    
    if debug and mostdebug:
        print(f"*Most* rectangles found but not neccasarily the biggest square in them: Mode {largest_square_mode}")
        debug_display_rectangles(most_rects, rgb_image, IWANTMOREDEBUG)
        print(f"*Biggest* square found but not neccasarily the most rectangles in them: Mode {largest_square_mode}")
        debug_display_rectangles(largest_square_rectangles, rgb_image, IWANTMOREDEBUG)
    
    if debug:
        plt.title("Largest recognised square in all of the image:")
        plt.imshow(largest_square_image)
        plt.show()
        square_mask = draw_boundary_to_new_mask(largest_square, rgb_image)
        debug_draw_mask_to_original_image(square_mask, rgb_image)
    
    grid = largest_square_image
    inverse_clean_grid = rgb_image_to_inverse_treshholded_grayscale(grid, purpose='recognise', debug=debug, moredebug=moredebug)
    borderless_inverse_clean_grid = remove_border_pixels(inverse_clean_grid, margin_percent=0.5)
    tiles: list = split_square_to_81(borderless_inverse_clean_grid)
    clean_tiles: list = list(map(clean_tile, tiles))
    
    return clean_tiles

# If I face more memory issues:
# 1. lower the size of the numbers/ files
# 2. lower the size of this image
def generate_grid(tiles: list, size: tuple, mostly_black: bool = False, debug: bool = False) -> Image.Image:
    picdict = {}
    DIRECTORY = 'numbers/'
    checked_side = False
    side = 0
    for n in range(0, 10):
        # print(f'do u crash here? {n}')
        key = f'{n}.png'
        image = Image.open(DIRECTORY+key)
        image = ImageOps.expand(image, border=37, fill='white')
        image = ImageOps.expand(image, border=17, fill='white')
        image = ImageOps.expand(image, border=18, fill='black')
        if not checked_side:
            side = image.width
            checked_side = True
        picdict.update({key: image})
    gc.collect()
    initial_size = (side*9, side*9)
    if debug:
        print(f"size before resize: {initial_size}")
    image = Image.new('RGB', initial_size)
    for i, n in enumerate(tiles):
        row = i // 9
        col = i % 9
        c_tile = picdict[f'{n}.png']
        image.paste(c_tile, (col*side, row*side))
        # print(f'do u crash here? {i}')
    image = ImageOps.expand(image, border=18, fill='black')
    image = image.resize(size, Image.LANCZOS)
    if mostly_black:
        image = ImageOps.invert(image)
    if debug:
        plt.imshow(image)
        plt.title('solved grid')
        plt.show()
    return image


def write_solved_grid_to_image(newfilename: str, filename: str, tile_list: list) -> tuple: 
    org_rgb_image = rgb_image_from_file(filename)
    rgb_image = deepcopy(org_rgb_image)
    blurmode = 0
    success = False
    badimage = False
    finish = False
    most_rects = []
    most_count = 0
    most_mode = -1
    largest_square = (0, 0, 0, 0)
    largest_square_image = np.ndarray([],dtype=np.uint8)
    largest_suqare_rectangles = []
    largest_square_mode = -1
    while not finish:
        try:
            threshholded_grayscale_image = rgb_image_to_inverse_treshholded_grayscale(rgb_image, purpose='detect', blurdiff=blurmode)
            rectangle_boxes = rectangle_contours_from_inverse_threshholded_image(threshholded_grayscale_image)
            count = len(rectangle_boxes)
            if count == max(most_count, count):
                most_count = count
                most_rects = deepcopy(rectangle_boxes)
                most_mode = blurmode
            square_image, square_properties = rectangles_to_square_image(rectangle_boxes, rgb_image)
            x, y, w, h = square_properties
            if w > largest_square[2]:
                largest_square = deepcopy(square_properties)
                largest_square_image = deepcopy(square_image)
                largest_square_rectangles = deepcopy(rectangle_boxes)
                largest_square_mode = deepcopy(blurmode)
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
    print(np.shape(grid)[0:2])
    print('^ grid shape')
    print(np.shape(largest_square_image))
    print([i for i in largest_square])
    print('??? is there a mismatch here?')  # yup
    mostly_black = False
    if np.average(grid) < (255.0/2.1):
        mostly_black = True
    # grid_size = (1080, 1080)
    grid_size = (512, 512)
    solved_grid = generate_grid(tiles=tile_list, size=grid_size, mostly_black=mostly_black)
    solved_grid.save(newfilename)
    return (largest_square, solved_grid, org_rgb_image, mostly_black)


def write_solved_grid_to_original_image(newfilename: str, largest_square: tuple, solved_grid: Image.Image, org_rgb_image: np.ndarray, mostly_black):
    x, y, w, h = largest_square
    # print(f'x {x}  y {y}  w {w}  h {h}')
    # print(np.shape(solved_grid))
    # print(np.shape(org_rgb_image))
    
    # solved_grid = generate_grid(tiles=tile_list, size=grid_size, mostly_black=mostly_black, debug=debug)
    solved_grid = solved_grid.resize((w, h), Image.LANCZOS)
    print((w,h))
    print('^ grid shape, important function')

    if mostly_black:
        solved_grid = ImageOps.invert(solved_grid)

    # solved_grid = generate_grid(tiles=tile_list, size=grid_size, mostly_black=mostly_black, debug=debug)
    # solved_image = np.asarray(deepcopy(org_rgb_image), dtype=np.uint8).copy()
    # x, y, w, h = largest_square
    # solved_image[y:y+h, x:x+h] = np.asarray(deepcopy(solved_grid), dtype=np.uint8).copy()
    # solved_image = Image.fromarray(solved_image)

    solved_grid_np = np.asarray(deepcopy(solved_grid), dtype=np.uint8).copy()
    solved_image_np = np.asarray(deepcopy(org_rgb_image), dtype=np.uint8).copy()
    print(f'x {x}  y {y}  w {w}  h {h}')
    print(f'solved grid  {np.shape(solved_grid_np)}')
    print(f'solved image {np.shape(solved_image_np)}')
    solved_image_np[y:y+h, x:x+w] = solved_grid_np

    solved_image = Image.fromarray(solved_image_np)
    solved_image.save(newfilename)
    gc.collect()
    return deepcopy(solved_image)


def IDIOTIC_write_solved_grid_to_original_image(newfilename: str, filename: str, tile_list: list, debug: bool = False, moredebug: bool = False, mostdebug: bool = False, IWANTMOREDEBUG: bool = False) -> np.ndarray:
    org_rgb_image = rgb_image_from_file(filename)
    
    blurmode = 0
    success = False
    badimage = False
    finish = False
    most_rects = []
    most_count = 0
    best_mode = -1

    largest_square = (0, 0, 0, 0)
    largest_square_image = np.ndarray([],dtype=np.uint8)
    largest_suqare_rectangles = []
    largest_square_mode = -1
    while not finish:
        try:
            threshholded_grayscale_image = rgb_image_to_inverse_treshholded_grayscale(org_rgb_image, purpose='detect', blurdiff=blurmode, debug=debug, moredebug=moredebug)
            rectangle_boxes = rectangle_contours_from_inverse_threshholded_image(threshholded_grayscale_image, debug=debug)
            count = len(rectangle_boxes)
            if count == max(most_count, count):
                most_count = count
                most_rects = deepcopy(rectangle_boxes)
                best_mode = deepcopy(blurmode)
            square_image, square_properties = rectangles_to_square_image(rectangle_boxes, org_rgb_image, debug=mostdebug)
            x, y, w, h = square_properties
            if w > largest_square[2] and (h == w):
                largest_square = deepcopy(square_properties)
                largest_square_image = deepcopy(square_image)
                largest_square_rectangles = deepcopy(rectangle_boxes)
                largest_square_mode = deepcopy(blurmode)
            success = True
        except BadImageException:
            if debug:
                print(f"Blur mode {blurmode} failed. Trying another.")
        except NoMoreBlurException:
            blurmode -= 1
            finish = True
            if debug:
                print("Ran out of blur modes.")
        finally:
            blurmode += 1
    
    if not success:
        if debug:
            print(f"Unsuccessful. Displaying the most amount of rectangles ({most_count}) that was accuired during mode {best_mode}")    
            debug_display_rectangles(most_rects, org_rgb_image, IWANTMOREDEBUG)
        raise BadImageException("Your image didn't have any shapes almost resembling a square or a grid.\nThis could be an issue of too-similarly colored edges on the boxes, or a low quality image.")

    if debug:
        print(f"At least one grid was recognised using blur mode(s) {largest_square_mode} and {best_mode}! Woo hoo!")
    
    if debug and mostdebug:
        print(f"*Most* rectangles found but not neccasarily the biggest square in them: Mode {largest_square_mode}")
        debug_display_rectangles(most_rects, org_rgb_image, IWANTMOREDEBUG)
        print(f"*Biggest* square found but not neccasarily the most rectangles in them: Mode {largest_square_mode}")
        debug_display_rectangles(largest_square_rectangles, org_rgb_image, IWANTMOREDEBUG)
    
    if debug:
        plt.title("Largest recognised square in all of the image:")
        plt.imshow(largest_square_image)
        plt.show()
        square_mask = draw_boundary_to_new_mask(largest_square, org_rgb_image)
        debug_draw_mask_to_original_image(square_mask, org_rgb_image)

    gc.collect()
    
    grid = largest_square_image
    if np.average(grid) < (255.0/2.1):  
        mostly_black = True
    else:
        mostly_black = False
    grid_size = np.shape(grid)[0:2]
    
    solved_grid = generate_grid(tiles=tile_list, size=grid_size, mostly_black=mostly_black, debug=debug)
    solved_image = np.asarray(deepcopy(org_rgb_image), dtype=np.uint8).copy()

    x, y, w, h = largest_square
    solved_image[y:y+h, x:x+h] = np.asarray(deepcopy(solved_grid), dtype=np.uint8).copy()
    solved_image = Image.fromarray(solved_image)

    solved_image.save(newfilename, 'PNG')
    
    return deepcopy(solved_image)


def main() -> None:
    filename = 'screenshot.png'

    tile_images = process_image_file_to_list_of_polished_np_tiles(filename=filename, debug=True, moredebug=False)
    print(len(tile_images))
    
    gridimagefilename = 'grid_solved.png'
    test_tiles = [((i%9)+(i//9))%10 for i in range(1, 82)]
    
    gridimage = write_solved_grid_to_image(newfilename=gridimagefilename, filename=filename, tile_list=test_tiles, debug=True, moredebug=False)
    
    solvedimagefilename = 'screenshot_solved.png'
    solvedimage = write_solved_grid_to_original_image(newfilename=solvedimagefilename, filename=filename, tile_list=test_tiles, debug=True, moredebug=False)


if __name__ == '__main__':
    main()
