import itertools
import math

class Factor:

	'''
		Abstract Class describing a factor object
	'''


	def __init__(self, id, input_variables=None):
		'''
			-input_variables : a tuple of tuples, of the inputs and dimension:
				(1, 2), (2, 2), (3, 3), ...
			-id : unique id for this factor
		'''
		self.id = id
		if not input_variables:
			self.probs = {}
		else:
			self.input_variables = input_variables
			self.generateStates()
			self.tables = self.makeTable()

	def getID(self):
		return self.id

	@staticmethod
	def readFactors(lines):
		'''
		Static method takes an input stream and parses it to generate a new factor object
		'''

		factorID = 0

		number_factors = None
		new_factor = Factor(factorID)
		new_factor.var_num = None
		new_factor.input_variables = None
		new_factor.dims = None
			
		prob_lines = None

		for line in lines:	

			line = line.rstrip('\r\n\t ')

			if line.isspace():
				continue

			# the first line should be the number of factors
			if not number_factors:
				number_factors = int(line)
				continue
			# and stop after the last factor has been read
			elif number_factors == factorID:
				break

			if not new_factor.var_num:
				new_factor.var_num = line
			elif not new_factor.input_variables:
				new_factor.input_variables = line.split(" ")
			elif not new_factor.dims:
				new_factor.dims = line.split(" ")
				# this is a bit of a hack: input_variables should be a set of tuples, with each
				# variable, paired with it's dimension
				nv = []
				for i in range(0,len(new_factor.dims)):
					nv.append((new_factor.input_variables[i], int(new_factor.dims[i])))
				new_factor.input_variables = nv
				# generate the ordered set of states
				new_factor.generateStates()
			elif not prob_lines:
				prob_lines = int(line)
			else:
				# set the probability 
				prob_lines -= 1
				idx, val = line.split()
				new_factor.setProb(int(idx), float(val))
					
				if prob_lines == 0:
					# on the last line of a block
					yield new_factor

					# set a new factor
					factorID += 1
					new_factor = Factor(factorID)		
					new_factor.var_num = None
					new_factor.input_variables = None
					new_factor.dims = None
			
					prob_lines = None
				
	def setProb(self, state_index, prob):
		state = self.states[state_index]	
		self.probs[state] = prob

	def generateStates(self):

		states = self.iterateStates(self.input_variables)
		self.states = []
		for state in states:
			self.states.append(tuple(self.flatten(state)))

	def iterateStates(self, variables):
		''' take the first variable, iterate over the possible states of the 
			next variables, in order
		'''
		states = []
		var, dim = variables[-1]

		if len(variables) == 1:
			for value in range(0,dim):
				states.append([value])
			return states

		for value in range(0,dim):
			for state in self.iterateStates(variables[0:len(variables)-1]):
				states.append([state, value])
			
		return states	

	def computeMI(self, tuple):
		
		# set-- 
		STATE_OFF = 0
		STATE_N = 1
		STATE_ON = 2

		aa = self.computeMIcompare(STATE_ON, STATE_ON, tuple)
		ii = self.computeMIcompare(STATE_OFF, STATE_OFF, tuple)
		ai = self.computeMIcompare(STATE_ON, STATE_OFF, tuple)
		ia = self.computeMIcompare(STATE_OFF, STATE_ON, tuple)
	
		activating = aa+ii
		inactivating = ai+ia

		return (activating, inactivating)
		
	def computeMIcompare(self, STATE1, STATE2, tuple):
		'''
			Compute the pairwise MI between these variables being in the specified states, 
			using the factor probability table for computation.

			STATE1: the state of interest for variable one 
			STATE2: state of interest for the second variable
		'''
		varIDX1 = tuple[0]
		varIDX2 = tuple[1]
		# compute (p(x=1,y=1) , p(x=1) and p(y=1)
		p12, pn12 = (0, 0)
		p1, pn1 = (0, 0)
		p2, pn2  = (0, 0)

		for state in self.states:
			p = self.probs[state]
			s1, s2 = (state[int(varIDX1)], state[int(varIDX2)])
			if s1 == STATE1:
				p1 += p
			else:
				pn1 += p

			if s2 == STATE2:
				p2 += p
			else:
				pn2 += p

			if s1 == STATE1 and s2 == STATE2:
				p12 += p
			else:
				pn12 += p

		p_1 = p1/(pn1+p1)
		p_2 = p2/(pn2+p2)
		p_12 = p12/(p12 + pn12)
		# pairwise MI in bits
		mi = p_12*math.log((p_12/(p_1*p_2)), 2)
		return mi


	def flatten(self, q):
		"""
		a recursive function that flattens a nested list q
		"""
		flat_q = []
		for x in q:
			# may have nested tuples or lists
			if type(x) in (list, tuple):
				flat_q.extend(self.flatten(x))
			else:
				flat_q.append(x)
		return flat_q
		
	def makeTable(self):
		
		raise Exception("Subclass must implement this method")

	def printFactor(self, fh):

		# print the number of input_variables on which this factor depends
		fh.write(str(len(self.input_variables))+"\n")
		vars = []
		dims = []
		for (var, dim) in self.input_variables:
			vars.append(var)
			dims.append(dim)
		fh.write(" ".join([str(i) for i in vars])+"\n")
		fh.write(" ".join([str(i) for i in dims])+"\n")
		# the number of states following
		fh.write(str(len(self.states))+"\n")
		# enumerate each state
		index = 0
		for state in self.states:
			prob = self.probs[state]
			fh.write(str(index)+" "+str(prob)+"\n")
			index += 1
		fh.write("\n")

