import re
import os
import sys
import time
import signal
import django
import socket
import pymysql
import logging
import argparse
import threading
import subprocess
from pull import PULL
from config import CONFIG
from django.core.wsgi import get_wsgi_application as GETWSGI
from django.core.management import call_command as DJANGOCALL

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Snarl.settings')
pull = PULL()
logger = logging.getLogger( __name__ )
logger.setLevel( logging.CRITICAL )

class EXECUTIONER:

	def __init__(self, bd, pt):
		self.address = bd
		self.port    = pt

	def bind(self):
		application = GETWSGI()
		pull.uprun( "Binding the Server to Address: %s:%s" % (self.address, self.port), pull.CYAN )
		pull.info( "You can Access Your Application Now!", pull.YELLOW )
		DJANGOCALL(
			'runserver', 
			"{}:{}".format(self.address, self.port),
			'--noreload',
			stdout=open( os.devnull, "w" )
		)

class PARSER:

	def __init__(self, opts):
		self.configure = self.configure( opts.configure )
		self.migrate   = self.migrate( opts.migrate  )
		self.cuser     = self.create( opts.cuser )
		self.bind      = self.bind(    opts.bind     )
		self.port      = self.port(    opts.port     )
		self.conn      = self.conn(    self.bind, self.port )
		self.init      = self.initialize( self.bind )
		self.signal    = signal.signal( signal.SIGINT, self.handler )

	def handler(self, sig, fr):
		pull.halt( "Received Interrupt. Exiting!", "\r" + pull.RED )

	def configure(self, conf):
		if conf:
			dbase = pull.ask( "Enter Your Database Name: ", pull.PURPLE )
			serve = pull.ask( "Enter Your Server Name [localhost]: ", pull.PURPLE )
			uname = pull.ask( "Enter Database Username: ", pull.PURPLE )
			passw = pull.ask( "Enter Database Password: ", pull.PURPLE )

			pull.uprun( "Checking Database Connection. Connecting!", pull.DARKCYAN )
			try:
				pymysql.connect(serve, uname, passw, dbase)
			except pymysql.err.OperationalError:
				pull.halt( "Access Denied for the user. Check Credentials and Server Status!" )

			config = CONFIG()
			config.read()
			config.dgen()
			config.write()

	def migrate(self, mig):
		if mig:
			pull.uprun( "Migration Phase. Initializing File & Configurations. ", pull.YELLOW )
			config = CONFIG()
			config.read()
			config.kgen()
			config.write()

			self.initialize()

			time.sleep( 3 )
			application = GETWSGI()

			pull.uprun( "Configuration Done. Uprnning Migrations Now. ", pull.DARKCYAN )
			DJANGOCALL('makemigrations', stdout=open( os.devnull, "w" ))
			DJANGOCALL('migrate', stdout=open( os.devnull, "w" ))
			pull.halt( "Migrations Applied Successfuly. Exiting Now!", pull.GREEN )
		else:
			config = CONFIG()
			if not os.path.isfile( config.SETTPATH ):
				pull.halt( "Application not yet initialized. Run the migrations first. See Manual!" )

	def create(self, cuser):
		if cuser:
			django.setup()
			from django.contrib.auth.models import User as SUPERUSER
			uname = pull.ask( "Enter Username for the admin user: ", pull.YELLOW )
			email = pull.ask( "Enter Email for the user: ", pull.YELLOW )
			passw = pull.ask( "Enter Password for the user: ", pull.YELLOW )

			if uname and passw:
				SUPERUSER.objects.create_superuser( uname, email, passw )
				pull.halt( "User Created Successfuly", pull.GREEN )
			else:
				pull.halt( "Username & Password Fields Are Mandatory & Must be Supplied", pull.RED )

	def initialize(self, addr=""):
		config = CONFIG()
		config.read()
		config.extend( addr )
		config.generate()

	def bind(self, bd):
		if bd:
			if re.match( r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", bd ):
				return bd
			else:
				pull.halt( "Not a Valid IP Address.", pull.RED, pull.BOLD )
		else:
			pull.halt( "Halt! Binding Address Not Provided. See Manual", pull.RED, pull.BOLD )

	def port(self, pt):
		if pt > 0 and pt < 65536:
			return pt
		else:
			pull.halt( "Invalid Port! Must be in Range 1-65535", pull.RED, pull.BOLD )

	def conn(self, bd, pt):
		try:
			s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
			s.bind((bd, pt))
			s.close()
		except:
			pull.halt( "Not able to Bind to Address. Check Your Address & Port!", pull.RED, pull.BOLD )

def main():
	parser = argparse.ArgumentParser( add_help=True )
	parser.add_argument( '-b', '--bind'   , dest="bind"     , default=None , type=str            )
	parser.add_argument( '-p', '--port'   , dest="port"     , default=8080 , type=int            )
	parser.add_argument( '-v', '--verbose', dest="verbose"  , default=False, action="store_true" )
	parser.add_argument( '-d', '--debug'  , dest="debug"    , default=False, action="store_true" )
	parser.add_argument( '--migrate'      , dest="migrate"  , default=False, action="store_true" )
	parser.add_argument( '--configure'    , dest="configure", default=False, action="store_true" )
	parser.add_argument( '--create-user'  , dest="cuser"    , default=False, action="store_true" )
	options = parser.parse_args()
	parser = PARSER( options )

	pull.gthen( "Firing UP Snarl. Have a Seat! ", pull.DARKCYAN )
	picker = EXECUTIONER( parser.bind, parser.port )
	picker.bind()
	pull.lthen( "Exiting!", pull.RED )

if __name__ == "__main__":
	main()