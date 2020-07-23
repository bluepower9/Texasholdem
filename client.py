import socket

class findserver(object):
	def __init__(self):
		self.ip=self.get_base_ip()
	
	def get_base_ip(self):
		ip=socket.gethostbyname(socket.gethostname())
		ip=ip.split('.')
		ip.remove(ip[3])
		ip='.'.join(ip)+'.'
		return ip

	def run(self):
		#if self.is_up('169.234.11.225'):
		#		return '169.234.11.225'
                
		
		for ip in xrange(1,256):    ## 'ping' addresses xxx.xxx.1.1 to .1.255
			addr = self.ip + str(ip)
			if self.is_up(addr):
				return addr
		
		
	
	def is_up(self,addr):
		print addr
		s = socket.socket()
		s.settimeout(5)   #original was .05 
		try:
			s.connect((addr,423))
			s.settimeout(None)
			print 'waiting for new game to start'
			s.send(' ')
			x=s.recv(1024)
			s.settimeout(0.01)
			if x=='texasholdem':
				s.close()
				return 1
		except socket.error as e:
			print e
			s.close()
			
	

class game(object):
	
	def __init__(self):
		self.name=raw_input("name: ")
		self.c=socket.socket()
		self.host='10.0.0.4' #ip of server  ip of comp sci: 10.229.27.18  home computer: 10.0.0.4
		self.port=423
	
	def locate_server():
		s=socket.socket()
		
	
	def connect(self):
		self.c.settimeout(None)
		while True:
			try:
				print 'trying to connect to server...'
				self.c.connect((self.host,self.port))
				print 'connected to server'
				break
			except socket.error:
				print 'server is down.'
				print 'retrying...'
				
		
	
	def new_game(self,game_name):
		self.connect()
		try:
			self.c.send('create_game:'+game_name+':'+self.name)
			print self.c.recv(1024)
		except socket.error:
			print 'failed to create game.'
	
				
	def join_game(self,game_name):
		self.connect()
		self.c.settimeout(None)
		try:
			while True:
				self.c.send('name:'+self.name+':'+game_name)
				print 'waiting for new game to start'
				x=self.c.recv(1024)
				print x
				if 'cannot connect to game' in x:
					return 0
				elif x=='name already used':
					self.name=raw_input('name: ')
					self.c.shutdown(socket.SHUT_RDWR)
					self.c=socket.socket()
					self.connect()
				else:
					break
		except socket.error as e:
			print e
			print 'socket error: cannot connect to game'
			return
		return 1
	
	def wait_for_start(self):
		self.c.settimeout(None)
		try:
			#self.c.settimeout(10000)
			x=self.c.recv(1024)
			if x=='check':
				self.c.send('here')
				return 1
		except socket.error as e:
			print 'socket error '+str(e)
			return 0
			

def user_input(text):
	action=raw_input(text)
	while action=='':
		action=raw_input(text)
	return action
	
server=findserver()
ip=server.run()
if ip:
	person=game()
	person.host=ip
else:
	print 'can not find server.'
	exit()
joined=person.join_game('default')

	
while True:
	print '\nwaiting for game to start\n'
	x=person.wait_for_start()
	if x==0:
		print 'game could not be started'
		break
	
	while True:
		z=person.c.recv(1024)
		print
		if z[0]=='-':
			print z[1:]
			person.c.send(' ')
		elif z[:4]=='hand':
			print z
			person.c.send(' ')
		elif z=='game over':
			person.c.send(' ')
			break
		elif z[:6]=='action' or z[:9]=='incorrect':
			action=user_input(z)
			person.c.send(action)
		elif z[:3]=='bet' or z[:5]=='raise':
			action=user_input(z)
			person.c.send(action)
		elif z[:6]=='WINNER':
			print z
			person.c.send(' ')
		elif z[:5]=='check':
			person.c.send(' ')
		elif z[:2]=='no':
			person.c.send(' ')
			print z
			exit()
			
		
		
	
	
	
	
	
