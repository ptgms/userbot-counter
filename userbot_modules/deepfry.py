import cv2
from PIL import Image, ImageOps, ImageEnhance
import os
from imutils import face_utils
import tkinter as tk
from tkinter import filedialog

'''
TODO: -> Compressing (Crushing) and back (to increase noise) :: DONE
      -> Applying Red and Orange hue filters for classic deep fry look :: DONE
      -> Detecting eye coordinates and applying the deepfry eye flare in the center::DONE

'''


def userInput():
    # Allowing user to choose the image that has to be deepfried
    root = tk.Tk()
    root.withdraw()
    global filepath
    filepath = list(root.tk.splitlist(filedialog.askopenfilenames(title="PyFry - Choose Image")))
    print("picture location = ", filepath)


def irisCoords(eye):
    # Finding the center point of the eye using the average outer extremes average of the eyes
    mid = (eye[0] + eye[3]) / 2
    mid = (int(mid[0]), int(mid[1]))
    return mid


def generateHue(img):
    # Generating and increasing prominency of red band of the image
    img = img.convert('RGB')
    red = img.split()[0]  # (R,G,B)
    red = ImageEnhance.Contrast(red).enhance(2.0)
    red = ImageEnhance.Brightness(red).enhance(1.5)
    red = ImageOps.colorize(red, Colors.RED, Colors.YELLOW)
    img = Image.blend(img, red, 0.77)
    # Keeping a 100% sharpness value for now, But would probably be better with a higher sharpness value
    img = ImageEnhance.Sharpness(img).enhance(150)
    return img


def crushAndBack(img):
    img = img.convert('RGB')
    w, h = img.width, img.height
    img = img.resize((int(w ** .95), int(h ** .95)), resample=Image.LANCZOS)
    img = img.resize((int(w ** .90), int(h ** .90)), resample=Image.BILINEAR)
    img = img.resize((int(w ** .90), int(h ** .90)), resample=Image.BICUBIC)
    img = img.resize((w, h), resample=Image.BICUBIC)
    return img


def main():
    userInput()

    for img_path in filepath:
        img = Image.open(img_path)
        # img = Image.opne('test2.jpg')
        img = img.convert('RGB')
        img = crushAndBack(img)
        img = generateHue(img)

        img.show()
        # img.save('output2.jpg')
        filename = os.path.splitext(os.path.basename(img_path))[0]
        img.save('%s_output.jpg' % filename)
        print("output saved as %s_output.jpg" % filename)


if __name__ == '__main__':
    main()
