import os
import tensorflow as tf
from deepface import DeepFace
selfie="./selfie/"
cnic="./cnic/"
print("Working...")
compute = tf.config.list_physical_devices()
for device in compute:
    print(device)
with tf.device('/CPU:0'):
	a = tf.constant([1.0, 2.0, 3.0])
	b = tf.constant([4.0, 5.0, 6.0])
	c = a * b
print("Result of GPU operation:", c)
for filename in os.listdir(selfie):
	if os.path.isfile(f"{selfie}{filename}") and os.path.isfile(f"{cnic}{filename}"):
		print(DeepFace.verify(img1_path = f'{selfie}img1.jpg', img2_path = f'{cnic}img2.jpg'))