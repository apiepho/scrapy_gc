from scrapy.spiders  import Spider
from scrapy.selector import Selector

import scrapy
import sys
import os

class GameChanger(Spider):
    name = "gc"
    allowed_domains = []
    start_urls      = []
    totalcount      = 0
    currentcount    = 0

    def usage(self):
        print "Usage: scrapy crawl gc -a email=\"<login email>\" -a password=<login password> -a cache_dir=<cache dir> --nolog"
        pass

    # init verify email and password
    # init set start_urls to gc login
    # parse will parse login, fill form, send request with parse_loggedin
    # parse_loggedin will send request for teams?s=1000 with parse_teams 
    # parse_teams will parse all teams and send request for each team

    def __init__(self, url=None, category=None, email = None, password = None, cache_dir = None, *args, **kwargs):
        super(GameChanger, self).__init__(*args, **kwargs)
        try:
            if url == None:
                print "please provide a url"
                raise Exception()
            if (email == None or len(email) == 0 or email.find("@") == -1):
                print "please provide a valid email."
                raise Exception()
            if (password == None or len(password) == 0):
                print "please provide a valid password"
                raise Exception()
            if (cache_dir == None or len(cache_dir) == 0):
                print "please provide a valid cache directory"
                raise Exception()

            self.orig_url = url + "/"
            self.cache_dir = cache_dir
            if category == 'list':
                print "list feature not supported yet."
            elif category != None and len(category) != 3:
                print "category must be 3 letters"
                raise Exception()
            elif category != None:
                url = url + "/search/" + category

            print "crawling: " + url
            self.url             = url
            self.category        = category
            parts                = url.replace("http://", "").replace("https://", "").split('/')
            domain               = parts[0]
            self.allowed_domains = ['%s' % domain]
            self.start_urls      = ['%s' % url]
        except:
            self.usage()
            sys.exit()    # is there a better way?
        print "..."
        pass

    def parse(self,response):
        print response.url
        print 

        # toward gc data:
        # create cache directory from command line arg
        # convert response.url to file name matching gc_app style
        # overwrite cache file
        cache_file = response.url
        cache_file = cache_file.replace(self.orig_url, "")
        cache_file = cache_file.replace("/", "_")
        cache_file = cache_file.replace("?", "_")
        cache_file = cache_file.replace("=", "_")
        cache_file = cache_file.replace("&", "_")
        cache_file = "%s/%s.html" % (self.cache_dir, cache_file)
        print cache_file
        # attempt to create cache dir
        try:
            os.makedirs(self.cache_dir)
        except:
            print "note: cache dir exists"
            pass
        # attempt to create write file
        try:
            text_file = open(cache_file, "w")
            text_file.write(response.body)
            text_file.close()
        except:
            print "note: cache file exists"
            pass

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
        else:
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

        # done
 


