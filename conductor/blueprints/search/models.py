import os
import json

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

_engine = None

ENABLED_SEARCHES = {
    'user': {
        'index': 'users',
        'doc_type': 'user_profile',
        '_source': ['idhash', 'name', 'avatar_url', 'datasets'],
        'q_fields': ['name']
    },
    'package': {
        'index': 'packages',
        'doc_type': 'package',
        '_source': ['id', 'model', 'package', 'origin_url'],
        'q_fields': ['package.title',
                     'package.author',
                     'package.description',
                     'package.regionCode',
                     'package.countryCode',
                     'package.cityCode']
    }
}


def _get_engine():
    global _engine
    if _engine is None:
        es_host = os.environ['OS_ELASTICSEARCH_ADDRESS']
        _engine = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)
    return _engine


def build_dsl(kind_params, kw):
    dsl = {'bool': {'must': []}}
    q = kw.get('q')
    if q is not None:
        dsl['bool']['must'].append(
            {
                'multi_match': {
                    'query': json.loads(q[0]),
                    'fields': kind_params['q_fields']
                }
            }
        )
    for k, v_arr in kw.items():
        if k.split('.')[0] in kind_params['_source']:
            dsl['bool']['must'].append({
                    'bool': {
                        'should': [{'match': {k: json.loads(v)}}
                                   for v in v_arr]
                    }
               })

    if len(dsl['bool']['must']) == 0:
        del dsl['bool']['must']
    if len(dsl['bool']) == 0:
        del dsl['bool']
    if len(dsl) == 0:
        dsl = {}
    else:
        dsl = {'query': dsl}
    return dsl


def query(kind, size=100, **kw):
    kind_params = ENABLED_SEARCHES.get(kind)
    if kind_params is None:
        return None
    try:
        # Arguments received from a network request come in kw, as a mapping
        # between param_name and a list of received values.
        # If size was provided by the user, it will be a list, so we take its
        # first item.
        if type(size) is list:
            size = size[0]
        api_params = dict([
            ('size', int(size)),
            ('index', kind_params['index']),
            ('doc_type', kind_params['doc_type']),
            ('_source', kind_params['_source'])
        ])

        body = build_dsl(kind_params, kw)
        api_params['body'] = json.dumps(body)
        ret = _get_engine().search(**api_params)
        if ret.get('hits') is not None:
            return [hit['_source'] for hit in ret['hits']['hits']]
    except (NotFoundError, json.decoder.JSONDecodeError, ValueError):
        pass
    return None
