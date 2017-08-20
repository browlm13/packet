#python 3

"""
	
	pack data structure


	map: represents the tag order and byte sizes help by the pack object, used for construction

		format:  [ [tag,size], ... , [tag,size] ] 	#where size is in bytes

	internally the pack contains a datastructure of the following format

		guts = [ [tag, data], ... , [tag, data] ] #where tag is a string and data is a bytearray


	indexing:

		-indexing with p[] (square brackets) returns a pack object with the feilds specified
			-indexing targets tags and their index in the map structure order, not the byte number
			exception: a single index returns a bytearray data type correspoding to the tag indexed

		-the () operator will return the pack's bytearrays concatinated in order
			-(tag,index) : aditional indexing will only return 
				those feilds indexeds (in order indexed) as concatinated bytearray

		-p.map() will return the map datastructure used for pack creation
			-p.map(tag,index...) additional feilds will return a map datastructure 
				of the feilds specified (in order specified)

	[todo]:
		which
		random fills?

		change map for existing for feild change (like payload split)
			-only works for same size bytes

"""
import struct
import random

#
#	useful functions
#
def concat(g): 
	r = next(g)
	for i in g: r += i
	return r

bytearray_generator = lambda length: concat(bytearray(struct.pack('B', random.randint(0,255))) for i in range(length))


