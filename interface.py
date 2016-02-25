#!/bin/bash /Users/FWerpers/.virtualenvs/jodlHack/bin/fwpy
#coding: utf-8

import wx
import wx.lib.scrolledpanel as scrolled
import wx.lib.wordwrap as ww
import ConfigParser
import dateutil
import dateutil.parser as dup
import datetime
import re
import urllib
import os
import json

import gmaps
import jodl

# Global config file
config = ConfigParser.RawConfigParser()
config.read('config.cfg')

base_dir = os.path.dirname(os.path.abspath(__file__))

class PostsPanel(scrolled.ScrolledPanel):
	def __init__(self, parent):
		scrolled.ScrolledPanel.__init__(self, parent, id=wx.ID_ANY)
		self.parent = parent
		self.SetBackgroundColour('WHITE')

		# Container for the posts
		self.posts_box = wx.BoxSizer(wx.VERTICAL)

		self.SetSizer(self.posts_box)
		self.SetupScrolling(scroll_x=False)

	def populate_posts(self, posts):
		for post in posts:
			post_panel = PostPanel(self,post)
			self.posts_box.Add(post_panel, proportion=0, flag=wx.EXPAND|wx.BOTTOM, border=2)

		self.posts_box.Layout()
		self.posts_box.Layout()

	def update(self, posts):
		self.Scroll(0,0)
		self.posts_box.Clear(True)
		self.populate_posts(posts)

class RepliesPanel(PostsPanel):

	def populate_posts(self, post):
		if 'children' in post:
			post_panel = PostPanel(self,post)
			self.posts_box.Add(post_panel, proportion=0, flag=wx.EXPAND|wx.BOTTOM, border=2)
			children = post['children']
			for child in children:
				post_panel = PostPanel(self,child)
				self.posts_box.Add(post_panel, proportion=0, flag=wx.EXPAND)

		self.posts_box.Layout()
		self.posts_box.Layout()

	def update(self,post):
		self.Scroll(0,0)
		self.posts_box.Clear(True)
		self.populate_posts(post)

class PostPanel(wx.Panel):
	def __init__(self,parent,post):
		wx.Panel.__init__(self, parent, id=wx.ID_ANY, style=wx.NO_BORDER)
		self.parent = parent
		self.post = post
		self.post_id = post['post_id']

		self.Bind(wx.EVT_LEFT_UP, self.onClick)

		message = self.post['message']
		message = self.remove_emojis(message)

		color = '#'+post['color']

		created_at = dup.parse(post['created_at'])
		now = datetime.datetime.now(dateutil.tz.tzutc())
		sec_diff = (now - created_at).total_seconds()
		min_diff = round(float(sec_diff)/60)

		self.SetBackgroundColour(color)
		dc = wx.ClientDC(self) # needed for wordwrapping

		# Image handling
		if 'image_url' in self.post:
			image_dir = base_dir + '/temp_images'
			if not os.path.isdir(image_dir):
				os.mkdir(image_dir)

			image_url = 'http:' + post['image_url']
			post_id = post['post_id']
			image_path = image_dir + '/' + post_id + '.jpg'
			urllib.urlretrieve(image_url, image_path)
			image = wx.Image(image_path)
			width = image.GetWidth()
			height = image.GetHeight()
			new_width = 170
			new_height = 170*height/width
			image = image.Scale(new_width, new_height)
			bitmap = image.ConvertToBitmap()
			image_view = wx.StaticBitmap(self, wx.ID_ANY, bitmap)

			content = image_view

		# Post text handling
		else:
			# Post text
			text_width = 170
			text_wrapped = ww.wordwrap(message,text_width,dc) # this line causes a segmentation fault
			text = wx.StaticText(self, label=text_wrapped)
			text.SetForegroundColour('WHITE')

			content = text

		# Post time
		if min_diff>59:
			h_diff = round(min_diff/60)
			time_label = str(int(h_diff))+'h'
		else:
			time_label = str(int(min_diff))+'m'

		time = wx.StaticText(self, label=time_label)
		time.SetForegroundColour('#e6e6e6')

		# Vote count
		vote_count = post['vote_count']
		votes = wx.StaticText(self, label=str(vote_count))
		votes.SetForegroundColour('WHITE')

		# Upvote button
		upvote_button = wx.Button(self, label='Upvote')
		self.Bind(wx.EVT_BUTTON, self.upvote_callback, upvote_button)

		# Downvote button
		downvote_button = wx.Button(self, label='Downvote')
		self.Bind(wx.EVT_BUTTON, self.downvote_callback, downvote_button)

		# Layout
		meta_box = wx.BoxSizer(wx.VERTICAL)
		meta_box.Add(time, flag=wx.ALIGN_RIGHT)
		meta_box.Add(votes, flag=wx.ALIGN_RIGHT|wx.BOTTOM, border=5)
		meta_box.Add(upvote_button, flag=wx.ALIGN_RIGHT|wx.BOTTOM, border=5)
		meta_box.Add(downvote_button, flag=wx.ALIGN_RIGHT)

		post_box = wx.BoxSizer(wx.HORIZONTAL)
		post_box.Add(content,proportion=1,flag=wx.TOP|wx.BOTTOM|wx.LEFT,border=5)
		post_box.Add(meta_box,proportion=0, flag=wx.ALL|wx.ALIGN_RIGHT, border=5)

		post_box.SetSizeHints(self)
		self.SetSizer(post_box)

	def remove_emojis(self, post):
		try:
			# Wide UCS-4 build
			regex = re.compile(u'['
				u'\U0001F300-\U0001F64F'
				u'\U0001F680-\U0001F6FF'
				u'\U0001F917'
				u'\u2600-\u26FF\u2700-\u27BF]+', 
				re.UNICODE)
		except re.error:
			# Narrow UCS-2 build
			regex = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
			# regex = re.compile(u'('
			# 	u'\ud83c[\udf00-\udfff]|'
			# 	u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
			# 	u'[\u2600-\u26FF\u2700-\u27BF])+', 
			# 	re.UNICODE)
		return regex.sub('',post)

	def onClick(self,event):
		self.parent.parent.populate_replies_panel(self.post)

	def upvote_callback(self, event):
		self.upvote()
		print(json.dumps(self.post,indent=4,separators=(',',':')))

	def downvote_callback(self, event):
		self.downvote()
		print(json.dumps(self.post,indent=4,separators=(',',':')))

	def upvote(self):
		location = self.post['location']['loc_coordinates']

		jodl_client = self.parent.parent.jodl_client

		jodl_client.get_karma()
		jodl_client.place(location)
		jodl_client.upvote(self.post_id)

	def downvote(self):
		location = self.post['location']['loc_coordinates']

		jodl_client = self.parent.parent.jodl_client

		jodl_client.get_karma()
		jodl_client.place(location)
		jodl_client.downvote(self.post_id)

