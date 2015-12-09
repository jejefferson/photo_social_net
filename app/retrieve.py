#/usr/bin/python
#-*- coding: utf-8 -*-

import lxml.etree
import urllib2

#return dict, where keys are names of films and value is list of times for this film, i.e {'крутой фильм': ['8:00', '12:00']}
def retrieveAfisha():
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
	return timetable

if __name__ == 'main':
	timetable = retrieveAfisha()
	for film in timetable:
		print film, timetable[film]
