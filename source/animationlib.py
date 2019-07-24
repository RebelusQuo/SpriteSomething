#this class acts as a go-between between the GUI and the sprite class
#in particular, keeps track of information like which palette the sprite is using, etc.

import tkinter as tk
import random
import json
import itertools
from source import common, widgetlib

class AnimationEngineParent():
	def __init__(self, my_subpath):
		self.resource_subpath = my_subpath           #the path to this sprite's subfolder in resources
		self.spiffy_buttons_exist = False
		self.overhead = True                         #by default, this will create NESW direction buttons.  If false, only left/right buttons
		self.overview_scale_factor = 2               #when the overview is made, it is scaled up by this amount
		self.plugins = []

		with open(common.get_resource("animations.json",subdir=self.resource_subpath)) as file:
			self.animations = json.load(file)

		self.current_animation = next(iter(self.animations.keys())) #TODO: hook this to the animation dropdown
		
	def attach_animation_panel(self, parent, canvas, overview_canvas, zoom_getter, frame_getter, coord_getter, fish):
		ANIMATION_DROPDOWN_WIDTH = 25
		PANEL_HEIGHT = 25
		self.canvas = canvas
		self.overview_canvas = overview_canvas
		self.zoom_getter = zoom_getter
		self.frame_getter = frame_getter
		self.coord_getter = coord_getter
		self.current_animation = None
		self.pose_number = None
		self.palette_number = None

		animation_panel = tk.Frame(parent, name="animation_panel")
		widgetlib.right_align_grid_in_frame(animation_panel)
		animation_label = tk.Label(animation_panel, text=fish.translate("meta","meta","animations") + ':')
		animation_label.grid(row=0, column=1)
		self.animation_selection = tk.StringVar(animation_panel)

		self.animation_selection.set(random.choice(list(self.animations.keys())))

		animation_dropdown = tk.ttk.Combobox(animation_panel, state="readonly", values=list(self.animations.keys()), name="animation_dropdown")
		animation_dropdown.configure(width=ANIMATION_DROPDOWN_WIDTH, exportselection=0, textvariable=self.animation_selection)
		animation_dropdown.grid(row=0, column=2)
		self.set_animation(self.animation_selection.get())

		widgetlib.leakless_dropdown_trace(self, "animation_selection", "set_animation")

		parent.add(animation_panel,minsize=PANEL_HEIGHT)

		direction_panel, height = self.get_direction_buttons(parent,fish).get_panel()
		parent.add(direction_panel, minsize=height)

		spiffy_panel, height = self.get_spiffy_buttons(parent,fish).get_panel()
		self.spiffy_buttons_exist = True
		parent.add(spiffy_panel,minsize=height)

		self.update_overview_panel()

		return animation_panel

	def set_animation(self, animation_name):
		self.current_animation = animation_name
		self.update_animation()

	def update_animation(self):
		pose_list = self.get_current_pose_list()
		if "frames" not in pose_list[0]:      #might not be a frame entry for static poses
			self.frame_progression_table = [1]
		else:
			self.frame_progression_table = list(itertools.accumulate([pose["frames"] for pose in pose_list]))

		if hasattr(self,"sprite_IDs"):
			for ID in self.sprite_IDs:
				self.canvas.delete(ID)       #remove the old tiles
		if hasattr(self,"active_tiles"):
			for tile in self.active_tiles:
				del tile                     #why this is not auto-destroyed is beyond me (memory leak otherwise)
		self.sprite_IDs = []
		self.active_tiles = []

		for tile,offset in self.get_tiles_for_current_pose():
			new_size = tuple(int(dim*self.zoom_getter()) for dim in tile.size)
			#TODO: Fix this
			scaled_tile = ImageTk.PhotoImage(tile.resize(new_size,resample=Image.NEAREST))
			coord_on_canvas = tuple(int(self.zoom_getter()*(pos+x)) for pos,x in zip(self.coord_getter(),offset))
			self.sprite_IDs.append(self.canvas.create_image(*coord_on_canvas, image=scaled_tile, anchor = tk.NW))
			self.active_tiles.append(scaled_tile)     #if you skip this part, then the auto-destructor will get rid of your picture!

	def get_current_pose_list(self):
		direction_dict = self.animations[self.current_animation]
		if self.spiffy_buttons_exist:     #this will also indicate if the direction buttons exist
			if hasattr(self,"facing_var"):
				direction = self.facing_var.get().lower()   #grabbed from the direction buttons, which are named "facing"
				if direction in direction_dict:
					return direction_dict[direction]
		#otherwise just grab the first listed direction
		return next(iter(direction_dict.values()))

	#Mike likes spiffy buttons
	def get_spiffy_buttons(self, parent, fish):
		#if this is not overriden by the child (sprite-specific) class, then there will be no spiffy buttons
		return widgetlib.SpiffyButtons(self, parent, fish)

	#Art likes direction buttons
	def get_direction_buttons(self, parent, fish):
		#if this is not overriden by the child (sprite-specific) class, then it will default to WASD layout for overhead, or just left/right if sideview (not overhead).
		direction_buttons = widgetlib.SpiffyButtons(self, parent, frame_name="direction_buttons", align="center")

		facing_group = direction_buttons.make_new_group("facing", fish)
		if self.overhead:
			facing_group.adds([
				(None,"",None), #a blank space, baby
				("up","arrow-up.png",False),
				(None,"",None), #a blank space, baby
				(None,None,None)
			],fish)
		facing_group.add("left", "arrow-left.png", fish)
		if self.overhead:
			facing_group.add("down", "arrow-down.png", fish)
		facing_group.add("right", "arrow-right.png", fish, default=True)

		return direction_buttons
