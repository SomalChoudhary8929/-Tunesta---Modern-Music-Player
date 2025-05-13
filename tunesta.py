import pygame
from pygame import mixer
from tkinter import *
from tkinter import ttk, messagebox
import os
from mutagen.mp3 import MP3
import time
from PIL import Image, ImageTk
import random
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title('Tunesta - Modern Music Player')
        self.root.geometry('800x600')
        self.root.configure(bg='#2C3E50')
        
        # Initialize mixer
        mixer.init()
        
        # Variables
        self.songstatus = StringVar()
        self.songstatus.set("Select a song")
        self.current_song = ""
        self.paused = False
        self.repeat_mode = False
        self.shuffle_mode = False
        self.is_mini_player = False
        self.original_geometry = "800x600"
        
        # Load and set icon
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
            
        # Create main frame
        self.main_frame = Frame(self.root, bg='#2C3E50')
        self.main_frame.pack(pady=20)
        
        # Search frame
        self.search_frame = Frame(self.main_frame, bg='#2C3E50')
        self.search_frame.grid(row=0, column=0, pady=10)
        
        self.search_var = StringVar()
        self.search_var.trace('w', self.filter_songs)
        self.search_entry = Entry(self.search_frame, textvariable=self.search_var,
                                font=('Helvetica', 12), width=40)
        self.search_entry.grid(row=0, column=0, padx=5)
        
        # Song list frame
        self.song_frame = Frame(self.main_frame, bg='#2C3E50')
        self.song_frame.grid(row=1, column=0, pady=20)
        
        # Playlist
        self.playlist = Listbox(self.song_frame, selectmode=SINGLE, bg='#34495E', fg='white',
                              font=('Helvetica', 12), width=50, height=10,
                              selectbackground='#3498DB', selectforeground='white')
        self.playlist.grid(row=0, column=0, pady=10)
        
        # Scrollbar
        scrollbar = Scrollbar(self.song_frame, orient=VERTICAL)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.playlist.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.playlist.yview)
        
        # Control frame
        self.control_frame = Frame(self.main_frame, bg='#2C3E50')
        self.control_frame.grid(row=2, column=0, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.control_frame, orient=HORIZONTAL, 
                                      length=400, mode='determinate')
        self.progress.grid(row=0, column=0, columnspan=5, pady=10)
        
        # Time labels
        self.time_label = Label(self.control_frame, text="00:00 / 00:00", 
                              bg='#2C3E50', fg='white', font=('Helvetica', 10))
        self.time_label.grid(row=1, column=0, columnspan=5, pady=5)
        
        # Volume control
        self.volume_label = Label(self.control_frame, text="Volume", 
                                bg='#2C3E50', fg='white', font=('Helvetica', 10))
        self.volume_label.grid(row=2, column=0, pady=5)
        
        self.volume_slider = ttk.Scale(self.control_frame, from_=0, to=1, 
                                     orient=HORIZONTAL, length=100, 
                                     command=self.set_volume)
        self.volume_slider.set(0.5)
        self.volume_slider.grid(row=2, column=1, pady=5)
        
        # Control buttons
        self.create_control_buttons()
        
        # Status bar
        self.status_bar = Label(self.root, textvariable=self.songstatus, 
                              bg='#34495E', fg='white', font=('Helvetica', 10))
        self.status_bar.pack(side=BOTTOM, fill=X)
        
        # Visualizer frame
        self.visualizer_frame = Frame(self.main_frame, bg='#2C3E50')
        self.visualizer_frame.grid(row=3, column=0, pady=10)
        
        # Create figure for visualizer
        self.fig = plt.Figure(figsize=(5, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.visualizer_frame)
        self.canvas.get_tk_widget().pack()
        
        # Load songs
        self.load_songs()
        
        # Bind events
        self.playlist.bind('<Double-1>', lambda e: self.playsong())
        self.root.bind('<space>', lambda e: self.toggle_play_pause())
        self.root.bind('<Left>', lambda e: self.previous_song())
        self.root.bind('<Right>', lambda e: self.next_song())
        self.root.bind('<Up>', lambda e: self.volume_up())
        self.root.bind('<Down>', lambda e: self.volume_down())
        self.root.bind('<m>', lambda e: self.toggle_mini_player())
        
        # Start progress bar update
        self.update_progress()
        
    def create_control_buttons(self):
        # Previous button
        self.prev_btn = Button(self.control_frame, text="⏮", command=self.previous_song,
                             font=('Helvetica', 20), bg='#3498DB', fg='white',
                             width=3, borderwidth=0)
        self.prev_btn.grid(row=3, column=0, padx=5)
        
        # Play button
        self.play_btn = Button(self.control_frame, text="▶", command=self.playsong,
                             font=('Helvetica', 20), bg='#3498DB', fg='white',
                             width=3, borderwidth=0)
        self.play_btn.grid(row=3, column=1, padx=5)
        
        # Pause button
        self.pause_btn = Button(self.control_frame, text="⏸", command=self.pausesong,
                              font=('Helvetica', 20), bg='#3498DB', fg='white',
                              width=3, borderwidth=0)
        self.pause_btn.grid(row=3, column=2, padx=5)
        
        # Stop button
        self.stop_btn = Button(self.control_frame, text="⏹", command=self.stopsong,
                             font=('Helvetica', 20), bg='#3498DB', fg='white',
                             width=3, borderwidth=0)
        self.stop_btn.grid(row=3, column=3, padx=5)
        
        # Next button
        self.next_btn = Button(self.control_frame, text="⏭", command=self.next_song,
                             font=('Helvetica', 20), bg='#3498DB', fg='white',
                             width=3, borderwidth=0)
        self.next_btn.grid(row=3, column=4, padx=5)
        
        # Shuffle button
        self.shuffle_btn = Button(self.control_frame, text="🔀", command=self.toggle_shuffle,
                                font=('Helvetica', 20), bg='#3498DB', fg='white',
                                width=3, borderwidth=0)
        self.shuffle_btn.grid(row=3, column=5, padx=5)
        
        # Repeat button
        self.repeat_btn = Button(self.control_frame, text="🔁", command=self.toggle_repeat,
                               font=('Helvetica', 20), bg='#3498DB', fg='white',
                               width=3, borderwidth=0)
        self.repeat_btn.grid(row=3, column=6, padx=5)
        
        # Mini player button
        self.mini_btn = Button(self.control_frame, text="⬆", command=self.toggle_mini_player,
                             font=('Helvetica', 20), bg='#3498DB', fg='white',
                             width=3, borderwidth=0)
        self.mini_btn.grid(row=3, column=7, padx=5)
        
    def load_songs(self):
        try:
            os.chdir(r'C:\Users\Somal choudhary\Music\Playlist')
            songs = [f for f in os.listdir() if f.endswith(('.mp3', '.wav'))]
            for song in songs:
                self.playlist.insert(END, song)
        except Exception as e:
            self.songstatus.set(f"Error loading songs: {str(e)}")
            
    def filter_songs(self, *args):
        search_term = self.search_var.get().lower()
        self.playlist.delete(0, END)
        try:
            os.chdir(r'C:\Users\Somal choudhary\Music\Playlist')
            songs = [f for f in os.listdir() if f.endswith(('.mp3', '.wav'))]
            for song in songs:
                if search_term in song.lower():
                    self.playlist.insert(END, song)
        except Exception as e:
            self.songstatus.set(f"Error filtering songs: {str(e)}")
            
    def playsong(self):
        try:
            self.current_song = self.playlist.get(ACTIVE)
            mixer.music.load(self.current_song)
            mixer.music.play()
            self.songstatus.set(f"Playing: {self.current_song}")
            self.paused = False
            self.update_progress()
            self.update_visualizer()
        except Exception as e:
            self.songstatus.set(f"Error playing song: {str(e)}")
            
    def pausesong(self):
        if not self.paused:
            mixer.music.pause()
            self.paused = True
            self.songstatus.set("Paused")
        else:
            mixer.music.unpause()
            self.paused = False
            self.songstatus.set("Playing")
            
    def stopsong(self):
        mixer.music.stop()
        self.songstatus.set("Stopped")
        self.progress['value'] = 0
        self.time_label.config(text="00:00 / 00:00")
        
    def next_song(self):
        try:
            current = self.playlist.curselection()
            if self.shuffle_mode:
                next_song = random.randint(0, self.playlist.size() - 1)
            else:
                next_song = current[0] + 1
                if next_song >= self.playlist.size():
                    if self.repeat_mode:
                        next_song = 0
                    else:
                        return
            self.playlist.selection_clear(0, END)
            self.playlist.activate(next_song)
            self.playlist.selection_set(next_song)
            self.playsong()
        except:
            pass
            
    def previous_song(self):
        try:
            current = self.playlist.curselection()
            if self.shuffle_mode:
                prev_song = random.randint(0, self.playlist.size() - 1)
            else:
                prev_song = current[0] - 1
                if prev_song < 0:
                    if self.repeat_mode:
                        prev_song = self.playlist.size() - 1
                    else:
                        return
            self.playlist.selection_clear(0, END)
            self.playlist.activate(prev_song)
            self.playlist.selection_set(prev_song)
            self.playsong()
        except:
            pass
            
    def set_volume(self, val):
        volume = float(val)
        mixer.music.set_volume(volume)
        
    def volume_up(self):
        current_volume = self.volume_slider.get()
        new_volume = min(1.0, current_volume + 0.1)
        self.volume_slider.set(new_volume)
        self.set_volume(new_volume)
        
    def volume_down(self):
        current_volume = self.volume_slider.get()
        new_volume = max(0.0, current_volume - 0.1)
        self.volume_slider.set(new_volume)
        self.set_volume(new_volume)
        
    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        self.shuffle_btn.config(bg='#E74C3C' if self.shuffle_mode else '#3498DB')
        
    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        self.repeat_btn.config(bg='#E74C3C' if self.repeat_mode else '#3498DB')
        
    def toggle_mini_player(self):
        if not self.is_mini_player:
            self.original_geometry = self.root.geometry()
            self.root.geometry("300x100")
            self.main_frame.pack_forget()
            self.visualizer_frame.pack_forget()
            self.is_mini_player = True
        else:
            self.root.geometry(self.original_geometry)
            self.main_frame.pack(pady=20)
            self.visualizer_frame.grid(row=3, column=0, pady=10)
            self.is_mini_player = False
            
    def toggle_play_pause(self):
        if self.paused:
            self.pausesong()
        else:
            self.playsong()
            
    def update_progress(self):
        if mixer.music.get_busy() and not self.paused:
            try:
                # Get current position
                current_time = mixer.music.get_pos() / 1000
                
                # Use a fixed duration for now (5 minutes)
                song_length = 300  # 5 minutes in seconds
                
                # Update progress bar
                progress = (current_time / song_length) * 100
                self.progress['value'] = progress
                
                # Update time labels
                current_time_str = time.strftime('%M:%S', time.gmtime(current_time))
                total_time_str = time.strftime('%M:%S', time.gmtime(song_length))
                self.time_label.config(text=f"{current_time_str} / {total_time_str}")
                
                # Check if song ended
                if current_time >= song_length:
                    if self.repeat_mode:
                        self.playsong()
                    else:
                        self.next_song()
                
            except:
                pass
                
        self.root.after(1000, self.update_progress)
        
    def update_visualizer(self):
        if mixer.music.get_busy() and not self.paused:
            try:
                # Generate random data for visualization
                data = np.random.rand(100)
                self.ax.clear()
                self.ax.plot(data, color='#3498DB')
                self.ax.set_ylim(0, 1)
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                self.canvas.draw()
            except:
                pass
                
        self.root.after(100, self.update_visualizer)

if __name__ == "__main__":
    root = Tk()
    app = MusicPlayer(root)
    root.mainloop()
