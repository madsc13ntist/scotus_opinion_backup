#!/usr/bin/env python

__version__    = "0.0.2"
__date__       = "09.22.2014"
__author__     = "Joseph Zeranski"
__maintainer__ = "Joseph Zeranski"
__email__      = "madsc13ntist@gmail.com"
__copyright__  = "Copyright 2014, " + __author__
__license__    = "MIT"
__status__     = "Prototype"
__credits__    = [""]
__description__= "Identify changes in scotus slip opinions."
__build__      = ""

####################### MIT License ####################### 
# Copyright (c) 2014 Joseph Zeranski
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###########################################################

### Import Modules
import os			# for directory commands
import re			# for regex matching of case names
import time			# for generating the current 2-digit year.
import hashlib		# part of script's version control (md5/build version)
import optparse		# parse cmd line options and generate help doc
import cookielib	# Makes the the scripted browser harder to identify as a script/bot
import mechanize	# (browser emulation) https://pypi.python.org/pypi/mechanize/

### Define Functions
def createBrowser():
	"""
	Create a virtual browser to pilot requests. (harder to block)
	"""
	br = mechanize.Browser()		# Browser handle
	cj = cookielib.LWPCookieJar()	# Cookie Jar
	br.set_cookiejar(cj)
	# Follows refresh 0 but not hangs on refresh > 0
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	return br

def scrapeUrls():
	# current url prefix for slip opinion pdf listings
	url_prefix = 'http://www.supremecourt.gov/opinions/slipopinions.aspx?Term='
	
	opinions = {}												# create  dict of opinions
	for yy in range(options.year,int(time.strftime('%y'))):		# interate from 2003 - this year
		yy = str(yy).zfill(2)									# make yy the 2-digit year value as a string
		r = br.open(url_prefix+yy)								# open browser for yy year
		resp_headers = r.info()									# parse response headers
		
		# Looking at some results in link format
		opinion_links = [ x for x in br.links(url_regex='\d{2}-\d+.*\.pdf') ]
		for l in opinion_links:			# parse only links to slip opinion
			case = l.text												# the name of the case
			pdf_url = 'http://www.supremecourt.gov/opinions/'+l.url
			if not options.regex:
				opinions[case] = pdf_url								# add entry to opinion dict
			elif re.findall(options.regex, case, re.I):					# if case name matches user provided regex...
				opinions[case] = pdf_url								# add entry to opinion dict
			#print("%s:\t%s" % (case, pdf_url))
		if options.verbose:
			print("Opinions for 20%s: %d" % (yy, len(opinion_links)))
	return opinions

def checkForChanges(opinions):
	changed = {}
	for case in sorted(opinions):	# step through cases / pdf urls
		try:
			pdf_url = opinions[case]
			if options.verbose:
				print("Checking: '%s'" % (case))
			r = br.open(pdf_url)										# connect to the pdf resource
			resp_headers = r.info()										# capture response headers
			last_mod_date = resp_headers.getheader('Last-Modified')		# parse last-modified datestamp
			etag = resp_headers.getheader('ETag').strip('"')			# parse Etag header
			
			if not os.path.isdir(options.dir+os.sep+case+os.sep+last_mod_date):		# the case/mod directory was not found locally
				changed[case] = pdf_url
				### THIS IS WHERE YOU ALERT/TAKE-ACTION WITH NEW/CHANGED DOCUMENTS.
				### SEND A TWEET WITH python-twitter
				### use pdfdiff and post the diffs in the pdfs
				
				if options.log_path:
					log.write("%s,%s,%s,%s,%s\n" % (time.strftime("%Y%m%d-%H:%M:%S"), last_mod_date, case, etag, pdf_url))	# write entry to log
				if options.verbose:
					print("Downloading NEW: %s\t%s\t%s\t%s" % (case, last_mod_date, etag, pdf_url))
				else:
					print("Downloading latest version of '%s'" % (case))
				os.makedirs(options.dir+os.sep+case+os.sep+last_mod_date)					# create case/mod directory
				br.retrieve(pdf_url, options.dir+os.sep+case+os.sep+last_mod_date+os.sep+os.path.basename(pdf_url))	# download the pdf.
		except Exception as e:
			if options.log_path:
				log.write("%s, Error: '%s',%s,%s\n" % (time.strftime("%Y%m%d-%H:%M:%S"), str(e), case, pdf_url))	# write entry to log
			print("Error: '%s'\t%s\t%s" % (str(e), case, pdf_url))
	return changed

