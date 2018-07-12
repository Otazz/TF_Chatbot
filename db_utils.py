from pymongo import MongoClient
from unidecode import unidecode


class DB(object):
	def __init__(self, db='chat', address='localhost', port=27017):
		self.client = MongoClient(address, port)
		self.db = self.client[db]
		self.inp = self.db.inputs
		self.vocabulary = self.db.vocabulary
		self.samples = self.db.samples

	def save_input(self, input):
		inp = self.db.inputs
		inp.insert_one(input)

	def get_all_samples(self):
		max_len = 0
		sentences = []
		cursor = self.samples.find({})

		for example in cursor:
			in_s = example['input']
			sentences.append((in_s, example['target']))
			if len(in_s.split(' ')) > max_len:
				max_len = len(in_s.split(' '))

		return sentences, max_len

	def get_vocabulary(self):
		return {int(k): v for k, v in self.vocabulary.find({})[0].items() if k != '_id'}

	def save_samples_from_file(self, file):
		self.samples.drop()
		with open(file, 'r') as s:
			for line in s:
				sep = unidecode(line).lower().split(' > ')
				self.samples.insert_one({
																'input': sep[0],
																'target': sep[1].replace('\n', '')
																})

	def save_vocabulary(self, dic):
		self.vocabulary.insert_one(dic)
