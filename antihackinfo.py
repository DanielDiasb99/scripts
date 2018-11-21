"""
Joint every hack detector and data calculation script.
a main component of antihacktools(AHT)

AHT can detect, 
 aimbot
 mulltiple bullet
 no recoil
 no spread
 lapid build and break
 transparent hack
  etc...


you want to use this script, you get also all AHT scripts
and you should make some txt file in dist 
please read "read me.txt"

script by yuyasato 20170715

"""
from pyspades.constants import *
from pyspades.constants import UPDATE_FREQUENCY
from twisted.internet.reactor import callLater
from twisted.internet import reactor
from pyspades.server import position_data
from commands import alias,add
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians
from commands import admin, add, name, get_team, get_player,where_from
from time import gmtime, strftime
from networkdict import NetworkDict, get_network
from random import choice
import sys
import os
import json
import datetime

from AHT_ratio_handi_Y2 import aht_send_ratio
from AHT_aimbot_Y4 import aht_send_accuracy, aht_send_aimbot
from AHT_NRCSWHNS_Y2 import aht_send_norecoil,aht_send_centershot,aht_wallhack_send, aht_noscope_send
from AHT_destroyblock_Y2 import aht_destroyblock_send
from AHT_softwater_Y1 import aht_send_softwater
from AHT_hackereject_Y1 import aht_hacker_eject
from AHT_clientcheck_Y1 import aht_client_send
from AHT_nospread_Y1 import aht_nospread_send


DATA_OUTPUT_ON_CONSOLE = False
PASSWORD_OF_hackpointzero = "hpzps"		# password of debug command
AHT_ANNOUNCE = True
announce_FREQ = 5 #minutes
announce_message_list = [
	"In this server, auto hack detector is working.",
	"Don't use cheat. Cheater will be eliminated.",
	"Auto cheat detection script in operation.",
	"Antihack script is working."
	]

@alias('ej')   # Eliminate hackers forcibly   /ej (name)
@admin			
@name('ejecthacker')		
def ejecthacker(connection, hacker=None, reason=None):
	protocol = connection.protocol
	if hacker is not None:
		hacker = get_player(protocol, hacker)
	elif connection in protocol.players:
		return "command error. add hacker name. ex: /ej (hackername)"
	else:
		raise ValueError()
	hacker.data_gathering(True,True)
	return "%s was ejected" % hacker.name	
add(ejecthacker)		

@alias('hpz')	#debug safety command. if AHT work bad, use this command. the players hackpoint return zero.
@admin			
@name('hackpointzero')		
def hackpointzero(connection, hacker=None, pas="default"):
	protocol = connection.protocol
	if hacker is not None:
		hacker = get_player(protocol, hacker)
	elif connection in protocol.players:
		return "command error."
	else:
		raise ValueError()

	if pas != PASSWORD_OF_hackpointzero:
		print  "warning! HPZ pass error '%s' by %s"%(pas,connection.name)
		connection.data_gathering(True)
		return "HPZ pass error"

	if hacker.hpz_zeroed:
		hacker.hpz_zeroed=False
		hacker.data_gathering(True)
		return "%s hackpoint unzeroed" % hacker.name
	else:			
		hacker.hpz_zeroed=True
		hacker.data_gathering(True)
		return "%s hackpoint zeroed" % hacker.name	
add(hackpointzero)		

@alias('unhack')	#remove hacker list
@admin			
@name('removehacklist')		
def removehacklist(connection, ip):
	returned = connection.aht_write_list_zero(ip)
	if returned:
		return "IP %s's hack record deleted."%ip
	else:
		return "ERROR  : The IP %s is not recorded."%ip
add(removehacklist)	