### If the script is being executed (not imported).
if __name__ == "__main__":
	if not __build__:
		__build__ = hashlib.md5(open(__file__, 'rb').read()).hexdigest()
	opt_parser = optparse.OptionParser()
	opt_parser.usage  = "%prog [options]\n"
	
	#''' Additional formatting for Meta-data ''''''''''''''''''
	opt_parser.usage += "version " + str(__version__) + ", build " + __build__ + "\n"
	if __description__ not in ["", [""], None, False]:
		opt_parser.usage += __description__ + "\n"
	opt_parser.usage += "Copyright (c) 2014 " + __author__ + " <" + __email__ + ">"
	if __credits__ not in ["", [""], None, False]:
		opt_parser.usage += "\nThanks go out to "
		if isinstance(__credits__, str):
			opt_parser.usage += __credits__ + "."
		elif isinstance(__credits__, list):
			if len(__credits__) == 1:
				opt_parser.usage += __credits__[0] + "."
			else:
				opt_parser.usage += ', '.join(__credits__[:-1]) + " and " + __credits__[-1] + "."
	#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

	opt_parser.add_option("-v", "--verbose",
						  dest    = "verbose",
						  action  = "store_true",
						  default = False,
						  help    = "Display more information while working.")
	opt_parser.add_option("-l", #"--log",
						  dest="log_path",
						  action  = "store",
						  default = False,
						  help    = "Specify a file to append log entries to.")
	opt_parser.add_option("-d", #"--pdf",
						  dest="dir",
						  action  = "store",
						  default = False,
						  help    = "Specify the dir to store pdfs in.")
	opt_parser.add_option("-c", #"--check",
						  dest="seconds",
						  action  = "store",
						  default = False,
						  help    = "Run in a loop. (that sleeps for n seconds between checks).")
	opt_parser.add_option("-f", #"--first",
						  dest="year",
						  action  = "store",
						  default = False,
						  help    = "The earliest year to check for changes.")
	opt_parser.add_option("-r", #"--regex",
						  dest="regex",
						  action  = "store",
						  default = False,
						  help    = "Only check cases that match a specified regex. (nocase)")
	
	
	# Parse options and args
	(options, args) = opt_parser.parse_args()
	
	### Make sure all user options are correct types and set default values.
	if not options.dir:
		options.dir = "scotus_opinions"
	if not os.path.exists(options.dir):
		os.makedirs(options.dir)
	
	log = False
	if options.log_path:
		if not os.path.isdir(os.path.dirname(os.path.abspath(options.log_path))):
			os.path.makedirs(os.path.dirname(os.path.abspath(options.log_path)))
		log = open(os.path.abspath(options.log_path), 'a')
	'''
	else:
		options.log_path = "scotus_opinions.log" #'''
	
	if not options.year:
		options.year = 3
	elif options.year.startswith("20"):
		options.year = int(''.join(options.year[-2:]))


##### Do the work
br = createBrowser()									# Create virtual browser
if not options.seconds:									# just check for changes once.
	changes = checkForChanges(scrapeUrls())				# Check for changes
	if changes:											# If there are any changes detected...
		for case in sorted(changes):
			print("Changes found in: %s" % (case))		# Display cases that changed
	if options.log_path:
		log.close()
else:													# Check for changes every n seconds
	options.seconds = int(options.seconds)				# Make sure user submitted seconds is valid and convert to int.
	while True:											# Loop forever
		changes = checkForChanges(scrapeUrls())			# Check for changes
		if changes:										# If there are any changes detected...
			for case in sorted(changes):
				print("Changes found in: %s" % (case))	# Display cases that changed
		try:
			print("[*] Sleeping for %d seconds..." % (options.seconds))
			time.sleep(options.seconds)
		except:
			if options.log_path:
				log.close()
			exit()