class ControlPanel(wx.Panel):
	def __init__(self,parent):
		wx.Panel.__init__(self,parent,id=wx.ID_ANY)
		self.parent = parent

		# Controls
		self.method_choice = wx.ComboBox(self, choices=['Address','Coordinates'])
		self.choice_button = wx.Button(self, label='Refresh')

		## Address controls
		self.addr_label = wx.StaticText(self, label='Address:')
		self.addr_input = wx.TextCtrl(self)
		if config.has_option('Remember', 'addr_input'):
			self.addr_input.SetValue(config.get('Remember', 'addr_input'))

		## Coordinates controls
		self.lat_label = wx.StaticText(self, label='Latitude:')
		self.lng_label = wx.StaticText(self, label='Longitude:')
		self.lat_input = wx.TextCtrl(self)
		self.lng_input = wx.TextCtrl(self)

		## Input bindings
		self.addr_input.Bind(wx.EVT_KEY_DOWN, self.key_callback)
		self.lat_input.Bind(wx.EVT_KEY_DOWN, self.key_callback)
		self.lng_input.Bind(wx.EVT_KEY_DOWN, self.key_callback)

		# Address method sizer
		self.addr_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.addr_sizer.Add(self.addr_label, proportion=1, flag=wx.EXPAND)
		self.addr_sizer.Add(self.addr_input, proportion=1, flag=wx.EXPAND)

		# Coordinate method szier
		self.lat_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.lat_sizer.Add(self.lat_label, proportion=1, flag=wx.EXPAND)
		self.lat_sizer.Add(self.lat_input, proportion=1, flag=wx.EXPAND)

		self.lng_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.lng_sizer.Add(self.lng_label, proportion=1, flag=wx.EXPAND)
		self.lng_sizer.Add(self.lng_input, proportion=1, flag=wx.EXPAND)

		self.coord_sizer = wx.BoxSizer(wx.VERTICAL)
		self.coord_sizer.Add(self.lat_sizer)
		self.coord_sizer.Add(self.lng_sizer)
		self.coord_sizer.Hide(self.coord_sizer, recursive=True)
		self.coord_sizer.Layout()

		# Layout
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		self.main_sizer.Add(self.method_choice, flag=wx.BOTTOM, border=5)
		self.main_sizer.Add(self.addr_sizer)
		self.main_sizer.Add(self.choice_button)

		padding_sizer = wx.BoxSizer()
		padding_sizer.Add(self.main_sizer, flag=wx.ALL|wx.EXPAND, border=5)
		self.SetSizer(padding_sizer)

	def key_callback(self, event):
		ENTER_code = 13
		if event.GetKeyCode() == ENTER_code:
			self.parent.refresh_callback()
		event.Skip()
	
	def get_location_method(self):
		return self.method_choice.GetValue()

	def location_input_empty(self):
		if (self.addr_input.IsEmpty()
			and (self.lat_input.IsEmpty()
				or self.lng_input.IsEmpty())):

			return True

	def get_location(self):
		location_method = self.get_location_method()
		if (location_method=='Coordinates'):
			lat = self.lat_input.GetValue()
			lng = self.lng_input.GetValue()
			coords = (float(lat),float(lng))

			# Update the address field
			addr = gmaps.get_address(coords)
			self.addr_input.SetValue(addr)

		elif (location_method=='Address'):
			addr = self.addr_input.GetValue()

			coords = gmaps.get_coords(addr)

			# Update the coordinate fields
			self.lat_input.SetValue(str(coords[0]))
			self.lng_input.SetValue(str(coords[1]))

		return coords

	def update_layout(self):
		location_method = self.get_location_method()
		sizer = self.main_sizer 
		if (location_method=='Coordinates'):

			sizer.Hide(1)
			sizer.Detach(1)
			sizer.Insert(1,self.coord_sizer)
			sizer.Show(1)

		elif (location_method=='Address'):

			sizer.Hide(1)
			sizer.Detach(1)
			sizer.Insert(1,self.addr_sizer)
			sizer.Show(1)

		sizer.Layout()


