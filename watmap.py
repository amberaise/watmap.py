# watmap.py v0.9.1
# Map a set of images into a target image

# Olle Logdahl, March 31 2018
# Ported and modified version of Processing Watmap by Tomasz Sulej, gemerateme.blog@gmail.com
# Licence: http://unlicense.org/

from PIL import Image

import os, os.path
import random, math

#Modes																							# vilken beräkning algoritmen ska använda när den jämför källbilderna
ABS_MODE = 1																					# skillnad på luma för varje pixel
EUCLID_MODE = 2																					# bäst matchning; vektorer mellan pixelfärger

#Select Modes 																					# hur vi avgör vart på källbilderna Parten ska vara
RANDOM = 1																						# väljer en random punkt, testar hur bra den är. jämför med <blockcount> andra



#Variabler
filename = "test.jpg"																			# sökväg till originalbild
sourcepath = "source/"																			# sökväg till källor
savepath = "saves/"																				# sökväg till sparfiler

THR = 0.0001																						# Threshold som stddev av luman måste vara över för att rekursion ska ske.
MINR = 4																						# minsta tillåta storlek på quad

iterations = 1																					# mer = mer varierad
blockcount = 30																					# fler = fler antal random försök

distanceMethod = ABS_MODE																		# ABS_MODE, EUCLID_MODE
selectMethod = RANDOM 																			# RANDOM



#privata
image = None																					# originalbilden laddad och konverterad till matrisformat
patterns = []																					# lista av alla LImage objekt, skapade för källbilderna
parts = []																						# list över alla part klasser
sessionid = None


class LImage:																					# klass som representerar bildobjekt
	def __init__(self, img, name, w, h):														# konstruktor för klassen
		self.pix = img
		self.name = name
		self.w = w
		self.h = h
class Part:																						# klass som representerar kopiering från källa till produkt
	def __init__(self, source, px, py, w, h, x, y):														# konstruktor för klassen
		self.source = source
		self.posx = px
		self.posy = py
		self.w = w
		self.h = h

		self.x = x
		self.y = y

	def toString(self):																			# funktion för att finare printa datan
		return "{}; ( {}, {}, {}, {} ) -> ( {}, {} )".format(
			self.source, self.posx, self.posy, self.w, self.h, self.x, self.y)
class QuadTree:																					# klass för quadträdet som populerar bilden
	def __init__(self, x1, x2, y1, y2):															# konstruktor för klassen
		self.x1 = x1 																			# x1, x2, y1, y2 är bounds för den första quaden
		self.x2 = x2
		self.y1 = y1
		self.y2 = y2

		diffx = x2-x1
		diffy = y2-y1

		if ( diffx > MINR and diffy > MINR and standardDeviation(x1, x2, y1, y2) > THR):		# kollar om quaden är stor nog och om standardavvikelsen i pixlarnas luma är stor nog.
			midx = int(random.uniform(1/4*diffx, 3/4*diffx)	)									# beräknar en random punkt som ska dela våra fyra nya quads
			midy = int(random.uniform(1/4*diffy, 3/4*diffy) )									# skapar rekursivt 4 nya quads

			QuadTree(x1,		x1+midx,	y1,			y1+midy)								# Top Vänster
			QuadTree(x1+midx+1,	x2, 		y1, 		y1+midy)								# Top Höger
			QuadTree(x1,		x1+midx,	y1+midy+1,	y2)										# Bot Vänster
			QuadTree(x1+midx+1,	x2,			y1+midy+1,	y2)										# Bot Höger
		else:
			match(x1, y1, diffx+1, diffy+1)														# om inte så försöker vi skapa en Part som passar in i quaden



def setup():																					# setup, gör inget mer än laddar bilden och kör algorithmen på objektet
	sessionid = '%0x' % random.getrandbits(8 * 4)												# genererar en random sessionid, save filen döps till detta senare
	img = Image.open(filename)																	# öppnar filen
	processImage(img);																			# påbörjar algorithm

def processImage(img):																			# main metod
	global sessionid
	print("Förbereder data...")
	prepareImage(img) 																			# förbereder Image objektet så det kan läsas som en matris
	preparePatterns() 																			# omvandlar Image objekten till LImage array

	print("Genererar QuadTree...")
	width, height = img.size
	qtree = QuadTree(0, width-1, 0, height-1)													# startar rekursionen

	print("Påbörjar rekonstruktion av {}".format(filename))										# börjar återskapandet av bilden
	new = Image.new("RGB", img.size)
	for p in parts:
		x1, x2, y1, y2 = p.posx, p.posy, p.posx + p.w, p.posy + p.h
		subimage = Image.open(p.source).crop( (x1, x2, y1, y2) )
		new.paste(subimage, (p.x, p.y))

	saveadd = "{}{}".format(savepath, filename)
	new.save(saveadd)

	new.show()



