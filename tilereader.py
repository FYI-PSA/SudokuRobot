from tensorflow.keras import models as kmodels
import numpy as np


def load_model(filename: str = 'retrained_network.keras'):
    # model = kmodels.load_model(filename)
    model = kmodels.load_model(filename, compile=False)  # Gets rid of the warning. I don't think it has an effect on how the model works, but not sure. Tests work out fine as before.
    return model


def grayscale_numpy_tiles_list_to_predicted_integer_list(model: kmodels.Model, tiles: list) -> list:
    images_arr = np.asarray(tiles, dtype=np.uint8)
    img_arr_data = np.array(images_arr, dtype=np.float32)
    tile_arr_data = img_arr_data / 255
    # I don't know why it wants another channel
    # seems to work without it
    # I will still keep this line of code in case something breaks.
    # tile_arr_data = np.expand_dims(tile_arr_data, axis=-1)
    predictions = model.predict(tile_arr_data, verbose=0)
    predicted_classes = np.argmax(predictions, axis=1)
    predicted_classes_normal = [int(n) for n in predicted_classes]  # The return value should be a list of ints, not a nparray of np.int64
    # print(tile_arr_data.shape)
    # print(predicted_classes)
    return predicted_classes_normal
