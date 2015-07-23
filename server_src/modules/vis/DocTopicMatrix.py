#!/usr/bin/env python

import json
import math
from handlers.Home_Core import Home_Core

class DocTopicMatrix(Home_Core):
	def __init__(self, request, response, bow_db, lda_db):
		super(DocTopicMatrix, self).__init__(request, response)
		self.bowDB = bow_db
		self.ldaDB = lda_db
		self.bow = bow_db.db
		self.lda = lda_db.db

	def GetStateModel(self):
		table = self.lda.topics
		rows = self.lda().select(table.topic_index, table.topic_label, orderby=table.topic_index)
		data = {
			'topicIndex' : [ {
				'color' : 'default',
				'id' : row.topic_index,
#				'name' : row.topic_label,
				'name' : 'Topic {}'.format(n+1),
				'position' : n,
				'selected' : False
			} for n, row in enumerate(rows) ]
		}
		return data

	def GetSeriatedTermTopicProbabilityModel(self):
		termLimit = 500
		data = {}
		
		table = self.lda.docs
		query = """SELECT doc_id FROM {TABLE}
		WHERE rank <= {UB}
		ORDER BY rank""".format(TABLE = table, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		data['docIndex'] = [ row['doc_id'] for row in rows ]
		
		table = self.lda.topics
		query = """SELECT topic_index, topic_label FROM {TABLE}
		ORDER BY topic_index""".format(TABLE = table)
		rows = self.lda().select(table.topic_index, table.topic_label, orderby=table.topic_index)
		data['topicIndex'] = [ row.topic_label for row in rows ]
		data['topicMapping'] = [ n for n, row in enumerate(rows) ]
		topicCount = len(rows)
		
		table = self.lda.doc_topic_matrix
		ref = self.lda.docs
		query = """SELECT t.rank as doc_rank, topic_index AS topic_index, value AS value FROM {TABLE} AS m
			INNER JOIN {REF} AS t ON m.doc_index = t.doc_index
			WHERE t.rank <= {UB}
			ORDER BY t.rank""".format(TABLE = table, REF = ref, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		matrix = [ [0.0] * topicCount for _ in range(termLimit) ]
		for row in rows:
			matrix[row['doc_rank']-1][row['topic_index']] = row['value']
		data['matrix'] = matrix

		table = self.lda.doc_topic_matrix #a
		ref = self.lda.term_topic_matrix  #b
		tabledoc = self.lda.docs #c
		tableterm = self.lda.terms #d
		
		#2015/07/14 try to mix (v)
		'''
		apple = """SELECT a.doc_index AS doc_index, MAX(a.value) As value, a.topic_index As topic_index, d.term_text As term_text 
			FROM {TABLE} AS a 
			INNER JOIN {REF} AS b on b.topic_index = a.topic_index
			INNER JOIN {TABLEDOC} As c on c.doc_index = a.doc_index
			LEFT JOIN {TABLETERM} As d on b.term_index = d.term_index
			GROUP BY a.doc_index
			ORDER BY c.rank""".format(TABLE = table, TABLEDOC = tabledoc, REF = ref, TABLETERM = tableterm)
		Apples = self.lda.executesql(apple, as_dict=True)
		data['Doc->Topic'] = [ row['topic_index'] for row in Apples ]
		data['docTerm'] = [ row['term_text'] for row in Apples]
		'''

		return data

	def GetFilteredTermTopicProbabilityModel(self):
		termLimit = 500
		data = {}

		table = self.lda.docs
		query = """SELECT doc_id, doc_freq, rank AS doc_rank FROM {TABLE}
		WHERE rank <= {UB}
		ORDER BY rank""".format(TABLE = table, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		data['termOrderMap'] = { row['doc_id'] : row['doc_rank']-1 for row in rows }
		data['termRankMap'] = { row['doc_id'] : row['doc_rank']-1 for row in rows }
		termTexts = [ row['doc_id'] for row in rows ]
		termFreqs = { row['doc_id'] : row['doc_freq'] for row in rows }
		
		table = self.lda.topics
		topicCount = self.lda(table).count()

		table = self.lda.doc_topic_matrix
		ref = self.lda.docs
		query = """SELECT t.rank as doc_rank, topic_index AS topic_index, value AS value FROM {TABLE} AS m
			INNER JOIN {REF} AS t ON m.doc_index = t.doc_index
			WHERE t.rank <= {UB}
			ORDER BY t.rank""".format(TABLE = table, REF = ref, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		matrix = [ [0.0] * topicCount for _ in range(termLimit) ]
		for row in rows:
			matrix[row['doc_rank']-1][row['topic_index']] = row['value']
		termDistinctiveness = {}
		termSaliency = {}
		for i, row in enumerate(matrix):
			normalization = 1.0 / sum(row) if sum(row) > 0 else 1.0
			normalized_row = [ d * normalization for d in row ]
			q = 1.0 / topicCount
			value = sum([ p * math.log(p) - p * math.log(q) if p > 0 else 0 for p in normalized_row ])
			if i < len(termTexts):
				termText = termTexts[i]
				termDistinctiveness[termText] = value
				termSaliency[termText] = termFreqs[termText] * value
		data['termDistinctivenessMap'] = termDistinctiveness
		data['termSaliencyMap'] = termSaliency
		return data

	def GetTermFrequencyModel(self):
		
		data = {}
		test = []

		### display doc_topic_matrix(V)
		'''
		termLimit = 500

		table = self.lda.docs
		query = """SELECT doc_id, doc_freq FROM {TABLE}
		WHERE rank <= {UB}
		ORDER BY rank""".format(TABLE = table, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		data['docIndex'] = [ row['doc_id'] for row in rows ]
		data['docFreqMap'] = { row['doc_id'] : row['doc_freq'] for row in rows }

		table = self.lda.topics
		query = """SELECT topic_index, topic_label FROM {TABLE}
		ORDER BY topic_index""".format(TABLE = table)
		rows = self.lda().select(table.topic_index, table.topic_label, orderby=table.topic_index)
#		data['topicIndex'] = [ row.topic_label for row in rows ]
		data['topicIndex'] = [ 'Topic {}'.format(n+1) for n, _ in enumerate(rows) ]
		data['topicMapping'] = [ n for n, row in enumerate(rows) ]
		topicCount = len(rows)

		table = self.lda.doc_topic_matrix
		ref = self.lda.docs
		query = """SELECT t.rank as doc_rank, topic_index AS topic_index, value AS value FROM {TABLE} AS m
			INNER JOIN {REF} AS t ON m.doc_index = t.doc_index
			WHERE t.rank <= {UB}
			ORDER BY t.rank""".format(TABLE = table, REF = ref, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		matrix = [ [0.0] * topicCount for _ in range(termLimit) ]
		for row in rows:
			matrix[row['doc_rank']-1][row['topic_index']] = row['value']
		data['matrix'] = matrix
   	'''

		### try to display term with doc_topic_matrix
		
		termLimit = 500

		
		
		table = self.lda.docs
		query = """SELECT doc_id, doc_freq FROM {TABLE}
		WHERE rank <= {UB}
		ORDER BY rank""".format(TABLE = table, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		data['docIndex'] = [ row['doc_id'] for row in rows ]
		data['docFreqMap'] = { row['doc_id'] : row['doc_freq'] for row in rows }
		

		
		table = self.lda.topics
		query = """SELECT topic_index, topic_label FROM {TABLE}
		ORDER BY topic_index""".format(TABLE = table)
		rows = self.lda().select(table.topic_index, table.topic_label, orderby=table.topic_index)
#		data['topicIndex'] = [ row.topic_label for row in rows ]
		data['topicIndex'] = [ 'Topic {}'.format(n+1) for n, _ in enumerate(rows) ]
		data['topicMapping'] = [ n for n, row in enumerate(rows) ]
		topicCount = len(rows)
		
		
		'''
		table = self.lda.doc_topic_matrix
		ref = self.lda.docs
		query = """SELECT t.rank as doc_rank, topic_index AS topic_index, value AS value FROM {TABLE} AS m
			INNER JOIN {REF} AS t ON m.doc_index = t.doc_index
			WHERE t.rank <= {UB}
			ORDER BY t.rank""".format(TABLE = table, REF = ref, UB = termLimit)
		rows = self.lda.executesql(query, as_dict=True)
		matrix = [ [0.0] * topicCount for _ in range(termLimit) ]
		for row in rows:
			matrix[row['doc_rank']-1][row['topic_index']] = row['value']
		data['matrix'] = matrix
		'''

		
		
		#2015/07/13 try to show term_topic_matrix order by rank(from doc)

		table = self.lda.doc_topic_matrix #a
		ref = self.lda.term_topic_matrix  #b
		tabledoc = self.lda.docs #c
		tableterm = self.lda.terms #d

		
		'''
		#get doc_topic_matrix MAX(value)(V)
		apple = """SELECT a.doc_index AS doc_index, MAX(a.value) As value, a.topic_index As topic_index 
			FROM {TABLE} AS a 
			LEFT JOIN {TABLEDOC} As c on c.doc_index = a.doc_index
			GROUP BY a.doc_index 
			ORDER BY c.rank""".format(TABLE = table, TABLEDOC = tabledoc)
		Apples = self.lda.executesql(apple, as_dict=True)
		data['Doc->Topic'] = [ row['topic_index'] for row in Apples ]
		#data['docIndex'] = [ row['topic_index'] for row in Apples ]
		#data['docFreqMap'] = { row['topic_index'] : row['topic_index'] for row in Apples }
		'''
		
		'''
		#2015/07/14 try to mix (v)
		apple = """SELECT a.doc_index AS doc_index, Max(a.value) As value, a.topic_index As topic_index, d.term_text As term_text 
			FROM {TABLE} AS a 
			INNER JOIN {REF} AS b on b.topic_index = a.topic_index
			INNER JOIN {TABLEDOC} As c on c.doc_index = a.doc_index
			LEFT JOIN {TABLETERM} As d on b.term_index = d.term_index
			GROUP BY a.doc_index
			ORDER BY c.rank""".format(TABLE = table, TABLEDOC = tabledoc, REF = ref, TABLETERM = tableterm)
		Apples = self.lda.executesql(apple, as_dict=True)
		data['Doc->Topic'] = [ row['topic_index'] for row in Apples ]
		data['docTerm'] = [ row['term_text'] for row in Apples]
		'''

		#2015/07/22 try to display 3 terms.

		#2015/07/23 get top 3 term (v)
		for i in range(10):
			dog = """SELECT d.term_index as term_index, d.term_text as term_text, b.topic_index as topic_index
				FROM {REF} As b
				LEFT JOIN {TABLETERM} As d on d.term_index = b.term_index
				where b.topic_index = {i}
				order by value desc
				limit 3 """.format(TABLE = table, TABLEDOC = tabledoc, REF = ref, TABLETERM = tableterm, i = i)
			Dogs = self.lda.executesql(dog, as_dict=True)
			data[i] = [ row['term_text'] for row in Dogs]
			data[i] = ", ".join(data[i]) #(v)

		'''
		cat = """SELECT f.term_index as term_index
			FROM {REF} As e
			LEFT JOIN {DOG} As f on f.term_index = e.term_index
			""".format(TABLE = table, TABLEDOC = tabledoc, REF = ref, TABLETERM = tableterm, DOG = Dogs)
		Cats = self.lda.executesql(cat, as_dict=True)
		data['cat'] = [ row['term_index'] for row in Cats ]
		'''

		apple = """SELECT a.doc_index AS doc_index, Max(a.value) As value, a.topic_index As topic_index, d.term_text As term_text 
			FROM {TABLE} AS a 
			INNER JOIN {REF} AS b on b.topic_index = a.topic_index
			INNER JOIN {TABLEDOC} As c on c.doc_index = a.doc_index
			LEFT JOIN {TABLETERM} As d on b.term_index = d.term_index
			GROUP BY a.doc_index
			ORDER BY c.rank""".format(TABLE = table, TABLEDOC = tabledoc, REF = ref, TABLETERM = tableterm)
		Apples = self.lda.executesql(apple, as_dict=True)
		data['Doc->Topic'] = [ row['topic_index'] for row in Apples ]
		#data['docTerm'] =[ row['term_text'] for row in Apples ]

		#for i in range(40):
		Eggs = [ data[row['topic_index']] for row in Apples]
		data['docTerm'] = [ row for row in Eggs]
		

		#get term_topic_matrix MAX(value)(V)
		banana = """SELECT b.term_index AS term_index, MAX(b.value) As value, b.topic_index As topic_index, c.term_text As term_text 
			FROM {REF} AS b 
			LEFT JOIN {TABLETERM} As c on c.term_index = b.term_index
			GROUP BY b.topic_index""".format(REF = ref, TABLETERM = tableterm)
		Bananas = self.lda.executesql(banana, as_dict=True)
		data['Topic->Term'] = [ row['term_text'] for row in Bananas]

		return data