class AC_Factor(Factor):
	'''
	Represents an activating link for two nodes, with 3 states each: -1, 0, 1
	'''
	def makeTable(self):
		'''
		Iterate over all possible states of input variables: set the 
		'''
		MAJOR = 0.6
		INT = 0.333
		MINOR = 0.2
		# P(B|A) 
		# A = 0 , B = 0 0.6
		# A = 1 , B = 0 0.333
		# A = 2 , B = 0 0.2
		# A = 0 , B = 1 0.2
		# A = 1 , B = 1 0.333
		# A = 2 , B = 1 0.2
		# A = 0 , B = 2 0.2
		# A = 1 , B = 2 0.333
		# A = 2 , B = 2 0.6

		self.probs = {}
		for state in self.states:
			if state[0] == 1:
				# this is the neutral state: 
				# set to no effect state
				self.probs[state] = INT
			elif state[0] == state[1]:
				# activating, inactivating
				self.probs[state] = MAJOR
			else:
				self.probs[state] = MINOR

class IA_Factor(Factor):
	'''
	Represents an in-activating link for two nodes, with 3 states each: -1, 0, 1
	'''
	def makeTable(self):
		'''
		Iterate over all possible states of input variables: set the 
		'''
		MAJOR = 0.6
		INT = 0.333
		MINOR = 0.2

		self.probs = {}
		# P(B|A) 
		# A = 0 , B = 0 0.2
		# A = 1 , B = 0 0.333
		# A = 2 , B = 0 0.6
		# A = 0 , B = 1 0.2
		# A = 1 , B = 1 0.333
		# A = 2 , B = 1 0.2
		# A = 0 , B = 2 0.6
		# A = 1 , B = 2 0.333
		# A = 2 , B = 2 0.2

		self.probs[(0,0)] = MINOR
		self.probs[(1,0)] = INT
		self.probs[(2,0)] = MAJOR
		self.probs[(0,1)] = MINOR
		self.probs[(1,1)] = INT
		self.probs[(2,1)] = MINOR
		self.probs[(0,2)] = MAJOR
		self.probs[(1,2)] = INT
		self.probs[(2,2)] = MINOR
		
class UNIFORM_Factor(Factor):
	'''

	'''
	def makeTable(self):
		'''
		Iterate over all possible states of input variables: set the 
		'''
		UP = 0.333
		# P(B|A) 
		# A = 0 , B = 0 0.333
		# A = 1 , B = 0 0.333
		# A = 2 , B = 0 0.333
		# A = 0 , B = 1 0.333
		# A = 1 , B = 1 0.333
		# A = 2 , B = 1 0.333
		# A = 0 , B = 2 0.333
		# A = 1 , B = 2 0.333
		# A = 2 , B = 2 0.333

		self.probs = {}
		for state in self.states:
			self.probs[state] = UP
			#print "\t".join([str(i) for i in self.flatten(state)])
		
		
class AND_Triple_Factor(Factor):
	'''

	'''
	def makeTable(self):
		'''
		Iterate over all possible states of input variables: set the 
		'''
		# P(B|A) 
		# A = 0 , B = 0, C = 0 0.1
		# A = 1 , B = 0, C = 0 0.1
		# A = 2 , B = 0, C = 0 0.1

		FLAT = 0.1
		AND = 1.0
		self.probs = {}
		for state in self.states:
			self.probs[state] = FLAT
	
		# only this probability is higher...	
		self.probs[(2,2,2)] = AND	
			
