from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import json
import os
from tensorflow.keras import layers, models, Model, Sequential


def AlexNet_pytorch(im_height=224, im_width=224, class_num=1000):
    # tensorflow中的tensor通道排序是NHWC
    input_image = layers.Input(shape=(im_height, im_width, 3), dtype="float32")  # output(None, 224, 224, 3)
    x = layers.ZeroPadding2D(((2, 1), (2, 1)))(input_image)                      # output(None, 227, 227, 3)
    x = layers.Conv2D(64, kernel_size=11, strides=4, activation="relu")(x)       # output(None, 55, 55, 64)
    x = layers.MaxPool2D(pool_size=3, strides=2)(x)                              # output(None, 27, 27, 64)
    x = layers.Conv2D(192, kernel_size=5, padding="same", activation="relu")(x)  # output(None, 27, 27, 192)
    x = layers.MaxPool2D(pool_size=3, strides=2)(x)                              # output(None, 13, 13, 128)
    x = layers.Conv2D(384, kernel_size=3, padding="same", activation="relu")(x)  # output(None, 13, 13, 384)
    x = layers.Conv2D(256, kernel_size=3, padding="same", activation="relu")(x)  # output(None, 13, 13, 256)
    x = layers.Conv2D(256, kernel_size=3, padding="same", activation="relu")(x)  # output(None, 13, 13, 256)
    x = layers.MaxPool2D(pool_size=3, strides=2)(x)                              # output(None, 6, 6, 256)

    x = layers.Flatten()(x)                         # output(None, 6*6*256)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(4096, activation="relu")(x)    # output(None, 4096)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(4096, activation="relu")(x)    # output(None, 4096)
    x = layers.Dense(class_num)(x)                  # output(None, 5)
    predict = layers.Softmax()(x)

    model = models.Model(inputs=input_image, outputs=predict)
    return model


data_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))  # get data root path
image_path = data_root + "/data_set/flower_data/"  # flower data set path
train_dir = image_path + "train"
validation_dir = image_path + "val"

# create direction for saving weights
if not os.path.exists("save_weights"):
    os.makedirs("save_weights")

im_height = 224
im_width = 224
batch_size = 32
epochs = 10


def pre_function(img: np.ndarray):
    # from PIL import Image as im
    # import numpy as np
    # img = im.open('test.jpg')
    # img = np.array(img).astype(np.float32)
    img = img / 255.
    img = img - [0.485, 0.456, 0.406]
    img = img / [0.229, 0.224, 0.225]

    return img


# data generator with data augmentation
train_image_generator = ImageDataGenerator(horizontal_flip=True,
                                           preprocessing_function=pre_function)
validation_image_generator = ImageDataGenerator(preprocessing_function=pre_function)

train_data_gen = train_image_generator.flow_from_directory(directory=train_dir,
                                                           batch_size=batch_size,
                                                           shuffle=True,
                                                           target_size=(im_height, im_width),
                                                           class_mode='categorical')
total_train = train_data_gen.n

# get class dict
class_indices = train_data_gen.class_indices

# transform value and key of dict
inverse_dict = dict((val, key) for key, val in class_indices.items())
# write dict into json file
json_str = json.dumps(inverse_dict, indent=4)
with open('class_indices.json', 'w') as json_file:
    json_file.write(json_str)

val_data_gen = validation_image_generator.flow_from_directory(directory=validation_dir,
                                                              batch_size=batch_size,
                                                              shuffle=False,
                                                              target_size=(im_height, im_width),
                                                              class_mode='categorical')
total_val = val_data_gen.n

model = AlexNet_pytorch(im_height=im_height, im_width=im_width, class_num=5)
model.load_weights('./pretrain_weights.ckpt')
for layer_t in model.layers:
    if 'conv2d' in layer_t.name:
        layer_t.trainable = False

model.summary()

# using keras high level api for training
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
              loss=tf.keras.losses.CategoricalCrossentropy(from_logits=False),
              metrics=["accuracy"])

callbacks = [tf.keras.callbacks.ModelCheckpoint(filepath='./save_weights/myAlex.h5',
                                                save_best_only=True,
                                                save_weights_only=True,
                                                monitor='val_loss')]

# tensorflow2.1 recommend to using fit
history = model.fit(x=train_data_gen,
                    steps_per_epoch=total_train // batch_size,
                    epochs=epochs,
                    validation_data=val_data_gen,
                    validation_steps=total_val // batch_size,
                    callbacks=callbacks)

# plot loss and accuracy image
history_dict = history.history
train_loss = history_dict["loss"]
train_accuracy = history_dict["accuracy"]
val_loss = history_dict["val_loss"]
val_accuracy = history_dict["val_accuracy"]

# figure 1
plt.figure()
plt.plot(range(epochs), train_loss, label='train_loss')
plt.plot(range(epochs), val_loss, label='val_loss')
plt.legend()
plt.xlabel('epochs')
plt.ylabel('loss')

# figure 2
plt.figure()
plt.plot(range(epochs), train_accuracy, label='train_accuracy')
plt.plot(range(epochs), val_accuracy, label='val_accuracy')
plt.legend()
plt.xlabel('epochs')
plt.ylabel('accuracy')
plt.show()
