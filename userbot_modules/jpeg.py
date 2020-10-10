import math

from PIL import Image


def jpegify(download_res: str) -> str:
    if download_res.endswith(".png") or download_res.endswith(".jpg") or download_res.endswith(".jpeg") or \
            download_res.endswith(".webp"):
        if download_res.endswith(".png") or download_res.endswith(".webp"):
            im = Image.open(download_res)
            im = im.convert('RGB')
            im.save(download_res.replace(".png", ".jpg").replace(".webp", ".jpg"))
        image = Image.open(download_res.replace(".png", ".jpg").replace(".webp", ".jpg"))
        x, y = image.size
        x2, y2 = math.floor(x / 2).__round__(0), math.floor(y / 2).__round__(0)
        image = image.resize((x2, y2), Image.ANTIALIAS)
        out_name = "out_" + download_res + ".jpg"
        image.save(out_name, quality=1, optimize=True)
        return out_name
    return "NULL"
