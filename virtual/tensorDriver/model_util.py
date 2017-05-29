import tensorflow as tf

# References:
# https://gist.github.com/kukuruza/03731dc494603ceab0c5
# https://github.com/tensorflow/tensorflow/issues/908
# http://nbviewer.jupyter.org/github/BVLC/caffe/blob/master/examples/00-classification.ipynb
# http://stackoverflow.com/questions/35759220/how-to-visualize-learned-filters-on-tensorflow
# http://stackoverflow.com/questions/33783672/how-can-i-visualize-the-weightsvariables-in-cnn-in-tensorflow
# https://www.youtube.com/watch?v=5tW3y7lm7V0
def put_kernels_on_grid (kernel, grid_Y, grid_X, pad = 1):

    '''Visualize conv. features as an image (mostly for the 1st layer).
    Place kernel into a grid, with some paddings between adjacent filters.

    Args:
      kernel:            tensor of shape [Y, X, NumChannels, NumKernels]
      (grid_Y, grid_X):  shape of the grid. Require: NumKernels == grid_Y * grid_X
                           User is responsible of how to break into two multiples.
      pad:               number of black pixels around each filter (between them)

    Return:
      Tensor of shape [(Y+2*pad)*grid_Y, (X+2*pad)*grid_X, NumChannels, 1].
    '''

    # Normalize weights
    x_min = tf.reduce_min(kernel)
    x_max = tf.reduce_max(kernel)
    kernel1 = (kernel - x_min) / (x_max - x_min)

    # pad X and Y (Just to create a border on the grid)
    x1 = tf.pad(kernel1, tf.constant( [[pad,pad],[pad, pad],[0,0],[0,0]] ), mode = 'CONSTANT')
    # X and Y dimensions, w.r.t. padding
    Y = kernel1.get_shape()[0] + 2 * pad
    X = kernel1.get_shape()[1] + 2 * pad

    channels = kernel1.get_shape()[2]

    # put NumKernels to the 1st dimension
    x2 = tf.transpose(x1, (3, 0, 1, 2))
    # organize grid on Y axis
    x3 = tf.reshape(x2, tf.stack([grid_X, Y * grid_Y, X, channels])) #3

    # switch X and Y axes
    x4 = tf.transpose(x3, (0, 2, 1, 3))
    # organize grid on X axis
    x5 = tf.reshape(x4, tf.stack([1, X * grid_X, Y * grid_Y, channels])) #3

    # back to normal order (not combining with the next step for clarity)
    x6 = tf.transpose(x5, (2, 1, 3, 0))

    # to tf.image_summary order [batch_size, height, width, channels],
    #   where in this case batch_size == 1
    x7 = tf.transpose(x6, (3, 0, 1, 2))

    # scale to [0, 255] and convert to uint8
    return tf.image.convert_image_dtype(x7, dtype = tf.uint8)

def conv2d(x, k_h, k_w, channels_in, channels_out, stride, name="conv", viewWeights=False):
    with tf.name_scope(name):
        # Define weights
        w = tf.Variable(tf.truncated_normal([k_h,k_w, channels_in, channels_out], stddev=0.1), name="weights")
        b = tf.Variable(tf.constant(0.1, shape=[channels_out]), name="bias")    
        # Convolution
        #conv = tf.nn.conv2d(x, w, strides=[1, 1, 1, 1], padding='SAME')    
        conv = tf.nn.conv2d(x, w, strides=[1, stride, stride, 1], padding='VALID')    
        # Relu
        activation = tf.nn.relu(conv + b)
        # Add summaries for helping debug
        tf.summary.histogram("weights", w)
        tf.summary.histogram("bias", b)
        tf.summary.histogram("activation", activation)
        
        # Visualize weights if needed
        if viewWeights == True:                        
            tf.summary.image("W_grid", put_kernels_on_grid(w,3,8), 1)            
            
        return activation

def max_pool(x, k_h, k_w, S, name="maxpool"):
    with tf.name_scope(name):
        return tf.nn.max_pool(x, ksize=[1, k_h, k_w, 1],strides=[1, S, S, 1], padding='SAME')

def fc_layer(x, channels_in, channels_out, name="fc"):
    with tf.name_scope(name):
        w = tf.Variable(tf.truncated_normal([channels_in, channels_out], stddev=0.1), name="weights")
        b = tf.Variable(tf.constant(0.1, shape=[channels_out]), name="bias")    
        activation = tf.nn.relu(tf.matmul(x, w) + b)
        # Add summaries for helping debug
        tf.summary.histogram("weights", w)
        tf.summary.histogram("bias", b)
        tf.summary.histogram("activation", activation)
        return activation

def output_layer(x, channels_in, channels_out, name="output"):
    with tf.name_scope(name):
        w = tf.Variable(tf.truncated_normal([channels_in, channels_out], stddev=0.1), name="weights")
        b = tf.Variable(tf.constant(0.1, shape=[channels_out]), name="bias")    
        activation = tf.matmul(x, w) + b
        # Add summaries for helping debug
        tf.summary.histogram("weights", w)
        tf.summary.histogram("bias", b)
        tf.summary.histogram("activation", activation)
        return activation    

