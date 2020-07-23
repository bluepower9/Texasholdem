import socket,random,copy


class game(object):
	def __init__(self):
		self.s=socket.socket()
		host='0.0.0.0'
		port=423
		self.s.bind((host,port))
		self.s.listen(10)
		self.s.settimeout(10)
		self.games={}

	def new_game(self,name):
		if name in self.games.iterkeys():
			return 'game already exists'
		else:
			self.games[name]=newgame(name)
			return 'game created'
	
	
		
class newgame(object):
	
	def __init__(self,name):
		self.name=name
		self.s=socket.socket()
		self.s.settimeout(10)
		self.clients={}
		
	def addclient(self,name,x):
		self.clients[name]=x
		print name+' added to '+self.name

	def final_check(self):
		print 'doing final check...'
		temp_clients=copy.copy(self.clients)
		for x in temp_clients.iterkeys():
			print 'checking: '+x
			try:
				self.clients[x].settimeout(1)
				self.clients[x].send('check')
				self.clients[x].recv(1024)
			except socket.error as e:
				print 'final check error: '+str(e)
				print x
				del self.clients[x]
			if len(self.clients)<2:
				print len(self.clients)
				print 'error here'
				return False
		if len(self.clients)>=2:
			return True
	
	def get_players(self,clients,pool,cards):
		p=""
		for player in self.clients.iterkeys():
			dashes='-'*(len(player)+1)
			p+=dashes+'\n'+player+' '*(len(dashes)-len(player))+'| money: $'+str(clients[player][0])+'\tbet: $'+str(clients[player][1])+'\tstatus: '+str(clients[player][3])+'\n'+dashes+'\n'
		p+='\nPRIZE POOL: $'+str(pool)+'\n'
		p+='\nCOMMUNITY CARDS: '+' '.join(cards)+'\n'
		return p

		
		
