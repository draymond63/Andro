import sys
src_path = 'c:\\Users\\dan\\Desktop\\Projects\\Andro\\models\\src'
sys.path.append(src_path)

from data_packed import x_test, y_test
import matplotlib.pyplot as plt

# Convert bitpacked image into plotable 2D array
def prepImg(img):
    # Create 28x28 image
    parsed_img = []
    row_index = -1  # 0 -> 27
    col_index = 0   # 0 -> 27

    for i in range(784):
        byte = img[i // 8]
        # Add a new row to the parsed image
        if col_index == 0:
            parsed_img.append([])
            row_index += 1

        # Parse out bit
        pixel = 1 if byte & ( 1 << (i % 8) ) else 0
        parsed_img[row_index].append(pixel)

        col_index += 1
        col_index %= 28
    return parsed_img

num_row = 5
num_col = 10
length = num_row * num_col # Max 50
images = x_test[:length]
labels = y_test[:length]

# plot images
# set dimensions
fig, axes = plt.subplots(num_row, num_col, figsize=(1.5*num_col,2*num_row))
# Put each image on the plot
for i in range(length):
    # Axes is a list of plt plots with built-in coordinates
    ax = axes[i//num_col, i%num_col]
    img = prepImg(images[i])
    ax.imshow(img, cmap='gray')
    ax.set_title(f'Answer: {labels[i]}')
plt.tight_layout()
plt.show()