def bound_layer(val_in, bound_val, name="bound_scale"):
    with tf.name_scope(name):        
        # Bound val_in between -1..1 and scale by multipling by bound_val
        activation = tf.multiply(tf.atan(val_in), bound_val)
        # Add summaries for helping debug        
        tf.summary.histogram("val_in", val_in)
        tf.summary.histogram("activation", activation)
        return activation


def create_input_graph(list_files, num_epochs, batch_size):
    with tf.name_scope('input_handler'):
        filename_queue = tf.train.string_input_producer(list_files, num_epochs=num_epochs)

        # Read files from TFRecord list
        image, label = read_decode_tfrecord_list(filename_queue)

        # Shuffle examples
        #images, labels = tf.train.shuffle_batch (
        #    [image, label], batch_size=batch_size, num_threads=3,
        #    capacity=50000,
        #    # Ensures a minimum amount of shuffling of examples.
        #    min_after_dequeue=10000)
        example_list = [read_decode_tfrecord_list(filename_queue)
                        for _ in range(3)]
        images, labels = tf.train.shuffle_batch_join(
            example_list, batch_size=batch_size,
            capacity=50000,
            # Ensures a minimum amount of shuffling of examples.
            min_after_dequeue=10000)

    return images, labels

def read_decode_tfrecord_list(file_list):
    ''''Read TFRecord content'''
    reader = tf.TFRecordReader()
    _, serialized_example = reader.read(file_list)
    features = tf.parse_single_example(
        serialized_example,
        # Defaults are not specified since both keys are required.
        features={
            'image': tf.FixedLenFeature([], tf.string),
            'shape': tf.FixedLenFeature([], tf.string),
            'label': tf.FixedLenFeature([], tf.float32),
        })

    shape = tf.decode_raw(features['shape'], tf.uint8)
    #print('Shape (shape) is:', shape.shape)
    image = tf.decode_raw(features['image'], tf.uint8)
    #print('Shape (image) is:', image.shape)
    label = tf.cast(features['label'], tf.float32)

    # TODO: Infer from shape field from TFRecord
    image.set_shape([256* 256* 3])
    image = tf.reshape(image, [256, 256, 3])

    image, label = process_features(image, label)


    return image, label

# Reference:
# http://stackoverflow.com/questions/37299345/using-if-conditions-inside-a-tensorflow-graph
# https://github.com/tensorflow/models/blob/master/inception/inception/image_processing.py
# http://stackoverflow.com/questions/42147427/tensorflow-how-to-randomly-crop-input-images-and-labels-in-the-same-way
# https://indico.io/blog/tensorflow-data-input-part2-extensions/
# http://stackoverflow.com/questions/36088277/how-to-select-rows-from-a-3-d-tensor-in-tensorflow
def process_features(image, label):
    # Do any image preprocessing/augmentation here...
    with tf.name_scope('process_features'):

        # Crop driving view (Start from row 126, and slice 100 rows)
        image = tf.slice(image, [126, 0, 0], [100, 256, 3])

        # Resize image
        image = tf.image.resize_images(image, [66, 200])

        # Change or not change colors
        def do_color_changes():
            distorted_image = tf.image.random_brightness(image, max_delta=63)
            distorted_image = tf.image.random_saturation(distorted_image, lower=0.5, upper=1.5)
            distorted_image = tf.image.random_hue(distorted_image, max_delta=0.2)
            distorted_image = tf.image.random_contrast(distorted_image, lower=0.2, upper=1.8)
            return distorted_image

        def no_color_change():
            distorted_image = image
            return distorted_image
        # Uniform variable in [0,1)
        flip_coin_color = tf.random_uniform(shape=[], minval=0., maxval=1., dtype=tf.float32)
        pred_color = tf.less(flip_coin_color, 0.5)
        # Randomically select doing color augmentation
        image = tf.cond(pred_color, do_color_changes, no_color_change, name='if_color')

        # Change or not change colors
        def flip_image_steering():
            distorted_image = tf.image.flip_left_right(image)
            distorted_label = -label
            return distorted_image, distorted_label

        def no_flip_image_steering():
            distorted_image = image
            distorted_label = label
            return distorted_image, distorted_label
        # Uniform variable in [0,1)
        flip_coin_flip = tf.random_uniform(shape=[], minval=0., maxval=1., dtype=tf.float32)
        pred_flip = tf.less(flip_coin_flip, 0.5)
        # Randomically select doing color augmentation
        image, label = tf.cond(pred_flip, flip_image_steering, no_flip_image_steering, name='if_steering')


        # Convert from [0, 255] -> [-0.5, 0.5] floats.
        image = tf.cast(image, tf.float32) * (1. / 255.0)

    return image, label


# Define the huber loss (More resilient against outliers)
def huber_loss(self, delta=1.0):
    with tf.name_scope('Huber_Loss'):
        # Calculate a residual difference (error)
        residual = tf.abs(self.labels - self.pred)

        # Check if error is bigger than a delta
        condition = tf.less(residual, delta)

        # Absolute error
        small_res = 0.5 * tf.square(residual)

        # L2
        large_res = (delta * residual) - 0.5 * tf.square(delta)

        # Decide between L2 and absolute error
        return tf.where(condition, small_res, large_res)