def prepareImage(img): 																			# omvandlar Image objektet till en matris av unit-vektorer
	global image
	image = img.load()																			# gör img readable och spara pixelmatrisen till image
def preparePatterns():																			# omvandlar Image objekten till LImage array
	for file in os.listdir(sourcepath):															# för varje fil i källsökvägen...
		print("öppnar {}{}".format(sourcepath, file) )
		img = Image.open('{}{}'.format(sourcepath, file))										# öppnar bilden
		img = img.convert("RGB")																# konverterar den till RGB (kan behövas om den är Svart-Vit)

		w, h = img.size
		patterns.append( LImage(img.load(), file, w, h) )										# gör den readable och skapar LImage objekt som parar med datan

def getLuma(v):	return int( 0.3*v[0] + 0.59*v[1] + 0.11*v[2] )									# returnerar luman från (r, g, b) 		[ ITU BT 601 formula ]

def standardDeviation(x1, x2, y1, y2):															# returnar  standardavvikelsen i pixlarnas lumasdadas
	samples = []																				# lista över lumasamples

	sampleCount = int( x2-x1 * y2-y1 )															# beräknar antalet samples som krävs
	for _ in range(sampleCount):
		x = int( random.uniform(x1, x2) )														# genererar random punkter innom bounden
		y = int( random.uniform(y1, y2) )

		samples.append( getLuma(image[x, y]) )													# lägger till luman av pixeln i samplelistan

	mean = sum(samples) / sampleCount															# skapar en normalfördelning av lumasamples
	diff = [ x - mean for x in samples]															# beräknar skillnaden av varje sample till mean
	sqDiff = [ d ** 2 for d in diff]															# tar skillnaden i kvadrat
	ssd = sum(sqDiff)																			# summerar sqDiff

	variance = ssd / (sampleCount)															# samplecount - 1 eftersom vi jobbar med samples och inte populationen
	stddev = math.sqrt(variance)																# beräknar standardavvikelsen

	return stddev																				# returnernar standardavvikelsen

def match(posx, posy, w, h):																	# matchar en quad till ett urklipp från källorna
	global patterns

	r = int(random.uniform(0, len(patterns)) )													# randomiserar ett värde...
	selectedSource = patterns[r]	

	samplex = -1																				# var quaden från källan placeras i x-led
	sampley = -1																				# var quaden från källan placeras i y-led

	for _ in range(iterations):
		if( selectMethod == RANDOM ):
			previousErr = 1.0e10
			for __ in range(blockcount):														# utför <blockcount> försök
				x1 = int(random.uniform(0, selectedSource.w - w -1) )							# väljer en slumpad x på källbilden som är top vänster hörn för sub
				y1 = int(random.uniform(0, selectedSource.h - h -1) )							# väljer en slumpad y på källbilden som är top vänster hörn för sub

				err = 0																			# summan av distans mellan original och källan

				for i in range(w-1):															# itererar igenom varje pixel innom subområdet
					for j in range(h-1):
						x = x1 + i 																# definerar x relativt till källbilden
						y = y1 + j 																# definerar y relativt till källbilden

						#print(selectedSource.name, x, y)
						pixel = selectedSource.pix[x, y]										# nurvarande pixel från källbild
						pixelOrig = image[posx+i, posy+j]										# nurvarande pixel från original

						err += distance(pixel, pixelOrig)										# ökar error summan

				if err < previousErr:															# om skilladen är mindre än förra blocket...
					previousErr = err 															# gör det nya blocket till bästa
					samplex = x1
					sampley = y1


	path = sourcepath + selectedSource.name
	p = Part(path, samplex, sampley, w, h, posx, posy)											# skapar ett Part objekt av alla värden
	parts.append(p) 																			# lägger till Part objektet till parts

	print("matchad: {}".format(p.toString()))

def distance(c1, c2):
	if( distanceMethod == ABS_MODE ):
		return absDistance(c1, c2)
	if( distanceMethod == EUCLID_MODE ):
		return sqrDistance(c1, c2)
def absDistance(c1, c2): return abs(c1[0]-c2[0]) + abs(c1[1]-c2[1]) + abs(c1[2]-c2[2])			# absDistance mellan två färgvektorer
def sqrDistance(c1, c2): return c1**2 + c2**2													# sqrDistance mellan två färgvektorer

if __name__ == "__main__":
	setup()