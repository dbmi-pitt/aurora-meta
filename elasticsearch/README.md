


Test query for es01

curl -X GET "es01:9200/aurora/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": { "match_all": {} }
}
'