class pack():

	def guts_to_bytearray(self, guts): 
		ba = bytearray()
		for i in guts: ba += i[1]
		return ba

	def guts_to_map(self, guts):
		return [ [i[0],len(i[1])] for i in guts ]

	def rank(self, tag=None):
		if tag == None:
			return len(self)-1
		tags, contents = zip(*self.guts)
		return tags.index(tag)

	#obtain tag name from rank
	def tag(self, rank):
		return self.guts[rank][0]

	def start_byte(self,tag):
		if self.rank(tag) == 0:
			return 0
		return len(self[:tag]())

	def end_byte(self,tag):
		index = self.rank(tag) + 1
		return len(self[:index]())

	def remove(self, *tags):
		trash_tags = [t for t in tags]

		#if rank/index, convert to tag
		for i in range(0,len(trash_tags)):
			if type(trash_tags[i]) == int:
				trash_tags[i] = self.tag(trash_tags[i])

		saved_tags = [i[0] for i in self.map() if i[0] not in trash_tags]
		new_map = self.map(*saved_tags)
		np = pack(new_map)

		for t in saved_tags:
			np[t] = self[t]

		self.__init__(np)

	def insert(self,rank,tag,ba):

		assert tag not in self
		additional_pack = pack([[tag,len(ba)]])
		additional_pack[tag] = ba

		if rank == 0:
			additional_pack.append(self)
			self.__init__(additional_pack)

		elif rank == len(self):
			self.append(additional_pack)
		else:
			pre_pack = self[:rank]
			post_pack = self[rank:]

			new_map = pre_pack.map() + additional_pack.map() + post_pack.map()
			np = pack(new_map)
			np <<= pre_pack() + additional_pack() + post_pack()

			self.__init__(np)

	def append(self,tail_pack):
		new_map = self.map() + tail_pack.map()
		np = pack(new_map)
		np <<= self() + tail_pack()
		self.__init__(np)

	def zero(self,*tags):
		if len(tags) == 0:
			self <<= bytearray(self.size_bytes())
		for t in tags:
			self[t] = bytearray(len(self[t]))

	def is_guts(self, arg):
		try:
			tags, contents = zip(*arg)
			for i in range(len(arg)):

				#ensure tag is string
				if type(tags[i]) != str: 
					raise Exception("Error: Tags must be type str.")

				#ensure that contents are of type bytearry
				if type(contents[i]) != bytearray: 
					raise Exception("Error: Guts must contain bytearray as content.")

			#ensure tags are unique
			if len(set(tags)) != len(tags): 
				raise Exception("Error: Tags must be unique.")	
		except: return False
		return True


	def is_map(self, arg):
		""" Ensure map formatting """
		try:
			tags, sizes = zip(*arg)
			for i in range(len(arg)):

				#ensure tag is string
				if type(tags[i]) != str: 
					raise Exception("Error: Tags must be type str.")

				#ensure size is int and greater than 0
				if (type(sizes[i]) != int) or (sizes[i] <= 0): 
					raise Exception("Error: Sizes must be int > 0.")

			#ensure tags are unique
			if len(set(tags)) != len(tags): 
				raise Exception("Error: Tags must be unique.")	
		except: return False
		return True

	#return map comprised of entire map or selected segments
	def map(self, *indexs):

		if len(indexs) == 0:		#.map() -> returns entire map
			return self.guts_to_map(self.guts)

		guts = list(filter(lambda i: (i[0] in indexs) or (self.rank(i[0]) in indexs), self.guts))
		return self.guts_to_map(guts)

	#remap -- takes new map of diffrent size
	def remap(self, map):

		#ennsure sizes match
		assert len(self()) ==  sum( (len(i[1]) for i in map) )

		np = pack(map)
		np <<= self()
		return np


	def __init__(self, initializer):
		""" pack takes a map, or another pack as its initializer """

		#empty pack object length 0
		if initializer == []:
			raise ValueError('Pack initialized with empty list')

		if type(initializer) == pack:
			self.guts = list(initializer.guts)

		elif self.is_guts(initializer):
			self.guts = initializer

		else:
			assert self.is_map(initializer)
			self.guts = [ [i[0], bytearray(i[1])] for i in initializer ]


	def __getitem__(self, indexer):

		if type(indexer) == int:
			return self.guts[indexer][1]

		if type(indexer) == str:
			return self.guts[self.rank(indexer)][1]

		if type(indexer) == slice:
			start, stop, step = indexer.start, indexer.stop, None

			if type(start) == str:
				start = self.rank(start)

			if type(stop) == str:
				stop = self.rank(stop)

			if start == None:
				start = 0

			if stop == None:
				stop = len(self.guts)

			#create reduced size pack object and return
			guts = []
			for i in range(start,stop):
				guts += [self.guts[i]]

			return pack(guts)


	def __setitem__(self, indexer, value_bytearray):

		assert type(value_bytearray) == bytearray

		if type(indexer) == int:
			self.guts[indexer][1] = value_bytearray

		if type(indexer) == str:
			self.guts[self.rank(indexer)][1] = value_bytearray

	#return bytearray with p(), or bytearray of indexed params in passed order 
	def __call__(self, *indexs):
		if len(indexs) == 0:
			return self.guts_to_bytearray(self.guts)

		selected = filter(lambda i: (i[0] in indexs) or (self.rank(i[0]) in indexs), self.guts)
		return self.guts_to_bytearray(selected)

	def __len__(self):
		return len(self.guts)

	#[todo]: take feilds as well
	def size_bytes(self):
		return sum( (len(i[1]) for i in self.guts) )

	def __repr__(self):
		tags, contents = zip(*self.guts)
		sizes = [len(i) for i in contents]
		ranks = tuple(self.rank(i) for i in tags)
		eq0 = tuple(map(lambda i: bytearray(len(self[i])) == self[i], tags))

		s = "rank:\ttag:\tsize:\tzero:\n"
		for i in range(len(self)):
			s += ("%d\t%s\t%d\t%r\n" % (ranks[i],tags[i],sizes[i],eq0[i]))

		return s

	def __bytearray__(self):
		return self()

	#label in p
	def __contains__(self, tag):
		if tag in [i[0] for i in self.guts]: return True
		return False


	#import byte array with <<= instead of [:], must be same length as guide/map
	def __ilshift__(self, raw_data):
		assert len(raw_data) == self.size_bytes()

		#break data into chunks of content sizes and set ==
		sizes = [len(i[1]) for i in self.guts]

		index = 0
		for i in range(len(sizes)):
			self.guts[i][1] = raw_data[index:index+sizes[i]]
			index += sizes[i]
	

		return self


	#import bytearray with ^=, read until full, bytearray must be at least as long as guide/map
	def __ixor__(self, raw_data):
		assert len(raw_data) >= self.size_bytes()
		return self.__ilshift__(raw_data[:self.size_bytes()])

	#import bytearray with |=, read until empty
	def __ior__(self, raw_data):
		assert len(raw_data) <= self.size_bytes()
		dif = len(self()) - len(raw_data)

		if dif == 0:
			return self.__ilshift__(raw_data)

		nba = raw_data + self()[-dif:]
		return self.__ilshift__(nba)

	#concatinate pack object to pack
	def __add__(self, rhs):
		assert type(rhs) == pack
		nm = self.map() + rhs.map()
		np = pack(nm)
		np <<= self() + rhs()
		return np

	#concatinate += pack object to pack
	def __iadd__(self, rhs):
		assert type(rhs) == pack
		self.append(rhs)
		return self


"""
	Testing
"""


"""
#test creation

m = [['t1',1],['t2',2],['t3',3], ['crc',2]]
p = pack(m)

p['crc'] = bytearray_generator(2)
p['t1'] = bytearray_generator(1)
p['t2'] = bytearray_generator(2)

print (p)
print (p())
#check setting crc

"""

"""
m2 = [['t1',1],['t2',2],['t3',3]]
p2 = pack(m2)
p2 <<= p[:'crc']()
print (p2)
print (p2())

#or
p2 = p[:'crc']
print (p2)
print (p2())


#new feilds
m1 = [['t1',2],['t2',2],['t3',2], ['crc',2]]
p1 = pack(m1)
p1['t2'] = bytearray_generator(2)

m2 = [['t1',2],['t2a',1],['t2b',1],['t3',2], ['crc',2]]
p2 = pack(m2)
p2 <<= p1()

print(p1)
print(p2)

"""
