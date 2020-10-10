import os


def cleanup(download_res: str):
    os.remove(download_res.replace(".png", ".jpg").replace(".webp", ".jpg"))
    os.remove("out_" + download_res + ".jpg")
    os.remove(download_res + ".jpg")
    os.remove(download_res)
    os.remove("sticker.webp")
