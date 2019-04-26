#!/usr/bin/env python
"""
Helper script to ingest generated data to a search index.

You must have access to a search index for this to work.

"""
import json
import globus_sdk
from login import load_tokens
import argparse

# 'cr3' index
INDEX = '11f4dbe5-1449-4d65-af83-72d322b117f3'
SEARCH_DATA = 'gmeta_ingest_doc.json'

def ingest():
    with open(SEARCH_DATA) as f:
        ingest_doc = json.loads(f.read())

    tokens = load_tokens()
    auther = globus_sdk.AccessTokenAuthorizer(
        tokens['search.api.globus.org']['access_token'])
    sc = globus_sdk.SearchClient(authorizer=auther)

    preview = [ent['subject'] for ent in ingest_doc['ingest_data']['gmeta']]
    print('\n'.join(preview))
    print('Ingest these to "{}"?'.format(
        sc.get_index(INDEX).data['display_name']))
    user_input = input('Y/N> ')
    if user_input in ['yes', 'Y', 'y', 'yarr']:
        sc.ingest(INDEX, ingest_doc)
        print('Finished')
    else:
        print('Aborting')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", help="input Gmet json data file")

    args = parser.parse_args()

    if args.i:
        SEARCH_DATA = args.i

    ingest()
