#!/usr/bin/python
# -*- coding:UTF-8 -*-

import codecs
import cProfile
import pstats
import json
import time
import sys
from optparse import OptionParser
from utils import price

from comment import comment


def init_parser():
	parser = OptionParser()
	parser.add_option('-i', '--input', action='store', dest='input',
		help='set the input filename', metavar='FILE')
	parser.add_option('--encoding', action='store', dest='encoding',
		default='utf-8', help='set the encoding of input filename', metavar='FILE')
	parser.add_option('--output', action='store', dest='output',
		default='./output/result.csv', help='set the output filename', metavar='FILE')
	parser.add_option('--output-mode', action='store', dest='output_mode',
		default='result', help='set the output mode')
	parser.add_option('--unmatch', action='store', dest='unmatch',
		default='./output/unmatch.txt', help='set the unmatch filename', metavar='FILE')
	parser.add_option('--count', action='store', dest='max_count',
		default=sys.maxsize, help='set the max count to process')
	parser.add_option('--log', action='store', dest='logfile',
		default='./output/failed.json', help='set the log file')
	parser.add_option('--statistics', action='store', dest='statistics',
		default='./output/statistic', help='set the statistics file')
	return parser.parse_args()


def main():
	(options, args) = init_parser()
	deduplication = {}
	summary = {}
	statistic = {}
	for field in comment.FIELDS:
		statistic[field] = 0
	count = 0

	prices = price.load_price(price.PRICE_FILE)

	input_file = codecs.open(options.input, 'r', encoding=options.encoding, errors='strict')
	output_file = codecs.open(options.output, 'w', encoding='utf-8')
	unmatch_file = codecs.open(options.unmatch, 'w', encoding='utf-8')
	log_file = codecs.open(options.logfile, 'w', encoding='utf-8')
	statistics_file = codecs.open(options.statistics, 'w', encoding='utf-8')

	if options.output_mode == 'result':
		output_file.write((','.join(comment.OUT_HEADERS) + '\n'))

	c = comment.Comment()
	for line in input_file.readlines():
		try:
			_json = json.loads(line)
			# get id
			if 'id' in _json:
				id = _json['id']
			elif 'commentId' in _json:
				id = _json['commentId']
			else:
				raise IndexError
			# deduplication
			if id in deduplication:
				continue
			else:
				deduplication[id] = True
			# skip len less than 15
			if len(_json['content']) < 15:
				continue
			# init comment object
			c.clean_and_fill(_json)
			# match regexes
			fields = c.match(_json['content'], comment.matchRegex)
		except:
			log_file.write(line)
			continue
		_match_count = len(fields)

		# log
		if divmod(count, 1000)[1] == 0:
			print('process {0} comments, {1}'.format(count, time.process_time()))

		if _match_count > 5:
			# set price
			try:
				c.data['price'] = price.get_price(_json['referenceId'], prices)
			except:
				continue
			# output
			if options.output_mode == 'relay':
				output_file.write(json.dumps({id: c.data, 'match': _match_count}, ensure_ascii=False) + '\n')
			elif options.output_mode == 'result':
				output_file.write(str(c) + '\n')
		elif _match_count == 0:
			# unmatch output
			unmatch_file.write(_json['content'] + '\n')
		# summary and statistic
		try:
			summary[_match_count] += 1
		except:
			summary[_match_count] = 1
		for field in fields:
			statistic[field] += 1
		count += 1
		if count == int(options.max_count):
			break
	sum = 0
	for key in statistic:
		sum += statistic[key]
	strs = 'statistic: {0}, \r\nsummary: {1}, \r\ncomment count {2}, field match count {3}, process {4}s'.format(
		json.dumps(statistic, indent=2, sort_keys=True), json.dumps(summary, indent=2, sort_keys=True),
		count, sum, time.process_time())
	statistics_file.write(strs)
	print(strs)


if __name__ == '__main__':
	cProfile.run('main()', 'timeit')
	p = pstats.Stats('timeit')
	p.sort_stats('time').print_stats(8)
