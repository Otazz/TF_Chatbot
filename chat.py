import numpy as np
import tensorflow as tf
import example_utils
from tensorflow.contrib.rnn import LSTMCell, LSTMStateTuple



class Seq2Seq(object):
  def __init__(self):
    tf.reset_default_graph()
    self.sess = tf.InteractiveSession()

    PAD = 0
    EOS = 1

    vocab_size = 100
    input_embedding_size = 20

    encoder_hidden_units = 20
    decoder_hidden_units = encoder_hidden_units * 2

    self.encoder_inputs = tf.placeholder(shape=(None, None), dtype=tf.int32, name='self.encoder_inputs')
    self.encoder_inputs_length = tf.placeholder(shape=(None, ), dtype=tf.int32, name='self.encoder_inputs_length')

    self.decoder_targets = tf.placeholder(shape=(None, None), dtype=tf.int32, name='self.decoder_targets')

    embeddings = tf.Variable(tf.random_uniform([vocab_size, input_embedding_size], -1.0, 1.0), dtype=tf.float32)

    #---------- ENCODE --------------

    self.encoder_inputs_embedded = tf.nn.embedding_lookup(embeddings, self.encoder_inputs)

    encoder_cell = LSTMCell(encoder_hidden_units)

    ((encoder_fw_outputs, encoder_bw_outputs), 
      (encoder_fw_final_state, encoder_bw_final_state)) = (
        tf.nn.bidirectional_dynamic_rnn(cell_fw=encoder_cell,
                        cell_bw=encoder_cell,
                        inputs=self.encoder_inputs_embedded,
                        sequence_length=self.encoder_inputs_length,
                        dtype=tf.float32, time_major=True)
      )

    encoder_outputs = tf.concat((encoder_fw_outputs, encoder_bw_outputs), 2)

    encoder_final_state_c = tf.concat(
        (encoder_fw_final_state.c, encoder_bw_final_state.c), 1)

    encoder_final_state_h = tf.concat(
        (encoder_fw_final_state.h, encoder_bw_final_state.h), 1)

    encoder_final_state = LSTMStateTuple(
        c=encoder_final_state_c,
        h=encoder_final_state_h
    )

    # ------------- DECODE ---------------

    decoder_cell = LSTMCell(decoder_hidden_units)

    encoder_max_time, batch_size = tf.unstack(tf.shape(self.encoder_inputs))

    decoder_lengths = self.encoder_inputs_length + 3

    W = tf.Variable(tf.random_uniform([decoder_hidden_units, vocab_size], -1, 1), dtype=tf.float32)
    b = tf.Variable(tf.zeros([vocab_size]), dtype=tf.float32)

    assert EOS == 1 and PAD == 0

    eos_time_slice = tf.ones([batch_size], dtype=tf.int32, name='EOS')
    pad_time_slice = tf.zeros([batch_size], dtype=tf.int32, name='PAD')

    eos_step_embedded = tf.nn.embedding_lookup(embeddings, eos_time_slice)
    pad_step_embedded = tf.nn.embedding_lookup(embeddings, pad_time_slice)

    def loop_fn_initial():
      initial_elements_finished = (0 >= decoder_lengths)
      initial_input = eos_step_embedded
      initial_cell_state = encoder_final_state
      initial_cell_output = None
      initial_loop_state = None
      return (initial_elements_finished,
              initial_input,
              initial_cell_state,
              initial_cell_output,
              initial_loop_state)

    def loop_fn_transition(time, previous_output, previous_state, previous_loop_state):

      def get_next_input():
        output_logits = tf.add(tf.matmul(previous_output, W), b)
        prediction = tf.argmax(output_logits, axis=1)
        next_input = tf.nn.embedding_lookup(embeddings, prediction)
        return next_input

      elements_finished = (time >= decoder_lengths)

      finished  = tf.reduce_all(elements_finished)
      input = tf.cond(finished, lambda: pad_step_embedded, get_next_input)
      state = previous_state
      output = previous_output
      loop_state = None

      return (elements_finished,
              input,
              state, 
              output,
              loop_state)

    def loop_fn(time, previous_output, previous_state, previous_loop_state):
      if previous_state is None:
        assert previous_output is None and previous_state is None
        return loop_fn_initial()
      else:
        return loop_fn_transition(time, previous_output, previous_state, previous_loop_state)


    decoder_outputs_ta, decoder_final_state, _ = tf.nn.raw_rnn(decoder_cell, loop_fn)
    decoder_outputs = decoder_outputs_ta.stack()

    decoder_max_steps, decoder_batch_size, decoder_dim = tf.unstack(tf.shape(decoder_outputs))
    decoder_outputs_flat = tf.reshape(decoder_outputs, (-1, decoder_dim))
    decoder_logits_flat = tf.add(tf.matmul(decoder_outputs_flat, W), b)
    decoder_logits = tf.reshape(decoder_logits_flat, (decoder_max_steps, decoder_batch_size, vocab_size))

    self.decoder_prediction = tf.argmax(decoder_logits, 2)

    self.stepwise_cross_entropy = tf.nn.softmax_cross_entropy_with_logits(
        labels=tf.one_hot(self.decoder_targets, depth=vocab_size, dtype=tf.float32),
        logits=decoder_logits,
    )

    

  def train(self, file_name='sample.txt', max_batches=3001, batches_in_epoch=1000):
    loss = tf.reduce_mean(self.stepwise_cross_entropy)
    train_op = tf.train.AdamOptimizer().minimize(loss)

    self.sess.run(tf.global_variables_initializer())
    loss_track = []

    try:
      batchy, target, lens = example_utils.get_sequences(file_name)
      for batch in range(max_batches):
        fd = {
          self.encoder_inputs: batchy.T,
          self.encoder_inputs_length: lens,
          self.decoder_targets: target.T
        }
        #batch, target = example_utils.get_sequences('sample.txt')
        _, l = self.sess.run([train_op, loss], fd)
        loss_track.append(1)
        if (batch == 0 or batch % batches_in_epoch == 0) and False:
          print('batch {}'.format(batch))
          print(' minibatch loss: {}'.format(self.sess.run(loss, fd)))
          predict_ = self.sess.run(self.decoder_prediction, fd)
          for i, (inp, pred) in enumerate(zip(fd[self.encoder_inputs].T, predict_.T)):
            print(' sample {}'.format(i+1))
            print(' input   > {}'.format(inp))
            print(' predicted > {}'.format(pred))
            if i >= 5:
              break
            print()

      return "Sucess"

    except KeyboardInterrupt:
      print('training interrupted')

    return "Fail"

  def predict(self, text):
    message = example_utils.to_int(text, 'vocabulary.txt')
    answer = self.sess.run(self.decoder_prediction, feed_dict={self.encoder_inputs:np.array([message]).T, self.encoder_inputs_length: [len(message)]})
    decoded = example_utils.to_string(answer.T[0], 'vocabulary.txt')
    
    return decoded