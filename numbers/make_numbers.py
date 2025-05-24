import numpy as np
import sys
import cv2

# IMGSIZE = 512
# too heavy
IMGSIZE = 216

# Create a 0(black) grayscale image 512x512 pixels 
background = np.zeros((IMGSIZE, IMGSIZE, 1), dtype=np.uint8)
font_color = 255
# thickness = 44
thickness = 17
try:
    thickness = int(sys.argv[1])
except Exception as e:
    pass
print(thickness)
line_type = cv2.LINE_AA
# target = 0.87
target = 0.74
limit = target * IMGSIZE
origin_should_be_bottom_left = False # if false, instead its in the top left

# font = cv2.FONT_HERSHEY_COMPLEX
font = cv2.FONT_HERSHEY_SIMPLEX
# font = cv2.FONT_HERSHEY_DUPLEX

for n in range(1, 10):
    text = str(n)
    size = (0, 0)
    font_scale_ = 0.1
    font_scale = 0.1
    run_loop = True
    while run_loop:
        size = cv2.getTextSize(text=text, fontFace=font, fontScale=font_scale_, thickness=thickness)[0]
        if size[0] > limit or size[1] > limit:
            run_loop = False
            break
        font_scale = font_scale_
        font_scale_ += 0.222
        font_scale_ = round(font_scale_, 3)
    width, height = cv2.getTextSize(text=text, fontFace=font, fontScale=font_scale, thickness=thickness)[0]
    origin = ( int((IMGSIZE-width)/2) , int((IMGSIZE+height)/2) )
    new_image = background.copy()
    cv2.putText(
        img=new_image,
        text=text, 
        org=origin,
        bottomLeftOrigin=origin_should_be_bottom_left,
        fontFace=font,
        fontScale=font_scale,
        color=font_color,
        thickness=thickness,
        lineType=line_type
        )
    new_image = np.asarray(255.0 - new_image, dtype=np.uint8)
    asrgbimg = cv2.cvtColor(new_image, cv2.COLOR_GRAY2RGB)
    cv2.imwrite(f'{text}.png', asrgbimg)
    print(f'saved "{text}.png"')
cv2.imwrite('0.png', cv2.cvtColor(np.asarray(255.0 - background, dtype=np.uint8), cv2.COLOR_GRAY2RGB))
print(f'saved "0.png"')
