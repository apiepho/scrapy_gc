from scrapy.spiders  import Spider
from scrapy.selector import Selector

import scrapy
import scrapy_splash
import sys
import os

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
        list = sel.css('ul[id=menu]')
        links = list.css('a')
        links = links[21:22]  # just roos for debug
        for link in links:
            href = link.css('a::attr(href)').extract_first()
            if href.find('/t/') != -1:
                next_page = self.base_url + href
                #yield scrapy.Request(next_page, callback=self.parse_team)
                yield scrapy.Request(next_page, callback=self.parse_team, meta={
                	'splash': {
                		'args': {
                			'wait': 0.0,
                			'html': 1
                		}
                	}
                })
                #return
        pass
       
    # handle response of each team page
    def parse_team(self, response):
        print "TEAM: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
        #print response.body

        sel = Selector(response)
        
        # process game links
        list = sel.css('li[class=newsFeedItem]')
        links = list.css('a')
        for link in links:
            href = link.css('a::attr(href)').extract_first()
            if href.find('/stats') != -1:
                next_page = self.base_url + href
                yield scrapy.Request(next_page, callback=self.parse_game_stats, meta={
                	'splash': {
                		'args': {
                			'wait': 0.0,
                			'html': 1
                		}
                	}
                })
                #return
        pass
        
    # handle response of each game stat page
    def parse_game_stats(self, response):
        print "GAME STAT: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
        pass
 
    # handle response of each game stat page
    def parse_game_recap(self, response):
        print "GAME RECAP: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)
        pass
       
    '''
GC_PLAYS_URI                      = GC_BASE_URI + "/game-%s/plays"
GC_SCOREBOOK_URI                  = GC_BASE_URI + "/game-%s/scorebook"

GC_ROSTER_URI                     = "%s/roster"                # given team guid
GC_PLAYER_URI                     = "%s/p/%s"                  # given team guid and player fname-lastinitial-guid
GC_RECAP_URI                      = "%s/game-%s/recap-story"   # given base and game guid

GC_STATS_URI                      = "%s/game-%s/stats"         # given base and game guid

# parameters for the following: [GC_BASE_URI, fteam, team_id, fname, linitial, player_id]
GC_PLAYER_BATTING_STANDARD_URI    = "%s/t/%s-%s/p/%s-%s-%s/batting/standard"
GC_PLAYER_BATTING_SPEED_URI       = "%s/t/%s-%s/p/%s-%s-%s/batting/expanded"
GC_PLAYER_BATTING_TEAMIMPACT_URI  = "%s/t/%s-%s/p/%s-%s-%s/batting/expanded2"
GC_PLAYER_PITCHING_STANDARD_URI   = "%s/t/%s-%s/p/%s-%s-%s/pitching/standard"
GC_PLAYER_PITCHING_EFFICIENCY_URI = "%s/t/%s-%s/p/%s-%s-%s/pitching/expanded"
GC_PLAYER_PITCHING_COMMAND_URI    = "%s/t/%s-%s/p/%s-%s-%s/pitching/expanded2"
GC_PLAYER_PITCHING_BATTER_URI     = "%s/t/%s-%s/p/%s-%s-%s/pitching/expanded3"
GC_PLAYER_PITCHING_RUNS_URI       = "%s/t/%s-%s/p/%s-%s-%s/pitching/expanded4"
GC_PLAYER_PITCHING_PITCH_URI      = "%s/t/%s-%s/p/%s-%s-%s/pitching/expanded5"
GC_PLAYER_FIELDING_STANDARD_URI   = "%s/t/%s-%s/p/%s-%s-%s/fielding/standard"
GC_PLAYER_FIELDING_CATCHING_URI   = "%s/t/%s-%s/p/%s-%s-%s/fielding/expanded"
GC_PLAYER_BATTING_SPRAY_URI       = "%s/t/%s-%s/p/%s-%s-%s/spray-chart"
    '''

