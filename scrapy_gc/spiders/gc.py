from scrapy.spiders  import Spider
from scrapy.selector import Selector

import scrapy
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
        #links = links[21:22]  # just roos for debug
        for link in links:
            href = link.css('a::attr(href)').extract_first()
            if href.find('/t/') != -1:
                next_page = self.base_url + href
                yield scrapy.Request(next_page, callback=self.parse_team)
                #return
        pass
       
    # handle response of each team page
    def parse_team(self, response):
        print "TEAM: " + response.url
        self.cache_name(response.url)
        self.cache_page(response.body)

        sel = Selector(response)
        list = sel.css('ul[id=newsList]')
        links = list.css('a')
        for link in links:
            href = link.css('a::attr(href)').extract_first()
            print href
            '''
            if href.find('/t/') != -1:
                next_page = self.base_url + href
                yield scrapy.Request(next_page, callback=self.parse_team)
                #return
            '''
        pass


        '''
        #self.cache_page(response.url)

        sel = Selector(response)
  
        # check for list, if so, list all categories from main page
        if self.category == 'list':
            print "listing categories:"
            container_lists = sel.css('a')
            for li in container_lists:
                if li.extract().find("data-cat") != -1:
                    sym  = li.css('a::attr(class)').extract_first()
                    href = li.css('a::attr(href)').extract_first()
                    desc = li.css('span::text').extract_first()
                    print("%-30s%-10s%s" % (desc, sym, href))

        # check for first page of a category, if so, find total and start sequence of pages
        elif response.url.find('?s=') == -1:
            self.totalcount = int(sel.css('span[class=totalcount]::text').extract_first())
            print("totalcount  : %d" % self.totalcount)
            next_page = "?s=%d" % self.currentcount
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
        # this should be one of the sequence of pages, parse items and start next page
        # select all rows
        container_lists = sel.css('li[class="result-row"]')
        for li in container_lists:
            yield {
                'description': li.css('p a::text').extract_first(),
                'location':    li.css('p a::attr(href)').extract_first(),
                'time':        li.css('p time::attr(datetime)').extract_first()
            }
            
        # update count and start next page
        self.currentcount += 100
        if self.currentcount < self.totalcount:
            next_page = "?s=%d" % self.currentcount
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
            #return
        '''