class MainPanel(wx.Panel):
	def __init__(self,parent):
		wx.Panel.__init__(self,parent,id=wx.ID_ANY)

		self.parent = parent

		self.control_panel = ControlPanel(self)
		self.posts_panel = PostsPanel(self)
		self.replies_panel = RepliesPanel(self)

		# Control events
		self.Bind(wx.EVT_BUTTON, self.refresh_callback, self.control_panel.choice_button)
		self.Bind(wx.EVT_COMBOBOX, self.location_callback, self.control_panel.method_choice)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.control_panel, proportion=0, flag=wx.EXPAND)
		sizer.Add(self.posts_panel, proportion=1, flag=wx.EXPAND)
		sizer.Add(self.replies_panel, proportion=0, flag=wx.EXPAND)

		# Fit the main frame to the content of the sizer
		self.SetSizer(sizer)
		sizer.Fit(parent)

	def refresh_callback(self, event=None):
		if not self.control_panel.location_input_empty():
			# Get location from control panel
			coords = self.control_panel.get_location()
			# Generate location data for the Jodel API
			self.jodl_location = gmaps.get_jodl_location(coords,10)

			# Get access token
			access_token = self.token_from_config()

			# Get posts
			try:
				self.jodl_client = jodl.ApiClient(access_token)
			except jodl.AuthException:
				# Re-register client if the saved one is invalid
				self.re_register_user()
			self.jodl_client.place(self.jodl_location)
			posts = self.jodl_client.get_posts()
			self.posts_panel.update(posts)
			
			self.adjust_frame_width()

			# Remember address field
			if not config.has_section('Remember'):
				config.add_section('Remember')
			config.set('Remember', 'addr_input', self.control_panel.addr_input.GetValue())
			with open('config.cfg', 'wb') as configfile:
				config.write(configfile)
			
		else:
			print('Location input is empty!')

	def token_from_config(self):
		if config.has_option('Credentials','access_token'):
			print('Access token found in config file.')
			access_token = config.get('Credentials','access_token')
			return access_token
		else:
			return self.create_new_token()

	def re_register_user(self):
		user_string = config.get('Credentials','user_string')
		user_id = jodl.create_ID(user_string)
		self.jodl_client = jodl.ApiClient(user_id, self.jodl_location)

		print('Adding access token to config file.')
		config.set('Credentials','access_token',self.jodl_client.access_token)

	def location_callback(self, event):
		self.control_panel.update_layout()

	def populate_replies_panel(self, post):
		self.replies_panel.update(post)
		self.adjust_frame_width()

	def adjust_frame_width(self):
		# FULHAXX???
		# Only fit the width
		# Unclear why this needs to be done twice
		new_frame_size = self.GetSizer().ComputeFittingClientSize(self.parent)
		self.parent.SetSize((new_frame_size.GetWidth(),-1))
		new_frame_size = self.GetSizer().ComputeFittingClientSize(self.parent)
		self.parent.SetSize((new_frame_size.GetWidth(),-1))

app = wx.App(0)
frame = wx.Frame(None, wx.ID_ANY,'jodl')
fa = MainPanel(frame)
frame.SetSize((-1,500))
frame.Show()
app.MainLoop()