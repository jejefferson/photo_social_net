#/usr/bin/python
#-*- coding: utf-8 -*-

import lxml.etree
import urllib2
from datetime import datetime, timedelta
from threading import RLock, Thread
import time
from pytz import timezone
import os

REFRACH_TIME = 1 #hour

class CacheRData(object):
	
	def __init__(self):
		self.last_request = {}
		self.last_time = datetime.utcnow()
			
	def caching_retrieve(self):
		if self.last_request and self.last_time + timedelta(hours=REFRACH_TIME) > datetime.utcnow():
			return self.last_request
		lock = RLock()
		with lock:
			doc = urllib2.urlopen('http://megafilm45.ru/schedule/')
			htmltext = doc.read().decode('utf-8')
			tree = lxml.etree.HTML(htmltext)
			timetable = {}
			filmslist = tree.xpath('/html/body/div[2]/div/div[2]/div[2]/div[*]/div[1]/a')
			for num, film in enumerate(filmslist):
				try:
					temp = tree.xpath('/html/body/div[2]/div/div[2]/div[2]/div[%s]/div[2]/div[*]/span[1]' % str(num+1))
					temp.extend(tree.xpath('/html/body/div[2]/div/div[2]/div[2]/div[%s]/div[2]/div[*]/a' % str(num+1)))
					temp = [time.text for time in temp if time.text.find(ur'зал') == -1]
					timetable[film.text] = temp
				except Exception as detail:
					print detail
			self.last_request = timetable
			self.last_time = datetime.utcnow()
			return self.last_request
			
	def get_last_update(self):
			return self.last_time

if __name__ == '__main__':
	"""многопоточное тестирование на потокобезопасность"""
	class ThreadWithReturnValue(Thread):
		def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
			Thread.__init__(self, group, target, name, args, kwargs, Verbose)
			self._return = None
		def run(self):
			if self._Thread__target is not None:
				self._return = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
		def join(self):
			Thread.join(self)
			return self._return
				
	cr = CacheRData()
	threads = []
	result = []
	number_of_threads = 100
	cr.caching_retrieve()
	time.sleep(5)
	for _ in range(number_of_threads):
		threads.append(ThreadWithReturnValue(target=cr.caching_retrieve))
	start = time.time()
	for thread in threads:
		thread.start()
		result.append(thread.join())
	print 'after: ',cr.get_last_update()
	
	threads = []
	result = []
	time.sleep(5)
	for _ in range(number_of_threads):
		threads.append(ThreadWithReturnValue(target=cr.caching_retrieve))
	start = time.time()
	for thread in threads:
		thread.start()
		result.append(thread.join())
	print ('%d thrads done in %f sec' % (number_of_threads, time.time()-start))
	print 'after two series: ', cr.get_last_update()
