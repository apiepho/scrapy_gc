from scrapy.spiders  import Spider
from scrapy.selector import Selector

import scrapy
import scrapy_splash  # better for server farm?
import sys
import os
import time

'''
import PyQt5.QtGui import QApplication
import PyQt5.QtCore import QUrl
import PyQt5.QtWebKit import QWebPage

Class QClient(QWwebPage):

	def __init__(self, url):
		self.app = QApplication(sys.argv)
		QWebPage.__init__(self)
		self.loadFinished.connect(self.on_page_load)
		self.mainFrame().load(QUrl(url))
	
	def on_page_load(self):
		self.app.quit()
'''
		

class GameChanger(Spider):
    name = "gc"
    allowed_domains = [ 'gc.com' ]
    start_urls      = [ 'https://gc.com/login' ]
    base_url        = 'https://gc.com'
    base_url_slash  = 'https://gc.com/'
    teams_url       = base_url + '/teams'
    cache_file      = ""

    def usage(self):
        print "Usage: scrapy crawl gc -a email=\"<login email>\" -a password=<login password> -a cache_dir=<cache dir> --nolog"
        pass

 
    def cache_name(self, url):
        # build gc_app style file name, do name when calling to avoid redirect changes
        self.cache_file = url
        self.cache_file = self.cache_file.replace(self.base_url_slash, "")
        self.cache_file = self.cache_file.replace("/", "_")
        self.cache_file = self.cache_file.replace("?", "_")
        self.cache_file = self.cache_file.replace("=", "_")
        self.cache_file = self.cache_file.replace("&", "_")
        self.cache_file = "%s/%s.html" % (self.cache_dir, self.cache_file)

    def cache_page(self, body):
        print self.cache_file
        # attempt to create cache dir
        try:
            os.makedirs(self.cache_dir)
        except:
            #print "note: cache dir exists"
            pass
        # attempt to create write file
        try:
            text_file = open(self.cache_file, "w")
            text_file.write(body)
            text_file.close()
        except:
            print("note: cache file exists (%s)" % self.cache_file)
            pass

    def __init__(self, email = None, password = None, cache_dir = None, *args, **kwargs):
        super(GameChanger, self).__init__(*args, **kwargs)
        try:
            if (email == None or len(email) == 0 or email.find("@") == -1):
                print "please provide a valid email."
                raise Exception()
            if (password == None or len(password) == 0):
                print "please provide a valid password"
                raise Exception()
            if (cache_dir == None or len(cache_dir) == 0):
                print "please provide a valid cache directory"
                raise Exception()

            self.email     = email
            self.password  = password
            self.cache_dir = cache_dir
            print "crawling: " + self.base_url
        except:
            self.usage()
            sys.exit()    # is there a better way?
        print "..."
        pass

    # default parse for login page
    def parse(self, response):
        print "LOGIN: " + response.url
        return scrapy.FormRequest.from_response(
			response,
			formdata={'email': self.email, 'password': self.password},
			callback=self.parse_home
		)

    # handle response of login, or home page
    def parse_home(self, response):
        print "HOME: " + response.url
        self.cache_name(self.teams_url)
        yield scrapy.Request(self.teams_url, callback=self.parse_teams)
        pass
 
    # handle response of teams page
    def parse_teams(self, response):
        print "TEAMS: " + response.url
        self.cache_page(response.body)

        sel = Selector(response)
        elems = sel.css('ul[id=menu]')
        links = elems.css('a')
        #links = links[21:22]  # DEBUG: just roos for debug
        for link in links:
            href = link.css('a::attr(href)').extract_first()
            if href.find('/t/') != -1:
                next_page = self.base_url + href
                #yield scrapy.Request(next_page, callback=self.parse_team)
                yield scrapy.Request(next_page, callback=self.parse_team, meta={'splash': {'args': {'wait': 0.0, 'html': 1}}})
                #return
        pass
       
    # handle response of each team page
    def parse_team(self, response):
        print "TEAM: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
       
        # get roster
        '''
        '''
        next_page = response.url + '/roster'
        yield scrapy.Request(
            next_page,
            callback=self.parse_team_roster,
            meta={'splash': {'args': {'wait': 0.0, 'html': 1}}}
        )
                
        # process game links
        sel = Selector(response)
        elems = sel.css('li[class=newsFeedItem]')
        links = elems.css('a')
        #links = links[-4:]  # DEBUG: just 1st game (hrefs in pairs)
        for link in links:
            href = link.css('a::attr(href)').extract_first()
            # want these /game-56e4c51a57a7013ef9000002, not with stats or recap. testing to keep order
            if len(href) == 30:
                next_page = self.base_url + href + '/stats'
                yield scrapy.Request(next_page, callback=self.parse_game_stats)
                #yield scrapy.Request(next_page, callback=self.parse_game_stats, meta={'splash': {'args': {'wait': 0.5, 'html': 1}}})

                # BUG: scrapy_gc cannot gather the plays pages correctly.  I have tried several methods to add
                # scrapy-splash and long waits, but here seems to be something about how those pages are streaming
                # the play by play data.  Disable for now.
                #
                # found suggestion that default user agent string is blocked
                #
                # try PyQt5
                '''
                next_page = self.base_url + href + '/plays'
                client_response = QClient(next_page)
                source = client_response.mainFrame().toHtml()
                self.cache_name(next_page)
                self.cache_page(source)
                '''
                #yield scrapy.Request(next_page, callback=self.parse_game_plays)
                #yield scrapy.Request(next_page, callback=self.parse_game_plays, meta={'splash': {'args': {'wait': 0.5, 'html': 1}}})
                luascript = '''
					function main(splash)
					  splash:init_cookies(splash.args.cookies)
					  assert(splash:go{
						splash.args.url,
						headers=splash.args.headers,
						http_method=splash.args.http_method,
						body=splash.args.body,
						})
					  splash:wait(5.0)
					  splash:wait(5.0)
					  -- requires Splash 2.3  
					  -- while not splash:select('.sabertooth_pbp_inning_row') do
					  -- splash:wait(0.1)
					  -- end

					  local entries = splash:history()
					  local last_response = entries[#entries].response
					  return {
						url = splash:url(),
						headers = last_response.headers,
						http_status = last_response.status,
						cookies = splash:get_cookies(),
						html = splash:html(),
					  }
					end
				'''
                #yield scrapy_splash.SplashRequest(next_page, callback=self.parse_game_plays, endpoint='execute', args={'lua_source': luascript})
                #return
        pass

        
    # handle response of each game stat page
    def parse_game_stats(self, response):
        print "GAME STATS: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
        pass
 
    # handle response of each game plays page
    '''
    def parse_game_plays(self, response):
        print "GAME PLAYS: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
        pass
    '''

    # handle response of each team roster page
    def parse_team_roster(self, response):
        print "TEAM ROSTER: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
        #return  # DEBUG: no stats

        # get player pages
        sel = Selector(response)
        tr_list = sel.css('tr')
        links = tr_list.css('a')
        #links = list(set(links))  # use set to get unique list
        for link in links:
            name = link.css('span::text').extract_first()
            if name.isnumeric() == True:
            	continue
            	
            # need to build player string like <first name>-<last initial>-<id>
            parts = name.split(' ')
            fname = parts[0].lower()
            lname = parts[1].lower()
            lname = lname[:1]
            id = link.css('a::attr(href)').extract_first().replace('/player-', '')
            pstr = "/p/%s-%s-%s" % (fname, lname, id)

            # response url is like
            # https://gc.com/t/spring-2016/roosevelt-rough-riders-varsity-56dfa90020277d0024b46bbb/roster
            # need
            # https://gc.com/t/roosevelt-56dfa90020277d0024b46bbb

            # get parts for /
            next_page = response.url
            parts = next_page.split('/')

            # fix teamname-id part
            parts2 = parts[5].split('-')
            parts[5] = parts2[0] + '-' + parts2[-1]

            # remove unwanted
            del parts[6]  # remove roster
            del parts[4]  # remove spring-2016
  
            # put them back together          
            next_page  = '/'.join(parts)
            next_page  = next_page + pstr
            saved_page = next_page

            next_page = saved_page + '/batting/standard'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)
            #yield scrapy.Request(next_page, callback=self.parse_player_stat, meta={'splash': {'args': {'wait': 0.0, 'html': 1}}})

            next_page = saved_page + '/batting/expanded'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/batting/expanded2'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/pitching/standard'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/pitching/expanded'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/pitching/expanded2'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/pitching/expanded3'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/pitching/expanded4'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/pitching/expanded5'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/fielding/standard'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/fielding/expanded'
            yield scrapy.Request(next_page, callback=self.parse_player_stat)

            next_page = saved_page + '/spray-chart'
            #yield scrapy.Request(next_page, callback=self.parse_player_stat)
            yield scrapy.Request(next_page, callback=self.parse_player_stat, meta={'splash': {'args': {'wait': 5.0, 'html': 1}}})
        pass

    # handle response of each player stat page
    def parse_player_stat(self, response):
        print "PLAYER STAT: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
        pass

