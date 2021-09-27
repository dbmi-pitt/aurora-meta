import requests, json, os
import argparse
import pandas as pd
import ijson
import time

# Elasticsearch python libs
from elasticsearch import Elasticsearch
from elasticsearch import helpers


directory = ""
indexName = "aurora-meta2"
typeName = "patient"
THRESHOLD = 10000  # this regulates how much data gets loaded then is processed in a bulk group
PK = "ID"
json_root = "item"
errors = []

def loadit():
	es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])

	for filename in os.listdir(directory):
		if filename.endswith(".json"):
			json_filename = directory+filename
			print("Loading " + json_filename)			
			
			with open(json_filename, 'r') as input_file:
				i = 1
				batchCtr = 1
				bulk_action = []
				bulkCount = 0
				ij = ijson.items(input_file, json_root)
				print(ij)
				for rec in ij:
					print(rec)
					#pk = rec['clin'][PK]
					pk = rec['clin'][PK]
					print(pk)
					bulk = {
						"_index"  : indexName,
						#"_type"   : typeName,
						"_id"     : pk,
						"_source" : rec,
					}
					bulk_action.append(bulk)
					i = i + 1
					batchCtr = batchCtr + 1
					if batchCtr > THRESHOLD:
						try:
							#print(bulk_action)
							bulkCount = bulkCount + batchCtr
							rtn_status = helpers.bulk(es, bulk_action)
							if rtn_status:
								print(rtn_status)
								#print ('Imported data ' + str(bulkCount-1) + ' successfully from ' + json_filename)
								batchCtr = 1
								bulk_action = []
						except Exception as ex:
							print ("Loading failed for " + json_filename)
							errors.append(json_filename)
							print ('Error:' + str(ex))
							#print ("Loading failed!")
							#pass
				if i < THRESHOLD:
					try:
						rtn_status = helpers.bulk(es, bulk_action)
						if rtn_status:
							print(rtn_status)
							#print ('Imported data ' + str(i-1) + ' successfully from ' + json_filename)
							batchCtr = 1
							bulk_action = []
					except Exception as ex:
						print ('Error:' + str(ex))
						print ("Loading failed for " + json_filename)
						errors.append(json_filename)
						#pass
	

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", required=True, help="dir path to json file(s)")
	parser.add_argument("-thres", help="set the batch threshold")
	parser.add_argument("-i", help="set the index name")
	parser.add_argument("-t", help="set the type")
	parser.add_argument("-pk", help="primary key of the record, default 'ID'")
	parser.add_argument("-r", help="json root node, default 'item', passing 'NOROOT' will ignore the root item")

	args = parser.parse_args()
	print("Args:")
	print(args)

	if args.d:
		directory = args.d
		if directory[-1] != '/':
			directory = directory + '/'
	if args.thres:
		THRESHOLD = int(args.thres)
		print ("Batch threshold: " + str(THRESHOLD))
		print(type(THRESHOLD))
	if args.i:
		indexName = args.i
	if args.t:
		typeName = args.t
	if args.pk:
		PK = args.pk
	if args.r:
		if args.r == "NOROOT":
			json_root = ""  # ignore the root
		else:
			json_root = args.r

	start = time.time()
	loadit()
	end = time.time()
	print("Elapsed time: {}".format((end-start)))
	if len(errors) > 0:
		print("The following files failed:")
		print(errors)