class holdem(object):
	
	def __init__(self,name):
		self.players={}
		self.pool=0
		self.community=[]
		self.cards=[]
		self.g=newgame(name)
		self.money_pool=0

	
	def add_player(self,name,location):
		if name in self.g.clients.iterkeys():
			return False
		self.g.clients[name]=location
		self.players[name]=[1000.0,0,[],'pending'] #money, bet, cards, status
		return True
	
	def createdeck(self):
		possible={}
		self.cards=[]
		for x in xrange(1,14):
			possible[x]=['C','H','S','D']
		for x in range(52):
			value=random.choice(possible.keys())
			suit=random.choice(possible[value])
			possible[value].remove(suit)
			if len(possible[value])==0:
				del possible[value]
			if value==1:
				value='A'
			elif value==11:
				value='J'
			elif value==12:
				value='Q'
			elif value==13:
				value='K'
			self.cards.append(str(value)+suit)
	
	def deal(self):
		for name in self.players.iterkeys():
			self.players[name][2]=[self.cards[0],self.cards[1]]
			self.cards.remove(self.cards[0])
			self.cards.remove(self.cards[0])
	
	def send_hands(self):
		for player in self.players.iterkeys():
			self.g.clients[player].settimeout(1)
			try:
				self.g.clients[player].send('hand: '+' '.join(self.players[player][2]))
				print 'sent hand to '+player
				self.g.clients[player].recv(1024)
			except socket.error as e:
				print 'send error'
				pass
	
	def send_player_info(self):
		for player in self.players.iterkeys():
			self.g.clients[player].settimeout(1)
			try:
				self.g.clients[player].send('-\n\n\n\n\n\n\n'+self.g.get_players(self.players,self.money_pool,self.community))
				print 'sent player info to '+player
				self.g.clients[player].recv(1024)
			except socket.error as e:
				print e
				print 'player info send error'
				print 'removing player: '+player
				self.players[player][3]='disconnected'
				pass
	
	def reset_bet(self):
		for player in self.players.iterkeys():
			self.players[player][1]=0
	
	def reset_status(self):
		for player in self.players.iterkeys():
			if self.players[player][3] in ['fold','disconnected']:
				pass
			else:
				 self.players[player][3]='not gone'
	
	def full_status_reset(self):
		temp_players=copy.copy(self.players)
		for player in temp_players.iterkeys():
			if self.players[player][3]=='disconnected':
				del self.players[player]
				continue
				self.players[player][3]='not gone'
		
	#orders the player turns
	def set_order(self,start):
		temp_order=self.players.keys()
		
		order=[]
		for x in xrange(len(temp_order)):
			if start+x>=len(temp_order):
				start=-1*x
			print 'start= %i' %start
			print 'x= %i' %x
			order.append(temp_order[start+x])
		#print order
		return order
	
	def send_game_over(self):
		for player in self.players:
			if self.players[player][3]!='disconnected':
				self.g.clients[player].send('game over')
				self.g.clients[player].recv(1024)
	
	def send_winner(self,winner):
		for player in self.players:
			if self.players[player][3]!='disconnected':
				self.g.clients[player].send('WINNER: '+winner)
				self.g.clients[player].recv(1024)
				
	
	
	def bet(self,player,bet):
		self.players[player][1]=bet
		self.players[player][0]-=bet
		self.players[player][3]='bet'
		self.money_pool+=bet

	
	def raise_bet(self,player,amount,bet):
		print 'raise_bet: %i, %i, %i' %(self.players[player][1],amount,bet)
		self.players[player][0]-=amount+bet-self.players[player][1]
		self.money_pool+=amount+bet-self.players[player][1]
		self.players[player][1]=amount+bet	
		self.players[player][3]='raise'
		
	
	def check_for_disconnects(self):
		for player in self.players:
			self.g.clients[player].settimeout(1)
			try:
				self.g.clients[player].send('check')
				self.g.clients[player].recv(1024)
			except socket.error:
				print '%s disconnected' %player
				self.players[player][3]='disconnected'
			finally:
				self.g.clients[player].settimeout(None)
	
	def check_no_money(self):
		temp_players=copy.copy(self.players)
		for player in temp_players:
			if self.players[player][0]<=0:
				self.g.clients[player].send('no more money!')
				del self.players[player]
	
	def betting(self,order):
		
		self.check_for_disconnects()
		
		end_player=order[len(order)-1]
		has_raise=False
	
		while True:
			for player in order:
				try:
					self.check_for_disconnects()
					#checks for ending player
					if player==end_player and has_raise:
						return -1
					
					if self.players[player][3]=='disconnected':
						continue
					
					if self.players[player][0]==0:
						self.players[player][3]='check'
						continue
					if self.players[player][3]=='fold':
						continue
					if self.players[player][3]=='big blind' or self.players[player][3]=='small blind':
						self.players[player][3]+='... pending action'
					else:
						self.players[player][3]='pending action'
					
					self.send_player_info()
					self.send_hands()
			
					self.g.clients[player].settimeout(None)
			
					#calculates if someone already bets and finds max bet
					betting=False
					max_bet=0
					for status in self.players.itervalues():
						if status[1]>max_bet:
							max_bet=status[1]
						if 'bet' in status[3] or 'raise' in status[3] or 'blind' in status[3]:
							betting=True
							#if status[1]>max_bet:
							#	max_bet=status[1]
					
					print 'max bet: %f' %max_bet
								
					all_actions=['bet','check','fold','call','raise']		
					if not betting:
						all_actions.remove('call')
						all_actions.remove('raise')
						self.check_for_disconnects()
						self.g.clients[player].send('action (%s): ' %', '.join(all_actions))	
					else:
						all_actions.remove('bet')
						if 'big blind' in self.players[player][3]:
							if self.players[player][1]==max_bet:
								all_actions.remove('call')
							else:
								all_actions.remove('check')
						else:
							all_actions.remove('check')
						if self.players[player][0]<=max_bet:
							all_actions.remove('raise')
						self.check_for_disconnects()
						self.g.clients[player].send('action (%s): '%', '.join(all_actions))
					while True:
						action=self.g.clients[player].recv(1024)
						print action
						if action not in all_actions:
							self.g.clients[player].send('incorrect action. ')
						else:
							if action=='bet':
								while True:
									self.g.clients[player].send('bet amount: ')
									betamount=self.g.clients[player].recv(1024)
									if unicode(betamount).isnumeric():
										betamount=int(betamount)
										if betamount<=self.players[player][0]:
											has_raise=True
											end_player=player
											break										
								self.bet(player,betamount)
							elif action=='raise':
								end_player=player
								has_raise=True
								while True:
									self.g.clients[player].send('raise amount: ')
									amount=self.g.clients[player].recv(1024)
									if unicode(amount).isnumeric():
										amount=int(amount)
										if amount<=self.players[player][0] and self.players[player][1]==max_bet:
											print 'valid amount'
											self.raise_bet(player,amount,max_bet)
											max_bet+=amount
											break
										elif self.players[player][1]<max_bet and amount+max_bet<=self.players[player][0]:
											self.raise_bet(player,amount,max_bet)
											max_bet=self.players[player][1]
											break
							elif action=='call':
								self.players[player][3]='call'
								old_bet=self.players[player][1]
								print 'max bet: '+str(max_bet)
								print 'old bet: '+str(old_bet)
								if self.players[player][0]>=max_bet:
									self.players[player][0]-=max_bet-old_bet
									self.players[player][1]+=max_bet-old_bet
									
								else:
									self.players[player][1]+=self.players[player][0]
									self.players[player][0]=0.0	
								self.money_pool+=self.players[player][1]-old_bet
							elif action=='check':
								self.players[player][3]='check'
							elif action=='fold':
								self.players[player][3]='fold'
							break
					
					#checks if everyone else folded
					p=self.check_all_fold(order)
					#print 'p='+str(p)
					if p!=-1:
						print 'sending winner...'
						self.players[p][0]+=self.money_pool
						self.reset_bet()
						self.reset_status()
						self.send_player_info()
						self.send_winner(p)					
						return p
					self.check_for_disconnects()
				except socket.error:
					pass
			if not has_raise:
				return -1
	
	
	#checks to see if everyone else folded				
	def check_all_fold(self,order):
		folds=0
		p=None
		for player in order:
		
			if self.players[player][3]=='fold' or self.players[player][3]=='disconnected':
				folds+=1
				if folds==len(order)-1:
					for p in order:
						if self.players[p][3]!='fold' and self.players[p][3]!='disconnected':
							return p
		return -1
					
				
				
	
	#main texasholdem method for game execution
	def manage_game(self,start):
		self.money_pool=0
		self.community=[]
		order=self.set_order(start)
		if self.players[order[0]][0]<20:
			self.players[order[0]][1]=self.players[order[0]][0]
		else:
			self.players[order[0]][1]=20
		self.players[order[0]][0]-=self.players[order[0]][1]
		self.players[order[0]][3]='big blind'
		self.money_pool+=self.players[order[0]][1]
		if self.players[order[1]][0]<10:
			self.players[order[len(order)-1]][1]=self.players[order[len(order)-1]][0]
		else:
			self.players[order[len(order)-1]][1]=10
		self.players[order[len(order)-1]][0]-=self.players[order[len(order)-1]][1]
		self.players[order[len(order)-1]][3]='small blind'
		self.money_pool+=self.players[order[len(order)-1]][1]
		for x in xrange(1,len(order)-1):
			self.players[order[x]][1]=0
			self.players[order[x]][3]='not gone'
		
		#blind betting
		print 'starting blind betting'
		p=self.betting(order)
		self.reset_bet()
		self.reset_status()
		print 'end of blind betting'
		if p!=-1:
			self.send_game_over()
			return
		
		# deals starting 3 cards
		print "dealing 3 cards..."
		for x in xrange(3):
			self.community.append(self.cards[0])
			self.cards.remove(self.cards[0])
		
		self.send_player_info()
		self.send_hands()
		
		p=self.betting(order)
		self.reset_bet()
		self.reset_status()
		
		if p!=-1:
			self.send_game_over()
			return
		
		#deals next 2 cards one by one going through betting cycle
		for x in xrange(2):
			self.community.append(self.cards[0])
			self.cards.remove(self.cards[0])
		
			self.send_player_info()
			self.send_hands()
			
			p=self.betting(order)
			self.reset_bet()
			self.reset_status()
			
			if p!=-1:
				self.send_game_over()
				return
		
		#finds winner
		scorer=checkhands()
		best=(None,None,None)
		winners=[]
		best=(None,None,None)
		for player in self.players:
			if self.players[player][3]!='fold' or self.players[player][3]!='disconnected':
				score=scorer.check_hand(self.players[player][2]+self.community)
				print player+" "+str(score)
				if score[0]>best[0]:
					best=score
					winners=[player]
				elif score[0]==best[0]:
					if score[1]>best[1]:
						best=score
						winners=[player]
					elif score[1]==best[1] and score[2]>best[2]:
						best=score
						winners=[player]
					elif score[0]==best[0] and score[1]==best[1] and score[2]==best[2]:
						winners.append(player)
		
		#sends winner to clients and adds money to winners
		#print 'pool: %i' %self.pool
		#print 'length winners: %i' %len(winners)
		pot=float(self.money_pool)/len(winners)
		print 'split amount: $ %f' %pot
		self.reset_bet()
		self.reset_status()
		self.send_player_info()
		for player in winners:
			self.players[player][0]+=pot	
			self.send_winner(player+'\thand: (%s)' %', '.join(self.players[player][2]))
		
		self.check_no_money()
		self.send_game_over()
		
		
		

