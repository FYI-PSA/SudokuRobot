from PIL import Image, ImageDraw, ImageFont
from PIL.ImageOps import invert

# IMG_SIZE = 512  # Too large
# IMG_SIZE = 216  # Still a bit too much
# IMG_SIZE = 128  # A bit too small
# IMG_SIZE = 171  # Average of 216 and 128
IMG_SIZE = 162  # 81 * 2

# black (value of 0)
# grayscale image (1 channel)
# IMG_SIZE pixels by IMG_SIZE pixels sized
BACKGROUND_IMAGE = Image.new(mode="RGB", size=(IMG_SIZE, IMG_SIZE), color=(0, 0, 0))  # type: ignore
WHITE_IMAGE = Image.new(mode="RGB", size=(IMG_SIZE, IMG_SIZE), color=(255, 255, 255))  # type: ignore

WHITE_IMAGE.save('0.png')
print('saved "0.png"')

FONT_COLOR = 255
TARGET = 0.81

LIMIT = IMG_SIZE * TARGET

# ANCHOR = 'ls'  # left bottom(baseline, only works in single lines)
ANCHOR = 'mm'  # exact middle
ORIGIN = (round(IMG_SIZE/2), round(IMG_SIZE/2))

for n in range(1, 10):
    size = (0, 0)  # pylint: disable=C0103
    variable_font_size = 0  # pylint: disable=C0103
    font_size = 1  # pylint: disable=C0103

    font_object = ImageFont.truetype(font='arial', size=font_size)

    TEXT = str(n)
    N_IMAGE: Image.Image = BACKGROUND_IMAGE.copy()
    PEN_OBJECT = ImageDraw.Draw(N_IMAGE)

    RUN_LOOP = True
    while RUN_LOOP:
        font_object = ImageFont.truetype(font='arial', size=font_size)
        size = font_object.getsize(text=TEXT)
        if size[0] > LIMIT or size[1] > LIMIT:
            RUN_LOOP = False  # pylint: disable=C0103
            break
        font_size = variable_font_size  # pylint:disable=C0103
        variable_font_size += 1
        variable_font_size = round(variable_font_size, 3)

    font_object = ImageFont.truetype(font='arial', size=font_size)
    # width, height = font_object.getsize(text=TEXT)
    # origin = (int((IMG_SIZE-width)/2), int((IMG_SIZE+height)/2))
    # for the 'ls' anchor
    PEN_OBJECT.text(text=TEXT, xy=ORIGIN, anchor=ANCHOR, fill=(255, 255, 255), font=font_object)
    FILE_NAME = f'{TEXT}.png'
    N_IMAGE = invert(N_IMAGE)
    N_IMAGE.save(fp=FILE_NAME)
    print(f'saved "{FILE_NAME}"')
    del N_IMAGE
