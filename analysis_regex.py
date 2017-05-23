#!/usr/bin/python
# -*- coding:UTF-8 -*-

import codecs
import cProfile
import pstats
import json
import time
import sys
from optparse import OptionParser

from comment import comment


def init_parser():
	parser = OptionParser()
	parser.add_option('-i', '--input', action='store', dest='input',
		help='set the input filename', metavar='FILE')
	parser.add_option('-o', '--output', action='store', dest='output',
		help='set the output filename', metavar='FILE')
	parser.add_option('-u', '--unmatch', action='store', dest='unmatch',
		help='set the unmatch filename', metavar='FILE')
	parser.add_option('-c', '--count', action='store', dest='max_count',
		default=sys.maxsize, help='set the max count to process')
	parser.add_option('-l', '--log', action='store', dest='logfile',
		help='set the log file')
	return parser.parse_args()


def main():
	(options, args) = init_parser()
	statistic = {}
	count = 0
	start_time = time.process_time()
	input = codecs.open(options.input, 'r', encoding='utf-8', errors='strict')
	output = codecs.open(options.output, 'w', encoding='utf-8')
	unmatch = codecs.open(options.unmatch, 'w', encoding='utf-8')
	log = codecs.open(options.logfile, 'w', encoding='utf-8')
	output.write((','.join(comment.OUT_HEADERS) + '\n'))

	c = comment.Comment()
	for line in input.readlines():
		try:
			_json = json.loads(line)
			if len(_json['content']) < 10:
				continue
			c.clean_and_fill(_json)
			fields = c.match(_json['content'], comment.matchRegex)
		except:
			log.write(line)
			continue
		_match_count = len(fields)

		if _match_count > 0:
			output.write(str(c) + '\n')
		else:
			unmatch.write(_json['content'] + '\n')
		try:
			statistic[_match_count] += 1
		except:
			statistic[_match_count] = 1
		if count == int(options.max_count):
			break
	summary = 0
	for key in statistic:
		summary += statistic[key]
	print('statistic {0}, summary {1}, process {2}s'.
		format(json.dumps(statistic, indent=2), summary, time.process_time()))


if __name__ == '__main__':
	cProfile.run('main()', 'timeit')
	p = pstats.Stats('timeit')
	p.sort_stats('time').print_stats(8)