class checkhands(object):
	
	def check_royal_straight(self,hand):
		order=['10','J','Q','K','A']
		rf=True
		for order_card in order:
			for card in hand:
				if order_card in card:
					rf=True
					break
				else:
					rf=False
			if not rf:
				return False
		return True
	
	
	def set_hand_numerical(self,hand):
		#sets hand to numerical values
		final_hand=[]
		for x in xrange(len(hand)):
			card=hand[x][0]
			if card=='A':
				final_hand.append(1)
			elif card=='J':
				final_hand.append(11)	
			elif card=='Q':
				final_hand.append(12)
			elif card=='K':
				final_hand.append(13)
			elif card=='1':
				final_hand.append(10)
			else:
				final_hand.append(int(card))
		return final_hand
	
	def check_straight(self,final_hand):
		
		hand=self.set_hand_numerical(final_hand)
				
		lowest=min(hand)
		original_lowest=lowest
		for x in xrange(len(hand)):
			for card in hand:
				if card==lowest+1:
					lowest=card
					break
		if lowest-original_lowest>=4:
			return (True, lowest)
		else:
			return (False,None)
		
	def check_multiple_cards(self,final_hand):
		
		hand=self.set_hand_numerical(final_hand)
		final={}
		
		for i in xrange(len(hand)-1):
			total=1
			for ii in xrange(i+1,len(hand)):
				if hand[i]==hand[ii]:
					total+=1
			if total>=2 and hand[i] not in final.iterkeys():
				final[hand[i]]=total
		return final
	
	def check_high_card(self,final_hand):
		hand=self.set_hand_numerical(final_hand)
		highest=hand[0]
		for card in hand:
			if card==1:
				card=14
			if card>highest:
				highest=card
		return highest
	
	def check_flush(self,hand):
		hand_num=self.set_hand_numerical(hand)
		for card in xrange(len(hand_num)):
			if hand_num[card]==1:
				hand_num[card]=14
		for i in xrange(len(hand)-1):
			total=1
			max_card=None
			for ii in xrange(i+1, len(hand)):
				if hand[i][1]==hand[ii][1]:
					total+=1
					if hand_num[ii]>max_card:
						max_card=hand_num[ii]
			if total>=5:
				return (True,max_card)
		return (False,max_card)
	
	def check_royal_straight_flush(self,hand):
		if self.check_royal_straight(hand) and self.check_flush(hand):
			return True
		else:
			return False
	
	def check_straight_flush(self,hand):
		straight=self.check_straight(hand)
		if straight[0] and self.check_flush(hand):
			return straight
		else:
			return (False, None)		

	############## IMPLEMENTS ALL THE CHECK HAND METHODS AND RETURNS HAND VALUE AND IMPORTANT CARDS	################
	def check_hand(self,final_hand):
		hand=copy.copy(final_hand)
		if self.check_royal_straight_flush(hand):
			return (10, None,None)
		
		#checks straight flush
		x,y=self.check_straight_flush(hand)
		if x:
			return (9,y,None)
		
		#gets list of multiple cards
		multiple_cards=self.check_multiple_cards(hand)
		print 'multiple cards: '+str(multiple_cards)
		#checks four of a kind
		for value in multiple_cards:
			if multiple_cards[value]==4:
				return (8,value,None)
				
		#checks full house
		pair=None
		three=None
		for value in multiple_cards:
		
		#need to fix 3 of a kind as a pair
			if multiple_cards[value]==2:
				if multiple_cards[value]>pair:
					pair=value
			if multiple_cards[value]==3:
				if multiple_cards[value]>three:
					three=value
				elif multiple_cards[value]>pair:
					pair=multiple_cards[value]
		if pair!=None and three!=None:
			return(7,three,pair)
		
		#checks flush
		x=self.check_flush(hand)
		if x[0]:
			return (6,x[1],0)
		
		#checks straight
		x=self.check_straight(hand)
		if x[0]:
			return (5,x[1])
		elif self.check_royal_straight(hand):
			return (5,13,None)
		
		#checks 3 of a kind
		for value in multiple_cards:
			if multiple_cards[value]==3:
				max_card=None
				temp_hand=self.set_hand_numerical(hand)
				for card in temp_hand:
					if card>max_card and card!=value:
						max_card=card
				return (4,max_card,None)
		
		#checks 2 pair
		pair1=None
		pair2=None
		for value in multiple_cards:
			pair=multiple_cards[value]
			if pair==2:
				if pair1==None:
					pair1=value
				elif pair2==None:
					if pair>pair1:
						temp_pair1=pair1
						pair1=value
						pair2=temp_pair1
					else:pair2=value
				else:
					if pair>pair1:
						temp_pair1=pair1
						pair1=value
						pair2=temp_pair1
					elif pair>pair2:
						pair2=value
		if pair1!=None and pair2!=None:
			return (3,pair1,pair2)
	
		#checks pair
		for value in multiple_cards:
			if value==1:
				multiple_cards[14]=copy.copy(multiple_cards[1])
				del multiple_cards[1]
				value=14
			if multiple_cards[value]==2:
				max_card=None
				temp_hand=self.set_hand_numerical(hand)
				for card in temp_hand:
					if card==1:
						card=14
					if card>max_card and card!=value:
						max_card=card
				return (2,value,max_card)
		
		#checks high card
		return (1,self.check_high_card(hand),0)
				
					
