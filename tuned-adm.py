#!/usr/bin/python
#
# tuned-adm: A command line utility for switching between user 
#            definable tuning profiles.
#
# Copyright (C) 2012 Red Hat, Inc.
# Authors: Jan Kaluza
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

import os
import sys
import locale
import signal

PIDFILE = "/run/tuned/tuned.pid"

def usage():
	print """
Usage: tuned-adm <command>

commands:
  help                           show this help message and exit
  list                           list all available and active profiles
  active                         show current active profile
  off                            switch off all tunning
  profile <profile-name>         switch to given profile
"""

def listdir_joined(path):
	return [os.path.join(path, entry) for entry in os.listdir(path)]

class Tuned_adm:

	def error(self, msg, exit_code = 1):
		print >>sys.stderr, msg
		sys.exit(exit_code)

	def check_permissions(self):
		if not os.geteuid() == 0:
			self.error("Only root can run this script.", 2)

	def run(self, args):
		if args[0] == "list":
			self.show_profiles()
		elif args[0] == "active":
			self.show_active_profile()
			#self.service_status("tuned")
			#self.service_status("ktune")
		elif args[0] == "off":
			self.check_permissions()
			self.off()
		elif args[0] == "profile":
			if len(args) >= 2:
			  self.check_permissions()
			  self.set_active_profile(args[1:])
			else:
				self.error("Invalid profile specification. Use 'tuned-adm list' to get all available profiles.")
		else:
			self.error("Nonexistent argument '%s'." % args[0])

	def off(self):
		pid = 0
		try:
			with open(PIDFILE) as f:
				pid = int(f.read())
		except (OSError,IOError) as e:
			pass
		if pid:
			os.kill(pid, signal.SIGTERM)

	def show_active_profile(self):
		try:
			with open("/etc/tuned/active_profile") as f:
				print "Current active profile:", f.read().replace("\n", " ")
		except:
			pass

	def get_profiles(self):
		profiles = []
		try:
			profiles += listdir_joined("/usr/lib/tuned")
		except:
			pass
		try:
			profiles += listdir_joined("/etc/tuned")
		except:
			pass

		return sorted(map(lambda p: os.path.basename(p), \
			filter(lambda p: os.path.exists(os.path.join(p, "tuned.conf")), profiles)))

	def show_profiles(self):
		print "Available profiles:"
		for p in self.get_profiles():
			print "- " + p
		self.show_active_profile()

	def set_active_profile(self, profiles):
		pid = 0
		try:
			with open(PIDFILE) as f:
				pid = int(f.read())
		except (OSError,IOError) as e:
			self.error("Cannot read %s: %s" % (PIDFILE, str(e)))

		for profile in profiles:
			if not profile in self.get_profiles():
				self.error("Profile %s doesn't exist." % profile)

		if pid:
			try:
				with open("/etc/tuned/active_profile", "w") as f:
					f.write('\n'.join(profiles))
			except (OSError,IOError) as e:
				log.error("Cannot write profile into /etc/tuned/active_profile: %s" % (e))
			os.kill(pid, signal.SIGHUP)
		

if __name__ == "__main__":
	args = sys.argv[1:]

	if len(args) < 1:
		print >>sys.stderr, "Missing arguments."
		usage()
		sys.exit(1)

	if args[0] in [ "help", "--help", "-h" ]:
		usage()
		sys.exit(0)

	tuned_adm = Tuned_adm()
	tuned_adm.run(args)
