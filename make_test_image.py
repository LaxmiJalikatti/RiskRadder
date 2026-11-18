from PIL import Image, ImageDraw, ImageFont

lines = open("data/sample.txt", encoding="utf-8").read().splitlines()
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
image = Image.new("RGB", (1900, 80 + len(lines) * 46), "white")
draw = ImageDraw.Draw(image)
for number, line in enumerate(lines):
    draw.text((40, 40 + number * 46), line, fill="black", font=font)
image.save("data/sample_photo.png")
print("Saved data/sample_photo.png")