def main():
	g=game()
	g.games['default']=holdem('default')
	print 'ok'
	start=0
	while True:
		while True:
			try:
				g.s.settimeout(10)
				c,addr=g.s.accept()
				while True:
					try:
						c.settimeout(5)
						x=c.recv(1024)
						idk=None
						if x[:4]!='name':
							c.send('texasholdem')				
						elif x[:4]=='name':
							idk=x.split(':')
							print 'got connection from: '+str(addr)
							print idk
							if idk[2] not in g.games:
								c.send('cannot connect to game')
							else:
								not_used_name=g.games[idk[2]].add_player(idk[1],c)
								if not_used_name:
									c.send('connected to '+idk[2])
								else:
									c.send('name already used')
						'''		
						elif idk[0]=='create_game':
							create=g.new_game(idk[1])
							if create=='game created':
								g.games[idk[1]].addclient(idk[2],x)
							c.send(create)
						'''
					except socket.error as e:
						print e
						pass
					finally:
						break
			except socket.error as e:
				if len(g.games['default'].g.clients)>=2:
					break
		
		ok=g.games['default'].g.final_check()
		if not ok:
			continue
		
		
		g.games['default'].createdeck()
		g.games['default'].deal()
		g.games['default'].reset_bet()
		g.games['default'].full_status_reset()
		g.games['default'].manage_game(start)
		
		start+=1
		if start>=len(g.games['default'].players):
			start=0
			

if __name__=='__main__':			
	#try:
		main()
	#except Exception as e:
	#	print e
	#	raw_input('done')
	
		
			