@alias('h')
@name('antihackinfo')
def antihackinfo(connection, suspect = None, output=1):
	protocol = connection.protocol

	if suspect is not None:
		suspect = get_player(protocol, suspect)
	elif connection in protocol.players:
		suspect = connection
	else:
		raise ValueError()
	if output=="pr":
		output=2
	else:
		output=1
	if DATA_OUTPUT_ON_CONSOLE:
		output=2


	hackpoints = suspect.data_gathering(output)

	if connection.name!="Console":
		if connection.admin:
			connection.send_chat("multiple bullet %s  // BANrecord %stimes"%( suspect.multi, suspect.hack_record ))
			connection.send_chat("ratio k/d:%.2f, HS:%.2f   (%sHS) "% (suspect.kd_ratio, suspect.hs_ratio, suspect.hs_num))
			connection.send_chat("accr. rifle:%4.1f%%(%s/%s)  SMG:%4.1f%%(%s/%s)  SG:%4.1f%%(%s/%s)"% (suspect.sr_acc*100,suspect.sr_hit,suspect.sr_bullet, suspect.smg_acc*100, suspect.smg_hit,suspect.smg_bullet, suspect.sg_acc*100, suspect.sg_hit, suspect.sg_bullet))
			if suspect.country_data ==-1:
				connection.send_chat("%s (country couldn't determined)"% suspect.name)	
			else:
				connection.send_chat("%s from %s"% (suspect.name, suspect.country_data)	)
			return "%s's hack points is %s / 100" % (suspect.name, hackpoints)
		elif connection.address[0] != suspect.address[0]:
			connection.send_chat("multiple bullet %s  // BANrecord %stimes"%( suspect.multi, suspect.hack_record ))
			connection.send_chat("ratio k/d:%.2f, HS:%.2f   (%sHS) "% (suspect.kd_ratio, suspect.hs_ratio, suspect.hs_num))
			connection.send_chat("accr. rifle:%4.1f%%(%s/%s)  SMG:%4.1f%%(%s/%s)  SG:%4.1f%%(%s/%s)"% (suspect.sr_acc*100,suspect.sr_hit,suspect.sr_bullet, suspect.smg_acc*100, suspect.smg_hit,suspect.smg_bullet, suspect.sg_acc*100, suspect.sg_hit, suspect.sg_bullet))
			return "%s's hack points is %s / 100" % (suspect.name, hackpoints)
		else:
			connection.send_chat("ratio k/d:%.2f, HS:%.2f   (%sHS) "% (suspect.kd_ratio, suspect.hs_ratio, suspect.hs_num))
			connection.send_chat("accr. rifle:%4.1f%%(%s/%s)  SMG:%4.1f%%(%s/%s)  SG:%4.1f%%(%s/%s)"% (suspect.sr_acc*100,suspect.sr_hit,suspect.sr_bullet, suspect.smg_acc*100, suspect.smg_hit,suspect.smg_bullet, suspect.sg_acc*100, suspect.sg_hit, suspect.sg_bullet))
			return 			
	return "commanded"


add(antihackinfo)

