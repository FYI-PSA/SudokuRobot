import numpy as np
import sys
import cv2

# IMG_SIZE = 512
# too heavy
# IMG_SIZE = 216
# still too heavy
IMG_SIZE = 128

# Create a 0(black) grayscale image IMG_SIZExIMG_SIZE pixels
background = np.zeros((IMG_SIZE, IMG_SIZE, 1), dtype=np.uint8)
FONT_COLOR = 255
# thickness = 44
# thickness = 17
THICKNESS = 9
TARGET = 0.87
# target = 0.74

try:
    THICKNESS = int(sys.argv[1])
except Exception:
    pass
print(THICKNESS)
line_type = cv2.LINE_AA
LIMIT = TARGET * IMG_SIZE
ORIGIN_SHOULD_BE_BOTTOM_LEFT = False  # if false, instead its in the top left

# font = cv2.FONT_HERSHEY_COMPLEX
font = cv2.FONT_HERSHEY_SIMPLEX
# font = cv2.FONT_HERSHEY_DUPLEX

for n in range(1, 10):
    text = str(n)  # pylint: disable=C0103
    size = (0, 0)
    font_scale_ = 0.1  # pylint: disable=C0103
    font_scale = 0.1  # pylint: disable=C0103
    run_loop = True  # pylint: disable=C0103
    while run_loop:
        size = cv2.getTextSize(text=text, fontFace=font, fontScale=font_scale_, thickness=THICKNESS)[0]
        if size[0] > LIMIT or size[1] > LIMIT:
            run_loop = False  # pylint: disable=C0103
            break
        font_scale = font_scale_  # pylint: disable=C0103
        font_scale_ += 0.222
        font_scale_ = round(font_scale_, 3)
    width, height = cv2.getTextSize(text=text, fontFace=font, fontScale=font_scale, thickness=THICKNESS)[0]
    origin = (int((IMG_SIZE-width)/2), int((IMG_SIZE+height)/2))
    new_image = background.copy()
    cv2.putText(
        img=new_image,
        text=text,
        org=origin,
        bottomLeftOrigin=ORIGIN_SHOULD_BE_BOTTOM_LEFT,
        fontFace=font,
        fontScale=font_scale,
        color=FONT_COLOR,  # type: ignore
        thickness=THICKNESS,
        lineType=line_type
        )
    new_image = np.asarray(255.0 - new_image, dtype=np.uint8)
    as_rgb_img = cv2.cvtColor(new_image, cv2.COLOR_GRAY2RGB)
    cv2.imwrite(f'{text}.png', as_rgb_img)
    print(f'saved "{text}.png"')
cv2.imwrite('0.png', cv2.cvtColor(np.asarray(255.0 - background, dtype=np.uint8), cv2.COLOR_GRAY2RGB))
print('saved "0.png"')
