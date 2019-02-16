from scene import *
from sound import load_effect, play_effect, set_volume
from math import modf
from random import random, randint, choice
import time
import shelve
import sys

EASY = 0
MEDIUM = 1
HARD = 2
EXPERT = 3


class Main (Scene):
	def setup(self):
		self.loaded = False
		self.sound = 'Coin_3'
		load_effect(self.sound)
		self.animationLength = 6
		self.soundInterval = 1
		self.gameStartTime = time.time()
		self.isBackgroundBroken = False
		self.isDistanceBroken = False
		self.isSoundBroken = False
		
		self.diagonal = abs(Point(self.size.w, self.size.h) - Point(0, 0))
		self.distance = self.diagonal
		
		self.titleF = 'AvenirNext-Heavy'
		self.titleS = 65
		
		self.f = 'Futura'
		self.s = 40
		
		self.instrF = 'Arial'
		self.instrS = 20
		
		self.gameModeF = 'AppleColorEmoji'
		
		self.ipad = self.size.w > 400
		if self.ipad:
			self.titleS *= 1.5
			self.s *= 1.5
			self.instrS *= 1.5
		
		self.goodItems = [
			'bubble', 'shell', 'fish', 'key', 'blowfish',
			'tropical fish', 'octopus', 'dolphin', 'whale'
		]
		self.badItems = ['monster', 'shoe', 'bomb', 'poo', 'toilet', 'cactus']
		self.itemsList = self.goodItems + self.badItems
		
		self.requirements = {
			'Easy': ('key', 0),  # Easy is unlocked by default
			'Medium': ('bubble', 1),
			'Hard': ('shell', 5),
			'Expert': ('fish', 10),
			'Sound': ('key', 1),
			'Colour': ('blowfish', 15),
			'Distance': ('tropical fish', 20),
			'SoundColour': ('octopus', 25),
			'SoundDistance': ('dolphin', 35),
			'ColourDistance': ('whale', 50)
		}
		
		with shelve.open('SonarSave') as save:
			if 'Items' in save:
				self.items = save['Items']
				self.highscores = save['Highscores']
			else:
				self.items = {}
				for item in self.itemsList:
					self.items[item] = 0
					
				self.highscores = [None for i in range(4)]  # Easy medium, hard, expert
		
		self.goToMenu()
		self.loaded = True
		
	def goToMenu(self):
		self.animationStart = time.time()
		self.lastSoundTime = self.animationStart
		self.state = 'Menu'
		
	def startGame(self, difficulty):
		self.difficulty = difficulty
		self.treasurePoint = Point(randint(0, self.size.width), randint(0, self.size.height))
		self.pointMargin = [25, 10, 5, 2][difficulty]  # EASY, MEDIUM, HARD, EXPERT
		self.gameStartTime = time.time()
		self.lastSoundTime = self.gameStartTime
		self.distance = None
		self.state = 'Playing'
	
	def getBackgroundColour(self, t):
		t /= (self.animationLength / 4)  # scale so that 1 unit in t means one segment of the animation
		t %= 4  # the animation repeats after the 4 steps
		
		if 0 <= t < 1:
			return [1, 0, 0]
		elif 1 <= t < 2:
			t -= 1
			return [1 - t, t, t]
		elif 2 <= t < 3:
			return [0, 1, 1]
		else:
			t -= 3
			return [t, 1 - t, 1 - t]

	def draw(self):
		w = self.size.w
		h = self.size.h
		
		if not self.loaded:
			return
			
		if self.state == 'Menu':
			bc = self.getBackgroundColour(time.time() - self.animationStart)
			background(*bc)
			tint(bc[1], bc[1], bc[1])
			
			if time.time() - self.lastSoundTime >= self.animationLength / 2:
				play_effect(self.sound)
				self.lastSoundTime += self.animationLength / 2
				
			text('Sonar', self.titleF, self.titleS, w * 0.5, h * 0.8)
			text('Explore', self.f, self.s, w * 0.5, h * 0.56)
			text('Broken Sonar', self.f, self.s, w * 0.5, h * 0.44)
			text('Highscores', self.f, self.s, w * 0.5, h * 0.32)
			text('Items', self.f, self.s, w * 0.5, h * 0.2)
			
		elif self.state.startswith('Starting'):
			background(0, 0, 0)
			tint(1, 1, 1)
		
			title = 'Explore' if self.state == 'Starting Exploration' else 'Broken Sonar'
			text(title, self.titleF, self.titleS * 0.75, w * 0.5, h - 5, alignment=2)
			text('How to play:', self.f, self.s * 0.8, w * 0.5, h * 0.83)
			text('Move your finger around the screen', self.instrF, self.instrS, w * 0.5, h * 0.77)
			text('to try to find the hidden item. The', self.instrF, self.instrS, w * 0.5, h * 0.73)
			text('background, sound and distance', self.instrF, self.instrS, w * 0.5, h * 0.69)
			text('sensor will tell you how close you', self.instrF, self.instrS, w * 0.5, h * 0.65)
			text('are to finding it. Good luck!', self.instrF, self.instrS, w * 0.5, h * 0.61)
			text('Tap a difficulty to start!', self.f, self.s * 0.75, w * 0.5, h * 0.5)
			
			for i, mode in enumerate(['Easy', 'Medium', 'Hard', 'Expert']):
				if self.hasUnlocked(mode):
					text(mode, self.gameModeF, self.s, w * 0.5, h * 0.4 - (h * 0.1 * i))
				else:
					req = self.requirements[mode]
					needed = req[1] - self.items[req[0]]
					message = 'You need %d more %s to unlock %s.' % (needed, self.plural(req[0], needed), mode)
					text(message, self.f, self.instrS * 0.8, w * 0.5, h * 0.4 - (h * 0.1 * i))
					
			text('Menu', self.f, self.instrS, w - 5, 5, alignment=7)
			
		elif self.state == 'Playing':
			# Change background colour
			if not self.isBackgroundBroken and self.distance is not None:
				c = self.distance / self.diagonal
				background(1 - c, c, c)
			else:
				background(0, 0, 0)
					
			# Display distance
			if not self.isDistanceBroken and self.distance is not None:
				if self.difficulty == EXPERT:
					text(str(int(round(self.distance * 0.1) * 10)), self.f, self.s, w * 0.5, 5, alignment=8)
				else:
					text(str(int(round(self.distance))), self.f, self.s, w * 0.5, 5, alignment=8)
					
			# Make sound
			if not self.isSoundBroken and self.distance is not None:
				volume = 1 - (self.distance / self.diagonal)
				set_volume(volume)
				if time.time() - self.lastSoundTime >= self.soundInterval:
					play_effect(self.sound)
					self.lastSoundTime += self.soundInterval
				
			# Display time
			e = time.time() - self.gameStartTime
			text(self.formatTime(e), self.f, self.instrS, 5, h - 5, alignment=3)
				
		elif self.state == 'Item Give':
			background(0, 0, 0)
			text('You got...', self.f, self.s, w * 0.5, h * 0.9)
			items = self.itemsToGive
			i1, i2 = items[0], (items[1] if len(items) == 2 else None)
			
			if len(items) == 1:
				a = 'A ' if i1 != 'octopus' else 'An '
				text(a + i1 + '!', self.f, self.s, w * 0.5, h * 0.27)
				image(self.imageName(self.itemsToGive[0]), w * 0.15, h * 0.3, w * 0.7, w * 0.7)
				
			elif len(items) == 2 and i1 == i2:
				text('Two' + self.plural(i1) + '!', self.f, self.s, w * 0.5, h * 0.27)
				image(self.imageName(i1), w * 0.15, h * 0.3, w * 0.7, w * 0.7)
				
			else:
				a1 = 'A ' if self.itemsToGive[0] != 'octopus' else 'An '
				a2 = 'a ' if self.itemsToGive[1] != 'octopus' else 'an '
				text(a1 + i1 + ' and ' + a2 + i2 + '!', self.f, self.s * 0.65, w * 0.5, h * 0.37)
				image(self.imageName(i1), w * 0.05, h * 0.4, w * 0.4, w * 0.4)
				image(self.imageName(i2), w * 0.55, h * 0.4, w * 0.4, w * 0.4)
				
			text('Tap to continue.', 'Futura', self.instrS, w, 0, alignment=7)
			
		elif self.state == 'Broken Select':
			background(0, 0, 0)
			tint(1, 1, 1)
			
			if not self.hasUnlocked('Sound'):
				text('Sorry, you need a key to unlock', self.instrF, self.instrS, w * 0.5, h * 0.5)
				text('this mode. Tap to return to the menu.', self.instrF, self.instrS, w * 0.5, h * 0.46)
			else:
				text('Broken Sonar', self.titleF, self.titleS * 0.75, w * 0.5, h - 5, alignment=2)
				text('You get 2 items for winning Broken Sonar.', self.f, self.instrS * 0.8, w * 0.5, h * 0.8)
				
				if self.isSoundBroken:
					tint(1, 0, 0)
				text('Sound', self.gameModeF, self.s, w * 0.5, h * 0.6)
				tint(1, 1, 1)
				if self.isBackgroundBroken:
					tint(1, 0, 0)
				text('Colour', self.gameModeF, self.s, w * 0.5, h * 0.5)
				tint(1, 1, 1)
				if self.isDistanceBroken:
					tint(1, 0, 0)
				text('Distance', self.gameModeF, self.s, w * 0.5, h * 0.4)
				tint(1, 1, 1)
				
				text('Menu', self.f, self.instrS, w - 5, 5, alignment=7)
					
				s = self.getBroken()
				if s and self.hasUnlocked(s):
					text('Continue', self.f, self.s, w * 0.5, h * 0.25)
				elif s == '':
					text('Select the broken sensors!', self.f, self.instrS, w * 0.5, h * 0.25)
				elif s == 'SoundColourDistance':
					text("You can't break all the sensors!", self.f, self.instrS, w * 0.5, h * 0.25)
				else:
					req = self.requirements[s]
					needed = req[1] - self.items[req[0]]
					message = 'You need %d more %s to unlock this mode.' % (needed, self.plural(req[0], needed))
					text(message, self.f, self.instrS * 0.75, w * 0.5, h * 0.25)
					
				text('Menu', self.f, self.instrS, w - 5, 5, alignment=7)
		
		elif self.state == 'Highscores':
			background(0, 0, 0)
			tint(1, 1, 1)
			text('Highscores', self.titleF, self.titleS * 0.9, w * 0.5, h, alignment=2)
			text('Easy: ' + self.formatTime(self.highscores[EASY]), self.f, self.s, w * 0.5, h * 0.7)
			text('Medium: ' + self.formatTime(self.highscores[MEDIUM]), self.f, self.s, w * 0.5, h * 0.6)
			text('Hard: ' + self.formatTime(self.highscores[HARD]), self.f, self.s, w * 0.5, h * 0.5)
			text('Expert: ' + self.formatTime(self.highscores[EXPERT]), self.f, self.s, w * 0.5, h * 0.4)
						
			text('Menu', self.f, self.instrS, w - 5, 5, alignment=7)
			
		elif self.state == 'Items':
			background(0, 0, 0)
			tint(1, 1, 1)
			text('Items', self.titleF, self.s, w * 0.5, h, alignment=2)
			
			border = 15
			iw = (w - border * 4) / 3
			
			yStart = h * 0.78
			
			for x in range(3):
				for y in range(5):
					item = self.itemsList[y * 3 + x]
					imageX = border * (x + 1) + (iw * x)
					imageY = yStart - (border * y) - (iw * y)
					image(self.imageName(item), imageX, imageY, iw * 0.85, iw * 0.85)
					text(str(self.items[item]), self.f, self.instrS, imageX + iw * 0.85, imageY, alignment=6)
			
			text('Menu', self.f, self.instrS, w, 0, alignment=7)
			
	def touch_began(self, touch):
		w = self.size.w
		h = self.size.h
		l = touch.location
		
		def touchingText(x, y, width, height):
			if self.ipad:
				width *= 1.5
				height *= 1.5
			return l in Rect(w * x - width / 2, h * y - height / 2, width, height)
		
		if self.state == 'Menu':
			if touchingText(0.5, 0.56, 100, 60):
				self.state = 'Starting Exploration'
				self.isBackgroundBroken = False
				self.isDistanceBroken = False
				self.isSoundBroken = False
				
			if touchingText(0.5, 0.44, 100, 60):
				self.state = 'Broken Select'
				
			if touchingText(0.5, 0.32, 100, 60):
				self.state = 'Highscores'
				
			if touchingText(0.5, 0.2, 100, 60):
				self.state = 'Items'
				
		elif self.state in ['Highscores', 'Items']:
			if touchingText(0.85, 0.05, 100, 60):
				self.goToMenu()

		elif self.state == 'Broken Select':
			if not self.hasUnlocked('Sound'):
				self.goToMenu()
		
			elif touchingText(0.5, 0.6, 100, 60):
				self.isSoundBroken = not self.isSoundBroken
				
			elif touchingText(0.5, 0.5, 100, 60):
				self.isBackgroundBroken = not self.isBackgroundBroken
				
			elif touchingText(0.5, 0.4, 100, 60):
				self.isDistanceBroken = not self.isDistanceBroken
				
			elif touchingText(0.85, 0.05, 100, 60):
				self.goToMenu()
				
			elif touchingText(0.5, 0.25, 100, 60) and self.hasUnlocked(self.getBroken()):
				self.state = 'Starting Broken Sonar'
		
		elif self.state.startswith('Starting'):
			for i, mode in enumerate(['Easy', 'Medium', 'Hard', 'Expert']):
				if self.hasUnlocked(mode) and touchingText(0.5, 0.4 - (0.1 * i), 100, 60):
					self.startGame(i)  # this works since EASY = 0, etc.
					
			if touchingText(0.85, 0.05, 100, 60):
				self.goToMenu()
				
		elif self.state == 'Playing':
			self.touch_moved(touch)  # code is the same
			
		elif self.state == 'Item Give':
			self.goToMenu()
			
	def touch_moved(self, touch):
		l = touch.location
		if self.state == 'Playing':
			self.distance = abs(self.treasurePoint - l)
			if self.distance <= self.pointMargin:
				e = time.time() - self.gameStartTime
				if self.highscores[self.difficulty] is None or self.highscores[self.difficulty] > e:
					self.highscores[self.difficulty] = e
			
				if self.isBackgroundBroken or self.isDistanceBroken or self.isSoundBroken:
					self.itemsToGive = [choice(self.itemsList), choice(self.itemsList)]
				else:
					self.itemsToGive = [choice(self.itemsList)]
				
				for item in self.itemsToGive:
					self.items[item] += 1
					
				self.state = 'Item Give'
		
	def imageName(self, itemName):
		imageNames = {
			'bubble': 'Blue_Circle', 'shell': 'Spiral_Shell',
			'tropical fish': 'Tropical_Fish',
			'monster': 'Alien_Monster',
			'shoe': 'Athletic_Shoe', 'poo': 'Pile_Of_Poo'
		}
			
		if itemName in imageNames:
			return imageNames[itemName]
		else:
			return itemName[0].upper() + itemName[1:]
			
	def plural(self, itemName, amount=2):
		if amount == 1 or itemName.endswith('fish'):
			return itemName
		elif itemName in ['cactus', 'octopus']:
			return itemName[:-2] + 'i'
		else:
			return itemName + 's'
			
	def hasUnlocked(self, difficulty):
		try:
			req = self.requirements[difficulty]
			return self.items[req[0]] >= req[1]
		except KeyError:
			return False
		
	def getBroken(self):
		return ('Sound' if self.isSoundBroken else '') + \
				('Colour' if self.isBackgroundBroken else '') + \
				('Distance' if self.isDistanceBroken else '')
		
	def formatTime(self, t):
		if t is None:
			return 'N/A'
		elif t >= 60:
			return '%d:%02d.%02d' % (t / 60, t % 60, (t % 1) * 100)
		else:
			return '%.02f' % t
		
	def pause(self):
		self.saveData()
		
	def stop(self):
		self.saveData()
		
	def saveData(self):
		with shelve.open('SonarSave') as save:
			save['Items'] = self.items
			save['Highscores'] = self.highscores
			
run(Main(), PORTRAIT)