def apply_script(protocol,connection,config):
	class AntihackinfoConnection(connection):

	#ratio data
		kill_num = hs_num = 0
		melee_num = grenade_num = 0
		death_num = shotkill_num = 0
		hs_ratio = kd_ratio = 0.0

	#accuracy data
		sr_hit = sr_bullet = 0
		smg_hit = smg_bullet = 0
		sg_hit = sg_bullet = 0
		sr_acc = smg_acc = sg_acc = 0.0

	#aimbot2 data
		hstime_point = killtime_point = 0
		multi = 0
		hstime_count = killtime_count = 0

	#norecoil data
		nr_points = 0
		nr_norecoil=0
		nr_small=0
		nr_normal=0

	#centershot data
		hits = 0
		cs = 0
		cs_points = 0

	#outrange shot
		ospt=0

	#softwater data
		sw_points = 0

	#wallhack data
		wh = 0
		wh_points = 0
		
	#country data
		country_data = -1	

	#clientcheck
		not_openspades = True

	#noscope
		noscope_points = 0
		short_on = short_off = 0
		middle_on = middle_off = 0
		long_on = long_off = 0

	#destroyblock
		destroy_hack_points=0
		destroy_suspicious_points=0
		build_hack_points=0
		bigspade=0

	#no spread
		nospread=0
		nosp_evidence=0

	#system
		hack_record=-1
		alart=False
		ban_reason = None
		hpz_zeroed=False
		ejected=False

		def on_hit(self, hit_amount, hit_player, type, grenade):
			hack = self.data_gathering()
			if not self.ejected:
				return connection.on_hit(self, hit_amount, hit_player, type, grenade)
			else:
				return False

		def on_block_destroy(self, x, y, z, mode):
			hack = self.data_gathering()
			if not self.ejected:
				return connection.on_block_destroy(self, x, y, z, mode)
			else:
				return False

		def data_gathering(suspect, printout = 0, eject_force=False):
			if suspect.hack_record <0:
				suspect.hack_record = suspect.aht_read_list()
			suspect.not_openspades = aht_client_send(suspect)
			suspect.kill_num, suspect.hs_num, suspect.melee_num, suspect.grenade_num, suspect.death_num, suspect.shotkill_num, suspect.hs_ratio, suspect.kd_ratio = aht_send_ratio(suspect)
			suspect.sr_hit, suspect.sr_bullet, suspect.smg_hit, suspect.smg_bullet, suspect.sg_hit, suspect.sg_bullet, suspect.sr_acc, suspect.smg_acc, suspect.sg_acc = aht_send_accuracy(suspect)
			suspect.hstime_point, suspect.killtime_point, suspect.multi, hstime_count, killtime_count = aht_send_aimbot(suspect)
			suspect.nospread, suspect.nosp_evidence = aht_nospread_send(suspect)
			s_sr_3, s_sr_2, s_sr_1, c_sr_3, c_sr_2, c_sr_1, s_smg_3, s_smg_2, s_smg_1, c_smg_3, c_smg_2, c_smg_1, s_sg_3, s_sg_2, s_sg_1, c_sg_3, c_sg_2, c_sg_1,suspect.nr_points = aht_send_norecoil(suspect)
			suspect.nr_norecoil = s_sr_3+c_sr_3+s_smg_3+c_smg_3+s_sg_3+c_sg_3
			suspect.nr_small =    s_sr_2+c_sr_2+s_smg_2+c_smg_2+s_sg_2+c_sg_2
			suspect.nr_normal =   s_sr_1+c_sr_1+s_smg_1+c_smg_1+s_sg_1+c_sg_1
			suspect.hits, suspect.cs, suspect.cs_points, suspect.ospt = aht_send_centershot(suspect)
			sw, nw, suspect.sw_points = aht_send_softwater(suspect)
			suspect.wh_points, suspect.wh = aht_wallhack_send(suspect)
			suspect.noscope_points, suspect.short_on, suspect.short_off, suspect.middle_on, suspect.middle_off, suspect.long_on, suspect.long_off = aht_noscope_send(suspect)
			suspect.destroy_hack_points, suspect.destroy_suspicious_points,suspect.bigspade, suspect.build_hack_points = aht_destroyblock_send(suspect)
			suspect.country_data, city_data, region_data = suspect.from_data()

		#records max points 
			if killtime_count>suspect.killtime_count:
				suspect.killtime_count = killtime_count
			if hstime_count>suspect.hstime_count:
				suspect.hstime_count = hstime_count

			hack_points, well_points = suspect.calculation()

			if suspect.wh_points>20 or suspect.nr_points>50 or suspect.noscope_points>20 or suspect.destroy_suspicious_points>70 or suspect.ospt>30 or suspect.nospread>50 or eject_force:
				printout=1
			if printout>=1 or hack_points>70:

								str=[]
								
								str.append("/////    %s    /////"%datetime.datetime.now())
								if suspect.country_data==-1:
									str.append("  %s (IP:%s)"%(suspect.name,suspect.address[0]))
								else:
									str.append("  %s (IP:%s) from %s"%(suspect.name,suspect.address[0], suspect.country_data))
								if suspect.user_types.admin:right="login as admin"
								elif suspect.user_types.trusted:right="login as trusted"
								else:right=""
								if suspect.not_openspades:
									str.append("Normal Client    ping %s     %s"%(suspect.latency,right))
								else:
									str.append("OpenSpades       ping %s     %s"%(suspect.latency,right))
								str.append("ratio   K/D        HS/shotkill")
								str.append("        %3.2f           %3.2f    " %(suspect.kd_ratio,suspect.hs_ratio  ))
								str.append("")
								str.append("kill %d   shotkill %d   HS %d"%(suspect.kill_num, suspect.shotkill_num, suspect.hs_num))
								str.append("melee %d   grenade %d   death %d"%(suspect.melee_num, suspect.grenade_num, suspect.death_num))
								str.append("")
								str.append("          rifle      SMG        SG")
								str.append("hit       %4d      %4d      %4d"%(suspect.sr_hit,suspect.smg_hit,suspect.sg_hit))
								str.append("bullet    %4d      %4d      %4d"%(suspect.sr_bullet,suspect.smg_bullet,suspect.sg_bullet))
								str.append("accuracy  %4.1f      %4.1f      %4.1f"%( suspect.sr_acc*100,suspect.smg_acc*100,suspect.sg_acc*100))
								str.append("")
								str.append(" max of in 20sec ")
								str.append("kill: %d    HS: %d"%(suspect.killtime_count,suspect.hstime_count))
								str.append("")
								str.append("norecoil    rifle         SMG           SG" )
								str.append("stand   %3d %3d %3d  %3d %3d %3d  %3d %3d %3d"% (s_sr_3, s_sr_2, s_sr_1, s_smg_3, s_smg_2, s_smg_1, s_sg_3, s_sg_2, s_sg_1))
								str.append("chrouh  %3d %3d %3d  %3d %3d %3d  %3d %3d %3d"% (c_sr_3, c_sr_2, c_sr_1, c_smg_3, c_smg_2, c_smg_1, c_sg_3, c_sg_2, c_sg_1))
								str.append("norecoil points = %s/200"%suspect.nr_points)
								str.append("")
								str.append("scope   short    middle     long") 
								str.append("  on     %3d      %3d       %3d"%(suspect.short_on, suspect.middle_on, suspect.long_on))
								str.append("  off    %3d      %3d       %3d"%(suspect.short_off, suspect.middle_off, suspect.long_off))
								str.append("noscope points %d/15"%suspect.noscope_points)
								str.append("")
								str.append("destroyblock  hack:%d   suspicious:%d"%(suspect.destroy_hack_points, suspect.destroy_suspicious_points))
								str.append("          bigspade:%d   rapidbuild:%d"%(suspect.bigspade, suspect.build_hack_points))
								str.append("")
								str.append("hit %d    center_shot %d   aim assist %d"%(suspect.hits,suspect.cs,suspect.ospt))
								str.append("centershot_points  %d/50"%suspect.cs_points)
								str.append("")
								str.append("soft water  %d    normal water  %d"%(sw,nw))
								str.append("softwater_points  %d/100"%suspect.sw_points)
								str.append("")
								str.append("wallhack_counts %d     wallhack_points %d/500 "%(suspect.wh, suspect.wh_points))
								str.append("")
								str.append(" multi,     HStime,     killtime")
								str.append(" %3d        %3d          %3d"%(suspect.multi, suspect.hstime_point,suspect.killtime_point))
								str.append("")
								str.append("nospread point %d/200 , evidence %d/100"%(suspect.nospread,suspect.nosp_evidence))
								str.append("")
								if suspect.hack_record>0:
									str.append("hack record     BAN %d times"%suspect.hack_record)
								str.append("%s well point is %.2f/100"%(suspect.name,well_points))
								str.append("%s hack point is %.2f/100"%(suspect.name, hack_points))
								if hack_points>=100 or eject_force:
									str.append("ban %d times.   reason:%s"%(suspect.hack_record+1,suspect.ban_reason))
									if eject_force:	
										str.append("manual ejected by admin")	
								str.append("////////////////////////////////////")
								str.append("")

								f = open('AHT_log.txt', 'a') 
								for s in str:
									f.write(s+'\n') 
									if eject_force or DATA_OUTPUT_ON_CONSOLE or printout==2:
										print s
								f.close()

			if hack_points>=100 or eject_force:
				if not (suspect.user_types.trusted or suspect.user_types.admin) or eject_force:
					f = open('../../AHT_ejected_log.txt', 'a') 
					for s in str:
						f.write(s+'\n') 
					f.close()

				#csv
					#   date, [], name, ip, country, city, region, [], opsp, ping, [], right, [], record, wellpt, hackpt, ejectforce, [], [],[],[],[],[], kdratio, hsratio, killnum, shotkill, hs, melee, grenade, death, [], srhit, smg, sg, srbullet, smg, sg, sracc, smg, sg, [], [],[],[],[],[], killtime, hstime, [], nrstandsr3, sr2, sr1, mg3, mg2, mg1, sg3, sg2, sg1,[],[],[],[], nrcrouchsr3, sr2, sr1, mg3, mg2, mg1, sg3, sg2, sg1,[],[],[],[], nrpt,[],[], scope_short_on, med_on, long_on, short_off, med_off, long_off, [], [], [], nscopept, [], destroy_hack, destroy_suspect, bigspade, rapidbuild, [], [], [], [], hit, cscount, ospt, cspt, [], [], [], [], softwater, normalwater,swpt, [], [], wallhack, wakkhackpt, [], [], nospreadpt, nospread_evidence, [], [], multi, hstimept, killtimept, [],[], [],[],[],[],[]
					csvdata=[]
					sname = suspect.name.replace(',', ' ').encode('ascii', 'ignore')
					scountry = suspect.country_data
					if suspect.country_data != -1: 
						scountry = suspect.country_data.replace(',', ' ').encode('ascii', 'ignore')
					scity = city_data
					if city_data != -1:
						scity = city_data.replace(',', ' ').encode('ascii', 'ignore')
					sregion = region_data
					if region_data != -1: 
						sregion = region_data.replace(',', ' ').encode('ascii', 'ignore')

					#general
					csvdata.append("%s,   , %s, %s, %s, %s, %s,   , %s, %s,   , %s,   , %d, %.2f, %.2f, %s,   , "%(
							   ## 	 d  []  na  ip  co  cty reg []  os  pg  []  rig []  rec wel   hkp   ejf
						datetime.datetime.now(),
						sname,
						suspect.address[0],
						scountry,
						scity,
						sregion,
						not suspect.not_openspades,
						suspect.latency,
						right,
						suspect.hack_record+1,
						well_points,
						hack_points,
						eject_force
						))

					#blank
					csvdata.append("  ,   ,   ,   ,   , ")

					#ratio
					csvdata.append("%3.2f, %3.2f , %d, %d, %d, %d, %d, %d,   , "%(
							   ## 	kd        hs  kil ski  hs  me  gr  de 
						suspect.kd_ratio,
						suspect.hs_ratio,
						suspect.kill_num,
						suspect.shotkill_num,
						suspect.hs_num,
						suspect.melee_num, 
						suspect.grenade_num, 
						suspect.death_num
						))

					#accuracy
					csvdata.append("%d, %d, %d, %d, %d, %d, %4.1f, %4.1f, %4.1f,   , "%(
							   ## 	sr  mg  sg  sr  mg  sg  sracc  mgacc  sgacc
						suspect.sr_hit,
						suspect.smg_hit,
						suspect.sg_hit,
						suspect.sr_bullet,
						suspect.smg_bullet,
						suspect.sg_bullet,
						suspect.sr_acc*100,
						suspect.smg_acc*100,
						suspect.sg_acc*100
						))

					#blank
					csvdata.append("  ,   ,   ,   ,   , ")

					#killtime
					csvdata.append("%d, %d,   , "%(
							   ## 	kil  hs
						suspect.killtime_count,
						suspect.hstime_count
						))

					#norecoil_stand
					csvdata.append("%d, %d, %d, %d, %d, %d, %d, %d, %d,   ,   ,   ,   , "%(
							   ## 	sr3 sr2 sr1 mg3 mg2 mg1 sg3 sg2 sg1
						s_sr_3, s_sr_2, s_sr_1, s_smg_3, s_smg_2, s_smg_1, s_sg_3, s_sg_2, s_sg_1
						))

					#norecoil_crouch
					csvdata.append("%d, %d, %d, %d, %d, %d, %d, %d, %d,   ,   ,   ,   , "%(
							   ## 	sr3 sr2 sr1 mg3 mg2 mg1 sg3 sg2 sg1
						c_sr_3, c_sr_2, c_sr_1, c_smg_3, c_smg_2, c_smg_1, c_sg_3, c_sg_2, c_sg_1
						))

					#norecoil_pt
					csvdata.append("%s,   ,   , "%(
							   ## 	nr
						suspect.nr_points
						))

					#noscope
					csvdata.append("%d, %d, %d, %d, %d, %d,   ,   ,   , %d,   , "%(
							   ## 	son mon lon sof mof lof             pt
						suspect.short_on,
						suspect.middle_on, 
						suspect.long_on,
						suspect.short_off, 
						suspect.middle_off, 
						suspect.long_off,
						suspect.noscope_points
						))

					#rapidhack
					csvdata.append("%d, %d, %d, %d,   ,   ,   ,   , "%(
							   ## 	db  ds  bs  bh              
						suspect.destroy_hack_points,
						suspect.destroy_suspicious_points,
						suspect.bigspade,
						suspect.build_hack_points
						))

					#center shot
					csvdata.append("%d, %d, %d, %d,   ,   ,   ,   , "%(
							   ## 	ht  cs  os  pt              
						suspect.hits,
						suspect.cs,
						suspect.ospt,
						suspect.cs_points
						))

					#soft water
					csvdata.append("%d, %d, %d,   ,   , "%(
							   ## 	sw  nw  pt               
						sw,
						nw,
						suspect.sw_points
						))

					#wall hack
					csvdata.append("%d, %d,   ,   , "%(
							   ## 	wh  pt               
						suspect.wh,
						suspect.wh_points
						))

					#nospread
					csvdata.append("%d, %d,   ,   , "%(
							   ## 	nsp evd               
						suspect.nospread,
						suspect.nosp_evidence
						))

					#other
					csvdata.append("%d, %d, %d,   ,   , "%(
							   ## 	mlt hst klt              
						suspect.multi,
						suspect.hstime_point,
						suspect.killtime_point
						))

					#blank
					csvdata.append("  ,   ,   ,   ,   , ")

					f = open('../../AHT_ejected_csv.csv', 'a') 
					for s in csvdata:
						f.write(s) 
					f.write('\n') 
					f.close()				


					suspect.aht_write_list(suspect.hack_record+1)
					suspect.ejected=True
					aht_hacker_eject(suspect, suspect.ban_reason, suspect.hack_record+1)
				else:
					print "trusted user %s's hack point is %s/100" % (suspect.name, hack_points)
					for player in suspect.protocol.players.values():
						if player.admin:
							player.send_chat("trusted user %s's hack point is %s/100" % (suspect.name, hack_points))
				
			if 70<hack_points:
				if not suspect.alart:
					suspect.alart=True
					suspect.warn_admins(hack_points)
			return hack_points

		def warn_admins(self, hack_points):
			for player in self.protocol.players.values():
				if player.admin:
					player.send_chat("%s's hack point is %s/100" % (self.name, hack_points))
			return

		def calculation(suspect):
			well_points = 0
			hack_points = 0
			suspect.ban_reason = None

			if suspect.hstime_point>2:
				well_points += suspect.hstime_point * suspect.hstime_count
			if suspect.killtime_point>2:
				well_points += suspect.killtime_point * suspect.killtime_count/3
			if suspect.kd_ratio>4:
				well_points += suspect.kd_ratio*2

		#high HSratio
			if suspect.hs_ratio>=0.9 and (suspect.shotkill_num > 15 or suspect.hack_record):
				well_points += suspect.shotkill_num	*suspect.hs_ratio * 2
				if suspect.hs_ratio>=1:					
					if suspect.shotkill_num>150 or (suspect.cs_points >= 20 or suspect.nr_points >=80 or suspect.ospt>30 or suspect.hack_record):
						hack_points += suspect.shotkill_num
				elif suspect.hs_ratio>=0.9 and ( suspect.cs_points >= 20 or suspect.nr_points >=80 or suspect.ospt>30 or suspect.hack_record):
						hack_points += suspect.shotkill_num/1.5
				elif suspect.hs_ratio>=0.95 and suspect.shotkill_num > 50 and ( suspect.cs_points >= 20 or suspect.nr_points >=80 or suspect.ospt>30 or suspect.hack_record):
						hack_points += suspect.shotkill_num
			
		#high accuracy
			if suspect.sr_acc > 0.9:
				if suspect.sr_bullet>5:
					well_points += suspect.sr_bullet*suspect.sr_acc 
				if suspect.sr_acc == 1 and (suspect.sr_bullet>50 or suspect.cs_points >= 20 or suspect.nr_points >=80 or (suspect.hack_record and suspect.sr_bullet>15)):
						hack_points += suspect.sr_bullet*suspect.sr_acc*(suspect.cs_points+1)
				if suspect.sr_acc > 1 and (suspect.sr_bullet>20 or suspect.multi >= 4 or  suspect.nr_points >=80 or suspect.hack_record or suspect.destroy_hack_points>1 or suspect.destroy_suspicious_points>9):
						hack_points += suspect.sr_bullet*suspect.sr_acc*(suspect.multi+1)* (suspect.hack_record+1)*((suspect.destroy_suspicious_points/10)+1)

			if suspect.smg_acc > 0.8:
				if suspect.smg_bullet>10:
					well_points += suspect.smg_bullet*suspect.smg_acc 
				if suspect.smg_acc == 1 and (suspect.smg_bullet>50 or suspect.cs_points >= 20 or suspect.nr_points >=80):
						hack_points += suspect.smg_bullet*suspect.smg_acc*(suspect.cs_points+1)
				if suspect.smg_acc > 1 and (suspect.smg_bullet>20 or suspect.multi >= 4 or  suspect.nr_points >=80 or suspect.hack_record or suspect.destroy_hack_points>1 or suspect.destroy_suspicious_points>9):
						hack_points += suspect.smg_bullet*suspect.smg_acc*(suspect.multi+1)* (suspect.hack_record+1)*((suspect.destroy_suspicious_points/10)+1)

			if suspect.sg_acc > 0.9:
				if suspect.sg_bullet>4:
					well_points += suspect.sg_bullet*suspect.sg_acc 
				if suspect.sg_acc >= 1 and (suspect.sg_bullet>20 or suspect.multi >= 20  or  suspect.nr_points >=80 or suspect.hack_record):
						hack_points += suspect.sg_bullet*suspect.sg_acc*(suspect.multi+1)* (suspect.hack_record+1)

			if hack_points>=90:		
				suspect.ban_reason = "aimbot"

		##softwater hack
			if suspect.sw_points >= 20 or (suspect.hack_record and suspect.sw_points >= 12):
				hack_points += suspect.sw_points*(suspect.hack_record+1)
				if suspect.sw_points>=80:		
					suspect.ban_reason = "softwater hack"

		##norecoil
			if suspect.nr_points >=50 or suspect.hack_record:		
				hack_points += suspect.nr_points/4 * (suspect.hack_record+1)
				if suspect.nr_points>=140:		
					suspect.ban_reason = "norecoil hack"

		##aim assist
			if suspect.ospt>100 or  (suspect.hack_record and suspect.ospt > 30):
				hack_points += suspect.ospt/0.6	*(suspect.hack_record+1)
				if suspect.ospt>100:		
					suspect.ban_reason = "aimbot hack"

		##rapid hack
			rapidhack=0
			if suspect.destroy_hack_points>20 or suspect.destroy_suspicious_points>50:
				rapidhack += suspect.destroy_hack_points*3

			if suspect.bigspade>31:
				rapidhack += suspect.bigspade*3

			if suspect.build_hack_points>3:
				if suspect.build_hack_points<9:
					rapidhack += suspect.build_hack_points*10
				elif suspect.build_hack_points<20:
					rapidhack += 80
				else:
					rapidhack += suspect.build_hack_points*10

			if rapidhack>80:		
				suspect.ban_reason = "rapid hack"
			hack_points += rapidhack

		#nospread
			nospr=0
			if suspect.nospread>20:
				nospr += suspect.nospread/2* (suspect.hack_record+1)


			if suspect.nosp_evidence>=100:
				nospr += suspect.nosp_evidence

			if nospr>80:		
				suspect.ban_reason = "no spread hack"
			hack_points += nospr

		##aimbot
			if suspect.cs_points >= 20 or (suspect.hack_record and suspect.cs_points >= 12):
				hack_points += suspect.cs_points*2	*(suspect.hack_record/2.1+1)
				if suspect.cs_points>=30:		
					suspect.ban_reason = "aimbot hack"

		##wall penetrate
			if suspect.wh>4 or (suspect.hack_record and suspect.wh >= 2): 
				hack_points += suspect.wh_points/5
				if suspect.wh_points>400:
					suspect.ban_reason = "wallhack (penetrating bullet)"	

		##multiple bullets
			if suspect.multi>=4 or suspect.hack_record or suspect.destroy_hack_points>2 or suspect.destroy_suspicious_points>9:
				hack_points += suspect.multi * 5*( suspect.hack_record+1) *(1+(suspect.destroy_suspicious_points/5.0))
				if suspect.multi>=17:		
					suspect.ban_reason = "multiple bullets hack"
	
			hack_points += suspect.hack_record*10			

			if suspect.hpz_zeroed:
				hack_points = 0
			hack_points = int(hack_points)
			return hack_points, well_points

		def aht_write_list_zero(self, unban_ip):
			self.ips = NetworkDict()
			try:
				self.ips.read_list(json.load(open('../../AHT_hacker_list.txt', 'rb')))
			except IOError:
				print "AHT_hacker_list.txt open error."
				pass
			client_ip = unban_ip
			try:
				list = self.ips[client_ip]
				self.ips.remove(client_ip)
			except KeyError:
				return False
			looping = True
			while looping:
				try:
					list = self.ips[client_ip]
					self.ips.remove(client_ip)
				except KeyError:
					looping=False
			name = list[0]
			self.ips[client_ip] = (name or '(unknown)', 0)			
			json.dump(self.ips.make_list(), self.open_create('../../AHT_hacker_list.txt', 'wb'), indent = 4)

			try:
				self.protocol.remove_ban(client_ip)
			except KeyError:
				pass
			return True
				
		def aht_write_list(self, num):
			self.ips = NetworkDict()
			try:
				self.ips.read_list(json.load(open('../../AHT_hacker_list.txt', 'rb')))
			except IOError:
				print "AHT_hacker_list.txt open error."
				pass
			client_ip = self.address[0]
			try:
				list = self.ips[client_ip]
				name = self.name
				if list[0] == name or ('deuce' in list[0] and len(name)<8):
					self.ips.remove(client_ip)
				self.ips[client_ip] = (name or '(unknown)', num)			
				json.dump(self.ips.make_list(), self.open_create('../../AHT_hacker_list.txt', 'wb'), indent = 4)

			except KeyError:
				name = self.name
				self.ips[client_ip] = (name or '(unknown)', num)			
				json.dump(self.ips.make_list(), self.open_create('../../AHT_hacker_list.txt', 'wb'), indent = 4)

		def aht_read_list(self):
			client_ip = self.address[0]
			name = self.name
			with open('../../AHT_hacker_list.txt', 'rb') as file:
				data = json.load(file)
			ip_al_regi=False
			num=0	
			num_name=0
			ip_num=0		
			for list in data:
				regi_ip = list[1]
 				if regi_ip==client_ip:
					ip_al_regi=True
					if list[2]>ip_num:
						ip_num =list[2]
			if not ip_al_regi:
				for list in data:		
					regi_name = list[0]
					if (name == regi_name) and not((('deuce' in name )or ('Deuce' in name ))and len(name)<8):
						num_name =list[2]
					if num_name>num:
						num=num_name
				num=0
			else:
				num=ip_num
			return num

		def create_path(self,path):
		    if path:
		        try:
		            os.makedirs(path)
		        except OSError:
		            pass

		def create_filename_path(self,path):
		    self.create_path(os.path.dirname(path))

		def open_create(self,filename, mode):
		    self.create_filename_path(filename)
		    return open(filename, mode)

		def from_data(suspect):
			try:
				import pygeoip
				database = pygeoip.GeoIP('./data/GeoLiteCity.dat')
			except ImportError:
				print "('from' command disabled - missing pygeoip)"
				return
			except (IOError, OSError):
				print "('from' command disabled - missing data/GeoLiteCity.dat)"
				return
			record = database.record_by_addr(suspect.address[0])
			if record is None:
				country_data = -1
				city_data  = -1
				region_data = -1
			else:
				items = []		
				for entry in ('country_name', 'city', 'region_name'):
					# sometimes, the record entries are numbers or nonexistent
					try:
						value = record[entry]
						if entry=='country_name':
							country_data = value
						if entry=='city':
							city_data = value
						if entry=='region_name':
							region_data = value
						int(value) # if this raises a ValueError, it's not a number
						continue
					except KeyError:
						continue
					except ValueError:
						pass
					items.append(value)
			return country_data, city_data, region_data

	class AntihackinfoProtocol(protocol):
		def __init__(self, *arg, **kw):
			protocol.__init__(self, *arg, **kw)
			if AHT_ANNOUNCE and announce_FREQ >0:
				callLater(announce_FREQ * 30, self.send_announce)

		def send_announce(self):
			message = choice(announce_message_list)
			self.send_chat(message)

			callLater(announce_FREQ * 60, self.send_announce)
		
		def on_votekick_start(self, instigator, victim, reason):
			victim.data_gathering(True)
			instigator.data_gathering(True)
			return protocol.on_votekick_start(self, instigator, victim, reason)

	return AntihackinfoProtocol, AntihackinfoConnection

