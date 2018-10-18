import numpy as np
import db_utils
from unidecode import unidecode

def get_examples_to_list(file):
  a = []
  max_len_input = 0
  with open(file, 'r') as s:
    for line in s:
      sep = unidecode(line).lower().split(' > ')
      a.append([sep[0], sep[1].replace('\n', '')])
      if len(sep[0].split(' ')) > max_len_input:
        max_len_input = len(sep[0].split(' '))

  return a, max_len_input

def divide_and_convert_sample(x_y, d, max_len):
  x = []
  y = []
  lengths = []
  i = 0
  for example in x_y:
    x_n = text_to_int(example[0], d)
    x.append(np.array(x_n))
    lengths.append(len(x_n))
    if i == 0:
      y.append(np.array(text_to_int(example[1], d)+ [1] + [0] * (max_len - 3)))
      i+=1
    else:
      y.append(np.array(text_to_int(example[1], d)+ [1]))
  return numpy_fillna(np.array(x)), numpy_fillna(np.array(y)), lengths

def get_vocabulary(examples):
  v = dict()
  i = 3
  for e in examples:
    for a in e: 
      for word in a.split(' '):
        if word:
          if word not in v:
            v[word] = i
            i += 1
  return v

def reverse_dictionary(dictionary):
  new_dictionary = dict()
  for key in dictionary:
    new_dictionary[dictionary[key]] = key

  return new_dictionary

def dictionary_to_file(dictionary, file):
  with open(file, 'w') as f:
    f.write('2 <UNK>\n')
    for key in dictionary:
      f.write(str(key) + ' ' + dictionary[key] + '\n')

def text_to_int(text, dictionary=dict(), file=''):
  text_int = []
  text = unidecode(text).lower()
  if file:
    pass

  else:
    for word in text.split(' '):
      if word in dictionary:
        text_int.append(dictionary[word])
      else:
        text_int.append(2)

  return text_int

def get_sequences(file):
  sequences = []
  l, max_len_input = get_examples_to_list(file)
  d = get_vocabulary(l)
  rev_dict = reverse_dictionary(d)
  dictionary_to_file(rev_dict, 'vocabulary.txt')
  
  return divide_and_convert_sample(l, d, max_len_input)

def get_sequences_db(db):
  sequences = []
  l, max_len_input = db.get_all_samples()
  d = get_vocabulary(l)
  rev_dict = reverse_dictionary(d)
  rev_dict = {str(k): v for k, v in rev_dict.items()}
  db.save_vocabulary(rev_dict)
  #dictionary_to_file(rev_dict, 'vocabulary.txt')
  
  return divide_and_convert_sample(l, d, max_len_input)

def get_dict_from_file(file):
  dictionary = dict()
  with open(file, 'r') as f:
    for line in f:
      split = line.split(' ')
      dictionary[int(split[0])] = split[1].replace('\n', '')

  return dictionary

def get_dict_from_db(db):
  return db.get_vocabulary()

def to_int(string, file='', db=None):
  out = []
  dictionary = dict()
  string = unidecode(string).lower()
  if db:
    dictionary = get_dict_from_db(db)
  elif file:
    dictionary = get_dict_from_file(file)
  str_to_int = reverse_dictionary(dictionary)
  for word in string.split(' '):
    if word in str_to_int:
      out.append(str_to_int[word])
    else:
      out.append(2)

  return out

def to_string(integers, file='', db=None):
  out = ''
  dictionary = get_dict_from_file(file)
  for number in integers:
    if number != 1 and number != 0:
      out += dictionary[number] + ' '

  return out


def numpy_fillna(data):
  # Get lengths of each row of data
  lens = np.array([len(i) for i in data])

  # Mask of valid places in each row
  mask = np.arange(lens.max()) < lens[:,None]

  # Setup output array and put elements from data into masked positions
  out = np.zeros(mask.shape, dtype=data.dtype)
  out[mask] = np.concatenate(data)
  return out

#msg = to_int('Ola como posso ajudar', 'vocabulary.txt')
#print(to_string(msg, 'vocabulary.txt'))
#print(get_examples('sample.txt'))
'''l = get_examples_to_list('sample.txt')
print(l)
print(divide_sample(l))
d = get_vocabulary(l)
rev_dict = reverse_dictionary(d)
dictionary_to_file(rev_dict, 'vocabulary.txt')
li = text_to_int('Ola ajudar mesa', d)
print(li)'''

db = db_utils.DB()
print(get_dict_from_db(db))