


Test query for es01

curl -X GET "localhost:9200/aurora/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": { "match_all": {} }
}
'



curl -X DELETE "localhost:9200/aurora?pretty"
